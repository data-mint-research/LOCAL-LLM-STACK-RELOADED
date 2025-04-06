"""
Knowledge Graph Modul für den LLM Stack.

Dieses Modul stellt Funktionen zur Integration des neo4j-Knowledge-Graphs bereit,
der als zentrale Wissensbasis für autonome AI Coding Agents dient.
"""

import os
import sys
from typing import Dict, List, Optional, Tuple, Union

import click
from rich.console import Console
from rich.table import Table

from llm_stack.core import config, docker, error, logging, system
from llm_stack.knowledge_graph import client, migration, models, schema

# Konsole für formatierte Ausgabe
console = Console()


class KnowledgeGraphModule:
    """Modul für die Integration des neo4j-Knowledge-Graphs."""
    
    def __init__(self):
        """Initialisiert das Knowledge Graph Modul."""
        self.name = "knowledge_graph"
        self.description = "Knowledge Graph Integration für autonome AI Coding Agents"
        self.neo4j_client = None
        self.schema_manager = None
    
    def start(self) -> bool:
        """
        Startet das Knowledge Graph Modul.
        
        Returns:
            bool: True, wenn das Modul erfolgreich gestartet wurde, sonst False
        """
        logging.info("Starte Knowledge Graph Modul...")
        
        # Docker Compose-Datei für neo4j starten
        if not docker.compose_up(
            f"{config.CORE_PROJECT}-{self.name}",
            f"-f docker/modules/neo4j.yml",
            ""
        ):
            logging.error("Fehler beim Starten des neo4j-Containers")
            return False
        
        # Warten, bis neo4j bereit ist
        if not docker.wait_for_container_health("neo4j", "healthy", 60):
            logging.warn("Timeout beim Warten auf neo4j. Versuche trotzdem fortzufahren...")
        
        # Neo4j-Client initialisieren
        uri = f"bolt://localhost:{config.get_config('HOST_PORT_NEO4J_BOLT', '7687')}"
        username = config.get_config("NEO4J_USERNAME", "neo4j")
        password = config.get_config("NEO4J_PASSWORD", "password")
        database = config.get_config("NEO4J_DATABASE", "neo4j")
        
        self.neo4j_client = client.init_client(uri, username, password, database)
        
        if not self.neo4j_client.connect():
            logging.error("Fehler beim Verbinden mit der neo4j-Datenbank")
            return False
        
        # Schema-Manager initialisieren
        self.schema_manager = schema.SchemaManager(self.neo4j_client)
        
        # Schema erstellen
        if not self.schema_manager.create_schema():
            logging.error("Fehler beim Erstellen des Schemas")
            return False
        
        # Vorhandenes Schema und Graph importieren, wenn vorhanden
        schema_file = os.path.join(system.get_project_root(), "docs/knowledge-graph/schema.json")
        graph_file = os.path.join(system.get_project_root(), "docs/knowledge-graph/graph.json")
        
        if os.path.isfile(schema_file):
            if not schema.import_json_ld_schema(schema_file, self.neo4j_client):
                logging.warn(f"Fehler beim Importieren des Schemas aus {schema_file}")
        
        if os.path.isfile(graph_file):
            if not schema.import_json_ld_graph(graph_file, self.neo4j_client):
                logging.warn(f"Fehler beim Importieren des Graphen aus {graph_file}")
        
        logging.success("Knowledge Graph Modul erfolgreich gestartet")
        return True
    
    def stop(self) -> bool:
        """
        Stoppt das Knowledge Graph Modul.
        
        Returns:
            bool: True, wenn das Modul erfolgreich gestoppt wurde, sonst False
        """
        logging.info("Stoppe Knowledge Graph Modul...")
        
        # Neo4j-Client schließen
        if self.neo4j_client:
            self.neo4j_client.close()
            self.neo4j_client = None
        
        # Docker Compose-Datei für neo4j stoppen
        if not docker.compose_down(
            f"{config.CORE_PROJECT}-{self.name}",
            f"-f docker/modules/neo4j.yml",
            ""
        ):
            logging.error("Fehler beim Stoppen des neo4j-Containers")
            return False
        
        logging.success("Knowledge Graph Modul erfolgreich gestoppt")
        return True
    
    def status(self) -> Dict:
        """
        Ruft den Status des Knowledge Graph Moduls ab.
        
        Returns:
            Dict: Status des Moduls
        """
        logging.info("Prüfe Status des Knowledge Graph Moduls...")
        
        # Container-Status abrufen
        container_status = docker.get_container_status("neo4j")
        
        # Verbindungsstatus prüfen
        connection_status = False
        if self.neo4j_client:
            connection_status = self.neo4j_client.ensure_connected()
        else:
            # Temporären Client erstellen
            uri = f"bolt://localhost:{config.get_config('HOST_PORT_NEO4J_BOLT', '7687')}"
            username = config.get_config("NEO4J_USERNAME", "neo4j")
            password = config.get_config("NEO4J_PASSWORD", "password")
            database = config.get_config("NEO4J_DATABASE", "neo4j")
            
            temp_client = client.Neo4jClient(uri, username, password, database)
            connection_status = temp_client.connect()
            temp_client.close()
        
        # Migrationsstatistiken abrufen
        migration_stats = {}
        if connection_status:
            migration_stats = migration.get_migration_statistics()
        
        return {
            "name": self.name,
            "description": self.description,
            "container_status": container_status["status"] if container_status else "not_running",
            "connection_status": "connected" if connection_status else "disconnected",
            "migration_stats": migration_stats
        }
    
    def record_migration_decision(
        self,
        decision: str,
        rationale: str,
        bash_file_path: Optional[str] = None,
        python_file_path: Optional[str] = None,
        alternatives: Optional[List[str]] = None,
        impact: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Zeichnet eine Migrationsentscheidung im Knowledge Graph auf.
        
        Args:
            decision: Die getroffene Entscheidung
            rationale: Begründung für die Entscheidung
            bash_file_path: Pfad zur Bash-Datei, auf die sich die Entscheidung bezieht
            python_file_path: Pfad zur Python-Datei, auf die sich die Entscheidung bezieht
            alternatives: Alternative Entscheidungen, die in Betracht gezogen wurden
            impact: Auswirkungen der Entscheidung
            
        Returns:
            Optional[Dict]: Erstellter Entscheidungsknoten oder None, wenn ein Fehler aufgetreten ist
        """
        if not self.neo4j_client or not self.neo4j_client.ensure_connected():
            logging.error("Keine Verbindung zur neo4j-Datenbank")
            return None
        
        return migration.record_migration_decision(
            decision,
            rationale,
            bash_file_path,
            python_file_path,
            alternatives,
            impact,
            self.neo4j_client
        )
    
    def record_code_transformation(
        self,
        transformation_type: str,
        before: str,
        after: str,
        bash_file_path: Optional[str] = None,
        python_file_path: Optional[str] = None,
        decision_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Zeichnet eine Code-Transformation im Knowledge Graph auf.
        
        Args:
            transformation_type: Typ der Transformation (z.B. "function_migration", "syntax_change")
            before: Code vor der Transformation
            after: Code nach der Transformation
            bash_file_path: Pfad zur Bash-Datei, auf die sich die Transformation bezieht
            python_file_path: Pfad zur Python-Datei, auf die sich die Transformation bezieht
            decision_id: ID der zugehörigen Migrationsentscheidung
            
        Returns:
            Optional[Dict]: Erstellter Transformationsknoten oder None, wenn ein Fehler aufgetreten ist
        """
        if not self.neo4j_client or not self.neo4j_client.ensure_connected():
            logging.error("Keine Verbindung zur neo4j-Datenbank")
            return None
        
        return migration.record_code_transformation(
            transformation_type,
            before,
            after,
            bash_file_path,
            python_file_path,
            decision_id,
            self.neo4j_client
        )
    
    def record_bash_file(
        self,
        file_path: str,
        content: str
    ) -> Optional[Dict]:
        """
        Zeichnet eine Bash-Datei im Knowledge Graph auf.
        
        Args:
            file_path: Pfad zur Bash-Datei
            content: Inhalt der Bash-Datei
            
        Returns:
            Optional[Dict]: Erstellter Dateiknoten oder None, wenn ein Fehler aufgetreten ist
        """
        if not self.neo4j_client or not self.neo4j_client.ensure_connected():
            logging.error("Keine Verbindung zur neo4j-Datenbank")
            return None
        
        return migration.record_bash_file(
            file_path,
            content,
            self.neo4j_client
        )
    
    def record_python_file(
        self,
        file_path: str,
        content: str,
        bash_file_path: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Zeichnet eine Python-Datei im Knowledge Graph auf.
        
        Args:
            file_path: Pfad zur Python-Datei
            content: Inhalt der Python-Datei
            bash_file_path: Pfad zur entsprechenden Bash-Datei
            
        Returns:
            Optional[Dict]: Erstellter Dateiknoten oder None, wenn ein Fehler aufgetreten ist
        """
        if not self.neo4j_client or not self.neo4j_client.ensure_connected():
            logging.error("Keine Verbindung zur neo4j-Datenbank")
            return None
        
        return migration.record_python_file(
            file_path,
            content,
            bash_file_path,
            self.neo4j_client
        )
    
    def get_migration_decisions(
        self,
        bash_file_path: Optional[str] = None,
        python_file_path: Optional[str] = None
    ) -> List[Dict]:
        """
        Ruft Migrationsentscheidungen aus dem Knowledge Graph ab.
        
        Args:
            bash_file_path: Pfad zur Bash-Datei, für die Entscheidungen abgerufen werden sollen
            python_file_path: Pfad zur Python-Datei, für die Entscheidungen abgerufen werden sollen
            
        Returns:
            List[Dict]: Liste von Migrationsentscheidungen
        """
        if not self.neo4j_client or not self.neo4j_client.ensure_connected():
            logging.error("Keine Verbindung zur neo4j-Datenbank")
            return []
        
        return migration.get_migration_decisions(
            bash_file_path,
            python_file_path,
            self.neo4j_client
        )
    
    def get_code_transformations(
        self,
        bash_file_path: Optional[str] = None,
        python_file_path: Optional[str] = None,
        transformation_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Ruft Code-Transformationen aus dem Knowledge Graph ab.
        
        Args:
            bash_file_path: Pfad zur Bash-Datei, für die Transformationen abgerufen werden sollen
            python_file_path: Pfad zur Python-Datei, für die Transformationen abgerufen werden sollen
            transformation_type: Typ der Transformation
            
        Returns:
            List[Dict]: Liste von Code-Transformationen
        """
        if not self.neo4j_client or not self.neo4j_client.ensure_connected():
            logging.error("Keine Verbindung zur neo4j-Datenbank")
            return []
        
        return migration.get_code_transformations(
            bash_file_path,
            python_file_path,
            transformation_type,
            self.neo4j_client
        )
    
    def get_file_migration_status(
        self,
        bash_file_path: str
    ) -> Dict:
        """
        Ruft den Migrationsstatus einer Datei aus dem Knowledge Graph ab.
        
        Args:
            bash_file_path: Pfad zur Bash-Datei
            
        Returns:
            Dict: Migrationsstatus der Datei
        """
        if not self.neo4j_client or not self.neo4j_client.ensure_connected():
            logging.error("Keine Verbindung zur neo4j-Datenbank")
            return {
                "bash_file": bash_file_path,
                "python_file": None,
                "migrated": False,
                "decisions": [],
                "transformations": []
            }
        
        return migration.get_file_migration_status(
            bash_file_path,
            self.neo4j_client
        )
    
    def get_migration_statistics(self) -> Dict:
        """
        Ruft Migrationsstatistiken aus dem Knowledge Graph ab.
        
        Returns:
            Dict: Migrationsstatistiken
        """
        if not self.neo4j_client or not self.neo4j_client.ensure_connected():
            logging.error("Keine Verbindung zur neo4j-Datenbank")
            return {
                "total_bash_files": 0,
                "total_python_files": 0,
                "migrated_files": 0,
                "migration_progress": 0.0,
                "total_decisions": 0,
                "total_transformations": 0
            }
        
        return migration.get_migration_statistics(self.neo4j_client)
    
    def show_migration_statistics(self) -> None:
        """Zeigt Migrationsstatistiken in einer formatierten Tabelle an."""
        stats = self.get_migration_statistics()
        
        # Tabelle erstellen
        table = Table(title="Migration Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        # Zeilen hinzufügen
        table.add_row("Total Bash Files", str(stats["total_bash_files"]))
        table.add_row("Total Python Files", str(stats["total_python_files"]))
        table.add_row("Migrated Files", str(stats["migrated_files"]))
        table.add_row("Migration Progress", f"{stats['migration_progress']:.2f}%")
        table.add_row("Total Decisions", str(stats["total_decisions"]))
        table.add_row("Total Transformations", str(stats["total_transformations"]))
        
        # Tabelle anzeigen
        console.print(table)


# Singleton-Instanz des Knowledge Graph Moduls
_module = None


def get_module() -> KnowledgeGraphModule:
    """
    Ruft die Singleton-Instanz des Knowledge Graph Moduls ab.
    
    Returns:
        KnowledgeGraphModule: Knowledge Graph Modul-Instanz
    """
    global _module
    
    if _module is None:
        _module = KnowledgeGraphModule()
    
    return _module


# CLI-Befehle für das Knowledge Graph Modul
@click.group(name="kg")
def kg_cli():
    """Knowledge Graph Befehle."""
    pass


@kg_cli.command(name="status")
def status_command():
    """Zeigt den Status des Knowledge Graph Moduls an."""
    module = get_module()
    status = module.status()
    
    # Tabelle erstellen
    table = Table(title="Knowledge Graph Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    # Zeilen hinzufügen
    table.add_row("Name", status["name"])
    table.add_row("Description", status["description"])
    table.add_row("Container Status", status["container_status"])
    table.add_row("Connection Status", status["connection_status"])
    
    # Tabelle anzeigen
    console.print(table)
    
    # Migrationsstatistiken anzeigen, wenn verbunden
    if status["connection_status"] == "connected":
        module.show_migration_statistics()


@kg_cli.command(name="stats")
def stats_command():
    """Zeigt Migrationsstatistiken an."""
    module = get_module()
    module.show_migration_statistics()


@kg_cli.command(name="record-decision")
@click.option("--decision", required=True, help="Die getroffene Entscheidung")
@click.option("--rationale", required=True, help="Begründung für die Entscheidung")
@click.option("--bash-file", help="Pfad zur Bash-Datei")
@click.option("--python-file", help="Pfad zur Python-Datei")
@click.option("--alternatives", help="Alternative Entscheidungen (kommagetrennt)")
@click.option("--impact", help="Auswirkungen der Entscheidung")
def record_decision_command(decision, rationale, bash_file, python_file, alternatives, impact):
    """Zeichnet eine Migrationsentscheidung auf."""
    module = get_module()
    
    # Alternativen in Liste umwandeln
    alt_list = None
    if alternatives:
        alt_list = [alt.strip() for alt in alternatives.split(",")]
    
    result = module.record_migration_decision(
        decision,
        rationale,
        bash_file,
        python_file,
        alt_list,
        impact
    )
    
    if result:
        logging.success("Migrationsentscheidung erfolgreich aufgezeichnet")
    else:
        logging.error("Fehler beim Aufzeichnen der Migrationsentscheidung")


@kg_cli.command(name="record-transformation")
@click.option("--type", "transformation_type", required=True, help="Typ der Transformation")
@click.option("--before", required=True, help="Code vor der Transformation")
@click.option("--after", required=True, help="Code nach der Transformation")
@click.option("--bash-file", help="Pfad zur Bash-Datei")
@click.option("--python-file", help="Pfad zur Python-Datei")
@click.option("--decision-id", help="ID der zugehörigen Migrationsentscheidung")
def record_transformation_command(transformation_type, before, after, bash_file, python_file, decision_id):
    """Zeichnet eine Code-Transformation auf."""
    module = get_module()
    
    result = module.record_code_transformation(
        transformation_type,
        before,
        after,
        bash_file,
        python_file,
        decision_id
    )
    
    if result:
        logging.success("Code-Transformation erfolgreich aufgezeichnet")
    else:
        logging.error("Fehler beim Aufzeichnen der Code-Transformation")


@kg_cli.command(name="record-bash-file")
@click.option("--file-path", required=True, help="Pfad zur Bash-Datei")
@click.option("--content-file", help="Pfad zur Datei mit dem Inhalt")
@click.option("--content", help="Inhalt der Bash-Datei")
def record_bash_file_command(file_path, content_file, content):
    """Zeichnet eine Bash-Datei auf."""
    module = get_module()
    
    # Inhalt aus Datei oder Parameter laden
    if content_file:
        with open(content_file, "r") as f:
            content = f.read()
    elif not content:
        logging.error("Entweder --content oder --content-file muss angegeben werden")
        return
    
    result = module.record_bash_file(file_path, content)
    
    if result:
        logging.success(f"Bash-Datei {file_path} erfolgreich aufgezeichnet")
    else:
        logging.error(f"Fehler beim Aufzeichnen der Bash-Datei {file_path}")


@kg_cli.command(name="record-python-file")
@click.option("--file-path", required=True, help="Pfad zur Python-Datei")
@click.option("--content-file", help="Pfad zur Datei mit dem Inhalt")
@click.option("--content", help="Inhalt der Python-Datei")
@click.option("--bash-file", help="Pfad zur entsprechenden Bash-Datei")
def record_python_file_command(file_path, content_file, content, bash_file):
    """Zeichnet eine Python-Datei auf."""
    module = get_module()
    
    # Inhalt aus Datei oder Parameter laden
    if content_file:
        with open(content_file, "r") as f:
            content = f.read()
    elif not content:
        logging.error("Entweder --content oder --content-file muss angegeben werden")
        return
    
    result = module.record_python_file(file_path, content, bash_file)
    
    if result:
        logging.success(f"Python-Datei {file_path} erfolgreich aufgezeichnet")
    else:
        logging.error(f"Fehler beim Aufzeichnen der Python-Datei {file_path}")


@kg_cli.command(name="get-decisions")
@click.option("--bash-file", help="Pfad zur Bash-Datei")
@click.option("--python-file", help="Pfad zur Python-Datei")
def get_decisions_command(bash_file, python_file):
    """Ruft Migrationsentscheidungen ab."""
    module = get_module()
    
    decisions = module.get_migration_decisions(bash_file, python_file)
    
    if not decisions:
        logging.info("Keine Migrationsentscheidungen gefunden")
        return
    
    # Tabelle erstellen
    table = Table(title="Migration Decisions")
    table.add_column("ID", style="cyan")
    table.add_column("Decision", style="green")
    table.add_column("Rationale", style="yellow")
    
    # Zeilen hinzufügen
    for decision in decisions:
        table.add_row(
            decision.get("id", ""),
            decision.get("decision", ""),
            decision.get("rationale", "")
        )
    
    # Tabelle anzeigen
    console.print(table)


@kg_cli.command(name="get-transformations")
@click.option("--bash-file", help="Pfad zur Bash-Datei")
@click.option("--python-file", help="Pfad zur Python-Datei")
@click.option("--type", "transformation_type", help="Typ der Transformation")
def get_transformations_command(bash_file, python_file, transformation_type):
    """Ruft Code-Transformationen ab."""
    module = get_module()
    
    transformations = module.get_code_transformations(bash_file, python_file, transformation_type)
    
    if not transformations:
        logging.info("Keine Code-Transformationen gefunden")
        return
    
    # Tabelle erstellen
    table = Table(title="Code Transformations")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Before", style="yellow")
    table.add_column("After", style="blue")
    
    # Zeilen hinzufügen
    for transformation in transformations:
        # Gekürzte Versionen für die Tabelle
        before = transformation.get("before", "")
        after = transformation.get("after", "")
        
        if len(before) > 50:
            before = before[:47] + "..."
        
        if len(after) > 50:
            after = after[:47] + "..."
        
        table.add_row(
            transformation.get("id", ""),
            transformation.get("transformation_type", ""),
            before,
            after
        )
    
    # Tabelle anzeigen
    console.print(table)


@kg_cli.command(name="get-file-status")
@click.option("--bash-file", required=True, help="Pfad zur Bash-Datei")
def get_file_status_command(bash_file):
    """Ruft den Migrationsstatus einer Datei ab."""
    module = get_module()
    
    status = module.get_file_migration_status(bash_file)
    
    # Tabelle erstellen
    table = Table(title=f"Migration Status: {bash_file}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    # Zeilen hinzufügen
    table.add_row("Bash File", status["bash_file"])
    table.add_row("Python File", status["python_file"] or "Not migrated")
    table.add_row("Migrated", "Yes" if status["migrated"] else "No")
    table.add_row("Decisions", str(len(status["decisions"])))
    table.add_row("Transformations", str(len(status["transformations"])))
    
    # Tabelle anzeigen
    console.print(table)


# Modul initialisieren
logging.debug("Knowledge Graph Modul initialisiert")