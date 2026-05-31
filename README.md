# 🖥️ Simulador de Sistema Operativo — Python

> Proyecto académico para la asignatura **Sistemas Operativos**  
> Universidad Pedagógica y Tecnológica de Colombia (UPTC)  
> Ingeniería de Sistemas

---

## 📋 Descripción

Este es un simulador académico de un Sistema Operativo escrito en Python 3, orientado a la
enseñanza de los tres subsistemas fundamentales:

| Módulo | Conceptos demostrados |
|---|---|
| **Gestión de Procesos** | Round Robin, Prioridad, SJF, preempción, estados de proceso |
| **Gestión de Memoria** | Paginación por demanda, FIFO, LRU, page faults |
| **Sistema de Archivos** | Acceso concurrente, mutex, semáforos, detección de conflictos |

> ⚠️ **No es un SO real.** No ejecuta código, no gestiona hardware.  
> Es una simulación lógica para visualizar y entender los algoritmos.

---

## 🗂️ Arquitectura del Proyecto

```
os_simulator/
│
├── main.py                    # Punto de entrada y orquestador
├── config.py                  # Constantes globales (quantum, marcos, etc.)
│
├── core/                      # Clases base compartidas
│   ├── enums.py               # ProcessState, PageState, FileAccessType
│   └── exceptions.py          # Excepciones personalizadas
│
├── process/                   # Módulo de gestión de procesos
│   ├── process.py             # Clase Process con todos sus atributos
│   └── schedulers/
│       ├── round_robin.py     # Algoritmo Round Robin con quantum
│       └── priority.py        # Planificador por Prioridad y SJF
│
├── memory/                    # Módulo de gestión de memoria
│   ├── ram.py                 # RAM simulada con marcos de página
│   ├── page_table.py          # Tabla de páginas por proceso
│   └── replacement.py         # Algoritmos FIFO y LRU
│
├── filesystem/                # Módulo de sistema de archivos
│   ├── file_manager.py        # Gestión de archivos y acceso concurrente
│   └── mutex.py               # SimMutex y SimSemaphore
│
├── metrics/                   # Módulo de métricas
│   └── calculator.py          # Waiting time, turnaround, response time
│
├── ui/                        # Interfaz de consola
│   ├── console_ui.py          # Vistas, tablas, menús con colores ANSI
│   └── colors.py              # Constantes de color de terminal
│
└── tests/                     # Pruebas unitarias
    ├── test_process.py         # 20 tests de procesos y planificadores
    ├── test_memory.py          # 14 tests de memoria y reemplazo
    └── test_filesystem.py      # 12 tests de archivos y mutex
```

---

## ⚡ Requisitos

- Python **3.10+** (se usa `match`, type hints con `|`)
- Sin dependencias externas para ejecutar el simulador
- `pytest` solo para correr los tests: `pip install pytest`

---

## 🚀 Cómo Ejecutar

```bash
# 1. Clonar / descomprimir el proyecto
cd os_simulator

# 2. Ejecutar el simulador
python main.py

# 3. Ejecutar todos los tests
python -m pytest tests/ -v

# 4. Ejecutar tests de un módulo específico
python -m pytest tests/test_process.py -v
python -m pytest tests/test_memory.py -v
python -m pytest tests/test_filesystem.py -v
```

---

## 🎮 Menú Principal

```
[1] Gestión de Procesos        → Elegir entre Round Robin / Prioridad / SJF
[2] Gestión de Memoria         → Paginación por demanda con FIFO
[3] Sistema de Archivos        → Escenarios de concurrencia con mutex
[4] Métricas del Sistema       → Tablas de waiting/turnaround/response time
[5] Demostración Completa      → Ejecuta los 3 módulos en secuencia automática
[0] Salir
```

---

## 🧠 Algoritmos Implementados

### Planificación de CPU

| Algoritmo | Preemptivo | Política |
|---|---|---|
| **Round Robin** | ✅ Sí | Turno equitativo con quantum configurable |
| **Prioridad** | ❌ No | Proceso con mayor prioridad va primero |
| **SJF** | ❌ No | Proceso con menor burst time va primero |

### Reemplazo de Páginas

| Algoritmo | Descripción | Anomalía |
|---|---|---|
| **FIFO** | Expulsa la página más antigua | Bélady posible |
| **LRU** | Expulsa la menos recientemente usada | No tiene anomalía de Bélady |

### Control de Concurrencia

| Mecanismo | Uso |
|---|---|
| **SimMutex** | Escritura exclusiva (1 escritor a la vez) |
| **SimSemaphore** | Lectura concurrente (N lectores configurables) |

---

## 📊 Métricas Calculadas

```
Turnaround Time  = finish_time - arrival_time
Waiting Time     = ticks acumulados en cola ready
Response Time    = start_time - arrival_time
Throughput       = procesos_terminados / ticks_totales
```

---

## 🔧 Configuración (`config.py`)

```python
DEFAULT_QUANTUM     = 3    # Ticks por proceso en Round Robin
TOTAL_FRAMES        = 8    # Marcos de página en RAM
MAX_PAGES_PER_PROC  = 6    # Páginas máximas por proceso
MAX_CONCURRENT_READ = 3    # Lectores simultáneos máximos
TICK_DELAY          = 0.05 # Velocidad de la simulación (segundos)
```

---

## 🧪 Resultados de Tests

```
46 passed in 0.06s
✅ TestProcess          (7 tests)
✅ TestRoundRobin       (3 tests)
✅ TestPriorityScheduler(2 tests)
✅ TestSJFScheduler     (1 test)
✅ TestMetrics          (4 tests)
✅ TestRAM              (6 tests)
✅ TestFIFOReplacement  (2 tests)
✅ TestLRUReplacement   (1 test)
✅ TestPageTable        (4 tests)
✅ TestSimMutex         (5 tests)
✅ TestSimSemaphore     (3 tests)
✅ TestFileManager      (8 tests)
```

---

## 📚 Referencias

- Silberschatz, A., Galvin, P. B., & Gagne, G. — *Operating System Concepts* (10ª ed.)
- Tanenbaum, A. — *Modern Operating Systems* (4ª ed.)
- UPTC — Material de cátedra Sistemas Operativos
