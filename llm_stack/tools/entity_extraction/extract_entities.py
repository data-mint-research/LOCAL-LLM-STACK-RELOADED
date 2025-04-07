"""
Extrahiert Entitäten aus Shell-Skripten.

Dieses Skript extrahiert Funktionen, Variablen, Komponenten und andere Entitäten aus Shell-Skripten.
"""

import json
import os
import re
import sys
import tempfile
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


def create_entities_directory(entities_dir: str) -> bool:
    """
    Erstellt das Entitäten-Verzeichnis, falls es nicht existiert.

    Args:
        entities_dir: Pfad zum Entitäten-Verzeichnis

    Returns:
        bool: True, wenn das Verzeichnis erstellt wurde oder bereits existiert, sonst False
    """
    if not os.path.isdir(entities_dir):
        try:
            os.makedirs(entities_dir)
            logging.info(f"Entitäten-Verzeichnis erstellt: {entities_dir}")
            return True
        except Exception as e:
            logging.error(
                f"Fehler beim Erstellen des Entitäten-Verzeichnisses: {str(e)}"
            )
            return False
    return True


def extract_functions(file_path: str, output_file: str) -> bool:
    """
    Extrahiert Funktionen aus einem Shell-Skript.

    Args:
        file_path: Pfad zum Shell-Skript
        output_file: Pfad zur Ausgabedatei

    Returns:
        bool: True bei Erfolg, sonst False
    """
    file_name = os.path.basename(file_path)
    module_name = os.path.splitext(file_name)[0]

    logging.info(f"Extrahiere Funktionen aus {file_path}")

    # Initialisieren oder laden der vorhandenen Funktionsdatei
    if not os.path.isfile(output_file):
        with open(output_file, "w") as f:
            json.dump([], f)

    try:
        with open(output_file) as f:
            functions_data = json.load(f)
    except Exception as e:
        logging.error(f"Fehler beim Laden der Funktionsdatei: {str(e)}")
        return False

    # Dateiinhalt lesen
    try:
        with open(file_path) as f:
            content = f.read()
            lines = content.splitlines()
    except Exception as e:
        logging.error(f"Fehler beim Lesen der Datei {file_path}: {str(e)}")
        return False

    # Funktionsdefinitionen extrahieren
    # Muster: function_name() { oder function function_name {
    function_pattern = re.compile(r"(^[a-zA-Z0-9_]+\(\))|^function [a-zA-Z0-9_]+ \{")

    for line_num, line in enumerate(lines, 1):
        match = function_pattern.search(line)
        if match:
            # Funktionsname extrahieren
            if "function " in line:
                function_name = re.search(r"function ([a-zA-Z0-9_]+)", line).group(1)
            else:
                function_name = re.search(r"([a-zA-Z0-9_]+)\(\)", line).group(1)

            logging.info(f"Funktion gefunden: {function_name} in Zeile {line_num}")

            # Funktionsbeschreibung aus Kommentaren darüber extrahieren
            description = ""
            start_line = (
                line_num - 2
            )  # -1 für 0-basierter Index, -1 für vorherige Zeile

            while start_line >= 0:
                prev_line = lines[start_line]
                comment_match = re.match(r"^[[:space:]]*#[[:space:]]*(.*)", prev_line)
                if comment_match:
                    if not description:
                        description = comment_match.group(1)
                    else:
                        description = f"{comment_match.group(1)}. {description}"
                    start_line -= 1
                else:
                    break

            # Wenn keine Beschreibung gefunden wurde, eine generische verwenden
            if not description:
                description = f"Function {function_name} in {file_name}"

            # Funktionskörper extrahieren
            function_body = ""
            in_function = True
            brace_count = (
                1  # Die öffnende Klammer ist bereits in der Funktionsdefinition
            )
            end_line = line_num

            while end_line < len(lines) and in_function:
                current_line = lines[end_line]
                function_body += current_line + "\n"

                # Öffnende und schließende Klammern zählen
                open_braces = current_line.count("{")
                close_braces = current_line.count("}")
                brace_count += open_braces - close_braces

                # Wenn die Klammerzahl 0 ist, haben wir das Ende der Funktion erreicht
                if brace_count == 0:
                    in_function = False

                end_line += 1

            # Parameter extrahieren
            # Nach Variablenreferenzen wie $1, $2 usw. suchen
            param_refs = re.findall(r"\$([0-9]+)", function_body)

            # Auch nach Parametervalidierung wie [[ -z "$1" ]] suchen
            param_validations = re.findall(
                r'\[\[ -[a-z] "\$([0-9]+)" \]\]', function_body
            )

            # Beide Parametersets kombinieren
            all_params = sorted(set(param_refs + param_validations))

            # Parameter in JSON-Array konvertieren
            param_json = []
            for param_num in all_params:
                # Nach Parameterbeschreibung in Kommentaren suchen
                param_desc = ""
                param_pattern = f"\\${param_num}"
                param_comment_pattern = re.compile(f"#.*{param_pattern}")

                for body_line in function_body.splitlines():
                    param_comment_match = param_comment_pattern.search(body_line)
                    if param_comment_match:
                        param_desc_match = re.search(
                            f"#[[:space:]]*(.*{param_pattern}[^:]*):?[[:space:]]*(.*)",
                            body_line,
                        )
                        if param_desc_match:
                            param_desc = param_desc_match.group(2)
                            break

                # Wenn keine Beschreibung gefunden wurde, eine generische verwenden
                if not param_desc:
                    param_desc = f"Parameter {param_num}"

                # Parameter zum JSON-Array hinzufügen
                param_json.append(
                    {
                        "name": f"param{param_num}",
                        "description": param_desc,
                        "type": "string",
                        "required": True,
                    }
                )

            # Rückgabewert extrahieren
            return_type = "void"
            return_desc = "No return value"

            # Nach return-Anweisungen suchen
            return_stmt_pattern = re.compile(
                r"return[[:space:]]+([^$]*\$?[a-zA-Z0-9_]+)"
            )
            return_stmt_match = return_stmt_pattern.search(function_body)

            if return_stmt_match:
                return_val = return_stmt_match.group(1).strip()

                # Wenn der Rückgabewert eine Zahl ist, handelt es sich wahrscheinlich um einen Fehlercode
                if re.match(r"^[0-9]+$", return_val):
                    return_type = "integer"
                    return_desc = f"Error code ({return_val})"
                elif return_val.startswith("$ERR_"):
                    return_type = "integer"
                    return_desc = f"Error code ({return_val[1:]})"
                else:
                    return_type = "string"
                    return_desc = "Return value"

            # Funktionsentität erstellen
            function_entity = {
                "@id": f"llm:{module_name}_{function_name}",
                "@type": "llm:Function",
                "name": function_name,
                "description": description,
                "filePath": file_path,
                "lineNumber": line_num,
                "parameters": param_json,
                "returnType": return_type,
                "returnDescription": return_desc,
                "module": f"llm:{module_name}",
            }

            # Funktion zur Ausgabedatei hinzufügen
            functions_data.append(function_entity)

            logging.info(f"Funktion hinzugefügt: {function_name}")

    # Aktualisierte Daten in die Ausgabedatei schreiben
    try:
        with open(output_file, "w") as f:
            json.dump(functions_data, f, indent=2)
    except Exception as e:
        logging.error(f"Fehler beim Schreiben der Funktionsdatei: {str(e)}")
        return False

    logging.success(f"Funktionen aus {file_path} extrahiert")
    return True


