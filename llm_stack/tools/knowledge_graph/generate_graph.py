"""
Generiert einen Knowledge Graph aus extrahierten Entitäten und Beziehungen.

Dieses Skript generiert einen JSON-LD Knowledge Graph aus den extrahierten Entitäten und Beziehungen.
"""

import json
import os
import subprocess
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
    # Prüfen, ob Graphviz installiert ist
    graphviz_installed = False
    try:
        subprocess.run(["dot", "-V"], capture_output=True, check=False)
        graphviz_installed = True
    except FileNotFoundError:
        logging.warn(
            "Warnung: Graphviz (dot) ist nicht installiert. Visualisierungen werden nicht generiert."
        )
        logging.info("Sie können es mit 'sudo apt-get install graphviz' installieren.")

    return True


def create_output_directories(graph_dir: str, visualizations_dir: str) -> bool:
    """
    Erstellt die Ausgabeverzeichnisse, falls sie nicht existieren.

    Args:
        graph_dir: Pfad zum Graph-Verzeichnis
        visualizations_dir: Pfad zum Visualisierungsverzeichnis

    Returns:
        bool: True, wenn die Verzeichnisse erstellt wurden oder bereits existieren, sonst False
    """
    if not os.path.isdir(graph_dir):
        try:
            os.makedirs(graph_dir)
            logging.info(f"Knowledge Graph-Verzeichnis erstellt: {graph_dir}")
        except Exception as e:
            logging.error(
                f"Fehler beim Erstellen des Knowledge Graph-Verzeichnisses: {str(e)}"
            )
            return False

    if not os.path.isdir(visualizations_dir):
        try:
            os.makedirs(visualizations_dir)
            logging.info(f"Visualisierungsverzeichnis erstellt: {visualizations_dir}")
        except Exception as e:
            logging.error(
                f"Fehler beim Erstellen des Visualisierungsverzeichnisses: {str(e)}"
            )
            return False

    return True


