"""
config.py - Configuración global del simulador de SO
Centraliza todas las constantes para facilitar ajustes sin tocar lógica.
"""

# ─────────────────────────────────────────────
# Gestión de Procesos
# ─────────────────────────────────────────────
MAX_PROCESSES       = 20          # Máximo de procesos simultáneos
DEFAULT_QUANTUM     = 3           # Quantum (time slice) para Round Robin, en "ticks"
MAX_PRIORITY        = 10          # Prioridad más alta (1 = más baja, 10 = más alta)
DEFAULT_BURST_TIME  = 5           # Tiempo de ráfaga por defecto si no se especifica

# ─────────────────────────────────────────────
# Gestión de Memoria
# ─────────────────────────────────────────────
TOTAL_FRAMES        = 8           # Marcos de página disponibles en RAM simulada
PAGE_SIZE           = 4           # Tamaño de cada página en KB (simbólico)
MAX_PAGES_PER_PROC  = 6           # Máximo de páginas que puede tener un proceso

# ─────────────────────────────────────────────
# Sistema de Archivos
# ─────────────────────────────────────────────
MAX_FILES           = 10          # Número máximo de archivos simulados
MAX_CONCURRENT_READ = 3           # Lectores simultáneos permitidos (semáforo)

# ─────────────────────────────────────────────
# Interfaz / Simulación
# ─────────────────────────────────────────────
TICK_DELAY          = 0.05        # Segundos entre ticks de simulación (para velocidad visual)
DEMO_MODE           = True        # Si True, pre-carga escenarios de demostración
