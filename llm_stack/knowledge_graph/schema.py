"""
Schema for the LLM Stack Knowledge Graph.

This module defines the schema for the neo4j Knowledge Graph
based on the existing JSON-LD schema.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from llm_stack.core import error, logging
from llm_stack.knowledge_graph.client import Neo4jClient, get_client


class NodeLabel(str, Enum):
    """Labels for nodes in the Knowledge Graph."""

    # Base classes
    ENTITY = "Entity"
    COMPONENT = "Component"
    RELATIONSHIP = "Relationship"
    INTERFACE = "Interface"
    DATA_FLOW = "DataFlow"

    # Component types
    CONTAINER = "Container"
    SCRIPT = "Script"
    LIBRARY = "Library"
    MODULE = "Module"
    FUNCTION = "Function"
    VARIABLE = "Variable"
    PARAMETER = "Parameter"
    CONFIG_PARAM = "ConfigParam"
    SERVICE = "Service"

    # Relationship types
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

    # Interface types
    API = "API"
    CLI = "CLI"
    API_ENDPOINT = "APIEndpoint"
    CLI_COMMAND = "CLICommand"

    # Data flow types
    DATA_FLOW_STEP = "DataFlowStep"

    # Migration types
    MIGRATION_DECISION = "MigrationDecision"
    CODE_TRANSFORMATION = "CodeTransformation"
    PYTHON_EQUIVALENT = "PythonEquivalent"
    BASH_ORIGINAL = "BashOriginal"


class RelationshipType(str, Enum):
    """Types for relationships in the Knowledge Graph."""

    # Base relationships
    DEPENDS_ON = "DEPENDS_ON"
    CALLS = "CALLS"
    IMPORTS = "IMPORTS"
    CONFIGURES = "CONFIGURES"
    DEFINES = "DEFINES"
    USES = "USES"
    PROVIDES_SERVICE_TO = "PROVIDES_SERVICE_TO"

    # Specific dependencies
    STARTUP_DEPENDENCY = "STARTUP_DEPENDENCY"
    RUNTIME_DEPENDENCY = "RUNTIME_DEPENDENCY"
    CONFIGURATION_DEPENDENCY = "CONFIGURATION_DEPENDENCY"

    # Interface relationships
    EXPOSES = "EXPOSES"
    IMPLEMENTS = "IMPLEMENTS"
    HAS_FUNCTION = "HAS_FUNCTION"
    HAS_PARAMETER = "HAS_PARAMETER"
    HAS_STEP = "HAS_STEP"
    HAS_ENDPOINT = "HAS_ENDPOINT"
    HAS_COMMAND = "HAS_COMMAND"

    # Data flow relationships
    SOURCE = "SOURCE"
    TARGET = "TARGET"

    # Migration relationships
    MIGRATED_TO = "MIGRATED_TO"
    TRANSFORMED_FROM = "TRANSFORMED_FROM"
    EQUIVALENT_TO = "EQUIVALENT_TO"
    DECISION_FOR = "DECISION_FOR"


class SchemaManager:
    """Manager for the Knowledge Graph schema."""

    def __init__(self, client: Optional[Neo4jClient] = None):
        """
        Initializes a new SchemaManager.

        Args:
            client: Neo4j client instance
        """
        self.client = client or get_client()

    def create_schema(self) -> bool:
        """
        Creates the schema for the Knowledge Graph.

        Returns:
            bool: True if the schema was successfully created, False otherwise
        """
        try:
            # Establish connection to the database
            if not self.client.ensure_connected():
                logging.error("No connection to Neo4j database")
                return False

            # Create constraints
            self._create_constraints()

            # Create indices
            self._create_indices()

            logging.success("Schema successfully created")
            return True
        except Exception as e:
            logging.error(f"Error creating schema: {str(e)}")
            return False

    def _create_constraints(self) -> None:
        """Creates constraints for the Knowledge Graph."""
        # Define constraints with their parameters
        constraints = [
            {"label": "Entity", "property": "id", "type": "UNIQUE"},
            {"label": "Component", "property": "name", "type": "UNIQUE"},
            {"label": "Function", "property": "name,filePath", "type": "UNIQUE"},
            {"label": "Variable", "property": "name,filePath", "type": "UNIQUE"},
            {"label": "ConfigParam", "property": "name", "type": "UNIQUE"},
            {"label": "Service", "property": "name", "type": "UNIQUE"},
            {"label": "API", "property": "name", "type": "UNIQUE"},
            {"label": "CLI", "property": "name", "type": "UNIQUE"},
            {"label": "MigrationDecision", "property": "id", "type": "UNIQUE"}
        ]
        
        # Create each constraint
        for constraint in constraints:
            # Neo4j doesn't support parameterization for schema operations
            # so we need to construct the query safely
            if "," in constraint["property"]:
                # Composite property constraint
                query = f"""
                CREATE CONSTRAINT ON (n:{constraint["label"]})
                ASSERT ({constraint["property"]}) IS {constraint["type"]}
                """
            else:
                # Single property constraint
                query = f"""
                CREATE CONSTRAINT ON (n:{constraint["label"]})
                ASSERT n.{constraint["property"]} IS {constraint["type"]}
                """
                
            self.client.run_query(query)

        logging.info("Constraints successfully created")

    def _create_indices(self) -> None:
        """Creates indices for the Knowledge Graph."""
        # Define indices with their parameters
        indices = [
            {"label": "Entity", "property": "type"},
            {"label": "Component", "property": "type"},
            {"label": "Function", "property": "name"},
            {"label": "Function", "property": "filePath"},
            {"label": "Variable", "property": "name"},
            {"label": "ConfigParam", "property": "name"},
            {"label": "Service", "property": "name"},
            {"label": "BashOriginal", "property": "filePath"},
            {"label": "PythonEquivalent", "property": "filePath"}
        ]
        
        # Create each index
        for index in indices:
            # Neo4j doesn't support parameterization for schema operations
            # so we need to construct the query safely
            query = f"""
            CREATE INDEX ON :{index["label"]}({index["property"]})
            """
            
            self.client.run_query(query)

        logging.info("Indices successfully created")

    def drop_schema(self) -> bool:
        """
        Drops the schema for the Knowledge Graph.

        Returns:
            bool: True if the schema was successfully dropped, False otherwise
        """
        try:
            # Establish connection to the database
            if not self.client.ensure_connected():
                logging.error("No connection to Neo4j database")
                return False

            # Delete constraints - using APOC procedure which doesn't need parameterization
            self.client.run_query("CALL apoc.schema.assert({}, {})")

            logging.success("Schema successfully dropped")
            return True
        except Exception as e:
            logging.error(f"Error dropping schema: {str(e)}")
            return False

    def get_schema_info(self) -> Dict:
        """
        Retrieves information about the schema.

        Returns:
            Dict: Information about the schema
        """
        try:
            # Establish connection to the database
            if not self.client.ensure_connected():
                logging.error("No connection to Neo4j database")
                return {}

            # Retrieve constraints - system procedure doesn't need parameterization
            constraints_result = self.client.run_query("CALL db.constraints()")

            # Retrieve indices - system procedure doesn't need parameterization
            indices_result = self.client.run_query("CALL db.indexes()")

            return {"constraints": constraints_result, "indices": indices_result}
        except Exception as e:
            logging.error(f"Error retrieving schema information: {str(e)}")
            return {}


def create_entity_node(
    client: Optional[Neo4jClient] = None,
    entity_id: str = None,
    labels: List[str] = None,
    properties: Dict = None,
) -> Optional[Dict]:
    """
    Creates an entity node in the Knowledge Graph.

    Args:
        client: Neo4j client instance
        entity_id: ID of the entity
        labels: Labels for the node
        properties: Properties of the node

    Returns:
        Optional[Dict]: Created node or None if an error occurred
    """
    if client is None:
        client = get_client()

    if not client.ensure_connected():
        logging.error("No connection to Neo4j database")
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
        # Create node
        result = client.create_node(labels, properties)
        return result
    except Exception as e:
        logging.error(f"Error creating entity node: {str(e)}")
        return None


def create_relationship(
    client: Optional[Neo4jClient] = None,
    start_node_id: int = None,
    end_node_id: int = None,
    relationship_type: str = None,
    properties: Dict = None,
) -> Optional[Dict]:
    """
    Creates a relationship between two nodes in the Knowledge Graph.

    Args:
        client: Neo4j client instance
        start_node_id: ID of the start node
        end_node_id: ID of the end node
        relationship_type: Type of the relationship
        properties: Properties of the relationship

    Returns:
        Optional[Dict]: Created relationship or None if an error occurred
    """
    if client is None:
        client = get_client()

    if not client.ensure_connected():
        logging.error("No connection to Neo4j database")
        return None

    if start_node_id is None or end_node_id is None or relationship_type is None:
        logging.error(
            "Start node ID, end node ID, and relationship type must be specified"
        )
        return None

    if properties is None:
        properties = {}

    try:
        # Create relationship
        result = client.create_relationship(
            start_node_id, end_node_id, relationship_type, properties
        )
        return result
    except Exception as e:
        logging.error(f"Error creating relationship: {str(e)}")
        return None


def import_json_ld_schema(
    schema_file_path: str, client: Optional[Neo4jClient] = None
) -> bool:
    """
    Imports a JSON-LD schema into the Knowledge Graph.

    Args:
        schema_file_path: Path to the JSON-LD schema file
        client: Neo4j client instance

    Returns:
        bool: True if the schema was successfully imported, False otherwise
    """
    import json
    import os

    if client is None:
        client = get_client()

    if not client.ensure_connected():
        logging.error("No connection to Neo4j database")
        return False

    if not os.path.isfile(schema_file_path):
        logging.error(f"Schema file not found: {schema_file_path}")
        return False

    try:
        # Load schema file
        with open(schema_file_path) as f:
            schema = json.load(f)

        # Import entity types
        if "entityTypes" in schema:
            for entity_type in schema["entityTypes"]:
                labels = [NodeLabel.ENTITY]
                if "@type" in entity_type and entity_type["@type"] == "rdfs:Class":
                    labels.append(entity_type["name"])

                properties = {
                    "id": entity_type["@id"],
                    "name": entity_type["name"],
                    "description": entity_type.get("description", ""),
                }

                if "subClassOf" in entity_type:
                    properties["subClassOf"] = entity_type["subClassOf"]

                create_entity_node(client, entity_type["@id"], labels, properties)

        # Import relationship types
        if "relationshipTypes" in schema:
            for relationship_type in schema["relationshipTypes"]:
                labels = [NodeLabel.RELATIONSHIP]
                if (
                    "@type" in relationship_type
                    and relationship_type["@type"] == "rdfs:Class"
                ):
                    labels.append(relationship_type["name"])

                properties = {
                    "id": relationship_type["@id"],
                    "name": relationship_type["name"],
                    "description": relationship_type.get("description", ""),
                }

                if "subClassOf" in relationship_type:
                    properties["subClassOf"] = relationship_type["subClassOf"]

                create_entity_node(client, relationship_type["@id"], labels, properties)

        # Import interface types
        if "interfaceTypes" in schema:
            for interface_type in schema["interfaceTypes"]:
                labels = [NodeLabel.INTERFACE]
                if (
                    "@type" in interface_type
                    and interface_type["@type"] == "rdfs:Class"
                ):
                    labels.append(interface_type["name"])

                properties = {
                    "id": interface_type["@id"],
                    "name": interface_type["name"],
                    "description": interface_type.get("description", ""),
                }

                if "subClassOf" in interface_type:
                    properties["subClassOf"] = interface_type["subClassOf"]

                create_entity_node(client, interface_type["@id"], labels, properties)

        # Import data flow types
        if "dataFlowTypes" in schema:
            for data_flow_type in schema["dataFlowTypes"]:
                labels = [NodeLabel.DATA_FLOW]
                if (
                    "@type" in data_flow_type
                    and data_flow_type["@type"] == "rdfs:Class"
                ):
                    labels.append(data_flow_type["name"])

                properties = {
                    "id": data_flow_type["@id"],
                    "name": data_flow_type["name"],
                    "description": data_flow_type.get("description", ""),
                }

                if "subClassOf" in data_flow_type:
                    properties["subClassOf"] = data_flow_type["subClassOf"]

                create_entity_node(client, data_flow_type["@id"], labels, properties)

        logging.success(f"Schema successfully imported from {schema_file_path}")
        return True
    except Exception as e:
        logging.error(f"Error importing schema: {str(e)}")
        return False


def import_json_ld_graph(
    graph_file_path: str, client: Optional[Neo4jClient] = None
) -> bool:
    """
    Imports a JSON-LD graph into the Knowledge Graph.

    Args:
        graph_file_path: Path to the JSON-LD graph file
        client: Neo4j client instance

    Returns:
        bool: True if the graph was successfully imported, False otherwise
    """
    import json
    import os

    if client is None:
        client = get_client()

    if not client.ensure_connected():
        logging.error("No connection to Neo4j database")
        return False

    if not os.path.isfile(graph_file_path):
        logging.error(f"Graph file not found: {graph_file_path}")
        return False

    try:
        # Load graph file
        with open(graph_file_path) as f:
            graph_data = json.load(f)

        # Node ID mapping for relationships
        node_id_map = {}

        # Import graph
        if "@graph" in graph_data:
            # First create all nodes
            for node in graph_data["@graph"]:
                if "@id" in node:
                    # Determine node type
                    node_type = node.get("@type", "Entity")
                    labels = [node_type]

                    # Extract properties
                    properties = {
                        k: v
                        for k, v in node.items()
                        if not k.startswith("@") and not isinstance(v, dict)
                    }

                    # Create node
                    created_node = create_entity_node(
                        client, node["@id"], labels, properties
                    )

                    if created_node:
                        # Save ID mapping
                        node_id_map[node["@id"]] = created_node["id"]

            # Then create all relationships
            for node in graph_data["@graph"]:
                if "@id" in node:
                    start_node_id = node_id_map.get(node["@id"])

                    if start_node_id:
                        # Extract relationships
                        for key, value in node.items():
                            if isinstance(value, dict) and "@id" in value:
                                end_node_id = node_id_map.get(value["@id"])

                                if end_node_id:
                                    # Create relationship
                                    create_relationship(
                                        client, start_node_id, end_node_id, key.upper()
                                    )

        logging.success(f"Graph successfully imported from {graph_file_path}")
        return True
    except Exception as e:
        logging.error(f"Error importing graph: {str(e)}")
        return False


def init_knowledge_graph(
    schema_file_path: Optional[str] = None,
    graph_file_path: Optional[str] = None,
    client: Optional[Neo4jClient] = None,
) -> bool:
    """
    Initializes the Knowledge Graph with schema and data.

    Args:
        schema_file_path: Path to the JSON-LD schema file
        graph_file_path: Path to the JSON-LD graph file
        client: Neo4j client instance

    Returns:
        bool: True if the Knowledge Graph was successfully initialized, False otherwise
    """
    if client is None:
        client = get_client()

    if not client.ensure_connected():
        logging.error("No connection to Neo4j database")
        return False

    # Create schema
    schema_manager = SchemaManager(client)
    if not schema_manager.create_schema():
        logging.error("Error creating schema")
        return False

    # Import schema if specified
    if schema_file_path:
        if not import_json_ld_schema(schema_file_path, client):
            logging.error(f"Error importing schema from {schema_file_path}")
            return False

    # Import graph if specified
    if graph_file_path:
        if not import_json_ld_graph(graph_file_path, client):
            logging.error(f"Error importing graph from {graph_file_path}")
            return False

    logging.success("Knowledge Graph successfully initialized")
    return True


logging.debug("Knowledge Graph schema module initialized")
