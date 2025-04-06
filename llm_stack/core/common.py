"""
Gemeinsame Funktionen für den LLM Stack CLI.

Dieses Modul stellt gemeinsame Funktionen für die LLM Stack CLI bereit,
die von verschiedenen Befehlen verwendet werden.
"""

import os
import sys
from typing import Dict, List, Optional, Tuple, Union

import click
from rich.console import Console
from rich.table import Table

from llm_stack.core import config, docker, error, logging, system
from llm_stack.knowledge_graph import client as kg_client
from llm_stack.modules.knowledge_graph.module import get_module as get_kg_module

# Konsole für formatierte Ausgabe
console = Console()

# Knowledge Graph Modul
kg_module = None
try:
    kg_module = get_kg_module()
except ImportError:
    logging.debug("Knowledge Graph Modul nicht verfügbar")


# Start-Befehl-Implementierung mit verbessertem Benutzerfeedback
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
        if not os.path.isdir(f"modules/{module}"):
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


# Stop-Befehl-Implementierung mit verbessertem Benutzerfeedback
def stop_command(component: Optional[str] = None, module: Optional[str] = None) -> bool:
    """
    Implementiert den Stop-Befehl.
    
    Args:
        component: Name der zu stoppenden Komponente
        module: Name des zu stoppenden Moduls
        
    Returns:
        bool: True, wenn der Befehl erfolgreich ausgeführt wurde, sonst False
    """
    if component is None and module is None:
        logging.info("Stoppe alle Komponenten...")
        if not docker.compose_down(config.CORE_PROJECT, config.CORE_COMPOSE, ""):
            return False
        logging.success("Alle Komponenten erfolgreich gestoppt.")
        return True
    elif module is not None:
        if not os.path.isdir(f"modules/{module}"):
            logging.error(f"Modul nicht gefunden: {module}")
            return False

        logging.info(f"Stoppe Kernkomponenten und {module} Modul...")
        if not docker.compose_down(f"{config.CORE_PROJECT}-{module}", f"-f modules/{module}/docker-compose.yml", ""):
            return False
        if not docker.compose_down(config.CORE_PROJECT, config.CORE_COMPOSE, ""):
            return False
        logging.success(f"Kernkomponenten und {module} Modul erfolgreich gestoppt.")
        return True
    else:
        logging.info(f"Stoppe {component} Komponente...")
        if not docker.compose_down(f"{config.CORE_PROJECT}-{component}", f"-f core/{component}.yml", ""):
            return False
        logging.success(f"{component} Komponente erfolgreich gestoppt.")
        return True


# Debug-Befehl-Implementierung mit verbesserter Benutzerführung
def debug_command(component: Optional[str] = None) -> bool:
    """
    Implementiert den Debug-Befehl.
    
    Args:
        component: Name der zu debuggenden Komponente
        
    Returns:
        bool: True, wenn der Befehl erfolgreich ausgeführt wurde, sonst False
    """
    if component is None:
        logging.info("Starte alle Komponenten im Debug-Modus...")
        # Prüfen, ob Secrets generiert sind
        config.check_secrets()
        if not docker.compose_up(config.DEBUG_PROJECT, config.DEBUG_COMPOSE, ""):
            return False
        logging.success("Kernkomponenten im Debug-Modus gestartet.")
        logging.info("LibreChat Node.js-Debugger ist verfügbar unter localhost:9229")
        logging.info("Tipp: Verwenden Sie VSCode's 'Attach to LibreChat' Debug-Konfiguration zum Verbinden")
        return True
    elif component == "librechat":
        logging.info("Starte LibreChat im Debug-Modus...")
        if not docker.compose_up(config.DEBUG_PROJECT, config.DEBUG_COMPOSE, "librechat"):
            return False
        logging.success("LibreChat im Debug-Modus gestartet.")
        logging.info("Node.js-Debugger ist verfügbar unter localhost:9229")
        logging.info("Tipp: Verwenden Sie VSCode's 'Attach to LibreChat' Debug-Konfiguration zum Verbinden")
        return True
    else:
        logging.error("Debug-Modus wird derzeit nur für LibreChat unterstützt.")
        logging.info("Verwendung: llm debug [librechat]")
        return False


