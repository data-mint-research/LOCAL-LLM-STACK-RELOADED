"""
Updates the knowledge graph with code structure from Python files.

This script scans Python files in the codebase, extracts high-level structure information
(modules, classes, functions/methods, and their relationships), and updates the knowledge graph.
"""

import ast
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from llm_stack.core import error, logging, system
from llm_stack.knowledge_graph.client import get_client
from llm_stack.knowledge_graph.schema import NodeLabel, RelationshipType


class CodeVisitor(ast.NodeVisitor):
    """AST visitor that extracts code structure information."""

    def __init__(self, file_path: str):
        """
        Initialize the visitor.

        Args:
            file_path: Path to the Python file being parsed
        """
        self.file_path = file_path
        self.module_name = os.path.splitext(os.path.basename(file_path))[0]
        self.imports = []
        self.classes = []
        self.functions = []
        self.method_calls = []
        self.current_class = None

    def visit_Import(self, node: ast.Import) -> None:
        """Extract import statements."""
        for name in node.names:
            self.imports.append({"name": name.name, "alias": name.asname})
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Extract from import statements."""
        module = node.module or ""
        for name in node.names:
            self.imports.append(
                {
                    "name": f"{module}.{name.name}" if module else name.name,
                    "alias": name.asname,
                    "level": node.level,
                }
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Extract class definitions."""
        # Save previous class context if we're nested
        prev_class = self.current_class

        # Get base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{self._get_attribute_full_name(base)}")

        # Create class info
        class_info = {
            "name": node.name,
            "bases": bases,
            "docstring": ast.get_docstring(node),
            "methods": [],
            "line_number": node.lineno,
        }

        self.classes.append(class_info)
        self.current_class = class_info

        # Visit class body
        self.generic_visit(node)

        # Restore previous class context
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Extract function and method definitions."""
        # Get parameters
        params = []
        for arg in node.args.args:
            param = {"name": arg.arg}
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    param["type"] = arg.annotation.id
                elif isinstance(arg.annotation, ast.Attribute):
                    param["type"] = self._get_attribute_full_name(arg.annotation)
                elif isinstance(arg.annotation, ast.Subscript):
                    param["type"] = self._get_subscript_name(arg.annotation)
            params.append(param)

        # Get return type
        return_type = None
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return_type = node.returns.id
            elif isinstance(node.returns, ast.Attribute):
                return_type = self._get_attribute_full_name(node.returns)
            elif isinstance(node.returns, ast.Subscript):
                return_type = self._get_subscript_name(node.returns)

        # Create function info
        func_info = {
            "name": node.name,
            "params": params,
            "return_type": return_type,
            "docstring": ast.get_docstring(node),
            "line_number": node.lineno,
            "is_method": self.current_class is not None,
            "class_name": self.current_class["name"] if self.current_class else None,
        }

        # Add to appropriate collection
        if self.current_class:
            self.current_class["methods"].append(func_info)
        else:
            self.functions.append(func_info)

        # Visit function body
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Extract function and method calls."""
        func_name = None

        # Get the function name being called
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = self._get_attribute_full_name(node.func)

        if func_name:
            call_info = {
                "name": func_name,
                "line_number": node.lineno,
                "in_class": self.current_class["name"] if self.current_class else None,
            }
            self.method_calls.append(call_info)

        self.generic_visit(node)

    def _get_attribute_full_name(self, node: ast.Attribute) -> str:
        """Get the full name of an attribute (e.g., module.submodule.name)."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_full_name(node.value)}.{node.attr}"
        return node.attr

    def _get_subscript_name(self, node: ast.Subscript) -> str:
        """Get the name of a subscript (e.g., List[str])."""
        if isinstance(node.value, ast.Name):
            value_name = node.value.id
        elif isinstance(node.value, ast.Attribute):
            value_name = self._get_attribute_full_name(node.value)
        else:
            value_name = "Unknown"

        # For Python 3.8+
        if isinstance(node.slice, ast.Index):
            if isinstance(node.slice.value, ast.Name):
                slice_name = node.slice.value.id
            elif isinstance(node.slice.value, ast.Attribute):
                slice_name = self._get_attribute_full_name(node.slice.value)
            else:
                slice_name = "Any"
        else:
            slice_name = "Any"

        return f"{value_name}[{slice_name}]"


def parse_python_file(file_path: str) -> Dict[str, Any]:
    """
    Parse a Python file and extract its structure.

    Args:
        file_path: Path to the Python file

    Returns:
        Dict[str, Any]: Dictionary containing the file's structure
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Parse the file
        tree = ast.parse(content)
        visitor = CodeVisitor(file_path)
        visitor.visit(tree)

        # Get module docstring
        module_docstring = ast.get_docstring(tree)

        return {
            "file_path": file_path,
            "module_name": visitor.module_name,
            "docstring": module_docstring,
            "imports": visitor.imports,
            "classes": visitor.classes,
            "functions": visitor.functions,
            "method_calls": visitor.method_calls,
        }
    except Exception as e:
        logging.error(f"Error parsing {file_path}: {str(e)}")
        return {
            "file_path": file_path,
            "module_name": os.path.splitext(os.path.basename(file_path))[0],
            "error": str(e),
        }


