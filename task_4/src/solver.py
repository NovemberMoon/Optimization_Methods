import csv
from config import DATA

# ==========================================
# ПАРАМЕТРЫ ОГРАНИЧЕНИЯ ПОИСКА
# ==========================================

# Ограничение количества пакетов для одного актива за одну операцию.
# Предотвращает рассмотрение экстремальных стратегий.
MAX_PACKET_PER_ASSET = 5

# Ограничение на суммарное количество изменений в портфеле за один шаг.
# Позволяет ускорить расчет, отсекая маловероятные комбинации (например, одновременная покупка всех активов).
MAX_TOTAL_MOVES = 6

# Шаг дискретизации сетки состояний (в д.е.).
# Используется для группировки близких состояний при кэшировании (мемоизации).
GRID_STEP = 10


# ==========================================
# ВСПОМОГАТЕЛЬНЫЕ КЛАССЫ
# ==========================================

class PortfolioState:
    """
    Представление состояния портфеля для взаимодействия с внешним кодом.
    Служит для удобного хранения и форматированного вывода данных.
    """
    def __init__(self, cb1, cb2, dep, cash):
        self.cb1 = float(cb1)
        self.cb2 = float(cb2)
        self.dep = float(dep)
        self.cash = float(cash)
    
    def __repr__(self):
        """Строковое представление для отчетов (округленное до целых)."""
        return f"[ЦБ1={self.cb1:.0f}|ЦБ2={self.cb2:.0f}|Деп={self.dep:.0f}|Кэш={self.cash:.0f}]"
    
    def to_tuple(self):
        """Конвертация в неизменяемый кортеж для передачи в алгоритм."""
        return (self.cb1, self.cb2, self.dep, self.cash)


# ==========================================
# ОСНОВНОЙ АЛГОРИТМ (SOLVER)
# ==========================================

