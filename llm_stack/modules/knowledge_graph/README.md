# Knowledge Graph Module

This module provides integration with neo4j for the LOCAL-LLM-STACK-RELOADED, serving as a central knowledge base for autonomous AI Coding Agents.

## Overview

The Knowledge Graph Module enables capturing, storing, and querying information about the migration process from Bash to Python. It tracks migration decisions, code transformations, and the relationships between original Bash files and their Python equivalents.

## Features

- **Record Migration Decisions**: Documents decisions made during the migration process, including rationales and alternatives.
- **Track Code Transformations**: Records changes to code, including before and after transformation states.
- **Link Bash and Python Files**: Establishes relationships between original Bash files and their Python equivalents.
- **Migration Statistics**: Provides insight into the progress of the migration process.
- **Query and Visualization**: Enables querying and visualization of the Knowledge Graph through the neo4j user interface.

## Architecture

The module consists of the following components:

1. **neo4j Database**: Stores the Knowledge Graph.
2. **Client Library**: Provides connection to the neo4j database and basic operations.
3. **Schema Manager**: Defines and manages the schema of the Knowledge Graph.
4. **Migration Tracker**: Records migration decisions and code transformations.
5. **CLI Commands**: Enables interaction with the Knowledge Graph via the command line.

## Usage

### Starting the Module

```bash
llm start --with knowledge_graph
```

### Checking Status

```bash
llm kg status
```

### Displaying Migration Statistics

```bash
llm kg stats
```

### Recording a Migration Decision

```bash
llm kg record-decision --decision "Migrate function X to Python" --rationale "Better readability and maintainability" --bash-file "path/to/bash/file.sh" --python-file "path/to/python/file.py"
```

### Recording a Code Transformation

```bash
llm kg record-transformation --type "function_migration" --before "bash_code_here" --after "python_code_here" --bash-file "path/to/bash/file.sh" --python-file "path/to/python/file.py"
```

### Recording a Bash File

```bash
llm kg record-bash-file --file-path "path/to/bash/file.sh" --content-file "path/to/content/file.sh"
```

### Recording a Python File

```bash
llm kg record-python-file --file-path "path/to/python/file.py" --content-file "path/to/content/file.py" --bash-file "path/to/bash/file.sh"
```

### Retrieving Migration Decisions

```bash
llm kg get-decisions --bash-file "path/to/bash/file.sh"
```

### Retrieving Code Transformations

```bash
llm kg get-transformations --bash-file "path/to/bash/file.sh"
```

### Retrieving File Status

```bash
llm kg get-file-status --bash-file "path/to/bash/file.sh"
```

## Programming with the Knowledge Graph

The module can also be used programmatically:

```python
from llm_stack.modules.knowledge_graph.module import get_module

# Get module instance
kg_module = get_module()

# Record migration decision
kg_module.record_migration_decision(
    decision="Migrate function X to Python",
    rationale="Better readability and maintainability",
    bash_file_path="path/to/bash/file.sh",
    python_file_path="path/to/python/file.py"
)

# Record code transformation
kg_module.record_code_transformation(
    transformation_type="function_migration",
    before="bash_code_here",
    after="python_code_here",
    bash_file_path="path/to/bash/file.sh",
    python_file_path="path/to/python/file.py"
)

# Get migration statistics
stats = kg_module.get_migration_statistics()
print(f"Migration progress: {stats['migration_progress']:.2f}%")
```

## Neo4j User Interface

The neo4j user interface is available at http://localhost:7474. The default credentials are:

- Username: neo4j
- Password: password

In the user interface, you can execute Cypher queries to explore and visualize the Knowledge Graph.

### Example Queries

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