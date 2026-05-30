"""
process/process.py - Clase Process: unidad fundamental de ejecución simulada.

Un proceso simulado NO ejecuta código real. Solo mantiene estado y atributos
que los planificadores manipulan tick a tick.
"""
import time
from dataclasses import dataclass, field
from typing import List, Optional

from core.enums import ProcessState


# Contador global para asignar PIDs únicos y crecientes
_pid_counter = 0


def _next_pid() -> int:
    global _pid_counter
    _pid_counter += 1
    return _pid_counter


@dataclass
class Process:
    """
    Representa un proceso simulado en el SO.

    Atributos clave:
        pid          : Identificador único del proceso
        name         : Nombre legible (ej. "calc", "editor")
        priority     : 1 (baja) a 10 (alta) — usado por el planificador por prioridad
        burst_time   : Unidades de CPU totales que necesita para terminar
        remaining    : Unidades de CPU restantes (decrece en cada tick)
        state        : Estado actual según ProcessState
        cpu_usage    : Porcentaje acumulado de uso de CPU (métrica)
        files_open   : Lista de nombres de archivos que tiene abiertos
        arrival_time : Tick en que llegó al sistema
        start_time   : Tick en que obtuvo CPU por primera vez
        finish_time  : Tick en que terminó
    """
    name         : str
    priority     : int   = 5
    burst_time   : int   = 5

    # Campos calculados automáticamente al crear
    pid          : int             = field(default_factory=_next_pid)
    state        : ProcessState    = field(default=ProcessState.NEW)
    remaining    : int             = field(init=False)
    cpu_usage    : float           = 0.0
    files_open   : List[str]       = field(default_factory=list)

    # Tiempos para métricas (se llenan durante la simulación)
    arrival_time : Optional[int]   = None
    start_time   : Optional[int]   = None
    finish_time  : Optional[int]   = None

    # Tiempo acumulado esperando en cola (para waiting time)
    wait_ticks   : int             = 0

    def __post_init__(self):
        # remaining empieza igual a burst_time
        self.remaining = self.burst_time
        # Validaciones básicas
        if not (1 <= self.priority <= 10):
            raise ValueError(f"Prioridad debe estar entre 1 y 10, se recibió: {self.priority}")
        if self.burst_time <= 0:
            raise ValueError("burst_time debe ser mayor a 0")

    def tick(self) -> bool:
        """
        Ejecuta un tick de CPU sobre este proceso.
        Devuelve True si el proceso terminó en este tick.
        """
        if self.state != ProcessState.RUNNING:
            raise RuntimeError(f"tick() llamado en proceso {self.pid} que no está RUNNING")
        self.remaining -= 1
        if self.remaining <= 0:
            self.state = ProcessState.FINISHED
            return True
        return False

    def to_ready(self, current_tick: int = 0):
        """Transición a estado READY."""
        self.state = ProcessState.READY
        if self.arrival_time is None:
            self.arrival_time = current_tick

    def to_running(self, current_tick: int = 0):
        """Transición a estado RUNNING. Registra start_time si es la primera vez."""
        self.state = ProcessState.RUNNING
        if self.start_time is None:
            self.start_time = current_tick

    def to_waiting(self):
        """Transición a estado WAITING (bloqueado por recurso)."""
        self.state = ProcessState.WAITING

    def to_finished(self, current_tick: int = 0):
        """Transición a estado FINISHED."""
        self.state = ProcessState.FINISHED
        self.finish_time = current_tick

    @property
    def progress_pct(self) -> float:
        """Porcentaje de completitud del proceso (0.0 a 100.0)."""
        if self.burst_time == 0:
            return 100.0
        return round((1 - self.remaining / self.burst_time) * 100, 1)

    def __repr__(self) -> str:
        return (f"Process(pid={self.pid}, name='{self.name}', "
                f"state={self.state.value}, remaining={self.remaining}/{self.burst_time}, "
                f"priority={self.priority})")