def generate_graph(
    graph_file: str, entities_dir: str, relationships_dir: str, root_dir: str
) -> bool:
    """
    Generiert den Knowledge Graph.

    Args:
        graph_file: Pfad zur Graph-Datei
        entities_dir: Pfad zum Entitäten-Verzeichnis
        relationships_dir: Pfad zum Beziehungen-Verzeichnis
        root_dir: Pfad zum Wurzelverzeichnis

    Returns:
        bool: True bei Erfolg, sonst False
    """
    logging.info("Generiere Knowledge Graph...")

    # Basis-Graph-Struktur erstellen
    graph_data = {
        "@context": {
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "llm": "http://local-llm-stack.org/ontology#",
            "name": "rdfs:label",
            "description": "rdfs:comment",
            "type": "rdf:type",
            "component": "llm:Component",
            "container": "llm:Container",
            "script": "llm:Script",
            "library": "llm:Library",
            "module": "llm:Module",
            "relationship": "llm:Relationship",
            "interface": "llm:Interface",
            "api": "llm:API",
            "cli": "llm:CLI",
            "function": "llm:Function",
            "variable": "llm:Variable",
            "parameter": "llm:Parameter",
            "configParam": "llm:ConfigParam",
            "service": "llm:Service",
            "dataFlow": "llm:DataFlow",
            "source": "llm:source",
            "target": "llm:target",
            "dependsOn": "llm:dependsOn",
            "calls": "llm:calls",
            "imports": "llm:imports",
            "configures": "llm:configures",
            "defines": "llm:defines",
            "uses": "llm:uses",
            "providesServiceTo": "llm:providesServiceTo",
            "startupDependency": "llm:startupDependency",
            "runtimeDependency": "llm:runtimeDependency",
            "configurationDependency": "llm:configurationDependency",
            "exposes": "llm:exposes",
            "implements": "llm:implements",
            "hasFunction": "llm:hasFunction",
            "hasParameter": "llm:hasParameter",
            "hasStep": "llm:hasStep",
            "hasEndpoint": "llm:hasEndpoint",
            "hasCommand": "llm:hasCommand",
            "filePath": "llm:filePath",
            "lineNumber": "llm:lineNumber",
            "signature": "llm:signature",
            "returnType": "llm:returnType",
            "parameterType": "llm:parameterType",
            "defaultValue": "llm:defaultValue",
            "required": "llm:required",
        },
        "@graph": [],
    }

    # Graph-Datei schreiben
    with open(graph_file, "w") as f:
        json.dump(graph_data, f, indent=2)

    # Entitäten zum Graph hinzufügen
    logging.info("Füge Entitäten zum Graph hinzu...")

    # Komponenten hinzufügen
    components_file = os.path.join(entities_dir, "components.json")
    if os.path.isfile(components_file):
        logging.info("Füge Komponenten hinzu...")
        try:
            with open(components_file) as f:
                components_data = json.load(f)

            for component in components_data:
                # Komponente zum Graph hinzufügen
                graph_data["@graph"].append(component)

                component_name = component.get("name", "")
                logging.info(f"Komponente hinzugefügt: {component_name}")
        except Exception as e:
            logging.error(f"Fehler beim Hinzufügen von Komponenten: {str(e)}")

    # Funktionen hinzufügen
    functions_file = os.path.join(entities_dir, "functions.json")
    if os.path.isfile(functions_file):
        logging.info("Füge Funktionen hinzu...")
        try:
            with open(functions_file) as f:
                functions_data = json.load(f)

            for function in functions_data:
                # Funktion zum Graph hinzufügen
                graph_data["@graph"].append(function)

                function_name = function.get("name", "")
                logging.info(f"Funktion hinzugefügt: {function_name}")
        except Exception as e:
            logging.error(f"Fehler beim Hinzufügen von Funktionen: {str(e)}")

    # Variablen hinzufügen
    variables_file = os.path.join(entities_dir, "variables.json")
    if os.path.isfile(variables_file):
        logging.info("Füge Variablen hinzu...")
        try:
            with open(variables_file) as f:
                variables_data = json.load(f)

            for variable in variables_data:
                # Variable zum Graph hinzufügen
                graph_data["@graph"].append(variable)

                variable_name = variable.get("name", "")
                logging.info(f"Variable hinzugefügt: {variable_name}")
        except Exception as e:
            logging.error(f"Fehler beim Hinzufügen von Variablen: {str(e)}")

    # Konfigurationsparameter hinzufügen
    config_params_file = os.path.join(entities_dir, "config_params.json")
    if os.path.isfile(config_params_file):
        logging.info("Füge Konfigurationsparameter hinzu...")
        try:
            with open(config_params_file) as f:
                config_params_data = json.load(f)

            for config_param in config_params_data:
                # Konfigurationsparameter zum Graph hinzufügen
                graph_data["@graph"].append(config_param)

                param_name = config_param.get("name", "")
                logging.info(f"Konfigurationsparameter hinzugefügt: {param_name}")
        except Exception as e:
            logging.error(
                f"Fehler beim Hinzufügen von Konfigurationsparametern: {str(e)}"
            )

    # Dienste hinzufügen
    services_file = os.path.join(entities_dir, "services.json")
    if os.path.isfile(services_file):
        logging.info("Füge Dienste hinzu...")
        try:
            with open(services_file) as f:
                services_data = json.load(f)

            for service in services_data:
                # Dienst zum Graph hinzufügen
                graph_data["@graph"].append(service)

                service_name = service.get("name", "")
                logging.info(f"Dienst hinzugefügt: {service_name}")
        except Exception as e:
            logging.error(f"Fehler beim Hinzufügen von Diensten: {str(e)}")

    # Beziehungen zum Graph hinzufügen
    logging.info("Füge Beziehungen zum Graph hinzu...")

    # Funktionsaufrufe hinzufügen
    function_calls_file = os.path.join(relationships_dir, "function_calls.json")
    if os.path.isfile(function_calls_file):
        logging.info("Füge Funktionsaufrufe hinzu...")
        try:
            with open(function_calls_file) as f:
                function_calls_data = json.load(f)

            for function_call in function_calls_data:
                # Funktionsaufruf zum Graph hinzufügen
                graph_data["@graph"].append(function_call)

                call_name = function_call.get("name", "")
                logging.info(f"Funktionsaufruf hinzugefügt: {call_name}")
        except Exception as e:
            logging.error(f"Fehler beim Hinzufügen von Funktionsaufrufen: {str(e)}")

    # Komponentenabhängigkeiten hinzufügen
    component_dependencies_file = os.path.join(
        relationships_dir, "component_dependencies.json"
    )
    if os.path.isfile(component_dependencies_file):
        logging.info("Füge Komponentenabhängigkeiten hinzu...")
        try:
            with open(component_dependencies_file) as f:
                component_dependencies_data = json.load(f)

            for component_dependency in component_dependencies_data:
                # Komponentenabhängigkeit zum Graph hinzufügen
                graph_data["@graph"].append(component_dependency)

                dependency_name = component_dependency.get("name", "")
                logging.info(f"Komponentenabhängigkeit hinzugefügt: {dependency_name}")
        except Exception as e:
            logging.error(
                f"Fehler beim Hinzufügen von Komponentenabhängigkeiten: {str(e)}"
            )

    # Konfigurationsabhängigkeiten hinzufügen
    config_dependencies_file = os.path.join(
        relationships_dir, "config_dependencies.json"
    )
    if os.path.isfile(config_dependencies_file):
        logging.info("Füge Konfigurationsabhängigkeiten hinzu...")
        try:
            with open(config_dependencies_file) as f:
                config_dependencies_data = json.load(f)

            for config_dependency in config_dependencies_data:
                # Konfigurationsabhängigkeit zum Graph hinzufügen
                graph_data["@graph"].append(config_dependency)

                dependency_name = config_dependency.get("name", "")
                logging.info(
                    f"Konfigurationsabhängigkeit hinzugefügt: {dependency_name}"
                )
        except Exception as e:
            logging.error(
                f"Fehler beim Hinzufügen von Konfigurationsabhängigkeiten: {str(e)}"
            )

    # Importe hinzufügen
    imports_file = os.path.join(relationships_dir, "imports.json")
    if os.path.isfile(imports_file):
        logging.info("Füge Importe hinzu...")
        try:
            with open(imports_file) as f:
                imports_data = json.load(f)

            for import_item in imports_data:
                # Import zum Graph hinzufügen
                graph_data["@graph"].append(import_item)

                import_name = import_item.get("name", "")
                logging.info(f"Import hinzugefügt: {import_name}")
        except Exception as e:
            logging.error(f"Fehler beim Hinzufügen von Importen: {str(e)}")

    # Datenflüsse hinzufügen
    data_flows_file = os.path.join(relationships_dir, "data_flows.json")
    if os.path.isfile(data_flows_file):
        logging.info("Füge Datenflüsse hinzu...")
        try:
            with open(data_flows_file) as f:
                data_flows_data = json.load(f)

            for data_flow in data_flows_data:
                # Datenfluss zum Graph hinzufügen
                graph_data["@graph"].append(data_flow)

                flow_name = data_flow.get("name", "")
                logging.info(f"Datenfluss hinzugefügt: {flow_name}")
        except Exception as e:
            logging.error(f"Fehler beim Hinzufügen von Datenflüssen: {str(e)}")

    # Schnittstellen aus YAML-Dokumentation hinzufügen
    logging.info("Füge Schnittstellen aus YAML-Dokumentation hinzu...")
    interfaces_file = os.path.join(root_dir, "docs", "system", "interfaces.yaml")

    if os.path.isfile(interfaces_file):
        try:
            with open(interfaces_file) as f:
                interfaces_data = yaml.safe_load(f)

            # API-Schnittstellen hinzufügen
            api_interfaces = interfaces_data.get("api_interfaces", [])
            if api_interfaces:
                logging.info("Füge API-Schnittstellen hinzu...")

                for api_interface in api_interfaces:
                    component = api_interface.get("component", "")
                    interface_type = api_interface.get("interface_type", "")
                    base_url = api_interface.get("base_url", "")

                    # API-Schnittstellenknoten erstellen
                    api_node = {
                        "@id": f"llm:{component}_api",
                        "@type": "llm:API",
                        "name": f"{component} API",
                        "description": f"API interface for {component}",
                        "baseUrl": base_url,
                    }

                    # API-Schnittstelle zum Graph hinzufügen
                    graph_data["@graph"].append(api_node)

                    # Beziehung zwischen Komponente und API hinzufügen
                    api_relationship = {
                        "@id": f"llm:{component}",
                        "exposes": {"@id": f"llm:{component}_api"},
                    }

                    # API-Beziehung zum Graph hinzufügen
                    graph_data["@graph"].append(api_relationship)

                    logging.info(f"API-Schnittstelle hinzugefügt für: {component}")

            # CLI-Schnittstellen hinzufügen
            cli_interfaces = interfaces_data.get("cli_interfaces", [])
            if cli_interfaces:
                logging.info("Füge CLI-Schnittstellen hinzu...")

                for cli_interface in cli_interfaces:
                    component = cli_interface.get("component", "")

                    # CLI-Schnittstellenknoten erstellen
                    cli_node = {
                        "@id": f"llm:{component}_cli",
                        "@type": "llm:CLI",
                        "name": f"{component} CLI",
                        "description": f"CLI interface for {component}",
                    }

                    # CLI-Schnittstelle zum Graph hinzufügen
                    graph_data["@graph"].append(cli_node)

                    # Beziehung zwischen Komponente und CLI hinzufügen
                    cli_relationship = {
                        "@id": f"llm:{component}",
                        "exposes": {"@id": f"llm:{component}_cli"},
                    }

                    # CLI-Beziehung zum Graph hinzufügen
                    graph_data["@graph"].append(cli_relationship)

                    logging.info(f"CLI-Schnittstelle hinzugefügt für: {component}")
        except Exception as e:
            logging.error(f"Fehler beim Hinzufügen von Schnittstellen: {str(e)}")

    # Aktualisierte Graph-Daten in die Datei schreiben
    try:
        with open(graph_file, "w") as f:
            json.dump(graph_data, f, indent=2)
    except Exception as e:
        logging.error(f"Fehler beim Schreiben der Graph-Datei: {str(e)}")
        return False

    logging.success(f"Knowledge Graph erfolgreich generiert: {graph_file}")
    return True