def find_python_files(
    root_dir: str, exclude_dirs: Optional[List[str]] = None
) -> List[str]:
    """
    Find all Python files in the given directory.

    Args:
        root_dir: Root directory to search in
        exclude_dirs: List of directories to exclude

    Returns:
        List[str]: List of Python file paths
    """
    if exclude_dirs is None:
        exclude_dirs = ["venv", "env", ".venv", ".env", "__pycache__", ".git"]

    python_files = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

        for filename in filenames:
            if filename.endswith(".py"):
                python_files.append(os.path.join(dirpath, filename))

    return python_files


def extract_code_structure(root_dir: str) -> Dict[str, Any]:
    """
    Extract code structure from all Python files in the given directory.

    Args:
        root_dir: Root directory to search in

    Returns:
        Dict[str, Any]: Dictionary containing the code structure
    """
    logging.info("Extracting code structure from Python files...")

    # Find all Python files
    python_files = find_python_files(root_dir)
    logging.info(f"Found {len(python_files)} Python files")

    # Parse each file
    modules = []
    for file_path in python_files:
        logging.info(f"Parsing {file_path}")
        module_info = parse_python_file(file_path)
        modules.append(module_info)

    return {"modules": modules}


def create_module_nodes(code_structure: Dict[str, Any], entities_dir: str) -> None:
    """
    Create module nodes from code structure.

    Args:
        code_structure: Code structure dictionary
        entities_dir: Directory to store entity JSON files
    """
    logging.info("Creating module nodes...")

    # Create components directory if it doesn't exist
    os.makedirs(entities_dir, exist_ok=True)

    # Create components file path
    components_file = os.path.join(entities_dir, "components.json")

    # Load existing components if the file exists
    existing_components = []
    if os.path.isfile(components_file):
        try:
            with open(components_file) as f:
                existing_components = json.load(f)
        except Exception as e:
            logging.error(f"Error loading existing components: {str(e)}")

    # Create module nodes
    module_nodes = []
    for module in code_structure["modules"]:
        module_id = f"llm:{module['module_name']}"

        # Check if module already exists
        existing_module = next(
            (c for c in existing_components if c.get("@id") == module_id), None
        )

        if existing_module:
            # Update existing module
            existing_module["description"] = module.get("docstring", "")
            existing_module["filePath"] = module.get("file_path", "")
            module_nodes.append(existing_module)
        else:
            # Create new module
            module_node = {
                "@id": module_id,
                "@type": "llm:Module",
                "name": module["module_name"],
                "description": module.get("docstring", ""),
                "filePath": module.get("file_path", ""),
            }
            module_nodes.append(module_node)

    # Merge with existing components
    # Keep existing components that are not modules
    non_module_components = [
        c for c in existing_components if "llm:Module" not in c.get("@type", "")
    ]
    all_components = non_module_components + module_nodes

    # Write to file
    with open(components_file, "w") as f:
        json.dump(all_components, f, indent=2)

    logging.success(f"Created {len(module_nodes)} module nodes")


