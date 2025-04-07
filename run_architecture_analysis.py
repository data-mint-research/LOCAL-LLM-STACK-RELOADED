#!/usr/bin/env python3
"""
Run Architecture Analysis for LOCAL-LLM-STACK-RELOADED

This script is a wrapper around the architecture_analysis.py script that provides
a more user-friendly interface for running the architecture analysis.
"""

import os
import sys
import argparse
import webbrowser
from pathlib import Path

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the utility modules
from llm_stack.core import logging
from llm_stack.core.file_utils import ensure_directory_exists


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run architecture analysis for LOCAL-LLM-STACK-RELOADED"
    )
    
    parser.add_argument(
        "--open-report",
        action="store_true",
        help="Open the HTML report in a web browser after analysis"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="architecture_analysis",
        help="Directory to store analysis results (default: architecture_analysis)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def run_analysis(args):
    """Run the architecture analysis."""
    try:
        # Import the architecture analysis module
        from architecture_analysis import ArchitectureAnalyzer
        
        # Set verbose logging if requested
        if args.verbose:
            logging.set_verbose(True)
        
        logging.info("Starting architecture analysis...")
        
        # Create output directory if it doesn't exist using file_utils
        output_dir = Path(args.output_dir)
        ensure_directory_exists(str(output_dir))
        
        # Create and run the architecture analyzer
        analyzer = ArchitectureAnalyzer()
        analyzer.output_dir = output_dir  # Override the default output directory
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
        print(f"Visualizations and detailed results saved to: {output_dir}")
        print(f"HTML report available at: {html_report}")
        print("=" * 80)
        
        # Open the HTML report in a web browser if requested
        if args.open_report and html_report:
            html_report_path = Path(html_report)
            # Use file_utils to check if the file exists
            if os.path.isfile(str(html_report_path)):
                webbrowser.open(f"file://{html_report_path.absolute()}")
                print(f"\nOpened HTML report in web browser: {html_report_path}")
            else:
                logging.error(f"HTML report not found: {html_report_path}")
        
        logging.info("Architecture analysis completed successfully")
        return 0
    
    except ImportError as e:
        logging.error(f"Failed to import required modules: {str(e)}")
        print("\nPlease make sure you have installed the required dependencies:")
        print("  - matplotlib")
        print("  - networkx")
        print("  - neo4j")
        return 1
    
    except Exception as e:
        logging.error(f"Error running architecture analysis: {str(e)}")
        return 1


def main():
    """Main function."""
    args = parse_arguments()
    return run_analysis(args)


if __name__ == "__main__":
    sys.exit(main())