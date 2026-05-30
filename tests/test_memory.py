"""
tests/test_memory.py - Pruebas unitarias para gestión de memoria.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from memory.ram         import RAM
from memory.replacement import FIFOReplacement, LRUReplacement
from memory.page_table  import PageTable
from core.exceptions    import MemoryFullError


class TestRAM(unittest.TestCase):

    def setUp(self):
        self.ram = RAM(total_frames=4)

    def test_initial_state(self):
        """Todos los marcos deben estar libres al inicio."""
        self.assertEqual(len(self.ram.free_frames()), 4)
        self.assertEqual(len(self.ram.occupied_frames()), 0)

    def test_load_page(self):
        """Cargar una página debe ocupar un marco y generar page fault."""
        frame, fault = self.ram.load_page(pid=1, page_num=0)
        self.assertTrue(fault)
        self.assertEqual(self.ram.page_faults, 1)
        self.assertEqual(len(self.ram.free_frames()), 3)

    def test_page_hit(self):
        """Cargar la misma página dos veces no debe generar page fault."""
        self.ram.load_page(1, 0)
        frame, fault = self.ram.load_page(1, 0)
        self.assertFalse(fault)
        self.assertEqual(self.ram.page_faults, 1)   # Solo 1 fault total

    def test_memory_full_raises(self):
        """Con RAM llena sin reemplazo debe lanzar MemoryFullError."""
        for i in range(4):
            self.ram.load_page(1, i)
        with self.assertRaises(MemoryFullError):
            self.ram.load_page(1, 4)

    def test_free_process_pages(self):
        """Liberar páginas de un proceso debe dejar los marcos libres."""
        self.ram.load_page(1, 0)
        self.ram.load_page(1, 1)
        self.ram.load_page(2, 0)
        self.ram.free_process_pages(1)
        self.assertEqual(len(self.ram.frames_by_process(1)), 0)
        # Quedan libres: 4 marcos totales - 1 de P2 = 3 libres
        self.assertEqual(len(self.ram.free_frames()), 3)

    def test_occupancy_pct(self):
        self.ram.load_page(1, 0)
        self.ram.load_page(1, 1)
        self.assertEqual(self.ram.occupancy_pct, 50.0)


class TestFIFOReplacement(unittest.TestCase):

    def setUp(self):
        self.ram  = RAM(total_frames=3)
        self.fifo = FIFOReplacement(self.ram)

    def test_evicts_oldest(self):
        """FIFO debe expulsar la página más antigua al llenarse RAM."""
        # Cargar 3 páginas (llenan RAM)
        self.fifo.access(1, 0)
        self.fifo.access(1, 1)
        self.fifo.access(1, 2)
        # La cuarta debe expulsar la página 0 (la más antigua)
        frame, fault = self.fifo.access(1, 3)
        self.assertTrue(fault)
        # Página 0 ya no debe estar en RAM
        self.assertIsNone(self.ram.find_frame(1, 0))

    def test_no_fault_on_hit(self):
        self.fifo.access(1, 0)
        _, fault = self.fifo.access(1, 0)
        self.assertFalse(fault)


class TestLRUReplacement(unittest.TestCase):

    def setUp(self):
        self.ram = RAM(total_frames=3)
        self.lru = LRUReplacement(self.ram)

    def test_evicts_lru(self):
        """LRU debe expulsar la página menos recientemente usada."""
        self.lru.access(1, 0)
        self.lru.access(1, 1)
        self.lru.access(1, 2)
        # Re-acceder a página 0 (la hace la más reciente)
        self.lru.access(1, 0)
        # Cargar página 3 → debe expulsar página 1 (LRU)
        self.lru.access(1, 3)
        self.assertIsNone(self.ram.find_frame(1, 1))
        # Página 0 debe seguir en RAM
        self.assertIsNotNone(self.ram.find_frame(1, 0))


class TestPageTable(unittest.TestCase):

    def test_initially_not_loaded(self):
        pt = PageTable(pid=1, num_pages=4)
        for i in range(4):
            self.assertFalse(pt.is_loaded(i))

    def test_update_marks_loaded(self):
        pt = PageTable(pid=1, num_pages=4)
        pt.update(0, frame_id=2)
        self.assertTrue(pt.is_loaded(0))

    def test_invalidate(self):
        pt = PageTable(pid=1, num_pages=4)
        pt.update(0, frame_id=2)
        pt.invalidate(frame_id=2)
        self.assertFalse(pt.is_loaded(0))

    def test_invalid_page(self):
        pt = PageTable(pid=1, num_pages=2)
        with self.assertRaises(KeyError):
            pt.update(99, frame_id=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
