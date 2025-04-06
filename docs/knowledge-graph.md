# Knowledge Graph Integration

Die Knowledge Graph Integration ist ein zentraler Bestandteil des LOCAL-LLM-STACK-RELOADED, der als Wissensbasis für autonome AI Coding Agents dient. Diese Dokumentation beschreibt die Architektur, Funktionalität und Verwendung des Knowledge Graphs.

## Übersicht

Der Knowledge Graph verwendet neo4j, eine Graphdatenbank, um Informationen über den Migrationsprozess von Bash zu Python zu speichern und abzufragen. Er ermöglicht die Verfolgung von Migrationsentscheidungen, Code-Transformationen und die Beziehungen zwischen Original-Bash-Dateien und ihren Python-Äquivalenten.

## Architektur

Die Knowledge Graph Integration besteht aus mehreren Komponenten:

1. **neo4j-Datenbank**: Eine Graphdatenbank, die den Knowledge Graph speichert.
2. **Knowledge Graph Modul**: Ein Python-Modul, das die Integration mit der neo4j-Datenbank bereitstellt.
3. **CLI-Befehle**: Befehlszeilenschnittstelle für die Interaktion mit dem Knowledge Graph.
4. **API**: Programmierschnittstelle für die Integration in andere Komponenten.

### Datenmodell

Das Datenmodell des Knowledge Graphs basiert auf dem JSON-LD-Schema des ursprünglichen LOCAL-LLM-STACK und wurde um spezifische Entitäten und Beziehungen für den Migrationsprozess erweitert:

- **Entitäten**:
  - `BashOriginal`: Repräsentiert eine Original-Bash-Datei.
  - `PythonEquivalent`: Repräsentiert eine Python-Datei, die aus einer Bash-Datei migriert wurde.
  - `MigrationDecision`: Repräsentiert eine Entscheidung, die während des Migrationsprozesses getroffen wurde.
  - `CodeTransformation`: Repräsentiert eine Transformation von Bash-Code zu Python-Code.

- **Beziehungen**:
  - `EQUIVALENT_TO`: Verbindet eine Python-Datei mit ihrer entsprechenden Bash-Datei.
  - `DECISION_FOR`: Verbindet eine Migrationsentscheidung mit einer Datei.
  - `TRANSFORMED_FROM`: Verbindet eine Code-Transformation mit einer Bash-Datei.
  - `MIGRATED_TO`: Verbindet eine Code-Transformation mit einer Python-Datei.

## Funktionalität

Der Knowledge Graph bietet folgende Funktionen:

### Migrationsentscheidungen aufzeichnen

Während des Migrationsprozesses können Entscheidungen aufgezeichnet werden, einschließlich der Begründung, Alternativen und Auswirkungen. Diese Entscheidungen werden im Knowledge Graph gespeichert und können später abgefragt werden.

```python
from llm_stack.modules.knowledge_graph.module import get_module

kg_module = get_module()
kg_module.record_migration_decision(
    decision="Funktion X nach Python migrieren",
    rationale="Bessere Lesbarkeit und Wartbarkeit",
    bash_file_path="path/to/bash/file.sh",
    python_file_path="path/to/python/file.py"
)
```

### Code-Transformationen verfolgen

Code-Transformationen können aufgezeichnet werden, einschließlich des Codes vor und nach der Transformation. Diese Transformationen werden im Knowledge Graph gespeichert und können später abgefragt werden.

```python
kg_module.record_code_transformation(
    transformation_type="function_migration",
    before="bash_code_here",
    after="python_code_here",
    bash_file_path="path/to/bash/file.sh",
    python_file_path="path/to/python/file.py"
)
```

### Dateien verknüpfen

Bash- und Python-Dateien können im Knowledge Graph aufgezeichnet und miteinander verknüpft werden. Dies ermöglicht die Nachverfolgung des Migrationsprozesses auf Dateiebene.

```python
# Bash-Datei aufzeichnen
kg_module.record_bash_file(
    file_path="path/to/bash/file.sh",
    content="bash_content_here"
)

# Python-Datei aufzeichnen und mit Bash-Datei verknüpfen
kg_module.record_python_file(
    file_path="path/to/python/file.py",
    content="python_content_here",
    bash_file_path="path/to/bash/file.sh"
)
```

### Migrationsstatistiken

Der Knowledge Graph bietet Statistiken über den Migrationsprozess, einschließlich der Anzahl der migrierten Dateien, der Anzahl der Migrationsentscheidungen und der Anzahl der Code-Transformationen.

```python
stats = kg_module.get_migration_statistics()
print(f"Migration progress: {stats['migration_progress']:.2f}%")
```

## Verwendung

### Modul starten

Das Knowledge Graph Modul kann zusammen mit den Kernkomponenten gestartet werden:

```bash
llm start --with knowledge_graph
```

### CLI-Befehle

Die Knowledge Graph Integration bietet verschiedene CLI-Befehle für die Interaktion mit dem Knowledge Graph:

