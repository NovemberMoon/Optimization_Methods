import matplotlib.pyplot as plt
import numpy as np
import os

class Visualizer:
    """Визуализатор"""
    
    def __init__(self, optimizer):
        self.optimizer = optimizer
        os.makedirs("results", exist_ok=True)
    
    def plot(self, save_path=None):
        """Построение графика"""
        # Находим лучшую точку
        best_idx = np.argmin(self.optimizer.values)
        best_x = self.optimizer.points[best_idx]
        best_f = self.optimizer.values[best_idx]
        
        # Сетка для построения
        x = np.linspace(self.optimizer.a, self.optimizer.b, 1000)
        y_func = [self.optimizer.func(xi) for xi in x]
        y_p = [self.optimizer.p_function(xi) for xi in x]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # График 1: Функция и огибающая
        ax1.plot(x, y_func, 'b-', linewidth=2, label='J(u)')
        ax1.plot(x, y_p, 'g--', linewidth=1.5, label='p_n(u)')
        ax1.scatter(self.optimizer.points, self.optimizer.values, 
                   color='red', s=30, alpha=0.6, label='Точки вычислений')
        
        # Лучшее решение
        ax1.scatter([best_x], [best_f], color='gold', s=200, 
                   marker='*', label=f'Минимум: u={best_x:.6f}\nJ(u)={best_f:.6f}')
        
        ax1.set_xlabel('u')
        ax1.set_ylabel('J(u)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_title(f'Метод ломаных (итераций: {self.optimizer.iterations})')
        
        # График 2: Сходимость значения функции
        if len(self.optimizer.points) > 1:
            # Вычисляем последовательность лучших значений
            best_values = []
            current_best = float('inf')
            for value in self.optimizer.values:
                if value < current_best:
                    current_best = value
                best_values.append(current_best)
            
            ax2.plot(range(len(best_values)), best_values, 'ro-', linewidth=2, markersize=4)
            ax2.set_xlabel('Итерация')
            ax2.set_ylabel('Лучшее значение J(u)')
            ax2.grid(True, alpha=0.3)
            ax2.set_title('Сходимость к минимуму')
            
            # Добавляем горизонтальную линию на финальном значении
            ax2.axhline(y=best_f, color='blue', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(f"results/{save_path}", dpi=300, bbox_inches='tight')
            print(f"График сохранен: results/{save_path}")
        
        plt.show()