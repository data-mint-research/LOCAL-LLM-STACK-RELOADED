"""
Systemfunktionen für den LLM Stack.

Dieses Modul stellt Funktionen für systembezogene Operationen bereit,
wie die Überprüfung von Systemressourcen, die Sicherstellung, dass Verzeichnisse existieren, usw.
"""

import functools
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

import psutil

from llm_stack.core import error, logging

# Cache for system information
_system_info_cache = {}
_system_info_ttl = 60  # Cache TTL in seconds (1 minute)
_env_var_cache = {}
_env_var_ttl = 300  # Cache TTL in seconds (5 minutes)
_memory_usage_cache = None
_memory_usage_timestamp = 0
_disk_usage_cache = {}
_disk_usage_timestamp = 0


def cache_system_info(func: Callable) -> Callable:
    """
    Decorator to cache system information.
    
    Args:
        func: Function to decorate
        
    Returns:
        Callable: Decorated function
    """
    @functools.wraps(func)
    def wrapper():
        # Use a simple cache key since this function takes no arguments
        cache_key = "system_info"
        
        # Check cache
        if cache_key in _system_info_cache:
            info, timestamp = _system_info_cache[cache_key]
            if time.time() - timestamp < _system_info_ttl:
                return info
        
        # Call original function
        result = func()
        
        # Update cache
        _system_info_cache[cache_key] = (result, time.time())
            
        return result
    
    return wrapper

@cache_system_info
def get_system_info() -> Dict[str, str]:
    """
    Ruft Systeminformationen ab mit Caching.

    Returns:
        Dict[str, str]: Systeminformationen
    """
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": platform.python_version(),
        "cpu_count": str(os.cpu_count()),
        "memory_total": format_bytes(psutil.virtual_memory().total),
        "disk_total": format_bytes(psutil.disk_usage("/").total),
        "disk_free": format_bytes(psutil.disk_usage("/").free),
    }

    return info


def format_bytes(bytes_value: int) -> str:
    """
    Formatiert Bytes in eine lesbare Form.

    Args:
        bytes_value: Wert in Bytes

    Returns:
        str: Formatierter Wert
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def check_system_requirements() -> bool:
    """
    Prüft, ob das System die Mindestanforderungen erfüllt.

    Returns:
        bool: True, wenn das System die Anforderungen erfüllt, sonst False
    """
    # Mindestanforderungen
    min_memory_gb = 8
    min_disk_gb = 20
    min_cpu_cores = 2

    # Systemressourcen abrufen
    memory_gb = psutil.virtual_memory().total / (1024**3)
    disk_gb = psutil.disk_usage("/").free / (1024**3)
    cpu_cores = os.cpu_count() or 0

    # Anforderungen prüfen
    if memory_gb < min_memory_gb:
        logging.error(
            f"Nicht genügend Arbeitsspeicher. Benötigt: {min_memory_gb} GB, Verfügbar: {memory_gb:.2f} GB"
        )
        return False

    if disk_gb < min_disk_gb:
        logging.error(
            f"Nicht genügend freier Speicherplatz. Benötigt: {min_disk_gb} GB, Verfügbar: {disk_gb:.2f} GB"
        )
        return False

    if cpu_cores < min_cpu_cores:
        logging.error(
            f"Nicht genügend CPU-Kerne. Benötigt: {min_cpu_cores}, Verfügbar: {cpu_cores}"
        )
        return False

    logging.success("System erfüllt die Mindestanforderungen")
    return True


def ensure_directory(directory_path: str) -> bool:
    """
    Stellt sicher, dass ein Verzeichnis existiert.

    Args:
        directory_path: Pfad zum Verzeichnis

    Returns:
        bool: True, wenn das Verzeichnis existiert oder erstellt wurde, sonst False
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        logging.error(
            f"Fehler beim Erstellen des Verzeichnisses {directory_path}: {str(e)}"
        )
        return False


def backup_file(file_path: str, backup_suffix: Optional[str] = None) -> Optional[str]:
    """
    Erstellt ein Backup einer Datei.

    Args:
        file_path: Pfad zur Datei
        backup_suffix: Optionales Suffix für die Backup-Datei

    Returns:
        Optional[str]: Pfad zur Backup-Datei oder None, wenn ein Fehler aufgetreten ist
    """
    if not os.path.isfile(file_path):
        logging.error(f"Datei nicht gefunden: {file_path}")
        return None

    try:
        # Backup-Dateinamen erstellen
        if backup_suffix is None:
            import datetime

            backup_suffix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        backup_path = f"{file_path}.{backup_suffix}.bak"

        # Datei kopieren
        shutil.copy2(file_path, backup_path)
        logging.debug(f"Backup erstellt: {backup_path}")

        return backup_path
    except Exception as e:
        logging.error(f"Fehler beim Erstellen des Backups von {file_path}: {str(e)}")
        return None