class Solver:
    """
    Реализация алгоритма стохастического динамического программирования.
    Осуществляет поиск оптимальной стратегии управления портфелем.
    """
    def __init__(self):
        self.data = DATA
        
        # Предварительный расчет параметров активов для быстрого доступа в циклах
        # 1. Размеры пакетов (25% от базы)
        self.step_sizes = [
            self.data['assets']['CB1']['step_base'] * 0.25,
            self.data['assets']['CB2']['step_base'] * 0.25,
            self.data['assets']['Dep']['step_base'] * 0.25
        ]
        # 2. Минимальные неснижаемые остатки
        self.min_limits = [
            self.data['assets']['CB1']['min_limit'],
            self.data['assets']['CB2']['min_limit'],
            self.data['assets']['Dep']['min_limit']
        ]
        # 3. Комиссионные ставки
        self.comm_rates = [
            self.data['assets']['CB1']['commission'],
            self.data['assets']['CB2']['commission'],
            self.data['assets']['Dep']['commission']
        ]
        
        # Словарь для мемоизации (хранит результаты уже вычисленных подзадач)
        self.memo = {}

    def get_grid_key(self, state_tuple, stage_idx):
        """
        Формирует ключ для кэша на основе дискретной сетки.
        Позволяет сопоставлять непрерывные состояния (float) с дискретными узлами сетки.
        """
        return (
            stage_idx,
            int(state_tuple[0] / GRID_STEP),
            int(state_tuple[1] / GRID_STEP),
            int(state_tuple[2] / GRID_STEP),
            int(state_tuple[3] / GRID_STEP)
        )

    def maximize_expected_value(self, state_obj, stage_idx):
        """
        Точка входа в алгоритм оптимизации.
        Запускает рекурсивный процесс поиска решения.
        """
        state_tuple = state_obj.to_tuple()
        # Очистка кэша обеспечивает корректность при повторных запусках с новыми параметрами
        self.memo.clear() 
        res = self._solve_recursive(state_tuple, stage_idx)
        return res

    def _solve_recursive(self, state, stage_idx):
        """
        Рекурсивная реализация уравнения Беллмана.
        Определяет максимальный ожидаемый доход для текущего состояния и этапа.
        
        Аргументы:
            state (tuple): Кортеж текущих значений активов и кэша.
            stage_idx (int): Текущий номер этапа.
            
        Возвращает:
            tuple: (Макс. EV, Лучшее управление, Дерево вариантов)
        """
        # --- 1. База рекурсии (Терминальное состояние) ---
        if stage_idx not in self.data['stages']:
            # Возвращаем суммарную стоимость портфеля в конце срока
            return sum(state), None, []

        # --- 2. Проверка кэша (Мемоизация) ---
        grid_key = self.get_grid_key(state, stage_idx)
        if grid_key in self.memo:
            return self.memo[grid_key]

        # Распаковка параметров для удобства чтения формул
        cb1, cb2, dep, cash = state
        s1, s2, s3 = self.step_sizes
        lim1, lim2, lim3 = self.min_limits
        cr1, cr2, cr3 = self.comm_rates

        # --- 3. Генерация пространства допустимых решений ---
        
        # Расчет диапазонов покупки/продажи для каждого актива
        
        # ЦБ 1
        sell1 = int(max(0, cb1 - lim1) // s1)
        buy1_cost = s1 * (1 + cr1)
        buy1 = int(cash // buy1_cost) if buy1_cost > 0 else 0
        r1 = range(max(-sell1, -MAX_PACKET_PER_ASSET), min(buy1, MAX_PACKET_PER_ASSET) + 1)

        # ЦБ 2
        sell2 = int(max(0, cb2 - lim2) // s2)
        buy2_cost = s2 * (1 + cr2)
        buy2 = int(cash // buy2_cost) if buy2_cost > 0 else 0
        r2 = range(max(-sell2, -MAX_PACKET_PER_ASSET), min(buy2, MAX_PACKET_PER_ASSET) + 1)

        # Депозит
        sell3 = int(max(0, dep - lim3) // s3)
        buy3_cost = s3 * (1 + cr3)
        buy3 = int(cash // buy3_cost) if buy3_cost > 0 else 0
        r3 = range(max(-sell3, -MAX_PACKET_PER_ASSET), min(buy3, MAX_PACKET_PER_ASSET) + 1)

        best_ev = -1.0         # Лучшее мат. ожидание
        best_u = (0, 0, 0)     # Оптимальный вектор управления
        best_tree = []         # Структура дерева решений

        # --- 4. Перебор вариантов управления ---
        for u1 in r1:
            for u2 in r2:
                # Отсечение по общему количеству действий
                if abs(u1) + abs(u2) > MAX_TOTAL_MOVES: continue
                
                for u3 in r3:
                    if abs(u1) + abs(u2) + abs(u3) > MAX_TOTAL_MOVES: continue
                    
                    # Применение управления (детерминированный шаг)
                    d1 = u1 * s1
                    d2 = u2 * s2
                    d3 = u3 * s3
                    
                    # Расчет комиссий (от объема операции)
                    cost = (d1 + d2 + d3 + 
                           abs(d1)*cr1 + abs(d2)*cr2 + abs(d3)*cr3)
                    
                    new_cash = cash - cost
                    
                    # Проверка финансовой реализуемости
                    if new_cash < -0.01: continue
                    
                    # --- 5. Оценка стохастических исходов ---
                    current_ev = 0.0
                    outcomes = []
                    
                    # Промежуточное состояние активов перед реакцией рынка
                    pre_cb1 = cb1 + d1
                    pre_cb2 = cb2 + d2
                    pre_dep = dep + d3
                    
                    # Перебор сценариев рынка для текущего этапа
                    scenarios = self.data['stages'][stage_idx]
                    
                    for scen in scenarios:
                        mult = scen['mults']
                        prob = scen['prob']
                        
                        # Состояние на начало следующего этапа
                        next_state = (
                            pre_cb1 * mult['CB1'],
                            pre_cb2 * mult['CB2'],
                            pre_dep * mult['Dep'],
                            new_cash
                        )
                        
                        # Рекурсивный вызов для следующего этапа
                        val, next_u, sub = self._solve_recursive(next_state, stage_idx + 1)
                        
                        # Накопление мат. ожидания (Критерий Байеса)
                        current_ev += prob * val
                        outcomes.append({
                            "name": scen['name'],
                            "prob": prob,
                            "next_s_tuple": next_state,
                            "res": (val, next_u, sub)
                        })
                    
                    # Обновление оптимума
                    if current_ev > best_ev:
                        best_ev = current_ev
                        best_u = (u1, u2, u3)
                        best_tree = outcomes

        res = (best_ev, best_u, best_tree)
        # Сохранение результата в кэш
        self.memo[grid_key] = res
        return res

    def export_csv(self, root_res, root_state_obj, filename="strategy.csv"):
        """
        Сохраняет найденную стратегию в файл формата CSV.
        Использует обход в ширину (BFS) для записи дерева решений.
        """
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f, delimiter=';')
            w.writerow(["Этап", "Сценарий (Путь)", "Состояние (до решения)", 
                        "ЦБ1(пак)", "ЦБ2(пак)", "Деп(пак)", "Ожидаемый Доход (EV)"])
            
            queue = [(root_res, root_state_obj.to_tuple(), 0, "Start")]
            processed = set()

            while queue:
                (ev, u, tree), s_tuple, stg, path = queue.pop(0)
                
                # Исключение дубликатов для сокращения объема отчета
                state_hash = (int(s_tuple[0]), int(s_tuple[1]), int(s_tuple[2]), int(s_tuple[3]))
                csv_key = (path, state_hash)
                
                if csv_key in processed: continue
                processed.add(csv_key)

                u = u if u else (0,0,0)
                
                # Формирование строки состояния
                s_str = f"[ЦБ1={s_tuple[0]:.0f}|ЦБ2={s_tuple[1]:.0f}|Деп={s_tuple[2]:.0f}|Кэш={s_tuple[3]:.0f}]"
                w.writerow([stg, path, s_str, u[0], u[1], u[2], f"{ev:.2f}"])
                
                if tree:
                    for branch in tree:
                        new_path = path + "->" + branch['name'][:4]
                        queue.append((branch['res'], branch['next_s_tuple'], stg + 1, new_path))