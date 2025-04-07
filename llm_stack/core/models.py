"""
Model management for the LLM Stack.

This module provides functions for managing LLM models,
including listing, adding, and removing models.
"""

import functools
import json
import sys
import time
from typing import Dict, List, Optional, Union, Any, Callable

import requests
from rich.console import Console
from rich.table import Table

from llm_stack.core import error, logging

# Rich console for formatted output
CONSOLE = Console()

# Cache for model information
_MODEL_CACHE = {}
_MODEL_CACHE_TTL = 300  # Cache TTL in seconds (5 minutes)
_MODEL_LIST_CACHE = None
_MODEL_LIST_TIMESTAMP = 0


def check_ollama_running(ollama_url: str) -> bool:
    """
    Checks if the Ollama service is running.

    Args:
        ollama_url: URL of the Ollama service

    Returns:
        bool: True if the Ollama service is running, False otherwise
    """
    try:
        response = requests.get(f"{ollama_url}/api/version", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def cache_model_info(func: Callable) -> Callable:
    """
    Decorator to cache model information.
    
    Args:
        func: Function to decorate
        
    Returns:
        Callable: Decorated function
    """
    @functools.wraps(func)
    def wrapper(ollama_url: str, model_name: str):
        cache_key = f"{ollama_url}:{model_name}"
        
        # Check cache
        if cache_key in _MODEL_CACHE:
            model_info, timestamp = _MODEL_CACHE[cache_key]
            if time.time() - timestamp < _MODEL_CACHE_TTL:
                return model_info
        
        # Call original function
        result = func(ollama_url, model_name)
        
        # Update cache
        if result is not None:
            _MODEL_CACHE[cache_key] = (result, time.time())
            
        return result
    
    return wrapper

def list_models(ollama_url: str) -> List[Dict[str, str]]:
    """
    Lists available models with caching.

    Args:
        ollama_url: URL of the Ollama service

    Returns:
        List[Dict[str, str]]: List of model information
    """
    global _MODEL_LIST_CACHE, _MODEL_LIST_TIMESTAMP
    
    logging.info("Listing available models...")

    # Check if we have a cached model list that's still valid
    if _MODEL_LIST_CACHE is not None and time.time() - _MODEL_LIST_TIMESTAMP < _MODEL_CACHE_TTL:
        logging.debug("Using cached model list")
        models = _MODEL_LIST_CACHE
    else:
        try:
            response = requests.get(f"{ollama_url}/api/tags", timeout=10)
            if response.status_code != 200:
                logging.error(
                    f"Error listing models. Ollama API returned an error: {response.text}"
                )
                return []

            data = response.json()
            models = data.get("models", [])
            
            # Update cache
            _MODEL_LIST_CACHE = models
            _MODEL_LIST_TIMESTAMP = time.time()
            
        except requests.RequestException as e:
            logging.error(f"Error listing models: {str(e)}")
            return []

    # Display models in a table
    table = Table(title="Available Models")
    table.add_column("Name", style="cyan")
    table.add_column("Size", style="green")
    table.add_column("Modified", style="yellow")

    for model in models:
        table.add_row(
            model.get("name", "Unknown"),
            format_size(model.get("size", 0)),
            model.get("modified", "Unknown"),
        )

    CONSOLE.print(table)

    # Display helpful tips
    CONSOLE.print()
    logging.info(
        "Tip: Add a model with 'llm models add model_name'"
    )

    return models


def add_model(ollama_url: str, model_name: str) -> bool:
    """
    Adds a model.

    Args:
        ollama_url: URL of the Ollama service
        model_name: Name of the model

    Returns:
        bool: True if the model was successfully added, False otherwise
    """
    logging.info(f"Adding model {model_name}...")
    logging.warn("This may take a while depending on the model size...")

    try:
        response = requests.post(
            f"{ollama_url}/api/pull",
            json={"name": model_name},
            timeout=600,  # Longer timeout for large models
        )

        if response.status_code != 200:
            logging.error(
                f"Error adding model {model_name}. Ollama API returned an error: {response.text}"
            )
            return False

        logging.success(f"Model {model_name} successfully added.")
        logging.info(
            "Tip: Use 'llm models list' to display all available models"
        )
        return True
    except requests.RequestException as e:
        logging.error(f"Error adding model {model_name}: {str(e)}")
        return False


def remove_model(ollama_url: str, model_name: str) -> bool:
    """
    Removes a model.

    Args:
        ollama_url: URL of the Ollama service
        model_name: Name of the model

    Returns:
        bool: True if the model was successfully removed, False otherwise
    """
    logging.info(f"Removing model {model_name}...")

    try:
        response = requests.delete(
            f"{ollama_url}/api/delete", json={"name": model_name}, timeout=30
        )

        if response.status_code != 200:
            logging.error(
                f"Error removing model {model_name}. Ollama API returned an error: {response.text}"
            )
            return False

        logging.success(f"Model {model_name} successfully removed.")
        return True
    except requests.RequestException as e:
        logging.error(f"Error removing model {model_name}: {str(e)}")
        return False


@cache_model_info
def get_model_info(
    ollama_url: str, model_name: str
) -> Optional[Dict[str, Union[str, int]]]:
    """
    Gets information about a model with caching.

    Args:
        ollama_url: URL of the Ollama service
        model_name: Name of the model

    Returns:
        Optional[Dict[str, Union[str, int]]]: Model information or None if the model was not found
    """
    try:
        # Check if we have a cached model list
        global _MODEL_LIST_CACHE, _MODEL_LIST_TIMESTAMP
        
        if _MODEL_LIST_CACHE is not None and time.time() - _MODEL_LIST_TIMESTAMP < _MODEL_CACHE_TTL:
            # Search in cached model list first
            for model in _MODEL_LIST_CACHE:
                if model.get("name") == model_name:
                    return model
        
        # If not found in cache or cache expired, get list of all models
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        if response.status_code != 200:
            logging.error(
                f"Error retrieving model information. Ollama API returned an error: {response.text}"
            )
            return None

        data = response.json()
        models = data.get("models", [])
        
        # Update model list cache
        _MODEL_LIST_CACHE = models
        _MODEL_LIST_TIMESTAMP = time.time()

        # Search for the specified model
        for model in models:
            if model.get("name") == model_name:
                return model

        logging.error(f"Model {model_name} not found")
        return None
    except requests.RequestException as e:
        logging.error(f"Error retrieving model information: {str(e)}")
        return None


def format_size(size_bytes: int) -> str:
    """
    Formats a size in bytes into a readable form.

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Formatted size
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def generate_model_completion(
    ollama_url: str, model_name: str, prompt: str, options: Optional[Dict] = None
) -> Optional[str]:
    """
    Generates a completion with a model.

    Args:
        ollama_url: URL of the Ollama service
        model_name: Name of the model
        prompt: Input prompt
        options: Options for generation

    Returns:
        Optional[str]: Generated completion or None if an error occurred
    """
    if options is None:
        options = {}

    try:
        # Verify model exists before sending request
        if get_model_info(ollama_url, model_name) is None:
            logging.error(f"Model {model_name} not found")
            return None
            
        payload = {"model": model_name, "prompt": prompt, **options}

        response = requests.post(f"{ollama_url}/api/generate", json=payload, timeout=60)

        if response.status_code != 200:
            logging.error(
                f"Error during generation. Ollama API returned an error: {response.text}"
            )
            return None

        data = response.json()
        return data.get("response", "")
    except requests.RequestException as e:
        logging.error(f"Error during generation: {str(e)}")
        return None


def chat_with_model(
    ollama_url: str,
    model_name: str,
    messages: List[Dict[str, str]],
    options: Optional[Dict] = None,
) -> Optional[str]:
    """
    Chats with a model.

    Args:
        ollama_url: URL of the Ollama service
        model_name: Name of the model
        messages: List of messages (each with 'role' and 'content')
        options: Options for the chat

    Returns:
        Optional[str]: Model response or None if an error occurred
    """
    if options is None:
        options = {}

    try:
        # Verify model exists before sending request
        if get_model_info(ollama_url, model_name) is None:
            logging.error(f"Model {model_name} not found")
            return None
            
        payload = {"model": model_name, "messages": messages, **options}

        response = requests.post(f"{ollama_url}/api/chat", json=payload, timeout=60)

        if response.status_code != 200:
            logging.error(
                f"Error during chat. Ollama API returned an error: {response.text}"
            )
            return None

        data = response.json()
        return data.get("message", {}).get("content", "")
    except requests.RequestException as e:
        logging.error(f"Error during chat: {str(e)}")
        return None


def create_model(ollama_url: str, model_name: str, modelfile_content: str) -> bool:
    """
    Creates a custom model.

    Args:
        ollama_url: URL of the Ollama service
        model_name: Name of the model
        modelfile_content: Content of the model file

    Returns:
        bool: True if the model was successfully created, False otherwise
    """
    logging.info(f"Creating custom model {model_name}...")

    try:
        response = requests.post(
            f"{ollama_url}/api/create",
            json={"name": model_name, "modelfile": modelfile_content},
            timeout=600,  # Longer timeout for model creation
        )

        if response.status_code != 200:
            logging.error(
                f"Error creating model {model_name}. Ollama API returned an error: {response.text}"
            )
            return False

        logging.success(f"Model {model_name} successfully created.")
        return True
    except requests.RequestException as e:
        logging.error(f"Error creating model {model_name}: {str(e)}")
        return False


logging.debug("Model management module initialized")
