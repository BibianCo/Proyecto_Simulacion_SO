"""
filesystem/mutex.py - Mutex y semáforo de conteo simulados.

NO usa threading real. Simula el estado de bloqueos a nivel lógico,
lo que es más claro pedagógicamente y evita race conditions reales.

Clases:
  SimMutex    → exclusión mutua estricta (1 escritor a la vez)
  SimSemaphore → semáforo de conteo (N lectores simultáneos)
"""
from typing import Optional, List
from dataclasses import dataclass, field
import time

from config import MAX_CONCURRENT_READ


@dataclass
class LockEntry:
    """Registro de un bloqueo activo."""
    pid       : int
    access    : str       # "READ" o "WRITE"
    timestamp : float = field(default_factory=time.time)


class SimMutex:
    """
    Mutex binario simulado — exclusión mutua para escritura.

    Estados:
      locked=False  → libre, cualquier proceso puede adquirirlo
      locked=True   → adquirido, otros procesos deben esperar (WAITING)

    Registra historia de bloqueos y liberaciones para el log.
    """

    def __init__(self, name: str):
        self.name        : str                  = name
        self.locked      : bool                 = False
        self.owner_pid   : Optional[int]        = None
        self.wait_queue  : List[int]            = []   # PIDs esperando
        self.lock_log    : List[str]            = []   # Historial legible

    def acquire(self, pid: int) -> bool:
        """
        Intenta adquirir el mutex.
        Retorna True si se adquirió, False si está bloqueado (proceso debe esperar).
        """
        if not self.locked:
            self.locked    = True
            self.owner_pid = pid
            self.lock_log.append(f"[LOCK]    PID {pid} adquirió '{self.name}'")
            return True
        else:
            if pid not in self.wait_queue:
                self.wait_queue.append(pid)
            self.lock_log.append(
                f"[WAIT]    PID {pid} esperando '{self.name}' (dueño: PID {self.owner_pid})"
            )
            return False

    def release(self, pid: int) -> Optional[int]:
        """
        Libera el mutex. Solo el dueño puede liberarlo.
        Retorna el PID del siguiente proceso en la cola (si hay alguno), o None.
        """
        if self.owner_pid != pid:
            self.lock_log.append(
                f"[ERROR]   PID {pid} intentó liberar '{self.name}' (no es el dueño)"
            )
            return None

        next_pid = None
        if self.wait_queue:
            next_pid       = self.wait_queue.pop(0)
            self.owner_pid = next_pid
            self.lock_log.append(
                f"[UNLOCK]  PID {pid} liberó '{self.name}' → transferido a PID {next_pid}"
            )
        else:
            self.locked    = False
            self.owner_pid = None
            self.lock_log.append(f"[UNLOCK]  PID {pid} liberó '{self.name}' → libre")

        return next_pid

    @property
    def status_str(self) -> str:
        if self.locked:
            return f"LOCKED por PID {self.owner_pid} ({len(self.wait_queue)} esperando)"
        return "LIBRE"


class SimSemaphore:
    """
    Semáforo de conteo simulado — permite N lectores simultáneos.

    count inicial = MAX_CONCURRENT_READ (ej. 3).
    Cada acquire() decrementa count; release() lo incrementa.
    Si count == 0, el proceso debe esperar.
    """

    def __init__(self, name: str, initial: int = MAX_CONCURRENT_READ):
        self.name       : str       = name
        self.initial    : int       = initial
        self.count      : int       = initial
        self.holders    : List[int] = []   # PIDs con acceso activo
        self.wait_queue : List[int] = []
        self.sem_log    : List[str] = []

    def acquire(self, pid: int) -> bool:
        if self.count > 0:
            self.count -= 1
            self.holders.append(pid)
            self.sem_log.append(
                f"[SEM ACQ] PID {pid} → '{self.name}' (disponibles: {self.count}/{self.initial})"
            )
            return True
        else:
            if pid not in self.wait_queue:
                self.wait_queue.append(pid)
            self.sem_log.append(
                f"[SEM WAIT] PID {pid} bloqueado en '{self.name}' (sem=0)"
            )
            return False

    def release(self, pid: int) -> Optional[int]:
        if pid in self.holders:
            self.holders.remove(pid)
            self.count = min(self.count + 1, self.initial)
            next_pid = None
            if self.wait_queue:
                next_pid = self.wait_queue.pop(0)
                self.holders.append(next_pid)
                self.count -= 1
                self.sem_log.append(
                    f"[SEM REL] PID {pid} liberó '{self.name}' → PID {next_pid} desbloqueado"
                )
            else:
                self.sem_log.append(
                    f"[SEM REL] PID {pid} liberó '{self.name}' (disponibles: {self.count}/{self.initial})"
                )
            return next_pid
        return None

    @property
    def status_str(self) -> str:
        return f"count={self.count}/{self.initial}, lectores={self.holders}"
