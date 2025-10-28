import numpy as np
from .problem import CanonicalProblem

def to_canonical_form(problem):
    """Приведение общей задачи к канонической форме"""
    canonical = CanonicalProblem()
    n_original = len(problem.c)
    canonical.original_var_count = n_original
    
    # Определяем неотрицательные переменные
    non_negative_vars = set(problem.non_negative_vars)
    
    # Создаем mapping для замены свободных переменных
    free_var_replacements = {}
    
    # Сначала определяем, какие переменные будут в канонической форме
    # Неотрицательные переменные остаются как есть
    # Свободные переменные заменяются на x⁺ и x⁻
    
    # Счетчик для новых переменных
    current_var_index = 0
    canonical_var_indices = {}  # Сопоставление исходных индексов с каноническими
    
    # Добавляем неотрицательные переменные
    for i in range(n_original):
        if i in non_negative_vars:
            canonical_var_indices[i] = [current_var_index]
            current_var_index += 1
    
    # Добавляем замены для свободных переменных
    for i in range(n_original):
        if i not in non_negative_vars:
            free_var_replacements[i] = (current_var_index, current_var_index + 1)
            canonical_var_indices[i] = [current_var_index, current_var_index + 1]
            current_var_index += 2
    
    # Подсчитываем фиктивные переменные
    num_slack_vars = 0
    for constraint in problem.constraints:
        if constraint['inequality'] != '=':
            num_slack_vars += 1
    
    # Общее количество переменных в канонической форме
    total_vars = current_var_index + num_slack_vars
    
    # Инициализируем матрицу A и вектор b
    num_constraints = len(problem.constraints)
    canonical.A = np.zeros((num_constraints, total_vars))
    canonical.b = np.zeros(num_constraints)
    
    # Заполняем матрицу ограничений
    slack_var_idx = current_var_index
    for i, constraint in enumerate(problem.constraints):
        coefficients = constraint['coefficients']
        constant = constraint['constant']
        
        # Заполняем коэффициенты для всех исходных переменных
        for j, coeff in enumerate(coefficients):
            if j in free_var_replacements:
                # Свободная переменная: x_j = x_j⁺ - x_j⁻
                pos_idx, neg_idx = free_var_replacements[j]
                canonical.A[i, pos_idx] = coeff
                canonical.A[i, neg_idx] = -coeff
            else:
                # Неотрицательная переменная
                canonical_idx = canonical_var_indices[j][0]
                canonical.A[i, canonical_idx] = coeff
        
        # Добавляем фиктивные переменные
        if constraint['inequality'] == '<=':
            canonical.A[i, slack_var_idx] = 1
            slack_var_idx += 1
        elif constraint['inequality'] == '>=':
            canonical.A[i, slack_var_idx] = -1
            slack_var_idx += 1
        
        # Устанавливаем правую часть
        canonical.b[i] = constant
        if canonical.b[i] < 0:
            canonical.b[i] = -canonical.b[i]
            canonical.A[i, :] = -canonical.A[i, :]
    
    # Формируем целевую функцию
    canonical.c = np.zeros(total_vars)
    
    # Заполняем коэффициенты целевой функции
    for j in range(n_original):
        if j in free_var_replacements:
            # Для свободной переменной: c_j * x_j = c_j * (x_j⁺ - x_j⁻)
            pos_idx, neg_idx = free_var_replacements[j]
            if problem.objective == 'max':
                canonical.c[pos_idx] = -problem.c[j]
                canonical.c[neg_idx] = problem.c[j]
            else:
                canonical.c[pos_idx] = problem.c[j]
                canonical.c[neg_idx] = -problem.c[j]
        else:
            # Для неотрицательной переменной
            canonical_idx = canonical_var_indices[j][0]
            if problem.objective == 'max':
                canonical.c[canonical_idx] = -problem.c[j]
            else:
                canonical.c[canonical_idx] = problem.c[j]
    
    # Создаем имена переменных
    canonical.var_names = [""] * total_vars
    
    # Заполняем имена для неотрицательных переменных
    for i in range(n_original):
        if i in non_negative_vars:
            canonical_idx = canonical_var_indices[i][0]
            canonical.var_names[canonical_idx] = f"x{i+1}"
    
    # Заполняем имена для замен свободных переменных
    for i in range(n_original):
        if i not in non_negative_vars:
            pos_idx, neg_idx = free_var_replacements[i]
            canonical.var_names[pos_idx] = f"x{i+1}⁺"
            canonical.var_names[neg_idx] = f"x{i+1}⁻"
    
    # Заполняем имена для фиктивных переменных
    for i in range(num_slack_vars):
        idx = current_var_index + i
        canonical.var_names[idx] = f"s{i+1}"
    
    canonical.free_var_mapping = free_var_replacements
    canonical.canonical_var_indices = canonical_var_indices
    
    return canonical

def get_original_solution(canonical_problem, solution):
    """Преобразование решения канонической задачи к исходным переменным"""
    original_solution = np.zeros(canonical_problem.original_var_count)
    
    for i in range(canonical_problem.original_var_count):
        if i in canonical_problem.free_var_mapping:
            pos_idx, neg_idx = canonical_problem.free_var_mapping[i]
            original_solution[i] = solution[pos_idx] - solution[neg_idx]
        else:
            # Находим индекс в канонической форме
            canonical_idx = canonical_problem.canonical_var_indices[i][0]
            original_solution[i] = solution[canonical_idx]
    
    return original_solution