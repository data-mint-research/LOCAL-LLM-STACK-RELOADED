"""
Validiert alle Konfigurationsdateien.

Dieses Modul stellt Funktionen zur Validierung aller Konfigurationsdateien bereit.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import yaml

from llm_stack.cli_commands import register_command
from llm_stack.core import config, error, logging, validation


def validate_env_file(env_file: str) -> bool:
    """
    Validiert eine .env-Datei.

    Args:
        env_file: Pfad zur .env-Datei

    Returns:
        bool: True, wenn die Datei gültig ist, sonst False
    """
    logging.debug(f"Validiere .env-Datei: {env_file}")

    # Prüfen, ob die Datei existiert
    if not os.path.isfile(env_file):
        logging.error(f"Datei nicht gefunden: {env_file}")
        return False

    # Variablen aus der Datei lesen
    variables = {}
    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                # Kommentare und leere Zeilen überspringen
                if not line or line.startswith("#"):
                    continue

                # Schlüssel und Wert trennen
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    variables[key] = value
    except Exception as e:
        logging.error(f"Fehler beim Lesen der Datei: {str(e)}")
        return False

    # Erforderliche Variablen prüfen
    required_vars = [
        "HOST_PORT_OLLAMA",
        "HOST_PORT_LIBRECHAT",
        "OLLAMA_CPU_LIMIT",
        "OLLAMA_MEMORY_LIMIT",
    ]

    for var in required_vars:
        if var not in variables:
            logging.error(f"Erforderliche Variable fehlt: {var}")
            return False

    # Port-Variablen validieren
    port_vars = [var for var in variables if var.startswith("HOST_PORT_")]
    for var in port_vars:
        if not validation.validate_port(variables[var], var):
            return False

    # CPU-Limit-Variablen validieren
    cpu_vars = [var for var in variables if var.endswith("_CPU_LIMIT")]
    for var in cpu_vars:
        if not validation.validate_cpu_format(variables[var], var):
            return False

    # Speicher-Limit-Variablen validieren
    memory_vars = [var for var in variables if var.endswith("_MEMORY_LIMIT")]
    for var in memory_vars:
        if not validation.validate_memory_format(variables[var], var):
            return False

    logging.success(f".env-Datei validiert: {env_file}")
    return True


def validate_yaml_file(yaml_file: str) -> bool:
    """
    Validiert eine YAML-Datei.

    Args:
        yaml_file: Pfad zur YAML-Datei

    Returns:
        bool: True, wenn die Datei gültig ist, sonst False
    """
    logging.debug(f"Validiere YAML-Datei: {yaml_file}")

    # Prüfen, ob die Datei existiert
    if not os.path.isfile(yaml_file):
        logging.error(f"Datei nicht gefunden: {yaml_file}")
        return False

    # YAML-Datei parsen
    try:
        with open(yaml_file) as f:
            yaml_data = yaml.safe_load(f)

        # Prüfen, ob die Datei gültiges YAML enthält
        if yaml_data is None:
            logging.error(f"Leere YAML-Datei: {yaml_file}")
            return False

        logging.success(f"YAML-Datei validiert: {yaml_file}")
        return True
    except yaml.YAMLError as e:
        logging.error(f"Ungültiges YAML in {yaml_file}: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Fehler beim Lesen der Datei: {str(e)}")
        return False


def validate_all_configs() -> bool:
    """
    Validiert alle Konfigurationsdateien.

    Returns:
        bool: True, wenn alle Dateien gültig sind, sonst False
    """
    logging.info("Validiere alle Konfigurationsdateien...")

    # Hauptkonfigurationsdatei validieren
    if not validate_env_file(config.ENV_FILE):
        return False

    # LibreChat-Konfigurationsdatei validieren
    librechat_env = os.path.join(config.CONFIG_DIR, "librechat", ".env")
    if os.path.isfile(librechat_env):
        if not validate_env_file(librechat_env):
            return False

    # YAML-Dateien in core/ validieren
    core_dir = "core"
    if os.path.isdir(core_dir):
        for file in os.listdir(core_dir):
            if file.endswith(".yml") or file.endswith(".yaml"):
                yaml_file = os.path.join(core_dir, file)
                if not validate_yaml_file(yaml_file):
                    return False

    # YAML-Dateien in modules/ validieren
    modules_dir = "modules"
    if os.path.isdir(modules_dir):
        for module in os.listdir(modules_dir):
            module_dir = os.path.join(modules_dir, module)
            if os.path.isdir(module_dir):
                for file in os.listdir(module_dir):
                    if file.endswith(".yml") or file.endswith(".yaml"):
                        yaml_file = os.path.join(module_dir, file)
                        if not validate_yaml_file(yaml_file):
                            return False

    logging.success("Alle Konfigurationsdateien sind gültig")
    return True


@register_command("validate-configs")
def validate_configs(args: Optional[argparse.Namespace] = None) -> int:
    """
    Validiert alle Konfigurationsdateien.

    Args:
        args: Argumente für den Befehl

    Returns:
        int: Exit-Code (0 bei Erfolg, 1 bei Fehler)
    """
    logging.info("Validiere alle Konfigurationsdateien...")

    # Alle Konfigurationsdateien validieren
    if not validate_all_configs():
        error.handle_error(
            error.ERR_VALIDATION_ERROR, "Konfigurationsvalidierung fehlgeschlagen"
        )
        return 1

    logging.success("Alle Konfigurationsdateien sind gültig")
    return 0


def setup_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    Richtet den Parser für den validate-configs-Befehl ein.

    Args:
        subparsers: Subparser-Aktion, zu der der Parser hinzugefügt werden soll
    """
    parser = subparsers.add_parser(
        "validate-configs",
        help="Validiert alle Konfigurationsdateien",
        description="Validiert alle Konfigurationsdateien gegen das Schema",
    )


def main() -> int:
    """
    Hauptfunktion für die direkte Ausführung des Skripts.

    Returns:
        int: Exit-Code (0 bei Erfolg, 1 bei Fehler)
    """
    return validate_configs()


if __name__ == "__main__":
    sys.exit(main())
