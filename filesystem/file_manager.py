"""
filesystem/file_manager.py - Sistema de archivos simulado.

Simula:
  - Archivos como objetos con nombre y contenido ficticio
  - Acceso concurrente controlado por mutex (escritura) y semáforo (lectura)
  - Registro detallado de cada operación para mostrar en UI
  - Detección de conflictos (intento de escritura mientras hay lectores)
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from filesystem.mutex import SimMutex, SimSemaphore
from core.enums import FileAccessType
from core.exceptions import FileNotFoundError as SimFileNotFoundError
from config import MAX_FILES, MAX_CONCURRENT_READ


@dataclass
class SimFile:
    """Archivo simulado."""
    name      : str
    content   : str   = "contenido simulado"
    size_kb   : int   = 4
    # Mutex para escritura exclusiva
    write_lock: SimMutex    = field(init=False)
    # Semáforo para lecturas concurrentes
    read_sem  : SimSemaphore = field(init=False)

    def __post_init__(self):
        self.write_lock = SimMutex(f"mutex_{self.name}")
        self.read_sem   = SimSemaphore(f"sem_{self.name}", MAX_CONCURRENT_READ)


class FileManager:
    """
    Gestor del sistema de archivos simulado.

    Responsabilidades:
      1. CRUD de archivos simulados
      2. Control de acceso concurrente (mutex/semáforo)
      3. Registro de todas las operaciones (access_log)
      4. Detección y registro de conflictos
    """

    def __init__(self):
        self.files       : Dict[str, SimFile] = {}
        self.access_log  : List[str]          = []
        self.conflict_log: List[str]          = []
        self.open_handles: Dict[int, List[str]] = {}   # pid → [archivos abiertos]

    # ── Gestión de archivos ───────────────────────────────────────────

    def create_file(self, name: str, content: str = "datos simulados",
                    size_kb: int = 4) -> SimFile:
        """Crea un archivo simulado. Lanza error si ya existe o si se alcanzó el límite."""
        if name in self.files:
            raise ValueError(f"El archivo '{name}' ya existe")
        if len(self.files) >= MAX_FILES:
            raise RuntimeError(f"Límite de {MAX_FILES} archivos alcanzado")
        f = SimFile(name=name, content=content, size_kb=size_kb)
        self.files[name] = f
        self.access_log.append(f"[CREATE]  Archivo '{name}' creado ({size_kb} KB)")
        return f

    def delete_file(self, name: str):
        """Elimina un archivo si no tiene accesos activos."""
        f = self._get_file(name)
        if f.write_lock.locked or len(f.read_sem.holders) > 0:
            raise RuntimeError(f"No se puede eliminar '{name}': tiene accesos activos")
        del self.files[name]
        self.access_log.append(f"[DELETE]  Archivo '{name}' eliminado")

    # ── Control de acceso ─────────────────────────────────────────────

    def open_file(self, pid: int, name: str,
                  access: FileAccessType) -> Tuple[bool, str]:
        """
        Intenta abrir un archivo con el tipo de acceso dado.
        Retorna (éxito, mensaje).

        Lógica:
          WRITE → adquirir mutex exclusivo
          READ  → adquirir semáforo (hasta MAX_CONCURRENT_READ lectores)

        Detecta conflictos:
          - Intento de escritura cuando hay lectores activos
          - Intento de lectura cuando hay un escritor
        """
        f = self._get_file(name)

        if access == FileAccessType.WRITE:
            # Verificar conflicto: ¿hay lectores activos?
            if len(f.read_sem.holders) > 0:
                msg = (f"[CONFLICT] PID {pid} quiere ESCRIBIR '{name}' "
                       f"pero hay {len(f.read_sem.holders)} lector(es) activo(s)")
                self.conflict_log.append(msg)
                self.access_log.append(msg)
                return False, msg

            acquired = f.write_lock.acquire(pid)
            if acquired:
                self._register_open(pid, name)
                msg = f"[OPEN-W]  PID {pid} abrió '{name}' para ESCRITURA"
            else:
                msg = f"[WAIT-W]  PID {pid} espera ESCRITURA en '{name}' (mutex ocupado)"
            self.access_log.append(msg)
            return acquired, msg

        else:  # READ
            # Verificar conflicto: ¿hay un escritor activo?
            if f.write_lock.locked:
                msg = (f"[CONFLICT] PID {pid} quiere LEER '{name}' "
                       f"pero PID {f.write_lock.owner_pid} está escribiendo")
                self.conflict_log.append(msg)
                self.access_log.append(msg)
                return False, msg

            acquired = f.read_sem.acquire(pid)
            if acquired:
                self._register_open(pid, name)
                msg = f"[OPEN-R]  PID {pid} abrió '{name}' para LECTURA"
            else:
                msg = f"[WAIT-R]  PID {pid} espera LECTURA en '{name}' (sem=0)"
            self.access_log.append(msg)
            return acquired, msg

    def close_file(self, pid: int, name: str,
                   access: FileAccessType) -> Tuple[Optional[int], str]:
        """
        Cierra un archivo y libera el lock/semáforo correspondiente.
        Retorna (pid_desbloqueado, mensaje) — pid_desbloqueado es el próximo
        proceso que obtuvo el recurso, o None.
        """
        f = self._get_file(name)
        next_pid = None

        if access == FileAccessType.WRITE:
            next_pid = f.write_lock.release(pid)
            msg = f"[CLOSE-W] PID {pid} cerró '{name}' (escritura)"
        else:
            next_pid = f.read_sem.release(pid)
            msg = f"[CLOSE-R] PID {pid} cerró '{name}' (lectura)"

        self._unregister_open(pid, name)
        self.access_log.append(msg)
        if next_pid:
            self.access_log.append(
                f"[UNBLOCK] PID {next_pid} desbloqueado en '{name}'"
            )
        return next_pid, msg

    # ── Utilidades ────────────────────────────────────────────────────

    def _get_file(self, name: str) -> SimFile:
        if name not in self.files:
            raise SimFileNotFoundError(f"Archivo '{name}' no encontrado")
        return self.files[name]

    def _register_open(self, pid: int, name: str):
        if pid not in self.open_handles:
            self.open_handles[pid] = []
        if name not in self.open_handles[pid]:
            self.open_handles[pid].append(name)

    def _unregister_open(self, pid: int, name: str):
        if pid in self.open_handles and name in self.open_handles[pid]:
            self.open_handles[pid].remove(name)

    def file_status(self, name: str) -> Dict:
        """Retorna estado legible de un archivo para la UI."""
        f = self._get_file(name)
        return {
            "nombre": name,
            "tamaño": f"{f.size_kb} KB",
            "escritor": f.write_lock.owner_pid,
            "lectores": list(f.read_sem.holders),
            "en_espera_write": list(f.write_lock.wait_queue),
            "en_espera_read": list(f.read_sem.wait_queue),
        }

    def all_files_status(self) -> List[Dict]:
        return [self.file_status(name) for name in self.files]
