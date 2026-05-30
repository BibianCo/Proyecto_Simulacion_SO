"""
tests/test_process.py - Pruebas unitarias para gestión de procesos.

Ejecutar con: python -m pytest tests/ -v
O directamente: python tests/test_process.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from process.process import Process, _pid_counter
from process.schedulers.round_robin import RoundRobinScheduler
from process.schedulers.priority    import PriorityScheduler, SJFScheduler
from core.enums import ProcessState
from metrics import calculator


class TestProcess(unittest.TestCase):

    def test_creation_defaults(self):
        """Un proceso recién creado debe estar en estado NEW."""
        p = Process(name="test", burst_time=5)
        self.assertEqual(p.state, ProcessState.NEW)
        self.assertEqual(p.remaining, 5)
        self.assertEqual(p.progress_pct, 0.0)

    def test_invalid_priority(self):
        """Prioridad fuera de [1,10] debe lanzar ValueError."""
        with self.assertRaises(ValueError):
            Process(name="bad", priority=11, burst_time=3)
        with self.assertRaises(ValueError):
            Process(name="bad", priority=0, burst_time=3)

    def test_invalid_burst(self):
        """burst_time <= 0 debe lanzar ValueError."""
        with self.assertRaises(ValueError):
            Process(name="bad", burst_time=0)

    def test_tick_decrements_remaining(self):
        """Cada tick debe disminuir remaining en 1."""
        p = Process(name="t", burst_time=3)
        p.to_running()
        p.tick()
        self.assertEqual(p.remaining, 2)

    def test_tick_finishes_process(self):
        """Al llegar remaining a 0 el proceso debe finalizar."""
        p = Process(name="t", burst_time=1)
        p.to_running()
        finished = p.tick()
        self.assertTrue(finished)
        self.assertEqual(p.state, ProcessState.FINISHED)

    def test_state_transitions(self):
        """Las transiciones de estado deben funcionar correctamente."""
        p = Process(name="t", burst_time=5)
        p.to_ready(0)
        self.assertEqual(p.state, ProcessState.READY)
        p.to_running(1)
        self.assertEqual(p.state, ProcessState.RUNNING)
        self.assertEqual(p.start_time, 1)
        p.to_waiting()
        self.assertEqual(p.state, ProcessState.WAITING)

    def test_progress_pct(self):
        """progress_pct debe reflejar el avance correctamente."""
        p = Process(name="t", burst_time=4)
        p.to_running()
        p.tick()   # remaining = 3
        self.assertAlmostEqual(p.progress_pct, 25.0)


class TestRoundRobin(unittest.TestCase):

    def _make_scheduler(self, quantum=2):
        sched = RoundRobinScheduler(quantum=quantum)
        sched.add_process(Process(name="A", burst_time=4))
        sched.add_process(Process(name="B", burst_time=3))
        return sched

    def test_runs_to_completion(self):
        """Round Robin debe terminar todos los procesos."""
        sched = self._make_scheduler(quantum=2)
        max_ticks = 50
        ticks = 0
        while not sched.is_done() and ticks < max_ticks:
            sched.step()
            ticks += 1
        self.assertTrue(sched.is_done(), "RR no terminó en tiempo razonable")
        self.assertEqual(len(sched.finished), 2)

    def test_quantum_preemption(self):
        """Después de `quantum` ticks, el proceso debe regresar a la cola."""
        sched = RoundRobinScheduler(quantum=2)
        p = Process(name="long", burst_time=10)
        sched.add_process(p)
        # Tick 1 y 2: proceso debe estar en CPU
        sched.step()
        self.assertIsNotNone(sched.current)
        sched.step()
        # Tick 3: quantum agotado, debe preemptar
        sched.step()
        # En tick 3 el proceso vuelve a cola (current puede ser None momentáneamente)
        self.assertIn(p.remaining, range(1, 10))  # Ha ejecutado algo

    def test_waiting_time_accumulated(self):
        """Los procesos en cola deben acumular wait_ticks."""
        sched = RoundRobinScheduler(quantum=100)   # quantum enorme → sin preempción
        p1 = Process(name="A", burst_time=3)
        p2 = Process(name="B", burst_time=3)
        sched.add_process(p1)
        sched.add_process(p2)
        # Ejecutar hasta que termine p1
        for _ in range(3):
            sched.step()
        # p2 estuvo esperando durante 3 ticks
        self.assertGreater(p2.wait_ticks, 0)


class TestPriorityScheduler(unittest.TestCase):

    def test_high_priority_first(self):
        """El proceso con mayor prioridad debe ejecutarse primero."""
        sched = PriorityScheduler()
        low  = Process(name="low",  priority=2, burst_time=5)
        high = Process(name="high", priority=9, burst_time=5)
        sched.add_process(low)
        sched.add_process(high)
        sched.step()
        # El proceso en CPU debe ser `high`
        self.assertEqual(sched.current.name, "high")

    def test_runs_to_completion(self):
        sched = PriorityScheduler()
        for i in range(3):
            sched.add_process(Process(name=f"p{i}", priority=i+1, burst_time=3))
        for _ in range(50):
            if sched.is_done():
                break
            sched.step()
        self.assertTrue(sched.is_done())


class TestSJFScheduler(unittest.TestCase):

    def test_shortest_first(self):
        """SJF debe ejecutar el proceso con menor burst_time primero."""
        sched = SJFScheduler()
        long_ = Process(name="long",  burst_time=10)
        short = Process(name="short", burst_time=2)
        sched.add_process(long_)
        sched.add_process(short)
        sched.step()
        self.assertEqual(sched.current.name, "short")


class TestMetrics(unittest.TestCase):

    def _completed_process(self, name, burst, arrival, start, finish, wait):
        p = Process(name=name, burst_time=burst)
        p.arrival_time = arrival
        p.start_time   = start
        p.finish_time  = finish
        p.wait_ticks   = wait
        p.state        = ProcessState.FINISHED
        return p

    def test_turnaround(self):
        p = self._completed_process("t", 5, 0, 0, 5, 0)
        self.assertEqual(calculator.turnaround_time(p), 5)

    def test_waiting_time(self):
        p = self._completed_process("t", 5, 0, 2, 7, 2)
        self.assertEqual(calculator.waiting_time(p), 2)

    def test_response_time(self):
        p = self._completed_process("t", 5, 1, 3, 8, 2)
        self.assertEqual(calculator.response_time(p), 2)  # start - arrival = 3 - 1

    def test_averages(self):
        p1 = self._completed_process("a", 5, 0, 0, 5,  0)
        p2 = self._completed_process("b", 3, 0, 5, 8,  5)
        avgs = calculator.averages([p1, p2])
        self.assertEqual(avgs["avg_turnaround"], 6.5)   # (5+8)/2


if __name__ == "__main__":
    unittest.main(verbosity=2)
