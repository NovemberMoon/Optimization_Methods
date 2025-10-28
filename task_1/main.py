import sys
import os
from src.problem import LinearProgrammingProblem
from src.converter import to_canonical_form, get_original_solution
from src.solver import LinearProgrammingSolver

def read_problem_from_file(filename):
    """Чтение задачи из файла"""
    problem = LinearProgrammingProblem()
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    # Парсинг целевой функции
    objective_line = lines[0].lower()
    if objective_line.startswith('max'):
        problem.objective = 'max'
        coefficients = list(map(float, objective_line[3:].split()))
    elif objective_line.startswith('min'):
        problem.objective = 'min'
        coefficients = list(map(float, objective_line[3:].split()))
    else:
        raise ValueError("Неверный формат целевой функции")
    
    problem.c = coefficients
    
    problem.non_negative_vars = []
    
    # Парсинг ограничений и информации о переменных
    for line in lines[1:]:
        line_lower = line.lower()
        
        if line_lower.startswith('var'):
            # Обработка информации о переменных
            parts = line_lower.split()
            if '>=' in parts:
                idx = parts.index('>=')
                # Собираем все числа до '>='
                var_indices = []
                for part in parts[1:idx]:
                    if part.isdigit():
                        var_indices.append(int(part) - 1)  # Переводим в 0-based индексы
                problem.non_negative_vars = var_indices
            continue
            
        if '<=' in line:
            idx = line.index('<=')
            coeffs_str = line[:idx].strip()
            constant_str = line[idx+2:].strip()
            coeffs = list(map(float, coeffs_str.split()))
            constant = float(constant_str)
            problem.add_constraint(coeffs, '<=', constant)
        elif '>=' in line:
            idx = line.index('>=')
            coeffs_str = line[:idx].strip()
            constant_str = line[idx+2:].strip()
            coeffs = list(map(float, coeffs_str.split()))
            constant = float(constant_str)
            problem.add_constraint(coeffs, '>=', constant)
        elif '=' in line:
            idx = line.index('=')
            coeffs_str = line[:idx].strip()
            constant_str = line[idx+1:].strip()
            coeffs = list(map(float, coeffs_str.split()))
            constant = float(constant_str)
            problem.add_constraint(coeffs, '=', constant)
    
    return problem

def main():
    if len(sys.argv) != 2:
        print("Использование: python main.py <файл_с_задачей>")
        print("Пример: python main.py data/input1.txt")
        return
    
    try:
        # Создаем файл для записи лога
        input_filename = sys.argv[1]
        base_name = os.path.splitext(input_filename)[0]
        log_filename = f"{base_name}_solution.txt"
        
        with open(log_filename, 'w', encoding='utf-8') as log_file:
            # Чтение и преобразование задачи
            log_file.write("=== РЕШЕНИЕ ЗАДАЧИ ЛИНЕЙНОГО ПРОГРАММИРОВАНИЯ ===\n\n")
            
            log_file.write("Чтение задачи из файла...\n")
            problem = read_problem_from_file(input_filename)
            
            log_file.write("\n=== ИСХОДНАЯ ЗАДАЧА ===\n")
            log_file.write(str(problem) + "\n")
            
            log_file.write("\nПреобразование к канонической форме...\n")
            canonical_problem = to_canonical_form(problem)
            
            log_file.write("\n=== КАНОНИЧЕСКАЯ ФОРМА ===\n")
            log_file.write(str(canonical_problem) + "\n")
            
            # Решение
            solver = LinearProgrammingSolver()
            solution, objective_value = solver.solve(canonical_problem, log_file)
            
            # Вывод результатов
            log_file.write("\n=== РЕЗУЛЬТАТ ===\n")
            
            # Преобразуем решение к исходным переменным
            original_solution = get_original_solution(canonical_problem, solution)
            
            log_file.write("Оптимальное решение:\n")
            for i, val in enumerate(original_solution):
                log_file.write(f"x{i+1} = {val:.6f}\n")
            
            # Корректировка значения целевой функции для исходной задачи
            if problem.objective == 'max':
                final_objective = -objective_value
            else:
                final_objective = objective_value
                
            log_file.write(f"Значение целевой функции: {final_objective:.6f}\n")
        
        print(f"Решение сохранено в файл: {log_filename}")
        
        # Также выводим результат в консоль
        print("\n=== РЕЗУЛЬТАТ ===")
        print("Оптимальное решение:")
        for i, val in enumerate(original_solution):
            print(f"x{i+1} = {val:.6f}")
        print(f"Значение целевой функции: {final_objective:.6f}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()