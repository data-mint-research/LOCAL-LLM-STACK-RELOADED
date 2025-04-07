#!/usr/bin/env python3
"""
Enhanced Architecture Analysis for LOCAL-LLM-STACK-RELOADED

This script extends the original architecture_analysis.py with additional
analysis capabilities to provide a more comprehensive architecture assessment,
including:

1. Architecture Baseline Analysis
2. Deeper Component Analysis
3. Pattern & Convention Analysis
4. Orphaned Files Impact Assessment
5. Gap Analysis
6. Detailed Recommendations
"""

import os
import re
import sys
import json
import glob
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any
import networkx as nx
from datetime import datetime

# Import the original architecture analyzer
from architecture_analysis import ArchitectureAnalyzer as BaseArchitectureAnalyzer

# Import utility modules
from llm_stack.core.file_utils import read_file, write_file, ensure_directory_exists
from llm_stack.core.visualization_utils import create_network_graph, create_bar_chart, create_pie_chart
from llm_stack.core import logging

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the knowledge graph modules
from llm_stack.knowledge_graph.client import get_client
from llm_stack.knowledge_graph.schema import NodeLabel, RelationshipType


class EnhancedArchitectureAnalyzer(BaseArchitectureAnalyzer):
    """Enhanced architecture analyzer with additional analysis capabilities."""

    def __init__(self):
        """Initialize the enhanced architecture analyzer."""
        super().__init__()
        self.project_root = Path(os.path.abspath(os.path.dirname(__file__)))
        self.llm_stack_dir = self.project_root / "llm_stack"
        self.orphaned_files_report = self.project_root / "orphaned_files_report.md"
        
        # Initialize analysis results
        self.architecture_baseline = {}
        self.pattern_analysis = {}
        self.convention_analysis = {}
        self.orphaned_files_assessment = {}
        self.gap_analysis = {}
        self.recommendations = {}

    def establish_architecture_baseline(self) -> Dict:
        """
        Establish the architecture baseline by analyzing the project structure.
        
        Returns:
            Dict: Architecture baseline information
        """
        logging.info("Establishing architecture baseline...")
        
        # Analyze directory structure
        directory_structure = self._analyze_directory_structure()
        
        # Identify key interfaces
        interfaces = self._identify_key_interfaces()
        
        # Identify architectural patterns
        patterns = self._identify_architectural_patterns()
        
        # Compile results
        baseline = {
            "directory_structure": directory_structure,
            "interfaces": interfaces,
            "patterns": patterns
        }
        
        self.architecture_baseline = baseline
        logging.info("Architecture baseline established")
        return baseline

    def _analyze_directory_structure(self) -> Dict:
        """
        Analyze the project directory structure.
        
        Returns:
            Dict: Directory structure information
        """
        logging.info("Analyzing directory structure...")
        
        # Get all Python files in the project
        python_files = list(self.project_root.glob("**/*.py"))
        
        # Count files by directory
        directory_counts = {}
        for file_path in python_files:
            rel_path = file_path.relative_to(self.project_root)
            parent_dir = str(rel_path.parent)
            if parent_dir == ".":
                parent_dir = "root"
            
            if parent_dir not in directory_counts:
                directory_counts[parent_dir] = 0
            directory_counts[parent_dir] += 1
        
        # Analyze main components
        components = {
            "core": len(list(self.llm_stack_dir.glob("core/**/*.py"))),
            "modules": len(list(self.llm_stack_dir.glob("modules/**/*.py"))),
            "tools": len(list(self.llm_stack_dir.glob("tools/**/*.py"))),
            "knowledge_graph": len(list(self.llm_stack_dir.glob("knowledge_graph/**/*.py"))),
            "cli_commands": len(list(self.llm_stack_dir.glob("cli_commands/**/*.py"))),
            "code_quality": len(list(self.llm_stack_dir.glob("code_quality/**/*.py")))
        }
        
        # Analyze test structure
        tests = {
            "unit": len(list(self.project_root.glob("tests/unit/**/*.py"))),
            "integration": len(list(self.project_root.glob("tests/integration/**/*.py"))),
            "fixtures": len(list(self.project_root.glob("tests/fixtures/**/*.py")))
        }
        
        return {
            "directory_counts": directory_counts,
            "components": components,
            "tests": tests,
            "total_python_files": len(python_files)
        }

    def _identify_key_interfaces(self) -> Dict:
        """
        Identify key interfaces in the project.
        
        Returns:
            Dict: Key interfaces information
        """
        logging.info("Identifying key interfaces...")
        
        interfaces = {}
        
        # Read the interfaces.py file
        interfaces_path = self.llm_stack_dir / "core" / "interfaces.py"
        success, content = read_file(str(interfaces_path))
        
        if success:
            # Extract interface classes using regex
            interface_classes = re.findall(r'class\s+(\w+)\(.*\):\s*"""(.*?)"""', content, re.DOTALL)
            
            for class_name, docstring in interface_classes:
                # Extract methods using regex
                methods = re.findall(r'def\s+(\w+)\(.*?\).*?"""(.*?)"""', content, re.DOTALL)
                
                interfaces[class_name] = {
                    "docstring": docstring.strip(),
                    "methods": {method_name: docstring.strip() for method_name, docstring in methods}
                }
        
        # Check for implementations of these interfaces
        implementations = self._find_interface_implementations(interfaces.keys())
        
        return {
            "interfaces": interfaces,
            "implementations": implementations
        }

    def _find_interface_implementations(self, interface_names: List[str]) -> Dict:
        """
        Find implementations of the specified interfaces.
        
        Args:
            interface_names: List of interface names to find implementations for
            
        Returns:
            Dict: Interface implementations information
        """
        implementations = {interface: [] for interface in interface_names}
        
        # Get all Python files in the project
        python_files = list(self.project_root.glob("**/*.py"))
        
        for file_path in python_files:
            success, content = read_file(str(file_path))
            
            if success:
                for interface in interface_names:
                    # Look for class definitions that implement the interface
                    if re.search(rf'class\s+\w+\(.*{interface}.*\):', content):
                        rel_path = file_path.relative_to(self.project_root)
                        implementations[interface].append(str(rel_path))
        
        return implementations

    def _identify_architectural_patterns(self) -> Dict:
        """
        Identify architectural patterns used in the project.
        
        Returns:
            Dict: Architectural patterns information
        """
        logging.info("Identifying architectural patterns...")
        
        patterns = {}
        
        # Check for Dependency Injection pattern
        di_pattern = self._check_dependency_injection_pattern()
        patterns["dependency_injection"] = di_pattern
        
        # Check for Singleton pattern
        singleton_pattern = self._check_singleton_pattern()
        patterns["singleton"] = singleton_pattern
        
        # Check for Factory pattern
        factory_pattern = self._check_factory_pattern()
        patterns["factory"] = factory_pattern
        
        # Check for Observer pattern (events)
        observer_pattern = self._check_observer_pattern()
        patterns["observer"] = observer_pattern
        
        return patterns

    def _check_dependency_injection_pattern(self) -> Dict:
        """
        Check for the Dependency Injection pattern.
        
        Returns:
            Dict: Dependency Injection pattern information
        """
        di_files = []
        di_usage = []
        
        # Check for dependency_injection.py
        di_path = self.llm_stack_dir / "core" / "dependency_injection.py"
        if di_path.exists():
            di_files.append(str(di_path.relative_to(self.project_root)))
            
            # Read the file to understand the implementation
            success, content = read_file(str(di_path))
            if success:
                # Extract key functions and classes
                functions = re.findall(r'def\s+(\w+)\(.*?\):', content)
                classes = re.findall(r'class\s+(\w+)\(.*?\):', content)
                
                # Look for usage of these functions and classes in other files
                for file_path in self.project_root.glob("**/*.py"):
                    if file_path == di_path:
                        continue
                        
                    success, file_content = read_file(str(file_path))
                    if success:
                        for func in functions:
                            if re.search(rf'{func}\(', file_content):
                                rel_path = file_path.relative_to(self.project_root)
                                di_usage.append({
                                    "file": str(rel_path),
                                    "function": func
                                })
                        
                        for cls in classes:
                            if re.search(rf'{cls}\(', file_content):
                                rel_path = file_path.relative_to(self.project_root)
                                di_usage.append({
                                    "file": str(rel_path),
                                    "class": cls
                                })
        
        return {
            "files": di_files,
            "usage": di_usage,
            "usage_count": len(di_usage)
        }

    def _check_singleton_pattern(self) -> Dict:
        """
        Check for the Singleton pattern.
        
        Returns:
            Dict: Singleton pattern information
        """
        singleton_instances = []
        
        # Look for singleton pattern implementations
        for file_path in self.project_root.glob("**/*.py"):
            success, content = read_file(str(file_path))
            
            if success:
                # Look for common singleton implementation patterns
                if re.search(r'_instance\s*=\s*None', content) and re.search(r'if\s+cls\._instance\s+is\s+None', content):
                    rel_path = file_path.relative_to(self.project_root)
                    
                    # Extract class name
                    class_match = re.search(r'class\s+(\w+)', content)
                    class_name = class_match.group(1) if class_match else "Unknown"
                    
                    singleton_instances.append({
                        "file": str(rel_path),
                        "class": class_name
                    })
                
                # Look for get_module() pattern
                if re.search(r'def\s+get_module\(\)', content) and re.search(r'_module\s*=\s*None', content):
                    rel_path = file_path.relative_to(self.project_root)
                    singleton_instances.append({
                        "file": str(rel_path),
                        "type": "get_module"
                    })
        
        return {
            "instances": singleton_instances,
            "count": len(singleton_instances)
        }

    def _check_factory_pattern(self) -> Dict:
        """
        Check for the Factory pattern.
        
        Returns:
            Dict: Factory pattern information
        """
        factory_instances = []
        
        # Look for factory pattern implementations
        for file_path in self.project_root.glob("**/*.py"):
            success, content = read_file(str(file_path))
            
            if success:
                # Look for factory method pattern
                factory_methods = re.findall(r'def\s+create_(\w+)\(.*?\):', content)
                
                for method in factory_methods:
                    rel_path = file_path.relative_to(self.project_root)
                    factory_instances.append({
                        "file": str(rel_path),
                        "method": f"create_{method}"
                    })
        
        return {
            "instances": factory_instances,
            "count": len(factory_instances)
        }

    def _check_observer_pattern(self) -> Dict:
        """
        Check for the Observer pattern (events).
        
        Returns:
            Dict: Observer pattern information
        """
        observer_instances = []
        
        # Check for events.py
        events_path = self.llm_stack_dir / "core" / "events.py"
        if events_path.exists():
            # Read the file to understand the implementation
            success, content = read_file(str(events_path))
            
            if success:
                # Extract event-related functions and classes
                functions = re.findall(r'def\s+(\w+event\w*)\(.*?\):', content)
                classes = re.findall(r'class\s+(\w+Event\w*)\(.*?\):', content)
                
                # Look for usage of these functions and classes in other files
                for file_path in self.project_root.glob("**/*.py"):
                    if file_path == events_path:
                        continue
                        
                    success, file_content = read_file(str(file_path))
                    if success:
                        for func in functions:
                            if re.search(rf'{func}\(', file_content):
                                rel_path = file_path.relative_to(self.project_root)
                                observer_instances.append({
                                    "file": str(rel_path),
                                    "function": func
                                })
                        
                        for cls in classes:
                            if re.search(rf'{cls}\(', file_content):
                                rel_path = file_path.relative_to(self.project_root)
                                observer_instances.append({
                                    "file": str(rel_path),
                                    "class": cls
                                })
        
        return {
            "instances": observer_instances,
            "count": len(observer_instances)
        }

    def analyze_patterns_and_conventions(self) -> Dict:
        """
        Analyze patterns and conventions used in the project.
        
        Returns:
            Dict: Patterns and conventions analysis
        """
        logging.info("Analyzing patterns and conventions...")
        
        # Analyze dependency injection pattern
        di_analysis = self._analyze_dependency_injection()
        
        # Analyze module interface pattern
        module_interface_analysis = self._analyze_module_interface()
        
        # Analyze tool interface pattern
        tool_interface_analysis = self._analyze_tool_interface()
        
        # Analyze directory structure conventions
        directory_conventions = self._analyze_directory_conventions()
        
        # Analyze naming conventions
        naming_conventions = self._analyze_naming_conventions()
        
        # Analyze import structure
        import_structure = self._analyze_import_structure()
        
        # Analyze test organization
        test_organization = self._analyze_test_organization()
        
        # Compile pattern analysis results
        pattern_analysis = {
            "dependency_injection": di_analysis,
            "module_interface": module_interface_analysis,
            "tool_interface": tool_interface_analysis
        }
        
        # Compile convention analysis results
        convention_analysis = {
            "directory_structure": directory_conventions,
            "naming_conventions": naming_conventions,
            "import_structure": import_structure,
            "test_organization": test_organization
        }
        
        self.pattern_analysis = pattern_analysis
        self.convention_analysis = convention_analysis
        
        return {
            "pattern_analysis": pattern_analysis,
            "convention_analysis": convention_analysis
        }

    def _analyze_dependency_injection(self) -> Dict:
        """
        Analyze the dependency injection pattern implementation.
        
        Returns:
            Dict: Dependency injection analysis
        """
        logging.info("Analyzing dependency injection pattern...")
        
        # Get the dependency injection pattern information
        di_pattern = self.architecture_baseline.get("patterns", {}).get("dependency_injection", {})
        
        # Check for consistency in usage
        consistency = self._check_di_consistency()
        
        return {
            **di_pattern,
            "consistency": consistency
        }

    def _check_di_consistency(self) -> Dict:
        """
        Check for consistency in dependency injection usage.
        
        Returns:
            Dict: Dependency injection consistency information
        """
        # Get all module files
        module_files = list(self.llm_stack_dir.glob("modules/**/*.py"))
        module_files.extend(list(self.llm_stack_dir.glob("tools/**/*.py")))
        
        # Check each module file for constructor injection
        consistent_files = []
        inconsistent_files = []
        
        for file_path in module_files:
            success, content = read_file(str(file_path))
            
            if success:
                # Check for constructor injection pattern
                has_constructor = re.search(r'def\s+__init__\(self,.*?=None', content) is not None
                
                # Check for dependency resolution in constructor
                has_resolution = re.search(r'if\s+self\.\w+\s+is\s+None', content) is not None
                
                if has_constructor and has_resolution:
                    consistent_files.append(str(file_path.relative_to(self.project_root)))
                elif re.search(r'class\s+\w+\(', content):  # Only check files with classes
                    inconsistent_files.append(str(file_path.relative_to(self.project_root)))
        
        return {
            "consistent_files": consistent_files,
            "inconsistent_files": inconsistent_files,
            "consistency_percentage": len(consistent_files) / (len(consistent_files) + len(inconsistent_files)) * 100 if (len(consistent_files) + len(inconsistent_files)) > 0 else 0
        }

    def _analyze_module_interface(self) -> Dict:
        """
        Analyze the module interface pattern implementation.
        
        Returns:
            Dict: Module interface analysis
        """
        logging.info("Analyzing module interface pattern...")
        
        # Get the interfaces information
        interfaces = self.architecture_baseline.get("interfaces", {}).get("interfaces", {})
        implementations = self.architecture_baseline.get("interfaces", {}).get("implementations", {})
        
        # Check if ModuleInterface exists
        if "ModuleInterface" not in interfaces:
            return {
                "exists": False,
                "implementations": []
            }
        
        # Get ModuleInterface implementations
        module_implementations = implementations.get("ModuleInterface", [])
        
        # Check for consistency in implementations
        consistent_implementations = []
        inconsistent_implementations = []
        
        for impl_file in module_implementations:
            success, content = read_file(str(self.project_root / impl_file))
            
            if success:
                # Check if all required methods are implemented
                required_methods = interfaces["ModuleInterface"].get("methods", {}).keys()
                
                all_methods_implemented = True
                for method in required_methods:
                    if not re.search(rf'def\s+{method}\(', content):
                        all_methods_implemented = False
                        break
                
                if all_methods_implemented:
                    consistent_implementations.append(impl_file)
                else:
                    inconsistent_implementations.append(impl_file)
        
        return {
            "exists": True,
            "consistent_implementations": consistent_implementations,
            "inconsistent_implementations": inconsistent_implementations,
            "consistency_percentage": len(consistent_implementations) / len(module_implementations) * 100 if module_implementations else 0
        }

    def _analyze_tool_interface(self) -> Dict:
        """
        Analyze the tool interface pattern implementation.
        
        Returns:
            Dict: Tool interface analysis
        """
        logging.info("Analyzing tool interface pattern...")
        
        # Get the interfaces information
        interfaces = self.architecture_baseline.get("interfaces", {}).get("interfaces", {})
        implementations = self.architecture_baseline.get("interfaces", {}).get("implementations", {})
        
        # Check if ToolInterface exists
        if "ToolInterface" not in interfaces:
            return {
                "exists": False,
                "implementations": []
            }
        
        # Get ToolInterface implementations
        tool_implementations = implementations.get("ToolInterface", [])
        
        # Check for consistency in implementations
        consistent_implementations = []
        inconsistent_implementations = []
        
        for impl_file in tool_implementations:
            success, content = read_file(str(self.project_root / impl_file))
            
            if success:
                # Check if all required methods are implemented
                required_methods = interfaces["ToolInterface"].get("methods", {}).keys()
                
                all_methods_implemented = True
                for method in required_methods:
                    if not re.search(rf'def\s+{method}\(', content):
                        all_methods_implemented = False
                        break
                
                if all_methods_implemented:
                    consistent_implementations.append(impl_file)
                else:
                    inconsistent_implementations.append(impl_file)
        
        return {
            "exists": True,
            "consistent_implementations": consistent_implementations,
            "inconsistent_implementations": inconsistent_implementations,
            "consistency_percentage": len(consistent_implementations) / len(tool_implementations) * 100 if tool_implementations else 0
        }

    def _analyze_directory_conventions(self) -> Dict:
        """
        Analyze directory structure conventions.
        
        Returns:
            Dict: Directory structure conventions analysis
        """
        logging.info("Analyzing directory structure conventions...")
        
        # Define expected directory structure
        expected_structure = {
            "core": self.llm_stack_dir / "core",
            "modules": self.llm_stack_dir / "modules",
            "tools": self.llm_stack_dir / "tools",
            "knowledge_graph": self.llm_stack_dir / "knowledge_graph",
            "cli_commands": self.llm_stack_dir / "cli_commands",
            "tests/unit": self.project_root / "tests" / "unit",
            "tests/integration": self.project_root / "tests" / "integration",
            "tests/fixtures": self.project_root / "tests" / "fixtures"
        }
        
        # Check if expected directories exist
        existing_dirs = {}
        for name, path in expected_structure.items():
            existing_dirs[name] = path.exists()
        
        # Check for unexpected directories
        unexpected_dirs = []
        for path in self.llm_stack_dir.iterdir():
            if path.is_dir() and path.name not in ["core", "modules", "tools", "knowledge_graph", "cli_commands", "code_quality", "__pycache__"]:
                unexpected_dirs.append(str(path.relative_to(self.project_root)))
        
        # Check for files in the root directory
        root_files = []
        for path in self.llm_stack_dir.iterdir():
            if path.is_file() and path.name not in ["__init__.py", "cli.py"]:
                root_files.append(str(path.relative_to(self.project_root)))
        
        return {
            "expected_directories": existing_dirs,
            "unexpected_directories": unexpected_dirs,
            "root_files": root_files,
            "compliance_percentage": sum(existing_dirs.values()) / len(existing_dirs) * 100
        }

    def _analyze_naming_conventions(self) -> Dict:
        """
        Analyze naming conventions.
        
        Returns:
            Dict: Naming conventions analysis
        """
        logging.info("Analyzing naming conventions...")
        
        # Define naming conventions
        conventions = {
            "snake_case_files": r'^[a-z][a-z0-9_]*\.py$',
            "snake_case_functions": r'def\s+[a-z][a-z0-9_]*\(',
            "snake_case_variables": r'[a-z][a-z0-9_]*\s*=',
            "camel_case_classes": r'class\s+[A-Z][a-zA-Z0-9]*\(',
            "uppercase_constants": r'[A-Z][A-Z0-9_]*\s*='
        }
        
        # Check files for naming conventions
        convention_compliance = {name: {"compliant": 0, "non_compliant": 0} for name in conventions}
        
        for file_path in self.project_root.glob("**/*.py"):
            # Check file name convention
            if re.match(conventions["snake_case_files"], file_path.name):
                convention_compliance["snake_case_files"]["compliant"] += 1
            else:
                convention_compliance["snake_case_files"]["non_compliant"] += 1
            
            # Check content conventions
            success, content = read_file(str(file_path))
            
            if success:
                # Check function names
                functions = re.findall(r'def\s+(\w+)\(', content)
                for func in functions:
                    if re.match(r'^[a-z][a-z0-9_]*$', func):
                        convention_compliance["snake_case_functions"]["compliant"] += 1
                    else:
                        convention_compliance["snake_case_functions"]["non_compliant"] += 1
                
                # Check class names
                classes = re.findall(r'class\s+(\w+)\(', content)
                for cls in classes:
                    if re.match(r'^[A-Z][a-zA-Z0-9]*$', cls):
                        convention_compliance["camel_case_classes"]["compliant"] += 1
                    else:
                        convention_compliance["camel_case_classes"]["non_compliant"] += 1
                
                # Check variable names (simplified approach)
                variables = re.findall(r'(\w+)\s*=', content)
                for var in variables:
                    if var.isupper() and len(var) > 1:
                        convention_compliance["uppercase_constants"]["compliant"] += 1
                    elif re.match(r'^[a-z][a-z0-9_]*$', var):
                        convention_compliance["snake_case_variables"]["compliant"] += 1
                    else:
                        # Skip special variables like __init__
                        if not (var.startswith('__') and var.endswith('__')):
                            convention_compliance["snake_case_variables"]["non_compliant"] += 1
        
        # Calculate compliance percentages
        compliance_percentages = {}
        for name, counts in convention_compliance.items():
            total = counts["compliant"] + counts["non_compliant"]
            compliance_percentages[name] = (counts["compliant"] / total * 100) if total > 0 else 0
        
        return {
            "convention_compliance": convention_compliance,
            "compliance_percentages": compliance_percentages,
            "overall_compliance": sum(compliance_percentages.values()) / len(compliance_percentages) if compliance_percentages else 0
        }

    def _analyze_import_structure(self) -> Dict:
        """
        Analyze import structure.
        
        Returns:
            Dict: Import structure analysis
        """
        logging.info("Analyzing import structure...")
        
        # Define import conventions
        conventions = {
            "standard_library_first": r'import\s+[a-zA-Z0-9_]+\s*(?:\n|$)',
            "third_party_second": r'from\s+(?!llm_stack)[a-zA-Z0-9_\.]+\s+import',
            "project_imports_last": r'from\s+llm_stack\.[a-zA-Z0-9_\.]+\s+import'
        }
        
        # Check files for import conventions
        convention_compliance = {name: {"compliant": 0, "non_compliant": 0} for name in conventions}
        
        for file_path in self.project_root.glob("**/*.py"):
            success, content = read_file(str(file_path))
            
            if success:
                # Extract import statements
                import_statements = re.findall(r'((?:import|from)\s+[a-zA-Z0-9_\.]+\s+(?:import\s+[a-zA-Z0-9_\.\*,\s]+)?)', content)
                
                # Check import order
                if import_statements:
                    # Group imports by type
                    standard_imports = []
                    third_party_imports = []
                    project_imports = []
                    
                    for stmt in import_statements:
                        if re.match(r'import\s+[a-zA-Z0-9_]+\s*(?:\n|$)', stmt):
                            standard_imports.append(stmt)
                        elif re.match(r'from\s+(?!llm_stack)[a-zA-Z0-9_\.]+\s+import', stmt):
                            third_party_imports.append(stmt)
                        elif re.match(r'from\s+llm_stack\.[a-zA-Z0-9_\.]+\s+import', stmt):
                            project_imports.append(stmt)
                    
                    # Check if imports are in the correct order
                    correct_order = True
                    last_type = None
                    
                    for stmt in import_statements:
                        current_type = None
                        
                        if re.match(r'import\s+[a-zA-Z0-9_]+\s*(?:\n|$)', stmt):
                            current_type = "standard"
                        elif re.match(r'from\s+(?!llm_stack)[a-zA-Z0-9_\.]+\s+import', stmt):
                            current_type = "third_party"
                        elif re.match(r'from\s+llm_stack\.[a-zA-Z0-9_\.]+\s+import', stmt):
                            current_type = "project"
                        
                        if last_type and current_type:
                            if (last_type == "standard" and current_type != "standard" and current_type != "third_party") or \
                               (last_type == "third_party" and current_type != "third_party" and current_type != "project") or \
                               (last_type == "project" and current_type != "project"):
                                correct_order = False
                                break
                        
                        last_type = current_type
                    
                    if correct_order:
                        convention_compliance["standard_library_first"]["compliant"] += 1