# Status-Befehl-Implementierung mit verbesserter Formatierung
def status_command() -> bool:
    """
    Implementiert den Status-Befehl.
    
    Returns:
        bool: True, wenn der Befehl erfolgreich ausgeführt wurde, sonst False
    """
    logging.info("Prüfe Status aller Komponenten...")

    # Container-Status mit besserer Formatierung abrufen
    docker.show_container_status()

    # Hilfreiche Tipps anzeigen
    # Port-Werte mit Fallbacks abrufen
    librechat_port = config.get_config("HOST_PORT_LIBRECHAT", "3080")
    ollama_port = config.get_config("HOST_PORT_OLLAMA", "11434")

    console.print()
    logging.info(f"Tipp: Zugriff auf LibreChat unter http://localhost:{librechat_port}")
    logging.info(f"Tipp: Ollama API ist verfügbar unter http://localhost:{ollama_port}")
    
    return True


# Models-Befehl-Implementierung mit verbesserter Benutzerführung
def models_command(action: str, model: Optional[str] = None) -> bool:
    """
    Implementiert den Models-Befehl.
    
    Args:
        action: Auszuführende Aktion (list, add, remove)
        model: Name des Modells
        
    Returns:
        bool: True, wenn der Befehl erfolgreich ausgeführt wurde, sonst False
    """
    from llm_stack.core import models as models_module
    
    # Ollama-Port mit Fallback abrufen
    ollama_port = config.get_config("HOST_PORT_OLLAMA", "11434")
    ollama_url = f"http://localhost:{ollama_port}"
    
    # Prüfen, ob Ollama läuft
    if not models_module.check_ollama_running(ollama_url):
        logging.error("Ollama-Dienst läuft nicht.")
        logging.info("Tipp: Starten Sie Ollama zuerst mit 'llm start ollama'")
        return False
    
    if action == "list":
        models_module.list_models(ollama_url)
        return True
    elif action == "add":
        if model is None:
            logging.error("Modellname ist für die Aktion 'add' erforderlich")
            return False
        return models_module.add_model(ollama_url, model)
    elif action == "remove":
        if model is None:
            logging.error("Modellname ist für die Aktion 'remove' erforderlich")
            return False
        return models_module.remove_model(ollama_url, model)
    else:
        logging.info("Verwendung: llm models [list|add|remove] [model_name]")
        console.print()
        console.print("Beispiele:")
        console.print("  llm models list           Liste aller verfügbaren Modelle")
        console.print("  llm models add llama3     Füge das Llama 3 Modell hinzu")
        console.print("  llm models remove mistral Entferne das Mistral Modell")
        return False


# Config-Befehl-Implementierung mit verbesserter Benutzerführung
def config_command(action: str) -> bool:
    """
    Implementiert den Config-Befehl.
    
    Args:
        action: Auszuführende Aktion (show, edit)
        
    Returns:
        bool: True, wenn der Befehl erfolgreich ausgeführt wurde, sonst False
    """
    if action == "show":
        logging.info("Zeige Konfiguration...")
        config.show_config()
        
        # Hilfreiche Tipps anzeigen
        console.print()
        logging.info("Tipp: Bearbeiten Sie die Konfiguration mit 'llm config edit'")
        return True
    elif action == "edit":
        logging.info("Erstelle Backup der Konfiguration...")
        backup_file = config.backup_config_file()
        if backup_file is None:
            logging.error("Fehler beim Erstellen eines Backups der Konfigurationsdatei")
            return False
        
        logging.info("Bearbeite Konfiguration...")
        config.edit_config()
        
        logging.warn("Hinweis: Wenn Sie einen Fehler gemacht haben, können Sie vom Backup wiederherstellen:")
        logging.warn(f"cp {backup_file} {config.ENV_FILE}")
        return True
    else:
        logging.info("Verwendung: llm config [show|edit]")
        console.print()
        console.print("Beispiele:")
        console.print("  llm config show    Zeige aktuelle Konfiguration")
        console.print("  llm config edit    Bearbeite Konfiguration in deinem Standardeditor")
        return False


