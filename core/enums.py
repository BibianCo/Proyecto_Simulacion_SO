"""
core/enums.py - Enumeraciones compartidas entre todos los módulos.
Usar Enum evita "magic strings" como "ready", "blocked", etc.
"""
from enum import Enum, auto


class ProcessState(Enum):
    """Estados posibles de un proceso (diagrama de estados clásico de SO)."""
    NEW       = "new"        # Recién creado, aún no en cola
    READY     = "ready"      # En cola, esperando CPU
    RUNNING   = "running"    # Actualmente en CPU
    WAITING   = "waiting"    # Bloqueado esperando recurso (archivo)
    FINISHED  = "finished"   # Ejecución completada


class PageState(Enum):
    """Estado de un marco de página en RAM."""
    FREE     = auto()   # Marco disponible
    OCCUPIED = auto()   # Marco ocupado por una página de proceso


class FileAccessType(Enum):
    """Tipo de acceso a un archivo simulado."""
    READ  = "READ"
    WRITE = "WRITE"


class SchedulerType(Enum):
    """Algoritmos de planificación disponibles."""
    ROUND_ROBIN = "Round Robin"
    PRIORITY    = "Prioridad"
    SJF         = "SJF (Shortest Job First)"
