# dp_core.py
"""
Основной модуль решения DP.
Содержит:
 - State dataclass (сделан хешируемым для использования в словарях/множествах)
 - get_actions(state, steps, max_pkg_each) -> список действий
 - apply_and_move(state, action, multiplier) -> новое состояние (после сценария)
 - forward_reachable(initial, steps, stages, cap_per_t) -> множества достижимых состояний
 - backward_dp(reachable, stages, steps) -> V, policy
 - solve(config) -> запускает процесс и возвращает V, policy, initial_state
Документы и комментарии в функциях.
"""

from dataclasses import dataclass
from typing import Tuple, Dict, List, Set
import math

# -------------------------------
@dataclass(frozen=True)
class State:
    """Состояние: денежная стоимость активов и cash"""
    x1: float
    x2: float
    d: float
    cash: float

    def total(self) -> float:
        """Общая стоимость (итоговая функция)"""
        return self.x1 + self.x2 + self.d + self.cash

    def quantize(self, steps: Dict[str, float]) -> "State":
        """
        Квантование состояния до ближайших кратных шагов (чтобы состояния сравнивались по ключам).
        steps: {'x1': step_x1, 'x2': step_x2, 'd': step_d}
        cash округляем до min(step_x1,step_x2,step_d) — это простая договорённость.
        """
        def q(v, step):
            if step <= 0:
                return v
            return round(v / step) * step
        step_cash = min(steps['x1'], steps['x2'], steps['d'])
        return State(q(self.x1, steps['x1']),
                     q(self.x2, steps['x2']),
                     q(self.d,  steps['d']),
                     q(self.cash, step_cash))

# -------------------------------
def get_actions(s: State, steps: Dict[str, float], max_pkg_each: int = 5) -> List[Tuple[float, float, float]]:
    """
    Генерирует допустимые действия (dx1, dx2, dd).
    Ограничения:
      - cash_after = s.cash - (dx1+dx2+dd) >= 0  (нельзя иметь отрицательный cash)
      - Нельзя продать больше, чем имеется (контролируется диапазоном)
    Для управления комбинаторикой вводим max_pkg_each: максимальное число пакетов покупки для каждого актива,
    и диапазоны продажи ограничены текущими holdings.
    Возвращает список кортежей (dx1, dx2, dd) — денежные изменения.
    """
    step_x1 = steps['x1']; step_x2 = steps['x2']; step_d = steps['d']
    # макс покупаемых пакетов с учётом cash и max_pkg_each
    max_buy_x1 = min(max_pkg_each, int(math.floor(s.cash / step_x1)) if step_x1 > 0 else 0)
    max_buy_x2 = min(max_pkg_each, int(math.floor(s.cash / step_x2)) if step_x2 > 0 else 0)
    max_buy_d  = min(max_pkg_each, int(math.floor(s.cash / step_d))  if step_d  > 0 else 0)
    # макс продаваемых пакетов (сколько есть)
    max_sell_x1 = int(math.floor(s.x1 / step_x1)) if step_x1>0 else 0
    max_sell_x2 = int(math.floor(s.x2 / step_x2)) if step_x2>0 else 0
    max_sell_d  = int(math.floor(s.d  / step_d )) if step_d>0  else 0

    rng_x1 = range(-max_sell_x1, max_buy_x1 + 1)
    rng_x2 = range(-max_sell_x2, max_buy_x2 + 1)
    rng_d  = range(-max_sell_d,  max_buy_d  + 1)

    # если слишком много комбинаций — сузим диапазоны (защита от взрывного роста)
    if len(rng_x1)*len(rng_x2)*len(rng_d) > 5000:
        rng_x1 = range(max(-2, -max_sell_x1), min(2, max_buy_x1) + 1)
        rng_x2 = range(max(-2, -max_sell_x2), min(2, max_buy_x2) + 1)
        rng_d  = range(max(-2, -max_sell_d),  min(2, max_buy_d)  + 1)

    actions = []
    for a1 in rng_x1:
        dx1 = a1 * step_x1
        for a2 in rng_x2:
            dx2 = a2 * step_x2
            for ad in rng_d:
                dd = ad * step_d
                cash_after = s.cash - (dx1 + dx2 + dd)
                if cash_after < -1e-9:
                    continue
                if dx1 < -s.x1 - 1e-9 or dx2 < -s.x2 - 1e-9 or dd < -s.d - 1e-9:
                    continue
                actions.append((dx1, dx2, dd))
    return actions