def create_class_nodes(code_structure: Dict[str, Any], entities_dir: str) -> None:
    """
    Create class nodes from code structure.

    Args:
        code_structure: Code structure dictionary
        entities_dir: Directory to store entity JSON files
    """
    logging.info("Creating class nodes...")

    # Create components directory if it doesn't exist
    os.makedirs(entities_dir, exist_ok=True)

    # Create components file path
    components_file = os.path.join(entities_dir, "components.json")

    # Load existing components if the file exists
    existing_components = []
    if os.path.isfile(components_file):
        try:
            with open(components_file) as f:
                existing_components = json.load(f)
        except Exception as e:
            logging.error(f"Error loading existing components: {str(e)}")

    # Create class nodes
    class_nodes = []
    for module in code_structure["modules"]:
        for class_info in module.get("classes", []):
            class_id = f"llm:{module['module_name']}.{class_info['name']}"

            # Check if class already exists
            existing_class = next(
                (c for c in existing_components if c.get("@id") == class_id), None
            )

            if existing_class:
                # Update existing class
                existing_class["description"] = class_info.get("docstring", "")
                existing_class["filePath"] = module.get("file_path", "")
                existing_class["lineNumber"] = class_info.get("line_number", 0)
                class_nodes.append(existing_class)
            else:
                # Create new class
                class_node = {
                    "@id": class_id,
                    "@type": "llm:Component",
                    "name": class_info["name"],
                    "description": class_info.get("docstring", ""),
                    "filePath": module.get("file_path", ""),
                    "lineNumber": class_info.get("line_number", 0),
                }
                class_nodes.append(class_node)

    # Merge with existing components
    # Keep existing components that are not these classes
    class_ids = [c["@id"] for c in class_nodes]
    other_components = [c for c in existing_components if c.get("@id") not in class_ids]
    all_components = other_components + class_nodes

    # Write to file
    with open(components_file, "w") as f:
        json.dump(all_components, f, indent=2)

    logging.success(f"Created {len(class_nodes)} class nodes")


def create_function_nodes(code_structure: Dict[str, Any], entities_dir: str) -> None:
    """
    Create function nodes from code structure.

    Args:
        code_structure: Code structure dictionary
        entities_dir: Directory to store entity JSON files
    """
    logging.info("Creating function nodes...")

    # Create functions directory if it doesn't exist
    os.makedirs(entities_dir, exist_ok=True)

    # Create functions file path
    functions_file = os.path.join(entities_dir, "functions.json")

    # Load existing functions if the file exists
    existing_functions = []
    if os.path.isfile(functions_file):
        try:
            with open(functions_file) as f:
                existing_functions = json.load(f)
        except Exception as e:
            logging.error(f"Error loading existing functions: {str(e)}")

    # Create function nodes
    function_nodes = []
    for module in code_structure["modules"]:
        # Add standalone functions
        for func_info in module.get("functions", []):
            func_id = f"llm:{module['module_name']}.{func_info['name']}"

            # Check if function already exists
            existing_func = next(
                (f for f in existing_functions if f.get("@id") == func_id), None
            )

            if existing_func:
                # Update existing function
                existing_func["description"] = func_info.get("docstring", "")
                existing_func["filePath"] = module.get("file_path", "")
                existing_func["lineNumber"] = func_info.get("line_number", 0)
                existing_func["signature"] = _create_function_signature(func_info)
                existing_func["returnType"] = func_info.get("return_type", "")
                function_nodes.append(existing_func)
            else:
                # Create new function
                function_node = {
                    "@id": func_id,
                    "@type": "llm:Function",
                    "name": func_info["name"],
                    "description": func_info.get("docstring", ""),
                    "filePath": module.get("file_path", ""),
                    "lineNumber": func_info.get("line_number", 0),
                    "signature": _create_function_signature(func_info),
                    "returnType": func_info.get("return_type", ""),
                }
                function_nodes.append(function_node)

        # Add class methods
        for class_info in module.get("classes", []):
            for method_info in class_info.get("methods", []):
                method_id = f"llm:{module['module_name']}.{class_info['name']}.{method_info['name']}"

                # Check if method already exists
                existing_method = next(
                    (f for f in existing_functions if f.get("@id") == method_id), None
                )

                if existing_method:
                    # Update existing method
                    existing_method["description"] = method_info.get("docstring", "")
                    existing_method["filePath"] = module.get("file_path", "")
                    existing_method["lineNumber"] = method_info.get("line_number", 0)
                    existing_method["signature"] = _create_function_signature(
                        method_info
                    )
                    existing_method["returnType"] = method_info.get("return_type", "")
                    function_nodes.append(existing_method)
                else:
                    # Create new method
                    method_node = {
                        "@id": method_id,
                        "@type": "llm:Function",
                        "name": method_info["name"],
                        "description": method_info.get("docstring", ""),
                        "filePath": module.get("file_path", ""),
                        "lineNumber": method_info.get("line_number", 0),
                        "signature": _create_function_signature(method_info),
                        "returnType": method_info.get("return_type", ""),
                    }
                    function_nodes.append(method_node)

    # Merge with existing functions
    # Keep existing functions that are not these functions
    function_ids = [f["@id"] for f in function_nodes]
    other_functions = [
        f for f in existing_functions if f.get("@id") not in function_ids
    ]
    all_functions = other_functions + function_nodes

    # Write to file
    with open(functions_file, "w") as f:
        json.dump(all_functions, f, indent=2)

    logging.success(f"Created {len(function_nodes)} function nodes")


