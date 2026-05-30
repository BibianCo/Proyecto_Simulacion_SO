"""
core/exceptions.py - Excepciones personalizadas del simulador.
Tener excepciones propias mejora la legibilidad y el manejo de errores.
"""


class SimulatorError(Exception):
    """Excepción base del simulador."""
    pass


class ProcessLimitError(SimulatorError):
    """Se alcanzó el límite máximo de procesos simultáneos."""
    pass


class MemoryFullError(SimulatorError):
    """No hay marcos libres disponibles en RAM."""
    pass


class FileNotFoundError(SimulatorError):
    """El archivo simulado solicitado no existe."""
    pass


class MutexDeadlockError(SimulatorError):
    """Se detectó un posible deadlock en el sistema de archivos."""
    pass
