"""
Aktualisiert den Knowledge Graph.

Dieses Skript aktualisiert den Knowledge Graph, wenn Änderungen im Codebase erkannt werden.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from llm_stack.core import error, logging, system


def check_dependencies() -> bool:
    """
    Prüft, ob die erforderlichen Tools installiert sind.

    Returns:
        bool: True, wenn alle Abhängigkeiten erfüllt sind, sonst False
    """
    # Prüfen, ob Git installiert ist
    git_installed = False
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=False)
        git_installed = True
    except FileNotFoundError:
        logging.error(
            "Fehler: Git ist nicht installiert. Bitte installieren Sie es, um Änderungen zu erkennen."
        )
        return False

    return git_installed


def detect_changes(root_dir: str) -> List[str]:
    """
    Erkennt Änderungen im Codebase.

    Args:
        root_dir: Pfad zum Wurzelverzeichnis

    Returns:
        List[str]: Liste der geänderten Dateien
    """
    logging.info("Erkenne Änderungen im Codebase...")

    # Liste der geänderten Dateien seit dem letzten Update abrufen
    last_update_file = os.path.join(root_dir, ".last_kg_update")
    changed_files = []

    try:
        if os.path.isfile(last_update_file):
            with open(last_update_file) as f:
                last_update = f.read().strip()

            # Git-Befehl ausführen, um geänderte Dateien zu erhalten
            result = subprocess.run(
                ["git", "diff", "--name-only", last_update, "HEAD"],
                cwd=root_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                changed_files = result.stdout.strip().split("\n")
                # Leere Einträge entfernen
                changed_files = [f for f in changed_files if f]
            else:
                logging.error(f"Fehler beim Ausführen von git diff: {result.stderr}")
                # Fallback: Alle Dateien betrachten
                result = subprocess.run(
                    ["git", "ls-files"],
                    cwd=root_dir,
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if result.returncode == 0:
                    changed_files = result.stdout.strip().split("\n")
                    # Leere Einträge entfernen
                    changed_files = [f for f in changed_files if f]
                else:
                    logging.error(
                        f"Fehler beim Ausführen von git ls-files: {result.stderr}"
                    )
        else:
            # Wenn kein letztes Update, alle Dateien betrachten
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=root_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                changed_files = result.stdout.strip().split("\n")
                # Leere Einträge entfernen
                changed_files = [f for f in changed_files if f]
            else:
                logging.error(
                    f"Fehler beim Ausführen von git ls-files: {result.stderr}"
                )
    except Exception as e:
        logging.error(f"Fehler beim Erkennen von Änderungen: {str(e)}")

    # Nach Shell-Skripten und YAML-Dokumentation filtern
    shell_scripts = [f for f in changed_files if f.endswith(".sh")]
    yaml_docs = [
        f for f in changed_files if f.endswith(".yaml") and "docs/system/" in f
    ]

    # Ergebnisse kombinieren
    relevant_changes = sorted(set(shell_scripts + yaml_docs))

    return relevant_changes


def update_entities(changed_files: List[str], root_dir: str) -> bool:
    """
    Aktualisiert Entitäten für geänderte Dateien.

    Args:
        changed_files: Liste der geänderten Dateien
        root_dir: Pfad zum Wurzelverzeichnis

    Returns:
        bool: True bei Erfolg, sonst False
    """
    logging.info("Aktualisiere Entitäten für geänderte Dateien...")

    # Prüfen, ob es Shell-Skripte zu verarbeiten gibt
    shell_scripts = [f for f in changed_files if f.endswith(".sh")]

    if shell_scripts:
        logging.info("Verarbeite Shell-Skripte...")

        try:
            # Für jedes geänderte Shell-Skript Entitäten extrahieren
            from llm_stack.tools.entity_extraction import extract_entities

            for script in shell_scripts:
                script_path = os.path.join(root_dir, script)
                logging.info(f"Extrahiere Entitäten aus {script}")
                extract_entities.extract_all_entities(root_dir, script_path)
        except ImportError:
            logging.error("Fehler beim Importieren des entity_extraction-Moduls.")
            logging.info("Führe extract-entities.sh aus...")

            for script in shell_scripts:
                script_path = os.path.join(root_dir, script)
                try:
                    subprocess.run(
                        [
                            os.path.join(
                                root_dir,
                                "tools",
                                "entity-extraction",
                                "extract-entities.sh",
                            ),
                            script_path,
                        ],
                        check=True,
                    )
                except Exception as e:
                    logging.error(
                        f"Fehler beim Ausführen von extract-entities.sh für {script}: {str(e)}"
                    )
                    return False

    # Prüfen, ob es YAML-Dokumentationsdateien zu verarbeiten gibt
    yaml_docs = [
        f for f in changed_files if f.endswith(".yaml") and "docs/system/" in f
    ]

    if yaml_docs:
        logging.info("Verarbeite YAML-Dokumentation...")

        try:
            # Komponenten und Dienste aus YAML-Dokumentation extrahieren
            from llm_stack.tools.entity_extraction import extract_entities

            extract_entities.extract_all_entities(root_dir, yaml=True)
        except ImportError:
            logging.error("Fehler beim Importieren des entity_extraction-Moduls.")
            logging.info("Führe extract-entities.sh aus...")
            try:
                subprocess.run(
                    [
                        os.path.join(
                            root_dir,
                            "tools",
                            "entity-extraction",
                            "extract-entities.sh",
                        ),
                        "--yaml",
                    ],
                    check=True,
                )
            except Exception as e:
                logging.error(
                    f"Fehler beim Ausführen von extract-entities.sh für YAML: {str(e)}"
                )
                return False

    logging.success("Entitätsaktualisierung abgeschlossen!")
    return True


def update_relationships(changed_files: List[str], root_dir: str) -> bool:
    """
    Aktualisiert Beziehungen für geänderte Dateien.

    Args:
        changed_files: Liste der geänderten Dateien
        root_dir: Pfad zum Wurzelverzeichnis

    Returns:
        bool: True bei Erfolg, sonst False
    """
    logging.info("Aktualisiere Beziehungen für geänderte Dateien...")

    # Prüfen, ob es Shell-Skripte zu verarbeiten gibt
    shell_scripts = [f for f in changed_files if f.endswith(".sh")]

    if shell_scripts:
        logging.info("Verarbeite Shell-Skripte...")

        try:
            # Für jedes geänderte Shell-Skript Beziehungen abbilden
            from llm_stack.tools.relationship_mapping import map_relationships

            for script in shell_scripts:
                script_path = os.path.join(root_dir, script)
                logging.info(f"Bilde Beziehungen aus {script} ab")
                map_relationships.map_all_relationships(root_dir, script_path)
        except ImportError:
            logging.error("Fehler beim Importieren des relationship_mapping-Moduls.")
            logging.info("Führe map-relationships.sh aus...")

            for script in shell_scripts:
                script_path = os.path.join(root_dir, script)
                try:
                    subprocess.run(
                        [
                            os.path.join(
                                root_dir,
                                "tools",
                                "relationship-mapping",
                                "map-relationships.sh",
                            ),
                            script_path,
                        ],
                        check=True,
                    )
                except Exception as e:
                    logging.error(
                        f"Fehler beim Ausführen von map-relationships.sh für {script}: {str(e)}"
                    )
                    return False

    # Prüfen, ob es YAML-Dokumentationsdateien zu verarbeiten gibt
    yaml_docs = [
        f for f in changed_files if f.endswith(".yaml") and "docs/system/" in f
    ]

    if yaml_docs:
        logging.info("Verarbeite YAML-Dokumentation...")

        try:
            # Beziehungen aus YAML-Dokumentation abbilden
            from llm_stack.tools.relationship_mapping import map_relationships

            map_relationships.map_all_relationships(root_dir, yaml=True)
        except ImportError:
            logging.error("Fehler beim Importieren des relationship_mapping-Moduls.")
            logging.info("Führe map-relationships.sh aus...")
            try:
                subprocess.run(
                    [
                        os.path.join(
                            root_dir,
                            "tools",
                            "relationship-mapping",
                            "map-relationships.sh",
                        ),
                        "--yaml",
                    ],
                    check=True,
                )
            except Exception as e:
                logging.error(
                    f"Fehler beim Ausführen von map-relationships.sh für YAML: {str(e)}"
                )
                return False

    logging.success("Beziehungsaktualisierung abgeschlossen!")
    return True


def regenerate_graph(root_dir: str) -> bool:
    """
    Regeneriert den Knowledge Graph.

    Args:
        root_dir: Pfad zum Wurzelverzeichnis

    Returns:
        bool: True bei Erfolg, sonst False
    """
    logging.info("Regeneriere den Knowledge Graph...")

    try:
        # Knowledge Graph generieren
        from llm_stack.tools.knowledge_graph import generate_graph

        result = generate_graph.main()
        return result == 0
    except ImportError:
        logging.error("Fehler beim Importieren des generate_graph-Moduls.")
        logging.info("Führe generate-graph.sh aus...")
        try:
            subprocess.run(
                [
                    os.path.join(
                        root_dir, "tools", "knowledge-graph", "generate-graph.sh"
                    )
                ],
                check=True,
            )
            return True
        except Exception as e:
            logging.error(f"Fehler beim Ausführen von generate-graph.sh: {str(e)}")
            return False


def update_timestamp(root_dir: str) -> bool:
    """
    Aktualisiert den Zeitstempel der letzten Aktualisierung.

    Args:
        root_dir: Pfad zum Wurzelverzeichnis

    Returns:
        bool: True bei Erfolg, sonst False
    """
    logging.info("Aktualisiere Zeitstempel der letzten Aktualisierung...")

    try:
        # Aktuellen Commit-Hash abrufen
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            current_commit = result.stdout.strip()

            # Aktuellen Commit-Hash als letzte Aktualisierung speichern
            last_update_file = os.path.join(root_dir, ".last_kg_update")
            with open(last_update_file, "w") as f:
                f.write(current_commit)

            logging.info(
                f"Zeitstempel der letzten Aktualisierung auf {current_commit} gesetzt"
            )
            return True
        else:
            logging.error(
                f"Fehler beim Abrufen des aktuellen Commit-Hashs: {result.stderr}"
            )
            return False
    except Exception as e:
        logging.error(f"Fehler beim Aktualisieren des Zeitstempels: {str(e)}")
        return False


def main() -> int:
    """
    Hauptfunktion für die direkte Ausführung des Skripts.

    Returns:
        int: Exit-Code (0 bei Erfolg, 1 bei Fehler)
    """
    logging.info("Starte Knowledge Graph-Aktualisierung...")

    # Abhängigkeiten prüfen
    if not check_dependencies():
        return 1

    # Projektverzeichnis ermitteln
    root_dir = system.get_project_root()

    # Änderungen im Codebase erkennen
    changed_files = detect_changes(root_dir)

    # Wenn keine Änderungen, beenden
    if not changed_files:
        logging.info(
            "Keine relevanten Änderungen erkannt. Knowledge Graph ist aktuell."
        )
        return 0

    logging.info("Änderungen in folgenden Dateien erkannt:")
    for file in changed_files:
        logging.info(f"  {file}")

    # Entitäten für geänderte Dateien aktualisieren
    if not update_entities(changed_files, root_dir):
        return 1

    # Beziehungen für geänderte Dateien aktualisieren
    if not update_relationships(changed_files, root_dir):
        return 1

    # Knowledge Graph regenerieren
    if not regenerate_graph(root_dir):
        return 1

    # Zeitstempel der letzten Aktualisierung aktualisieren
    if not update_timestamp(root_dir):
        return 1

    logging.success("Knowledge Graph-Aktualisierung erfolgreich abgeschlossen!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
