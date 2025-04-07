"""
Extrahiert Dokumentation aus Code und aktualisiert YAML-Dateien.

Dieses Skript extrahiert Informationen aus Shell-Skripten, Docker Compose-Dateien und anderen
Quelldateien, um die maschinenlesbare Dokumentation zu aktualisieren.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

from llm_stack.core import error, logging, system
from llm_stack.tools.doc_sync import validate_docs


def backup_file(file_path: str) -> Optional[str]:
    """
    Erstellt ein Backup einer Datei.

    Args:
        file_path: Pfad zur Datei

    Returns:
        Optional[str]: Pfad zur Backup-Datei oder None, wenn ein Fehler aufgetreten ist
    """
    if os.path.isfile(file_path):
        backup_path = f"{file_path}.bak"
        try:
            shutil.copy2(file_path, backup_path)
            logging.info(f"Backup erstellt: {backup_path}")
            return backup_path
        except Exception as e:
            logging.error(f"Fehler beim Erstellen des Backups: {str(e)}")
            return None
    return None


def extract_shell_functions(file_path: str, output_file: str) -> None:
    """
    Extrahiert Shell-Funktionen aus einer Datei.

    Args:
        file_path: Pfad zur Shell-Datei
        output_file: Pfad zur Ausgabedatei
    """
    file_name = os.path.basename(file_path)
    logging.info(f"Extrahiere Funktionen aus {file_name}")

    # Prüfen, ob der shell_functions-Abschnitt bereits in der Datei existiert
    try:
        with open(output_file) as f:
            content = f.read()
            if "shell_functions:" not in content:
                with open(output_file, "a") as f:
                    f.write("# Shell Functions\n")
                    f.write("shell_functions:\n")
    except Exception as e:
        logging.error(f"Fehler beim Lesen/Schreiben der Ausgabedatei: {str(e)}")
        return

    # Dateiinhalt lesen
    try:
        with open(file_path) as f:
            lines = f.readlines()
    except Exception as e:
        logging.error(f"Fehler beim Lesen der Datei {file_path}: {str(e)}")
        return

    # Projektverzeichnis ermitteln
    project_root = system.get_project_root()

    # Dateieintrag hinzufügen
    with open(output_file, "a") as out_f:
        out_f.write(f'  - file: "{os.path.relpath(file_path, project_root)}"\n')
        out_f.write("    functions:\n")

        # Funktionsdefinitionen extrahieren
        function_pattern = re.compile(
            r"^[\s]*function[\s]+([a-zA-Z0-9_]+)[\s]*\(\)[\s]*\{"
        )

        for line_num, line in enumerate(lines, 1):
            match = function_pattern.match(line)
            if match:
                func_name = match.group(1)

                # Funktionsbeschreibung aus Kommentaren darüber extrahieren
                description = ""
                start_line = (
                    line_num - 2
                )  # -1 für 0-basierter Index, -1 für vorherige Zeile

                while start_line >= 0:
                    prev_line = lines[start_line]
                    comment_match = re.match(r"^[\s]*#[\s]*(.*)", prev_line)
                    if comment_match:
                        if not description:
                            description = comment_match.group(1)
                        else:
                            description = f"{comment_match.group(1)} {description}"
                        start_line -= 1
                    else:
                        break

                # Wenn keine Beschreibung gefunden wurde, eine generische verwenden
                if not description:
                    description = f"Function {func_name} in {os.path.relpath(file_path, project_root)}"

                # Funktionsinformationen in die Ausgabedatei schreiben
                out_f.write(f'      - name: "{func_name}"\n')
                out_f.write(f'        description: "{description}"\n')

                # Parameter extrahieren, indem nach local var=$1 usw. gesucht wird
                out_f.write("        parameters:\n")

                # In den nächsten 20 Zeilen nach Parametern suchen
                end_line = min(line_num + 20, len(lines))
                for i in range(line_num, end_line):
                    param_match = re.search(
                        r"local[\s]+([a-zA-Z0-9_]+)=[\s]*\$([0-9]+)", lines[i]
                    )
                    if param_match:
                        param_name = param_match.group(1)
                        param_pos = param_match.group(2)

                        out_f.write(f'          - name: "{param_name}"\n')
                        out_f.write(f'            type: "string"\n')
                        out_f.write(f"            required: true\n")
                        out_f.write(
                            f'            description: "Parameter {param_name} (position {param_pos})"\n'
                        )

                # Nach return-Anweisung suchen, um Rückgabewert zu dokumentieren
                returns = ""
                for i in range(line_num, end_line):
                    return_match = re.search(r"return[\s]+([a-zA-Z0-9_]+)", lines[i])
                    if return_match:
                        return_val = return_match.group(1)
                        if re.match(r"^[0-9]+$", return_val):
                            returns = f"Error code {return_val}"
                        elif "ERR_" in return_val:
                            returns = f"Error code ({return_val})"
                        else:
                            returns = return_val
                        break

                if returns:
                    out_f.write(f'        returns: "{returns}"\n')
                else:
                    out_f.write('        returns: "No explicit return value"\n')


def extract_cli_commands(file_path: str, output_file: str) -> None:
    """
    Extrahiert CLI-Befehle aus dem Hauptskript.

    Args:
        file_path: Pfad zum Hauptskript
        output_file: Pfad zur Ausgabedatei
    """
    logging.info(f"Extrahiere CLI-Befehle aus {os.path.basename(file_path)}")

    # Prüfen, ob der cli_interfaces-Abschnitt bereits in der Datei existiert
    try:
        with open(output_file) as f:
            content = f.read()
            if "cli_interfaces:" not in content:
                with open(output_file, "a") as f:
                    f.write("# CLI Interfaces\n")
                    f.write("cli_interfaces:\n")
    except Exception as e:
        logging.error(f"Fehler beim Lesen/Schreiben der Ausgabedatei: {str(e)}")
        return

    # Dateiinhalt lesen
    try:
        with open(file_path) as f:
            content = f.read()
    except Exception as e:
        logging.error(f"Fehler beim Lesen der Datei {file_path}: {str(e)}")
        return

    # Komponenten-Eintrag hinzufügen
    with open(output_file, "a") as out_f:
        out_f.write('  - component: "llm_script"\n')
        out_f.write("    commands:\n")

        # Befehle aus der case-Anweisung in der Hauptfunktion extrahieren
        case_pattern = re.compile(r'case\s+"?\$command"?\s+in(.*?)esac', re.DOTALL)
        case_match = case_pattern.search(content)

        if case_match:
            case_content = case_match.group(1)
            command_pattern = re.compile(r"^\s*([a-zA-Z0-9_-]+)\)", re.MULTILINE)

            for cmd_match in command_pattern.finditer(case_content):
                cmd_name = cmd_match.group(1)
                cmd_function = f"{cmd_name}_command"

                # Befehlsinformationen in die Ausgabedatei schreiben
                out_f.write(f'      - name: "{cmd_name}"\n')
                out_f.write(f'        description: "{cmd_name.capitalize()} command"\n')
                out_f.write(f'        function: "{cmd_function}"\n')
                out_f.write("        parameters: []\n")


def extract_docker_components(file_path: str, output_file: str) -> None:
    """
    Extrahiert Komponenten aus der Docker Compose-Datei.

    Args:
        file_path: Pfad zur Docker Compose-Datei
        output_file: Pfad zur Ausgabedatei
    """
    logging.info(f"Extrahiere Komponenten aus {os.path.basename(file_path)}")

    # Prüfen, ob der components-Abschnitt bereits in der Datei existiert
    try:
        with open(output_file) as f:
            content = f.read()
            if "components:" not in content:
                with open(output_file, "a") as f:
                    f.write("# LOCAL-LLM-Stack Components Documentation\n")
                    f.write(
                        "# This file documents all system components in a machine-readable format\n"
                    )
                    f.write("\n")
                    f.write("components:\n")
    except Exception as e:
        logging.error(f"Fehler beim Lesen/Schreiben der Ausgabedatei: {str(e)}")
        return

    # Docker Compose-Datei als YAML laden
    try:
        with open(file_path) as f:
            compose_data = yaml.safe_load(f)
    except Exception as e:
        logging.error(
            f"Fehler beim Laden der Docker Compose-Datei {file_path}: {str(e)}"
        )
        return

    # Dienste extrahieren
    services = compose_data.get("services", {})

    with open(output_file, "a") as out_f:
        for service_name, service_config in services.items():
            # Dienst überspringen, wenn es kein echter Dienst ist
            if service_name == "services":
                continue

            out_f.write('  - type: "container"\n')
            out_f.write(f'    name: "{service_name}"\n')

            # Image extrahieren
            image = service_config.get("image")
            if image:
                # Basis-Image und Versionsvariable extrahieren
                image_pattern = re.compile(r"(.+):\$\{([A-Z_]+):-([^}]+)\}")
                match = image_pattern.match(str(image))

                if match:
                    base_image = match.group(1)
                    version_var = match.group(2)
                    default_version = match.group(3)
                    out_f.write(f'    image: "{base_image}"\n')
                    out_f.write(f'    version_var: "{version_var}"\n')
                    out_f.write(f'    default_version: "{default_version}"\n')
                else:
                    out_f.write(f'    image: "{image}"\n')

            # Zweck basierend auf dem Dienstnamen bestimmen
            if service_name == "ollama":
                out_f.write(
                    '    purpose: "Provides local LLM inference capabilities"\n'
                )
            elif service_name == "librechat":
                out_f.write(
                    '    purpose: "Provides web interface for interacting with LLMs"\n'
                )
            elif service_name == "mongodb":
                out_f.write('    purpose: "Provides database storage for LibreChat"\n')
            elif service_name == "meilisearch":
                out_f.write(
                    '    purpose: "Provides search capabilities for LibreChat"\n'
                )
            else:
                out_f.write(f'    purpose: "{service_name} service"\n')

            # Ports extrahieren
            ports = service_config.get("ports", [])
            if ports:
                out_f.write("    ports:\n")
                for port in ports:
                    port_str = str(port)
                    port_pattern = re.compile(r'"?\$\{([A-Z_]+):-([0-9]+)\}:([0-9]+)"?')
                    match = port_pattern.match(port_str)

                    if match:
                        var_name = match.group(1)
                        default_external = match.group(2)
                        internal = match.group(3)

                        out_f.write(f"      - internal: {internal}\n")
                        out_f.write(f'        external_var: "{var_name}"\n')
                        out_f.write(f"        default_external: {default_external}\n")
                        out_f.write('        protocol: "tcp"\n')
                        out_f.write('        purpose: "Service port"\n')

            # Volumes extrahieren
            volumes = service_config.get("volumes", [])
            if volumes:
                out_f.write("    volumes:\n")
                for volume in volumes:
                    volume_str = str(volume)
                    volume_parts = volume_str.split(":")

                    if len(volume_parts) >= 2:
                        host_path = volume_parts[0]
                        container_path = volume_parts[1]

                        out_f.write(f'      - host_path: "{host_path}"\n')
                        out_f.write(f'        container_path: "{container_path}"\n')

                        # Zweck basierend auf dem Pfad bestimmen
                        if "/data" in container_path:
                            out_f.write('        purpose: "data_storage"\n')
                        elif (
                            "/config" in container_path
                            or ".yaml" in container_path
                            or ".yml" in container_path
                        ):
                            out_f.write('        purpose: "configuration"\n')
                        elif ".env" in container_path:
                            out_f.write('        purpose: "environment_variables"\n')
                        elif (
                            "/models" in container_path or "/.ollama" in container_path
                        ):
                            out_f.write('        purpose: "model_storage"\n')
                        else:
                            out_f.write('        purpose: "storage"\n')

            # Umgebungsvariablen extrahieren
            environment = service_config.get("environment", [])
            if environment:
                out_f.write("    environment_variables:\n")
                for env_var in environment:
                    env_str = str(env_var)
                    env_parts = env_str.split("=", 1)

                    if len(env_parts) == 2:
                        name = env_parts[0]
                        value = env_parts[1]

                        out_f.write(f'      - name: "{name}"\n')
                        out_f.write(f'        value: "{value}"\n')

                        # Zweck basierend auf dem Namen bestimmen
                        if "HOST" in name:
                            out_f.write('        purpose: "Host configuration"\n')
                        elif "PORT" in name:
                            out_f.write('        purpose: "Port configuration"\n')
                        elif "URI" in name or "URL" in name:
                            out_f.write('        purpose: "Connection URL"\n')
                        elif "SECRET" in name or "KEY" in name or "PASSWORD" in name:
                            out_f.write('        purpose: "Security credential"\n')
                        elif "ENABLE" in name or "ALLOW" in name:
                            out_f.write('        purpose: "Feature flag"\n')
                        else:
                            out_f.write('        purpose: "Configuration"\n')

            # Ressourcenbeschränkungen extrahieren
            resources = service_config.get("resources", {})
            limits = resources.get("limits", {})

            if limits:
                out_f.write("    resource_limits:\n")

                # CPU-Limit extrahieren
                cpu = limits.get("cpus")
                if cpu:
                    cpu_str = str(cpu)
                    cpu_pattern = re.compile(r'"?\$\{([A-Z_]+):-([0-9.]+)\}"?')
                    match = cpu_pattern.match(cpu_str)

                    if match:
                        var_name = match.group(1)
                        default_value = match.group(2)

                        out_f.write(f'      cpu_var: "{var_name}"\n')
                        out_f.write(f"      cpu_default: {default_value}\n")

                # Speicher-Limit extrahieren
                memory = limits.get("memory")
                if memory:
                    memory_str = str(memory)
                    memory_pattern = re.compile(r"\$\{([A-Z_]+):-([0-9A-Za-z]+)\}")
                    match = memory_pattern.match(memory_str)

                    if match:
                        var_name = match.group(1)
                        default_value = match.group(2)

                        out_f.write(f'      memory_var: "{var_name}"\n')
                        out_f.write(f'      memory_default: "{default_value}"\n')

            # Healthcheck extrahieren
            healthcheck = service_config.get("healthcheck")
            if healthcheck:
                out_f.write("    health_check:\n")

                # Test-Befehl extrahieren
                test = healthcheck.get("test")
                if test and isinstance(test, list) and len(test) > 1:
                    out_f.write(f"      command: {test[1]}\n")

                # Intervall extrahieren
                interval = healthcheck.get("interval")
                if interval:
                    out_f.write(f'      interval: "{interval}"\n')

                # Timeout extrahieren
                timeout = healthcheck.get("timeout")
                if timeout:
                    out_f.write(f'      timeout: "{timeout}"\n')

                # Wiederholungen extrahieren
                retries = healthcheck.get("retries")
                if retries:
                    out_f.write(f"      retries: {retries}\n")

                # Startperiode extrahieren
                start_period = healthcheck.get("start_period")
                if start_period:
                    out_f.write(f'      start_period: "{start_period}"\n')


def extract_relationships(file_path: str, output_file: str) -> None:
    """
    Extrahiert Beziehungen aus der Docker Compose-Datei.

    Args:
        file_path: Pfad zur Docker Compose-Datei
        output_file: Pfad zur Ausgabedatei
    """
    logging.info(f"Extrahiere Beziehungen aus {os.path.basename(file_path)}")

    # Prüfen, ob der relationships-Abschnitt bereits in der Datei existiert
    try:
        with open(output_file) as f:
            content = f.read()
            if "relationships:" not in content:
                with open(output_file, "a") as f:
                    f.write("# LOCAL-LLM-Stack Relationships Documentation\n")
                    f.write(
                        "# This file documents all system relationships in a machine-readable format\n"
                    )
                    f.write("\n")
                    f.write("relationships:\n")
    except Exception as e:
        logging.error(f"Fehler beim Lesen/Schreiben der Ausgabedatei: {str(e)}")
        return

    # Docker Compose-Datei als YAML laden
    try:
        with open(file_path) as f:
            compose_data = yaml.safe_load(f)
    except Exception as e:
        logging.error(
            f"Fehler beim Laden der Docker Compose-Datei {file_path}: {str(e)}"
        )
        return

    # Dienste extrahieren
    services = compose_data.get("services", {})

    with open(output_file, "a") as out_f:
        # Abhängigkeiten aus der Docker Compose-Datei extrahieren
        for service_name, service_config in services.items():
            depends_on = service_config.get("depends_on", {})

            if depends_on:
                for target_service, condition in depends_on.items():
                    # Abhängigkeitsbeziehung schreiben
                    out_f.write(f'  - source: "{service_name}"\n')
                    out_f.write(f'    target: "{target_service}"\n')
                    out_f.write(f'    type: "depends_on"\n')
                    out_f.write(
                        f'    description: "{service_name} requires {target_service}"\n'
                    )

                    # Schnittstelle basierend auf Diensten bestimmen
                    if target_service == "mongodb":
                        out_f.write(f'    interface: "mongodb_driver"\n')
                    elif target_service in ["ollama", "meilisearch"]:
                        out_f.write(f'    interface: "http_api"\n')
                    else:
                        out_f.write(f'    interface: "service"\n')

                    out_f.write(f"    required: true\n")

                    # Bedingung prüfen
                    if isinstance(condition, dict) and "condition" in condition:
                        condition_value = condition["condition"]

                        # Startup-Abhängigkeit schreiben
                        out_f.write(f'  - source: "{service_name}"\n')
                        out_f.write(f'    target: "{target_service}"\n')
                        out_f.write(f'    type: "startup_dependency"\n')
                        out_f.write(
                            f'    description: "{service_name} must start after {target_service} is {condition_value}"\n'
                        )
                        out_f.write(f'    condition: "{condition_value}"\n')

                    # Umgekehrte Beziehung schreiben (provides service)
                    out_f.write(f'  - source: "{target_service}"\n')
                    out_f.write(f'    target: "{service_name}"\n')
                    out_f.write(f'    type: "provides_service_to"\n')
                    out_f.write(
                        f'    description: "{target_service} provides service to {service_name}"\n'
                    )

                    # Schnittstelle basierend auf Diensten bestimmen
                    if target_service == "mongodb":
                        out_f.write(f'    interface: "mongodb_driver"\n')
                    elif target_service in ["ollama", "meilisearch"]:
                        out_f.write(f'    interface: "http_api"\n')
                    else:
                        out_f.write(f'    interface: "service"\n')

                    out_f.write(f"    required: false\n")

        # Netzwerkbeziehungen extrahieren
        for service_name, service_config in services.items():
            networks = service_config.get("networks", [])

            if networks:
                for network in networks:
                    # Netzwerkbeziehung schreiben
                    out_f.write(f'  - source: "{service_name}"\n')
                    out_f.write(f'    target: "{network}"\n')
                    out_f.write(f'    type: "depends_on"\n')
                    out_f.write(
                        f'    description: "{service_name} requires the {network} for communication"\n'
                    )
                    out_f.write(f"    required: true\n")


def main() -> int:
    """
    Hauptfunktion für die direkte Ausführung des Skripts.

    Returns:
        int: Exit-Code (0 bei Erfolg, 1 bei Fehler)
    """
    logging.info("Starte Dokumentationsextraktion...")

    # Projektverzeichnis ermitteln
    project_root = system.get_project_root()

    # Quellpfade
    core_dir = os.path.join(project_root, "lib", "core")
    docker_compose_file = os.path.join(project_root, "core", "docker-compose.yml")
    main_script = os.path.join(project_root, "llm")

    # Ausgabepfade
    components_file = os.path.join(project_root, "docs", "system", "components.yaml")
    interfaces_file = os.path.join(project_root, "docs", "system", "interfaces.yaml")
    relationships_file = os.path.join(
        project_root, "docs", "system", "relationships.yaml"
    )

    # Temporäre Dateien
    components_tmp = f"{components_file}.tmp"
    interfaces_tmp = f"{interfaces_file}.tmp"
    relationships_tmp = f"{relationships_file}.tmp"

    # Backup von vorhandenen Dateien erstellen
    backup_file(components_file)
    backup_file(interfaces_file)
    backup_file(relationships_file)

    # Temporäre Dateien initialisieren
    with open(interfaces_tmp, "w") as f:
        f.write("# API Interfaces\n")
        f.write("api_interfaces:\n")

    # Informationen aus Quelldateien extrahieren
    extract_docker_components(docker_compose_file, components_tmp)
    extract_relationships(docker_compose_file, relationships_tmp)
    extract_cli_commands(main_script, interfaces_tmp)

    # Shell-Funktionen aus Core-Bibliotheksdateien extrahieren
    for file_path in Path(core_dir).glob("*.sh"):
        extract_shell_functions(str(file_path), interfaces_tmp)

    # Die extrahierte Dokumentation validieren
    validation_script_path = os.path.join(os.path.dirname(__file__), "validate_docs.py")

    # Validierung durchführen
    if validate_docs.main() == 0:
        # Die alten Dateien durch die neuen ersetzen
        shutil.move(components_tmp, components_file)
        shutil.move(interfaces_tmp, interfaces_file)
        shutil.move(relationships_tmp, relationships_file)
        logging.success("Dokumentation erfolgreich aktualisiert")
        return 0
    else:
        logging.error("Dokumentationsvalidierung fehlgeschlagen")
        logging.error(
            f"Temporäre Dateien nicht angewendet. Prüfen Sie {components_tmp}, {interfaces_tmp} und {relationships_tmp}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