def generate_visualizations(
    visualizations_dir: str, entities_dir: str, relationships_dir: str
) -> bool:
    """
    Generiert Visualisierungen des Knowledge Graphs.

    Args:
        visualizations_dir: Pfad zum Visualisierungsverzeichnis
        entities_dir: Pfad zum Entitäten-Verzeichnis
        relationships_dir: Pfad zum Beziehungen-Verzeichnis

    Returns:
        bool: True bei Erfolg, sonst False
    """
    logging.info("Generiere Visualisierungen...")

    # Prüfen, ob Graphviz installiert ist
    try:
        subprocess.run(["dot", "-V"], capture_output=True, check=False)
    except FileNotFoundError:
        logging.warn(
            "Warnung: Graphviz (dot) ist nicht installiert. Visualisierungen werden nicht generiert."
        )
        return False

    # Komponentenabhängigkeitsvisualisierung generieren
    logging.info("Generiere Komponentenabhängigkeitsvisualisierung...")
    component_dot_file = os.path.join(visualizations_dir, "component_dependencies.dot")
    component_svg_file = os.path.join(visualizations_dir, "component_dependencies.svg")

    # DOT-Dateiheader erstellen
    with open(component_dot_file, "w") as f:
        f.write("digraph ComponentDependencies {\n")
        f.write("  rankdir=LR;\n")
        f.write("  node [shape=box, style=filled, fillcolor=lightblue];\n")
        f.write("  edge [color=black, fontcolor=black];\n")
        f.write("  \n")

        # Komponenten und Abhängigkeiten hinzufügen
        components_file = os.path.join(entities_dir, "components.json")
        if os.path.isfile(components_file):
            try:
                with open(components_file) as cf:
                    components_data = json.load(cf)

                # Komponentenknoten hinzufügen
                for component in components_data:
                    component_name = component.get("name", "")
                    f.write(f'  "{component_name}" [label="{component_name}"];\n')

                # Abhängigkeitskanten hinzufügen
                component_dependencies_file = os.path.join(
                    relationships_dir, "component_dependencies.json"
                )
                if os.path.isfile(component_dependencies_file):
                    with open(component_dependencies_file) as df:
                        dependencies_data = json.load(df)

                    for dependency in dependencies_data:
                        source = dependency.get("source", "").replace("llm:", "")
                        target = dependency.get("target", "").replace("llm:", "")
                        f.write(f'  "{source}" -> "{target}" [label="depends on"];\n')
            except Exception as e:
                logging.error(
                    f"Fehler beim Generieren der Komponentenabhängigkeitsvisualisierung: {str(e)}"
                )

        # DOT-Datei schließen
        f.write("}\n")

    # SVG generieren
    try:
        subprocess.run(
            ["dot", "-Tsvg", component_dot_file, "-o", component_svg_file], check=True
        )
    except Exception as e:
        logging.error(f"Fehler beim Generieren der SVG-Datei: {str(e)}")

    # Funktionsaufrufvisualisierung generieren
    logging.info("Generiere Funktionsaufrufvisualisierung...")
    function_dot_file = os.path.join(visualizations_dir, "function_calls.dot")
    function_svg_file = os.path.join(visualizations_dir, "function_calls.svg")

    # DOT-Dateiheader erstellen
    with open(function_dot_file, "w") as f:
        f.write("digraph FunctionCalls {\n")
        f.write("  rankdir=LR;\n")
        f.write("  node [shape=ellipse, style=filled, fillcolor=lightgreen];\n")
        f.write("  edge [color=black, fontcolor=black];\n")
        f.write("  \n")

        # Funktionen und Aufrufe hinzufügen
        functions_file = os.path.join(entities_dir, "functions.json")
        if os.path.isfile(functions_file):
            try:
                with open(functions_file) as ff:
                    functions_data = json.load(ff)

                # Funktionsknoten hinzufügen
                for function in functions_data:
                    function_name = function.get("name", "")
                    f.write(f'  "{function_name}" [label="{function_name}"];\n')

                # Aufrufkanten hinzufügen
                function_calls_file = os.path.join(
                    relationships_dir, "function_calls.json"
                )
                if os.path.isfile(function_calls_file):
                    with open(function_calls_file) as cf:
                        calls_data = json.load(cf)

                    for call in calls_data:
                        source = call.get("source", "").replace("llm:", "")
                        target = call.get("target", "").replace("llm:", "")
                        f.write(f'  "{source}" -> "{target}" [label="calls"];\n')
            except Exception as e:
                logging.error(
                    f"Fehler beim Generieren der Funktionsaufrufvisualisierung: {str(e)}"
                )

        # DOT-Datei schließen
        f.write("}\n")

    # SVG generieren
    try:
        subprocess.run(
            ["dot", "-Tsvg", function_dot_file, "-o", function_svg_file], check=True
        )
    except Exception as e:
        logging.error(f"Fehler beim Generieren der SVG-Datei: {str(e)}")

    # Datenflussvisualisierung generieren
    logging.info("Generiere Datenflussvisualisierung...")
    dataflow_dot_file = os.path.join(visualizations_dir, "data_flows.dot")
    dataflow_svg_file = os.path.join(visualizations_dir, "data_flows.svg")

    # DOT-Dateiheader erstellen
    with open(dataflow_dot_file, "w") as f:
        f.write("digraph DataFlows {\n")
        f.write("  rankdir=LR;\n")
        f.write("  node [shape=box, style=filled, fillcolor=lightyellow];\n")
        f.write("  edge [color=black, fontcolor=black];\n")
        f.write("  \n")

        # Datenflüsse hinzufügen
        data_flows_file = os.path.join(relationships_dir, "data_flows.json")
        if os.path.isfile(data_flows_file):
            try:
                with open(data_flows_file) as df:
                    flows_data = json.load(df)

                # Flusskanten hinzufügen
                for flow in flows_data:
                    source = flow.get("source", "").replace("llm:", "")
                    target = flow.get("target", "").replace("llm:", "")
                    data = flow.get("data", "")
                    f.write(f'  "{source}" -> "{target}" [label="{data}"];\n')
            except Exception as e:
                logging.error(
                    f"Fehler beim Generieren der Datenflussvisualisierung: {str(e)}"
                )

        # DOT-Datei schließen
        f.write("}\n")

    # SVG generieren
    try:
        subprocess.run(
            ["dot", "-Tsvg", dataflow_dot_file, "-o", dataflow_svg_file], check=True
        )
    except Exception as e:
        logging.error(f"Fehler beim Generieren der SVG-Datei: {str(e)}")

    logging.success("Visualisierungen erfolgreich generiert!")
    return True


