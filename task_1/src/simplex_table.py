import numpy as np

class SimplexTable:
    """Симплекс-таблица"""
    
    def __init__(self, problem, basis_indices):
        self.problem = problem
        self.basis_indices = np.array(basis_indices, dtype=int)
        self.free_indices = np.array([j for j in range(len(problem.c)) if j not in basis_indices], dtype=int)
        self.table = None
        
        self._build_table()
    
    def _build_table(self):
        """Построение начальной симплекс-таблицы"""
        m, n = len(self.problem.A), len(self.problem.c)
        
        if len(self.basis_indices) != m:
            raise ValueError(f"Неверный размер базиса: {len(self.basis_indices)} != {m}")
        
        # Строим таблицу
        self.table = np.zeros((m + 1, len(self.free_indices) + 1))
        
        # Заполняем строки базисных переменных
        for i, basis_idx in enumerate(self.basis_indices):
            for j, free_idx in enumerate(self.free_indices):
                self.table[i, j] = self.problem.A[i, free_idx]
            self.table[i, -1] = self.problem.b[i]
        
        # Изначально заполняем последнюю строку нулями, затем пересчитаем
        self.table[-1, :] = 0
        self._recalculate_estimates()
    
    def _recalculate_estimates(self):
        """Пересчет оценок через базисные переменные"""
        m = len(self.basis_indices)
        
        for j in range(len(self.free_indices) + 1):
            # Начальное значение: коэффициент целевой функции для этой переменной
            if j < len(self.free_indices):
                # Свободная переменная
                delta = self.problem.c[self.free_indices[j]]
            else:
                # Столбец b
                delta = 0
            
            # Вычитаем вклад базисных переменных
            for i in range(m):
                basis_idx = self.basis_indices[i]
                delta -= self.problem.c[basis_idx] * self.table[i, j]
            
            self.table[-1, j] = delta
    
    def find_pivot(self):
        """Нахождение разрешающего элемента"""
        m = len(self.basis_indices)
        last_row = self.table[-1, :-1]  # Все кроме последнего столбца
        
        # 1. Выбор разрешающего столбца
        if np.all(last_row >= -1e-10):  # Учитываем погрешность вычислений
            return None, None  # Решение найдено
        
        pivot_col = np.argmin(last_row)
        
        # 2. Выбор разрешающей строки
        ratios = []
        for i in range(m):
            a_ij = self.table[i, pivot_col]
            if a_ij > 1e-10:  # Учитываем погрешность вычислений
                ratio = self.table[i, -1] / a_ij
                ratios.append(ratio)
            else:
                ratios.append(np.inf)
        
        if np.all(np.isinf(ratios)):
            raise ValueError("Целевая функция не ограничена")
        
        pivot_row = np.argmin(ratios)
        
        return pivot_row, pivot_col
    
    def pivot(self, pivot_row, pivot_col):
        """Шаг симплекс-метода"""
        # Сохраняем старые значения для пересчета
        old_pivot = self.table[pivot_row, pivot_col]
        old_row = self.table[pivot_row, :].copy()
        old_col = self.table[:, pivot_col].copy()
        
        # Перерасчет разрешающего элемента
        self.table[pivot_row, pivot_col] = 1.0 / old_pivot
        
        # Перерасчет элементов разрешающей строки
        for j in range(self.table.shape[1]):
            if j != pivot_col:
                self.table[pivot_row, j] = old_row[j] / old_pivot
        
        # Перерасчет элементов разрешающего столбца
        for i in range(self.table.shape[0]):
            if i != pivot_row:
                self.table[i, pivot_col] = -old_col[i] / old_pivot
        
        # Перерасчет оставшихся элементов таблицы
        for i in range(self.table.shape[0]):
            if i != pivot_row:
                for j in range(self.table.shape[1]):
                    if j != pivot_col:
                        self.table[i, j] = self.table[i, j] - (old_row[j] * old_col[i]) / old_pivot
        
        # Обновление базиса
        old_basis = self.basis_indices[pivot_row]
        new_basis = self.free_indices[pivot_col]
        
        self.basis_indices[pivot_row] = new_basis
        self.free_indices[pivot_col] = old_basis
    
    def replace_objective(self, new_c, new_var_names=None):
        """Замена целевой функции на исходную"""
        self.problem.c = new_c
        if new_var_names is not None:
            self.problem.var_names = new_var_names
        
        # Пересчитываем оценки с новой целевой функцией
        self._recalculate_estimates()
    
    def remove_auxiliary_columns(self, n_original):
        """Удаление столбцов вспомогательных переменных, которые стали свободными (только для вспомогательной задачи)"""
        to_remove = []
        
        for j, free_idx in enumerate(self.free_indices):
            if free_idx >= n_original:  # Это вспомогательная переменная
                to_remove.append(j)
        
        # Удаляем столбцы в обратном порядке
        for j in sorted(to_remove, reverse=True):
            self.table = np.delete(self.table, j, axis=1)
            self.free_indices = np.delete(self.free_indices, j)
    
    def get_solution(self):
        """Получение текущего решения"""
        solution = np.zeros(len(self.problem.c))
        
        # Базисные переменные берут значения из правой части
        for i, basis_idx in enumerate(self.basis_indices):
            solution[basis_idx] = self.table[i, -1]
        
        objective_value = -self.table[-1, -1]
        
        return solution, objective_value
    
    def __str__(self):
        result = "Симплекс-таблица:\n"
        result += f"Базисные: {[self.problem.var_names[i] for i in self.basis_indices]}\n"
        result += f"Свободные: {[self.problem.var_names[i] for i in self.free_indices]}\n\n"
        
        # Заголовки
        result += "     "
        for j in self.free_indices:
            result += f"{self.problem.var_names[j]:>8} "
        result += "        b\n"
        
        # Строки базисных переменных
        for i, basis_idx in enumerate(self.basis_indices):
            result += f"{self.problem.var_names[basis_idx]:>3} |"
            for j in range(self.table.shape[1]):
                result += f"{self.table[i, j]:8.3f} "
            result += "\n"
        
        # Строка оценок
        result += " W  |"
        for j in range(self.table.shape[1]):
            result += f"{self.table[-1, j]:8.3f} "
        
        return result