def _create_function_signature(func_info: Dict[str, Any]) -> str:
    """
    Create a function signature string.

    Args:
        func_info: Function information dictionary

    Returns:
        str: Function signature
    """
    params_str = []
    for param in func_info.get("params", []):
        if "type" in param:
            params_str.append(f"{param['name']}: {param['type']}")
        else:
            params_str.append(param["name"])

    return_type = (
        f" -> {func_info['return_type']}" if func_info.get("return_type") else ""
    )

    return f"{func_info['name']}({', '.join(params_str)}){return_type}"


def create_import_relationships(
    code_structure: Dict[str, Any], relationships_dir: str
) -> None:
    """
    Create import relationships from code structure.

    Args:
        code_structure: Code structure dictionary
        relationships_dir: Directory to store relationship JSON files
    """
    logging.info("Creating import relationships...")

    # Create relationships directory if it doesn't exist
    os.makedirs(relationships_dir, exist_ok=True)

    # Create imports file path
    imports_file = os.path.join(relationships_dir, "imports.json")

    # Load existing imports if the file exists
    existing_imports = []
    if os.path.isfile(imports_file):
        try:
            with open(imports_file) as f:
                existing_imports = json.load(f)
        except Exception as e:
            logging.error(f"Error loading existing imports: {str(e)}")

    # Create import relationships
    import_relationships = []
    for module in code_structure["modules"]:
        module_id = f"llm:{module['module_name']}"

        for import_info in module.get("imports", []):
            import_name = import_info["name"]

            # Skip standard library imports
            if "." not in import_name:
                continue

            # Create relationship ID
            rel_id = f"llm:import_{module['module_name']}_{import_name}"

            # Check if relationship already exists
            existing_rel = next(
                (r for r in existing_imports if r.get("@id") == rel_id), None
            )

            if existing_rel:
                # Update existing relationship
                existing_rel["source"] = {"@id": module_id}
                existing_rel["target"] = {"@id": f"llm:{import_name}"}
                import_relationships.append(existing_rel)
            else:
                # Create new relationship
                import_rel = {
                    "@id": rel_id,
                    "@type": "llm:Imports",
                    "name": f"{module['module_name']} imports {import_name}",
                    "source": {"@id": module_id},
                    "target": {"@id": f"llm:{import_name}"},
                }
                import_relationships.append(import_rel)

    # Merge with existing imports
    # Keep existing imports that are not these imports
    import_ids = [r["@id"] for r in import_relationships]
    other_imports = [r for r in existing_imports if r.get("@id") not in import_ids]
    all_imports = other_imports + import_relationships

    # Write to file
    with open(imports_file, "w") as f:
        json.dump(all_imports, f, indent=2)

    logging.success(f"Created {len(import_relationships)} import relationships")


