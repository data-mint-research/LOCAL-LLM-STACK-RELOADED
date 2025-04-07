# Knowledge Graph Integration

The Knowledge Graph Integration is a central component of LOCAL-LLM-STACK-RELOADED, serving as a knowledge base for autonomous AI Coding Agents. This documentation describes the architecture, functionality, and usage of the Knowledge Graph.

## Overview

The Knowledge Graph uses neo4j, a graph database, to store and query information about the migration process from Bash to Python. It enables tracking of migration decisions, code transformations, and the relationships between original Bash files and their Python equivalents.

## Architecture

The Knowledge Graph Integration consists of several components:

1. **neo4j Database**: A graph database that stores the Knowledge Graph.
2. **Client Library**: Provides connection to the neo4j database and basic operations.
3. **Schema Manager**: Defines and manages the Knowledge Graph schema.
4. **Migration Tracker**: Records migration decisions and code transformations.
5. **CLI Commands**: Command-line interface for interacting with the Knowledge Graph.
6. **API**: Programming interface for integration with other components.

### Data Model

The Knowledge Graph's data model is based on the JSON-LD schema of the original LOCAL-LLM-STACK and has been extended with specific entities and relationships for the migration process:

- **Entities**:
  - `BashOriginal`: Represents an original Bash file.
  - `PythonEquivalent`: Represents a Python file that was migrated from a Bash file.
  - `MigrationDecision`: Represents a decision made during the migration process.
  - `CodeTransformation`: Represents a transformation from Bash code to Python code.

- **Relationships**:
  - `EQUIVALENT_TO`: Connects a Python file to its corresponding Bash file.
  - `DECISION_FOR`: Connects a migration decision to a file.
  - `TRANSFORMED_FROM`: Connects a code transformation to a Bash file.
  - `MIGRATED_TO`: Connects a code transformation to a Python file.

## Functionality

The Knowledge Graph provides the following functions:

### Recording Migration Decisions

During the migration process, decisions can be recorded, including rationale, alternatives, and impacts. These decisions are stored in the Knowledge Graph and can be queried later.

```python
from llm_stack.modules.knowledge_graph.module import get_module

kg_module = get_module()
kg_module.record_migration_decision(
    decision="Migrate function X to Python",
    rationale="Better readability and maintainability",
    bash_file_path="path/to/bash/file.sh",
    python_file_path="path/to/python/file.py"
)
```

### Tracking Code Transformations

Code transformations can be recorded, including the code before and after the transformation. These transformations are stored in the Knowledge Graph and can be queried later.

```python
kg_module.record_code_transformation(
    transformation_type="function_migration",
    before="bash_code_here",
    after="python_code_here",
    bash_file_path="path/to/bash/file.sh",
    python_file_path="path/to/python/file.py"
)
```

### Linking Files

Bash and Python files can be recorded in the Knowledge Graph and linked to each other. This enables tracking of the migration process at the file level.

```python
# Record Bash file
kg_module.record_bash_file(
    file_path="path/to/bash/file.sh",
    content="bash_content_here"
)

# Record Python file and link with Bash file
kg_module.record_python_file(
    file_path="path/to/python/file.py",
    content="python_content_here",
    bash_file_path="path/to/bash/file.sh"
)
```

### Migration Statistics

The Knowledge Graph provides statistics about the migration process, including the number of migrated files, the number of migration decisions, and the number of code transformations.

```python
stats = kg_module.get_migration_statistics()
print(f"Migration progress: {stats['migration_progress']:.2f}%")
```

## Usage

### Starting the Module

The Knowledge Graph module can be started together with the core components:

```bash
llm start --with knowledge_graph
```

### CLI Commands

The Knowledge Graph Integration provides various CLI commands for interacting with the Knowledge Graph:

```bash
# Display status of the Knowledge Graph module
llm kg status

# Display migration statistics
llm kg stats

# Record migration decision
llm kg record-decision --decision "Migrate function X to Python" --rationale "Better readability and maintainability" --bash-file "path/to/bash/file.sh" --python-file "path/to/python/file.py"

# Record code transformation
llm kg record-transformation --type "function_migration" --before "bash_code_here" --after "python_code_here" --bash-file "path/to/bash/file.sh" --python-file "path/to/python/file.py"

# Record Bash file
llm kg record-bash-file --file-path "path/to/bash/file.sh" --content-file "path/to/content/file.sh"

# Record Python file
llm kg record-python-file --file-path "path/to/python/file.py" --content-file "path/to/content/file.py" --bash-file "path/to/bash/file.sh"

# Retrieve migration decisions
llm kg get-decisions --bash-file "path/to/bash/file.sh"

# Retrieve code transformations
llm kg get-transformations --bash-file "path/to/bash/file.sh"

# Retrieve file status
llm kg get-file-status --bash-file "path/to/bash/file.sh"
```

