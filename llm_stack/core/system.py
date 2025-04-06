"""
Systemfunktionen für den LLM Stack.

Dieses Modul stellt Funktionen für systembezogene Operationen bereit,
wie die Überprüfung von Systemressourcen, die Sicherstellung, dass Verzeichnisse existieren, usw.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import psutil

from llm_stack.core import error, logging


def get_system_info() -> Dict[str, str]:
    """
    Ruft Systeminformationen ab.
    
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
    memory_gb = psutil.virtual_memory().total / (1024 ** 3)
    disk_gb = psutil.disk_usage("/").free / (1024 ** 3)
    cpu_cores = os.cpu_count() or 0
    
    # Anforderungen prüfen
    if memory_gb < min_memory_gb:
        logging.error(f"Nicht genügend Arbeitsspeicher. Benötigt: {min_memory_gb} GB, Verfügbar: {memory_gb:.2f} GB")
        return False
    
    if disk_gb < min_disk_gb:
        logging.error(f"Nicht genügend freier Speicherplatz. Benötigt: {min_disk_gb} GB, Verfügbar: {disk_gb:.2f} GB")
        return False
    
    if cpu_cores < min_cpu_cores:
        logging.error(f"Nicht genügend CPU-Kerne. Benötigt: {min_cpu_cores}, Verfügbar: {cpu_cores}")
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
        logging.error(f"Fehler beim Erstellen des Verzeichnisses {directory_path}: {str(e)}")
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
            except socket.error:
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


def execute_command(command: str, shell: bool = True, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    """
    Führt einen Befehl aus.
    
    Args:
        command: Auszuführender Befehl
        shell: Ob der Befehl in einer Shell ausgeführt werden soll
        timeout: Timeout in Sekunden
        
    Returns:
        Tuple[int, str, str]: Rückgabecode, Standardausgabe, Standardfehlerausgabe
    """
    try:
        process = subprocess.Popen(
            command,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        logging.error(f"Timeout bei der Ausführung des Befehls: {command}")
        return -1, stdout, stderr
    except Exception as e:
        logging.error(f"Fehler bei der Ausführung des Befehls {command}: {str(e)}")
        return -1, "", str(e)


def get_environment_variable(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Ruft eine Umgebungsvariable ab.
    
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
    Ruft die Speichernutzung ab.
    
    Returns:
        Dict[str, Union[int, float, str]]: Speichernutzungsinformationen
    """
    memory = psutil.virtual_memory()
    return {
        "total": memory.total,
        "available": memory.available,
        "used": memory.used,
        "percent": memory.percent,
        "total_formatted": format_bytes(memory.total),
        "available_formatted": format_bytes(memory.available),
        "used_formatted": format_bytes(memory.used)
    }


def get_disk_usage(path: str = "/") -> Dict[str, Union[int, float, str]]:
    """
    Ruft die Festplattennutzung ab.
    
    Args:
        path: Pfad, für den die Festplattennutzung abgerufen werden soll
        
    Returns:
        Dict[str, Union[int, float, str]]: Festplattennutzungsinformationen
    """
    disk = psutil.disk_usage(path)
    return {
        "total": disk.total,
        "free": disk.free,
        "used": disk.used,
        "percent": disk.percent,
        "total_formatted": format_bytes(disk.total),
        "free_formatted": format_bytes(disk.free),
        "used_formatted": format_bytes(disk.used)
    }


def get_cpu_usage() -> float:
    """
    Ruft die CPU-Nutzung ab.
    
    Returns:
        float: CPU-Nutzung in Prozent
    """
    return psutil.cpu_percent(interval=1)


logging.debug("Systemmodul initialisiert")