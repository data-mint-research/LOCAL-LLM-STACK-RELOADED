#!/usr/bin/env python3
"""
Architecture Analyzer for LOCAL-LLM-STACK-RELOADED

This script analyzes the architecture of the LOCAL-LLM-STACK-RELOADED project,
focusing on:

1. Architecture Baseline Analysis
2. Component Analysis
3. Pattern & Convention Analysis
4. Orphaned Files Impact Assessment
5. Gap Analysis
6. Recommendations Development
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any

# Import utility modules
from llm_stack.core.file_utils import read_file, write_file, ensure_directory_exists
from llm_stack.core import logging

class ArchitectureAnalyzer:
    """Analyzes the architecture of the LOCAL-LLM-STACK-RELOADED project."""

    def __init__(self):
        """Initialize the architecture analyzer."""
        self.project_root = Path(os.path.abspath(os.path.dirname(__file__)))
        self.llm_stack_dir = self.project_root / "llm_stack"
        self.output_dir = Path("architecture_analysis")
        ensure_directory_exists(str(self.output_dir))
        
        # Initialize analysis results
        self.architecture_baseline = {}
        self.component_analysis = {}
        self.pattern_analysis = {}
        self.convention_analysis = {}
        self.orphaned_files_assessment = {}
        self.gap_analysis = {}
        self.recommendations = {}

    def analyze_architecture(self):
        """Perform a comprehensive architecture analysis."""
        logging.info("Starting comprehensive architecture analysis...")
        
        # 1. Establish Architecture Baseline
        self.architecture_baseline = self.establish_architecture_baseline()
        
        # 2. Perform Component Analysis
        self.component_analysis = self.analyze_components()
        
        # 3. Analyze Patterns and Conventions
        patterns_and_conventions = self.analyze_patterns_and_conventions()
        self.pattern_analysis = patterns_and_conventions["pattern_analysis"]
        self.convention_analysis = patterns_and_conventions["convention_analysis"]
        
        # 4. Assess Orphaned Files Impact
        self.orphaned_files_assessment = self.assess_orphaned_files_impact()
        
        # 5. Perform Gap Analysis
        self.gap_analysis = self.perform_gap_analysis()
        
        # 6. Develop Recommendations
        self.recommendations = self.develop_recommendations()
        
        # Compile results
        results = {
            "architecture_baseline": self.architecture_baseline,
            "component_analysis": self.component_analysis,
            "pattern_analysis": self.pattern_analysis,
            "convention_analysis": self.convention_analysis,
            "orphaned_files_assessment": self.orphaned_files_assessment,
            "gap_analysis": self.gap_analysis,
            "recommendations": self.recommendations
        }
        
        # Save results
        self.save_results(results)
        
        logging.info("Architecture analysis completed successfully")
        return results

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
        
        # Compile results
        baseline = {
            "directory_structure": directory_structure,
            "interfaces": interfaces
        }
        
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
        
        return {
            "directory_counts": directory_counts,
            "components": components,
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
        
        return interfaces

    def analyze_components(self) -> Dict:
        """
        Analyze the components of the project.
        
        Returns:
            Dict: Component analysis information
        """
        logging.info("Analyzing components...")
        
        # Analyze core components
        core_analysis = self._analyze_core_components()
        
        # Analyze modules
        modules_analysis = self._analyze_modules()
        
        # Analyze tools
        tools_analysis = self._analyze_tools()
        
        # Analyze knowledge graph
        kg_analysis = self._analyze_knowledge_graph()
        
        # Analyze CLI commands
        cli_analysis = self._analyze_cli_commands()
        
        # Analyze code quality
        code_quality_analysis = self._analyze_code_quality()
        
        # Compile results
        component_analysis = {
            "core": core_analysis,
            "modules": modules_analysis,
            "tools": tools_analysis,
            "knowledge_graph": kg_analysis,
            "cli_commands": cli_analysis,
            "code_quality": code_quality_analysis
        }
        
        logging.info("Component analysis completed")
        return component_analysis

    def _analyze_core_components(self) -> Dict:
        """
        Analyze core components.
        
        Returns:
            Dict: Core components analysis
        """
        logging.info("Analyzing core components...")
        
        # Get all Python files in the core directory
        core_files = list(self.llm_stack_dir.glob("core/**/*.py"))
        
        # Extract file names
        core_file_names = [file_path.name for file_path in core_files]
        
        # Count files
        file_count = len(core_files)
        
        return {
            "file_count": file_count,
            "files": core_file_names
        }

    def _analyze_modules(self) -> Dict:
        """
        Analyze modules.
        
        Returns:
            Dict: Modules analysis
        """
        logging.info("Analyzing modules...")
        
        # Get all Python files in the modules directory
        module_files = list(self.llm_stack_dir.glob("modules/**/*.py"))
        
        # Extract module names
        module_dirs = set()
        for file_path in module_files:
            rel_path = file_path.relative_to(self.llm_stack_dir / "modules")
            if rel_path.parts:
                module_dirs.add(rel_path.parts[0])
        
        # Count files
        file_count = len(module_files)
        
        return {
            "file_count": file_count,
            "modules": list(module_dirs)
        }

    def _analyze_tools(self) -> Dict:
        """
        Analyze tools.
        
        Returns:
            Dict: Tools analysis
        """
        logging.info("Analyzing tools...")
        
        # Get all Python files in the tools directory
        tool_files = list(self.llm_stack_dir.glob("tools/**/*.py"))
        
        # Extract tool names
        tool_dirs = set()
        for file_path in tool_files:
            rel_path = file_path.relative_to(self.llm_stack_dir / "tools")
            if rel_path.parts:
                tool_dirs.add(rel_path.parts[0])
        
        # Count files
        file_count = len(tool_files)
        
        return {
            "file_count": file_count,
            "tools": list(tool_dirs)
        }

    def _analyze_knowledge_graph(self) -> Dict:
        """
        Analyze knowledge graph.
        
        Returns:
            Dict: Knowledge graph analysis
        """
        logging.info("Analyzing knowledge graph...")
        
        # Get all Python files in the knowledge_graph directory
        kg_files = list(self.llm_stack_dir.glob("knowledge_graph/**/*.py"))
        
        # Extract file names
        kg_file_names = [file_path.name for file_path in kg_files]
        
        # Count files
        file_count = len(kg_files)
        
        return {
            "file_count": file_count,
            "files": kg_file_names
        }

    def _analyze_cli_commands(self) -> Dict:
        """
        Analyze CLI commands.
        
        Returns:
            Dict: CLI commands analysis
        """
        logging.info("Analyzing CLI commands...")
        
        # Get all Python files in the cli_commands directory
        cli_files = list(self.llm_stack_dir.glob("cli_commands/**/*.py"))
        
        # Extract file names
        cli_file_names = [file_path.name for file_path in cli_files]
        
        # Count files
        file_count = len(cli_files)
        
        return {
            "file_count": file_count,
            "files": cli_file_names
        }

    def _analyze_code_quality(self) -> Dict:
        """
        Analyze code quality.
        
        Returns:
            Dict: Code quality analysis
        """
        logging.info("Analyzing code quality...")
        
        # Get all Python files in the code_quality directory
        cq_files = list(self.llm_stack_dir.glob("code_quality/**/*.py"))
        
        # Extract file names
        cq_file_names = [file_path.name for file_path in cq_files]
        
        # Count files
        file_count = len(cq_files)
        
        return {
            "file_count": file_count,
            "files": cq_file_names
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
        
        # Compile pattern analysis results
        pattern_analysis = {
            "dependency_injection": di_analysis,
            "module_interface": module_interface_analysis,
            "tool_interface": tool_interface_analysis
        }
        
        # Compile convention analysis results
        convention_analysis = {
            "directory_structure": directory_conventions,
            "naming_conventions": naming_conventions
        }
        
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
        
        di_files = []
        
        # Check for dependency_injection.py
        di_path = self.llm_stack_dir / "core" / "dependency_injection.py"
        if di_path.exists():
            di_files.append(str(di_path.relative_to(self.project_root)))
        
        return {
            "files": di_files,
            "exists": len(di_files) > 0
        }

    def _analyze_module_interface(self) -> Dict:
        """
        Analyze the module interface pattern implementation.
        
        Returns:
            Dict: Module interface analysis
        """
        logging.info("Analyzing module interface pattern...")
        
        # Get the interfaces information
        interfaces = self.architecture_baseline.get("interfaces", {})
        
        # Check if ModuleInterface exists
        exists = "ModuleInterface" in interfaces
        
        return {
            "exists": exists
        }

    def _analyze_tool_interface(self) -> Dict:
        """
        Analyze the tool interface pattern implementation.
        
        Returns:
            Dict: Tool interface analysis
        """
        logging.info("Analyzing tool interface pattern...")
        
        # Get the interfaces information
        interfaces = self.architecture_baseline.get("interfaces", {})
        
        # Check if ToolInterface exists
        exists = "ToolInterface" in interfaces
        
        return {
            "exists": exists
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
        
        return {
            "expected_directories": existing_dirs,
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
            "camel_case_classes": r'class\s+[A-Z][a-zA-Z0-9]*\('
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
                # Check class names
                classes = re.findall(r'class\s+(\w+)\(', content)
                for cls in classes:
                    if re.match(r'^[A-Z][a-zA-Z0-9]*$', cls):
                        convention_compliance["camel_case_classes"]["compliant"] += 1
                    else:
                        convention_compliance["camel_case_classes"]["non_compliant"] += 1
        
        return {
            "convention_compliance": convention_compliance
        }

    def assess_orphaned_files_impact(self) -> Dict:
        """
        Assess the impact of orphaned files.
        
        Returns:
            Dict: Orphaned files impact assessment
        """
        logging.info("Assessing orphaned files impact...")
        
        # Read the orphaned files report
        orphaned_files_report = self.project_root / "orphaned_files_report.md"
        orphaned_files = []
        
        if orphaned_files_report.exists():
            success, content = read_file(str(orphaned_files_report))
            
            if success:
                # Extract orphaned files using regex
                file_sections = re.findall(r'###\s+(.*?)\n\n\*\*Category\*\*:\s+(.*?)\n\n\*\*Description\*\*:\s+(.*?)\n\n', content, re.DOTALL)
                
                for file_name, category, description in file_sections:
                    # Extract risk level
                    risk_match = re.search(r'\*\*Risk Level\*\*:\s+(.*?)\n', content)
                    risk_level = risk_match.group(1) if risk_match else "Unknown"
                    
                    # Extract rationale
                    rationale_match = re.search(r'\*\*Rationale for Removal\*\*:\s+(.*?)\n', content)
                    rationale = rationale_match.group(1) if rationale_match else "Unknown"
                    
                    orphaned_files.append({
                        "file": file_name.strip(),
                        "category": category.strip(),
                        "description": description.strip(),
                        "risk_level": risk_level.strip(),
                        "rationale": rationale.strip()
                    })
        
        # Analyze impact of removing orphaned files
        impact_assessment = []
        
        for file_info in orphaned_files:
            file_path = self.project_root / file_info["file"]
            
            # Check if file exists
            if file_path.exists():
                # Check for imports of this file
                file_name_without_ext = file_path.stem
                imports = []
                
                for py_file in self.project_root.glob("**/*.py"):
                    if py_file != file_path:
                        success, content = read_file(str(py_file))
                        
                        if success:
                            # Look for imports of this file
                            if re.search(rf'(?:import|from)\s+.*{file_name_without_ext}', content):
                                imports.append(str(py_file.relative_to(self.project_root)))
                
                impact_assessment.append({
                    "file": file_info["file"],
                    "risk_level": file_info["risk_level"],
                    "imports": imports,
                    "impact": "High" if imports else "Low"
                })
        
        return {
            "orphaned_files": orphaned_files,
            "impact_assessment": impact_assessment
        }

    def perform_gap_analysis(self) -> Dict:
        """
        Perform a gap analysis to identify areas for improvement.
        
        Returns:
            Dict: Gap analysis information
        """
        logging.info("Performing gap analysis...")
        
        # Identify gaps in architecture
        architecture_gaps = []
        
        # Check for missing interfaces
        interfaces = self.architecture_baseline.get("interfaces", {})
        if "ModuleInterface" not in interfaces:
            architecture_gaps.append({
                "type": "missing_interface",
                "name": "ModuleInterface",
                "impact": "High",
                "description": "The ModuleInterface is missing, which is essential for standardizing module implementations."
            })
        
        if "ToolInterface" not in interfaces:
            architecture_gaps.append({
                "type": "missing_interface",
                "name": "ToolInterface",
                "impact": "High",
                "description": "The ToolInterface is missing, which is essential for standardizing tool implementations."
            })
        
        # Check for missing directories
        expected_dirs = {
            "core": self.llm_stack_dir / "core",
            "modules": self.llm_stack_dir / "modules",
            "tools": self.llm_stack_dir / "tools",
            "knowledge_graph": self.llm_stack_dir / "knowledge_graph",
            "cli_commands": self.llm_stack_dir / "cli_commands",
            "tests/unit": self.project_root / "tests" / "unit",
            "tests/integration": self.project_root / "tests" / "integration",
            "tests/fixtures": self.project_root / "tests" / "fixtures"
        }
        
        for name, path in expected_dirs.items():
            if not path.exists():
                architecture_gaps.append({
                    "type": "missing_directory",
                    "name": name,
                    "impact": "Medium",
                    "description": f"The {name} directory is missing, which is part of the expected project structure."
                })
        
        return {
            "architecture_gaps": architecture_gaps
        }

    def develop_recommendations(self) -> Dict:
        """
        Develop recommendations for improving the architecture.
        
        Returns:
            Dict: Recommendations information
        """
        logging.info("Developing recommendations...")
        
        # Develop recommendations based on the analysis
        structure_recommendations = []
        pattern_recommendations = []
        convention_recommendations = []
        orphaned_files_recommendations = []
        gap_closure_recommendations = []
        
        # Structure recommendations
        directory_structure = self.convention_analysis.get("directory_structure", {})
        expected_directories = directory_structure.get("expected_directories", {})
        
        for name, exists in expected_directories.items():
            if not exists:
                structure_recommendations.append({
                    "type": "create_directory",
                    "name": name,
                    "priority": "High",
                    "description": f"Create the {name} directory to align with the expected project structure."
                })
        
        # Pattern recommendations
        di_analysis = self.pattern_analysis.get("dependency_injection", {})
        if not di_analysis.get("exists", False):
            pattern_recommendations.append({
                "type": "implement_pattern",
                "name": "dependency_injection",
                "priority": "High",
                "description": "Implement the Dependency Injection pattern to improve modularity and testability."
            })
        
        # Convention recommendations
        naming_conventions = self.convention_analysis.get("naming_conventions", {})
        convention_compliance = naming_conventions.get("convention_compliance", {})
        
        for convention, counts in convention_compliance.items():
            if counts.get("non_compliant", 0) > 0:
                convention_recommendations.append({
                    "type": "follow_convention",
                    "name": convention,
                    "priority": "Medium",
                    "description": f"Follow the {convention} naming convention consistently across the project."
                })
        
        # Orphaned files recommendations
        orphaned_files = self.orphaned_files_assessment.get("orphaned_files", [])
        impact_assessment = self.orphaned_files_assessment.get("impact_assessment", [])
        
        for assessment in impact_assessment:
            if assessment.get("impact") == "Low":
                orphaned_files_recommendations.append({
                    "type": "remove_file",
                    "name": assessment.get("file"),
                    "priority": "Medium",
                    "description": f"Remove the orphaned file {assessment.get('file')} as it has low impact on the project."
                })
            else:
                orphaned_files_recommendations.append({
                    "type": "review_file",
                    "name": assessment.get("file"),
                    "priority": "High",
                    "description": f"Review the orphaned file {assessment.get('file')} as it has high impact on the project."
                })
        
        # Gap closure recommendations
        architecture_gaps = self.gap_analysis.get("architecture_gaps", [])
        
        for gap in architecture_gaps:
            gap_closure_recommendations.append({
                "type": "close_gap",
                "name": gap.get("name"),
                "priority": "High" if gap.get("impact") == "High" else "Medium",
                "description": f"Address the {gap.get('type')} gap for {gap.get('name')}."
            })
        
        return {
            "structure_recommendations": structure_recommendations,
            "pattern_recommendations": pattern_recommendations,
            "convention_recommendations": convention_recommendations,
            "orphaned_files_recommendations": orphaned_files_recommendations,
            "gap_closure_recommendations": gap_closure_recommendations
        }

    def save_results(self, results: Dict) -> None:
        """
        Save the analysis results to a file.
        
        Args:
            results: Analysis results
        """
        logging.info("Saving analysis results...")
        
        # Save results as JSON
        results_path = self.output_dir / "architecture_analysis_results.json"
        write_file(str(results_path), json.dumps(results, indent=2))
        
        logging.info(f"Analysis results saved to {results_path}")

def main():
    """Main function."""
    logging.info("Starting architecture analysis...")
    
    # Create and run the architecture analyzer
    analyzer = ArchitectureAnalyzer()
    results = analyzer.analyze_architecture()
    
    # Print summary
    print("\n" + "=" * 80)
    print("Architecture Analysis Summary:")
    print("=" * 80)
    
    # Component analysis
    print(f"\nComponent Analysis:")
    for component, analysis in results["component_analysis"].items():
        print(f"  - {component.capitalize()}: {analysis.get('file_count', 0)} files")
    
    # Pattern analysis
    print(f"\nPattern Analysis:")
    for pattern, analysis in results["pattern_analysis"].items():
        print(f"  - {pattern.replace('_', ' ').capitalize()}: {'Present' if analysis.get('exists', False) else 'Missing'}")
    
    # Orphaned files assessment
    print(f"\nOrphaned Files Assessment:")
    orphaned_files = results["orphaned_files_assessment"].get("orphaned_files", [])
    print(f"  - Orphaned files: {len(orphaned_files)}")
    
    # Gap analysis
    print(f"\nGap Analysis:")
    architecture_gaps = results["gap_analysis"].get("architecture_gaps", [])
    print(f"  - Architecture gaps: {len(architecture_gaps)}")
    
    # Recommendations
    print(f"\nRecommendations:")
    structure_recommendations = results["recommendations"].get("structure_recommendations", [])
    pattern_recommendations = results["recommendations"].get("pattern_recommendations", [])
    convention_recommendations = results["recommendations"].get("convention_recommendations", [])
    orphaned_files_recommendations = results["recommendations"].get("orphaned_files_recommendations", [])
    gap_closure_recommendations = results["recommendations"].get("gap_closure_recommendations", [])
    
    print(f"  - Structure recommendations: {len(structure_recommendations)}")
    print(f"  - Pattern recommendations: {len(pattern_recommendations)}")
    print(f"  - Convention recommendations: {len(convention_recommendations)}")
    print(f"  - Orphaned files recommendations: {len(orphaned_files_recommendations)}")
    print(f"  - Gap closure recommendations: {len(gap_closure_recommendations)}")
    
    print("\n" + "=" * 80)
    print(f"Detailed results saved to: {analyzer.output_dir / 'architecture_analysis_results.json'}")
    print("=" * 80)
    
    logging.info("Architecture analysis completed successfully")

if __name__ == "__main__":
    main()