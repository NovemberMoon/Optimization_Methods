import time
from config import DATA
from solver import Solver, PortfolioState, GRID_STEP, MAX_PACKET_PER_ASSET, MAX_TOTAL_MOVES

def main():
    print("=== ОПТИМИЗАЦИЯ ИНВЕСТИЦИОННОГО ПОРТФЕЛЯ ===")
    print("Метод: Стохастическое динамическое программирование")
    print("Критерий оптимальности: Максимизация мат. ожидания (Байес)")
    print("-" * 60)
    
    # Вывод параметров алгоритма
    print("ПАРАМЕТРЫ ОГРАНИЧЕНИЯ ОБЛАСТИ ПОИСКА:")
    print(f"  1. Лимит изменения одного актива (за шаг): +/- {MAX_PACKET_PER_ASSET} пакетов")
    print(f"  2. Лимит суммарных изменений (за шаг):     {MAX_TOTAL_MOVES} пакетов")
    print(f"  3. Шаг дискретизации сетки (Grid Step):    {GRID_STEP} д.е.")
    print("-" * 60)
    
    # Инициализация начального состояния из конфигурации
    init_assets = DATA['assets']
    start_state = PortfolioState(
        cb1=init_assets['CB1']['start_val'],
        cb2=init_assets['CB2']['start_val'],
        dep=init_assets['Dep']['start_val'],
        cash=DATA['initial_cash']
    )
    
    print(f"НАЧАЛЬНОЕ СОСТОЯНИЕ ПОРТФЕЛЯ:\n  {start_state}")
    
    solver = Solver()
    t0 = time.time()
    
    print("\n[INFO] Запуск алгоритма оптимизации...")
    
    # Запуск решения для этапа 0
    res = solver.maximize_expected_value(start_state, 0)
    
    dt = time.time() - t0
    print(f"[INFO] Расчет завершен.")
    print(f"       Время выполнения: {dt:.4f} сек.")
    print(f"       Количество просмотренных узлов сетки: {len(solver.memo)}")
    
    # Получение результатов для корневого узла
    ev, u, _ = res
    
    print("\n" + "="*30)
    print(f"МАКСИМАЛЬНЫЙ ОЖИДАЕМЫЙ ДОХОД: {ev:.2f} д.е.")
    print("="*30)
    
    print(f"\nОПТИМАЛЬНОЕ УПРАВЛЕНИЕ (ЭТАП 0 - ТЕКУЩИЙ МОМЕНТ):")
    # Вывод конкретных рекомендаций
    print(f"  > ЦБ 1: {u[0]:+d} пак. ({u[0] * 25} д.е.)")
    print(f"  > ЦБ 2: {u[1]:+d} пак. ({u[1] * 200} д.е.)")
    print(f"  > Деп : {u[2]:+d} пак. ({u[2] * 100} д.е.)")
    print("-" * 60)
    
    # Экспорт полной стратегии
    fname = "optimal_strategy_plan.csv"
    solver.export_csv(res, start_state, fname)
    print(f"[RESULT] Полный план управления (Дерево решений) сохранен в файл: {fname}")

if __name__ == "__main__":
    main()