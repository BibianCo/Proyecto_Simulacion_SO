"""
metrics/calculator.py - Cálculo de métricas de planificación.

Métricas estándar de sistemas operativos:

  Turnaround Time  = finish_time - arrival_time
      (tiempo total desde que llega hasta que termina)

  Waiting Time     = wait_ticks acumulados en cola ready
      (tiempo que el proceso esperó sin ejecutar)

  Response Time    = start_time - arrival_time
      (tiempo hasta que el proceso recibió CPU por primera vez)
      Importante para sistemas interactivos.

  CPU Throughput   = procesos_terminados / ticks_totales
      (cuántos procesos por tick completa el sistema)
"""
from typing import List, Dict, Optional
from process.process import Process


def turnaround_time(p: Process) -> Optional[int]:
    """Tiempo total en el sistema. None si el proceso no terminó."""
    if p.finish_time is None:
        return None
    return p.finish_time - p.arrival_time


def waiting_time(p: Process) -> int:
    """Tiempo acumulado en cola ready sin ejecutar."""
    return p.wait_ticks


def response_time(p: Process) -> Optional[int]:
    """Tiempo hasta la primera ejecución. None si nunca obtuvo CPU."""
    if p.start_time is None:
        return None
    return p.start_time - p.arrival_time


def compute_all(processes: List[Process]) -> List[Dict]:
    """
    Calcula las tres métricas para una lista de procesos.
    Retorna lista de dicts listos para mostrar en tabla.
    """
    rows = []
    for p in processes:
        tt = turnaround_time(p)
        wt = waiting_time(p)
        rt = response_time(p)
        rows.append({
            "PID"           : p.pid,
            "Nombre"        : p.name,
            "Llegada"       : p.arrival_time,
            "Burst"         : p.burst_time,
            "Inicio"        : p.start_time if p.start_time is not None else "-",
            "Fin"           : p.finish_time if p.finish_time is not None else "-",
            "Turnaround"    : tt if tt is not None else "-",
            "Waiting"       : wt,
            "Response"      : rt if rt is not None else "-",
        })
    return rows


def averages(processes: List[Process]) -> Dict[str, float]:
    """Promedios de las métricas para el conjunto de procesos terminados."""
    finished = [p for p in processes if p.finish_time is not None]
    if not finished:
        return {"avg_turnaround": 0.0, "avg_waiting": 0.0, "avg_response": 0.0}

    avg_tt = sum(turnaround_time(p) or 0 for p in finished) / len(finished)
    avg_wt = sum(waiting_time(p)    for p in finished) / len(finished)
    avg_rt = sum(response_time(p) or 0 for p in finished) / len(finished)

    return {
        "avg_turnaround" : round(avg_tt, 2),
        "avg_waiting"    : round(avg_wt, 2),
        "avg_response"   : round(avg_rt, 2),
        "throughput"     : round(len(finished) / max(p.finish_time or 1 for p in finished), 3),
    }
