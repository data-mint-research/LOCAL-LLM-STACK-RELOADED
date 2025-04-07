"""
Beispiel für die Aufzeichnung einer Code-Transformation im Knowledge Graph.

Dieses Skript zeigt, wie eine Code-Transformation von Bash zu Python
im Knowledge Graph aufgezeichnet werden kann.
"""
import os
import sys

# Pfad zum Projektverzeichnis hinzufügen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llm_stack.core.file_utils import ensure_file_exists
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llm_stack.modules.knowledge_graph.module import get_module as get_kg_module

# Bash-Code der start_command-Funktion
BASH_CODE = """
# Start command implementation with improved user feedback
start_command() {
  local component=$1
  local module=$2

  if [[ -z "$component" ]]; then
    log_info "Starting all components..."
    # Check if secrets are generated before starting
    check_secrets
    docker_compose_op "up" "$CORE_PROJECT" "$CORE_COMPOSE" ""
    log_success "Core components started successfully."
    log_info "Tip: Use 'llm status' to check component status"
  elif [[ "$component" == "--with" ]]; then
    if [[ -z "$module" ]]; then
      handle_error $ERR_INVALID_ARGUMENT "Module name is required with --with flag"
    fi

    if [[ ! -d "modules/$module" ]]; then
      handle_error $ERR_MODULE_ERROR "Module not found: $module"
    fi

    log_info "Starting core components with $module module..."
    docker_compose_op "up" "$CORE_PROJECT" "$CORE_COMPOSE" ""
    docker_compose_op "up" "$CORE_PROJECT-$module" "-f modules/$module/docker-compose.yml" ""
    log_success "Core components and $module module started successfully."
    log_info "Tip: Use 'llm status' to check component status"
  else
    log_info "Starting $component component..."
    docker_compose_op "up" "$CORE_PROJECT-$component" "-f core/$component.yml" ""
    log_success "$component component started successfully."
  fi
}
"""

# Python-Code der start_command-Funktion
PYTHON_CODE = '''
def start_command(component: Optional[str] = None, module: Optional[str] = None) -> bool:
    """
    Implementiert den Start-Befehl.
    
    Args:
        component: Name der zu startenden Komponente
        module: Name des zu startenden Moduls
        
    Returns:
        bool: True, wenn der Befehl erfolgreich ausgeführt wurde, sonst False
    """
    if component is None and module is None:
        logging.info("Starte alle Komponenten...")
        # Prüfen, ob Secrets generiert sind
        config.check_secrets()
        if not docker.compose_up(config.CORE_PROJECT, config.CORE_COMPOSE, ""):
            return False
        logging.success("Kernkomponenten erfolgreich gestartet.")
        logging.info("Tipp: Verwenden Sie 'llm status', um den Komponentenstatus zu prüfen")
        return True
    elif module is not None:
        # Verwende file_utils, um zu prüfen, ob das Modul existiert
        module_path = f"modules/{module}"
        if not os.path.isdir(module_path):
            logging.error(f"Modul nicht gefunden: {module}")
            return False

        logging.info(f"Starte Kernkomponenten mit {module} Modul...")
        if not docker.compose_up(config.CORE_PROJECT, config.CORE_COMPOSE, ""):
            return False
        if not docker.compose_up(f"{config.CORE_PROJECT}-{module}", f"-f modules/{module}/docker-compose.yml", ""):
            return False
        logging.success(f"Kernkomponenten und {module} Modul erfolgreich gestartet.")
        logging.info("Tipp: Verwenden Sie 'llm status', um den Komponentenstatus zu prüfen")
        return True
    else:
        logging.info(f"Starte {component} Komponente...")
        if not docker.compose_up(f"{config.CORE_PROJECT}-{component}", f"-f core/{component}.yml", ""):
            return False
        logging.success(f"{component} Komponente erfolgreich gestartet.")
        return True
'''


def main():
    """Hauptfunktion."""
    try:
        # Knowledge Graph Modul abrufen
        kg_module = get_kg_module()

        # Prüfe, ob die Dateipfade existieren
        bash_file_path = "lib/common.sh"
        python_file_path = "llm_stack/core/common.py"
        
        # In diesem Beispiel müssen die Dateien nicht existieren, aber in einer realen Anwendung
        # würde man prüfen, ob die Dateien existieren, bevor man die Transformation aufzeichnet
        # if not ensure_file_exists(bash_file_path) or not ensure_file_exists(python_file_path):
        #     print(f"Eine oder beide Dateien existieren nicht: {bash_file_path}, {python_file_path}")
        #     return

        # Code-Transformation aufzeichnen
        result = kg_module.record_code_transformation(
            transformation_type="function_migration",
            before=BASH_CODE,
            after=PYTHON_CODE,
            bash_file_path=bash_file_path,
            python_file_path=python_file_path,
            decision_id=None,  # Hier könnte die ID einer zuvor aufgezeichneten Entscheidung stehen
        )

        if result:
            print("Code-Transformation erfolgreich aufgezeichnet")
        else:
            print("Fehler beim Aufzeichnen der Code-Transformation")
    except ImportError:
        print("Knowledge Graph Modul nicht verfügbar")
    except Exception as e:
        print(f"Fehler: {str(e)}")


if __name__ == "__main__":
    main()