def extract_variables(file_path: str, output_file: str) -> bool:
    """
    Extrahiert Variablen aus einem Shell-Skript.

    Args:
        file_path: Pfad zum Shell-Skript
        output_file: Pfad zur Ausgabedatei

    Returns:
        bool: True bei Erfolg, sonst False
    """
    file_name = os.path.basename(file_path)
    module_name = os.path.splitext(file_name)[0]

    logging.info(f"Extrahiere Variablen aus {file_path}")

    # Initialisieren oder laden der vorhandenen Variablendatei
    if not os.path.isfile(output_file):
        with open(output_file, "w") as f:
            json.dump([], f)

    try:
        with open(output_file) as f:
            variables_data = json.load(f)
    except Exception as e:
        logging.error(f"Fehler beim Laden der Variablendatei: {str(e)}")
        return False

    # Dateiinhalt lesen
    try:
        with open(file_path) as f:
            content = f.read()
            lines = content.splitlines()
    except Exception as e:
        logging.error(f"Fehler beim Lesen der Datei {file_path}: {str(e)}")
        return False

    # Variablendefinitionen extrahieren
    # Muster: VAR=value oder readonly VAR=value oder export VAR=value
    variable_pattern = re.compile(
        r"^[[:space:]]*(readonly|export)?[[:space:]]*([A-Z0-9_]+)="
    )

    for line_num, line in enumerate(lines, 1):
        match = variable_pattern.search(line)
        if match:
            # Variablenname extrahieren
            variable_name = match.group(2)

            # Überspringen, wenn der Variablenname Leerzeichen enthält
            if " " in variable_name:
                continue

            logging.info(f"Variable gefunden: {variable_name} in Zeile {line_num}")

            # Variablenbeschreibung aus Kommentaren darüber extrahieren
            description = ""
            start_line = (
                line_num - 2
            )  # -1 für 0-basierter Index, -1 für vorherige Zeile

            while start_line >= 0:
                prev_line = lines[start_line]
                comment_match = re.match(r"^[[:space:]]*#[[:space:]]*(.*)", prev_line)
                if comment_match:
                    if not description:
                        description = comment_match.group(1)
                    else:
                        description = f"{comment_match.group(1)}. {description}"
                    start_line -= 1
                else:
                    break

            # Wenn keine Beschreibung gefunden wurde, eine generische verwenden
            if not description:
                description = f"Variable {variable_name} in {file_name}"

            # Variablenwert extrahieren
            variable_value = ""
            value_match = re.search(f'{variable_name}="?([^"]+)"?', line)
            if value_match:
                variable_value = value_match.group(1)

            # Bestimmen, ob die Variable readonly oder exported ist
            is_readonly = "readonly" in line
            is_exported = "export" in line

            # Variablenentität erstellen
            variable_entity = {
                "@id": f"llm:{module_name}_{variable_name}",
                "@type": "llm:Variable",
                "name": variable_name,
                "description": description,
                "filePath": file_path,
                "lineNumber": line_num,
                "value": variable_value,
                "readonly": is_readonly,
                "exported": is_exported,
                "module": f"llm:{module_name}",
            }

            # Variable zur Ausgabedatei hinzufügen
            variables_data.append(variable_entity)

            logging.info(f"Variable hinzugefügt: {variable_name}")

    # Aktualisierte Daten in die Ausgabedatei schreiben
    try:
        with open(output_file, "w") as f:
            json.dump(variables_data, f, indent=2)
    except Exception as e:
        logging.error(f"Fehler beim Schreiben der Variablendatei: {str(e)}")
        return False

    logging.success(f"Variablen aus {file_path} extrahiert")
    return True


