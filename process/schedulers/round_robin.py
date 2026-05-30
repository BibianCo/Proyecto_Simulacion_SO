"""
process/schedulers/round_robin.py - Algoritmo Round Robin.

Idea central: cada proceso recibe exactamente `quantum` ticks de CPU.
Si no termina, vuelve al final de la cola. Justo pero no óptimo para procesos cortos.

Ventaja pedagógica: demuestra preempción y equidad.
"""
from collections import deque
from typing import List, Optional, Tuple

from process.process import Process
from core.enums import ProcessState
from config import DEFAULT_QUANTUM


class RoundRobinScheduler:
    """
    Planificador Round Robin con quantum configurable.

    Atributos:
        quantum      : Ticks máximos por proceso antes de preempción
        ready_queue  : Cola FIFO de procesos listos (deque para eficiencia O(1))
        current      : Proceso actualmente en CPU (None si CPU libre)
        ticks_used   : Ticks que lleva usando CPU el proceso actual
        current_tick : Reloj global de la simulación
        finished     : Lista de procesos que completaron ejecución
    """

    def __init__(self, quantum: int = DEFAULT_QUANTUM):
        self.quantum      : int              = quantum
        self.ready_queue  : deque[Process]   = deque()
        self.current      : Optional[Process] = None
        self.ticks_used   : int              = 0
        self.current_tick : int              = 0
        self.finished     : List[Process]    = []

    def add_process(self, process: Process):
        """Agrega un proceso a la cola ready."""
        process.to_ready(self.current_tick)
        self.ready_queue.append(process)

    def step(self) -> Tuple[Optional[Process], str]:
        """
        Avanza un tick de simulación.
        Retorna (proceso_en_cpu, evento_string) para que la UI lo muestre.

        Lógica:
        1. Si hay proceso en CPU y alcanzó quantum → preempt, volver a cola
        2. Si no hay proceso en CPU → tomar primero de la cola
        3. Ejecutar tick del proceso actual
        4. Actualizar wait_ticks de los procesos en cola
        """
        self.current_tick += 1
        event = ""

        # Incrementar wait_ticks de todos en cola
        for p in self.ready_queue:
            p.wait_ticks += 1

        # Preempción por quantum agotado
        if self.current and self.ticks_used >= self.quantum:
            event = f"[PREEMPT] P{self.current.pid} ({self.current.name}) regresa a cola"
            self.current.to_ready(self.current_tick)
            self.ready_queue.append(self.current)
            self.current = None
            self.ticks_used = 0

        # Asignar CPU si está libre
        if self.current is None and self.ready_queue:
            self.current = self.ready_queue.popleft()
            self.current.to_running(self.current_tick)
            event += f" → CPU asignada a P{self.current.pid} ({self.current.name})"

        # Ejecutar tick
        if self.current:
            self.ticks_used += 1
            finished = self.current.tick()
            if finished:
                self.current.to_finished(self.current_tick)
                self.finished.append(self.current)
                event = f"[FIN] P{self.current.pid} ({self.current.name}) terminó en tick {self.current_tick}"
                self.current = None
                self.ticks_used = 0
        else:
            event = "[CPU IDLE] No hay procesos en cola"

        return self.current, event.strip()

    def is_done(self) -> bool:
        """True cuando no hay nada más que ejecutar."""
        return self.current is None and len(self.ready_queue) == 0

    def queue_snapshot(self) -> List[Process]:
        """Retorna copia de la cola ready para mostrar en UI."""
        return list(self.ready_queue)
