"""
Record the creation of the style guide in the knowledge graph.

This script records the creation of the style guide as a migration decision
in the knowledge graph, documenting the rationale and purpose.
"""

import os
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

# Import the knowledge graph module
try:
    from llm_stack.modules.knowledge_graph.module import get_module as get_kg_module
except ImportError:
    print("Could not import knowledge graph module. Make sure it's installed.")
    sys.exit(1)


def main():
    """Record the style guide creation in the knowledge graph."""
    try:
        # Get the knowledge graph module
        kg_module = get_kg_module()

        # Record the creation of the style guide as a migration decision
        result = kg_module.record_migration_decision(
            decision="Create a comprehensive style guide for the project",
            rationale=(
                "To document coding standards and conventions based on PEP 8 and "
                "Google docstring style, ensuring consistency across the codebase "
                "and facilitating code quality improvements."
            ),
            bash_file_path=None,  # Not applicable for this decision
            python_file_path="docs/style-guide.md",
            alternatives=[
                "Use an existing style guide without customization",
                "Implement style enforcement without documentation"
            ]
        )

        if result:
            print("Style guide creation successfully recorded in the knowledge graph")
        else:
            print("Error recording style guide creation in the knowledge graph")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()