# Generate-Secrets-Befehl-Implementierung mit verbesserter Benutzerführung
def generate_secrets_command() -> bool:
    """
    Implementiert den Generate-Secrets-Befehl.
    
    Returns:
        bool: True, wenn der Befehl erfolgreich ausgeführt wurde, sonst False
    """
    # Die Core-Bibliotheksfunktion verwenden
    return config.generate_secrets()


# Befehle und Beschreibungen als Dictionary
COMMANDS = {
    "start": "Starte den Stack oder bestimmte Komponenten",
    "stop": "Stoppe den Stack oder bestimmte Komponenten",
    "status": "Zeige Status aller Komponenten",
    "debug": "Starte Komponenten im Debug-Modus",
    "models": "Verwalte Modelle",
    "config": "Zeige/bearbeite Konfiguration",
    "generate-secrets": "Generiere sichere Secrets für die Konfiguration",
    "help": "Zeige Hilfe für einen Befehl",
}


# Help-Befehl-Implementierung mit verbesserter Formatierung
def help_command(command: Optional[str] = None) -> bool:
    """
    Implementiert den Help-Befehl.
    
    Args:
        command: Name des Befehls, für den Hilfe angezeigt werden soll
        
    Returns:
        bool: True, wenn der Befehl erfolgreich ausgeführt wurde, sonst False
    """
    if command is None:
        console.print("Verwendung: llm [command] [options]")
        console.print()
        console.print("Befehle:")
        # Befehle für konsistente Anzeige sortieren
        for cmd in sorted(COMMANDS.keys()):
            console.print(f"  {cmd:<15} {COMMANDS[cmd]}")
        console.print()
        console.print("Führen Sie 'llm help [command]' aus, um weitere Informationen zu einem Befehl zu erhalten.")
        return True
    
    if command == "start":
        console.print("Verwendung: llm start [component|--with module]")
        console.print()
        console.print("Starte den Stack oder bestimmte Komponenten.")
        console.print()
        console.print("Optionen:")
        console.print("  component       Name der zu startenden Komponente (z.B. ollama, librechat)")
        console.print("  --with module   Starte mit einem bestimmten Modul (z.B. monitoring, security)")
        console.print()
        console.print("Beispiele:")
        console.print("  llm start                 Starte alle Komponenten")
        console.print("  llm start ollama          Starte nur die Ollama-Komponente")
        console.print("  llm start --with monitoring  Starte mit dem Monitoring-Modul")
    elif command == "stop":
        console.print("Verwendung: llm stop [component|--with module]")
        console.print()
        console.print("Stoppe den Stack oder bestimmte Komponenten.")
        console.print()
        console.print("Optionen:")
        console.print("  component       Name der zu stoppenden Komponente (z.B. ollama, librechat)")
        console.print("  --with module   Stoppe mit einem bestimmten Modul (z.B. monitoring, security)")
        console.print()
        console.print("Beispiele:")
        console.print("  llm stop                  Stoppe alle Komponenten")
        console.print("  llm stop librechat        Stoppe nur die LibreChat-Komponente")
        console.print("  llm stop --with monitoring  Stoppe Kernkomponenten und Monitoring-Modul")
    elif command == "status":
        console.print("Verwendung: llm status")
        console.print()
        console.print("Zeige Status aller Komponenten.")
        console.print()
        console.print("Dieser Befehl zeigt den Status aller laufenden Container an,")
        console.print("einschließlich ihrer Namen, Status und exponierten Ports.")
    elif command == "debug":
        console.print("Verwendung: llm debug [component]")
        console.print()
        console.print("Starte Komponenten im Debug-Modus.")
        console.print()
        console.print("Optionen:")
        console.print("  component       Name der zu debuggenden Komponente (derzeit wird nur 'librechat' unterstützt)")
        console.print()
        console.print("Beispiele:")
        console.print("  llm debug                Starte alle Komponenten im Debug-Modus")
        console.print("  llm debug librechat      Starte nur LibreChat im Debug-Modus")
        console.print()
        console.print("Im Debug-Modus ist der Node.js-Debugger unter localhost:9229 verfügbar.")
        console.print("Sie können sich mit VSCode's 'Attach to LibreChat' Debug-Konfiguration verbinden.")
    elif command == "models":
        console.print("Verwendung: llm models [list|add|remove] [model_name]")
        console.print()
        console.print("Verwalte Modelle.")
        console.print()
        console.print("Aktionen:")
        console.print("  list            Liste verfügbarer Modelle")
        console.print("  add model_name  Füge ein neues Modell hinzu")
        console.print("  remove model_name Entferne ein Modell")
        console.print()
        console.print("Beispiele:")
        console.print("  llm models list           Liste aller verfügbaren Modelle")
        console.print("  llm models add llama3     Füge das Llama 3 Modell hinzu")
        console.print("  llm models remove mistral Entferne das Mistral Modell")
    elif command == "config":
        console.print("Verwendung: llm config [show|edit]")
        console.print()
        console.print("Zeige oder bearbeite Konfiguration.")
        console.print()
        console.print("Aktionen:")
        console.print("  show            Zeige aktuelle Konfiguration")
        console.print("  edit            Bearbeite Konfiguration in deinem Standardeditor")
        console.print()
        console.print("Beispiele:")
        console.print("  llm config show    Zeige aktuelle Konfiguration")
        console.print("  llm config edit    Bearbeite Konfiguration in deinem Standardeditor")
    elif command == "generate-secrets":
        console.print("Verwendung: llm generate-secrets")
        console.print()
        console.print("Generiere sichere zufällige Secrets für die Konfiguration.")
        console.print()
        console.print("Dieser Befehl wird:")
        console.print("  1. Ein Backup der aktuellen Konfiguration erstellen")
        console.print("  2. Sichere zufällige Werte für alle Secret-Felder generieren")
        console.print("  3. Die Konfigurationsdatei mit diesen Werten aktualisieren")
        console.print("  4. Das Admin-Passwort anzeigen (speichern Sie dies an einem sicheren Ort)")
    else:
        console.print(f"Unbekannter Befehl: {command}")
        console.print("Führen Sie 'llm help' aus, um eine Liste verfügbarer Befehle zu erhalten.")
        return False
    
    return True


