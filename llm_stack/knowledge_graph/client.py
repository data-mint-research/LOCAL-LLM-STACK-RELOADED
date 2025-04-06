"""
Neo4j-Client für den LLM Stack Knowledge Graph.

Dieses Modul stellt Funktionen zur Verbindung mit einer Neo4j-Datenbank bereit
und bietet grundlegende Operationen für den Knowledge Graph.
"""

import os
from typing import Any, Dict, List, Optional, Tuple, Union

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from llm_stack.core import error, logging


class Neo4jClient:
    """Client für die Interaktion mit der Neo4j-Datenbank."""
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "password",
        database: str = "neo4j"
    ):
        """
        Initialisiert einen neuen Neo4j-Client.
        
        Args:
            uri: URI der Neo4j-Datenbank
            username: Benutzername für die Authentifizierung
            password: Passwort für die Authentifizierung
            database: Name der zu verwendenden Datenbank
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        Stellt eine Verbindung zur Neo4j-Datenbank her.
        
        Returns:
            bool: True, wenn die Verbindung erfolgreich hergestellt wurde, sonst False
        """
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            
            # Verbindung testen
            self.driver.verify_connectivity()
            
            self.connected = True
            logging.success(f"Verbindung zur Neo4j-Datenbank hergestellt: {self.uri}")
            return True
        except ServiceUnavailable as e:
            logging.error(f"Neo4j-Datenbank nicht erreichbar: {str(e)}")
            self.connected = False
            return False
        except Exception as e:
            logging.error(f"Fehler beim Verbinden mit der Neo4j-Datenbank: {str(e)}")
            self.connected = False
            return False
    
    def close(self) -> None:
        """Schließt die Verbindung zur Neo4j-Datenbank."""
        if self.driver:
            self.driver.close()
            self.connected = False
            logging.info("Verbindung zur Neo4j-Datenbank geschlossen")
    
    def ensure_connected(self) -> bool:
        """
        Stellt sicher, dass eine Verbindung zur Neo4j-Datenbank besteht.
        
        Returns:
            bool: True, wenn eine Verbindung besteht, sonst False
        """
        if not self.connected or not self.driver:
            return self.connect()
        return True
    
    def run_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Führt eine Cypher-Abfrage aus.
        
        Args:
            query: Cypher-Abfrage
            parameters: Parameter für die Abfrage
            database: Name der zu verwendenden Datenbank (überschreibt den Standardwert)
            
        Returns:
            List[Dict[str, Any]]: Ergebnisse der Abfrage
        
        Raises:
            error.DatabaseError: Wenn ein Fehler bei der Ausführung der Abfrage auftritt
        """
        if not self.ensure_connected():
            raise error.DatabaseError("Keine Verbindung zur Neo4j-Datenbank")
        
        if parameters is None:
            parameters = {}
        
        db = database or self.database
        
        try:
            with self.driver.session(database=db) as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
        except Neo4jError as e:
            logging.error(f"Neo4j-Fehler bei der Ausführung der Abfrage: {str(e)}")
            raise error.DatabaseError(f"Neo4j-Fehler: {str(e)}")
        except Exception as e:
            logging.error(f"Fehler bei der Ausführung der Abfrage: {str(e)}")
            raise error.DatabaseError(f"Fehler: {str(e)}")
    
    def create_node(
        self,
        labels: Union[str, List[str]],
        properties: Dict[str, Any],
        database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Erstellt einen Knoten im Knowledge Graph.
        
        Args:
            labels: Label oder Liste von Labels für den Knoten
            properties: Eigenschaften des Knotens
            database: Name der zu verwendenden Datenbank (überschreibt den Standardwert)
            
        Returns:
            Optional[Dict[str, Any]]: Erstellter Knoten oder None, wenn ein Fehler aufgetreten ist
        """
        if isinstance(labels, str):
            labels = [labels]
        
        labels_str = ":".join(labels)
        
        query = f"""
        CREATE (n:{labels_str} $properties)
        RETURN n
        """
        
        try:
            result = self.run_query(query, {"properties": properties}, database)
            if result and len(result) > 0:
                return result[0].get("n")
            return None
        except Exception as e:
            logging.error(f"Fehler beim Erstellen des Knotens: {str(e)}")
            return None
    
    def create_relationship(
        self,
        start_node_id: int,
        end_node_id: int,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Erstellt eine Beziehung zwischen zwei Knoten im Knowledge Graph.
        
        Args:
            start_node_id: ID des Startknotens
            end_node_id: ID des Endknotens
            relationship_type: Typ der Beziehung
            properties: Eigenschaften der Beziehung
            database: Name der zu verwendenden Datenbank (überschreibt den Standardwert)
            
        Returns:
            Optional[Dict[str, Any]]: Erstellte Beziehung oder None, wenn ein Fehler aufgetreten ist
        """
        if properties is None:
            properties = {}
        
        query = f"""
        MATCH (a), (b)
        WHERE ID(a) = $start_id AND ID(b) = $end_id
        CREATE (a)-[r:{relationship_type} $properties]->(b)
        RETURN r
        """
        
        try:
            result = self.run_query(
                query,
                {
                    "start_id": start_node_id,
                    "end_id": end_node_id,
                    "properties": properties
                },
                database
            )
            if result and len(result) > 0:
                return result[0].get("r")
            return None
        except Exception as e:
            logging.error(f"Fehler beim Erstellen der Beziehung: {str(e)}")
            return None
    
    def get_node_by_id(
        self,
        node_id: int,
        database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Ruft einen Knoten anhand seiner ID ab.
        
        Args:
            node_id: ID des Knotens
            database: Name der zu verwendenden Datenbank (überschreibt den Standardwert)
            
        Returns:
            Optional[Dict[str, Any]]: Knoten oder None, wenn der Knoten nicht gefunden wurde
        """
        query = """
        MATCH (n)
        WHERE ID(n) = $node_id
        RETURN n
        """
        
        try:
            result = self.run_query(query, {"node_id": node_id}, database)
            if result and len(result) > 0:
                return result[0].get("n")
            return None
        except Exception as e:
            logging.error(f"Fehler beim Abrufen des Knotens: {str(e)}")
            return None
    
    def get_nodes_by_label(
        self,
        label: str,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Ruft Knoten anhand ihres Labels ab.
        
        Args:
            label: Label der Knoten
            database: Name der zu verwendenden Datenbank (überschreibt den Standardwert)
            
        Returns:
            List[Dict[str, Any]]: Liste von Knoten
        """
        query = f"""
        MATCH (n:{label})
        RETURN n
        """
        
        try:
            result = self.run_query(query, {}, database)
            return [record.get("n") for record in result]
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Knoten: {str(e)}")
            return []
    
    def get_nodes_by_property(
        self,
        property_name: str,
        property_value: Any,
        label: Optional[str] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Ruft Knoten anhand einer Eigenschaft ab.
        
        Args:
            property_name: Name der Eigenschaft
            property_value: Wert der Eigenschaft
            label: Optionales Label zur Einschränkung der Suche
            database: Name der zu verwendenden Datenbank (überschreibt den Standardwert)
            
        Returns:
            List[Dict[str, Any]]: Liste von Knoten
        """
        label_clause = f":{label}" if label else ""
        
        query = f"""
        MATCH (n{label_clause})
        WHERE n.{property_name} = $property_value
        RETURN n
        """
        
        try:
            result = self.run_query(query, {"property_value": property_value}, database)
            return [record.get("n") for record in result]
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Knoten: {str(e)}")
            return []
    
    def update_node(
        self,
        node_id: int,
        properties: Dict[str, Any],
        database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Aktualisiert die Eigenschaften eines Knotens.
        
        Args:
            node_id: ID des Knotens
            properties: Neue Eigenschaften des Knotens
            database: Name der zu verwendenden Datenbank (überschreibt den Standardwert)
            
        Returns:
            Optional[Dict[str, Any]]: Aktualisierter Knoten oder None, wenn ein Fehler aufgetreten ist
        """
        query = """
        MATCH (n)
        WHERE ID(n) = $node_id
        SET n += $properties
        RETURN n
        """
        
        try:
            result = self.run_query(
                query,
                {
                    "node_id": node_id,
                    "properties": properties
                },
                database
            )
            if result and len(result) > 0:
                return result[0].get("n")
            return None
        except Exception as e:
            logging.error(f"Fehler beim Aktualisieren des Knotens: {str(e)}")
            return None
    
    def delete_node(
        self,
        node_id: int,
        database: Optional[str] = None
    ) -> bool:
        """
        Löscht einen Knoten.
        
        Args:
            node_id: ID des Knotens
            database: Name der zu verwendenden Datenbank (überschreibt den Standardwert)
            
        Returns:
            bool: True, wenn der Knoten erfolgreich gelöscht wurde, sonst False
        """
        query = """
        MATCH (n)
        WHERE ID(n) = $node_id
        DETACH DELETE n
        """
        
        try:
            self.run_query(query, {"node_id": node_id}, database)
            return True
        except Exception as e:
            logging.error(f"Fehler beim Löschen des Knotens: {str(e)}")
            return False
    
    def delete_relationship(
        self,
        relationship_id: int,
        database: Optional[str] = None
    ) -> bool:
        """
        Löscht eine Beziehung.
        
        Args:
            relationship_id: ID der Beziehung
            database: Name der zu verwendenden Datenbank (überschreibt den Standardwert)
            
        Returns:
            bool: True, wenn die Beziehung erfolgreich gelöscht wurde, sonst False
        """
        query = """
        MATCH ()-[r]->()
        WHERE ID(r) = $relationship_id
        DELETE r
        """
        
        try:
            self.run_query(query, {"relationship_id": relationship_id}, database)
            return True
        except Exception as e:
            logging.error(f"Fehler beim Löschen der Beziehung: {str(e)}")
            return False
    
    def clear_database(self, database: Optional[str] = None) -> bool:
        """
        Löscht alle Knoten und Beziehungen in der Datenbank.
        
        Args:
            database: Name der zu verwendenden Datenbank (überschreibt den Standardwert)
            
        Returns:
            bool: True, wenn die Datenbank erfolgreich geleert wurde, sonst False
        """
        query = """
        MATCH (n)
        DETACH DELETE n
        """
        
        try:
            self.run_query(query, {}, database)
            logging.success("Datenbank erfolgreich geleert")
            return True
        except Exception as e:
            logging.error(f"Fehler beim Leeren der Datenbank: {str(e)}")
            return False
    
    def create_index(
        self,
        label: str,
        property_name: str,
        database: Optional[str] = None
    ) -> bool:
        """
        Erstellt einen Index für eine Eigenschaft eines Labels.
        
        Args:
            label: Label, für das der Index erstellt werden soll
            property_name: Name der Eigenschaft, für die der Index erstellt werden soll
            database: Name der zu verwendenden Datenbank (überschreibt den Standardwert)
            
        Returns:
            bool: True, wenn der Index erfolgreich erstellt wurde, sonst False
        """
        query = f"""
        CREATE INDEX ON :{label}({property_name})
        """
        
        try:
            self.run_query(query, {}, database)
            logging.success(f"Index für {label}.{property_name} erfolgreich erstellt")
            return True
        except Exception as e:
            logging.error(f"Fehler beim Erstellen des Index: {str(e)}")
            return False
    
    def create_constraint(
        self,
        label: str,
        property_name: str,
        constraint_type: str = "UNIQUE",
        database: Optional[str] = None
    ) -> bool:
        """
        Erstellt eine Einschränkung für eine Eigenschaft eines Labels.
        
        Args:
            label: Label, für das die Einschränkung erstellt werden soll
            property_name: Name der Eigenschaft, für die die Einschränkung erstellt werden soll
            constraint_type: Typ der Einschränkung (UNIQUE, EXISTS, etc.)
            database: Name der zu verwendenden Datenbank (überschreibt den Standardwert)
            
        Returns:
            bool: True, wenn die Einschränkung erfolgreich erstellt wurde, sonst False
        """
        query = f"""
        CREATE CONSTRAINT ON (n:{label}) ASSERT n.{property_name} IS {constraint_type}
        """
        
        try:
            self.run_query(query, {}, database)
            logging.success(f"Einschränkung für {label}.{property_name} erfolgreich erstellt")
            return True
        except Exception as e:
            logging.error(f"Fehler beim Erstellen der Einschränkung: {str(e)}")
            return False
    
    def get_shortest_path(
        self,
        start_node_id: int,
        end_node_id: int,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 10,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Findet den kürzesten Pfad zwischen zwei Knoten.
        
        Args:
            start_node_id: ID des Startknotens
            end_node_id: ID des Endknotens
            relationship_types: Liste von Beziehungstypen, die berücksichtigt werden sollen
            max_depth: Maximale Tiefe des Pfads
            database: Name der zu verwendenden Datenbank (überschreibt den Standardwert)
            
        Returns:
            List[Dict[str, Any]]: Liste von Knoten und Beziehungen im Pfad
        """
        rel_types = ""
        if relationship_types:
            rel_types = "|".join([f":{rel_type}" for rel_type in relationship_types])
            rel_types = f"[{rel_types}]"
        
        query = f"""
        MATCH path = shortestPath((a)-[{rel_types}*1..{max_depth}]->(b))
        WHERE ID(a) = $start_id AND ID(b) = $end_id
        RETURN path
        """
        
        try:
            result = self.run_query(
                query,
                {
                    "start_id": start_node_id,
                    "end_id": end_node_id
                },
                database
            )
            if result and len(result) > 0:
                return result[0].get("path")
            return []
        except Exception as e:
            logging.error(f"Fehler beim Finden des kürzesten Pfads: {str(e)}")
            return []
    
    def get_connected_nodes(
        self,
        node_id: int,
        relationship_type: Optional[str] = None,
        direction: str = "OUTGOING",
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Ruft Knoten ab, die mit einem bestimmten Knoten verbunden sind.
        
        Args:
            node_id: ID des Knotens
            relationship_type: Typ der Beziehung
            direction: Richtung der Beziehung (OUTGOING, INCOMING, BOTH)
            database: Name der zu verwendenden Datenbank (überschreibt den Standardwert)
            
        Returns:
            List[Dict[str, Any]]: Liste von verbundenen Knoten
        """
        rel_type = f":{relationship_type}" if relationship_type else ""
        
        if direction == "OUTGOING":
            query = f"""
            MATCH (a)-[r{rel_type}]->(b)
            WHERE ID(a) = $node_id
            RETURN b
            """
        elif direction == "INCOMING":
            query = f"""
            MATCH (a)<-[r{rel_type}]-(b)
            WHERE ID(a) = $node_id
            RETURN b
            """
        else:  # BOTH
            query = f"""
            MATCH (a)-[r{rel_type}]-(b)
            WHERE ID(a) = $node_id
            RETURN b
            """
        
        try:
            result = self.run_query(query, {"node_id": node_id}, database)
            return [record.get("b") for record in result]
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der verbundenen Knoten: {str(e)}")
            return []
    
    def execute_batch(
        self,
        queries: List[Tuple[str, Dict[str, Any]]],
        database: Optional[str] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Führt mehrere Abfragen als Batch aus.
        
        Args:
            queries: Liste von Tupeln (Abfrage, Parameter)
            database: Name der zu verwendenden Datenbank (überschreibt den Standardwert)
            
        Returns:
            List[List[Dict[str, Any]]]: Liste von Ergebnissen für jede Abfrage
        """
        if not self.ensure_connected():
            raise error.DatabaseError("Keine Verbindung zur Neo4j-Datenbank")
        
        db = database or self.database
        results = []
        
        try:
            with self.driver.session(database=db) as session:
                with session.begin_transaction() as tx:
                    for query, parameters in queries:
                        result = tx.run(query, parameters)
                        results.append([record.data() for record in result])
            return results
        except Neo4jError as e:
            logging.error(f"Neo4j-Fehler bei der Ausführung des Batches: {str(e)}")
            raise error.DatabaseError(f"Neo4j-Fehler: {str(e)}")
        except Exception as e:
            logging.error(f"Fehler bei der Ausführung des Batches: {str(e)}")
            raise error.DatabaseError(f"Fehler: {str(e)}")


# Singleton-Instanz des Neo4j-Clients
_client = None


def get_client() -> Neo4jClient:
    """
    Ruft die Singleton-Instanz des Neo4j-Clients ab.
    
    Returns:
        Neo4jClient: Neo4j-Client-Instanz
    """
    global _client
    
    if _client is None:
        # Konfiguration aus Umgebungsvariablen laden
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        username = os.environ.get("NEO4J_USERNAME", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "password")
        database = os.environ.get("NEO4J_DATABASE", "neo4j")
        
        _client = Neo4jClient(uri, username, password, database)
    
    return _client


def init_client(
    uri: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    database: Optional[str] = None
) -> Neo4jClient:
    """
    Initialisiert die Singleton-Instanz des Neo4j-Clients mit benutzerdefinierten Parametern.
    
    Args:
        uri: URI der Neo4j-Datenbank
        username: Benutzername für die Authentifizierung
        password: Passwort für die Authentifizierung
        database: Name der zu verwendenden Datenbank
        
    Returns:
        Neo4jClient: Neo4j-Client-Instanz
    """
    global _client
    
    # Konfiguration aus Umgebungsvariablen laden, wenn nicht angegeben
    if uri is None:
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    if username is None:
        username = os.environ.get("NEO4J_USERNAME", "neo4j")
    if password is None:
        password = os.environ.get("NEO4J_PASSWORD", "password")
    if database is None:
        database = os.environ.get("NEO4J_DATABASE", "neo4j")
    
    _client = Neo4jClient(uri, username, password, database)
    return _client


def close_client() -> None:
    """Schließt die Verbindung des Neo4j-Clients."""
    global _client
    
    if _client:
        _client.close()
        _client = None


logging.debug("Neo4j-Client-Modul initialisiert")