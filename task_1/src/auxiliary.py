import numpy as np
from .problem import CanonicalProblem
from .simplex_table import SimplexTable

class AuxiliaryProblemSolver:
    """Решение вспомогательной задачи"""
    
    def __init__(self, canonical_problem):
        self.original = canonical_problem
        self.auxiliary = None
    
    def create_auxiliary_problem(self):
        """Создание вспомогательной задачи"""
        self.auxiliary = CanonicalProblem()
        m, n = self.original.A.shape[0], len(self.original.c)
        
        # Целевая функция: сумма вспомогательных переменных → min
        auxiliary_c = np.zeros(n + m)
        auxiliary_c[n:] = 1  # Коэффициенты для вспомогательных переменных
        
        # Матрица ограничений
        auxiliary_A = np.zeros((m, n + m))
        auxiliary_A[:, :n] = self.original.A
        for i in range(m):
            auxiliary_A[i, n + i] = 1  # Вспомогательная переменная
        
        auxiliary_b = self.original.b.copy()
        
        # Имена переменных
        auxiliary_var_names = self.original.var_names.copy()
        for i in range(m):
            auxiliary_var_names.append(f"y{i+1}")
        
        self.auxiliary.c = auxiliary_c
        self.auxiliary.A = auxiliary_A
        self.auxiliary.b = auxiliary_b
        self.auxiliary.var_names = auxiliary_var_names
        self.auxiliary.original_var_count = self.original.original_var_count
        
        return self.auxiliary
    
    def solve(self, log_file=None):
        """Решение вспомогательной задачи и возврат таблицы для основной задачи"""
        if self.auxiliary is None:
            self.create_auxiliary_problem()
        
        # Начальный базис - вспомогательные переменные
        n_original = len(self.original.c)
        initial_basis = list(range(n_original, n_original + self.original.A.shape[0]))
        
        table = SimplexTable(self.auxiliary, initial_basis)
        
        if log_file:
            log_file.write("Начальная симплекс-таблица вспомогательной задачи:\n")
            log_file.write(str(table) + "\n")
        
        # Решаем вспомогательную задачу
        iteration = 0
        while iteration < 100:
            pivot_row, pivot_col = table.find_pivot()
            
            if pivot_row is None:
                break
                
            if log_file:
                log_file.write(f"\nШаг {iteration + 1}:\n")
                log_file.write(f"Разрешающий элемент: строка {pivot_row}, столбец {pivot_col}\n")
            
            table.pivot(pivot_row, pivot_col)
            
            # Удаляем столбцы вспомогательных переменных
            table.remove_auxiliary_columns(n_original)
            
            if log_file:
                log_file.write(str(table) + "\n")
            
            iteration += 1
        
        # Проверяем результат
        solution, objective_value = table.get_solution()
        
        if log_file:
            log_file.write(f"\nРезультат вспомогательной задачи: W = {objective_value:.6f}\n")
        
        if abs(objective_value) > 1e-6:
            raise ValueError("Исходная задача не имеет допустимых решений")
        
        # Проверяем, что в базисе нет вспомогательных переменных
        for basis_idx in table.basis_indices:
            if basis_idx >= n_original:
                raise ValueError("В базисе остались вспомогательные переменные")
        
        # Замена целевой функции на исходную
        table.replace_objective(self.original.c, self.original.var_names)
        
        if log_file:
            log_file.write("\nСимплекс-таблица после замены целевой функции на исходную:\n")
            log_file.write(str(table) + "\n")
        
        return table