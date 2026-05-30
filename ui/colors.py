"""
ui/colors.py - Constantes de color ANSI para terminal.
Centraliza todos los códigos de escape para que console_ui.py sea legible.
"""

# Estilos base
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"

# Colores de texto
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
CYAN    = "\033[96m"
WHITE   = "\033[97m"
GRAY    = "\033[90m"

# Fondos
BG_RED    = "\033[41m"
BG_GREEN  = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE   = "\033[44m"

# Helpers
def colored(text: str, color: str, bold: bool = False) -> str:
    prefix = BOLD if bold else ""
    return f"{prefix}{color}{text}{RESET}"

def success(text: str) -> str:   return colored(text, GREEN,   bold=True)
def warning(text: str) -> str:   return colored(text, YELLOW)
def error(text: str)   -> str:   return colored(text, RED,     bold=True)
def info(text: str)    -> str:   return colored(text, CYAN)
def dim(text: str)     -> str:   return colored(text, GRAY)
def highlight(text: str) -> str: return colored(text, MAGENTA, bold=True)

# Mapa de color por estado de proceso
STATE_COLORS = {
    "new"      : BLUE,
    "ready"    : YELLOW,
    "running"  : GREEN,
    "waiting"  : MAGENTA,
    "finished" : GRAY,
}

def state_colored(state_value: str) -> str:
    color = STATE_COLORS.get(state_value, WHITE)
    return colored(state_value.upper(), color, bold=(state_value == "running"))
