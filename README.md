# LOCAL-LLM-STACK-RELOADED

Eine moderne, wartbare und performante Python-Implementierung des LOCAL-LLM-STACK.

## Übersicht

LOCAL-LLM-STACK-RELOADED ist eine vollständige Migration des ursprünglichen Bash-basierten LOCAL-LLM-STACK zu einer Python-Codebasis. Diese Migration behält die gesamte Funktionalität des Originals bei, während sie moderne Python-Best-Practices und -Design-Patterns implementiert.

Der Stack ermöglicht die einfache Bereitstellung und Verwaltung lokaler Large Language Model (LLM) Dienste mit Docker-Containern.

## Hauptmerkmale

- **Vollständige Python-Implementierung**: Ersetzt Bash-Skripte durch strukturierten, wartbaren Python-Code
- **Modulare Architektur**: Klar definierte Komponenten mit sauberen Schnittstellen
- **Robuste Fehlerbehandlung**: Umfassende Fehlerbehandlungsstrategien in allen Codebereichen
- **Integrierter neo4j-Knowledge Graph**: Zentrale Wissensbasis für autonome AI Coding Agents
- **Docker-basierte Dienste**: Einfache Bereitstellung und Verwaltung von LLM-Diensten
- **Erweiterbare Module**: Monitoring, Skalierung, Sicherheit und mehr

## Komponenten

- **Core**: Grundlegende Dienste (Ollama, LibreChat, MongoDB, Meilisearch)
- **Module**: Erweiterbare Funktionalitäten (Monitoring, Skalierung, Sicherheit, Snapshot)
- **Tools**: Hilfsprogramme für Dokumentation, Entitätsextraktion, Knowledge-Graph-Generierung
- **Knowledge Graph**: Neo4j-basierte Wissensbasis für Systemzusammenhänge und Migrationsentscheidungen

## Erste Schritte

```bash
# Repository klonen
git clone https://github.com/username/LOCAL-LLM-STACK-RELOADED.git
cd LOCAL-LLM-STACK-RELOADED

# Abhängigkeiten installieren
pip install -e .

# Stack starten
llm start
```

## Dokumentation

Ausführliche Dokumentation finden Sie im [docs](./docs) Verzeichnis.

## Lizenz

Dieses Projekt steht unter der gleichen Lizenz wie das Original-Repository.