### Neo4j User Interface

The neo4j user interface is available at http://localhost:7474. The default credentials are:

- Username: neo4j
- Password: password

In the user interface, you can execute Cypher queries to explore and visualize the Knowledge Graph.

#### Example Queries

Display all migration decisions:

```cypher
MATCH (d:MigrationDecision)
RETURN d
```

Display all code transformations for a specific Bash file:

```cypher
MATCH (t:CodeTransformation)-[:TRANSFORMED_FROM]->(b:BashOriginal)
WHERE b.file_path = "path/to/bash/file.sh"
RETURN t, b
```

Display relationships between Bash and Python files:

```cypher
MATCH (p:PythonEquivalent)-[:EQUIVALENT_TO]->(b:BashOriginal)
RETURN p, b
```

## Integration with Autonomous AI Coding Agents

The Knowledge Graph is an integral part of the migration process. It is used to store and query information about the migration process that can be utilized by autonomous AI Coding Agents.

### Autonomous AI Coding Agents

Autonomous AI Coding Agents can use the Knowledge Graph to:

1. **Obtain information about the migration process**: Agents can retrieve information about already migrated files, decisions made, and transformations performed.
2. **Make migration decisions**: Agents can make decisions based on the information stored in the Knowledge Graph.
3. **Record migration decisions**: Agents can record their decisions in the Knowledge Graph to make them available to other agents and for tracking.
4. **Record code transformations**: Agents can record the code transformations they perform in the Knowledge Graph.

### Boomerang Method

The Boomerang Method for the iterative migration process uses the Knowledge Graph to store and retrieve information between iterations:

1. **Planning**: Agents analyze the Knowledge Graph to understand the current state of the migration process and plan the next steps.
2. **Implementation**: Agents perform the migration and record their decisions and transformations in the Knowledge Graph.
3. **Control**: Agents review the results of the migration and record feedback in the Knowledge Graph.
4. **Improvement**: Agents analyze the feedback in the Knowledge Graph and improve the migration process for the next iteration.

## Configuration

The configuration of the Knowledge Graph module is done via environment variables:

- `NEO4J_URI`: URI of the neo4j database (default: "bolt://localhost:7687")
- `NEO4J_USERNAME`: Username for the neo4j database (default: "neo4j")
- `NEO4J_PASSWORD`: Password for the neo4j database (default: "password")
- `NEO4J_DATABASE`: Name of the database to use (default: "neo4j")
- `HOST_PORT_NEO4J_HTTP`: HTTP port for the neo4j user interface (default: 7474)
- `HOST_PORT_NEO4J_BOLT`: Bolt port for the neo4j database (default: 7687)
- `HOST_PORT_NEO4J_HTTPS`: HTTPS port for the neo4j user interface (default: 7473)
- `NEO4J_CPU_LIMIT`: CPU limit for the neo4j container (default: 0.5)
- `NEO4J_MEMORY_LIMIT`: Memory limit for the neo4j container (default: 4G)
- `NEO4J_HEAP_INITIAL`: Initial heap size for neo4j (default: 512M)
- `NEO4J_HEAP_MAX`: Maximum heap size for neo4j (default: 2G)
- `NEO4J_PAGECACHE`: Pagecache size for neo4j (default: 512M)

These variables can be set in the `.env` configuration file.

## Performance Considerations

The Knowledge Graph is designed to be efficient and scalable. However, when working with large codebases, consider the following:

1. **Batch Operations**: When recording multiple files or transformations, use batch operations where possible.
2. **Query Optimization**: Use specific queries rather than retrieving all data and filtering client-side.
3. **Index Usage**: The schema includes indexes on commonly queried properties for better performance.
4. **Memory Configuration**: Adjust the neo4j memory settings based on the size of your Knowledge Graph.

## Integration with Other Components

The Knowledge Graph integrates with other components of the LOCAL-LLM-STACK-RELOADED:

1. **Code Quality Module**: Records code quality metrics and improvements.
2. **CLI**: Provides commands for interacting with the Knowledge Graph.
3. **Core Utilities**: Uses core utilities for configuration and error handling.