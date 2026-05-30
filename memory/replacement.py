"""
memory/replacement.py - Algoritmos de reemplazo de páginas.

Cuando RAM está llena y hay un page fault, estos algoritmos deciden
qué página expulsar para hacer espacio.

Implementados:
  - FIFO  : First In, First Out — expulsa la página más antigua
  - LRU   : Least Recently Used — expulsa la página sin usar por más tiempo
"""
from collections import deque, OrderedDict
from typing import Tuple

from memory.ram import RAM, Frame
from core.exceptions import MemoryFullError


class FIFOReplacement:
    """
    FIFO — First In, First Out.

    Mantiene una cola de marcos en orden de carga.
    Al necesitar espacio, expulsa el que lleva más tiempo en RAM.

    Ventaja : simple, fácil de implementar.
    Desventaja: puede expulsar páginas muy usadas (anomalía de Bélady).
    """

    def __init__(self, ram: RAM):
        self.ram    : RAM              = ram
        # Cola FIFO de frame_ids en orden de carga
        self._queue : deque[int]       = deque()
        # Precarga la cola con marcos ya ocupados (si los hay)
        for f in ram.occupied_frames():
            self._queue.append(f.frame_id)

    def access(self, pid: int, page_num: int) -> Tuple[Frame, bool]:
        """
        Accede a una página. Si no está en RAM, aplica FIFO para hacer espacio.
        Retorna (frame, hubo_page_fault).
        """
        # Intentar cargar directamente
        try:
            frame, fault = self.ram.load_page(pid, page_num)
            if fault:
                self._queue.append(frame.frame_id)   # Registrar en FIFO
            return frame, fault
        except MemoryFullError:
            pass

        # RAM llena → expulsar el más antiguo (frente de la cola)
        victim_id = self._queue.popleft()
        victim     = self.ram.frames[victim_id]
        evicted_info = f"P{victim.pid} pág.{victim.page_num}"
        self.ram.evict_frame(victim_id)

        # Ahora cargar la nueva página
        frame, fault = self.ram.load_page(pid, page_num)
        self._queue.append(frame.frame_id)
        return frame, fault

    def reset(self):
        self._queue.clear()


class LRUReplacement:
    """
    LRU — Least Recently Used.

    Usa un OrderedDict: las claves son frame_ids, ordenadas por último acceso.
    La primera entrada es la menos recientemente usada → víctima.

    Ventaja : más cercano al comportamiento óptimo que FIFO.
    Desventaja: overhead de tracking del orden de acceso.
    """

    def __init__(self, ram: RAM):
        self.ram    : RAM              = ram
        # OrderedDict: {frame_id: True}, orden = más antiguo al frente
        self._order : OrderedDict[int, bool] = OrderedDict()
        for f in ram.occupied_frames():
            self._order[f.frame_id] = True

    def access(self, pid: int, page_num: int) -> Tuple[Frame, bool]:
        """
        Accede a una página y actualiza el orden LRU.
        """
        existing = self.ram.find_frame(pid, page_num)
        if existing:
            # Hit: mover al final (más recientemente usado)
            self._order.move_to_end(existing.frame_id)
            return existing, False

        # Page fault
        try:
            frame, fault = self.ram.load_page(pid, page_num)
            self._order[frame.frame_id] = True   # Añadir al final
            return frame, fault
        except MemoryFullError:
            pass

        # RAM llena → expulsar el LRU (primero del OrderedDict)
        victim_id, _ = self._order.popitem(last=False)
        self.ram.evict_frame(victim_id)

        frame, fault = self.ram.load_page(pid, page_num)
        self._order[frame.frame_id] = True
        return frame, fault

    def reset(self):
        self._order.clear()
