from src.broken_line import BrokenLineOptimizer
from src.functions import functions
from src.visualizer import Visualizer

def main():
    """Основная демонстрация"""
    print("=== Метод ломаных - демонстрация ===\n")
    
    # Точнсть
    eps = 1e-4

    # Тест на разных функциях
    test_cases = [
        ('rastrigin', -2, 2, eps),
        ('shifted_rastrigin', -0.5, 3.5, eps),
        ('ackley', -5, 5, eps),
        ('multimodal', -3, 3, eps),
        ("multi_minima", -2, 2, eps)
    ]
    
    for func_name, a, b, eps in test_cases:
        print(f"\n--- Функция: {func_name} на [{a}, {b}] ---")
        
        # Создание оптимизатора
        optimizer = BrokenLineOptimizer(functions[func_name], a, b, eps=eps)
        
        # Оптимизация
        x_opt, f_opt = optimizer.optimize()
        
        # Результаты
        print(f"Найденный минимум: u* = {x_opt:.8f}")
        print(f"Значение функции: J(u*) = {f_opt:.8f}")
        print(f"Количество итераций: {optimizer.iterations}")
        print(f"Вычислений функции: {len(optimizer.points)}")
        print(f"Затраченное время: {optimizer.optimization_time:.4f} сек")
        
        # Визуализация
        visualizer = Visualizer(optimizer)
        visualizer.plot(save_path=f"{func_name}.png")

if __name__ == "__main__":
    main()