# -------------------------------
def apply_and_move(s: State, a: Tuple[float, float, float], mult: Dict[str, float]) -> State:
    """
    Применить действие a к состоянию s, затем применить мультипликаторы mult.
    mult: {'m1':..., 'm2':..., 'md':...}
    Возвращает новое состояние (до квантования).
    """
    dx1, dx2, dd = a
    x1_post = s.x1 + dx1
    x2_post = s.x2 + dx2
    d_post  = s.d  + dd
    cash_post = s.cash - (dx1 + dx2 + dd)
    x1_next = x1_post * mult['m1']
    x2_next = x2_post * mult['m2']
    d_next  = d_post  * mult['md']
    return State(x1_next, x2_next, d_next, cash_post)

# -------------------------------
def forward_reachable(initial: State, steps: Dict[str, float], stages: List[Dict], cap_per_t: int = 2000):
    """
    Формируем множества достижимых состояний для каждого t: reachable[0..T]
    Ограничение cap_per_t предотвращает слишком большой рост числа состояний.
    Возвращает list of sets: reachable[t] — множества состояний (квантованных).
    """
    T = len(stages)
    reachable = [set() for _ in range(T+1)]
    reachable[0].add(initial.quantize(steps))
    for t in range(T):
        Snext = set()
        for s in reachable[t]:
            actions = get_actions(s, steps, max_pkg_each=5)
            for a in actions:
                for scen in stages[t]['scenarios']:
                    mult = {'m1':scen['m1'], 'm2':scen['m2'], 'md':scen['md']}
                    s2 = apply_and_move(s, a, mult).quantize(steps)
                    Snext.add(s2)
                    if len(Snext) >= cap_per_t:
                        break
                if len(Snext) >= cap_per_t:
                    break
            if len(Snext) >= cap_per_t:
                break
        if not Snext:
            raise RuntimeError(f"Reachable set empty at t={t+1} — проверьте входные данные.")
        reachable[t+1] = Snext
    return reachable

# -------------------------------
def backward_dp(reachable, stages, steps):
    """
    Прямо реализует рекуррентное соотношение Беллмана с критерием Байеса (ожидание).
    Возвращает:
      - V: список словарей V[t][state] = значение
      - policy: словарь policy[(t, state)] = лучшее действие
    """
    T = len(stages)
    V = [dict() for _ in range(T+1)]
    policy = dict()
    # Терминальное значение
    for s in reachable[T]:
        V[T][s] = s.total()
    # Backward induction
    for t in range(T-1, -1, -1):
        for s in reachable[t]:
            best_val = -1e18
            best_action = (0.0,0.0,0.0)
            actions = get_actions(s, steps, max_pkg_each=5)
            for a in actions:
                exp_val = 0.0
                for scen in stages[t]['scenarios']:
                    mult = {'m1':scen['m1'],'m2':scen['m2'],'md':scen['md']}
                    s_next = apply_and_move(s, a, mult).quantize(steps)
                    v_next = V[t+1].get(s_next, s_next.total())  # fallback: если s_next не в reachable
                    exp_val += scen['p'] * v_next
                if exp_val > best_val:
                    best_val = exp_val
                    best_action = a
            V[t][s] = best_val
            policy[(t,s)] = best_action
    return V, policy

# -------------------------------
def solve(config: Dict, cap_per_t: int = 2000):
    """
    Удобная обёртка:
    config: {'initial':..., 'steps':..., 'stages':...}
    Возвращает initial_state, V, policy
    """
    init = config['initial']; steps = config['steps']; stages = config['stages']
    initial_state = State(init['x1'], init['x2'], init['d'], init['cash']).quantize(steps)
    reachable = forward_reachable(initial_state, steps, stages, cap_per_t=cap_per_t)
    V, policy = backward_dp(reachable, stages, steps)
    return initial_state, V, policy
