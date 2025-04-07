"""
Migration functions for the LLM Stack Knowledge Graph.

This module provides functions for tracking and managing
migration decisions in the Knowledge Graph.
"""

import functools
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable

from llm_stack.core import error, logging
from llm_stack.knowledge_graph.client import Neo4jClient, get_client, create_indexes
from llm_stack.knowledge_graph.models import (
    BashOriginal,
    CodeTransformation,
    EntityType,
    MigrationDecision,
    PythonEquivalent,
)
from llm_stack.knowledge_graph.schema import NodeLabel, RelationshipType

# Cache for frequently accessed data
_FILE_NODE_CACHE = {}
_DECISION_NODE_CACHE = {}
_CACHE_TTL = 300  # Cache TTL in seconds

# Initialize indexes on module import
_INDEXES_INITIALIZED = False


# Ensure indexes are created
def ensure_indexes(func: Callable) -> Callable:
    """
    Decorator to ensure indexes are created before executing a function.
    
    Args:
        func: Function to decorate
        
    Returns:
        Callable: Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global _INDEXES_INITIALIZED
        
        if not _INDEXES_INITIALIZED:
            client = kwargs.get('client')
            if client is None and args:
                # Try to find client in positional arguments
                for arg in args:
                    if isinstance(arg, Neo4jClient):
                        client = arg
                        break
            
            if client is None:
                client = get_client()
                
            if client.ensure_connected():
                create_indexes(client)
                _INDEXES_INITIALIZED = True
                
        return func(*args, **kwargs)
    
    return wrapper

# Cache decorator for file node lookups
def cache_file_node(func: Callable) -> Callable:
    """
    Decorator to cache file node lookups.
    
    Args:
        func: Function to decorate
        
    Returns:
        Callable: Decorated function
    """
    @functools.wraps(func)
    def wrapper(client: Neo4jClient, node_type: str, file_path: str):
        cache_key = f"{node_type}:{file_path}"
        
        # Check cache
        if cache_key in _FILE_NODE_CACHE:
            node_id, timestamp = _FILE_NODE_CACHE[cache_key]
            if time.time() - timestamp < _CACHE_TTL:
                return node_id
        
        # Call original function
        result = func(client, node_type, file_path)
        
        # Update cache
        if result is not None:
            _FILE_NODE_CACHE[cache_key] = (result, time.time())
            
        return result
    
    return wrapper

@cache_file_node
def _find_node_by_file_path(
    client: Neo4jClient,
    node_type: str,
    file_path: str
) -> Optional[int]:
    """
    Finds a node by its file path with caching.

    Args:
        client: Neo4j client instance
        node_type: Type of node to find (e.g., "BashOriginal", "PythonEquivalent")
        file_path: Path to the file

    Returns:
        Optional[int]: Node ID or None if not found
    """
    # Use index for efficient lookup
    nodes = client.run_query(
        f"""
        MATCH (n:{node_type})
        WHERE n.file_path = $file_path
        RETURN n
        """,
        {"file_path": file_path},
    )

    if nodes and len(nodes) > 0:
        return nodes[0]["n"]["id"]
    return None


def _create_file_relationship(
    client: Neo4jClient,
    source_node_id: int,
    file_path: str,
    node_type: str,
    relationship_type: str
) -> bool:
    """
    Creates a relationship between a node and a file node.

    Args:
        client: Neo4j client instance
        source_node_id: ID of the source node
        file_path: Path to the file
        node_type: Type of file node (e.g., "BashOriginal", "PythonEquivalent")
        relationship_type: Type of relationship to create

    Returns:
        bool: True if the relationship was created, False otherwise
    """
    file_node_id = _find_node_by_file_path(client, node_type, file_path)
    
    if file_node_id:
        client.create_relationship(
            source_node_id, file_node_id, relationship_type
        )
        return True
    return False


@ensure_indexes
def record_migration_decision(
    decision: str,
    rationale: str,
    bash_file_path: Optional[str] = None,
    python_file_path: Optional[str] = None,
    alternatives: Optional[List[str]] = None,
    impact: Optional[str] = None,
    client: Optional[Neo4jClient] = None,
) -> Optional[Dict]:
    """
    Records a migration decision in the Knowledge Graph.

    Args:
        decision: The decision made
        rationale: Justification for the decision
        bash_file_path: Path to the Bash file the decision relates to
        python_file_path: Path to the Python file the decision relates to
        alternatives: Alternative decisions that were considered
        impact: Impact of the decision
        client: Neo4j client instance

    Returns:
        Optional[Dict]: Created decision node or None if an error occurred
    """
    if client is None:
        client = get_client()

    if not client.ensure_connected():
        logging.error("No connection to Neo4j database")
        return None

    try:
        # Generate decision ID
        decision_id = f"decision:{uuid.uuid4()}"

        # Create decision node
        decision_node = MigrationDecision(
            id=decision_id,
            name=f"Migration Decision: {decision[:30]}...",
            description=rationale,
            decision=decision,
            rationale=rationale,
            alternatives=alternatives,
            impact=impact,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Prepare batch operations
        batch_operations = []
        
        # Create node operation
        create_node_query = """
        CREATE (n:MigrationDecision $properties)
        RETURN n
        """
        batch_operations.append((create_node_query, {"properties": decision_node.to_neo4j_properties()}))
        
        # Execute batch and get result
        results = client.execute_batch(batch_operations)
        if not results or not results[0]:
            logging.error("Error creating decision node")
            return None
            
        result = results[0][0]
        decision_node_id = result["n"]["id"]

        # Create relationships to Bash and Python files if specified
        relationship_operations = []
        
        if bash_file_path:
            bash_node_id = _find_node_by_file_path(client, "BashOriginal", bash_file_path)
            if bash_node_id:
                rel_query = """
                MATCH (d), (b)
                WHERE ID(d) = $decision_id AND ID(b) = $bash_id
                CREATE (d)-[:DECISION_FOR]->(b)
                """
                relationship_operations.append((rel_query, {
                    "decision_id": decision_node_id,
                    "bash_id": bash_node_id
                }))

        if python_file_path:
            python_node_id = _find_node_by_file_path(client, "PythonEquivalent", python_file_path)
            if python_node_id:
                rel_query = """
                MATCH (d), (p)
                WHERE ID(d) = $decision_id AND ID(p) = $python_id
                CREATE (d)-[:DECISION_FOR]->(p)
                """
                relationship_operations.append((rel_query, {
                    "decision_id": decision_node_id,
                    "python_id": python_node_id
                }))
                
        # Execute relationship operations if any
        if relationship_operations:
            client.execute_batch(relationship_operations)

        # Update decision node cache
        _DECISION_NODE_CACHE[decision_id] = (decision_node_id, time.time())

        logging.success(
            f"Migration decision successfully recorded: {decision_id}"
        )
        return result["n"]
    except Exception as e:
        logging.error(f"Error recording migration decision: {str(e)}")
        return None

# Cache decorator for decision node lookups
def cache_decision_node(func: Callable) -> Callable:
    """
    Decorator to cache decision node lookups.
    
    Args:
        func: Function to decorate
        
    Returns:
        Callable: Decorated function
    """
    @functools.wraps(func)
    def wrapper(client: Neo4jClient, decision_id: str):
        # Check cache
        if decision_id in _DECISION_NODE_CACHE:
            node_id, timestamp = _DECISION_NODE_CACHE[decision_id]
            if time.time() - timestamp < _CACHE_TTL:
                return node_id
        
        # Call original function
        result = func(client, decision_id)
        
        # Update cache
        if result is not None:
            _DECISION_NODE_CACHE[decision_id] = (result, time.time())
            
        return result
    
    return wrapper

@cache_decision_node
def _find_decision_by_id(
    client: Neo4jClient,
    decision_id: str
) -> Optional[int]:
    """
    Finds a decision node by its ID with caching.

    Args:
        client: Neo4j client instance
        decision_id: ID of the decision

    Returns:
        Optional[int]: Node ID or None if not found
    """
    # Use index for efficient lookup
    decision_nodes = client.run_query(
        """
        MATCH (n:MigrationDecision)
        WHERE n.id = $decision_id
        RETURN n
        """,
        {"decision_id": decision_id},
    )

    if decision_nodes and len(decision_nodes) > 0:
        return decision_nodes[0]["n"]["id"]
    return None


@ensure_indexes
def record_code_transformation(
    transformation_type: str,
    before: str,
    after: str,
    bash_file_path: Optional[str] = None,
    python_file_path: Optional[str] = None,
    decision_id: Optional[str] = None,
    client: Optional[Neo4jClient] = None,
) -> Optional[Dict]:
    """
    Records a code transformation in the Knowledge Graph.

    Args:
        transformation_type: Type of transformation (e.g., "function_migration", "syntax_change")
        before: Code before the transformation
        after: Code after the transformation
        bash_file_path: Path to the Bash file the transformation relates to
        python_file_path: Path to the Python file the transformation relates to
        decision_id: ID of the associated migration decision
        client: Neo4j client instance

    Returns:
        Optional[Dict]: Created transformation node or None if an error occurred
    """
    if client is None:
        client = get_client()

    if not client.ensure_connected():
        logging.error("No connection to Neo4j database")
        return None

    try:
        # Generate transformation ID
        transformation_id = f"transformation:{uuid.uuid4()}"

        # Create transformation node
        transformation_node = CodeTransformation(
            id=transformation_id,
            name=f"Code Transformation: {transformation_type}",
            description=f"Transformation from Bash to Python: {transformation_type}",
            transformation_type=transformation_type,
            before=before,
            after=after,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Prepare batch operations
        batch_operations = []
        
        # Create node operation
        create_node_query = """
        CREATE (n:CodeTransformation $properties)
        RETURN n
        """
        batch_operations.append((create_node_query, {"properties": transformation_node.to_neo4j_properties()}))
        
        # Execute batch and get result
        results = client.execute_batch(batch_operations)
        if not results or not results[0]:
            logging.error("Error creating transformation node")
            return None
            
        result = results[0][0]
        transformation_node_id = result["n"]["id"]

        # Prepare relationship operations
        relationship_operations = []
        
        # Create relationships to Bash and Python files if specified
        if bash_file_path:
            bash_node_id = _find_node_by_file_path(client, "BashOriginal", bash_file_path)
            if bash_node_id:
                rel_query = """
                MATCH (t), (b)
                WHERE ID(t) = $trans_id AND ID(b) = $bash_id
                CREATE (t)-[:TRANSFORMED_FROM]->(b)
                """
                relationship_operations.append((rel_query, {
                    "trans_id": transformation_node_id,
                    "bash_id": bash_node_id
                }))

        if python_file_path:
            python_node_id = _find_node_by_file_path(client, "PythonEquivalent", python_file_path)
            if python_node_id:
                rel_query = """
                MATCH (t), (p)
                WHERE ID(t) = $trans_id AND ID(p) = $python_id
                CREATE (t)-[:MIGRATED_TO]->(p)
                """
                relationship_operations.append((rel_query, {
                    "trans_id": transformation_node_id,
                    "python_id": python_node_id
                }))

        # Create relationship to decision if specified
        if decision_id:
            decision_node_id = _find_decision_by_id(client, decision_id)
            if decision_node_id:
                rel_query = """
                MATCH (t), (d)
                WHERE ID(t) = $trans_id AND ID(d) = $decision_id
                CREATE (t)-[:DECISION_FOR]->(d)
                """
                relationship_operations.append((rel_query, {
                    "trans_id": transformation_node_id,
                    "decision_id": decision_node_id
                }))
                
        # Execute relationship operations if any
        if relationship_operations:
            client.execute_batch(relationship_operations)

        logging.success(
            f"Code transformation successfully recorded: {transformation_id}"
        )
        return result["n"]
    except Exception as e:
        logging.error(f"Error recording code transformation: {str(e)}")
        return None


def _update_file_content(
    client: Neo4jClient,
    node_id: int,
    content: str
) -> Optional[Dict]:
    """
    Updates the content of a file node.

    Args:
        client: Neo4j client instance
        node_id: ID of the node to update
        content: New content for the file

    Returns:
        Optional[Dict]: Updated node or None if an error occurred
    """
    return client.update_node(
        node_id,
        {
            "content": content,
            "updated_at": datetime.now().isoformat()
        }
    )


def _create_file_node(
    file_type: str,
    file_path: str,
    content: str,
    client: Neo4jClient
) -> Optional[Dict]:
    """
    Creates a file node in the Knowledge Graph.

    Args:
        file_type: Type of file ("bash" or "python")
        file_path: Path to the file
        content: Content of the file
        client: Neo4j client instance

    Returns:
        Optional[Dict]: Created file node or None if an error occurred
    """
    # Generate file ID
    file_id = f"{file_type}:{uuid.uuid4()}"
    
    # Determine node class and description based on file type
    if file_type == "bash":
        node_class = BashOriginal
        description = f"Original Bash file: {file_path}"
    else:  # python
        node_class = PythonEquivalent
        description = f"Python equivalent file: {file_path}"
    
    # Create file node
    file_node = node_class(
        id=file_id,
        name=f"{file_type.capitalize()} File: {file_path}",
        description=description,
        file_path=file_path,
        content=content,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    # Create node
    return client.create_node(
        file_node.get_labels(), file_node.to_neo4j_properties()
    )


@ensure_indexes
def record_bash_file(
    file_path: str, content: str, client: Optional[Neo4jClient] = None
) -> Optional[Dict]:
    """
    Records a Bash file in the Knowledge Graph.

    Args:
        file_path: Path to the Bash file
        content: Content of the Bash file
        client: Neo4j client instance

    Returns:
        Optional[Dict]: Created file node or None if an error occurred
    """
    if client is None:
        client = get_client()

    if not client.ensure_connected():
        logging.error("No connection to Neo4j database")
        return None

    try:
        # Check if the file already exists
        bash_node_id = _find_node_by_file_path(client, "BashOriginal", file_path)
        
        if bash_node_id:
            # Update file - use parameterized query
            update_query = """
            MATCH (n)
            WHERE ID(n) = $node_id
            SET n.content = $content, n.updated_at = $updated_at
            RETURN n
            """
            result = client.run_query(
                update_query,
                {
                    "node_id": bash_node_id,
                    "content": content,
                    "updated_at": datetime.now().isoformat()
                }
            )
            
            if result and len(result) > 0:
                # Clear cache entry to ensure fresh data
                cache_key = f"BashOriginal:{file_path}"
                if cache_key in _FILE_NODE_CACHE:
                    del _FILE_NODE_CACHE[cache_key]
                    
                logging.success(f"Bash file successfully updated: {file_path}")
                return result[0]["n"]
            return None

        # Create new file node with a single query
        file_id = f"bash:{uuid.uuid4()}"
        description = f"Original Bash file: {file_path}"
        
        # Create file node with a single query
        create_query = """
        CREATE (n:BashOriginal:Entity {
            id: $id,
            name: $name,
            description: $description,
            file_path: $file_path,
            content: $content,
            created_at: $timestamp,
            updated_at: $timestamp,
            entity_type: 'BashOriginal'
        })
        RETURN n
        """
        
        timestamp = datetime.now().isoformat()
        result = client.run_query(
            create_query,
            {
                "id": file_id,
                "name": f"Bash File: {file_path}",
                "description": description,
                "file_path": file_path,
                "content": content,
                "timestamp": timestamp
            }
        )
        
        if result and len(result) > 0:
            # Update cache with new node
            node_id = result[0]["n"]["id"]
            _FILE_NODE_CACHE[f"BashOriginal:{file_path}"] = (node_id, time.time())
            
            logging.success(f"Bash file successfully recorded: {file_path}")
            return result[0]["n"]
        return None
    except Exception as e:
        logging.error(f"Error recording Bash file: {str(e)}")
        return None


@ensure_indexes
def record_python_file(
    file_path: str,
    content: str,
    bash_file_path: Optional[str] = None,
    client: Optional[Neo4jClient] = None,
) -> Optional[Dict]:
    """
    Records a Python file in the Knowledge Graph.

    Args:
        file_path: Path to the Python file
        content: Content of the Python file
        bash_file_path: Path to the corresponding Bash file
        client: Neo4j client instance

    Returns:
        Optional[Dict]: Created file node or None if an error occurred
    """
    if client is None:
        client = get_client()

    if not client.ensure_connected():
        logging.error("No connection to Neo4j database")
        return None

    try:
        # Check if the file already exists
        python_node_id = _find_node_by_file_path(client, "PythonEquivalent", file_path)
        
        if python_node_id:
            # Update file - use parameterized query
            update_query = """
            MATCH (n)
            WHERE ID(n) = $node_id
            SET n.content = $content, n.updated_at = $updated_at
            RETURN n
            """
            result = client.run_query(
                update_query,
                {
                    "node_id": python_node_id,
                    "content": content,
                    "updated_at": datetime.now().isoformat()
                }
            )
            
            if result and len(result) > 0:
                # Clear cache entry to ensure fresh data
                cache_key = f"PythonEquivalent:{file_path}"
                if cache_key in _FILE_NODE_CACHE:
                    del _FILE_NODE_CACHE[cache_key]
                    
                logging.success(f"Python file successfully updated: {file_path}")
                return result[0]["n"]
            return None

        # Create new file node and relationship in a batch operation
        batch_operations = []
        
        # Generate file ID
        file_id = f"python:{uuid.uuid4()}"
        timestamp = datetime.now().isoformat()
        
        # Create file node
        create_query = """
        CREATE (n:PythonEquivalent:Entity {
            id: $id,
            name: $name,
            description: $description,
            file_path: $file_path,
            content: $content,
            created_at: $timestamp,
            updated_at: $timestamp,
            entity_type: 'PythonEquivalent'
        })
        RETURN n
        """
        
        batch_operations.append((
            create_query,
            {
                "id": file_id,
                "name": f"Python File: {file_path}",
                "description": f"Python equivalent file: {file_path}",
                "file_path": file_path,
                "content": content,
                "timestamp": timestamp
            }
        ))
        
        # Execute batch and get result
        results = client.execute_batch(batch_operations)
        if not results or not results[0]:
            logging.error("Error creating Python file node")
            return None
            
        result = results[0][0]
        python_node_id = result["n"]["id"]
        
        # Update cache with new node
        _FILE_NODE_CACHE[f"PythonEquivalent:{file_path}"] = (python_node_id, time.time())

        # Create relationship to Bash file if specified
        if bash_file_path:
            bash_node_id = _find_node_by_file_path(client, "BashOriginal", bash_file_path)
            
            if bash_node_id:
                rel_query = """
                MATCH (p), (b)
                WHERE ID(p) = $python_id AND ID(b) = $bash_id
                CREATE (p)-[:EQUIVALENT_TO]->(b)
                """
                client.run_query(rel_query, {
                    "python_id": python_node_id,
                    "bash_id": bash_node_id
                })

        logging.success(f"Python file successfully recorded: {file_path}")
        return result["n"]
    except Exception as e:
        logging.error(f"Error recording Python file: {str(e)}")
        return None


def _get_decisions_for_file(
    client: Neo4jClient,
    file_path: str,
    file_type: str
) -> List[Dict]:
    """
    Retrieves migration decisions for a specific file.

    Args:
        client: Neo4j client instance
        file_path: Path to the file
        file_type: Type of file ("BashOriginal" or "PythonEquivalent")

    Returns:
        List[Dict]: List of migration decisions
    """
    result = client.run_query(
        f"""
        MATCH (d:MigrationDecision)-[:DECISION_FOR]->(f:{file_type})
        WHERE f.file_path = $file_path
        RETURN d
        """,
        {"file_path": file_path},
    )
    
    return [record["d"] for record in result]


def _extract_records(result: List[Dict], key: str) -> List[Dict]:
    """
    Extracts records from a query result.

    Args:
        result: Query result
        key: Key to extract

    Returns:
        List[Dict]: Extracted records
    """
    return [record[key] for record in result]


def get_migration_decisions(
    bash_file_path: Optional[str] = None,
    python_file_path: Optional[str] = None,
    client: Optional[Neo4jClient] = None,
) -> List[Dict]:
    """
    Retrieves migration decisions from the Knowledge Graph.

    Args:
        bash_file_path: Path to the Bash file for which decisions should be retrieved
        python_file_path: Path to the Python file for which decisions should be retrieved
        client: Neo4j client instance

    Returns:
        List[Dict]: List of migration decisions
    """
    if client is None:
        client = get_client()

    if not client.ensure_connected():
        logging.error("No connection to Neo4j database")
        return []

    try:
        if bash_file_path:
            return _get_decisions_for_file(client, bash_file_path, "BashOriginal")
        elif python_file_path:
            return _get_decisions_for_file(client, python_file_path, "PythonEquivalent")
        else:
            # Retrieve all decisions
            result = client.run_query(
                """
                MATCH (d:MigrationDecision)
                RETURN d
                """
            )
            
            return _extract_records(result, "d")
    except Exception as e:
        logging.error(f"Error retrieving migration decisions: {str(e)}")
        return []


def _build_transformation_query(
    bash_file_path: Optional[str] = None,
    python_file_path: Optional[str] = None,
    transformation_type: Optional[str] = None
) -> Tuple[str, Dict]:
    """
    Builds a query for retrieving code transformations.

    Args:
        bash_file_path: Path to the Bash file
        python_file_path: Path to the Python file
        transformation_type: Type of transformation

    Returns:
        Tuple[str, Dict]: Query string and parameters
    """
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
    
    return query, params


def get_code_transformations(
    bash_file_path: Optional[str] = None,
    python_file_path: Optional[str] = None,
    transformation_type: Optional[str] = None,
    client: Optional[Neo4jClient] = None,
) -> List[Dict]:
    """
    Retrieves code transformations from the Knowledge Graph.

    Args:
        bash_file_path: Path to the Bash file for which transformations should be retrieved
        python_file_path: Path to the Python file for which transformations should be retrieved
        transformation_type: Type of transformation
        client: Neo4j client instance

    Returns:
        List[Dict]: List of code transformations
    """
    if client is None:
        client = get_client()

    if not client.ensure_connected():
        logging.error("No connection to Neo4j database")
        return []

    try:
        query, params = _build_transformation_query(
            bash_file_path, python_file_path, transformation_type
        )
        result = client.run_query(query, params)
        
        return _extract_records(result, "t")
    except Exception as e:
        logging.error(f"Error retrieving code transformations: {str(e)}")
        return []


def _create_empty_migration_status(bash_file_path: str) -> Dict:
    """
    Creates an empty migration status object.

    Args:
        bash_file_path: Path to the Bash file

    Returns:
        Dict: Empty migration status
    """
    return {
        "bash_file": bash_file_path,
        "python_file": None,
        "migrated": False,
        "decisions": [],
        "transformations": [],
    }


def _find_python_equivalent(client: Neo4jClient, bash_file_path: str) -> Optional[str]:
    """
    Finds the Python equivalent of a Bash file.

    Args:
        client: Neo4j client instance
        bash_file_path: Path to the Bash file

    Returns:
        Optional[str]: Path to the Python file or None if not found
    """
    python_nodes = client.run_query(
        """
        MATCH (p:PythonEquivalent)-[:EQUIVALENT_TO]->(b:BashOriginal)
        WHERE b.file_path = $file_path
        RETURN p
        """,
        {"file_path": bash_file_path},
    )

    if python_nodes and len(python_nodes) > 0:
        return python_nodes[0]["p"]["file_path"]
    return None


def get_file_migration_status(
    bash_file_path: str, client: Optional[Neo4jClient] = None
) -> Dict:
    """
    Retrieves the migration status of a file from the Knowledge Graph.

    Args:
        bash_file_path: Path to the Bash file
        client: Neo4j client instance

    Returns:
        Dict: Migration status of the file
    """
    if client is None:
        client = get_client()

    if not client.ensure_connected():
        logging.error("No connection to Neo4j database")
        return _create_empty_migration_status(bash_file_path)

    try:
        # Check if Bash file exists
        bash_exists = _find_node_by_file_path(client, "BashOriginal", bash_file_path) is not None
        
        if not bash_exists:
            return _create_empty_migration_status(bash_file_path)

        # Find Python equivalent
        python_file = _find_python_equivalent(client, bash_file_path)

        # Retrieve decisions and transformations
        decisions = get_migration_decisions(bash_file_path, client=client)
        transformations = get_code_transformations(bash_file_path, client=client)

        return {
            "bash_file": bash_file_path,
            "python_file": python_file,
            "migrated": python_file is not None,
            "decisions": decisions,
            "transformations": transformations,
        }
    except Exception as e:
        logging.error(f"Error retrieving migration status: {str(e)}")
        return _create_empty_migration_status(bash_file_path)


def _create_empty_statistics() -> Dict:
    """
    Creates an empty statistics object.

    Returns:
        Dict: Empty statistics
    """
    return {
        "total_bash_files": 0,
        "total_python_files": 0,
        "migrated_files": 0,
        "migration_progress": 0.0,
        "total_decisions": 0,
        "total_transformations": 0,
    }


def _get_count(client: Neo4jClient, node_type: str) -> int:
    """
    Gets the count of nodes of a specific type.

    Args:
        client: Neo4j client instance
        node_type: Type of node to count

    Returns:
        int: Count of nodes
    """
    count_result = client.run_query(
        f"""
        MATCH (n:{node_type})
        RETURN COUNT(n) AS count
        """
    )
    
    return count_result[0]["count"] if count_result else 0


def _get_migrated_files_count(client: Neo4jClient) -> int:
    """
    Gets the count of migrated files.

    Args:
        client: Neo4j client instance

    Returns:
        int: Count of migrated files
    """
    migrated_count_result = client.run_query(
        """
        MATCH (p:PythonEquivalent)-[:EQUIVALENT_TO]->(b:BashOriginal)
        RETURN COUNT(DISTINCT b) AS count
        """
    )
    
    return migrated_count_result[0]["count"] if migrated_count_result else 0


def get_migration_statistics(client: Optional[Neo4jClient] = None) -> Dict:
    """
    Retrieves migration statistics from the Knowledge Graph.

    Args:
        client: Neo4j client instance

    Returns:
        Dict: Migration statistics
    """
    if client is None:
        client = get_client()

    if not client.ensure_connected():
        logging.error("No connection to Neo4j database")
        return _create_empty_statistics()

    try:
        # Get counts of different node types
        total_bash_files = _get_count(client, "BashOriginal")
        total_python_files = _get_count(client, "PythonEquivalent")
        migrated_files = _get_migrated_files_count(client)
        total_decisions = _get_count(client, "MigrationDecision")
        total_transformations = _get_count(client, "CodeTransformation")

        # Calculate migration progress
        migration_progress = 0.0
        if total_bash_files > 0:
            migration_progress = (migrated_files / total_bash_files) * 100.0

        return {
            "total_bash_files": total_bash_files,
            "total_python_files": total_python_files,
            "migrated_files": migrated_files,
            "migration_progress": migration_progress,
            "total_decisions": total_decisions,
            "total_transformations": total_transformations,
        }
    except Exception as e:
        logging.error(f"Error retrieving migration statistics: {str(e)}")
        return _create_empty_statistics()


logging.debug("Migration module initialized")
