"""
Database utilities for the LLM Stack.

This module provides common database operations with consistent error handling
and connection management, particularly for Neo4j.
"""

from typing import Dict, List, Optional, Tuple, Union, Any, Callable

from llm_stack.core import logging


class DatabaseConnectionManager:
    """Base class for database connection managers."""
    
    def __init__(self):
        """Initialize the database connection manager."""
        self.connected = False
    
    def connect(self) -> bool:
        """
        Connect to the database.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        raise NotImplementedError("Subclasses must implement connect()")
    
    def disconnect(self) -> bool:
        """
        Disconnect from the database.
        
        Returns:
            bool: True if disconnected successfully, False otherwise
        """
        raise NotImplementedError("Subclasses must implement disconnect()")
    
    def ensure_connected(self) -> bool:
        """
        Ensure the database is connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not self.connected:
            return self.connect()
        return True
    
    def with_connection(self, func: Callable) -> Callable:
        """
        Decorator to ensure a function is executed with a database connection.
        
        Args:
            func: Function to decorate
            
        Returns:
            Callable: Decorated function
        """
        def wrapper(*args, **kwargs):
            if not self.ensure_connected():
                return None
            return func(*args, **kwargs)
        return wrapper


class Neo4jConnectionManager(DatabaseConnectionManager):
    """Neo4j connection manager."""
    
    def __init__(
        self, 
        uri: Optional[str] = None, 
        username: Optional[str] = None, 
        password: Optional[str] = None
    ):
        """
        Initialize the Neo4j connection manager.
        
        Args:
            uri: Neo4j URI
            username: Neo4j username
            password: Neo4j password
        """
        super().__init__()
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
    
    def connect(self) -> bool:
        """
        Connect to Neo4j.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            # Import here to avoid dependency issues
            from neo4j import GraphDatabase
            
            if not self.uri or not self.username or not self.password:
                logging.error("Neo4j connection parameters not set")
                return False
            
            self.driver = GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            )
            
            # Test the connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            
            self.connected = True
            logging.info("Connected to Neo4j database")
            return True
        
        except Exception as e:
            logging.error(f"Error connecting to Neo4j: {str(e)}")
            self.driver = None
            self.connected = False
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from Neo4j.
        
        Returns:
            bool: True if disconnected successfully, False otherwise
        """
        try:
            if self.driver:
                self.driver.close()
                self.driver = None
            
            self.connected = False
            logging.info("Disconnected from Neo4j database")
            return True
        
        except Exception as e:
            logging.error(f"Error disconnecting from Neo4j: {str(e)}")
            return False
    
    def run_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Run a Cypher query.
        
        Args:
            query: Cypher query
            parameters: Query parameters
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        if not self.ensure_connected():
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        
        except Exception as e:
            logging.error(f"Error running Neo4j query: {str(e)}")
            return []
    
    def run_transaction(
        self, func: Callable, parameters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Run a function in a transaction.
        
        Args:
            func: Function to run in the transaction
            parameters: Parameters for the function
            
        Returns:
            Any: Result of the function
        """
        if not self.ensure_connected():
            return None
        
        try:
            with self.driver.session() as session:
                return session.write_transaction(func, parameters or {})
        
        except Exception as e:
            logging.error(f"Error running Neo4j transaction: {str(e)}")
            return None


# Singleton instance of Neo4j connection manager
_neo4j_manager = None


def get_neo4j_manager(
    uri: Optional[str] = None, 
    username: Optional[str] = None, 
    password: Optional[str] = None
) -> Neo4jConnectionManager:
    """
    Get the singleton instance of Neo4j connection manager.
    
    Args:
        uri: Neo4j URI
        username: Neo4j username
        password: Neo4j password
        
    Returns:
        Neo4jConnectionManager: Neo4j connection manager
    """
    global _neo4j_manager
    
    if _neo4j_manager is None:
        _neo4j_manager = Neo4jConnectionManager(uri, username, password)
    
    # Update connection parameters if provided
    if uri is not None:
        _neo4j_manager.uri = uri
    if username is not None:
        _neo4j_manager.username = username
    if password is not None:
        _neo4j_manager.password = password
    
    return _neo4j_manager