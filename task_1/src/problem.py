import numpy as np

class LinearProgrammingProblem:
    """Задача линейного программирования в общей форме"""
    
    def __init__(self):
        self.objective = None  # 'min' или 'max'
        self.c = []           # Коэффициенты целевой функции
        self.constraints = [] # Ограничения
        self.non_negative_vars = []  # Индексы неотрицательных переменных
        
    def add_constraint(self, coefficients, inequality, constant):
        """Добавление ограничения"""
        self.constraints.append({
            'coefficients': coefficients,
            'inequality': inequality,  # '<=', '=', '>='
            'constant': constant
        })
    
    def __str__(self):
        result = f"Целевая функция: {self.objective} "
        result += " + ".join([f"{self.c[i]}*x{i+1}" for i in range(len(self.c))]) + "\n"
        result += "Ограничения:\n"
        for constraint in self.constraints:
            coeffs = " + ".join([f"{constraint['coefficients'][i]}*x{i+1}" for i in range(len(constraint['coefficients']))])
            result += f"{coeffs} {constraint['inequality']} {constraint['constant']}\n"
        if self.non_negative_vars:
            var_names = [f"x{i+1}" for i in sorted(self.non_negative_vars)]
            result += f"Неотрицательные переменные: {', '.join(var_names)}\n"
        else:
            result += "Все переменные могут иметь любой знак\n"
        return result

class CanonicalProblem:
    """Каноническая задача линейного программирования"""
    
    def __init__(self):
        self.c = None        # Коэффициенты целевой функции (min)
        self.A = None        # Матрица ограничений
        self.b = None        # Правые части
        self.var_names = []  # Имена переменных
        self.free_var_mapping = {}  # Отображение свободных переменных
        self.canonical_var_indices = {}  # Сопоставление исходных индексов с каноническими
        self.original_var_count = 0 # Количество исходных переменных
    
    def __str__(self):
        result = "Каноническая форма:\n"
        
        # Формируем целевую функцию
        obj_terms = []
        for i in range(len(self.c)):
            if abs(self.c[i]) > 1e-10:  # Показываем только ненулевые коэффициенты
                obj_terms.append(f"{self.c[i]:.2f}*{self.var_names[i]}")
        
        if obj_terms:
            result += "Целевая функция: min " + " + ".join(obj_terms) + "\n"
        else:
            result += "Целевая функция: min 0\n"
        
        result += "Ограничения:\n"
        for i in range(len(self.A)):
            equation_terms = []
            for j in range(self.A.shape[1]):
                if abs(self.A[i, j]) > 1e-10:  # Показываем только ненулевые коэффициенты
                    equation_terms.append(f"{self.A[i, j]:.2f}*{self.var_names[j]}")
            
            if equation_terms:
                equation = " + ".join(equation_terms)
            else:
                equation = "0"
                
            result += f"{equation} = {self.b[i]:.2f}\n"
        
        return result