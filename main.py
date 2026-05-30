"""
main.py - Punto de entrada del Simulador de Sistema Operativo
UPTC - Ingeniería de Sistemas - Sistemas Operativos

Este archivo orquesta todos los módulos del simulador.
Cada sección del menú demuestra un concepto diferente de SO.
"""
import time
import sys

from process.process import Process
from process.schedulers.round_robin import RoundRobinScheduler
from process.schedulers.priority    import PriorityScheduler, SJFScheduler
from memory.ram                     import RAM
from memory.replacement             import FIFOReplacement, LRUReplacement
from memory.page_table              import PageTable
from filesystem.file_manager        import FileManager
from filesystem.mutex               import SimMutex
from core.enums                     import FileAccessType, SchedulerType
from metrics                        import calculator
from ui                             import console_ui as ui
from config                         import DEFAULT_QUANTUM, TOTAL_FRAMES, TICK_DELAY


# ══════════════════════════════════════════════════════════════════════════════
# Demos individuales por módulo
# ══════════════════════════════════════════════════════════════════════════════

def demo_processes(scheduler_type: SchedulerType = SchedulerType.ROUND_ROBIN):
    """Demo interactiva de gestión de procesos con el algoritmo seleccionado."""
    ui.clear()
    print(ui.header(f"SIMULADOR — {scheduler_type.value}"))

    # Crear procesos de ejemplo
    procs = [
        Process("calc",   priority=8, burst_time=6),
        Process("editor", priority=5, burst_time=4),
        Process("player", priority=3, burst_time=8),
        Process("browser",priority=7, burst_time=5),
        Process("compile",priority=9, burst_time=3),
    ]

    # Seleccionar planificador
    if scheduler_type == SchedulerType.ROUND_ROBIN:
        sched = RoundRobinScheduler(quantum=DEFAULT_QUANTUM)
        print(ui.info(f"  Quantum configurado: {DEFAULT_QUANTUM} ticks\n"))
    elif scheduler_type == SchedulerType.PRIORITY:
        sched = PriorityScheduler()
    else:
        sched = SJFScheduler()

    # Agregar todos los procesos
    for p in procs:
        sched.add_process(p)
        print(ui.dim(f"  + Proceso creado: {p}"))

    ui.pause()

    # Ciclo de simulación tick a tick
    tick = 0
    while not sched.is_done():
        tick += 1
        current, event = sched.step()

        ui.clear()
        print(ui.header(f"{scheduler_type.value} — Tick {tick}"))
        ui.show_process_panel(
            ready_queue    = sched.queue_snapshot(),
            current_process= sched.current,
            finished_list  = sched.finished
        )
        print(f"\n  {ui.info('Evento:')} {event}")
        time.sleep(TICK_DELAY * 5)   # Pausa para visualización

    # Métricas finales
    ui.clear()
    print(ui.header("MÉTRICAS FINALES"))
    all_procs = procs
    rows   = calculator.compute_all(all_procs)
    avgs   = calculator.averages(all_procs)
    ui.show_metrics_panel(rows, avgs)
    ui.pause()


def demo_memory():
    """Demo de paginación por demanda con reemplazo FIFO y LRU."""
    ui.clear()
    print(ui.header("GESTIÓN DE MEMORIA — Paginación por Demanda"))

    ram  = RAM(total_frames=TOTAL_FRAMES)
    fifo = FIFOReplacement(ram)

    # Tabla de páginas para dos procesos simulados
    pt1 = PageTable(pid=1, num_pages=5)
    pt2 = PageTable(pid=2, num_pages=4)

    # Secuencia de accesos que generará page faults
    accesses = [
        (1, 0), (1, 1), (2, 0), (1, 2), (2, 1),
        (1, 3), (2, 2), (1, 0), (2, 3), (1, 4),
        (2, 0), (1, 1), (2, 1), (1, 2),
    ]

    print(ui.info(f"\n  Marcos disponibles: {TOTAL_FRAMES}"))
    print(ui.info(f"  Algoritmo: FIFO\n"))
    print(ui.divider())

    for pid, page in accesses:
        frame, fault = fifo.access(pid, page)
        status = ui.error("PAGE FAULT") if fault else ui.success("HIT")
        print(f"  Acceso P{pid} → pág.{page}  {status}  → marco {frame.frame_id}")
        # Actualizar tabla de páginas
        pt = pt1 if pid == 1 else pt2
        pt.update(page, frame.frame_id)
        time.sleep(TICK_DELAY * 3)

    print()
    ui.show_memory_panel(ram, {1: pt1, 2: pt2})
    print(f"\n  Total page faults: {ui.error(str(ram.page_faults))}")
    print(f"  Tasa de fallos   : {ui.warning(str(ram.fault_rate) + '%')}")
    ui.pause()


