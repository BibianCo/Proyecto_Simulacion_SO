"""
ui/console_ui.py - Interfaz de consola del simulador de SO.

Responsabilidades:
  - Menú principal de navegación
  - Visualización de cola de procesos, CPU, memoria y archivos
  - Tablas formateadas con colores
  - Presentación de métricas al finalizar
"""
import os
import time
from typing import List, Optional, Any

from ui.colors import (colored, success, warning, error, info, dim, highlight,
                        state_colored, CYAN, BLUE, YELLOW, GREEN, RED, GRAY,
                        BOLD, RESET)


# ── Utilidades de display ──────────────────────────────────────────────────────

def clear():
    """Limpia la terminal (funciona en Windows y Linux/macOS)."""
    os.system('cls' if os.name == 'nt' else 'clear')


def divider(char: str = "─", width: int = 70, color: str = GRAY) -> str:
    return colored(char * width, color)


def header(title: str, width: int = 70) -> str:
    pad  = (width - len(title) - 2) // 2
    line = "═" * width
    return (
        f"\n{colored(line, CYAN)}\n"
        f"{colored('║', CYAN)}{' ' * pad}"
        f"{colored(title, CYAN, bold=True)}"
        f"{' ' * pad}{colored('║', CYAN)}\n"
        f"{colored(line, CYAN)}"
    )


def section(title: str) -> str:
    return f"\n{colored('▌ ' + title, YELLOW, bold=True)}\n{divider('─', 50)}"


# ── Tablas ─────────────────────────────────────────────────────────────────────

def format_table(rows: List[dict], max_col_width: int = 16) -> str:
    """
    Formatea una lista de dicts como tabla ASCII alineada.
    Todos los dicts deben tener las mismas keys.
    """
    if not rows:
        return dim("  (sin datos)")

    cols   = list(rows[0].keys())
    widths = {c: max(len(str(c)), max(len(str(r.get(c, ""))) for r in rows))
              for c in cols}
    widths = {c: min(w, max_col_width) for c, w in widths.items()}

    def fmt_cell(val: Any, col: str) -> str:
        s = str(val)[:max_col_width]
        return s.ljust(widths[col])

    sep  = "┼".join("─" * (w + 2) for w in widths.values())
    sep  = "├" + sep + "┤"
    top  = "┬".join("─" * (w + 2) for w in widths.values())
    top  = "┌" + top + "┐"
    bot  = "┴".join("─" * (w + 2) for w in widths.values())
    bot  = "└" + bot + "┘"

    header_row = "│" + "│".join(
        f" {colored(col.center(widths[col]), CYAN)} " for col in cols
    ) + "│"

    data_rows = []
    for row in rows:
        cells = []
        for col in cols:
            val   = row.get(col, "")
            cell  = fmt_cell(val, col)
            # Colorear columna Estado si existe
            if col.lower() in ("estado", "state") and isinstance(val, str):
                cell = state_colored(val).ljust(widths[col] + 10)
            cells.append(f" {cell} ")
        data_rows.append("│" + "│".join(cells) + "│")

    lines = [top, header_row, sep] + data_rows + [bot]
    return "\n".join(lines)


# ── Vistas específicas ─────────────────────────────────────────────────────────

def show_process_panel(ready_queue, current_process, finished_list):
    """
    Muestra el panel de gestión de procesos:
      - Cola Ready
      - Proceso en CPU
      - Procesos terminados
    """
    print(section("GESTIÓN DE PROCESOS"))

    # CPU
    print(f"\n  {colored('CPU:', BLUE, bold=True)}", end=" ")
    if current_process:
        bar_len = 20
        filled  = int((1 - current_process.remaining / current_process.burst_time) * bar_len)
        bar     = success("█" * filled) + dim("░" * (bar_len - filled))
        print(
            f"{success(current_process.name)} "
            f"[PID:{current_process.pid}] "
            f"[{bar}] {current_process.progress_pct}%  "
            f"restante:{current_process.remaining}"
        )
    else:
        print(warning("IDLE"))

    # Cola Ready
    print(f"\n  {colored('Cola Ready:', YELLOW, bold=True)}", end=" ")
    if ready_queue:
        items = [
            f"{YELLOW}({p.name}/P{p.pid}){RESET}" for p in ready_queue
        ]
        print(" → ".join(items))
    else:
        print(dim("vacía"))

    # Tabla de procesos terminados
    if finished_list:
        print(f"\n  {colored('Terminados:', GRAY, bold=True)}")
        rows = [
            {"PID": p.pid, "Nombre": p.name,
             "Burst": p.burst_time, "Espera": p.wait_ticks,
             "Fin": p.finish_time}
            for p in finished_list
        ]
        for line in format_table(rows).splitlines():
            print("  " + line)


