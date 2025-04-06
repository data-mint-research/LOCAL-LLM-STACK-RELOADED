# Knowledge Graph Modul

Dieses Modul stellt eine Integration mit neo4j für den LOCAL-LLM-STACK bereit, die als zentrale Wissensbasis für autonome AI Coding Agents dient.

## Übersicht

Das Knowledge Graph Modul ermöglicht die Erfassung, Speicherung und Abfrage von Informationen über den Migrationsprozess von Bash zu Python. Es verfolgt Migrationsentscheidungen, Code-Transformationen und die Beziehungen zwischen Original-Bash-Dateien und ihren Python-Äquivalenten.

## Funktionen

- **Migrationsentscheidungen aufzeichnen**: Dokumentiert Entscheidungen, die während des Migrationsprozesses getroffen werden, einschließlich Begründungen und Alternativen.
- **Code-Transformationen verfolgen**: Zeichnet Änderungen am Code auf, einschließlich des Codes vor und nach der Transformation.
- **Bash- und Python-Dateien verknüpfen**: Stellt Beziehungen zwischen Original-Bash-Dateien und ihren Python-Äquivalenten her.
- **Migrationsstatistiken**: Bietet Einblick in den Fortschritt des Migrationsprozesses.
- **Abfragen und Visualisierung**: Ermöglicht die Abfrage und Visualisierung des Knowledge Graphs über die neo4j-Benutzeroberfläche.

## Architektur

Das Modul besteht aus folgenden Komponenten:

1. **neo4j-Datenbank**: Speichert den Knowledge Graph.
2. **Client-Bibliothek**: Stellt eine Verbindung zur neo4j-Datenbank her und bietet grundlegende Operationen.
3. **Schema-Manager**: Definiert und verwaltet das Schema des Knowledge Graphs.
4. **Migrations-Tracker**: Zeichnet Migrationsentscheidungen und Code-Transformationen auf.
5. **CLI-Befehle**: Ermöglicht die Interaktion mit dem Knowledge Graph über die Befehlszeile.

## Verwendung

### Modul starten

```bash
llm start --with knowledge_graph
```

### Status prüfen

```bash
llm kg status
```

### Migrationsstatistiken anzeigen

```bash
llm kg stats
```

### Migrationsentscheidung aufzeichnen

```bash
llm kg record-decision --decision "Funktion X nach Python migrieren" --rationale "Bessere Lesbarkeit und Wartbarkeit" --bash-file "path/to/bash/file.sh" --python-file "path/to/python/file.py"
```

### Code-Transformation aufzeichnen

```bash
llm kg record-transformation --type "function_migration" --before "bash_code_here" --after "python_code_here" --bash-file "path/to/bash/file.sh" --python-file "path/to/python/file.py"
```

### Bash-Datei aufzeichnen

```bash
llm kg record-bash-file --file-path "path/to/bash/file.sh" --content-file "path/to/content/file.sh"
```

### Python-Datei aufzeichnen

```bash
llm kg record-python-file --file-path "path/to/python/file.py" --content-file "path/to/content/file.py" --bash-file "path/to/bash/file.sh"
```

### Migrationsentscheidungen abrufen

```bash
llm kg get-decisions --bash-file "path/to/bash/file.sh"
```

### Code-Transformationen abrufen

```bash
llm kg get-transformations --bash-file "path/to/bash/file.sh"
```

### Dateistatus abrufen

```bash
llm kg get-file-status --bash-file "path/to/bash/file.sh"
```

## Programmierung mit dem Knowledge Graph

Das Modul kann auch programmatisch verwendet werden:

```python
from llm_stack.modules.knowledge_graph.module import get_module

# Modul-Instanz abrufen
kg_module = get_module()

# Migrationsentscheidung aufzeichnen
kg_module.record_migration_decision(
    decision="Funktion X nach Python migrieren",
    rationale="Bessere Lesbarkeit und Wartbarkeit",
    bash_file_path="path/to/bash/file.sh",
    python_file_path="path/to/python/file.py"
)

# Code-Transformation aufzeichnen
kg_module.record_code_transformation(
    transformation_type="function_migration",
    before="bash_code_here",
    after="python_code_here",
    bash_file_path="path/to/bash/file.sh",
    python_file_path="path/to/python/file.py"
)

# Migrationsstatistiken abrufen
stats = kg_module.get_migration_statistics()
print(f"Migration progress: {stats['migration_progress']:.2f}%")
```

## Neo4j-Benutzeroberfläche

Die neo4j-Benutzeroberfläche ist unter http://localhost:7474 verfügbar. Die Standardanmeldedaten sind:

- Benutzername: neo4j
- Passwort: password

In der Benutzeroberfläche können Sie Cypher-Abfragen ausführen, um den Knowledge Graph zu erkunden und zu visualisieren.

### Beispielabfragen

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