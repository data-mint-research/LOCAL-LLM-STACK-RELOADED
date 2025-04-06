#!/usr/bin/env python3
"""
LLM Stack CLI - Befehlszeilenschnittstelle für den LLM Stack.

Diese Datei implementiert die Befehlszeilenschnittstelle für den LLM Stack,
die als Ersatz für das ursprüngliche Bash-basierte CLI dient.
"""

import os
import sys
from typing import Optional

import click
from rich.console import Console

from llm_stack import __version__
from llm_stack.core import config, docker, logging
from llm_stack.modules.knowledge_graph.module import kg_cli

# Konsole für formatierte Ausgabe
console = Console()


@click.group(invoke_without_command=True)
@click.version_option(version=__version__)
@click.pass_context
def main(ctx: click.Context) -> None:
    """LOCAL-LLM-Stack CLI.

    Diese Befehlszeilenschnittstelle ermöglicht die Verwaltung des LOCAL-LLM-Stacks,
    einschließlich Starten, Stoppen, Statusprüfung und Konfiguration der Komponenten.
    """
    # Konfiguration laden
    config.load_config()

    # Wenn kein Unterbefehl angegeben ist, Hilfe anzeigen
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.argument("component", required=False)
@click.option("--with", "with_module", help="Modul, das zusammen mit den Kernkomponenten gestartet werden soll")
def start(component: Optional[str], with_module: Optional[str]) -> None:
    """Startet den Stack oder bestimmte Komponenten.

    COMPONENT ist der Name der zu startenden Komponente (z.B. ollama, librechat).
    Wenn keine Komponente angegeben ist, werden alle Komponenten gestartet.
    """
    if component is None and with_module is None:
        logging.info("Starte alle Komponenten...")
        # Prüfen, ob Secrets generiert sind
        config.check_secrets()
        docker.compose_up(config.CORE_PROJECT, config.CORE_COMPOSE, "")
        logging.success("Kernkomponenten erfolgreich gestartet.")
        logging.info("Tipp: Verwenden Sie 'llm status', um den Komponentenstatus zu prüfen")
    elif with_module is not None:
        if not os.path.isdir(f"modules/{with_module}"):
            logging.error(f"Modul nicht gefunden: {with_module}")
            sys.exit(1)

        logging.info(f"Starte Kernkomponenten mit {with_module} Modul...")
        docker.compose_up(config.CORE_PROJECT, config.CORE_COMPOSE, "")
        docker.compose_up(f"{config.CORE_PROJECT}-{with_module}", f"-f modules/{with_module}/docker-compose.yml", "")
        logging.success(f"Kernkomponenten und {with_module} Modul erfolgreich gestartet.")
        logging.info("Tipp: Verwenden Sie 'llm status', um den Komponentenstatus zu prüfen")
    else:
        logging.info(f"Starte {component} Komponente...")
        docker.compose_up(f"{config.CORE_PROJECT}-{component}", f"-f core/{component}.yml", "")
        logging.success(f"{component} Komponente erfolgreich gestartet.")


@main.command()
@click.argument("component", required=False)
@click.option("--with", "with_module", help="Modul, das zusammen mit den Kernkomponenten gestoppt werden soll")
def stop(component: Optional[str], with_module: Optional[str]) -> None:
    """Stoppt den Stack oder bestimmte Komponenten.

    COMPONENT ist der Name der zu stoppenden Komponente (z.B. ollama, librechat).
    Wenn keine Komponente angegeben ist, werden alle Komponenten gestoppt.
    """
    if component is None and with_module is None:
        logging.info("Stoppe alle Komponenten...")
        docker.compose_down(config.CORE_PROJECT, config.CORE_COMPOSE, "")
        logging.success("Alle Komponenten erfolgreich gestoppt.")
    elif with_module is not None:
        if not os.path.isdir(f"modules/{with_module}"):
            logging.error(f"Modul nicht gefunden: {with_module}")
            sys.exit(1)

        logging.info(f"Stoppe Kernkomponenten und {with_module} Modul...")
        docker.compose_down(f"{config.CORE_PROJECT}-{with_module}", f"-f modules/{with_module}/docker-compose.yml", "")
        docker.compose_down(config.CORE_PROJECT, config.CORE_COMPOSE, "")
        logging.success(f"Kernkomponenten und {with_module} Modul erfolgreich gestoppt.")
    else:
        logging.info(f"Stoppe {component} Komponente...")
        docker.compose_down(f"{config.CORE_PROJECT}-{component}", f"-f core/{component}.yml", "")
        logging.success(f"{component} Komponente erfolgreich gestoppt.")


