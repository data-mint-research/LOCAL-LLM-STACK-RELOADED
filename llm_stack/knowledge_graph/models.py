"""
Data models for the LLM Stack Knowledge Graph.

This module defines Pydantic models for entities in the Knowledge Graph,
which are used for validation and serialization/deserialization.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field

from llm_stack.knowledge_graph.schema import NodeLabel, RelationshipType


class EntityType(str, Enum):
    """Types for entities in the Knowledge Graph."""

    COMPONENT = "Component"
    CONTAINER = "Container"
    SCRIPT = "Script"
    LIBRARY = "Library"
    MODULE = "Module"
    FUNCTION = "Function"
    VARIABLE = "Variable"
    PARAMETER = "Parameter"
    CONFIG_PARAM = "ConfigParam"
    SERVICE = "Service"
    INTERFACE = "Interface"
    API = "API"
    CLI = "CLI"
    API_ENDPOINT = "APIEndpoint"
    CLI_COMMAND = "CLICommand"
    DATA_FLOW = "DataFlow"
    DATA_FLOW_STEP = "DataFlowStep"
    MIGRATION_DECISION = "MigrationDecision"
    CODE_TRANSFORMATION = "CodeTransformation"
    PYTHON_EQUIVALENT = "PythonEquivalent"
    BASH_ORIGINAL = "BashOriginal"


class Entity(BaseModel):
    """Base model for all entities in the Knowledge Graph."""

    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    type: EntityType
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)

    def _convert_datetime_to_iso(self, properties: Dict) -> Dict:
        """
        Convert datetime objects to ISO format strings.
        
        Args:
            properties: Dictionary containing properties
            
        Returns:
            Dict: Dictionary with datetime objects converted to strings
        """
        # Create a copy to avoid modifying the original
        result = properties.copy()
        
        # Convert datetime objects to ISO format strings
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
                
        return result

    def to_neo4j_properties(self) -> Dict:
        """
        Converts the model to a dictionary for Neo4j.

        Returns:
            Dict: Neo4j properties
        """
        # Exclude type as it's represented as a label
        properties = self.dict(exclude={"type"})
        
        # Convert datetime objects to strings
        return self._convert_datetime_to_iso(properties)

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        return [NodeLabel.ENTITY, self.type]


class Component(Entity):
    """Model for components in the Knowledge Graph."""

    type: EntityType = EntityType.COMPONENT
    file_path: Optional[str] = None
    version: Optional[str] = None

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Add the COMPONENT label to the base labels
        base_labels = super().get_labels()
        return base_labels[:1] + [NodeLabel.COMPONENT] + base_labels[1:]


class Container(Component):
    """Model for containers in the Knowledge Graph."""

    type: EntityType = EntityType.CONTAINER
    image: Optional[str] = None
    ports: Optional[List[str]] = None
    environment: Optional[Dict[str, str]] = None
    volumes: Optional[List[str]] = None

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with CONTAINER
        base_labels = super().get_labels()
        return base_labels[:2] + [NodeLabel.CONTAINER]


class Script(Component):
    """Model for scripts in the Knowledge Graph."""

    type: EntityType = EntityType.SCRIPT
    language: Optional[str] = None

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with SCRIPT
        base_labels = super().get_labels()
        return base_labels[:2] + [NodeLabel.SCRIPT]


class Library(Component):
    """Model for libraries in the Knowledge Graph."""

    type: EntityType = EntityType.LIBRARY

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with LIBRARY
        base_labels = super().get_labels()
        return base_labels[:2] + [NodeLabel.LIBRARY]


class Module(Component):
    """Model for modules in the Knowledge Graph."""

    type: EntityType = EntityType.MODULE

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with MODULE
        base_labels = super().get_labels()
        return base_labels[:2] + [NodeLabel.MODULE]


class Function(Entity):
    """Model for functions in the Knowledge Graph."""

    type: EntityType = EntityType.FUNCTION
    file_path: str
    line_number: Optional[int] = None
    signature: Optional[str] = None
    return_type: Optional[str] = None

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with FUNCTION
        base_labels = super().get_labels()
        return [base_labels[0], NodeLabel.FUNCTION]


class Parameter(Entity):
    """Model for parameters in the Knowledge Graph."""

    type: EntityType = EntityType.PARAMETER
    parameter_type: Optional[str] = None
    default_value: Optional[str] = None
    required: bool = False

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with PARAMETER
        base_labels = super().get_labels()
        return [base_labels[0], NodeLabel.PARAMETER]


class Variable(Entity):
    """Model for variables in the Knowledge Graph."""

    type: EntityType = EntityType.VARIABLE
    file_path: str
    line_number: Optional[int] = None
    variable_type: Optional[str] = None
    value: Optional[str] = None

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with VARIABLE
        base_labels = super().get_labels()
        return [base_labels[0], NodeLabel.VARIABLE]


class ConfigParam(Entity):
    """Model for configuration parameters in the Knowledge Graph."""

    type: EntityType = EntityType.CONFIG_PARAM
    default_value: Optional[str] = None
    required: bool = False

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with CONFIG_PARAM
        base_labels = super().get_labels()
        return [base_labels[0], NodeLabel.CONFIG_PARAM]


class Service(Entity):
    """Model for services in the Knowledge Graph."""

    type: EntityType = EntityType.SERVICE

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with SERVICE
        base_labels = super().get_labels()
        return [base_labels[0], NodeLabel.SERVICE]


class Interface(Entity):
    """Model for interfaces in the Knowledge Graph."""

    type: EntityType = EntityType.INTERFACE

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with INTERFACE
        base_labels = super().get_labels()
        return [base_labels[0], NodeLabel.INTERFACE]


class API(Interface):
    """Model for APIs in the Knowledge Graph."""

    type: EntityType = EntityType.API
    base_url: Optional[str] = None

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Add API label to the interface labels
        base_labels = super().get_labels()
        return base_labels + [NodeLabel.API]


class CLI(Interface):
    """Model for CLIs in the Knowledge Graph."""

    type: EntityType = EntityType.CLI

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Add CLI label to the interface labels
        base_labels = super().get_labels()
        return base_labels + [NodeLabel.CLI]


class APIEndpoint(Entity):
    """Model for API endpoints in the Knowledge Graph."""

    type: EntityType = EntityType.API_ENDPOINT
    path: str
    method: str
    parameters: Optional[List[Dict]] = None
    response: Optional[Dict] = None

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with API_ENDPOINT
        base_labels = super().get_labels()
        return [base_labels[0], NodeLabel.API_ENDPOINT]


class CLICommand(Entity):
    """Model for CLI commands in the Knowledge Graph."""

    type: EntityType = EntityType.CLI_COMMAND
    command: str
    parameters: Optional[List[Dict]] = None

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with CLI_COMMAND
        base_labels = super().get_labels()
        return [base_labels[0], NodeLabel.CLI_COMMAND]


class DataFlow(Entity):
    """Model for data flows in the Knowledge Graph."""

    type: EntityType = EntityType.DATA_FLOW

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with DATA_FLOW
        base_labels = super().get_labels()
        return [base_labels[0], NodeLabel.DATA_FLOW]


class DataFlowStep(Entity):
    """Model for data flow steps in the Knowledge Graph."""

    type: EntityType = EntityType.DATA_FLOW_STEP
    step_number: int
    data: Optional[Dict] = None

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with DATA_FLOW_STEP
        base_labels = super().get_labels()
        return [base_labels[0], NodeLabel.DATA_FLOW_STEP]


class MigrationDecision(Entity):
    """Model for migration decisions in the Knowledge Graph."""

    type: EntityType = EntityType.MIGRATION_DECISION
    decision: str
    rationale: str
    alternatives: Optional[List[str]] = None
    impact: Optional[str] = None

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with MIGRATION_DECISION
        base_labels = super().get_labels()
        return [base_labels[0], NodeLabel.MIGRATION_DECISION]


class CodeTransformation(Entity):
    """Model for code transformations in the Knowledge Graph."""

    type: EntityType = EntityType.CODE_TRANSFORMATION
    transformation_type: str
    before: str
    after: str

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with CODE_TRANSFORMATION
        base_labels = super().get_labels()
        return [base_labels[0], NodeLabel.CODE_TRANSFORMATION]


class BashOriginal(Entity):
    """Model for Bash originals in the Knowledge Graph."""

    type: EntityType = EntityType.BASH_ORIGINAL
    file_path: str
    content: str

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with BASH_ORIGINAL
        base_labels = super().get_labels()
        return [base_labels[0], NodeLabel.BASH_ORIGINAL]


class PythonEquivalent(Entity):
    """Model for Python equivalents in the Knowledge Graph."""

    type: EntityType = EntityType.PYTHON_EQUIVALENT
    file_path: str
    content: str

    def get_labels(self) -> List[str]:
        """
        Returns the labels for the Neo4j node.

        Returns:
            List[str]: Neo4j labels
        """
        # Replace the type label with PYTHON_EQUIVALENT
        base_labels = super().get_labels()
        return [base_labels[0], NodeLabel.PYTHON_EQUIVALENT]


class Relationship(BaseModel):
    """Base model for all relationships in the Knowledge Graph."""

    source_id: int
    target_id: int
    type: RelationshipType
    properties: Optional[Dict] = None

    def to_neo4j_properties(self) -> Dict:
        """
        Converts the model to a dictionary for Neo4j.

        Returns:
            Dict: Neo4j properties
        """
        # Return properties if they exist, otherwise an empty dict
        return self.properties or {}


# Model type mapping
ENTITY_TYPE_TO_MODEL = {
    EntityType.COMPONENT: Component,
    EntityType.CONTAINER: Container,
    EntityType.SCRIPT: Script,
    EntityType.LIBRARY: Library,
    EntityType.MODULE: Module,
    EntityType.FUNCTION: Function,
    EntityType.VARIABLE: Variable,
    EntityType.PARAMETER: Parameter,
    EntityType.CONFIG_PARAM: ConfigParam,
    EntityType.SERVICE: Service,
    EntityType.INTERFACE: Interface,
    EntityType.API: API,
    EntityType.CLI: CLI,
    EntityType.API_ENDPOINT: APIEndpoint,
    EntityType.CLI_COMMAND: CLICommand,
    EntityType.DATA_FLOW: DataFlow,
    EntityType.DATA_FLOW_STEP: DataFlowStep,
    EntityType.MIGRATION_DECISION: MigrationDecision,
    EntityType.CODE_TRANSFORMATION: CodeTransformation,
    EntityType.PYTHON_EQUIVALENT: PythonEquivalent,
    EntityType.BASH_ORIGINAL: BashOriginal,
}


def create_entity_model(entity_type: EntityType, **kwargs) -> Entity:
    """
    Creates an entity model based on the type.

    Args:
        entity_type: Type of entity
        **kwargs: Properties of the entity

    Returns:
        Entity: Entity model

    Raises:
        ValueError: If the entity type is not supported
    """
    if entity_type not in ENTITY_TYPE_TO_MODEL:
        raise ValueError(f"Unsupported entity type: {entity_type}")

    model_class = ENTITY_TYPE_TO_MODEL[entity_type]
    return model_class(**kwargs)


def neo4j_to_entity_model(neo4j_node: Dict) -> Entity:
    """
    Converts a Neo4j node to an entity model.

    Args:
        neo4j_node: Neo4j node

    Returns:
        Entity: Entity model

    Raises:
        ValueError: If the node type is not supported
    """
    # Extract labels
    labels = neo4j_node.get("labels", [])

    # Determine entity type
    entity_type = None
    for label in labels:
        if label in EntityType.__members__:
            entity_type = EntityType(label)
            break

    if not entity_type:
        entity_type = EntityType.COMPONENT

    # Extract properties
    properties = neo4j_node.get("properties", {})

    # Convert datetime strings to datetime objects
    if "created_at" in properties and isinstance(properties["created_at"], str):
        try:
            properties["created_at"] = datetime.fromisoformat(properties["created_at"])
        except ValueError:
            properties["created_at"] = datetime.now()

    if "updated_at" in properties and isinstance(properties["updated_at"], str):
        try:
            properties["updated_at"] = datetime.fromisoformat(properties["updated_at"])
        except ValueError:
            properties["updated_at"] = datetime.now()

    # Create model
    return create_entity_model(entity_type, **properties)