def command_exists(command: str) -> bool:
    """
    Prüft, ob ein Befehl existiert.

    Args:
        command: Zu prüfender Befehl

    Returns:
        bool: True, wenn der Befehl existiert, sonst False
    """
    return shutil.which(command) is not None


def get_free_port(start_port: int = 8000, end_port: int = 9000) -> Optional[int]:
    """
    Findet einen freien Port im angegebenen Bereich.

    Args:
        start_port: Startport
        end_port: Endport

    Returns:
        Optional[int]: Freier Port oder None, wenn kein freier Port gefunden wurde
    """
    import socket

    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("localhost", port))
                return port
            except OSError:
                continue

    logging.error(f"Kein freier Port im Bereich {start_port}-{end_port} gefunden")
    return None


def is_port_in_use(port: int) -> bool:
    """
    Prüft, ob ein Port in Verwendung ist.

    Args:
        port: Zu prüfender Port

    Returns:
        bool: True, wenn der Port in Verwendung ist, sonst False
    """
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def get_script_directory() -> str:
    """
    Ruft das Verzeichnis des aktuellen Skripts ab.

    Returns:
        str: Verzeichnis des aktuellen Skripts
    """
    return os.path.dirname(os.path.abspath(__file__))


def get_project_root() -> str:
    """
    Ruft das Wurzelverzeichnis des Projekts ab.

    Returns:
        str: Wurzelverzeichnis des Projekts
    """
    return os.path.abspath(os.path.join(get_script_directory(), "..", ".."))