# Konfiguration laden
config.load_config()

# Migrationsentscheidung im Knowledge Graph aufzeichnen
if kg_module:
    try:
        kg_module.record_migration_decision(
            decision="common.sh nach Python migrieren",
            rationale="Bessere Typsicherheit, Modularität und Wartbarkeit durch Verwendung von Python-Klassen und -Funktionen",
            bash_file_path="lib/common.sh",
            python_file_path="llm_stack/core/common.py",
            alternatives=["Bash-Skript beibehalten", "Teilweise Migration"],
            impact="Verbesserte Codequalität, bessere Testbarkeit und einfachere Erweiterbarkeit"
        )
        
        # Bash-Datei im Knowledge Graph aufzeichnen
        with open("local-llm-stack/lib/common.sh", "r") as f:
            bash_content = f.read()
            kg_module.record_bash_file("lib/common.sh", bash_content)
        
        # Python-Datei im Knowledge Graph aufzeichnen
        with open(__file__, "r") as f:
            python_content = f.read()
            kg_module.record_python_file("llm_stack/core/common.py", python_content, "lib/common.sh")
    except Exception as e:
        logging.debug(f"Fehler beim Aufzeichnen der Migrationsentscheidung: {str(e)}")

logging.debug("Common-Funktionen-Modul initialisiert")