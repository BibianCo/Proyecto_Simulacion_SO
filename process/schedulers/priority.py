"""
process/schedulers/priority.py - Planificador por Prioridad (no preemptivo).

Idea: el proceso con mayor prioridad siempre obtiene CPU primero.
Si dos tienen la misma prioridad, se desempata por orden de llegada (FIFO).

También incluye SJF (Shortest Job First): el proceso con menor burst_time
restante va primero. Reduce el tiempo promedio de espera, pero puede provocar
inanición (starvation) en procesos largos.
"""
from typing import List, Optional, Tuple

from process.process import Process
from core.enums import ProcessState


class PriorityScheduler:
    """
    Planificador por Prioridad — no preemptivo.
    Una vez que un proceso obtiene CPU, lo mantiene hasta terminar.

    Orden: priority descendente → arrival_time ascendente (desempate)
    """

    def __init__(self):
        self.ready_queue  : List[Process]     = []
        self.current      : Optional[Process] = None
        self.current_tick : int               = 0
        self.finished     : List[Process]     = []

    def add_process(self, process: Process):
        """Agrega proceso y re-ordena la cola por prioridad."""
        process.to_ready(self.current_tick)
        self.ready_queue.append(process)
        self._sort_queue()

    def _sort_queue(self):
        """Ordena: mayor prioridad primero, FIFO como desempate."""
        self.ready_queue.sort(key=lambda p: (-p.priority, p.arrival_time))

    def step(self) -> Tuple[Optional[Process], str]:
        """Avanza un tick. Sin preempción: el proceso actual no se interrumpe."""
        self.current_tick += 1
        event = ""

        # Incrementar espera de procesos en cola
        for p in self.ready_queue:
            p.wait_ticks += 1

        # Asignar CPU si está libre
        if self.current is None and self.ready_queue:
            self.current = self.ready_queue.pop(0)
            self.current.to_running(self.current_tick)
            event = f"CPU → P{self.current.pid} (prioridad {self.current.priority})"

        # Ejecutar tick
        if self.current:
            finished = self.current.tick()
            if finished:
                self.current.to_finished(self.current_tick)
                self.finished.append(self.current)
                event = f"[FIN] P{self.current.pid} terminó. Prioridad fue {self.current.priority}"
                self.current = None
        else:
            event = "[IDLE] Cola vacía"

        return self.current, event

    def is_done(self) -> bool:
        return self.current is None and len(self.ready_queue) == 0

    def queue_snapshot(self) -> List[Process]:
        return list(self.ready_queue)


class SJFScheduler:
    """
    Shortest Job First — no preemptivo.
    Escoge el proceso con menor `remaining` (tiempo restante).
    Óptimo para minimizar waiting time promedio, pero puede causar starvation.
    """

    def __init__(self):
        self.ready_queue  : List[Process]     = []
        self.current      : Optional[Process] = None
        self.current_tick : int               = 0
        self.finished     : List[Process]     = []

    def add_process(self, process: Process):
        process.to_ready(self.current_tick)
        self.ready_queue.append(process)
        self._sort_queue()

    def _sort_queue(self):
        """Ordena por tiempo restante ascendente (proceso más corto primero)."""
        self.ready_queue.sort(key=lambda p: (p.remaining, p.arrival_time))

    def step(self) -> Tuple[Optional[Process], str]:
        self.current_tick += 1
        event = ""

        for p in self.ready_queue:
            p.wait_ticks += 1

        if self.current is None and self.ready_queue:
            self.current = self.ready_queue.pop(0)
            self.current.to_running(self.current_tick)
            event = f"CPU → P{self.current.pid} (burst restante: {self.current.remaining})"

        if self.current:
            finished = self.current.tick()
            if finished:
                self.current.to_finished(self.current_tick)
                self.finished.append(self.current)
                event = f"[FIN] P{self.current.pid} terminó (SJF)"
                self.current = None
        else:
            event = "[IDLE] Cola vacía"

        return self.current, event

    def is_done(self) -> bool:
        return self.current is None and len(self.ready_queue) == 0

    def queue_snapshot(self) -> List[Process]:
        return list(self.ready_queue)