def execute_command(
    command: Union[str, List[str]], shell: bool = False, timeout: Optional[int] = None
) -> Tuple[int, str, str]:
    """
    Executes a command.

    Args:
        command: Command to execute. Should be a list of arguments for security.
                If a string is provided and shell=False, it will be split into arguments.
        shell: Whether to execute the command in a shell. Default is False for security reasons.
               WARNING: Using shell=True with untrusted input is a security risk and should be avoided.
               This parameter is deprecated and will be removed in a future version.
        timeout: Timeout in seconds

    Returns:
        Tuple[int, str, str]: Return code, standard output, standard error output
    
    Security Note:
        Always prefer shell=False (the default) and pass command as a list of arguments
        to prevent command injection vulnerabilities.
    """
    try:
        # If command is a string and shell is False, split the command into arguments
        if isinstance(command, str) and not shell:
            import shlex
            command_args = shlex.split(command)
        else:
            command_args = command
            
        # Security warning for shell=True
        if shell:
            logging.warn("SECURITY RISK: Using shell=True is strongly discouraged as it can lead to command injection vulnerabilities")
            logging.warn("Consider refactoring your code to use shell=False with a list of arguments")
            
            # If shell=True and command is a list, convert it to a string
            if isinstance(command_args, list):
                import shlex
                command_args = " ".join(shlex.quote(arg) for arg in command_args)

        # Validate command before execution
        if shell and isinstance(command_args, str):
            # Basic validation for shell commands
            if ';' in command_args or '&&' in command_args or '||' in command_args:
                logging.error("Potentially unsafe command with shell=True containing command separators")
                return -1, "", "Security error: Command contains potentially unsafe separators"
        elif not shell and isinstance(command_args, list) and len(command_args) > 0:
            # Ensure the command exists when using a list of arguments
            if not command_exists(command_args[0]):
                logging.error(f"Command not found: {command_args[0]}")
                return -1, "", f"Command not found: {command_args[0]}"

        process = subprocess.Popen(
            command_args,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        logging.error(f"Timeout while executing command: {command}")
        return -1, stdout, stderr
    except Exception as e:
        logging.error(f"Error executing command {command}: {str(e)}")
        return -1, "", str(e)


def cache_env_var(func: Callable) -> Callable:
    """
    Decorator to cache environment variables.
    
    Args:
        func: Function to decorate
        
    Returns:
        Callable: Decorated function
    """
    @functools.wraps(func)
    def wrapper(name: str, default: Optional[str] = None):
        # Check cache
        if name in _env_var_cache:
            value, timestamp = _env_var_cache[name]
            if time.time() - timestamp < _env_var_ttl:
                return value
        
        # Call original function
        result = func(name, default)
        
        # Update cache
        _env_var_cache[name] = (result, time.time())
            
        return result
    
    return wrapper

@cache_env_var
def get_environment_variable(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Ruft eine Umgebungsvariable ab mit Caching.

    Args:
        name: Name der Umgebungsvariable
        default: Standardwert, falls die Variable nicht existiert

    Returns:
        Optional[str]: Wert der Umgebungsvariable oder Standardwert
    """
    return os.environ.get(name, default)


def set_environment_variable(name: str, value: str) -> None:
    """
    Setzt eine Umgebungsvariable.

    Args:
        name: Name der Umgebungsvariable
        value: Wert der Umgebungsvariable
    """
    os.environ[name] = value


def get_file_size(file_path: str) -> Optional[int]:
    """
    Ruft die Größe einer Datei ab.

    Args:
        file_path: Pfad zur Datei

    Returns:
        Optional[int]: Größe der Datei in Bytes oder None, wenn die Datei nicht existiert
    """
    if not os.path.isfile(file_path):
        logging.error(f"Datei nicht gefunden: {file_path}")
        return None

    return os.path.getsize(file_path)


def get_file_modification_time(file_path: str) -> Optional[float]:
    """
    Ruft die letzte Änderungszeit einer Datei ab.

    Args:
        file_path: Pfad zur Datei

    Returns:
        Optional[float]: Letzte Änderungszeit der Datei oder None, wenn die Datei nicht existiert
    """
    if not os.path.isfile(file_path):
        logging.error(f"Datei nicht gefunden: {file_path}")
        return None

    return os.path.getmtime(file_path)


def list_directory(directory_path: str, pattern: Optional[str] = None) -> List[str]:
    """
    Listet Dateien in einem Verzeichnis auf.

    Args:
        directory_path: Pfad zum Verzeichnis
        pattern: Optionales Glob-Muster für die Dateifilterung

    Returns:
        List[str]: Liste von Dateipfaden
    """
    if not os.path.isdir(directory_path):
        logging.error(f"Verzeichnis nicht gefunden: {directory_path}")
        return []

    if pattern:
        return [str(p) for p in Path(directory_path).glob(pattern)]
    else:
        return [os.path.join(directory_path, f) for f in os.listdir(directory_path)]


def is_process_running(process_name: str) -> bool:
    """
    Prüft, ob ein Prozess läuft.

    Args:
        process_name: Name des Prozesses

    Returns:
        bool: True, wenn der Prozess läuft, sonst False
    """
    for proc in psutil.process_iter(["name"]):
        try:
            if process_name.lower() in proc.info["name"].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def get_memory_usage() -> Dict[str, Union[int, float, str]]:
    """
    Ruft die Speichernutzung ab mit Caching.

    Returns:
        Dict[str, Union[int, float, str]]: Speichernutzungsinformationen
    """
    global _memory_usage_cache, _memory_usage_timestamp
    
    # Check if we have a cached memory usage that's still valid (5 seconds TTL)
    if _memory_usage_cache is not None and time.time() - _memory_usage_timestamp < 5:
        return _memory_usage_cache
        
    memory = psutil.virtual_memory()
    result = {
        "total": memory.total,
        "available": memory.available,
        "used": memory.used,
        "percent": memory.percent,
        "total_formatted": format_bytes(memory.total),
        "available_formatted": format_bytes(memory.available),
        "used_formatted": format_bytes(memory.used),
    }
    
    # Update cache
    _memory_usage_cache = result
    _memory_usage_timestamp = time.time()
    
    return result


def get_disk_usage(path: str = "/") -> Dict[str, Union[int, float, str]]:
    """
    Ruft die Festplattennutzung ab mit Caching.

    Args:
        path: Pfad, für den die Festplattennutzung abgerufen werden soll

    Returns:
        Dict[str, Union[int, float, str]]: Festplattennutzungsinformationen
    """
    global _disk_usage_cache, _disk_usage_timestamp
    
    # Check if we have a cached disk usage for this path that's still valid (10 seconds TTL)
    if path in _disk_usage_cache and time.time() - _disk_usage_timestamp < 10:
        return _disk_usage_cache[path]
        
    disk = psutil.disk_usage(path)
    result = {
        "total": disk.total,
        "free": disk.free,
        "used": disk.used,
        "percent": disk.percent,
        "total_formatted": format_bytes(disk.total),
        "free_formatted": format_bytes(disk.free),
        "used_formatted": format_bytes(disk.used),
    }
    
    # Update cache
    _disk_usage_cache[path] = result
    _disk_usage_timestamp = time.time()
    
    return result


def get_cpu_usage() -> float:
    """
    Ruft die CPU-Nutzung ab.

    Returns:
        float: CPU-Nutzung in Prozent
    """
    return psutil.cpu_percent(interval=1)


logging.debug("Systemmodul initialisiert")
