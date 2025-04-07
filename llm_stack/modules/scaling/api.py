"""
Standardisierte API-Schnittstelle für das Scaling-Modul.

Dieses Modul stellt eine standardisierte API-Schnittstelle für das Scaling-Modul bereit.
"""

import json
import os
from typing import Any, Dict, List, Optional, Union

from llm_stack.core import error, logging
from llm_stack.modules import module_api
from llm_stack.modules.scaling import (
    MODULE_API_VERSION,
    MODULE_NAME,
    MODULE_STATUS_ERROR,
    MODULE_STATUS_RUNNING,
    MODULE_STATUS_STARTING,
    MODULE_STATUS_STOPPED,
    MODULE_STATUS_STOPPING,
    MODULE_STATUS_TEXT,
    MODULE_STATUS_UNKNOWN,
)


def module_api_help() -> str:
    """
    Gibt die Hilfe für die Modul-API zurück.

    Returns:
        str: Hilfetext für die Modul-API
    """
    return module_api.get_module_api_help(MODULE_NAME, MODULE_API_VERSION)


def module_start() -> int:
    """
    Startet die Modul-Dienste.

    Returns:
        int: 0 bei Erfolg, Fehlercode bei Fehler
    """
    return module_api.module_start(MODULE_NAME, module_status, MODULE_STATUS_RUNNING)


def module_stop() -> int:
    """
    Stoppt die Modul-Dienste.

    Returns:
        int: 0 bei Erfolg, Fehlercode bei Fehler
    """
    return module_api.module_stop(MODULE_NAME, module_status, MODULE_STATUS_STOPPED)


def module_restart() -> int:
    """
    Startet die Modul-Dienste neu.

    Returns:
        int: 0 bei Erfolg, Fehlercode bei Fehler
    """
    return module_api.module_restart(MODULE_NAME, module_stop, module_start)


def module_status() -> int:
    """
    Ermittelt den aktuellen Status des Moduls.

    Returns:
        int: Status-Code (0-5)
    """
    return module_api.module_status(
        MODULE_NAME,
        MODULE_STATUS_UNKNOWN,
        MODULE_STATUS_STOPPED,
        MODULE_STATUS_ERROR,
        MODULE_STATUS_RUNNING,
    )


def module_get_status_text() -> str:
    """
    Gibt den aktuellen Status des Moduls als Text zurück.

    Returns:
        str: Status-Text
    """
    return module_api.module_get_status_text(module_status, MODULE_STATUS_TEXT)


def module_get_config(config_key: Optional[str] = None) -> Union[str, List[str], None]:
    """
    Gibt die aktuelle Konfiguration des Moduls zurück.

    Args:
        config_key: Konfigurationsschlüssel (optional)

    Returns:
        Union[str, List[str], None]: Konfigurationswert(e) oder None bei Fehler
    """
    return module_api.module_get_config(MODULE_NAME, config_key)


def module_set_config(config_key: str, config_value: str) -> int:
    """
    Setzt einen Konfigurationswert für das Modul.

    Args:
        config_key: Konfigurationsschlüssel
        config_value: Konfigurationswert

    Returns:
        int: 0 bei Erfolg, Fehlercode bei Fehler
    """
    return module_api.module_set_config(MODULE_NAME, config_key, config_value)


def module_get_logs(service_name: Optional[str] = None, lines: int = 100) -> str:
    """
    Gibt die Logs für die Modul-Dienste zurück.

    Args:
        service_name: Dienstname (optional)
        lines: Anzahl der Zeilen (optional, Standard: 100)

    Returns:
        str: Log-Ausgabe
    """
    return module_api.module_get_logs(MODULE_NAME, service_name, lines)


def module_get_health(service_name: Optional[str] = None) -> str:
    """
    Gibt den Gesundheitsstatus der Modul-Dienste zurück.

    Args:
        service_name: Dienstname (optional)

    Returns:
        str: Gesundheitsstatus (JSON)
    """
    return module_api.module_get_health(
        MODULE_NAME, module_get_status_text, service_name
    )


def module_get_version() -> str:
    """
    Gibt die Version des Moduls zurück.

    Returns:
        str: Modul-Version
    """
    return module_api.module_get_version(MODULE_NAME)


def module_get_api_version() -> str:
    """
    Gibt die Version der Modul-API zurück.

    Returns:
        str: API-Version
    """
    return module_api.module_get_api_version(MODULE_API_VERSION)


# Log-Modul-API-Initialisierung
logging.debug(f"{MODULE_NAME}-Modul-API initialisiert (v{MODULE_API_VERSION})")