def demo_filesystem():
    """Demo de acceso concurrente a archivos con mutex y semáforo."""
    ui.clear()
    print(ui.header("SISTEMA DE ARCHIVOS — Acceso Concurrente"))

    fm = FileManager()

    # Crear archivos de ejemplo
    fm.create_file("db.sql",    content="SELECT * FROM students", size_kb=12)
    fm.create_file("log.txt",   content="Server started",         size_kb=2)
    fm.create_file("config.ini",content="max_conn=100",           size_kb=1)

    # Escenario 1: Lectores concurrentes (debe funcionar OK)
    print(ui.section("Escenario 1: Lectores concurrentes"))
    ok1, msg1 = fm.open_file(101, "db.sql", FileAccessType.READ)
    ok2, msg2 = fm.open_file(102, "db.sql", FileAccessType.READ)
    ok3, msg3 = fm.open_file(103, "db.sql", FileAccessType.READ)
    print(ui.success("  " + msg1))
    print(ui.success("  " + msg2))
    print(ui.success("  " + msg3))
    time.sleep(0.3)

    # Escenario 2: Escritor mientras hay lectores (CONFLICTO)
    print(ui.section("Escenario 2: Escritor intenta entrar (CONFLICTO)"))
    ok_w, msg_w = fm.open_file(104, "db.sql", FileAccessType.WRITE)
    print(ui.error("  " + msg_w))
    time.sleep(0.3)

    # Cerrar lectores
    print(ui.section("Cerrando lectores uno a uno"))
    fm.close_file(101, "db.sql", FileAccessType.READ)
    fm.close_file(102, "db.sql", FileAccessType.READ)
    fm.close_file(103, "db.sql", FileAccessType.READ)
    print(ui.info("  Todos los lectores cerraron el archivo"))
    time.sleep(0.3)

    # Escenario 3: Escritura exclusiva
    print(ui.section("Escenario 3: Escritura exclusiva ahora posible"))
    ok_w2, msg_w2 = fm.open_file(104, "db.sql", FileAccessType.WRITE)
    print(ui.success("  " + msg_w2))
    time.sleep(0.3)
    fm.close_file(104, "db.sql", FileAccessType.WRITE)

    # Mostrar panel completo
    print()
    ui.show_filesystem_panel(fm)
    ui.pause()


def demo_full():
    """Demostración automática de todos los módulos en secuencia."""
    for algo in [SchedulerType.ROUND_ROBIN, SchedulerType.PRIORITY, SchedulerType.SJF]:
        demo_processes(algo)
    demo_memory()
    demo_filesystem()


# ══════════════════════════════════════════════════════════════════════════════
# Menú Principal
# ══════════════════════════════════════════════════════════════════════════════

def choose_scheduler() -> SchedulerType:
    print(ui.info("\n  Elegir algoritmo:"))
    print("    [1] Round Robin")
    print("    [2] Prioridad")
    print("    [3] SJF")
    opt = input(ui.colored("  Opción ▶ ", ui.YELLOW)).strip()
    return {
        "1": SchedulerType.ROUND_ROBIN,
        "2": SchedulerType.PRIORITY,
        "3": SchedulerType.SJF,
    }.get(opt, SchedulerType.ROUND_ROBIN)


def main():
    while True:
        ui.clear()
        print(ui.header("SIMULADOR DE SISTEMA OPERATIVO — UPTC Sogamoso"))
        print(ui.info("  Ingeniería de Sistemas | Sistemas Operativos\n"))

        opt = ui.main_menu()

        if opt == "1":
            algo = choose_scheduler()
            demo_processes(algo)
        elif opt == "2":
            demo_memory()
        elif opt == "3":
            demo_filesystem()
        elif opt == "4":
            # Mostrar métricas de la última sesión de procesos
            print(ui.warning("  Ejecuta primero la opción 1 para generar métricas."))
            ui.pause()
        elif opt == "5":
            demo_full()
        elif opt == "0":
            print(ui.success("\n  ¡Hasta luego!\n"))
            sys.exit(0)
        else:
            print(ui.error("  Opción no válida"))
            time.sleep(0.8)


if __name__ == "__main__":
    main()
