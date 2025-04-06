"""
Datenmodelle für den LLM Stack Knowledge Graph.

Dieses Modul definiert Pydantic-Modelle für die Entitäten im Knowledge Graph,
die für die Validierung und Serialisierung/Deserialisierung verwendet werden.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field

from llm_stack.knowledge_graph.schema import NodeLabel, RelationshipType


class EntityType(str, Enum):
    """Typen für Entitäten im Knowledge Graph."""
    
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
    """Basismodell für alle Entitäten im Knowledge Graph."""
    
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    type: EntityType
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    def to_neo4j_properties(self) -> Dict:
        """
        Konvertiert das Modell in ein Dictionary für Neo4j.
        
        Returns:
            Dict: Neo4j-Eigenschaften
        """
        properties = self.dict(exclude={"type"})
        
        # Datetime-Objekte in Strings konvertieren
        if "created_at" in properties and properties["created_at"]:
            properties["created_at"] = properties["created_at"].isoformat()
        
        if "updated_at" in properties and properties["updated_at"]:
            properties["updated_at"] = properties["updated_at"].isoformat()
        
        return properties
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, self.type]


class Component(Entity):
    """Modell für Komponenten im Knowledge Graph."""
    
    type: EntityType = EntityType.COMPONENT
    file_path: Optional[str] = None
    version: Optional[str] = None
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.COMPONENT, self.type]


class Container(Component):
    """Modell für Container im Knowledge Graph."""
    
    type: EntityType = EntityType.CONTAINER
    image: Optional[str] = None
    ports: Optional[List[str]] = None
    environment: Optional[Dict[str, str]] = None
    volumes: Optional[List[str]] = None
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.COMPONENT, NodeLabel.CONTAINER]


class Script(Component):
    """Modell für Skripte im Knowledge Graph."""
    
    type: EntityType = EntityType.SCRIPT
    language: Optional[str] = None
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.COMPONENT, NodeLabel.SCRIPT]


class Library(Component):
    """Modell für Bibliotheken im Knowledge Graph."""
    
    type: EntityType = EntityType.LIBRARY
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.COMPONENT, NodeLabel.LIBRARY]


class Module(Component):
    """Modell für Module im Knowledge Graph."""
    
    type: EntityType = EntityType.MODULE
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.COMPONENT, NodeLabel.MODULE]


class Function(Entity):
    """Modell für Funktionen im Knowledge Graph."""
    
    type: EntityType = EntityType.FUNCTION
    file_path: str
    line_number: Optional[int] = None
    signature: Optional[str] = None
    return_type: Optional[str] = None
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.FUNCTION]


class Parameter(Entity):
    """Modell für Parameter im Knowledge Graph."""
    
    type: EntityType = EntityType.PARAMETER
    parameter_type: Optional[str] = None
    default_value: Optional[str] = None
    required: bool = False
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.PARAMETER]


class Variable(Entity):
    """Modell für Variablen im Knowledge Graph."""
    
    type: EntityType = EntityType.VARIABLE
    file_path: str
    line_number: Optional[int] = None
    variable_type: Optional[str] = None
    value: Optional[str] = None
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.VARIABLE]


class ConfigParam(Entity):
    """Modell für Konfigurationsparameter im Knowledge Graph."""
    
    type: EntityType = EntityType.CONFIG_PARAM
    default_value: Optional[str] = None
    required: bool = False
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.CONFIG_PARAM]


class Service(Entity):
    """Modell für Dienste im Knowledge Graph."""
    
    type: EntityType = EntityType.SERVICE
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.SERVICE]


class Interface(Entity):
    """Modell für Schnittstellen im Knowledge Graph."""
    
    type: EntityType = EntityType.INTERFACE
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.INTERFACE]


class API(Interface):
    """Modell für APIs im Knowledge Graph."""
    
    type: EntityType = EntityType.API
    base_url: Optional[str] = None
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.INTERFACE, NodeLabel.API]


class CLI(Interface):
    """Modell für CLIs im Knowledge Graph."""
    
    type: EntityType = EntityType.CLI
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.INTERFACE, NodeLabel.CLI]


class APIEndpoint(Entity):
    """Modell für API-Endpunkte im Knowledge Graph."""
    
    type: EntityType = EntityType.API_ENDPOINT
    path: str
    method: str
    parameters: Optional[List[Dict]] = None
    response: Optional[Dict] = None
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.API_ENDPOINT]


class CLICommand(Entity):
    """Modell für CLI-Befehle im Knowledge Graph."""
    
    type: EntityType = EntityType.CLI_COMMAND
    command: str
    parameters: Optional[List[Dict]] = None
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.CLI_COMMAND]


class DataFlow(Entity):
    """Modell für Datenflüsse im Knowledge Graph."""
    
    type: EntityType = EntityType.DATA_FLOW
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.DATA_FLOW]


class DataFlowStep(Entity):
    """Modell für Datenflussschritte im Knowledge Graph."""
    
    type: EntityType = EntityType.DATA_FLOW_STEP
    step_number: int
    data: Optional[Dict] = None
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.DATA_FLOW_STEP]


class MigrationDecision(Entity):
    """Modell für Migrationsentscheidungen im Knowledge Graph."""
    
    type: EntityType = EntityType.MIGRATION_DECISION
    decision: str
    rationale: str
    alternatives: Optional[List[str]] = None
    impact: Optional[str] = None
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.MIGRATION_DECISION]


class CodeTransformation(Entity):
    """Modell für Code-Transformationen im Knowledge Graph."""
    
    type: EntityType = EntityType.CODE_TRANSFORMATION
    transformation_type: str
    before: str
    after: str
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.CODE_TRANSFORMATION]


class BashOriginal(Entity):
    """Modell für Bash-Originale im Knowledge Graph."""
    
    type: EntityType = EntityType.BASH_ORIGINAL
    file_path: str
    content: str
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.BASH_ORIGINAL]


class PythonEquivalent(Entity):
    """Modell für Python-Äquivalente im Knowledge Graph."""
    
    type: EntityType = EntityType.PYTHON_EQUIVALENT
    file_path: str
    content: str
    
    def get_labels(self) -> List[str]:
        """
        Gibt die Labels für den Neo4j-Knoten zurück.
        
        Returns:
            List[str]: Neo4j-Labels
        """
        return [NodeLabel.ENTITY, NodeLabel.PYTHON_EQUIVALENT]


class Relationship(BaseModel):
    """Basismodell für alle Beziehungen im Knowledge Graph."""
    
    source_id: int
    target_id: int
    type: RelationshipType
    properties: Optional[Dict] = None
    
    def to_neo4j_properties(self) -> Dict:
        """
        Konvertiert das Modell in ein Dictionary für Neo4j.
        
        Returns:
            Dict: Neo4j-Eigenschaften
        """
        if self.properties:
            return self.properties
        return {}


# Modelltyp-Zuordnung
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
    EntityType.BASH_ORIGINAL: BashOriginal
}


def create_entity_model(entity_type: EntityType, **kwargs) -> Entity:
    """
    Erstellt ein Entitätsmodell basierend auf dem Typ.
    
    Args:
        entity_type: Typ der Entität
        **kwargs: Eigenschaften der Entität
        
    Returns:
        Entity: Entitätsmodell
    
    Raises:
        ValueError: Wenn der Entitätstyp nicht unterstützt wird
    """
    if entity_type not in ENTITY_TYPE_TO_MODEL:
        raise ValueError(f"Nicht unterstützter Entitätstyp: {entity_type}")
    
    model_class = ENTITY_TYPE_TO_MODEL[entity_type]
    return model_class(**kwargs)


def neo4j_to_entity_model(neo4j_node: Dict) -> Entity:
    """
    Konvertiert einen Neo4j-Knoten in ein Entitätsmodell.
    
    Args:
        neo4j_node: Neo4j-Knoten
        
    Returns:
        Entity: Entitätsmodell
    
    Raises:
        ValueError: Wenn der Knotentyp nicht unterstützt wird
    """
    # Labels extrahieren
    labels = neo4j_node.get("labels", [])
    
    # Entitätstyp bestimmen
    entity_type = None
    for label in labels:
        if label in EntityType.__members__:
            entity_type = EntityType(label)
            break
    
    if not entity_type:
        entity_type = EntityType.COMPONENT
    
    # Eigenschaften extrahieren
    properties = neo4j_node.get("properties", {})
    
    # Datetime-Strings in Datetime-Objekte konvertieren
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
    
    # Modell erstellen
    return create_entity_model(entity_type, **properties)