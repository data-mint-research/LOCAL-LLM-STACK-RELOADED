"""
Visualization utilities for the LLM Stack.

This module provides common functions for creating visualizations
with consistent styling and error handling.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import networkx as nx

from llm_stack.core import logging


def create_directory(output_dir: Union[str, Path]) -> Path:
    """
    Create a directory for visualizations if it doesn't exist.

    Args:
        output_dir: Path to the output directory

    Returns:
        Path: Path object for the output directory
    """
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True)
    return output_dir


def create_network_graph(
    graph: nx.DiGraph,
    output_path: Union[str, Path],
    title: str,
    node_color: str = 'lightblue',
    figsize: Tuple[int, int] = (12, 10)
) -> str:
    """
    Create and save a network graph visualization.

    Args:
        graph: NetworkX graph to visualize
        output_path: Path to save the visualization
        title: Title for the visualization
        node_color: Color for the nodes
        figsize: Figure size (width, height)

    Returns:
        str: Path to the saved visualization
    """
    logging.info(f"Creating network graph visualization: {title}")
    
    if graph.number_of_nodes() == 0:
        logging.warn(f"No nodes to visualize for: {title}")
        return ""
    
    try:
        # Create a figure
        plt.figure(figsize=figsize)
        
        # Create a layout for the graph
        pos = nx.spring_layout(graph, seed=42)
        
        # Draw the graph
        nx.draw(graph, pos, with_labels=True, node_color=node_color, 
                node_size=1500, font_size=10, font_weight='bold', 
                arrowsize=15, width=2, edge_color='gray')
        
        # Draw edge labels
        edge_labels = {(u, v): d.get('relationship', '') for u, v, d in graph.edges(data=True)}
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=8)
        
        # Set title
        plt.title(title, fontsize=16)
        
        # Save the figure
        plt.savefig(output_path)
        plt.close()
        
        logging.info(f"Network graph visualization saved to {output_path}")
        return str(output_path)
    
    except Exception as e:
        logging.error(f"Error creating network graph visualization: {str(e)}")
        return ""


def create_bar_chart(
    data: Dict[str, Union[int, float]],
    output_path: Union[str, Path],
    title: str,
    xlabel: str,
    ylabel: str,
    color: str = 'skyblue',
    figsize: Tuple[int, int] = (12, 8),
    rotate_labels: bool = True
) -> str:
    """
    Create and save a bar chart visualization.

    Args:
        data: Dictionary of labels and values
        output_path: Path to save the visualization
        title: Title for the visualization
        xlabel: Label for the x-axis
        ylabel: Label for the y-axis
        color: Color for the bars
        figsize: Figure size (width, height)
        rotate_labels: Whether to rotate x-axis labels

    Returns:
        str: Path to the saved visualization
    """
    logging.info(f"Creating bar chart visualization: {title}")
    
    if not data:
        logging.warn(f"No data to visualize for: {title}")
        return ""
    
    try:
        # Create a figure
        plt.figure(figsize=figsize)
        
        # Create a bar chart
        labels = list(data.keys())
        values = list(data.values())
        
        plt.bar(labels, values, color=color)
        
        # Add labels and title
        plt.xlabel(xlabel, fontsize=12)
        plt.ylabel(ylabel, fontsize=12)
        plt.title(title, fontsize=16)
        
        # Rotate x-axis labels for better readability if needed
        if rotate_labels:
            plt.xticks(rotation=45, ha='right')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the figure
        plt.savefig(output_path)
        plt.close()
        
        logging.info(f"Bar chart visualization saved to {output_path}")
        return str(output_path)
    
    except Exception as e:
        logging.error(f"Error creating bar chart visualization: {str(e)}")
        return ""


def create_pie_chart(
    sizes: List[Union[int, float]],
    labels: List[str],
    output_path: Union[str, Path],
    title: str,
    colors: List[str] = None,
    explode: List[float] = None,
    figsize: Tuple[int, int] = (10, 6)
) -> str:
    """
    Create and save a pie chart visualization.

    Args:
        sizes: List of values for each slice
        labels: List of labels for each slice
        output_path: Path to save the visualization
        title: Title for the visualization
        colors: List of colors for each slice
        explode: List of explode values for each slice
        figsize: Figure size (width, height)

    Returns:
        str: Path to the saved visualization
    """
    logging.info(f"Creating pie chart visualization: {title}")
    
    if not sizes or not labels:
        logging.warn(f"No data to visualize for: {title}")
        return ""
    
    try:
        # Create a figure
        plt.figure(figsize=figsize)
        
        # Default colors if not provided
        if colors is None:
            colors = ['#66b3ff', '#ff9999', '#99ff99', '#ffcc99', '#c2c2f0']
        
        # Create a pie chart
        plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct='%1.1f%%', shadow=True, startangle=90)
        
        # Equal aspect ratio ensures that pie is drawn as a circle
        plt.axis('equal')
        
        # Set title
        plt.title(title, fontsize=16)
        
        # Save the figure
        plt.savefig(output_path)
        plt.close()
        
        logging.info(f"Pie chart visualization saved to {output_path}")
        return str(output_path)
    
    except Exception as e:
        logging.error(f"Error creating pie chart visualization: {str(e)}")
        return ""


def create_line_chart(
    x_values: List[Union[int, float, str]],
    y_values: List[Union[int, float]],
    output_path: Union[str, Path],
    title: str,
    xlabel: str,
    ylabel: str,
    color: str = 'blue',
    marker: str = 'o',
    figsize: Tuple[int, int] = (12, 8)
) -> str:
    """
    Create and save a line chart visualization.

    Args:
        x_values: List of x-axis values
        y_values: List of y-axis values
        output_path: Path to save the visualization
        title: Title for the visualization
        xlabel: Label for the x-axis
        ylabel: Label for the y-axis
        color: Color for the line
        marker: Marker style for data points
        figsize: Figure size (width, height)

    Returns:
        str: Path to the saved visualization
    """
    logging.info(f"Creating line chart visualization: {title}")
    
    if not x_values or not y_values:
        logging.warn(f"No data to visualize for: {title}")
        return ""
    
    try:
        # Create a figure
        plt.figure(figsize=figsize)
        
        # Create a line chart
        plt.plot(x_values, y_values, color=color, marker=marker)
        
        # Add labels and title
        plt.xlabel(xlabel, fontsize=12)
        plt.ylabel(ylabel, fontsize=12)
        plt.title(title, fontsize=16)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the figure
        plt.savefig(output_path)
        plt.close()
        
        logging.info(f"Line chart visualization saved to {output_path}")
        return str(output_path)
    
    except Exception as e:
        logging.error(f"Error creating line chart visualization: {str(e)}")
        return ""