def extract_config_params(file_path: str, output_file: str) -> bool:
    """
    Extrahiert Konfigurationsparameter aus einem Shell-Skript.

    Args:
        file_path: Pfad zum Shell-Skript
        output_file: Pfad zur Ausgabedatei

    Returns:
        bool: True bei Erfolg, sonst False
    """
    file_name = os.path.basename(file_path)
    module_name = os.path.splitext(file_name)[0]

    logging.info(f"Extrahiere Konfigurationsparameter aus {file_path}")

    # Initialisieren oder laden der vorhandenen Konfigurationsparameterdatei
    if not os.path.isfile(output_file):
        with open(output_file, "w") as f:
            json.dump([], f)

    try:
        with open(output_file) as f:
            config_params_data = json.load(f)
    except Exception as e:
        logging.error(f"Fehler beim Laden der Konfigurationsparameterdatei: {str(e)}")
        return False

    # Dateiinhalt lesen
    try:
        with open(file_path) as f:
            content = f.read()
            lines = content.splitlines()
    except Exception as e:
        logging.error(f"Fehler beim Lesen der Datei {file_path}: {str(e)}")
        return False

    # Konfigurationsparameterreferenzen extrahieren
    # Muster: get_config "PARAM_NAME" oder get_config "PARAM_NAME" "default_value"
    config_param_pattern = re.compile(r'get_config[[:space:]]*"([A-Z0-9_]+)"')

    for line_num, line in enumerate(lines, 1):
        match = config_param_pattern.search(line)
        if match:
            # Parametername extrahieren
            param_name = match.group(1)

            logging.info(
                f"Konfigurationsparameter gefunden: {param_name} in Zeile {line_num}"
            )

            # Parameterbeschreibung aus Kommentaren darüber extrahieren
            description = ""
            start_line = (
                line_num - 2
            )  # -1 für 0-basierter Index, -1 für vorherige Zeile

            while start_line >= 0:
                prev_line = lines[start_line]
                comment_match = re.match(r"^[[:space:]]*#[[:space:]]*(.*)", prev_line)
                if comment_match:
                    if not description:
                        description = comment_match.group(1)
                    else:
                        description = f"{comment_match.group(1)}. {description}"
                    start_line -= 1
                else:
                    break

            # Wenn keine Beschreibung gefunden wurde, eine generische verwenden
            if not description:
                description = f"Configuration parameter {param_name}"

            # Standardwert extrahieren, falls vorhanden
            default_value = ""
            default_value_match = re.search(
                f'get_config[[:space:]]*"{param_name}"[[:space:]]*"([^"]+)"', line
            )
            if default_value_match:
                default_value = default_value_match.group(1)

            # Konfigurationsparameterentität erstellen
            param_entity = {
                "@id": f"llm:config_{param_name}",
                "@type": "llm:ConfigParam",
                "name": param_name,
                "description": description,
                "filePath": file_path,
                "lineNumber": line_num,
                "defaultValue": default_value,
            }

            # Konfigurationsparameter zur Ausgabedatei hinzufügen
            config_params_data.append(param_entity)

            logging.info(f"Konfigurationsparameter hinzugefügt: {param_name}")

    # Aktualisierte Daten in die Ausgabedatei schreiben
    try:
        with open(output_file, "w") as f:
            json.dump(config_params_data, f, indent=2)
    except Exception as e:
        logging.error(
            f"Fehler beim Schreiben der Konfigurationsparameterdatei: {str(e)}"
        )
        return False

    logging.success(f"Konfigurationsparameter aus {file_path} extrahiert")
    return True