def create_inheritance_relationships(
    code_structure: Dict[str, Any], relationships_dir: str
) -> None:
    """
    Create inheritance relationships from code structure.

    Args:
        code_structure: Code structure dictionary
        relationships_dir: Directory to store relationship JSON files
    """
    logging.info("Creating inheritance relationships...")

    # Create relationships directory if it doesn't exist
    os.makedirs(relationships_dir, exist_ok=True)

    # Create component dependencies file path
    dependencies_file = os.path.join(relationships_dir, "component_dependencies.json")

    # Load existing dependencies if the file exists
    existing_dependencies = []
    if os.path.isfile(dependencies_file):
        try:
            with open(dependencies_file) as f:
                existing_dependencies = json.load(f)
        except Exception as e:
            logging.error(f"Error loading existing dependencies: {str(e)}")

    # Create inheritance relationships
    inheritance_relationships = []
    for module in code_structure["modules"]:
        for class_info in module.get("classes", []):
            class_id = f"llm:{module['module_name']}.{class_info['name']}"

            for base in class_info.get("bases", []):
                # Create relationship ID
                rel_id = (
                    f"llm:inherits_{module['module_name']}_{class_info['name']}_{base}"
                )

                # Check if relationship already exists
                existing_rel = next(
                    (r for r in existing_dependencies if r.get("@id") == rel_id), None
                )

                if existing_rel:
                    # Update existing relationship
                    existing_rel["source"] = {"@id": class_id}
                    existing_rel["target"] = {"@id": f"llm:{base}"}
                    inheritance_relationships.append(existing_rel)
                else:
                    # Create new relationship
                    inheritance_rel = {
                        "@id": rel_id,
                        "@type": "llm:DependsOn",
                        "name": f"{class_info['name']} inherits from {base}",
                        "source": {"@id": class_id},
                        "target": {"@id": f"llm:{base}"},
                    }
                    inheritance_relationships.append(inheritance_rel)

    # Merge with existing dependencies
    # Keep existing dependencies that are not these inheritance relationships
    inheritance_ids = [r["@id"] for r in inheritance_relationships]
    other_dependencies = [
        r for r in existing_dependencies if r.get("@id") not in inheritance_ids
    ]
    all_dependencies = other_dependencies + inheritance_relationships

    # Write to file
    with open(dependencies_file, "w") as f:
        json.dump(all_dependencies, f, indent=2)

    logging.success(
        f"Created {len(inheritance_relationships)} inheritance relationships"
    )


def create_function_call_relationships(
    code_structure: Dict[str, Any], relationships_dir: str
) -> None:
    """
    Create function call relationships from code structure.

    Args:
        code_structure: Code structure dictionary
        relationships_dir: Directory to store relationship JSON files
    """
    logging.info("Creating function call relationships...")

    # Create relationships directory if it doesn't exist
    os.makedirs(relationships_dir, exist_ok=True)

    # Create function calls file path
    function_calls_file = os.path.join(relationships_dir, "function_calls.json")

    # Load existing function calls if the file exists
    existing_calls = []
    if os.path.isfile(function_calls_file):
        try:
            with open(function_calls_file) as f:
                existing_calls = json.load(f)
        except Exception as e:
            logging.error(f"Error loading existing function calls: {str(e)}")

    # Create function call relationships
    call_relationships = []
    for module in code_structure["modules"]:
        # Process method calls
        for call_info in module.get("method_calls", []):
            # Skip calls without a clear caller
            if not call_info.get("in_class"):
                continue

            caller_id = f"llm:{module['module_name']}.{call_info['in_class']}"
            callee_name = call_info["name"]

            # Create relationship ID
            rel_id = f"llm:calls_{module['module_name']}_{call_info['in_class']}_{callee_name}_{call_info['line_number']}"

            # Check if relationship already exists
            existing_rel = next(
                (r for r in existing_calls if r.get("@id") == rel_id), None
            )

            if existing_rel:
                # Update existing relationship
                existing_rel["source"] = {"@id": caller_id}
                existing_rel["target"] = {"@id": f"llm:{callee_name}"}
                call_relationships.append(existing_rel)
            else:
                # Create new relationship
                call_rel = {
                    "@id": rel_id,
                    "@type": "llm:Calls",
                    "name": f"{call_info['in_class']} calls {callee_name}",
                    "source": {"@id": caller_id},
                    "target": {"@id": f"llm:{callee_name}"},
                }
                call_relationships.append(call_rel)

    # Merge with existing function calls
    # Keep existing calls that are not these call relationships
    call_ids = [r["@id"] for r in call_relationships]
    other_calls = [r for r in existing_calls if r.get("@id") not in call_ids]
    all_calls = other_calls + call_relationships

    # Write to file
    with open(function_calls_file, "w") as f:
        json.dump(all_calls, f, indent=2)

    logging.success(f"Created {len(call_relationships)} function call relationships")


