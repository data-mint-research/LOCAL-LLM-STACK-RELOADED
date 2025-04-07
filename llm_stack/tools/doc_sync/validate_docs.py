"""
Validiert Dokumentationsdateien gegen Schema.

Dieses Skript validiert die YAML-Dokumentationsdateien gegen ihre Schemas.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

from llm_stack.core import error, logging, system

# Validierungsstufen
STRICT = 0
WARNING_ONLY = 1


def validate_yaml(file_path: str) -> bool:
    """
    Validiert eine YAML-Datei.

    Args:
        file_path: Pfad zur YAML-Datei

    Returns:
        bool: True, wenn die Datei gültig ist, sonst False
    """
    # Prüfen, ob die Datei existiert
    if not os.path.isfile(file_path):
        logging.error(f"Fehler: Datei nicht gefunden: {file_path}")
        return False

    # Prüfen, ob die Datei gültige YAML ist
    try:
        with open(file_path) as f:
            yaml.safe_load(f)
    except yaml.YAMLError as e:
        logging.error(f"Fehler: Ungültige YAML in {file_path}: {str(e)}")
        return False

    logging.success(f"✓ {file_path} ist gültige YAML")
    return True


def validate_metadata(
    file_path: str, prefix: str = ".", validation_level: int = STRICT
) -> bool:
    """
    Validiert die Metadaten einer YAML-Datei.

    Args:
        file_path: Pfad zur YAML-Datei
        prefix: Präfix für den YAML-Pfad
        validation_level: Validierungsstufe (STRICT oder WARNING_ONLY)

    Returns:
        bool: True, wenn die Metadaten gültig sind, sonst False
    """
    logging.info(f"Validiere Metadaten in {file_path}")

    # YAML-Datei laden
    try:
        with open(file_path) as f:
            data = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Fehler beim Laden der YAML-Datei {file_path}: {str(e)}")
        return False

    # Metadaten-Abschnitt prüfen
    metadata = None
    if prefix == ".":
        metadata = data.get("metadata")
    else:
        # Präfix aufteilen und durch die Struktur navigieren
        parts = prefix.strip(".").split(".")
        current = data
        for part in parts:
            if part in current:
                current = current[part]
            else:
                current = None
                break

        if current is not None:
            metadata = current.get("metadata")

    if metadata is None:
        if validation_level == STRICT:
            logging.error(f"Fehler: Fehlender 'metadata'-Abschnitt in {file_path}")
            return False
        else:
            logging.warn(f"Warnung: Fehlender 'metadata'-Abschnitt in {file_path}")
            return True

    # Erforderliche Metadatenfelder prüfen
    version = metadata.get("version")
    last_updated = metadata.get("last_updated")
    author = metadata.get("author")

    if not version:
        if validation_level == STRICT:
            logging.error(f"Fehler: Fehlendes 'version'-Feld in den Metadaten")
            return False
        else:
            logging.warn(f"Warnung: Fehlendes 'version'-Feld in den Metadaten")

    if not last_updated:
        if validation_level == STRICT:
            logging.error(f"Fehler: Fehlendes 'last_updated'-Feld in den Metadaten")
            return False
        else:
            logging.warn(f"Warnung: Fehlendes 'last_updated'-Feld in den Metadaten")

    if not author:
        if validation_level == STRICT:
            logging.error(f"Fehler: Fehlendes 'author'-Feld in den Metadaten")
            return False
        else:
            logging.warn(f"Warnung: Fehlendes 'author'-Feld in den Metadaten")

    logging.success(f"✓ Metadaten-Validierung bestanden")
    return True


def validate_components(file_path: str, validation_level: int = STRICT) -> bool:
    """
    Validiert die Komponenten-Datei gegen das Schema.

    Args:
        file_path: Pfad zur Komponenten-Datei
        validation_level: Validierungsstufe (STRICT oder WARNING_ONLY)

    Returns:
        bool: True, wenn die Datei gültig ist, sonst False
    """
    logging.info(f"Validiere Komponenten-Datei: {file_path}")

    # Prüfen, ob die Datei existiert und gültige YAML ist
    if not validate_yaml(file_path):
        return False

    # Metadaten validieren
    metadata_valid = validate_metadata(file_path, ".", validation_level)
    if not metadata_valid and validation_level == STRICT:
        return False

    # YAML-Datei laden
    try:
        with open(file_path) as f:
            data = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Fehler beim Laden der YAML-Datei {file_path}: {str(e)}")
        return False

    # Prüfen, ob der Komponenten-Abschnitt existiert
    if "components" not in data:
        logging.error(f"Fehler: Fehlender 'components'-Abschnitt in {file_path}")
        return False

    # Jede Komponente prüfen
    components = data["components"]
    logging.info(f"Gefunden: {len(components)} Komponenten")

    for i, component in enumerate(components):
        name = component.get("name")
        type_ = component.get("type")
        purpose = component.get("purpose")

        # Erforderliche Felder prüfen
        if not name:
            logging.error(f"Fehler: Komponente #{i} fehlt das 'name'-Feld")
            return False

        if not type_:
            logging.error(f"Fehler: Komponente '{name}' fehlt das 'type'-Feld")
            return False

        if not purpose:
            logging.error(f"Fehler: Komponente '{name}' fehlt das 'purpose'-Feld")
            return False

        logging.success(f"✓ Komponente '{name}' ({type_}) ist gültig")

    logging.success(f"✓ Komponenten-Validierung bestanden")
    return True


def validate_relationships(file_path: str, validation_level: int = STRICT) -> bool:
    """
    Validiert die Beziehungen-Datei gegen das Schema.

    Args:
        file_path: Pfad zur Beziehungen-Datei
        validation_level: Validierungsstufe (STRICT oder WARNING_ONLY)

    Returns:
        bool: True, wenn die Datei gültig ist, sonst False
    """
    logging.info(f"Validiere Beziehungen-Datei: {file_path}")

    # Prüfen, ob die Datei existiert und gültige YAML ist
    if not validate_yaml(file_path):
        return False

    # Metadaten validieren
    metadata_valid = validate_metadata(file_path, ".", validation_level)
    if not metadata_valid and validation_level == STRICT:
        return False

    # YAML-Datei laden
    try:
        with open(file_path) as f:
            data = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Fehler beim Laden der YAML-Datei {file_path}: {str(e)}")
        return False

    # Prüfen, ob der Beziehungen-Abschnitt existiert
    if "relationships" not in data:
        logging.error(f"Fehler: Fehlender 'relationships'-Abschnitt in {file_path}")
        return False

    # Jede Beziehung prüfen
    relationships = data["relationships"]
    logging.info(f"Gefunden: {len(relationships)} Beziehungen")

    for i, relationship in enumerate(relationships):
        source = relationship.get("source")
        target = relationship.get("target")
        type_ = relationship.get("type")
        description = relationship.get("description")

        # Erforderliche Felder prüfen
        if not source:
            logging.error(f"Fehler: Beziehung #{i} fehlt das 'source'-Feld")
            return False

        if not target:
            logging.error(f"Fehler: Beziehung von '{source}' fehlt das 'target'-Feld")
            return False

        if not type_:
            logging.error(
                f"Fehler: Beziehung von '{source}' zu '{target}' fehlt das 'type'-Feld"
            )
            return False

        if not description:
            logging.error(
                f"Fehler: Beziehung von '{source}' zu '{target}' fehlt das 'description'-Feld"
            )
            return False

        logging.success(
            f"✓ Beziehung von '{source}' zu '{target}' ({type_}) ist gültig"
        )

    logging.success(f"✓ Beziehungen-Validierung bestanden")
    return True


def validate_interfaces(file_path: str, validation_level: int = STRICT) -> bool:
    """
    Validiert die Schnittstellen-Datei gegen das Schema.

    Args:
        file_path: Pfad zur Schnittstellen-Datei
        validation_level: Validierungsstufe (STRICT oder WARNING_ONLY)

    Returns:
        bool: True, wenn die Datei gültig ist, sonst False
    """
    logging.info(f"Validiere Schnittstellen-Datei: {file_path}")

    # Prüfen, ob die Datei existiert und gültige YAML ist
    if not validate_yaml(file_path):
        return False

    # Metadaten validieren
    metadata_valid = validate_metadata(file_path, ".", validation_level)
    if not metadata_valid and validation_level == STRICT:
        return False

    logging.success(f"✓ Schnittstellen-Validierung bestanden")
    return True


def validate_diagrams(file_path: str, validation_level: int = STRICT) -> bool:
    """
    Validiert die Diagramm-Datei gegen das Schema.

    Args:
        file_path: Pfad zur Diagramm-Datei
        validation_level: Validierungsstufe (STRICT oder WARNING_ONLY)

    Returns:
        bool: True, wenn die Datei gültig ist, sonst False
    """
    if os.path.isfile(file_path):
        logging.info(f"Validiere Diagramm-Datei: {file_path}")

        # Prüfen, ob die Datei existiert und gültige YAML ist
        if not validate_yaml(file_path):
            return False

        # Metadaten validieren
        metadata_valid = validate_metadata(file_path, ".", validation_level)
        if not metadata_valid and validation_level == STRICT:
            return False

        logging.success(f"✓ Diagramm-Validierung bestanden")
    else:
        logging.warn(f"Warnung: Diagramm-Datei nicht gefunden: {file_path}")

    return True


def validate_cross_references(components_file: str, relationships_file: str) -> bool:
    """
    Validiert die Querverweise zwischen Dateien.

    Args:
        components_file: Pfad zur Komponenten-Datei
        relationships_file: Pfad zur Beziehungen-Datei

    Returns:
        bool: True, wenn die Querverweise gültig sind, sonst False
    """
    logging.info("Validiere Querverweise zwischen Dateien")

    # Komponenten-Datei laden
    try:
        with open(components_file) as f:
            components_data = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Fehler beim Laden der YAML-Datei {components_file}: {str(e)}")
        return False

    # Beziehungen-Datei laden
    try:
        with open(relationships_file) as f:
            relationships_data = yaml.safe_load(f)
    except Exception as e:
        logging.error(
            f"Fehler beim Laden der YAML-Datei {relationships_file}: {str(e)}"
        )
        return False

    # Alle Komponentennamen abrufen
    components = []
    for component in components_data.get("components", []):
        name = component.get("name")
        if name:
            components.append(name)

    # Prüfen, ob Beziehungen auf gültige Komponenten verweisen
    for i, relationship in enumerate(relationships_data.get("relationships", [])):
        source = relationship.get("source")
        target = relationship.get("target")

        # Netzwerk- und Konfigurationsabhängigkeiten überspringen
        if target and (
            "network" in target
            or "config" in target
            or ".env" in target
            or ".yaml" in target
            or ".yml" in target
        ):
            continue

        # Externe Abhängigkeiten überspringen
        if target in ["docker", "docker-compose"]:
            continue

        # Prüfen, ob die Quellkomponente existiert
        if source and source not in components:
            logging.warn(
                f"Warnung: Beziehung #{i} verweist auf Quellkomponente '{source}', die nicht dokumentiert ist"
            )

        # Prüfen, ob die Zielkomponente existiert
        if target and target not in components:
            logging.warn(
                f"Warnung: Beziehung #{i} verweist auf Zielkomponente '{target}', die nicht dokumentiert ist"
            )

    logging.success(f"✓ Querverweis-Validierung bestanden")
    return True


def main() -> int:
    """
    Hauptfunktion für die direkte Ausführung des Skripts.

    Returns:
        int: Exit-Code (0 bei Erfolg, 1 bei Fehler)
    """
    # Kommandozeilenargumente parsen
    parser = argparse.ArgumentParser(
        description="Validiert Dokumentationsdateien gegen Schema"
    )
    parser.add_argument(
        "--warning-only",
        action="store_true",
        help="Nur Warnungen anzeigen, nicht bei Warnungen fehlschlagen",
    )
    args = parser.parse_args()

    # Validierungsstufe festlegen
    validation_level = WARNING_ONLY if args.warning_only else STRICT

    # Projektverzeichnis ermitteln
    project_root = system.get_project_root()

    # Dokumentationsdateien
    components_file = os.path.join(project_root, "docs", "system", "components.yaml")
    relationships_file = os.path.join(
        project_root, "docs", "system", "relationships.yaml"
    )
    interfaces_file = os.path.join(project_root, "docs", "system", "interfaces.yaml")
    diagrams_file = os.path.join(project_root, "docs", "system", "diagrams.yaml")

    logging.info("Starte Dokumentationsvalidierung...")

    # Jede Datei validieren
    components_valid = validate_components(components_file, validation_level)
    relationships_valid = validate_relationships(relationships_file, validation_level)
    interfaces_valid = validate_interfaces(interfaces_file, validation_level)
    diagrams_valid = validate_diagrams(diagrams_file, validation_level)

    # Querverweise validieren, wenn alle Dateien gültig sind
    if components_valid and relationships_valid and interfaces_valid:
        cross_references_valid = validate_cross_references(
            components_file, relationships_file
        )
    else:
        cross_references_valid = False

    # Gesamtergebnis der Validierung prüfen
    if (
        components_valid
        and relationships_valid
        and interfaces_valid
        and diagrams_valid
        and cross_references_valid
    ):
        logging.success("Alle Dokumentationsdateien sind gültig!")
        return 0
    else:
        logging.error("Dokumentationsvalidierung fehlgeschlagen!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
