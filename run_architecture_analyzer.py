#!/usr/bin/env python3
"""
Run Architecture Analyzer for LOCAL-LLM-STACK-RELOADED

This script runs the architecture analyzer and generates a comprehensive report
on the project's architecture, including:

1. Architecture Baseline Analysis
2. Component Analysis
3. Pattern & Convention Analysis
4. Orphaned Files Impact Assessment
5. Gap Analysis
6. Recommendations Development
"""

import os
import sys
import json
import argparse
import webbrowser
from pathlib import Path
from datetime import datetime

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the utility modules
from llm_stack.core import logging
from llm_stack.core.file_utils import read_file, write_file, ensure_directory_exists

# Import the architecture analyzer
from architecture_analyzer import ArchitectureAnalyzer


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


def generate_html_report(results, output_dir):
    """
    Generate an HTML report from the analysis results.
    
    Args:
        results: Analysis results
        output_dir: Output directory
        
    Returns:
        str: Path to the generated HTML report
    """
    logging.info("Generating HTML report...")
    
    # Read the enhanced template
    template_path = Path("architecture_report_template_enhanced.html")
    success, template = read_file(str(template_path))
    
    if not success:
        logging.error(f"Template file not found: {template_path}")
        return ""
    
    # Use the template as is - it already has all the sections we need
    enhanced_template = template
    
    # The enhanced template already has all the JavaScript we need
    
    # No need to replace the script section - the enhanced template already has all the JavaScript we need
    
    # Add timestamp
    timestamp = datetime.now().isoformat()
    enhanced_template = enhanced_template.replace('{{timestamp}}', timestamp)
    
    # Write the enhanced template to a file
    output_path = Path(output_dir) / "architecture_report.html"
    write_file(str(output_path), enhanced_template)
    
    # Copy the results JSON file to the output directory
    results_path = Path(output_dir) / "architecture_analysis_results.json"
    write_file(str(results_path), json.dumps(results, indent=2))
    
    logging.info(f"HTML report saved to {output_path}")
    return str(output_path)


def run_analysis(args):
    """Run the architecture analysis."""
    try:
        # Set verbose logging if requested
        if args.verbose:
            logging.set_verbose(True)
        
        logging.info("Starting architecture analysis...")
        
        # Create output directory if it doesn't exist
        output_dir = Path(args.output_dir)
        ensure_directory_exists(str(output_dir))
        
        # Create and run the architecture analyzer
        analyzer = ArchitectureAnalyzer()
        analyzer.output_dir = output_dir  # Override the default output directory
        results = analyzer.analyze_architecture()
        
        # Add timestamp to results
        results["timestamp"] = datetime.now().isoformat()
        
        # Generate HTML report
        html_report = generate_html_report(results, output_dir)
        
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
        print(f"Detailed results saved to: {output_dir / 'architecture_analysis_results.json'}")
        print(f"HTML report available at: {html_report}")
        print("=" * 80)
        
        # Open the HTML report in a web browser if requested
        if args.open_report and html_report:
            html_report_path = Path(html_report)
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