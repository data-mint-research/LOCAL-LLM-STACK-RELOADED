"""
Schema für den LLM Stack Knowledge Graph.

Dieses Modul definiert das Schema für den neo4j-Knowledge-Graph
basierend auf dem bestehenden JSON-LD-Schema.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from llm_stack.core import error, logging
from llm_stack.knowledge_graph.client import Neo4jClient, get_client


class NodeLabel(str, Enum):
    """Labels für Knoten im Knowledge Graph."""
    
    # Basisklassen
    ENTITY = "Entity"
    COMPONENT = "Component"
    RELATIONSHIP = "Relationship"
    INTERFACE = "Interface"
    DATA_FLOW = "DataFlow"
    
    # Komponententypen
    CONTAINER = "Container"
    SCRIPT = "Script"
    LIBRARY = "Library"
    MODULE = "Module"
    FUNCTION = "Function"
    VARIABLE = "Variable"
    PARAMETER = "Parameter"
    CONFIG_PARAM = "ConfigParam"
    SERVICE = "Service"
    
    # Beziehungstypen
    DEPENDS_ON = "DependsOn"
    CALLS = "Calls"
    IMPORTS = "Imports"
    CONFIGURES = "Configures"
    DEFINES = "Defines"
    USES = "Uses"
    PROVIDES_SERVICE_TO = "ProvidesServiceTo"
    STARTUP_DEPENDENCY = "StartupDependency"
    RUNTIME_DEPENDENCY = "RuntimeDependency"
    CONFIGURATION_DEPENDENCY = "ConfigurationDependency"
    
    # Schnittstellentypen
    API = "API"
    CLI = "CLI"
    API_ENDPOINT = "APIEndpoint"
    CLI_COMMAND = "CLICommand"
    
    # Datenflusstypen
    DATA_FLOW_STEP = "DataFlowStep"
    
    # Migrationstypen
    MIGRATION_DECISION = "MigrationDecision"
    CODE_TRANSFORMATION = "CodeTransformation"
    PYTHON_EQUIVALENT = "PythonEquivalent"
    BASH_ORIGINAL = "BashOriginal"


class RelationshipType(str, Enum):
    """Typen für Beziehungen im Knowledge Graph."""
    
    # Basisbeziehungen
    DEPENDS_ON = "DEPENDS_ON"
    CALLS = "CALLS"
    IMPORTS = "IMPORTS"
    CONFIGURES = "CONFIGURES"
    DEFINES = "DEFINES"
    USES = "USES"
    PROVIDES_SERVICE_TO = "PROVIDES_SERVICE_TO"
    
    # Spezifische Abhängigkeiten
    STARTUP_DEPENDENCY = "STARTUP_DEPENDENCY"
    RUNTIME_DEPENDENCY = "RUNTIME_DEPENDENCY"
    CONFIGURATION_DEPENDENCY = "CONFIGURATION_DEPENDENCY"
    
    # Schnittstellenbeziehungen
    EXPOSES = "EXPOSES"
    IMPLEMENTS = "IMPLEMENTS"
    HAS_FUNCTION = "HAS_FUNCTION"
    HAS_PARAMETER = "HAS_PARAMETER"
    HAS_STEP = "HAS_STEP"
    HAS_ENDPOINT = "HAS_ENDPOINT"
    HAS_COMMAND = "HAS_COMMAND"
    
    # Datenflussbeziehungen
    SOURCE = "SOURCE"
    TARGET = "TARGET"
    
    # Migrationsbeziehungen
    MIGRATED_TO = "MIGRATED_TO"
    TRANSFORMED_FROM = "TRANSFORMED_FROM"
    EQUIVALENT_TO = "EQUIVALENT_TO"
    DECISION_FOR = "DECISION_FOR"


class SchemaManager:
    """Manager für das Schema des Knowledge Graphs."""
    
    def __init__(self, client: Optional[Neo4jClient] = None):
        """
        Initialisiert einen neuen SchemaManager.
        
        Args:
            client: Neo4j-Client-Instanz
        """
        self.client = client or get_client()
    
    def create_schema(self) -> bool:
        """
        Erstellt das Schema für den Knowledge Graph.
        
        Returns:
            bool: True, wenn das Schema erfolgreich erstellt wurde, sonst False
        """
        try:
            # Verbindung zur Datenbank herstellen
            if not self.client.ensure_connected():
                logging.error("Keine Verbindung zur Neo4j-Datenbank")
                return False
            
            # Einschränkungen erstellen
            self._create_constraints()
            
            # Indizes erstellen
            self._create_indices()
            
            logging.success("Schema erfolgreich erstellt")
            return True
        except Exception as e:
            logging.error(f"Fehler beim Erstellen des Schemas: {str(e)}")
            return False
    
    def _create_constraints(self) -> None:
        """Erstellt Einschränkungen für den Knowledge Graph."""
        # Einschränkungen für Entitäten
        self.client.run_query("""
        CREATE CONSTRAINT ON (n:Entity)
        ASSERT n.id IS UNIQUE
        """)
        
        # Einschränkungen für Komponenten
        self.client.run_query("""
        CREATE CONSTRAINT ON (n:Component)
        ASSERT n.name IS UNIQUE
        """)
        
        # Einschränkungen für Funktionen
        self.client.run_query("""
        CREATE CONSTRAINT ON (n:Function)
        ASSERT (n.name, n.filePath) IS UNIQUE
        """)
        
        # Einschränkungen für Variablen
        self.client.run_query("""
        CREATE CONSTRAINT ON (n:Variable)
        ASSERT (n.name, n.filePath) IS UNIQUE
        """)
        
        # Einschränkungen für Konfigurationsparameter
        self.client.run_query("""
        CREATE CONSTRAINT ON (n:ConfigParam)
        ASSERT n.name IS UNIQUE
        """)
        
        # Einschränkungen für Dienste
        self.client.run_query("""
        CREATE CONSTRAINT ON (n:Service)
        ASSERT n.name IS UNIQUE
        """)
        
        # Einschränkungen für APIs
        self.client.run_query("""
        CREATE CONSTRAINT ON (n:API)
        ASSERT n.name IS UNIQUE
        """)
        
        # Einschränkungen für CLIs
        self.client.run_query("""
        CREATE CONSTRAINT ON (n:CLI)
        ASSERT n.name IS UNIQUE
        """)
        
        # Einschränkungen für Migrationsentscheidungen
        self.client.run_query("""
        CREATE CONSTRAINT ON (n:MigrationDecision)
        ASSERT n.id IS UNIQUE
        """)
        
        logging.info("Einschränkungen erfolgreich erstellt")
    
    def _create_indices(self) -> None:
        """Erstellt Indizes für den Knowledge Graph."""
        # Index für Entitäten
        self.client.run_query("""
        CREATE INDEX ON :Entity(type)
        """)
        
        # Index für Komponenten
        self.client.run_query("""
        CREATE INDEX ON :Component(type)
        """)
        
        # Index für Funktionen
        self.client.run_query("""
        CREATE INDEX ON :Function(name)
        """)
        
        # Index für Funktionen nach Dateipfad
        self.client.run_query("""
        CREATE INDEX ON :Function(filePath)
        """)
        
        # Index für Variablen
        self.client.run_query("""
        CREATE INDEX ON :Variable(name)
        """)
        
        # Index für Konfigurationsparameter
        self.client.run_query("""
        CREATE INDEX ON :ConfigParam(name)
        """)
        
        # Index für Dienste
        self.client.run_query("""
        CREATE INDEX ON :Service(name)
        """)
        
        # Index für Bash-Originale
        self.client.run_query("""
        CREATE INDEX ON :BashOriginal(filePath)
        """)
        
        # Index für Python-Äquivalente
        self.client.run_query("""
        CREATE INDEX ON :PythonEquivalent(filePath)
        """)
        
        logging.info("Indizes erfolgreich erstellt")
    
    def drop_schema(self) -> bool:
        """
        Löscht das Schema für den Knowledge Graph.
        
        Returns:
            bool: True, wenn das Schema erfolgreich gelöscht wurde, sonst False
        """
        try:
            # Verbindung zur Datenbank herstellen
            if not self.client.ensure_connected():
                logging.error("Keine Verbindung zur Neo4j-Datenbank")
                return False
            
            # Einschränkungen löschen
            self.client.run_query("""
            CALL apoc.schema.assert({}, {})
            """)
            
            logging.success("Schema erfolgreich gelöscht")
            return True
        except Exception as e:
            logging.error(f"Fehler beim Löschen des Schemas: {str(e)}")
            return False
    
    def get_schema_info(self) -> Dict:
        """
        Ruft Informationen über das Schema ab.
        
        Returns:
            Dict: Informationen über das Schema
        """
        try:
            # Verbindung zur Datenbank herstellen
            if not self.client.ensure_connected():
                logging.error("Keine Verbindung zur Neo4j-Datenbank")
                return {}
            
            # Einschränkungen abrufen
            constraints_result = self.client.run_query("""
            CALL db.constraints()
            """)
            
            # Indizes abrufen
            indices_result = self.client.run_query("""
            CALL db.indexes()
            """)
            
            return {
                "constraints": constraints_result,
                "indices": indices_result
            }
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Schema-Informationen: {str(e)}")
            return {}


def create_entity_node(
    client: Optional[Neo4jClient] = None,
    entity_id: str = None,
    labels: List[str] = None,
    properties: Dict = None
) -> Optional[Dict]:
    """
    Erstellt einen Entitätsknoten im Knowledge Graph.
    
    Args:
        client: Neo4j-Client-Instanz
        entity_id: ID der Entität
        labels: Labels für den Knoten
        properties: Eigenschaften des Knotens
        
    Returns:
        Optional[Dict]: Erstellter Knoten oder None, wenn ein Fehler aufgetreten ist
    """
    if client is None:
        client = get_client()
    
    if not client.ensure_connected():
        logging.error("Keine Verbindung zur Neo4j-Datenbank")
        return None
    
    if labels is None:
        labels = [NodeLabel.ENTITY]
    elif NodeLabel.ENTITY not in labels:
        labels.append(NodeLabel.ENTITY)
    
    if properties is None:
        properties = {}
    
    if entity_id:
        properties["id"] = entity_id
    
    try:
        # Knoten erstellen
        result = client.create_node(labels, properties)
        return result
    except Exception as e:
        logging.error(f"Fehler beim Erstellen des Entitätsknotens: {str(e)}")
        return None


def create_relationship(
    client: Optional[Neo4jClient] = None,
    start_node_id: int = None,
    end_node_id: int = None,
    relationship_type: str = None,
    properties: Dict = None
) -> Optional[Dict]:
    """
    Erstellt eine Beziehung zwischen zwei Knoten im Knowledge Graph.
    
    Args:
        client: Neo4j-Client-Instanz
        start_node_id: ID des Startknotens
        end_node_id: ID des Endknotens
        relationship_type: Typ der Beziehung
        properties: Eigenschaften der Beziehung
        
    Returns:
        Optional[Dict]: Erstellte Beziehung oder None, wenn ein Fehler aufgetreten ist
    """
    if client is None:
        client = get_client()
    
    if not client.ensure_connected():
        logging.error("Keine Verbindung zur Neo4j-Datenbank")
        return None
    
    if start_node_id is None or end_node_id is None or relationship_type is None:
        logging.error("Start-Knoten-ID, End-Knoten-ID und Beziehungstyp müssen angegeben werden")
        return None
    
    if properties is None:
        properties = {}
    
    try:
        # Beziehung erstellen
        result = client.create_relationship(
            start_node_id,
            end_node_id,
            relationship_type,
            properties
        )
        return result
    except Exception as e:
        logging.error(f"Fehler beim Erstellen der Beziehung: {str(e)}")
        return None


def import_json_ld_schema(
    schema_file_path: str,
    client: Optional[Neo4jClient] = None
) -> bool:
    """
    Importiert ein JSON-LD-Schema in den Knowledge Graph.
    
    Args:
        schema_file_path: Pfad zur JSON-LD-Schema-Datei
        client: Neo4j-Client-Instanz
        
    Returns:
        bool: True, wenn das Schema erfolgreich importiert wurde, sonst False
    """
    import json
    import os
    
    if client is None:
        client = get_client()
    
    if not client.ensure_connected():
        logging.error("Keine Verbindung zur Neo4j-Datenbank")
        return False
    
    if not os.path.isfile(schema_file_path):
        logging.error(f"Schema-Datei nicht gefunden: {schema_file_path}")
        return False
    
    try:
        # Schema-Datei laden
        with open(schema_file_path, "r") as f:
            schema = json.load(f)
        
        # Entitätstypen importieren
        if "entityTypes" in schema:
            for entity_type in schema["entityTypes"]:
                labels = [NodeLabel.ENTITY]
                if "@type" in entity_type and entity_type["@type"] == "rdfs:Class":
                    labels.append(entity_type["name"])
                
                properties = {
                    "id": entity_type["@id"],
                    "name": entity_type["name"],
                    "description": entity_type.get("description", "")
                }
                
                if "subClassOf" in entity_type:
                    properties["subClassOf"] = entity_type["subClassOf"]
                
                create_entity_node(client, entity_type["@id"], labels, properties)
        
        # Beziehungstypen importieren
        if "relationshipTypes" in schema:
            for relationship_type in schema["relationshipTypes"]:
                labels = [NodeLabel.RELATIONSHIP]
                if "@type" in relationship_type and relationship_type["@type"] == "rdfs:Class":
                    labels.append(relationship_type["name"])
                
                properties = {
                    "id": relationship_type["@id"],
                    "name": relationship_type["name"],
                    "description": relationship_type.get("description", "")
                }
                
                if "subClassOf" in relationship_type:
                    properties["subClassOf"] = relationship_type["subClassOf"]
                
                create_entity_node(client, relationship_type["@id"], labels, properties)
        
        # Schnittstellentypen importieren
        if "interfaceTypes" in schema:
            for interface_type in schema["interfaceTypes"]:
                labels = [NodeLabel.INTERFACE]
                if "@type" in interface_type and interface_type["@type"] == "rdfs:Class":
                    labels.append(interface_type["name"])
                
                properties = {
                    "id": interface_type["@id"],
                    "name": interface_type["name"],
                    "description": interface_type.get("description", "")
                }
                
                if "subClassOf" in interface_type:
                    properties["subClassOf"] = interface_type["subClassOf"]
                
                create_entity_node(client, interface_type["@id"], labels, properties)
        
        # Datenflusstypen importieren
        if "dataFlowTypes" in schema:
            for data_flow_type in schema["dataFlowTypes"]:
                labels = [NodeLabel.DATA_FLOW]
                if "@type" in data_flow_type and data_flow_type["@type"] == "rdfs:Class":
                    labels.append(data_flow_type["name"])
                
                properties = {
                    "id": data_flow_type["@id"],
                    "name": data_flow_type["name"],
                    "description": data_flow_type.get("description", "")
                }
                
                if "subClassOf" in data_flow_type:
                    properties["subClassOf"] = data_flow_type["subClassOf"]
                
                create_entity_node(client, data_flow_type["@id"], labels, properties)
        
        logging.success(f"Schema erfolgreich aus {schema_file_path} importiert")
        return True
    except Exception as e:
        logging.error(f"Fehler beim Importieren des Schemas: {str(e)}")
        return False


def import_json_ld_graph(
    graph_file_path: str,
    client: Optional[Neo4jClient] = None
) -> bool:
    """
    Importiert einen JSON-LD-Graphen in den Knowledge Graph.
    
    Args:
        graph_file_path: Pfad zur JSON-LD-Graphen-Datei
        client: Neo4j-Client-Instanz
        
    Returns:
        bool: True, wenn der Graph erfolgreich importiert wurde, sonst False
    """
    import json
    import os
    
    if client is None:
        client = get_client()
    
    if not client.ensure_connected():
        logging.error("Keine Verbindung zur Neo4j-Datenbank")
        return False
    
    if not os.path.isfile(graph_file_path):
        logging.error(f"Graphen-Datei nicht gefunden: {graph_file_path}")
        return False
    
    try:
        # Graphen-Datei laden
        with open(graph_file_path, "r") as f:
            graph_data = json.load(f)
        
        # Knoten-ID-Zuordnung für Beziehungen
        node_id_map = {}
        
        # Graphen importieren
        if "@graph" in graph_data:
            # Zuerst alle Knoten erstellen
            for node in graph_data["@graph"]:
                if "@id" in node:
                    # Typ des Knotens bestimmen
                    node_type = node.get("@type", "Entity")
                    labels = [node_type]
                    
                    # Eigenschaften extrahieren
                    properties = {k: v for k, v in node.items() if not k.startswith("@") and not isinstance(v, dict)}
                    
                    # Knoten erstellen
                    created_node = create_entity_node(client, node["@id"], labels, properties)
                    
                    if created_node:
                        # ID-Zuordnung speichern
                        node_id_map[node["@id"]] = created_node["id"]
            
            # Dann alle Beziehungen erstellen
            for node in graph_data["@graph"]:
                if "@id" in node:
                    start_node_id = node_id_map.get(node["@id"])
                    
                    if start_node_id:
                        # Beziehungen extrahieren
                        for key, value in node.items():
                            if isinstance(value, dict) and "@id" in value:
                                end_node_id = node_id_map.get(value["@id"])
                                
                                if end_node_id:
                                    # Beziehung erstellen
                                    create_relationship(
                                        client,
                                        start_node_id,
                                        end_node_id,
                                        key.upper()
                                    )
        
        logging.success(f"Graph erfolgreich aus {graph_file_path} importiert")
        return True
    except Exception as e:
        logging.error(f"Fehler beim Importieren des Graphen: {str(e)}")
        return False


def init_knowledge_graph(
    schema_file_path: Optional[str] = None,
    graph_file_path: Optional[str] = None,
    client: Optional[Neo4jClient] = None
) -> bool:
    """
    Initialisiert den Knowledge Graph mit Schema und Daten.
    
    Args:
        schema_file_path: Pfad zur JSON-LD-Schema-Datei
        graph_file_path: Pfad zur JSON-LD-Graphen-Datei
        client: Neo4j-Client-Instanz
        
    Returns:
        bool: True, wenn der Knowledge Graph erfolgreich initialisiert wurde, sonst False
    """
    if client is None:
        client = get_client()
    
    if not client.ensure_connected():
        logging.error("Keine Verbindung zur Neo4j-Datenbank")
        return False
    
    # Schema erstellen
    schema_manager = SchemaManager(client)
    if not schema_manager.create_schema():
        logging.error("Fehler beim Erstellen des Schemas")
        return False
    
    # Schema importieren, wenn angegeben
    if schema_file_path:
        if not import_json_ld_schema(schema_file_path, client):
            logging.error(f"Fehler beim Importieren des Schemas aus {schema_file_path}")
            return False
    
    # Graphen importieren, wenn angegeben
    if graph_file_path:
        if not import_json_ld_graph(graph_file_path, client):
            logging.error(f"Fehler beim Importieren des Graphen aus {graph_file_path}")
            return False
    
    logging.success("Knowledge Graph erfolgreich initialisiert")
    return True


logging.debug("Knowledge-Graph-Schema-Modul initialisiert")