#!/usr/bin/env python3
"""
Architecture Analysis for LOCAL-LLM-STACK-RELOADED

This script extracts architectural information from the knowledge graph,
analyzes component structures, and evaluates migration patterns.
It generates visualizations of the system architecture to support
the code quality review process.
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union
import networkx as nx
from datetime import datetime

# Import utility modules
from llm_stack.core.file_utils import read_file, write_file, ensure_directory_exists
from llm_stack.core.visualization_utils import create_network_graph, create_bar_chart, create_pie_chart

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the knowledge graph modules
from llm_stack.knowledge_graph.client import get_client
from llm_stack.knowledge_graph.schema import NodeLabel, RelationshipType
from llm_stack.core import logging


class ArchitectureAnalyzer:
    """Analyzes the architecture of the LOCAL-LLM-STACK-RELOADED project."""

    def __init__(self):
        """Initialize the architecture analyzer."""
        self.client = get_client()
        self.output_dir = Path("architecture_analysis")
        ensure_directory_exists(str(self.output_dir))
        
        # Ensure connection to Neo4j
        if not self.client.ensure_connected():
            logging.error("Failed to connect to Neo4j database")
            sys.exit(1)
        
        logging.info("Connected to Neo4j database")

    def extract_component_relationships(self) -> nx.DiGraph:
        """
        Extract component relationships from the knowledge graph.
        
        Returns:
            nx.DiGraph: A directed graph of component relationships
        """
        logging.info("Extracting component relationships...")
        
        # Query to get all components and their relationships
        query = """
        MATCH (c1:Component)-[r]->(c2:Component)
        RETURN c1.name as source, c2.name as target, type(r) as relationship
        """
        
        try:
            results = self.client.run_query(query)
            
            # Create a directed graph
            graph = nx.DiGraph()
            
            # Add nodes and edges
            for record in results:
                source = record.get("source", "Unknown")
                target = record.get("target", "Unknown")
                relationship = record.get("relationship", "UNKNOWN")
                
                graph.add_node(source)
                graph.add_node(target)
                graph.add_edge(source, target, relationship=relationship)
            
            logging.info(f"Extracted {graph.number_of_nodes()} components and {graph.number_of_edges()} relationships")
            return graph
        
        except Exception as e:
            logging.error(f"Error extracting component relationships: {str(e)}")
            return nx.DiGraph()

    def extract_module_dependencies(self) -> nx.DiGraph:
        """
        Extract module dependencies from the knowledge graph.
        
        Returns:
            nx.DiGraph: A directed graph of module dependencies
        """
        logging.info("Extracting module dependencies...")
        
        # Query to get all modules and their dependencies
        query = """
        MATCH (m1:Module)-[r]->(m2:Module)
        RETURN m1.name as source, m2.name as target, type(r) as relationship
        """
        
        try:
            results = self.client.run_query(query)
            
            # Create a directed graph
            graph = nx.DiGraph()
            
            # Add nodes and edges
            for record in results:
                source = record.get("source", "Unknown")
                target = record.get("target", "Unknown")
                relationship = record.get("relationship", "UNKNOWN")
                
                graph.add_node(source)
                graph.add_node(target)
                graph.add_edge(source, target, relationship=relationship)
            
            logging.info(f"Extracted {graph.number_of_nodes()} modules and {graph.number_of_edges()} dependencies")
            return graph
        
        except Exception as e:
            logging.error(f"Error extracting module dependencies: {str(e)}")
            return nx.DiGraph()

    def extract_migration_patterns(self) -> Dict:
        """
        Extract migration patterns from the knowledge graph.
        
        Returns:
            Dict: Migration statistics and patterns
        """
        logging.info("Extracting migration patterns...")
        
        # Query to get migration statistics
        query = """
        MATCH (p:PythonEquivalent)-[:EQUIVALENT_TO]->(b:BashOriginal)
        RETURN COUNT(DISTINCT b) as migrated_files
        """
        
        # Query to get total bash files
        bash_query = """
        MATCH (b:BashOriginal)
        RETURN COUNT(b) as total_bash_files
        """
        
        # Query to get transformation types
        transform_query = """
        MATCH (t:CodeTransformation)
        RETURN t.transformation_type as type, COUNT(t) as count
        """
        
        try:
            # Get migration statistics
            results = self.client.run_query(query)
            migrated_files = results[0].get("migrated_files", 0) if results else 0
            
            # Get total bash files
            bash_results = self.client.run_query(bash_query)
            total_bash_files = bash_results[0].get("total_bash_files", 0) if bash_results else 0
            
            # Calculate migration progress
            migration_progress = 0
            if total_bash_files > 0:
                migration_progress = (migrated_files / total_bash_files) * 100
            
            # Get transformation types
            transform_results = self.client.run_query(transform_query)
            transformation_types = {
                record.get("type", "Unknown"): record.get("count", 0)
                for record in transform_results
            }
            
            # Compile results
            migration_patterns = {
                "total_bash_files": total_bash_files,
                "migrated_files": migrated_files,
                "migration_progress": migration_progress,
                "transformation_types": transformation_types
            }
            
            logging.info(f"Migration progress: {migration_progress:.2f}%")
            return migration_patterns
        
        except Exception as e:
            logging.error(f"Error extracting migration patterns: {str(e)}")
            return {
                "total_bash_files": 0,
                "migrated_files": 0,
                "migration_progress": 0,
                "transformation_types": {}
            }

    def visualize_component_relationships(self, graph: nx.DiGraph) -> str:
        """
        Visualize component relationships.
        
        Args:
            graph: A directed graph of component relationships
            
        Returns:
            str: Path to the generated visualization
        """
        logging.info("Visualizing component relationships...")
        
        if graph.number_of_nodes() == 0:
            logging.warn("No components to visualize")
            return ""
        
        # Use the create_network_graph utility function
        output_path = self.output_dir / "component_relationships.png"
        result = create_network_graph(
            graph=graph,
            output_path=str(output_path),
            title="Component Relationships",
            node_color='lightblue',
            figsize=(12, 10)
        )
        
        return result

    def visualize_module_dependencies(self, graph: nx.DiGraph) -> str:
        """
        Visualize module dependencies.
        
        Args:
            graph: A directed graph of module dependencies
            
        Returns:
            str: Path to the generated visualization
        """
        logging.info("Visualizing module dependencies...")
        
        if graph.number_of_nodes() == 0:
            logging.warn("No modules to visualize")
            return ""
        
        # Use the create_network_graph utility function
        output_path = self.output_dir / "module_dependencies.png"
        result = create_network_graph(
            graph=graph,
            output_path=str(output_path),
            title="Module Dependencies",
            node_color='lightgreen',
            figsize=(12, 10)
        )
        
        return result

    def visualize_migration_progress(self, migration_patterns: Dict) -> str:
        """
        Visualize migration progress.
        
        Args:
            migration_patterns: Migration statistics and patterns
            
        Returns:
            str: Path to the generated visualization
        """
        logging.info("Visualizing migration progress...")
        
        # Prepare data for the pie chart
        labels = ['Migrated', 'Not Migrated']
        sizes = [
            migration_patterns['migrated_files'],
            migration_patterns['total_bash_files'] - migration_patterns['migrated_files']
        ]
        colors = ['#66b3ff', '#ff9999']
        explode = [0.1, 0]  # explode the 1st slice (Migrated)
        
        # Use the create_pie_chart utility function
        output_path = self.output_dir / "migration_progress.png"
        result = create_pie_chart(
            sizes=sizes,
            labels=labels,
            output_path=str(output_path),
            title=f"Migration Progress: {migration_patterns['migration_progress']:.2f}%",
            colors=colors,
            explode=explode,
            figsize=(10, 6)
        )
        
        return result

    def visualize_transformation_types(self, migration_patterns: Dict) -> str:
        """
        Visualize transformation types.
        
        Args:
            migration_patterns: Migration statistics and patterns
            
        Returns:
            str: Path to the generated visualization
        """
        logging.info("Visualizing transformation types...")
        
        transformation_types = migration_patterns.get('transformation_types', {})
        
        if not transformation_types:
            logging.warn("No transformation types to visualize")
            return ""
        
        # Use the create_bar_chart utility function
        output_path = self.output_dir / "transformation_types.png"
        result = create_bar_chart(
            data=transformation_types,
            output_path=str(output_path),
            title='Code Transformation Types',
            xlabel='Transformation Type',
            ylabel='Count',
            color='skyblue',
            figsize=(12, 8),
            rotate_labels=True
        )
        
        return result

    def generate_architecture_report(self) -> str:
        """
        Generate a comprehensive architecture report.
        
        Returns:
            str: Path to the generated report
        """
        logging.info("Generating architecture report...")
        
        # Extract data
        component_graph = self.extract_component_relationships()
        module_graph = self.extract_module_dependencies()
        migration_patterns = self.extract_migration_patterns()
        
        # Generate visualizations
        component_viz = self.visualize_component_relationships(component_graph)
        module_viz = self.visualize_module_dependencies(module_graph)
        migration_viz = self.visualize_migration_progress(migration_patterns)
        transformation_viz = self.visualize_transformation_types(migration_patterns)
        
        # Create report
        report = {
            "timestamp": datetime.now().isoformat(),
            "component_analysis": {
                "node_count": component_graph.number_of_nodes(),
                "edge_count": component_graph.number_of_edges(),
                "visualization": component_viz
            },
            "module_analysis": {
                "node_count": module_graph.number_of_nodes(),
                "edge_count": module_graph.number_of_edges(),
                "visualization": module_viz
            },
            "migration_analysis": {
                "total_bash_files": migration_patterns['total_bash_files'],
                "migrated_files": migration_patterns['migrated_files'],
                "migration_progress": migration_patterns['migration_progress'],
                "transformation_types": migration_patterns['transformation_types'],
                "migration_visualization": migration_viz,
                "transformation_visualization": transformation_viz
            }
        }
        
        # Save report as JSON using file_utils
        report_path = self.output_dir / "architecture_report.json"
        success = write_file(str(report_path), json.dumps(report, indent=2))
        
        logging.info(f"Architecture report saved to {report_path}")
        return str(report_path)

    def analyze_component_structure(self) -> Dict:
        """
        Analyze the component structure of the system.
        
        Returns:
            Dict: Component structure analysis
        """
        logging.info("Analyzing component structure...")
        
        # Query to get all components by type
        query = """
        MATCH (c:Component)
        RETURN labels(c) as types, COUNT(c) as count
        """
        
        # Query to get component relationships by type
        rel_query = """
        MATCH (c1:Component)-[r]->(c2:Component)
        RETURN type(r) as relationship, COUNT(r) as count
        """
        
        try:
            # Get component types
            results = self.client.run_query(query)
            component_types = {}
            
            for record in results:
                types = record.get("types", [])
                count = record.get("count", 0)
                
                for type_label in types:
                    if type_label != "Entity" and type_label != "Component":
                        component_types[type_label] = component_types.get(type_label, 0) + count
            
            # Get relationship types
            rel_results = self.client.run_query(rel_query)
            relationship_types = {
                record.get("relationship", "Unknown"): record.get("count", 0)
                for record in rel_results
            }
            
            # Compile results
            structure_analysis = {
                "component_types": component_types,
                "relationship_types": relationship_types
            }
            
            logging.info(f"Found {len(component_types)} component types and {len(relationship_types)} relationship types")
            return structure_analysis
        
        except Exception as e:
            logging.error(f"Error analyzing component structure: {str(e)}")
            return {
                "component_types": {},
                "relationship_types": {}
            }

    def visualize_component_structure(self, structure_analysis: Dict) -> str:
        """
        Visualize component structure.
        
        Args:
            structure_analysis: Component structure analysis
            
        Returns:
            str: Path to the generated visualization
        """
        logging.info("Visualizing component structure...")
        
        component_types = structure_analysis.get('component_types', {})
        
        if not component_types:
            logging.warn("No component types to visualize")
            return ""
        
        # Use the create_bar_chart utility function
        output_path = self.output_dir / "component_structure.png"
        result = create_bar_chart(
            data=component_types,
            output_path=str(output_path),
            title='Component Types Distribution',
            xlabel='Component Type',
            ylabel='Count',
            color='lightblue',
            figsize=(12, 8),
            rotate_labels=True
        )
        
        return result

    def generate_html_report(self, results: Dict) -> str:
        """
        Generate an HTML report from the analysis results.
        
        Args:
            results: Analysis results
            
        Returns:
            str: Path to the generated HTML report
        """
        logging.info("Generating HTML report...")
        # Read the template using file_utils
        template_path = Path("architecture_report_template.html")
        success, template = read_file(str(template_path))
        if not success:
            logging.error(f"Template file not found: {template_path}")
            return ""
            template = f.read()
        
        # Prepare data for template
        component_count = results["component_analysis"]["node_count"]
        module_count = results["module_analysis"]["node_count"]
        component_relationship_count = results["component_analysis"]["edge_count"]
        module_dependency_count = results["module_analysis"]["edge_count"]
        migration_progress = results["migration_analysis"]["migration_progress"]
        total_bash_files = results["migration_analysis"]["total_bash_files"]
        migrated_files = results["migration_analysis"]["migrated_files"]
        relationship_types_count = len(results["structure_analysis"]["relationship_types"])
        
        # Get visualization paths
        component_visualization = results["component_analysis"]["visualization"]
        module_visualization = results["module_analysis"]["visualization"]
        migration_visualization = results["migration_analysis"]["migration_visualization"]
        transformation_visualization = results["migration_analysis"]["transformation_visualization"]
        component_structure_visualization = results["structure_analysis"]["visualization"]
        
        # Make paths relative to the output directory
        component_visualization = os.path.basename(component_visualization)
        module_visualization = os.path.basename(module_visualization)
        migration_visualization = os.path.basename(migration_visualization)
        transformation_visualization = os.path.basename(transformation_visualization)
        component_structure_visualization = os.path.basename(component_structure_visualization)
        
        # Replace placeholders in the template
        replacements = {
            "{{timestamp}}": results["timestamp"],
            "{{component_count}}": str(component_count),
            "{{module_count}}": str(module_count),
            "{{migration_progress}}": f"{migration_progress:.2f}",
            "{{relationship_types_count}}": str(relationship_types_count),
            "{{component_relationship_count}}": str(component_relationship_count),
            "{{module_dependency_count}}": str(module_dependency_count),
            "{{total_bash_files}}": str(total_bash_files),
            "{{migrated_files}}": str(migrated_files),
            "{{component_visualization}}": f"architecture_analysis/{component_visualization}",
            "{{module_visualization}}": f"architecture_analysis/{module_visualization}",
            "{{migration_visualization}}": f"architecture_analysis/{migration_visualization}",
            "{{transformation_visualization}}": f"architecture_analysis/{transformation_visualization}",
            "{{component_structure_visualization}}": f"architecture_analysis/{component_structure_visualization}"
        }
        
        # Apply replacements
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)
        
        # Write the report using file_utils
        report_path = self.output_dir / "architecture_report.html"
        success = write_file(str(report_path), template)
        
        logging.info(f"HTML report saved to {report_path}")
        return str(report_path)
    
    def run_analysis(self) -> Dict:
        """
        Run the complete architecture analysis.
        
        Returns:
            Dict: Analysis results
        """
        logging.info("Running architecture analysis...")
        
        # Extract and visualize component relationships
        component_graph = self.extract_component_relationships()
        component_viz = self.visualize_component_relationships(component_graph)
        
        # Extract and visualize module dependencies
        module_graph = self.extract_module_dependencies()
        module_viz = self.visualize_module_dependencies(module_graph)
        
        # Extract and visualize migration patterns
        migration_patterns = self.extract_migration_patterns()
        migration_viz = self.visualize_migration_progress(migration_patterns)
        transformation_viz = self.visualize_transformation_types(migration_patterns)
        
        # Analyze and visualize component structure
        structure_analysis = self.analyze_component_structure()
        structure_viz = self.visualize_component_structure(structure_analysis)
        
        # Compile results
        results = {
            "timestamp": datetime.now().isoformat(),
            "component_analysis": {
                "node_count": component_graph.number_of_nodes(),
                "edge_count": component_graph.number_of_edges(),
                "visualization": component_viz
            },
            "module_analysis": {
                "node_count": module_graph.number_of_nodes(),
                "edge_count": module_graph.number_of_edges(),
                "visualization": module_viz
            },
            "migration_analysis": {
                "total_bash_files": migration_patterns['total_bash_files'],
                "migrated_files": migration_patterns['migrated_files'],
                "migration_progress": migration_patterns['migration_progress'],
                "transformation_types": migration_patterns['transformation_types'],
                "migration_visualization": migration_viz,
                "transformation_visualization": transformation_viz
            },
            "structure_analysis": {
                "component_types": structure_analysis['component_types'],
                "relationship_types": structure_analysis['relationship_types'],
                "visualization": structure_viz
            }
        }
        
        # Save results as JSON using file_utils
        results_path = self.output_dir / "architecture_analysis.json"
        success = write_file(str(results_path), json.dumps(results, indent=2))
        
        logging.info(f"Architecture analysis results saved to {results_path}")
        return results


def main():
    """Main function."""
    logging.info("Starting architecture analysis...")
    
    # Create and run the architecture analyzer
    analyzer = ArchitectureAnalyzer()
    results = analyzer.run_analysis()
    
    # Generate HTML report
    html_report = analyzer.generate_html_report(results)
    
    # Print summary
    print("\n" + "=" * 80)
    print("Architecture Analysis Summary:")
    print("=" * 80)
    
    # Component analysis
    print(f"\nComponent Analysis:")
    print(f"  - Components: {results['component_analysis']['node_count']}")
    print(f"  - Relationships: {results['component_analysis']['edge_count']}")
    
    # Module analysis
    print(f"\nModule Analysis:")
    print(f"  - Modules: {results['module_analysis']['node_count']}")
    print(f"  - Dependencies: {results['module_analysis']['edge_count']}")
    
    # Migration analysis
    print(f"\nMigration Analysis:")
    print(f"  - Total Bash Files: {results['migration_analysis']['total_bash_files']}")
    print(f"  - Migrated Files: {results['migration_analysis']['migrated_files']}")
    print(f"  - Migration Progress: {results['migration_analysis']['migration_progress']:.2f}%")
    
    # Structure analysis
    print(f"\nStructure Analysis:")
    print(f"  - Component Types: {len(results['structure_analysis']['component_types'])}")
    print(f"  - Relationship Types: {len(results['structure_analysis']['relationship_types'])}")
    print("\n" + "=" * 80)
    print(f"Visualizations and detailed results saved to: {analyzer.output_dir}")
    print(f"HTML report available at: {html_report}")
    print("=" * 80)
    
    
    logging.info("Architecture analysis completed successfully")


if __name__ == "__main__":
    main()