def main() -> int:
    """
    Hauptfunktion für die direkte Ausführung des Skripts.

    Returns:
        int: Exit-Code (0 bei Erfolg, 1 bei Fehler)
    """
    logging.info("Starte Knowledge Graph-Generierung...")

    # Abhängigkeiten prüfen
    check_dependencies()

    # Projektverzeichnis ermitteln
    root_dir = system.get_project_root()

    # Ein- und Ausgabeverzeichnisse
    entities_dir = os.path.join(root_dir, "docs", "knowledge-graph", "entities")
    relationships_dir = os.path.join(
        root_dir, "docs", "knowledge-graph", "relationships"
    )
    visualizations_dir = os.path.join(
        root_dir, "docs", "knowledge-graph", "visualizations"
    )

    # Ausgabedateien
    graph_file = os.path.join(root_dir, "docs", "knowledge-graph", "graph.json")
    graph_dir = os.path.dirname(graph_file)

    # Ausgabeverzeichnisse erstellen
    if not create_output_directories(graph_dir, visualizations_dir):
        return 1

    # Entitäten extrahieren, falls sie nicht existieren
    if not os.path.isfile(
        os.path.join(entities_dir, "components.json")
    ) or not os.path.isfile(os.path.join(entities_dir, "functions.json")):
        logging.info("Entitäten nicht gefunden. Extrahiere Entitäten...")
        try:
            from llm_stack.tools.entity_extraction import extract_entities

            extract_entities.extract_all_entities(root_dir)
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
                        )
                    ],
                    check=True,
                )
            except Exception as e:
                logging.error(
                    f"Fehler beim Ausführen von extract-entities.sh: {str(e)}"
                )
                return 1

    # Beziehungen abbilden, falls sie nicht existieren
    if not os.path.isfile(
        os.path.join(relationships_dir, "function_calls.json")
    ) or not os.path.isfile(
        os.path.join(relationships_dir, "component_dependencies.json")
    ):
        logging.info("Beziehungen nicht gefunden. Bilde Beziehungen ab...")
        try:
            from llm_stack.tools.relationship_mapping import map_relationships

            map_relationships.map_all_relationships(root_dir)
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
                        )
                    ],
                    check=True,
                )
            except Exception as e:
                logging.error(
                    f"Fehler beim Ausführen von map-relationships.sh: {str(e)}"
                )
                return 1

    # Knowledge Graph generieren
    if not generate_graph(graph_file, entities_dir, relationships_dir, root_dir):
        return 1

    # Visualisierungen generieren
    generate_visualizations(visualizations_dir, entities_dir, relationships_dir)

    logging.success("Knowledge Graph-Generierung erfolgreich abgeschlossen!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