def extract_components(components_file: str, output_file: str) -> bool:
    """
    Extrahiert Komponenten aus der YAML-Dokumentation.

    Args:
        components_file: Pfad zur Komponentendatei
        output_file: Pfad zur Ausgabedatei

    Returns:
        bool: True bei Erfolg, sonst False
    """
    logging.info(f"Extrahiere Komponenten aus {components_file}")

    # Prüfen, ob die Komponentendatei existiert
    if not os.path.isfile(components_file):
        logging.warn(f"Warnung: Komponentendatei nicht gefunden: {components_file}")
        return False

    # Komponentendatei initialisieren
    with open(output_file, "w") as f:
        json.dump([], f)

    # YAML-Datei laden
    try:
        with open(components_file) as f:
            components_data = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Fehler beim Laden der YAML-Datei {components_file}: {str(e)}")
        return False

    # Komponenten extrahieren
    components = components_data.get("components", [])

    # Ausgabedaten initialisieren
    output_data = []

    for component in components:
        component_type = component.get("type")
        name = component.get("name")
        purpose = component.get("purpose")

        # Überspringen, wenn erforderliche Felder fehlen
        if not component_type or not name or not purpose:
            continue

        logging.info(f"Komponente gefunden: {name} (Typ: {component_type})")

        # Komponentenentität erstellen
        component_entity = {
            "@id": f"llm:{name}",
            "@type": f"llm:{component_type.capitalize()}",
            "name": name,
            "description": purpose,
        }

        # Komponente zur Ausgabedatei hinzufügen
        output_data.append(component_entity)

        logging.info(f"Komponente hinzugefügt: {name}")

    # Aktualisierte Daten in die Ausgabedatei schreiben
    try:
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)
    except Exception as e:
        logging.error(f"Fehler beim Schreiben der Komponentendatei: {str(e)}")
        return False

    logging.success(f"Komponenten aus {components_file} extrahiert")
    return True


