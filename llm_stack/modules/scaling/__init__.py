"""
Scaling-Modul für den LLM Stack.

Dieses Modul stellt Funktionen zur Skalierung des LLM Stacks bereit.
"""

from typing import Dict, List, Optional, Union

# Modul-Name
MODULE_NAME = "scaling"

# Modul-API-Version
MODULE_API_VERSION = "1.0.0"

# Modul-Status-Konstanten
MODULE_STATUS_UNKNOWN = 0
MODULE_STATUS_STOPPED = 1
MODULE_STATUS_STARTING = 2
MODULE_STATUS_RUNNING = 3
MODULE_STATUS_STOPPING = 4
MODULE_STATUS_ERROR = 5

# Status-Text-Mapping
MODULE_STATUS_TEXT = {
    MODULE_STATUS_UNKNOWN: "Unknown",
    MODULE_STATUS_STOPPED: "Stopped",
    MODULE_STATUS_STARTING: "Starting",
    MODULE_STATUS_RUNNING: "Running",
    MODULE_STATUS_STOPPING: "Stopping",
    MODULE_STATUS_ERROR: "Error",
}

# Exportierte Symbole
__all__ = [
    "MODULE_NAME",
    "MODULE_API_VERSION",
    "MODULE_STATUS_UNKNOWN",
    "MODULE_STATUS_STOPPED",
    "MODULE_STATUS_STARTING",
    "MODULE_STATUS_RUNNING",
    "MODULE_STATUS_STOPPING",
    "MODULE_STATUS_ERROR",
    "MODULE_STATUS_TEXT",
]