@main.command()
def status() -> None:
    """Zeigt den Status aller Komponenten an."""
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


@main.command()
@click.argument("component", required=False)
def debug(component: Optional[str]) -> None:
    """Startet Komponenten im Debug-Modus.

    COMPONENT ist der Name der zu debuggenden Komponente (derzeit wird nur 'librechat' unterstützt).
    Wenn keine Komponente angegeben ist, werden alle Komponenten im Debug-Modus gestartet.
    """
    if component is None:
        logging.info("Starte alle Komponenten im Debug-Modus...")
        # Prüfen, ob Secrets generiert sind
        config.check_secrets()
        docker.compose_up(config.DEBUG_PROJECT, config.DEBUG_COMPOSE, "")
        logging.success("Kernkomponenten im Debug-Modus gestartet.")
        logging.info("LibreChat Node.js-Debugger ist verfügbar unter localhost:9229")
        logging.info("Tipp: Verwenden Sie VSCode's 'Attach to LibreChat' Debug-Konfiguration zum Verbinden")
    elif component == "librechat":
        logging.info("Starte LibreChat im Debug-Modus...")
        docker.compose_up(config.DEBUG_PROJECT, config.DEBUG_COMPOSE, "librechat")
        logging.success("LibreChat im Debug-Modus gestartet.")
        logging.info("Node.js-Debugger ist verfügbar unter localhost:9229")
        logging.info("Tipp: Verwenden Sie VSCode's 'Attach to LibreChat' Debug-Konfiguration zum Verbinden")
    else:
        logging.error("Debug-Modus wird derzeit nur für LibreChat unterstützt.")
        logging.info("Verwendung: llm debug [librechat]")
        sys.exit(1)


@main.command()
@click.argument("action", type=click.Choice(["list", "add", "remove"]))
@click.argument("model", required=False)
def models(action: str, model: Optional[str]) -> None:
    """Verwaltet Modelle.

    ACTION ist die auszuführende Aktion (list, add, remove).
    MODEL ist der Name des Modells (erforderlich für add und remove).
    """
    from llm_stack.core import models as models_module
    
    # Ollama-Port mit Fallback abrufen
    ollama_port = config.get_config("HOST_PORT_OLLAMA", "11434")
    ollama_url = f"http://localhost:{ollama_port}"
    
    # Prüfen, ob Ollama läuft
    if not models_module.check_ollama_running(ollama_url):
        logging.error("Ollama-Dienst läuft nicht.")
        logging.info("Tipp: Starten Sie Ollama zuerst mit 'llm start ollama'")
        sys.exit(1)
    
    if action == "list":
        models_module.list_models(ollama_url)
    elif action == "add":
        if model is None:
            logging.error("Modellname ist für die Aktion 'add' erforderlich")
            sys.exit(1)
        models_module.add_model(ollama_url, model)
    elif action == "remove":
        if model is None:
            logging.error("Modellname ist für die Aktion 'remove' erforderlich")
            sys.exit(1)
        models_module.remove_model(ollama_url, model)


@main.command()
@click.argument("action", type=click.Choice(["show", "edit"]))
def config_cmd(action: str) -> None:
    """Zeigt oder bearbeitet die Konfiguration.

    ACTION ist die auszuführende Aktion (show, edit).
    """
    if action == "show":
        logging.info("Zeige Konfiguration...")
        config.show_config()
        
        # Hilfreiche Tipps anzeigen
        console.print()
        logging.info("Tipp: Bearbeiten Sie die Konfiguration mit 'llm config edit'")
    elif action == "edit":
        logging.info("Erstelle Backup der Konfiguration...")
        backup_file = config.backup_config_file()
        if backup_file is None:
            logging.error("Fehler beim Erstellen eines Backups der Konfigurationsdatei")
            sys.exit(1)
        
        logging.info("Bearbeite Konfiguration...")
        config.edit_config()
        
        logging.warn("Hinweis: Wenn Sie einen Fehler gemacht haben, können Sie vom Backup wiederherstellen:")
        logging.warn(f"cp {backup_file} {config.ENV_FILE}")


@main.command()
def generate_secrets() -> None:
    """Generiert sichere Secrets für die Konfiguration."""
    # Die Core-Bibliotheksfunktion verwenden
    config.generate_secrets()


@main.help_option("-h", "--help")
def help_cmd() -> None:
    """Zeigt Hilfe für einen Befehl an."""
    pass


if __name__ == "__main__":
    main()

# Füge die Knowledge Graph CLI-Befehle hinzu
main.add_command(kg_cli)