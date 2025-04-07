"""
Bildet Beziehungen zwischen Entitäten ab.

Dieses Skript identifiziert Funktionsaufrufabhängigkeiten, Komponenteninteraktionen und Konfigurationsabhängigkeiten.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

from llm_stack.core import error, logging, system


def check_dependencies() -> bool:
    """
    Prüft, ob die erforderlichen Tools installiert sind.

    Returns:
        bool: True, wenn alle Abhängigkeiten erfüllt sind, sonst False
    """
    try:
        import json
        import re

        return True
    except ImportError as e:
        logging.error(f"Fehler: {str(e)}")
        return False


def create_relationships_directory(relationships_dir: str) -> bool:
    """
    Erstellt das Beziehungen-Verzeichnis, falls es nicht existiert.

    Args:
        relationships_dir: Pfad zum Beziehungen-Verzeichnis

    Returns:
        bool: True, wenn das Verzeichnis erstellt wurde oder bereits existiert, sonst False
    """
    if not os.path.isdir(relationships_dir):
        try:
            os.makedirs(relationships_dir)
            logging.info(f"Beziehungen-Verzeichnis erstellt: {relationships_dir}")
            return True
        except Exception as e:
            logging.error(
                f"Fehler beim Erstellen des Beziehungen-Verzeichnisses: {str(e)}"
            )
            return False
    return True


def map_function_calls(entities_dir: str, relationships_dir: str) -> bool:
    """
    Bildet Funktionsaufrufabhängigkeiten ab.

    Args:
        entities_dir: Pfad zum Entitäten-Verzeichnis
        relationships_dir: Pfad zum Beziehungen-Verzeichnis

    Returns:
        bool: True bei Erfolg, sonst False
    """
    output_file = os.path.join(relationships_dir, "function_calls.json")

    logging.info("Bilde Funktionsaufrufabhängigkeiten ab...")

    # Funktionsaufrufdatei initialisieren
    with open(output_file, "w") as f:
        json.dump([], f)

    # Funktionen aus Entitäten laden
    functions_file = os.path.join(entities_dir, "functions.json")

    if not os.path.isfile(functions_file):
        logging.warn(f"Warnung: Funktionsdatei nicht gefunden: {functions_file}")
        return False

    try:
        with open(functions_file) as f:
            functions_data = json.load(f)
    except Exception as e:
        logging.error(f"Fehler beim Laden der Funktionsdatei: {str(e)}")
        return False

    # Alle Funktionsnamen abrufen
    function_names = [function.get("name", "") for function in functions_data]

    # Für jede Funktion Aufrufe zu anderen Funktionen finden
    for function in functions_data:
        function_name = function.get("name", "")
        function_id = function.get("@id", "")
        file_path = function.get("filePath", "")
        line_number = function.get("lineNumber", 0)

        logging.info(f"Analysiere Funktionsaufrufe für: {function_name}")

        # Funktionskörper extrahieren
        function_body = ""
        try:
            with open(file_path) as f:
                lines = f.readlines()

            in_function = False
            brace_count = 0
            end_line = line_number

            # Datei zeilenweise lesen, um den Funktionskörper zu extrahieren
            for i in range(line_number - 1, len(lines)):
                line = lines[i]

                if in_function:
                    function_body += line

                    # Öffnende und schließende Klammern zählen
                    open_braces = line.count("{")
                    close_braces = line.count("}")
                    brace_count += open_braces - close_braces

                    # Wenn die Klammerzahl 0 ist, haben wir das Ende der Funktion erreicht
                    if brace_count == 0:
                        break

                    end_line += 1
                elif end_line == line_number:
                    function_body += line
                    in_function = True

                    # Öffnende Klammern in der ersten Zeile zählen
                    open_braces = line.count("{")
                    brace_count = open_braces

                    end_line += 1
        except Exception as e:
            logging.error(
                f"Fehler beim Extrahieren des Funktionskörpers für {function_name}: {str(e)}"
            )
            continue

        # Für jede andere Funktion prüfen, ob sie in dieser Funktion aufgerufen wird
        for called_function_name in function_names:
            # Selbstaufrufe überspringen
            if called_function_name == function_name:
                continue

            # Prüfen, ob die Funktion aufgerufen wird
            if re.search(
                rf"{re.escape(called_function_name)}[[:space:]]*\(", function_body
            ):
                logging.info(
                    f"Aufruf gefunden von {function_name} zu {called_function_name}"
                )

                # Details der aufgerufenen Funktion abrufen
                called_function = next(
                    (
                        f
                        for f in functions_data
                        if f.get("name") == called_function_name
                    ),
                    None,
                )

                if called_function:
                    called_function_id = called_function.get("@id", "")

                    # Funktionsaufrufbeziehung erstellen
                    call_relationship = {
                        "@id": f"llm:call_{function_name}_{called_function_name}",
                        "@type": "llm:Calls",
                        "name": f"{function_name}_calls_{called_function_name}",
                        "description": f"Function {function_name} calls function {called_function_name}",
                        "source": function_id,
                        "target": called_function_id,
                    }

                    # Funktionsaufruf zur Ausgabedatei hinzufügen
                    try:
                        with open(output_file) as f:
                            function_calls_data = json.load(f)

                        function_calls_data.append(call_relationship)

                        with open(output_file, "w") as f:
                            json.dump(function_calls_data, f, indent=2)

                        logging.info(
                            f"Funktionsaufruf hinzugefügt: {function_name} -> {called_function_name}"
                        )
                    except Exception as e:
                        logging.error(
                            f"Fehler beim Hinzufügen des Funktionsaufrufs: {str(e)}"
                        )

    logging.success("Funktionsaufrufabhängigkeiten abgebildet")
    return True


def map_component_dependencies(root_dir: str, relationships_dir: str) -> bool:
    """
    Bildet Komponentenabhängigkeiten aus YAML-Dokumentation ab.

    Args:
        root_dir: Pfad zum Wurzelverzeichnis
        relationships_dir: Pfad zum Beziehungen-Verzeichnis

    Returns:
        bool: True bei Erfolg, sonst False
    """
    relationships_file = os.path.join(root_dir, "docs", "system", "relationships.yaml")
    output_file = os.path.join(relationships_dir, "component_dependencies.json")

    logging.info("Bilde Komponentenabhängigkeiten ab...")

    # Prüfen, ob die Beziehungsdatei existiert
    if not os.path.isfile(relationships_file):
        logging.warn(f"Warnung: Beziehungsdatei nicht gefunden: {relationships_file}")
        return False

    # Komponentenabhängigkeitsdatei initialisieren
    with open(output_file, "w") as f:
        json.dump([], f)

    try:
        # YAML-Datei laden
        with open(relationships_file) as f:
            relationships_data = yaml.safe_load(f)

        # Abhängigkeitsblöcke extrahieren
        dependencies = []
        for relationship in relationships_data.get("relationships", []):
            if relationship.get("type") == "depends_on":
                dependencies.append(relationship)

        # Komponentenabhängigkeitsdaten initialisieren
        component_dependencies_data = []

        # Jeden Abhängigkeitsblock verarbeiten
        for dependency in dependencies:
            source = dependency.get("source")
            target = dependency.get("target")
            description = dependency.get("description")

            # Überspringen, wenn erforderliche Felder fehlen
            if not source or not target or not description:
                continue

            logging.info(f"Abhängigkeit gefunden: {source} hängt von {target} ab")

            # Abhängigkeitsbeziehung erstellen
            dependency_relationship = {
                "@id": f"llm:dependency_{source}_{target}",
                "@type": "llm:DependsOn",
                "name": f"{source}_depends_on_{target}",
                "description": description,
                "source": f"llm:{source}",
                "target": f"llm:{target}",
            }

            # Abhängigkeit zu den Daten hinzufügen
            component_dependencies_data.append(dependency_relationship)

            logging.info(f"Abhängigkeit hinzugefügt: {source} -> {target}")

        # Daten in die Ausgabedatei schreiben
        with open(output_file, "w") as f:
            json.dump(component_dependencies_data, f, indent=2)
    except Exception as e:
        logging.error(f"Fehler beim Abbilden von Komponentenabhängigkeiten: {str(e)}")
        return False

    logging.success("Komponentenabhängigkeiten abgebildet")
    return True


def map_config_dependencies(entities_dir: str, relationships_dir: str) -> bool:
    """
    Bildet Konfigurationsabhängigkeiten ab.

    Args:
        entities_dir: Pfad zum Entitäten-Verzeichnis
        relationships_dir: Pfad zum Beziehungen-Verzeichnis

    Returns:
        bool: True bei Erfolg, sonst False
    """
    output_file = os.path.join(relationships_dir, "config_dependencies.json")

    logging.info("Bilde Konfigurationsabhängigkeiten ab...")

    # Konfigurationsabhängigkeitsdatei initialisieren
    with open(output_file, "w") as f:
        json.dump([], f)

    # Funktionen aus Entitäten laden
    functions_file = os.path.join(entities_dir, "functions.json")
    config_params_file = os.path.join(entities_dir, "config_params.json")

    if not os.path.isfile(functions_file):
        logging.warn(f"Warnung: Funktionsdatei nicht gefunden: {functions_file}")
        return False

    if not os.path.isfile(config_params_file):
        logging.warn(
            f"Warnung: Konfigurationsparameterdatei nicht gefunden: {config_params_file}"
        )
        return False

    try:
        with open(functions_file) as f:
            functions_data = json.load(f)

        with open(config_params_file) as f:
            config_params_data = json.load(f)
    except Exception as e:
        logging.error(f"Fehler beim Laden der Entitätsdateien: {str(e)}")
        return False

    # Konfigurationsabhängigkeitsdaten initialisieren
    config_dependencies_data = []

    # Für jede Funktion Referenzen zu Konfigurationsparametern finden
    for function in functions_data:
        function_name = function.get("name", "")
        function_id = function.get("@id", "")
        file_path = function.get("filePath", "")

        # Überspringen, wenn erforderliche Felder fehlen
        if not function_name or not function_id or not file_path:
            continue

        logging.info(
            f"Analysiere Konfigurationsabhängigkeiten für Funktion: {function_name}"
        )

        # Für jeden Konfigurationsparameter prüfen, ob er in der Funktion referenziert wird
        for config_param in config_params_data:
            param_name = config_param.get("name", "")
            param_id = config_param.get("@id", "")

            # Überspringen, wenn erforderliche Felder fehlen
            if not param_name or not param_id:
                continue

            # Prüfen, ob der Parameter in der Funktion referenziert wird
            try:
                with open(file_path) as f:
                    content = f.read()

                if re.search(rf'get_config.*"{re.escape(param_name)}"', content):
                    logging.info(
                        f"Konfigurationsabhängigkeit gefunden: {function_name} verwendet {param_name}"
                    )

                    # Konfigurationsabhängigkeitsbeziehung erstellen
                    config_dependency = {
                        "@id": f"llm:config_dependency_{function_name}_{param_name}",
                        "@type": "llm:Configures",
                        "name": f"{function_name}_uses_{param_name}",
                        "description": f"Function {function_name} uses configuration parameter {param_name}",
                        "source": function_id,
                        "target": param_id,
                    }

                    # Konfigurationsabhängigkeit zu den Daten hinzufügen
                    config_dependencies_data.append(config_dependency)

                    logging.info(
                        f"Konfigurationsabhängigkeit hinzugefügt: {function_name} -> {param_name}"
                    )
            except Exception as e:
                logging.error(
                    f"Fehler beim Analysieren der Datei {file_path}: {str(e)}"
                )

    # Daten in die Ausgabedatei schreiben
    try:
        with open(output_file, "w") as f:
            json.dump(config_dependencies_data, f, indent=2)
    except Exception as e:
        logging.error(
            f"Fehler beim Schreiben der Konfigurationsabhängigkeitsdatei: {str(e)}"
        )
        return False

    logging.success("Konfigurationsabhängigkeiten abgebildet")
    return True


def map_imports(root_dir: str, relationships_dir: str) -> bool:
    """
    Bildet Importbeziehungen ab.

    Args:
        root_dir: Pfad zum Wurzelverzeichnis
        relationships_dir: Pfad zum Beziehungen-Verzeichnis

    Returns:
        bool: True bei Erfolg, sonst False
    """
    output_file = os.path.join(relationships_dir, "imports.json")

    logging.info("Bilde Importbeziehungen ab...")

    # Importdatei initialisieren
    with open(output_file, "w") as f:
        json.dump([], f)

    # Alle Shell-Skripte finden
    shell_scripts = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".sh"):
                shell_scripts.append(os.path.join(root, file))

    # Importdaten initialisieren
    imports_data = []

    # Jedes Skript verarbeiten
    for script in shell_scripts:
        script_name = os.path.basename(script)
        module_name = os.path.splitext(script_name)[0]

        logging.info(f"Analysiere Importe für Skript: {script_name}")

        try:
            with open(script) as f:
                content = f.readlines()

            # Source-Anweisungen finden
            for line_num, line in enumerate(content, 1):
                match = re.search(
                    r"^[[:space:]]*source[[:space:]]+\"?([^\"]+)\"?", line
                )
                if match:
                    import_path = match.group(1)

                    # Den Importpfad normalisieren
                    import_path = re.sub(r"\$[A-Z_]+\/", "", import_path)

                    # Den importierten Modulnamen extrahieren
                    imported_module = os.path.basename(import_path)
                    imported_module = os.path.splitext(imported_module)[0]

                    logging.info(
                        f"Import gefunden: {module_name} importiert {imported_module}"
                    )

                    # Importbeziehung erstellen
                    import_relationship = {
                        "@id": f"llm:import_{module_name}_{imported_module}",
                        "@type": "llm:Imports",
                        "name": f"{module_name}_imports_{imported_module}",
                        "description": f"Module {module_name} imports module {imported_module}",
                        "source": f"llm:{module_name}",
                        "target": f"llm:{imported_module}",
                        "filePath": script,
                        "lineNumber": line_num,
                    }

                    # Import zu den Daten hinzufügen
                    imports_data.append(import_relationship)

                    logging.info(
                        f"Import hinzugefügt: {module_name} -> {imported_module}"
                    )
        except Exception as e:
            logging.error(f"Fehler beim Analysieren der Datei {script}: {str(e)}")

    # Daten in die Ausgabedatei schreiben
    try:
        with open(output_file, "w") as f:
            json.dump(imports_data, f, indent=2)
    except Exception as e:
        logging.error(f"Fehler beim Schreiben der Importdatei: {str(e)}")
        return False

    logging.success("Importbeziehungen abgebildet")
    return True


def map_data_flows(root_dir: str, relationships_dir: str) -> bool:
    """
    Bildet Datenflussbeziehungen aus YAML-Dokumentation ab.

    Args:
        root_dir: Pfad zum Wurzelverzeichnis
        relationships_dir: Pfad zum Beziehungen-Verzeichnis

    Returns:
        bool: True bei Erfolg, sonst False
    """
    interfaces_file = os.path.join(root_dir, "docs", "system", "interfaces.yaml")
    output_file = os.path.join(relationships_dir, "data_flows.json")

    logging.info("Bilde Datenflussbeziehungen ab...")

    # Prüfen, ob die Schnittstellendatei existiert
    if not os.path.isfile(interfaces_file):
        logging.warn(f"Warnung: Schnittstellendatei nicht gefunden: {interfaces_file}")
        return False

    # Datenflussdatei initialisieren
    with open(output_file, "w") as f:
        json.dump([], f)

    try:
        # YAML-Datei laden
        with open(interfaces_file) as f:
            interfaces_data = yaml.safe_load(f)

        # Datenflussblöcke extrahieren
        data_flows = interfaces_data.get("data_flows", [])

        # Datenflussdaten initialisieren
        data_flows_data = []

        # Jeden Datenfluss verarbeiten
        for flow in data_flows:
            flow_name = flow.get("name")
            flow_description = flow.get("description")

            logging.info(f"Verarbeite Datenfluss: {flow_name}")

            # Schritte für diesen Datenfluss extrahieren
            steps = flow.get("steps", [])

            # Jeden Schritt verarbeiten
            for step in steps:
                step_num = step.get("step")
                source = step.get("source")
                target = step.get("target")
                data = step.get("data")
                format_type = step.get("format")
                transport = step.get("transport")

                # Überspringen, wenn erforderliche Felder fehlen
                if not step_num or not source or not target or not data:
                    continue

                logging.info(
                    f"Datenflussschritt gefunden: {source} -> {target} (Daten: {data})"
                )

                # Datenflussbeziehung erstellen
                data_flow_relationship = {
                    "@id": f"llm:dataflow_{flow_name}_step_{step_num}",
                    "@type": "llm:DataFlow",
                    "name": f"{flow_name}_step_{step_num}",
                    "description": f"{source} sends {data} to {target}",
                    "source": f"llm:{source}",
                    "target": f"llm:{target}",
                    "data": data,
                    "format": format_type or "",
                    "transport": transport or "",
                    "stepNumber": step_num,
                    "dataFlow": f"llm:dataflow_{flow_name}",
                }

                # Datenfluss zu den Daten hinzufügen
                data_flows_data.append(data_flow_relationship)

                logging.info(
                    f"Datenfluss hinzugefügt: {source} -> {target} (Schritt {step_num})"
                )

        # Daten in die Ausgabedatei schreiben
        with open(output_file, "w") as f:
            json.dump(data_flows_data, f, indent=2)
    except Exception as e:
        logging.error(f"Fehler beim Abbilden von Datenflussbeziehungen: {str(e)}")
        return False

    logging.success("Datenflussbeziehungen abgebildet")
    return True


def map_all_relationships(
    root_dir: Optional[str] = None,
    specific_file: Optional[str] = None,
    yaml: bool = False,
) -> int:
    """
    Bildet alle Beziehungen ab.

    Args:
        root_dir: Pfad zum Wurzelverzeichnis (optional)
        specific_file: Pfad zu einer spezifischen Datei (optional)
        yaml: Ob nur YAML-Dokumentation verarbeitet werden soll

    Returns:
        int: Exit-Code (0 bei Erfolg, 1 bei Fehler)
    """
    logging.info("Starte Beziehungsabbildung...")

    # Abhängigkeiten prüfen
    if not check_dependencies():
        return 1

    # Projektverzeichnis ermitteln
    if root_dir is None:
        root_dir = system.get_project_root()

    # Ein- und Ausgabeverzeichnisse
    entities_dir = os.path.join(root_dir, "docs", "knowledge-graph", "entities")
    relationships_dir = os.path.join(
        root_dir, "docs", "knowledge-graph", "relationships"
    )

    # Beziehungen-Verzeichnis erstellen
    if not create_relationships_directory(relationships_dir):
        return 1

    # Wenn eine spezifische Datei angegeben ist, nur diese verarbeiten
    if specific_file:
        # Funktionsaufrufabhängigkeiten abbilden
        map_function_calls(entities_dir, relationships_dir)

        # Konfigurationsabhängigkeiten abbilden
        map_config_dependencies(entities_dir, relationships_dir)

        return 0

    # Wenn YAML-Flag gesetzt ist, nur YAML-Dokumentation verarbeiten
    if yaml:
        # Komponentenabhängigkeiten abbilden
        map_component_dependencies(root_dir, relationships_dir)

        # Datenflussbeziehungen abbilden
        map_data_flows(root_dir, relationships_dir)

        return 0

    # Funktionsaufrufabhängigkeiten abbilden
    map_function_calls(entities_dir, relationships_dir)

    # Komponentenabhängigkeiten abbilden
    map_component_dependencies(root_dir, relationships_dir)

    # Konfigurationsabhängigkeiten abbilden
    map_config_dependencies(entities_dir, relationships_dir)

    # Importbeziehungen abbilden
    map_imports(root_dir, relationships_dir)

    # Datenflussbeziehungen abbilden
    map_data_flows(root_dir, relationships_dir)

    logging.success("Beziehungsabbildung erfolgreich abgeschlossen!")
    return 0


def main() -> int:
    """
    Hauptfunktion für die direkte Ausführung des Skripts.

    Returns:
        int: Exit-Code (0 bei Erfolg, 1 bei Fehler)
    """
    # Kommandozeilenargumente parsen
    import argparse

    parser = argparse.ArgumentParser(
        description="Bildet Beziehungen zwischen Entitäten ab"
    )
    parser.add_argument("file", nargs="?", help="Pfad zu einer spezifischen Datei")
    parser.add_argument(
        "--yaml", action="store_true", help="Nur YAML-Dokumentation verarbeiten"
    )
    parser.add_argument("--root-dir", help="Wurzelverzeichnis")
    args = parser.parse_args()

    return map_all_relationships(args.root_dir, args.file, args.yaml)


if __name__ == "__main__":
    sys.exit(main())
