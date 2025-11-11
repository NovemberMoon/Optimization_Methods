import math

def rastrigin(x):
    """Функция Растригина"""
    return 10 + x**2 - 10 * math.cos(2 * math.pi * x)

def shifted_rastrigin(x: float, shift: float = 1.5) -> float:
    """
    Сдвинутая функция Растригина
    """
    return rastrigin(x - shift)

def ackley(x):
    """Функция Экли"""
    return -20 * math.exp(-0.2 * math.sqrt(0.5 * x**2)) - \
           math.exp(0.5 * math.cos(2 * math.pi * x)) + 20 + math.exp(1)

def multimodal(x):
    """Функция с несколькими минимумами"""
    return math.sin(5*x) + 0.5 * math.cos(10*x) + 0.1 * x**2

def complex_oscillatory(x: float) -> float:
    """
    Сложная осциллирующая функция с ярко выраженными локальными минимумами
    """
    return math.sin(3*x) * math.cos(5*x) + 0.2 * (x - 1)**2 + 0.1 * math.sin(10*x)

def simple_quadratic(x):
    """Простая квадратичная функция"""
    return (x - 1)**2 + 2

def multi_minima(x: float) -> float:
    """
    Функция с несколькими явными минимумами
    f(x) = (x^2 - 1)^2 + sin(10*x)^2
    """
    return (x**2 - 1)**2 + math.sin(10*x)**2

# Словарь функций
functions = {
    'rastrigin': rastrigin,
    'shifted_rastrigin': shifted_rastrigin,
    'ackley': ackley,
    'multimodal': multimodal,
    'quadratic': simple_quadratic,
    'complex_oscillatory': complex_oscillatory,
    'multi_minima': multi_minima
}