def show_memory_panel(ram, page_tables: dict = None):
    """Muestra el estado de RAM: marcos ocupados, libres y fallos de página."""
    print(section("GESTIÓN DE MEMORIA"))

    frames = ram.snapshot()
    print(f"\n  Marcos totales: {len(frames)}   "
          f"Ocupados: {colored(str(len(ram.occupied_frames())), RED, bold=True)}   "
          f"Libres: {colored(str(len(ram.free_frames())), GREEN, bold=True)}   "
          f"Page faults: {colored(str(ram.page_faults), RED, bold=True)}   "
          f"Ocupación: {ram.occupancy_pct}%")

    # Mapa visual de marcos
    print()
    row = "  "
    for f in frames:
        if f["estado"] == "ocupado":
            label = f"[P{f['pid']}:pg{f['pagina']}]"
            row  += colored(label.center(11), GREEN)
        else:
            row  += colored("[  libre  ]".center(11), GRAY)
        if (f["frame"] + 1) % 4 == 0:
            print(row)
            row = "  "
    if row.strip():
        print(row)


def show_filesystem_panel(file_manager):
    """Muestra estado de archivos: locks, lectores, escritores y log."""
    print(section("GESTIÓN DE ARCHIVOS"))

    statuses = file_manager.all_files_status()
    if not statuses:
        print(dim("  Sin archivos creados"))
        return

    rows = []
    for s in statuses:
        escritor   = str(s["escritor"])   if s["escritor"]   else "-"
        lectores   = str(s["lectores"])   if s["lectores"]   else "-"
        en_espera  = str(s["en_espera_write"] + s["en_espera_read"])
        rows.append({
            "Archivo"  : s["nombre"],
            "Tamaño"   : s["tamaño"],
            "Escritor" : escritor,
            "Lectores" : lectores,
            "En espera": en_espera,
        })
    for line in format_table(rows).splitlines():
        print("  " + line)

    # Log reciente (últimas 8 entradas)
    if file_manager.access_log:
        print(f"\n  {colored('Log de accesos (últimos 8):', CYAN)}")
        for entry in file_manager.access_log[-8:]:
            if "CONFLICT" in entry:
                print("  " + error(entry))
            elif "FIN" in entry or "UNLOCK" in entry or "UNBLOCK" in entry:
                print("  " + success(entry))
            elif "WAIT" in entry:
                print("  " + warning(entry))
            else:
                print("  " + info(entry))


def show_metrics_panel(metrics_rows: list, averages: dict):
    """Muestra tabla de métricas y promedios."""
    print(section("MÉTRICAS DEL SISTEMA"))
    if not metrics_rows:
        print(dim("  Sin procesos terminados aún"))
        return

    for line in format_table(metrics_rows).splitlines():
        print("  " + line)

    print(f"\n  {colored('Promedios:', CYAN, bold=True)}")
    for key, val in averages.items():
        label = key.replace("_", " ").capitalize()
        print(f"    {label:<22}: {colored(str(val), YELLOW, bold=True)}")


# ── Menú principal ─────────────────────────────────────────────────────────────

def main_menu() -> str:
    """Muestra menú y retorna la opción elegida."""
    print(f"\n{divider('─', 50)}")
    options = [
        ("1", "Gestión de Procesos"),
        ("2", "Gestión de Memoria"),
        ("3", "Sistema de Archivos"),
        ("4", "Demostración Completa (auto)"),
        ("0", "Salir"),
    ]
    for key, label in options:
        print(f"  {colored('[' + key + ']', CYAN)} {label}")
    return input(f"\n{colored('Opción ▶', YELLOW)} ").strip()


def pause(msg: str = "Presiona Enter para continuar..."):
    input(f"\n{dim(msg)}")