```bash
# Status des Knowledge Graph Moduls anzeigen
llm kg status

# Migrationsstatistiken anzeigen
llm kg stats

# Migrationsentscheidung aufzeichnen
llm kg record-decision --decision "Funktion X nach Python migrieren" --rationale "Bessere Lesbarkeit und Wartbarkeit" --bash-file "path/to/bash/file.sh" --python-file "path/to/python/file.py"

# Code-Transformation aufzeichnen
llm kg record-transformation --type "function_migration" --before "bash_code_here" --after "python_code_here" --bash-file "path/to/bash/file.sh" --python-file "path/to/python/file.py"

# Bash-Datei aufzeichnen
llm kg record-bash-file --file-path "path/to/bash/file.sh" --content-file "path/to/content/file.sh"

# Python-Datei aufzeichnen
llm kg record-python-file --file-path "path/to/python/file.py" --content-file "path/to/content/file.py" --bash-file "path/to/bash/file.sh"

# Migrationsentscheidungen abrufen
llm kg get-decisions --bash-file "path/to/bash/file.sh"

# Code-Transformationen abrufen
llm kg get-transformations --bash-file "path/to/bash/file.sh"

# Dateistatus abrufen
llm kg get-file-status --bash-file "path/to/bash/file.sh"
```

### Neo4j-Benutzeroberfläche

Die neo4j-Benutzeroberfläche ist unter http://localhost:7474 verfügbar. Die Standardanmeldedaten sind:

- Benutzername: neo4j
- Passwort: password

In der Benutzeroberfläche können Sie Cypher-Abfragen ausführen, um den Knowledge Graph zu erkunden und zu visualisieren.

#### Beispielabfragen

Alle Migrationsentscheidungen anzeigen:

```cypher
MATCH (d:MigrationDecision)
RETURN d
```

Alle Code-Transformationen für eine bestimmte Bash-Datei anzeigen:

```cypher
MATCH (t:CodeTransformation)-[:TRANSFORMED_FROM]->(b:BashOriginal)
WHERE b.file_path = "path/to/bash/file.sh"
RETURN t, b
```

Beziehungen zwischen Bash- und Python-Dateien anzeigen:

```cypher
MATCH (p:PythonEquivalent)-[:EQUIVALENT_TO]->(b:BashOriginal)
RETURN p, b
```

## Integration in den Migrationsprozess

Der Knowledge Graph ist ein integraler Bestandteil des Migrationsprozesses. Er wird verwendet, um Informationen über den Migrationsprozess zu speichern und abzufragen, die von autonomen AI Coding Agents genutzt werden können.

### Autonome AI Coding Agents

Autonome AI Coding Agents können den Knowledge Graph nutzen, um:

1. **Informationen über den Migrationsprozess zu erhalten**: Agents können Informationen über bereits migrierte Dateien, getroffene Entscheidungen und durchgeführte Transformationen abrufen.
2. **Migrationsentscheidungen zu treffen**: Agents können auf der Grundlage der im Knowledge Graph gespeicherten Informationen Entscheidungen treffen.
3. **Migrationsentscheidungen aufzuzeichnen**: Agents können ihre Entscheidungen im Knowledge Graph aufzeichnen, um sie für andere Agents und für die Nachverfolgung verfügbar zu machen.
4. **Code-Transformationen aufzuzeichnen**: Agents können die von ihnen durchgeführten Code-Transformationen im Knowledge Graph aufzeichnen.

### Boomerang-Methode

Die Boomerang-Methode für den iterativen Migrationsprozess nutzt den Knowledge Graph, um Informationen zwischen den Iterationen zu speichern und abzurufen:

1. **Planung**: Agents analysieren den Knowledge Graph, um den aktuellen Stand des Migrationsprozesses zu verstehen und die nächsten Schritte zu planen.
2. **Implementierung**: Agents führen die Migration durch und zeichnen ihre Entscheidungen und Transformationen im Knowledge Graph auf.
3. **Kontrolle**: Agents überprüfen die Ergebnisse der Migration und zeichnen Feedback im Knowledge Graph auf.
4. **Verbesserung**: Agents analysieren das Feedback im Knowledge Graph und verbessern den Migrationsprozess für die nächste Iteration.

## Konfiguration

Die Konfiguration des Knowledge Graph Moduls erfolgt über Umgebungsvariablen:

- `NEO4J_URI`: URI der neo4j-Datenbank (Standard: "bolt://localhost:7687")
- `NEO4J_USERNAME`: Benutzername für die neo4j-Datenbank (Standard: "neo4j")
- `NEO4J_PASSWORD`: Passwort für die neo4j-Datenbank (Standard: "password")
- `NEO4J_DATABASE`: Name der zu verwendenden Datenbank (Standard: "neo4j")
- `HOST_PORT_NEO4J_HTTP`: HTTP-Port für die neo4j-Benutzeroberfläche (Standard: 7474)
- `HOST_PORT_NEO4J_BOLT`: Bolt-Port für die neo4j-Datenbank (Standard: 7687)
- `HOST_PORT_NEO4J_HTTPS`: HTTPS-Port für die neo4j-Benutzeroberfläche (Standard: 7473)
- `NEO4J_CPU_LIMIT`: CPU-Limit für den neo4j-Container (Standard: 0.5)
- `NEO4J_MEMORY_LIMIT`: Speicherlimit für den neo4j-Container (Standard: 4G)
- `NEO4J_HEAP_INITIAL`: Anfängliche Heap-Größe für neo4j (Standard: 512M)
- `NEO4J_HEAP_MAX`: Maximale Heap-Größe für neo4j (Standard: 2G)
- `NEO4J_PAGECACHE`: Größe des Pagecache für neo4j (Standard: 512M)

Diese Variablen können in der Konfigurationsdatei `.env` gesetzt werden.