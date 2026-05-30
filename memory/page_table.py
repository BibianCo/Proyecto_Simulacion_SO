"""
memory/page_table.py - Tabla de páginas por proceso.

Cada proceso tiene su propia tabla que mapea:
  número_de_página_virtual → (frame_id | None si no está en RAM)

Esto simula la MMU (Memory Management Unit) de un SO real.
"""
from typing import Dict, Optional, List


class PageTable:
    """
    Tabla de páginas de un proceso.

    page_map: { page_num: frame_id } → si frame_id es None, la página no está cargada.
    """

    def __init__(self, pid: int, num_pages: int):
        """
        pid       : PID del proceso dueño
        num_pages : Número de páginas virtuales que tiene el proceso
        """
        self.pid      : int                          = pid
        self.num_pages: int                          = num_pages
        # Inicialmente ninguna página está en RAM
        self.page_map : Dict[int, Optional[int]]     = {i: None for i in range(num_pages)}
        self.access_count : Dict[int, int]           = {i: 0 for i in range(num_pages)}

    def update(self, page_num: int, frame_id: Optional[int]):
        """Actualiza la entrada de la tabla para page_num."""
        if page_num not in self.page_map:
            raise KeyError(f"Proceso {self.pid} no tiene página {page_num}")
        self.page_map[page_num] = frame_id
        if frame_id is not None:
            self.access_count[page_num] += 1

    def is_loaded(self, page_num: int) -> bool:
        """True si la página está actualmente en RAM."""
        return self.page_map.get(page_num) is not None

    def invalidate(self, frame_id: int):
        """Marca como no cargada la entrada que apuntaba a frame_id."""
        for page, frame in self.page_map.items():
            if frame == frame_id:
                self.page_map[page] = None

    def loaded_pages(self) -> List[int]:
        """Lista de números de páginas actualmente en RAM."""
        return [p for p, f in self.page_map.items() if f is not None]

    def snapshot(self) -> List[Dict]:
        return [
            {"pagina": p, "frame": f, "en_ram": f is not None, "accesos": self.access_count[p]}
            for p, f in self.page_map.items()
        ]
