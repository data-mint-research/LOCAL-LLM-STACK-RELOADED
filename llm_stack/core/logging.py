"""
Logging-Funktionen für den LLM Stack.

Dieses Modul stellt Funktionen zum Protokollieren von Nachrichten mit verschiedenen
Ebenen und Formatierungen bereit.
"""

import os
import sys
from datetime import datetime
from enum import Enum
from typing import Optional

from rich.console import Console
from rich.theme import Theme

# Rich-Konsole mit benutzerdefiniertem Farbschema
custom_theme = Theme({
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "bold red",
    "debug": "dim blue",
    "timestamp": "dim",
})

console = Console(theme=custom_theme)

# Log-Ebenen
class LogLevel(Enum):
    """Log-Ebenen für den Logger."""
    DEBUG = 0
    INFO = 1
    SUCCESS = 2
    WARNING = 3
    ERROR = 4


# Aktuelle Log-Ebene (Standard: INFO)
current_log_level = LogLevel.INFO

# Log-Datei
log_file = None


def set_log_level(level: LogLevel) -> None:
    """
    Setzt die aktuelle Log-Ebene.
    
    Args:
        level: Die zu setzende Log-Ebene
    """
    global current_log_level
    current_log_level = level


def get_log_level() -> LogLevel:
    """
    Gibt die aktuelle Log-Ebene zurück.
    
    Returns:
        LogLevel: Die aktuelle Log-Ebene
    """
    return current_log_level


def set_log_file(file_path: str) -> bool:
    """
    Setzt die Log-Datei.
    
    Args:
        file_path: Pfad zur Log-Datei
        
    Returns:
        bool: True, wenn die Log-Datei erfolgreich gesetzt wurde, sonst False
    """
    global log_file
    
    try:
        # Sicherstellen, dass das Verzeichnis existiert
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Log-Datei öffnen
        log_file = open(file_path, "a")
        return True
    except Exception as e:
        console.print(f"[error]Fehler beim Öffnen der Log-Datei: {str(e)}[/error]")
        return False


def close_log_file() -> None:
    """Schließt die Log-Datei, wenn sie geöffnet ist."""
    global log_file
    
    if log_file:
        log_file.close()
        log_file = None


def _log(level: LogLevel, message: str, style: str, timestamp: bool = True) -> None:
    """
    Interne Funktion zum Protokollieren einer Nachricht.
    
    Args:
        level: Log-Ebene der Nachricht
        message: Die zu protokollierende Nachricht
        style: Rich-Stil für die Nachricht
        timestamp: Ob ein Zeitstempel angezeigt werden soll
    """
    # Prüfen, ob die Nachricht protokolliert werden soll
    if level.value < current_log_level.value:
        return
    
    # Zeitstempel erstellen
    ts = ""
    if timestamp:
        ts = f"[timestamp]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/timestamp] "
    
    # Nachricht formatieren
    formatted_message = f"{ts}[{style}]{message}[/{style}]"
    
    # Nachricht auf der Konsole ausgeben
    console.print(formatted_message)
    
    # Nachricht in die Log-Datei schreiben, wenn sie geöffnet ist
    if log_file:
        # Formatierung für die Datei entfernen
        plain_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        plain_message = f"{plain_ts} [{level.name}] {message}\n"
        log_file.write(plain_message)
        log_file.flush()


def debug(message: str) -> None:
    """
    Protokolliert eine Debug-Nachricht.
    
    Args:
        message: Die zu protokollierende Nachricht
    """
    _log(LogLevel.DEBUG, message, "debug")


def info(message: str) -> None:
    """
    Protokolliert eine Info-Nachricht.
    
    Args:
        message: Die zu protokollierende Nachricht
    """
    _log(LogLevel.INFO, message, "info")


def success(message: str) -> None:
    """
    Protokolliert eine Erfolgs-Nachricht.
    
    Args:
        message: Die zu protokollierende Nachricht
    """
    _log(LogLevel.SUCCESS, message, "success")


def warn(message: str) -> None:
    """
    Protokolliert eine Warnungs-Nachricht.
    
    Args:
        message: Die zu protokollierende Nachricht
    """
    _log(LogLevel.WARNING, message, "warning")


def error(message: str) -> None:
    """
    Protokolliert eine Fehler-Nachricht.
    
    Args:
        message: Die zu protokollierende Nachricht
    """
    _log(LogLevel.ERROR, message, "error")


# Alias für warn
warning = warn


# Log-Ebene aus Umgebungsvariable setzen
def init_logging() -> None:
    """Initialisiert das Logging-System basierend auf Umgebungsvariablen."""
    # Log-Ebene aus Umgebungsvariable abrufen
    log_level_str = os.environ.get("LLM_STACK_LOG_LEVEL", "INFO").upper()
    
    # Log-Ebene setzen
    if log_level_str == "DEBUG":
        set_log_level(LogLevel.DEBUG)
    elif log_level_str == "INFO":
        set_log_level(LogLevel.INFO)
    elif log_level_str == "WARNING" or log_level_str == "WARN":
        set_log_level(LogLevel.WARNING)
    elif log_level_str == "ERROR":
        set_log_level(LogLevel.ERROR)
    
    # Log-Datei aus Umgebungsvariable abrufen
    log_file_path = os.environ.get("LLM_STACK_LOG_FILE")
    if log_file_path:
        set_log_file(log_file_path)
    
    debug("Logging-System initialisiert")


# Logging initialisieren
init_logging()