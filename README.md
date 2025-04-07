# LOCAL-LLM-STACK-RELOADED

A modern, maintainable, and performant Python implementation of the LOCAL-LLM-STACK.

## Overview

LOCAL-LLM-STACK-RELOADED is a complete migration of the original Bash-based LOCAL-LLM-STACK to a Python codebase. This migration retains all the functionality of the original while implementing modern Python best practices and design patterns.

The stack enables easy deployment and management of local Large Language Model (LLM) services using Docker containers.

## Key Features

- **Complete Python Implementation**: Replaces Bash scripts with structured, maintainable Python code
- **Modular Architecture**: Clearly defined components with clean interfaces
- **Robust Error Handling**: Comprehensive error handling strategies in all code areas
- **Integrated neo4j Knowledge Graph**: Central knowledge base for autonomous AI Coding Agents
- **Docker-based Services**: Easy deployment and management of LLM services
- **Extensible Modules**: Monitoring, Scaling, Security, and more
- **Code Quality Integration**: Built-in tools for maintaining code quality
- **Single Responsibility Principle**: Refactored components follow SRP for better maintainability
- **Optimized Performance**: Improved resource management and performance

## Components

- **Core**: Basic services (Ollama, LibreChat, MongoDB, Meilisearch)
- **Modules**: Extensible functionalities (Monitoring, Scaling, Security, Snapshot)
- **Tools**: Utilities for documentation, entity extraction, knowledge graph generation
- **Knowledge Graph**: Neo4j-based knowledge base for system relationships and migration decisions
- **Code Quality**: Tools for maintaining code quality and adherence to best practices

## Project Structure

```
LOCAL-LLM-STACK-RELOADED/
├── docs/                  # Documentation
├── llm_stack/             # Main package
│   ├── cli.py             # Command-line interface
│   ├── cli_commands/      # CLI command implementations
│   ├── code_quality/      # Code quality tools
│   ├── core/              # Core functionality
│   ├── knowledge_graph/   # Knowledge graph integration
│   ├── modules/           # Extensible modules
│   └── tools/             # Utility tools
├── docker/                # Docker configurations
├── tests/                 # Test suite
│   ├── fixtures/          # Test fixtures
│   ├── integration/       # Integration tests
│   └── unit/              # Unit tests
└── examples/              # Example code
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/username/LOCAL-LLM-STACK-RELOADED.git
cd LOCAL-LLM-STACK-RELOADED

# Install dependencies
pip install -e .

# Start stack
llm start
```

### Basic Usage

```bash
# Start the stack with all components
llm start

# Start with specific modules
llm start --with knowledge_graph

# Check status
llm status

# Stop the stack
llm stop
```

## Documentation

Detailed documentation can be found in the [docs](./docs) directory:

- [Architecture](./docs/architecture.md)
- [Configuration](./docs/configuration.md)
- [Getting Started](./docs/getting-started.md)
- [Knowledge Graph](./docs/knowledge-graph.md)
- [API Documentation](./docs/api/README.md)
- [Code Quality](./docs/code-quality-integration-plan.md)

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your code follows the project's style guide and passes all tests.

## License

This project is licensed under the same license as the original repository.