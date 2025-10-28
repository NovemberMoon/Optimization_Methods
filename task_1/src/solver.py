from .auxiliary import AuxiliaryProblemSolver

class LinearProgrammingSolver:
    """Основной решатель задач линейного программирования"""
    
    def __init__(self):
        self.solution = None
        self.objective_value = None
        self.status = "not solved"
    
    def solve(self, canonical_problem, log_file=None):
        """Решение канонической задачи ЛП"""
        if log_file:
            log_file.write("=== РЕШЕНИЕ ВСПОМОГАТЕЛЬНОЙ ЗАДАЧИ ===\n")
        
        auxiliary_solver = AuxiliaryProblemSolver(canonical_problem)
        
        try:
            table = auxiliary_solver.solve(log_file)
        except ValueError as e:
            self.status = "infeasible"
            raise e
        
        if log_file:
            log_file.write("\n=== РЕШЕНИЕ ОСНОВНОЙ ЗАДАЧИ ===\n")
        
        iteration = 0
        while iteration < 100:
            pivot_row, pivot_col = table.find_pivot()
            
            if pivot_row is None:
                self.solution, self.objective_value = table.get_solution()
                self.status = "solved"
                if log_file:
                    log_file.write("\nОптимальное решение найдено!\n")
                    log_file.write(f"Финальная симплекс-таблица:\n")
                    log_file.write(str(table) + "\n")
                break
                
            if log_file:
                log_file.write(f"\nШаг {iteration + 1}:\n")
                log_file.write(f"Разрешающий элемент: строка {pivot_row}, столбец {pivot_col}\n")
            
            table.pivot(pivot_row, pivot_col)
            
            if log_file:
                log_file.write(str(table) + "\n")
            
            iteration += 1
        else:
            self.status = "max iterations reached"
            raise ValueError("Достигнуто максимальное число итераций")
        
        return self.solution, self.objective_value