def create_module_contains_relationships(
    code_structure: Dict[str, Any], relationships_dir: str
) -> None:
    """
    Create module contains relationships from code structure.

    Args:
        code_structure: Code structure dictionary
        relationships_dir: Directory to store relationship JSON files
    """
    logging.info("Creating module contains relationships...")

    # Create relationships directory if it doesn't exist
    os.makedirs(relationships_dir, exist_ok=True)

    # Create component dependencies file path
    dependencies_file = os.path.join(relationships_dir, "component_dependencies.json")

    # Load existing dependencies if the file exists
    existing_dependencies = []
    if os.path.isfile(dependencies_file):
        try:
            with open(dependencies_file) as f:
                existing_dependencies = json.load(f)
        except Exception as e:
            logging.error(f"Error loading existing dependencies: {str(e)}")

    # Create module contains relationships
    contains_relationships = []
    for module in code_structure["modules"]:
        module_id = f"llm:{module['module_name']}"

        # Module contains classes
        for class_info in module.get("classes", []):
            class_id = f"llm:{module['module_name']}.{class_info['name']}"

            # Create relationship ID
            rel_id = f"llm:contains_{module['module_name']}_{class_info['name']}"

            # Check if relationship already exists
            existing_rel = next(
                (r for r in existing_dependencies if r.get("@id") == rel_id), None
            )

            if existing_rel:
                # Update existing relationship
                existing_rel["source"] = {"@id": module_id}
                existing_rel["target"] = {"@id": class_id}
                contains_relationships.append(existing_rel)
            else:
                # Create new relationship
                contains_rel = {
                    "@id": rel_id,
                    "@type": "llm:Contains",
                    "name": f"{module['module_name']} contains {class_info['name']}",
                    "source": {"@id": module_id},
                    "target": {"@id": class_id},
                }
                contains_relationships.append(contains_rel)

        # Module contains functions
        for func_info in module.get("functions", []):
            func_id = f"llm:{module['module_name']}.{func_info['name']}"

            # Create relationship ID
            rel_id = f"llm:contains_{module['module_name']}_{func_info['name']}"

            # Check if relationship already exists
            existing_rel = next(
                (r for r in existing_dependencies if r.get("@id") == rel_id), None
            )

            if existing_rel:
                # Update existing relationship
                existing_rel["source"] = {"@id": module_id}
                existing_rel["target"] = {"@id": func_id}
                contains_relationships.append(existing_rel)
            else:
                # Create new relationship
                contains_rel = {
                    "@id": rel_id,
                    "@type": "llm:Contains",
                    "name": f"{module['module_name']} contains {func_info['name']}",
                    "source": {"@id": module_id},
                    "target": {"@id": func_id},
                }
                contains_relationships.append(contains_rel)

    # Merge with existing dependencies
    # Keep existing dependencies that are not these contains relationships
    contains_ids = [r["@id"] for r in contains_relationships]
    other_dependencies = [
        r for r in existing_dependencies if r.get("@id") not in contains_ids
    ]
    all_dependencies = other_dependencies + contains_relationships

    # Write to file
    with open(dependencies_file, "w") as f:
        json.dump(all_dependencies, f, indent=2)

    logging.success(
        f"Created {len(contains_relationships)} module contains relationships"
    )


def update_code_graph(root_dir: str) -> bool:
    """
    Update the knowledge graph with code structure from Python files.

    Args:
        root_dir: Root directory to search in

    Returns:
        bool: True if successful, False otherwise
    """
    logging.info("Updating knowledge graph with code structure...")

    # Extract code structure
    code_structure = extract_code_structure(root_dir)

    # Create directories for entities and relationships
    entities_dir = os.path.join(root_dir, "docs", "knowledge-graph", "entities")
    relationships_dir = os.path.join(
        root_dir, "docs", "knowledge-graph", "relationships"
    )

    # Create nodes
    create_module_nodes(code_structure, entities_dir)
    create_class_nodes(code_structure, entities_dir)
    create_function_nodes(code_structure, entities_dir)

    # Create relationships
    create_import_relationships(code_structure, relationships_dir)
    create_inheritance_relationships(code_structure, relationships_dir)
    create_function_call_relationships(code_structure, relationships_dir)
    create_module_contains_relationships(code_structure, relationships_dir)

    # Regenerate the graph
    from llm_stack.tools.knowledge_graph import generate_graph

    result = generate_graph.main()

    if result == 0:
        logging.success("Knowledge graph updated successfully")
        return True
    else:
        logging.error("Failed to regenerate knowledge graph")
        return False


def main() -> int:
    """
    Main function for the script.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    logging.info("Starting code graph update...")

    # Get project root directory
    root_dir = system.get_project_root()

    # Update code graph
    if update_code_graph(root_dir):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
