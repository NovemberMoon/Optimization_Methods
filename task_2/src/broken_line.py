import numpy as np
import time
from typing import Callable

class BrokenLineOptimizer:
    """
    Реализация метода ломаных для поиска глобального минимума
    """
    
    def __init__(self, func: Callable, a: float, b: float, L: float = None, eps: float = 1e-4):
        self.func = func
        self.a = a
        self.b = b
        self.eps = eps
        self.L = L
        
        # История вычислений
        self.points = []  # Точки u_i
        self.values = []  # Значения J(u_i)
        self.iterations = 0
        
    def estimate_L(self, n_points=1000):
        """Оценка константы Липшица"""
        x = np.linspace(self.a, self.b, n_points)
        y = [self.func(xi) for xi in x]
        
        L = 0
        for i in range(1, len(x)):
            L = max(L, abs(y[i] - y[i-1]) / abs(x[i] - x[i-1]))
        
        return L * 1.2  # Запас 20%
    
    def p_function(self, u):
        """Функция p_n(u) = max_i [J(u_i) - L|u - u_i|]"""
        if not self.points:
            return -np.inf
            
        return max(self.values[i] - self.L * abs(u - self.points[i]) 
                   for i in range(len(self.points)))
    
    def find_min_p(self, n_grid=1000):
        """Поиск минимума p_n(u) на сетке"""
        grid = np.linspace(self.a, self.b, n_grid)
        p_vals = [self.p_function(x) for x in grid]
        return grid[np.argmin(p_vals)]
    
    def optimize(self, max_iter=1000):
        """Основной алгоритм метода ломаных"""
        start_time = time.time()
        
        # Оценка L если не задана
        if self.L is None:
            self.L = self.estimate_L()
            print(f"Константа Липшица: {self.L:.4f}")
        
        # Начальная точка - середина отрезка
        u0 = (self.a + self.b) / 2
        self.points = [u0]
        self.values = [self.func(u0)]
        
        best_x, best_f = u0, self.values[0]
        
        for iteration in range(max_iter):
            self.iterations = iteration + 1
            
            # Находим минимум p_n(u)
            u_new = self.find_min_p()
            
            # Вычисляем J(u_new)
            f_new = self.func(u_new)
            
            # Вычисляем p_n(u_new)
            p_val = self.p_function(u_new)
            
            # Зазор
            gap = f_new - p_val
            
            # Добавляем точку
            self.points.append(u_new)
            self.values.append(f_new)
            
            # Обновляем лучшее решение
            if f_new < best_f:
                best_x, best_f = u_new, f_new
            
            # Вывод прогресса
            if (iteration + 1) % 10 == 0:
                print(f"Итерация {iteration+1}: u={u_new:.6f}, J={f_new:.6f}, зазор={gap:.6f}, лучший={best_f:.6f}")
            
            # Условие остановки
            if gap < self.eps:
                print(f"Достигнута точность на итерации {iteration+1}")
                break
        
        self.optimization_time = time.time() - start_time
        
        # Возвращаем лучшую найденную точку
        return best_x, best_f