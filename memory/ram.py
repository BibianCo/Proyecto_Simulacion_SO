"""
memory/ram.py - Simulación de RAM usando marcos de página (page frames).

Conceptos implementados:
  - Memoria dividida en N marcos de tamaño fijo
  - Cada marco puede estar libre u ocupado por (pid, num_pagina)
  - Registra page faults cada vez que se carga una página nueva
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict

from core.enums import PageState
from core.exceptions import MemoryFullError
from config import TOTAL_FRAMES


@dataclass
class Frame:
    """
    Un marco de página en RAM.
    frame_id : índice del marco (0 a TOTAL_FRAMES-1)
    pid      : proceso dueño (None si libre)
    page_num : número de página del proceso (None si libre)
    state    : FREE u OCCUPIED
    """
    frame_id : int
    pid      : Optional[int] = None
    page_num : Optional[int] = None
    state    : PageState     = PageState.FREE

    def occupy(self, pid: int, page_num: int):
        self.pid      = pid
        self.page_num = page_num
        self.state    = PageState.OCCUPIED

    def free(self):
        self.pid      = None
        self.page_num = None
        self.state    = PageState.FREE

    @property
    def is_free(self) -> bool:
        return self.state == PageState.FREE


class RAM:
    """
    Memoria RAM simulada con N marcos de página.

    Atributos:
        frames      : Lista de todos los marcos
        page_faults : Contador de fallos de página ocurridos
        total_loads : Contador de páginas cargadas exitosamente
    """

    def __init__(self, total_frames: int = TOTAL_FRAMES):
        self.frames      : List[Frame] = [Frame(i) for i in range(total_frames)]
        self.page_faults : int         = 0
        self.total_loads : int         = 0

    # ── Consultas ─────────────────────────────────────────────────────

    def find_frame(self, pid: int, page_num: int) -> Optional[Frame]:
        """Busca si una página ya está en RAM (hit). O(N)."""
        for f in self.frames:
            if f.pid == pid and f.page_num == page_num:
                return f
        return None

    def free_frames(self) -> List[Frame]:
        """Devuelve lista de marcos libres."""
        return [f for f in self.frames if f.is_free]

    def occupied_frames(self) -> List[Frame]:
        """Devuelve lista de marcos ocupados."""
        return [f for f in self.frames if not f.is_free]

    def frames_by_process(self, pid: int) -> List[Frame]:
        """Marcos que pertenecen a un proceso específico."""
        return [f for f in self.frames if f.pid == pid]

    # ── Operaciones ───────────────────────────────────────────────────

    def load_page(self, pid: int, page_num: int) -> tuple[Frame, bool]:
        """
        Carga la página (pid, page_num) en RAM.
        Retorna (frame_usado, hubo_page_fault).
        Lanza MemoryFullError si no hay marcos libres (el reemplazo debe manejarlo).
        """
        # ¿Ya está en RAM? → hit, sin fallo
        existing = self.find_frame(pid, page_num)
        if existing:
            return existing, False   # Page hit

        # Page fault: la página no está en RAM
        self.page_faults += 1
        free = self.free_frames()
        if not free:
            raise MemoryFullError(
                f"RAM llena ({len(self.frames)} marcos). "
                "Usa un algoritmo de reemplazo primero."
            )
        frame = free[0]
        frame.occupy(pid, page_num)
        self.total_loads += 1
        return frame, True   # Page fault resuelto

    def evict_frame(self, frame_id: int):
        """Libera un marco específico (llamado por algoritmos de reemplazo)."""
        self.frames[frame_id].free()

    def free_process_pages(self, pid: int):
        """Libera todos los marcos de un proceso (cuando el proceso termina)."""
        for f in self.frames_by_process(pid):
            f.free()

    # ── Estadísticas ──────────────────────────────────────────────────

    @property
    def occupancy_pct(self) -> float:
        """Porcentaje de marcos ocupados."""
        return round(len(self.occupied_frames()) / len(self.frames) * 100, 1)

    @property
    def fault_rate(self) -> float:
        """Tasa de fallos: page_faults / total intentos de carga."""
        total = self.page_faults + self.total_loads
        return round(self.page_faults / total * 100, 1) if total > 0 else 0.0

    def snapshot(self) -> List[Dict]:
        """Retorna estado de todos los marcos como lista de dicts (para UI)."""
        return [
            {
                "frame": f.frame_id,
                "estado": "ocupado" if not f.is_free else "libre",
                "pid": f.pid,
                "pagina": f.page_num
            }
            for f in self.frames
        ]
