"""
Migrationsfunktionen für den LLM Stack Knowledge Graph.

Dieses Modul stellt Funktionen für die Verfolgung und Verwaltung von
Migrationsentscheidungen im Knowledge Graph bereit.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union

from llm_stack.core import error, logging
from llm_stack.knowledge_graph.client import Neo4jClient, get_client
from llm_stack.knowledge_graph.models import (BashOriginal, CodeTransformation,
                                              EntityType, MigrationDecision,
                                              PythonEquivalent)
from llm_stack.knowledge_graph.schema import NodeLabel, RelationshipType


def record_migration_decision(
    decision: str,
    rationale: str,
    bash_file_path: Optional[str] = None,
    python_file_path: Optional[str] = None,
    alternatives: Optional[List[str]] = None,
    impact: Optional[str] = None,
    client: Optional[Neo4jClient] = None
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
        client: Neo4j-Client-Instanz
        
    Returns:
        Optional[Dict]: Erstellter Entscheidungsknoten oder None, wenn ein Fehler aufgetreten ist
    """
    if client is None:
        client = get_client()
    
    if not client.ensure_connected():
        logging.error("Keine Verbindung zur Neo4j-Datenbank")
        return None
    
    try:
        # Entscheidungs-ID generieren
        decision_id = f"decision:{uuid.uuid4()}"
        
        # Entscheidungsknoten erstellen
        decision_node = MigrationDecision(
            id=decision_id,
            name=f"Migration Decision: {decision[:30]}...",
            description=rationale,
            decision=decision,
            rationale=rationale,
            alternatives=alternatives,
            impact=impact,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Knoten erstellen
        result = client.create_node(
            decision_node.get_labels(),
            decision_node.to_neo4j_properties()
        )
        
        if not result:
            logging.error("Fehler beim Erstellen des Entscheidungsknotens")
            return None
        
        decision_node_id = result["id"]
        
        # Beziehungen zu Bash- und Python-Dateien erstellen, wenn angegeben
        if bash_file_path:
            # Bash-Datei suchen oder erstellen
            bash_nodes = client.run_query(
                """
                MATCH (n:BashOriginal)
                WHERE n.file_path = $file_path
                RETURN n
                """,
                {"file_path": bash_file_path}
            )
            
            bash_node_id = None
            if bash_nodes and len(bash_nodes) > 0:
                bash_node_id = bash_nodes[0]["n"]["id"]
            
            if bash_node_id:
                # Beziehung erstellen
                client.create_relationship(
                    decision_node_id,
                    bash_node_id,
                    RelationshipType.DECISION_FOR
                )
        
        if python_file_path:
            # Python-Datei suchen oder erstellen
            python_nodes = client.run_query(
                """
                MATCH (n:PythonEquivalent)
                WHERE n.file_path = $file_path
                RETURN n
                """,
                {"file_path": python_file_path}
            )
            
            python_node_id = None
            if python_nodes and len(python_nodes) > 0:
                python_node_id = python_nodes[0]["n"]["id"]
            
            if python_node_id:
                # Beziehung erstellen
                client.create_relationship(
                    decision_node_id,
                    python_node_id,
                    RelationshipType.DECISION_FOR
                )
        
        logging.success(f"Migrationsentscheidung erfolgreich aufgezeichnet: {decision_id}")
        return result
    except Exception as e:
        logging.error(f"Fehler beim Aufzeichnen der Migrationsentscheidung: {str(e)}")
        return None


def record_code_transformation(
    transformation_type: str,
    before: str,
    after: str,
    bash_file_path: Optional[str] = None,
    python_file_path: Optional[str] = None,
    decision_id: Optional[str] = None,
    client: Optional[Neo4jClient] = None
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
        client: Neo4j-Client-Instanz
        
    Returns:
        Optional[Dict]: Erstellter Transformationsknoten oder None, wenn ein Fehler aufgetreten ist
    """
    if client is None:
        client = get_client()
    
    if not client.ensure_connected():
        logging.error("Keine Verbindung zur Neo4j-Datenbank")
        return None
    
    try:
        # Transformations-ID generieren
        transformation_id = f"transformation:{uuid.uuid4()}"
        
        # Transformationsknoten erstellen
        transformation_node = CodeTransformation(
            id=transformation_id,
            name=f"Code Transformation: {transformation_type}",
            description=f"Transformation from Bash to Python: {transformation_type}",
            transformation_type=transformation_type,
            before=before,
            after=after,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Knoten erstellen
        result = client.create_node(
            transformation_node.get_labels(),
            transformation_node.to_neo4j_properties()
        )
        
        if not result:
            logging.error("Fehler beim Erstellen des Transformationsknotens")
            return None
        
        transformation_node_id = result["id"]
        
        # Beziehungen zu Bash- und Python-Dateien erstellen, wenn angegeben
        if bash_file_path:
            # Bash-Datei suchen oder erstellen
            bash_nodes = client.run_query(
                """
                MATCH (n:BashOriginal)
                WHERE n.file_path = $file_path
                RETURN n
                """,
                {"file_path": bash_file_path}
            )
            
            bash_node_id = None
            if bash_nodes and len(bash_nodes) > 0:
                bash_node_id = bash_nodes[0]["n"]["id"]
            
            if bash_node_id:
                # Beziehung erstellen
                client.create_relationship(
                    transformation_node_id,
                    bash_node_id,
                    RelationshipType.TRANSFORMED_FROM
                )
        
        if python_file_path:
            # Python-Datei suchen oder erstellen
            python_nodes = client.run_query(
                """
                MATCH (n:PythonEquivalent)
                WHERE n.file_path = $file_path
                RETURN n
                """,
                {"file_path": python_file_path}
            )
            
            python_node_id = None
            if python_nodes and len(python_nodes) > 0:
                python_node_id = python_nodes[0]["n"]["id"]
            
            if python_node_id:
                # Beziehung erstellen
                client.create_relationship(
                    transformation_node_id,
                    python_node_id,
                    RelationshipType.MIGRATED_TO
                )
        
        # Beziehung zur Entscheidung erstellen, wenn angegeben
        if decision_id:
            # Entscheidung suchen
            decision_nodes = client.run_query(
                """
                MATCH (n:MigrationDecision)
                WHERE n.id = $decision_id
                RETURN n
                """,
                {"decision_id": decision_id}
            )
            
            if decision_nodes and len(decision_nodes) > 0:
                decision_node_id = decision_nodes[0]["n"]["id"]
                
                # Beziehung erstellen
                client.create_relationship(
                    transformation_node_id,
                    decision_node_id,
                    RelationshipType.DECISION_FOR
                )
        
        logging.success(f"Code-Transformation erfolgreich aufgezeichnet: {transformation_id}")
        return result
    except Exception as e:
        logging.error(f"Fehler beim Aufzeichnen der Code-Transformation: {str(e)}")
        return None


def record_bash_file(
    file_path: str,
    content: str,
    client: Optional[Neo4jClient] = None
) -> Optional[Dict]:
    """
    Zeichnet eine Bash-Datei im Knowledge Graph auf.
    
    Args:
        file_path: Pfad zur Bash-Datei
        content: Inhalt der Bash-Datei
        client: Neo4j-Client-Instanz
        
    Returns:
        Optional[Dict]: Erstellter Dateiknoten oder None, wenn ein Fehler aufgetreten ist
    """
    if client is None:
        client = get_client()
    
    if not client.ensure_connected():
        logging.error("Keine Verbindung zur Neo4j-Datenbank")
        return None
    
    try:
        # Prüfen, ob die Datei bereits existiert
        existing_nodes = client.run_query(
            """
            MATCH (n:BashOriginal)
            WHERE n.file_path = $file_path
            RETURN n
            """,
            {"file_path": file_path}
        )
        
        if existing_nodes and len(existing_nodes) > 0:
            # Datei aktualisieren
            node_id = existing_nodes[0]["n"]["id"]
            result = client.update_node(
                node_id,
                {
                    "content": content,
                    "updated_at": datetime.now().isoformat()
                }
            )
            
            logging.success(f"Bash-Datei erfolgreich aktualisiert: {file_path}")
            return result
        
        # Datei-ID generieren
        file_id = f"bash:{uuid.uuid4()}"
        
        # Dateiknoten erstellen
        file_node = BashOriginal(
            id=file_id,
            name=f"Bash File: {file_path}",
            description=f"Original Bash file: {file_path}",
            file_path=file_path,
            content=content,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Knoten erstellen
        result = client.create_node(
            file_node.get_labels(),
            file_node.to_neo4j_properties()
        )
        
        logging.success(f"Bash-Datei erfolgreich aufgezeichnet: {file_path}")
        return result
    except Exception as e:
        logging.error(f"Fehler beim Aufzeichnen der Bash-Datei: {str(e)}")
        return None


def record_python_file(
    file_path: str,
    content: str,
    bash_file_path: Optional[str] = None,
    client: Optional[Neo4jClient] = None
) -> Optional[Dict]:
    """
    Zeichnet eine Python-Datei im Knowledge Graph auf.
    
    Args:
        file_path: Pfad zur Python-Datei
        content: Inhalt der Python-Datei
        bash_file_path: Pfad zur entsprechenden Bash-Datei
        client: Neo4j-Client-Instanz
        
    Returns:
        Optional[Dict]: Erstellter Dateiknoten oder None, wenn ein Fehler aufgetreten ist
    """
    if client is None:
        client = get_client()
    
    if not client.ensure_connected():
        logging.error("Keine Verbindung zur Neo4j-Datenbank")
        return None
    
    try:
        # Prüfen, ob die Datei bereits existiert
        existing_nodes = client.run_query(
            """
            MATCH (n:PythonEquivalent)
            WHERE n.file_path = $file_path
            RETURN n
            """,
            {"file_path": file_path}
        )
        
        if existing_nodes and len(existing_nodes) > 0:
            # Datei aktualisieren
            node_id = existing_nodes[0]["n"]["id"]
            result = client.update_node(
                node_id,
                {
                    "content": content,
                    "updated_at": datetime.now().isoformat()
                }
            )
            
            logging.success(f"Python-Datei erfolgreich aktualisiert: {file_path}")
            return result
        
        # Datei-ID generieren
        file_id = f"python:{uuid.uuid4()}"
        
        # Dateiknoten erstellen
        file_node = PythonEquivalent(
            id=file_id,
            name=f"Python File: {file_path}",
            description=f"Python equivalent file: {file_path}",
            file_path=file_path,
            content=content,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Knoten erstellen
        result = client.create_node(
            file_node.get_labels(),
            file_node.to_neo4j_properties()
        )
        
        if not result:
            logging.error("Fehler beim Erstellen des Python-Dateiknotens")
            return None
        
        python_node_id = result["id"]
        
        # Beziehung zur Bash-Datei erstellen, wenn angegeben
        if bash_file_path:
            # Bash-Datei suchen
            bash_nodes = client.run_query(
                """
                MATCH (n:BashOriginal)
                WHERE n.file_path = $file_path
                RETURN n
                """,
                {"file_path": bash_file_path}
            )
            
            if bash_nodes and len(bash_nodes) > 0:
                bash_node_id = bash_nodes[0]["n"]["id"]
                
                # Beziehung erstellen
                client.create_relationship(
                    python_node_id,
                    bash_node_id,
                    RelationshipType.EQUIVALENT_TO
                )
        
        logging.success(f"Python-Datei erfolgreich aufgezeichnet: {file_path}")
        return result
    except Exception as e:
        logging.error(f"Fehler beim Aufzeichnen der Python-Datei: {str(e)}")
        return None


def get_migration_decisions(
    bash_file_path: Optional[str] = None,
    python_file_path: Optional[str] = None,
    client: Optional[Neo4jClient] = None
) -> List[Dict]:
    """
    Ruft Migrationsentscheidungen aus dem Knowledge Graph ab.
    
    Args:
        bash_file_path: Pfad zur Bash-Datei, für die Entscheidungen abgerufen werden sollen
        python_file_path: Pfad zur Python-Datei, für die Entscheidungen abgerufen werden sollen
        client: Neo4j-Client-Instanz
        
    Returns:
        List[Dict]: Liste von Migrationsentscheidungen
    """
    if client is None:
        client = get_client()
    
    if not client.ensure_connected():
        logging.error("Keine Verbindung zur Neo4j-Datenbank")
        return []
    
    try:
        if bash_file_path:
            # Entscheidungen für eine Bash-Datei abrufen
            result = client.run_query(
                """
                MATCH (d:MigrationDecision)-[:DECISION_FOR]->(b:BashOriginal)
                WHERE b.file_path = $file_path
                RETURN d
                """,
                {"file_path": bash_file_path}
            )
            
            return [record["d"] for record in result]
        elif python_file_path:
            # Entscheidungen für eine Python-Datei abrufen
            result = client.run_query(
                """
                MATCH (d:MigrationDecision)-[:DECISION_FOR]->(p:PythonEquivalent)
                WHERE p.file_path = $file_path
                RETURN d
                """,
                {"file_path": python_file_path}
            )
            
            return [record["d"] for record in result]
        else:
            # Alle Entscheidungen abrufen
            result = client.run_query(
                """
                MATCH (d:MigrationDecision)
                RETURN d
                """
            )
            
            return [record["d"] for record in result]
    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Migrationsentscheidungen: {str(e)}")
        return []


def get_code_transformations(
    bash_file_path: Optional[str] = None,
    python_file_path: Optional[str] = None,
    transformation_type: Optional[str] = None,
    client: Optional[Neo4jClient] = None
) -> List[Dict]:
    """
    Ruft Code-Transformationen aus dem Knowledge Graph ab.
    
    Args:
        bash_file_path: Pfad zur Bash-Datei, für die Transformationen abgerufen werden sollen
        python_file_path: Pfad zur Python-Datei, für die Transformationen abgerufen werden sollen
        transformation_type: Typ der Transformation
        client: Neo4j-Client-Instanz
        
    Returns:
        List[Dict]: Liste von Code-Transformationen
    """
    if client is None:
        client = get_client()
    
    if not client.ensure_connected():
        logging.error("Keine Verbindung zur Neo4j-Datenbank")
        return []
    
    try:
        query_parts = ["MATCH (t:CodeTransformation)"]
        params = {}
        
        if bash_file_path:
            query_parts.append("MATCH (t)-[:TRANSFORMED_FROM]->(b:BashOriginal)")
            query_parts.append("WHERE b.file_path = $bash_file_path")
            params["bash_file_path"] = bash_file_path
        
        if python_file_path:
            query_parts.append("MATCH (t)-[:MIGRATED_TO]->(p:PythonEquivalent)")
            query_parts.append("WHERE p.file_path = $python_file_path")
            params["python_file_path"] = python_file_path
        
        if transformation_type:
            if "WHERE" in " ".join(query_parts):
                query_parts.append("AND t.transformation_type = $transformation_type")
            else:
                query_parts.append("WHERE t.transformation_type = $transformation_type")
            params["transformation_type"] = transformation_type
        
        query_parts.append("RETURN t")
        
        query = " ".join(query_parts)
        result = client.run_query(query, params)
        
        return [record["t"] for record in result]
    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Code-Transformationen: {str(e)}")
        return []


def get_file_migration_status(
    bash_file_path: str,
    client: Optional[Neo4jClient] = None
) -> Dict:
    """
    Ruft den Migrationsstatus einer Datei aus dem Knowledge Graph ab.
    
    Args:
        bash_file_path: Pfad zur Bash-Datei
        client: Neo4j-Client-Instanz
        
    Returns:
        Dict: Migrationsstatus der Datei
    """
    if client is None:
        client = get_client()
    
    if not client.ensure_connected():
        logging.error("Keine Verbindung zur Neo4j-Datenbank")
        return {
            "bash_file": bash_file_path,
            "python_file": None,
            "migrated": False,
            "decisions": [],
            "transformations": []
        }
    
    try:
        # Bash-Datei abrufen
        bash_nodes = client.run_query(
            """
            MATCH (b:BashOriginal)
            WHERE b.file_path = $file_path
            RETURN b
            """,
            {"file_path": bash_file_path}
        )
        
        if not bash_nodes or len(bash_nodes) == 0:
            return {
                "bash_file": bash_file_path,
                "python_file": None,
                "migrated": False,
                "decisions": [],
                "transformations": []
            }
        
        # Python-Äquivalent abrufen
        python_nodes = client.run_query(
            """
            MATCH (p:PythonEquivalent)-[:EQUIVALENT_TO]->(b:BashOriginal)
            WHERE b.file_path = $file_path
            RETURN p
            """,
            {"file_path": bash_file_path}
        )
        
        python_file = None
        if python_nodes and len(python_nodes) > 0:
            python_file = python_nodes[0]["p"]["file_path"]
        
        # Entscheidungen abrufen
        decisions = get_migration_decisions(bash_file_path, client=client)
        
        # Transformationen abrufen
        transformations = get_code_transformations(bash_file_path, client=client)
        
        return {
            "bash_file": bash_file_path,
            "python_file": python_file,
            "migrated": python_file is not None,
            "decisions": decisions,
            "transformations": transformations
        }
    except Exception as e:
        logging.error(f"Fehler beim Abrufen des Migrationsstatus: {str(e)}")
        return {
            "bash_file": bash_file_path,
            "python_file": None,
            "migrated": False,
            "decisions": [],
            "transformations": []
        }


def get_migration_statistics(client: Optional[Neo4jClient] = None) -> Dict:
    """
    Ruft Migrationsstatistiken aus dem Knowledge Graph ab.
    
    Args:
        client: Neo4j-Client-Instanz
        
    Returns:
        Dict: Migrationsstatistiken
    """
    if client is None:
        client = get_client()
    
    if not client.ensure_connected():
        logging.error("Keine Verbindung zur Neo4j-Datenbank")
        return {
            "total_bash_files": 0,
            "total_python_files": 0,
            "migrated_files": 0,
            "migration_progress": 0.0,
            "total_decisions": 0,
            "total_transformations": 0
        }
    
    try:
        # Anzahl der Bash-Dateien abrufen
        bash_count_result = client.run_query(
            """
            MATCH (b:BashOriginal)
            RETURN COUNT(b) AS count
            """
        )
        
        total_bash_files = bash_count_result[0]["count"] if bash_count_result else 0
        
        # Anzahl der Python-Dateien abrufen
        python_count_result = client.run_query(
            """
            MATCH (p:PythonEquivalent)
            RETURN COUNT(p) AS count
            """
        )
        
        total_python_files = python_count_result[0]["count"] if python_count_result else 0
        
        # Anzahl der migrierten Dateien abrufen
        migrated_count_result = client.run_query(
            """
            MATCH (p:PythonEquivalent)-[:EQUIVALENT_TO]->(b:BashOriginal)
            RETURN COUNT(DISTINCT b) AS count
            """
        )
        
        migrated_files = migrated_count_result[0]["count"] if migrated_count_result else 0
        
        # Migrationsfortschritt berechnen
        migration_progress = 0.0
        if total_bash_files > 0:
            migration_progress = (migrated_files / total_bash_files) * 100.0
        
        # Anzahl der Entscheidungen abrufen
        decisions_count_result = client.run_query(
            """
            MATCH (d:MigrationDecision)
            RETURN COUNT(d) AS count
            """
        )
        
        total_decisions = decisions_count_result[0]["count"] if decisions_count_result else 0
        
        # Anzahl der Transformationen abrufen
        transformations_count_result = client.run_query(
            """
            MATCH (t:CodeTransformation)
            RETURN COUNT(t) AS count
            """
        )
        
        total_transformations = transformations_count_result[0]["count"] if transformations_count_result else 0
        
        return {
            "total_bash_files": total_bash_files,
            "total_python_files": total_python_files,
            "migrated_files": migrated_files,
            "migration_progress": migration_progress,
            "total_decisions": total_decisions,
            "total_transformations": total_transformations
        }
    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Migrationsstatistiken: {str(e)}")
        return {
            "total_bash_files": 0,
            "total_python_files": 0,
            "migrated_files": 0,
            "migration_progress": 0.0,
            "total_decisions": 0,
            "total_transformations": 0
        }


logging.debug("Migrationsmodul initialisiert")