def extract_services(relationships_file: str, output_file: str) -> bool:
    """
    Extrahiert Dienste aus der YAML-Dokumentation.

    Args:
        relationships_file: Pfad zur Beziehungsdatei
        output_file: Pfad zur Ausgabedatei

    Returns:
        bool: True bei Erfolg, sonst False
    """
    logging.info(f"Extrahiere Dienste aus {relationships_file}")

    # Prüfen, ob die Beziehungsdatei existiert
    if not os.path.isfile(relationships_file):
        logging.warn(f"Warnung: Beziehungsdatei nicht gefunden: {relationships_file}")
        return False

    # Dienstdatei initialisieren
    with open(output_file, "w") as f:
        json.dump([], f)

    # YAML-Datei laden
    try:
        with open(relationships_file) as f:
            relationships_data = yaml.safe_load(f)
    except Exception as e:
        logging.error(
            f"Fehler beim Laden der YAML-Datei {relationships_file}: {str(e)}"
        )
        return False

    # Dienste extrahieren
    relationships = relationships_data.get("relationships", [])

    # Ausgabedaten initialisieren
    output_data = []

    for relationship in relationships:
        relationship_type = relationship.get("type")

        # Nur Beziehungen vom Typ "provides_service_to" berücksichtigen
        if relationship_type != "provides_service_to":
            continue

        source = relationship.get("source")
        target = relationship.get("target")
        description = relationship.get("description")
        interface = relationship.get("interface")

        # Überspringen, wenn erforderliche Felder fehlen
        if not source or not target or not description or not interface:
            continue

        logging.info(f"Dienst gefunden: {source} stellt Dienst für {target} bereit")

        # Dienstentität erstellen
        service_entity = {
            "@id": f"llm:service_{source}_{target}",
            "@type": "llm:Service",
            "name": f"{source}_{target}_service",
            "description": description,
            "provider": f"llm:{source}",
            "consumer": f"llm:{target}",
            "interface": interface,
        }

        # Dienst zur Ausgabedatei hinzufügen
        output_data.append(service_entity)

        logging.info(f"Dienst hinzugefügt: {source}_{target}_service")

    # Aktualisierte Daten in die Ausgabedatei schreiben
    try:
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)
    except Exception as e:
        logging.error(f"Fehler beim Schreiben der Dienstdatei: {str(e)}")
        return False

    logging.success(f"Dienste aus {relationships_file} extrahiert")
    return True


def extract_all_entities(root_dir: Optional[str] = None) -> int:
    """
    Extrahiert alle Entitäten.

    Args:
        root_dir: Wurzelverzeichnis (optional)

    Returns:
        int: Exit-Code (0 bei Erfolg, 1 bei Fehler)
    """
    logging.info("Starte Entitätsextraktion...")

    # Abhängigkeiten prüfen
    if not check_dependencies():
        return 1

    # Projektverzeichnis ermitteln
    if root_dir is None:
        root_dir = system.get_project_root()

    # Ausgabeverzeichnisse
    entities_dir = os.path.join(root_dir, "docs", "knowledge-graph", "entities")

    # Entitäten-Verzeichnis erstellen
    if not create_entities_directory(entities_dir):
        return 1

    # Komponenten aus YAML-Dokumentation extrahieren
    components_file = os.path.join(root_dir, "docs", "system", "components.yaml")
    components_output = os.path.join(entities_dir, "components.json")
    extract_components(components_file, components_output)

    # Dienste aus YAML-Dokumentation extrahieren
    relationships_file = os.path.join(root_dir, "docs", "system", "relationships.yaml")
    services_output = os.path.join(entities_dir, "services.json")
    extract_services(relationships_file, services_output)

    # Entitäten aus Shell-Skripten extrahieren
    shell_scripts = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".sh"):
                shell_scripts.append(os.path.join(root, file))

    functions_output = os.path.join(entities_dir, "functions.json")
    variables_output = os.path.join(entities_dir, "variables.json")
    config_params_output = os.path.join(entities_dir, "config_params.json")

    for script in shell_scripts:
        # Funktionen extrahieren
        extract_functions(script, functions_output)

        # Variablen extrahieren
        extract_variables(script, variables_output)

        # Konfigurationsparameter extrahieren
        extract_config_params(script, config_params_output)

    logging.success("Entitätsextraktion erfolgreich abgeschlossen!")
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
        description="Extrahiert Entitäten aus Shell-Skripten"
    )
    parser.add_argument("--root-dir", help="Wurzelverzeichnis")
    args = parser.parse_args()

    return extract_all_entities(args.root_dir)


if __name__ == "__main__":
    sys.exit(main())
