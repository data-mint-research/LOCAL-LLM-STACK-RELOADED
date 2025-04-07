"""
Neo4j Client for the LLM Stack Knowledge Graph.

This module provides functions for connecting to a Neo4j database
and offers basic operations for the Knowledge Graph.
"""

import os
import threading
import collections
import functools
import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from llm_stack.core import dependency_injection, error, logging
from llm_stack.core.db_utils import Neo4jConnectionManager, get_neo4j_manager


class Neo4jClient:
    """Client for interacting with the Neo4j database."""
    
    # Cache for query results - using OrderedDict for LRU functionality
    _QUERY_CACHE = collections.OrderedDict()
    _CACHE_LOCK = threading.Lock()
    _CACHE_TTL = 300  # Cache TTL in seconds
    _CACHE_MAX_SIZE = 100  # Maximum number of items in cache
    _CACHE_STATS = {"hits": 0, "misses": 0}  # Cache statistics for monitoring
    
    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        """
        Initializes a new Neo4j client.

        Args:
            uri: URI of the Neo4j database (defaults to environment variable or secure fallback)
            username: Username for authentication (defaults to environment variable or secure fallback)
            password: Password for authentication (defaults to environment variable or secure fallback)
            database: Name of the database to use (defaults to environment variable or secure fallback)
        """
        # Load configuration from environment variables or use secure defaults
        from llm_stack.core import system
        
        self.uri = uri or system.get_environment_variable("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or system.get_environment_variable("NEO4J_USERNAME", "neo4j")
        
        # No default password - require explicit configuration
        self.password = password or system.get_environment_variable("NEO4J_PASSWORD")
        if not self.password:
            logging.error("No Neo4j password provided. Please set NEO4J_PASSWORD environment variable.")
            logging.warn("Database operations will fail until a password is configured.")
            
        self.database = database or system.get_environment_variable("NEO4J_DATABASE", "neo4j")
        
        # Use the Neo4jConnectionManager from db_utils
        self.connection_manager = Neo4jConnectionManager(self.uri, self.username, self.password)
        self.connected = False
        
        # Initialize indexes for frequently queried properties
        self._indexes_created = False

    def connect(self) -> bool:
        """
        Establishes a connection to the Neo4j database with retry logic.

        Returns:
            bool: True if the connection was successfully established, False otherwise
        """
        max_retries = 3
        retry_delay = 1.0  # seconds
        
        for attempt in range(1, max_retries + 1):
            try:
                self.connected = self.connection_manager.connect()
                if self.connected:
                    logging.success(f"Connection to Neo4j database established: {self.uri}")
                return self.connected
            except ServiceUnavailable as e:
                if attempt < max_retries:
                    logging.warn(f"Neo4j database not reachable (attempt {attempt}/{max_retries}): {str(e)}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logging.error(f"Neo4j database not reachable after {max_retries} attempts: {str(e)}")
                    self.connected = False
                    return False
            except Exception as e:
                logging.error(f"Error connecting to Neo4j database: {str(e)}")
                self.connected = False
                return False

    def close(self) -> None:
        """Closes the connection to the Neo4j database."""
        if self.connection_manager:
            self.connection_manager.disconnect()
            self.connected = False
            logging.info("Connection to Neo4j database closed")

    def ensure_connected(self) -> bool:
        """
        Ensures that a connection to the Neo4j database exists with connection verification.

        Returns:
            bool: True if a connection exists, False otherwise
        """
        if not self.connected:
            return self.connect()
        
        # Periodically verify connection is still valid
        current_time = time.time()
        if not hasattr(self, '_last_connection_check') or current_time - self._last_connection_check > 60:  # Check every minute
            try:
                # Lightweight connection check
                if self.connection_manager.driver:
                    self.connection_manager.driver.verify_connectivity()
                    self._last_connection_check = current_time
                    return True
                else:
                    return self.connect()
            except Exception:
                logging.warn("Neo4j connection lost, attempting to reconnect...")
                return self.connect()
        
        return True

    def _handle_query_error(self, error_obj: Exception, operation_name: str) -> None:
        """
        Handles query execution errors in a consistent way.

        Args:
            error_obj: The exception that was raised
            operation_name: Name of the operation being performed

        Raises:
            error.DatabaseError: With appropriate error message
        """
        if isinstance(error_obj, Neo4jError):
            logging.error(f"Neo4j error during {operation_name}: {str(error_obj)}")
            raise error.DatabaseError(f"Neo4j error: {str(error_obj)}")
        else:
            logging.error(f"Error during {operation_name}: {str(error_obj)}")
            raise error.DatabaseError(f"Error: {str(error_obj)}")

    def _get_cache_key(self, query: str, parameters: Dict[str, Any], database: Optional[str]) -> str:
        """
        Generate a cache key for a query using a more efficient hashing approach.
        
        Args:
            query: The query string
            parameters: Query parameters
            database: Database name
            
        Returns:
            str: Cache key
        """
        # Create a stable representation of parameters for the cache key
        param_str = json.dumps(parameters, sort_keys=True) if parameters else "{}"
        db = database or self.database
        
        # Use hash for more efficient key generation and storage
        key_str = f"{query}:{param_str}:{db}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _cache_result(self, key: str, result: List[Dict[str, Any]]) -> None:
        """
        Cache a query result using OrderedDict for efficient LRU implementation.
        
        Args:
            key: Cache key
            result: Query result to cache
        """
        with self._CACHE_LOCK:
            # If cache is full, OrderedDict will automatically remove oldest item
            if len(self._QUERY_CACHE) >= self._CACHE_MAX_SIZE:
                self._QUERY_CACHE.popitem(last=False)  # Remove oldest item (first inserted)
            
            # Store result with timestamp and move to end (most recently used)
            self._QUERY_CACHE[key] = (result, time.time())
    
    def _get_cached_result(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get a cached query result if available and not expired.
        Uses OrderedDict for efficient LRU implementation.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[List[Dict[str, Any]]]: Cached result or None if not found or expired
        """
        with self._CACHE_LOCK:
            if key in self._QUERY_CACHE:
                result, timestamp = self._QUERY_CACHE[key]
                if time.time() - timestamp < self._CACHE_TTL:
                    # Move to end (most recently used)
                    self._QUERY_CACHE.move_to_end(key)
                    self._CACHE_STATS["hits"] += 1
                    return result
                else:
                    # Remove expired item
                    del self._QUERY_CACHE[key]
            
            self._CACHE_STATS["misses"] += 1
            return None
    
    @functools.lru_cache(maxsize=128)
    def _is_read_only_query(self, query: str) -> bool:
        """
        Determine if a query is read-only (doesn't modify data).
        Uses LRU cache for repeated query type checks.
        
        Args:
            query: The query string to check
            
        Returns:
            bool: True if the query is read-only, False otherwise
        """
        write_keywords = ["CREATE", "DELETE", "REMOVE", "SET", "MERGE"]
        query_upper = query.upper()
        return not any(keyword in query_upper for keyword in write_keywords)
    
    # Remove this method as it's now integrated directly into run_query for better performance
    
    # Remove this method as it's now integrated directly into run_query for better performance
    
    def run_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Executes a Cypher query with optimized caching.

        Args:
            query: Cypher query
            parameters: Parameters for the query
            database: Name of the database to use (overrides the default value)
            use_cache: Whether to use query caching (default: True)

        Returns:
            List[Dict[str, Any]]: Results of the query

        Raises:
            error.DatabaseError: If an error occurs during query execution
        """
        if not self.ensure_connected():
            raise error.DatabaseError("No connection to Neo4j database")

        parameters = parameters or {}
        db = database or self.database
        
        # Fast path for read-only queries with caching
        if use_cache and self._is_read_only_query(query):
            cache_key = self._get_cache_key(query, parameters, db)
            cached_result = self._get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result

        try:
            # Execute the query with connection pooling
            result_data = self.connection_manager.run_query(query, parameters)
            
            # Cache the result if appropriate (only for read-only queries)
            if use_cache and self._is_read_only_query(query):
                cache_key = self._get_cache_key(query, parameters, db)
                self._cache_result(cache_key, result_data)
            
            return result_data
        except Exception as e:
            self._handle_query_error(e, "query execution")

    def _handle_operation_error(self, error_obj: Exception, operation_name: str) -> None:
        """
        Handles operation errors in a consistent way.

        Args:
            error_obj: The exception that was raised
            operation_name: Name of the operation being performed
        """
        logging.error(f"Error {operation_name}: {str(error_obj)}")

    def _extract_first_result(self, result: List[Dict[str, Any]], key: str = "n") -> Optional[Dict[str, Any]]:
        """
        Extracts the first result from a query result list.

        Args:
            result: Query result list
            key: Key to extract from the result

        Returns:
            Optional[Dict[str, Any]]: Extracted result or None if not found
        """
        if result and len(result) > 0:
            return result[0].get(key)
        return None

    def create_node(
        self,
        labels: Union[str, List[str]],
        properties: Dict[str, Any],
        database: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Creates a node in the Knowledge Graph.

        Args:
            labels: Label or list of labels for the node
            properties: Properties of the node
            database: Name of the database to use (overrides the default value)

        Returns:
            Optional[Dict[str, Any]]: Created node or None if an error occurred
        """
        if isinstance(labels, str):
            labels = [labels]

        # Use fully parameterized query
        query = """
        CALL apoc.create.node($labels, $properties) YIELD node
        RETURN node as n
        """

        try:
            result = self.run_query(
                query,
                {
                    "labels": labels,
                    "properties": properties
                },
                database
            )
            return self._extract_first_result(result)
        except Exception as e:
            self._handle_operation_error(e, "creating node")
            return None

    def create_relationship(
        self,
        start_node_id: int,
        end_node_id: int,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Creates a relationship between two nodes in the Knowledge Graph.

        Args:
            start_node_id: ID of the start node
            end_node_id: ID of the end node
            relationship_type: Type of relationship
            properties: Properties of the relationship
            database: Name of the database to use (overrides the default value)

        Returns:
            Optional[Dict[str, Any]]: Created relationship or None if an error occurred
        """
        if properties is None:
            properties = {}

        # Use fully parameterized query
        query = """
        MATCH (a), (b)
        WHERE ID(a) = $start_id AND ID(b) = $end_id
        CALL apoc.create.relationship(a, $rel_type, $properties, b) YIELD rel
        RETURN rel as r
        """

        try:
            result = self.run_query(
                query,
                {
                    "start_id": start_node_id,
                    "end_id": end_node_id,
                    "rel_type": relationship_type,
                    "properties": properties,
                },
                database,
            )
            return self._extract_first_result(result, "r")
        except Exception as e:
            self._handle_operation_error(e, "creating relationship")
            return None

    def get_node_by_id(
        self, node_id: int, database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves a node by its ID.

        Args:
            node_id: ID of the node
            database: Name of the database to use (overrides the default value)

        Returns:
            Optional[Dict[str, Any]]: Node or None if the node was not found
        """
        query = """
        MATCH (n)
        WHERE ID(n) = $node_id
        RETURN n
        """

        try:
            result = self.run_query(query, {"node_id": node_id}, database)
            return self._extract_first_result(result)
        except Exception as e:
            self._handle_operation_error(e, "retrieving node")
            return None

    def get_nodes_by_label(
        self, label: str, database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves nodes by their label.

        Args:
            label: Label of the nodes
            database: Name of the database to use (overrides the default value)

        Returns:
            List[Dict[str, Any]]: List of nodes
        """
        # Use fully parameterized query
        query = """
        MATCH (n)
        WHERE $label IN labels(n)
        RETURN n
        """

        try:
            result = self.run_query(query, {"label": label}, database)
            return [record.get("n") for record in result]
        except Exception as e:
            logging.error(f"Error retrieving nodes: {str(e)}")
            return []

    def get_nodes_by_property(
        self,
        property_name: str,
        property_value: Any,
        label: Optional[str] = None,
        database: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves nodes by a property.

        Args:
            property_name: Name of the property
            property_value: Value of the property
            label: Optional label to restrict the search
            database: Name of the database to use (overrides the default value)

        Returns:
            List[Dict[str, Any]]: List of nodes
        """
        # Use fully parameterized query
        query = """
        MATCH (n)
        WHERE ($label IS NULL OR $label IN labels(n))
        AND n[$property_name] = $property_value
        RETURN n
        """

        try:
            result = self.run_query(
                query,
                {
                    "label": label,
                    "property_name": property_name,
                    "property_value": property_value
                },
                database
            )
            return [record.get("n") for record in result]
        except Exception as e:
            logging.error(f"Error retrieving nodes: {str(e)}")
            return []

    def update_node(
        self, node_id: int, properties: Dict[str, Any], database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Updates the properties of a node.

        Args:
            node_id: ID of the node
            properties: New properties of the node
            database: Name of the database to use (overrides the default value)

        Returns:
            Optional[Dict[str, Any]]: Updated node or None if an error occurred
        """
        query = """
        MATCH (n)
        WHERE ID(n) = $node_id
        SET n += $properties
        RETURN n
        """

        try:
            result = self.run_query(
                query, {"node_id": node_id, "properties": properties}, database
            )
            return self._extract_first_result(result)
        except Exception as e:
            self._handle_operation_error(e, "updating node")
            return None

    def delete_node(self, node_id: int, database: Optional[str] = None) -> bool:
        """
        Deletes a node.

        Args:
            node_id: ID of the node
            database: Name of the database to use (overrides the default value)

        Returns:
            bool: True if the node was successfully deleted, False otherwise
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
            self._handle_operation_error(e, "deleting node")
            return False

    def delete_relationship(
        self, relationship_id: int, database: Optional[str] = None
    ) -> bool:
        """
        Deletes a relationship.

        Args:
            relationship_id: ID of the relationship
            database: Name of the database to use (overrides the default value)

        Returns:
            bool: True if the relationship was successfully deleted, False otherwise
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
            self._handle_operation_error(e, "deleting relationship")
            return False

    def clear_database(self, database: Optional[str] = None) -> bool:
        """
        Deletes all nodes and relationships in the database.

        Args:
            database: Name of the database to use (overrides the default value)

        Returns:
            bool: True if the database was successfully cleared, False otherwise
        """
        query = """
        MATCH (n)
        DETACH DELETE n
        """

        try:
            self.run_query(query, {}, database)
            logging.success("Database successfully cleared")
            return True
        except Exception as e:
            logging.error(f"Error clearing database: {str(e)}")
            return False

    def _build_schema_query(self, template: str, replacements: Dict[str, str]) -> str:
        """
        Build a schema query by replacing placeholders with actual values.
        
        Args:
            template: Query template with placeholders
            replacements: Dictionary of placeholder to value mappings
            
        Returns:
            str: Formatted query with placeholders replaced
        """
        result = template
        for placeholder, value in replacements.items():
            result = result.replace(f'`${placeholder}`', f'`{value}`')
            result = result.replace(f'${placeholder}', value)
        return result
    
    def create_index(
        self, label: str, property_name: str, database: Optional[str] = None
    ) -> bool:
        """
        Creates an index for a property of a label.

        Args:
            label: Label for which the index should be created
            property_name: Name of the property for which the index should be created
            database: Name of the database to use (overrides the default value)

        Returns:
            bool: True if the index was successfully created, False otherwise
        """
        # Template query with placeholders
        template = """
        CREATE INDEX ON :`$label`(`$property_name`)
        """
        
        # Replace placeholders with actual values
        query = self._build_schema_query(template, {
            "label": label,
            "property_name": property_name
        })

        try:
            self.run_query(query, {}, database)
            logging.success(f"Index for {label}.{property_name} successfully created")
            return True
        except Exception as e:
            logging.error(f"Error creating index: {str(e)}")
            return False

    def create_constraint(
        self,
        label: str,
        property_name: str,
        constraint_type: str = "UNIQUE",
        database: Optional[str] = None,
    ) -> bool:
        """
        Creates a constraint for a property of a label.

        Args:
            label: Label for which the constraint should be created
            property_name: Name of the property for which the constraint should be created
            constraint_type: Type of constraint (UNIQUE, EXISTS, etc.)
            database: Name of the database to use (overrides the default value)

        Returns:
            bool: True if the constraint was successfully created, False otherwise
        """
        # Template query with placeholders
        template = """
        CREATE CONSTRAINT ON (n:`$label`) ASSERT n.`$property_name` IS $constraint_type
        """
        
        # Replace placeholders with actual values
        query = self._build_schema_query(template, {
            "label": label,
            "property_name": property_name,
            "constraint_type": constraint_type
        })

        try:
            self.run_query(query, {}, database)
            logging.success(
                f"Constraint for {label}.{property_name} successfully created"
            )
            return True
        except Exception as e:
            logging.error(f"Error creating constraint: {str(e)}")
            return False

    def _build_relationship_pattern(self, relationship_types: Optional[List[str]], max_depth: int) -> str:
        """
        Build a Cypher relationship pattern for path queries.
        
        Args:
            relationship_types: List of relationship types to consider
            max_depth: Maximum depth of the path
            
        Returns:
            str: Formatted relationship pattern for Cypher query
        """
        # Build the depth pattern
        rel_pattern = f"*1..{max_depth}"
        
        # Add relationship types if specified
        if relationship_types:
            rel_types = "|".join([f":{rel_type}" for rel_type in relationship_types])
            rel_pattern = f"[{rel_types}]{rel_pattern}"
            
        return rel_pattern
    
    def get_shortest_path(
        self,
        start_node_id: int,
        end_node_id: int,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 10,
        database: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Finds the shortest path between two nodes.

        Args:
            start_node_id: ID of the start node
            end_node_id: ID of the end node
            relationship_types: List of relationship types to consider
            max_depth: Maximum depth of the path
            database: Name of the database to use (overrides the default value)

        Returns:
            List[Dict[str, Any]]: List of nodes and relationships in the path
        """
        # Build the relationship pattern
        rel_pattern = self._build_relationship_pattern(relationship_types, max_depth)
            
        # Use parameterized query where possible
        query = f"""
        MATCH path = shortestPath((a)-{rel_pattern}->(b))
        WHERE ID(a) = $start_id AND ID(b) = $end_id
        RETURN path
        """

        try:
            result = self.run_query(
                query, {"start_id": start_node_id, "end_id": end_node_id}, database
            )
            if result and len(result) > 0:
                return result[0].get("path")
            return []
        except Exception as e:
            logging.error(f"Error finding shortest path: {str(e)}")
            return []

    def _build_relationship_direction_pattern(self, direction: str) -> str:
        """
        Build a Cypher relationship direction pattern.
        
        Args:
            direction: Direction of the relationship (OUTGOING, INCOMING, BOTH)
            
        Returns:
            str: Formatted direction pattern for Cypher query
        """
        if direction == "OUTGOING":
            return "-[r]->"
        elif direction == "INCOMING":
            return "<-[r]-"
        else:  # BOTH
            return "-[r]-"
    
    def _build_relationship_type_clause(self, relationship_type: Optional[str]) -> Tuple[str, Dict[str, Any]]:
        """
        Build a Cypher clause for relationship type filtering.
        
        Args:
            relationship_type: Type of relationship or None
            
        Returns:
            Tuple[str, Dict[str, Any]]: Clause and parameters
        """
        params = {}
        if relationship_type:
            params["rel_type"] = relationship_type
            return "type(r) = $rel_type", params
        else:
            return "1=1", params  # Always true if no relationship type specified
    
    def get_connected_nodes(
        self,
        node_id: int,
        relationship_type: Optional[str] = None,
        direction: str = "OUTGOING",
        database: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves nodes that are connected to a specific node.

        Args:
            node_id: ID of the node
            relationship_type: Type of relationship
            direction: Direction of the relationship (OUTGOING, INCOMING, BOTH)
            database: Name of the database to use (overrides the default value)

        Returns:
            List[Dict[str, Any]]: List of connected nodes
        """
        # Build relationship direction pattern
        rel_direction = self._build_relationship_direction_pattern(direction)
        
        # Build relationship type clause and parameters
        rel_type_clause, type_params = self._build_relationship_type_clause(relationship_type)
        
        # Combine parameters
        params = {"node_id": node_id, **type_params}
        
        # Build the query
        query = f"""
        MATCH (a){rel_direction}(b)
        WHERE ID(a) = $node_id AND {rel_type_clause}
        RETURN b
        """

        try:
            result = self.run_query(query, params, database)
            return [record.get("b") for record in result]
        except Exception as e:
            logging.error(f"Error retrieving connected nodes: {str(e)}")
            return []

    def execute_batch(
        self, queries: List[Tuple[str, Dict[str, Any]]], database: Optional[str] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Executes multiple queries as a batch within a single transaction with optimized cache handling.

        Args:
            queries: List of tuples (query, parameters)
            database: Name of the database to use (overrides the default value)

        Returns:
            List[List[Dict[str, Any]]]: List of results for each query
        """
        if not self.ensure_connected():
            raise error.DatabaseError("No connection to Neo4j database")

        db = database or self.database
        results = []

        try:
            # Optimize transaction function to reduce memory usage
            def transaction_function(tx, params):
                batch_results = []
                for query, parameters in params:
                    result = tx.run(query, parameters)
                    # Process results immediately to avoid keeping large result sets in memory
                    batch_results.append([record.data() for record in result])
                return batch_results
            
            results = self.connection_manager.run_transaction(transaction_function, queries)
            
            # Selective cache invalidation - only clear affected entries
            has_write_operations = False
            affected_patterns = []
            
            for query, _ in queries:
                if not self._is_read_only_query(query):
                    has_write_operations = True
                    # Extract table/node names from write queries to selectively invalidate cache
                    if "CREATE" in query.upper() or "DELETE" in query.upper() or "SET" in query.upper():
                        # Extract node labels or relationship types from the query
                        # This is a simplified approach - in a real system, you'd use a more sophisticated parser
                        for label in ["Person", "Company", "BashOriginal", "PythonEquivalent", "MigrationDecision", "CodeTransformation"]:
                            if label in query:
                                affected_patterns.append(label)
            
            # Selective cache invalidation
            if has_write_operations:
                with self._CACHE_LOCK:
                    if affected_patterns:
                        # Selectively invalidate cache entries related to affected patterns
                        keys_to_remove = []
                        for key in self._QUERY_CACHE.keys():
                            if any(pattern in key for pattern in affected_patterns):
                                keys_to_remove.append(key)
                        
                        for key in keys_to_remove:
                            del self._QUERY_CACHE[key]
                    else:
                        # If we can't determine affected patterns, clear the entire cache
                        self._QUERY_CACHE.clear()
                    
            return results
        except Exception as e:
            self._handle_query_error(e, "batch execution")

# Factory function for creating Neo4jClient instances with connection pooling
def create_neo4j_client(
    uri: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    database: Optional[str] = None
) -> Neo4jClient:
    """
    Creates a new Neo4jClient instance with the provided parameters.
    Uses connection pooling for better performance.
    
    Args:
        uri: URI of the Neo4j database (defaults to environment variable or secure fallback)
        username: Username for authentication (defaults to environment variable or secure fallback)
        password: Password for authentication (defaults to environment variable or secure fallback)
        database: Name of the database to use (defaults to environment variable or secure fallback)
        
    Returns:
        Neo4jClient: A new Neo4j client instance
    """
    client = Neo4jClient(uri, username, password, database)
    
    # Pre-warm connection for faster initial queries
    if uri and username and password:
        client.connect()
        
    return client
    
@functools.lru_cache(maxsize=1)
def get_client() -> Neo4jClient:
    """
    Gets the singleton instance of the Neo4j client using the dependency injection framework.
    Uses LRU cache for efficient singleton access.
    
    This function uses the dependency injection framework to retrieve or create
    the Neo4jClient instance. If the client is not registered in the dependency
    container, it will be registered as a singleton.

    Returns:
        Neo4jClient: Neo4j client instance
    """
    # Check if the client is registered in the dependency container
    if not dependency_injection.is_dependency_registered("neo4j_client"):
        # Register the client factory
        dependency_injection.register_dependency(
            "neo4j_client",
            create_neo4j_client,
            singleton=True
        )
    
    # Resolve and return the client
    return dependency_injection.resolve_dependency("neo4j_client")


def init_client(
    uri: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    database: Optional[str] = None,
) -> Neo4jClient:
    """
    Initializes the singleton instance of the Neo4j client with custom parameters.

    Args:
        uri: URI of the Neo4j database
        username: Username for authentication
        password: Password for authentication
        database: Name of the database to use

    Returns:
        Neo4jClient: Neo4j client instance
    """
    # Create a new client with the provided parameters
    client = create_neo4j_client(uri, username, password, database)
    
    # Register it in the dependency container
    dependency_injection.register_dependency(
        "neo4j_client",
        lambda: client,
        singleton=True
    )
    
    return client


def close_client() -> None:
    """Closes the connection of the Neo4j client."""
    # Get the client from the dependency container
    if dependency_injection.is_dependency_registered("neo4j_client"):
        client = dependency_injection.resolve_dependency("neo4j_client")
        client.close()
        
        # Clear the dependency
        dependency_injection.get_container().clear()


# Create indexes for frequently queried properties
def create_indexes(client: Optional[Neo4jClient] = None) -> bool:
    """
    Creates indexes for frequently queried properties with batched operations.
    
    Args:
        client: Neo4j client instance
        
    Returns:
        bool: True if indexes were created successfully, False otherwise
    """
    if client is None:
        client = get_client()
        
    if not client.ensure_connected():
        logging.error("No connection to Neo4j database")
        return False
        
    try:
        # Batch index creation for better performance
        index_operations = [
            # Index for file paths
            ("BashOriginal", "file_path"),
            ("PythonEquivalent", "file_path"),
            
            # Index for IDs in all entity types
            ("MigrationDecision", "id"),
            ("CodeTransformation", "id"),
            ("BashOriginal", "id"),
            ("PythonEquivalent", "id"),
            
            # Index for transformation types
            ("CodeTransformation", "transformation_type"),
            
            # Additional indexes for frequently queried properties
            ("BashOriginal", "name"),
            ("PythonEquivalent", "name"),
        ]
        
        # Execute index creation in batches
        batch_size = 3
        for i in range(0, len(index_operations), batch_size):
            batch = index_operations[i:i+batch_size]
            batch_success = True
            
            for label, property_name in batch:
                batch_success &= client.create_index(label, property_name)
            
            if not batch_success:
                logging.warn(f"Some indexes in batch {i//batch_size + 1} could not be created")
        
        logging.success("Indexes created successfully")
        return True
    except Exception as e:
        logging.error(f"Error creating indexes: {str(e)}")
        return False


logging.debug("Neo4j client module initialized")
