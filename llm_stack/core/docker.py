"""
Docker functions for the LLM Stack.

This module provides functions for interacting with Docker and managing
Docker Compose operations.
"""
import functools
import os
import time
import threading
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

from docker.errors import DockerException
from rich.console import Console
from rich.table import Table

import docker
from llm_stack.core import error, logging
from llm_stack.core.command_utils import run_command, check_command_exists

# Cache for Docker operations with improved structure
_cache = {
    'container_status': {'data': {}, 'ttl': 5},  # Cache TTL in seconds
    'container_health': {'data': {}, 'ttl': 3},  # Cache TTL in seconds
    'image_exists': {'data': {}, 'ttl': 60},     # Cache TTL in seconds (1 minute)
    'stats': {'hits': 0, 'misses': 0}            # Cache statistics for monitoring
}
_cache_lock = threading.Lock()  # Global lock for thread safety

# Docker client
try:
    docker_client = docker.from_env()
except DockerException as e:
    logging.error(f"Error initializing Docker client: {str(e)}")
    docker_client = None

# Rich console for formatted output
console = Console()


def cache_docker_result(cache_type: str, ttl: Optional[int] = None) -> Callable:
    """
    Enhanced decorator to cache Docker operation results with better key generation.
    
    Args:
        cache_type: Type of cache to use ('container_status', 'container_health', 'image_exists', or 'custom')
        ttl: Cache TTL in seconds (overrides default TTL for the cache type)
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Use the specified cache or create a new one for custom types
            if cache_type not in _cache and cache_type != 'custom':
                raise ValueError(f"Invalid cache type: {cache_type}")
            
            # For custom cache type, use function-specific cache
            if cache_type == 'custom':
                if not hasattr(wrapper, '_cache'):
                    wrapper._cache = {}
                cache_data = wrapper._cache
                cache_ttl = ttl or 30  # Default TTL for custom caches
            else:
                cache_data = _cache[cache_type]['data']
                cache_ttl = ttl or _cache[cache_type]['ttl']
            
            # Create a more efficient cache key
            # For simple arguments, use direct string representation
            # For complex objects, use their id() to avoid expensive string conversions
            key_parts = [func.__name__]
            
            for arg in args:
                if isinstance(arg, (str, int, float, bool, type(None))):
                    key_parts.append(str(arg))
                else:
                    key_parts.append(f"obj_{id(arg)}")
            
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float, bool, type(None))):
                    key_parts.append(f"{k}={v}")
                else:
                    key_parts.append(f"{k}=obj_{id(v)}")
            
            key = ":".join(key_parts)
            
            # Thread-safe cache access
            with _cache_lock:
                # Check cache
                if key in cache_data:
                    result, timestamp = cache_data[key]
                    if time.time() - timestamp < cache_ttl:
                        _cache['stats']['hits'] += 1
                        return result
                
                _cache['stats']['misses'] += 1
            
            # Call original function
            result = func(*args, **kwargs)
            
            # Update cache
            with _cache_lock:
                cache_data[key] = (result, time.time())
                
                # Implement LRU-like cleanup if cache gets too large
                if len(cache_data) > 1000:  # Arbitrary limit to prevent memory issues
                    # Remove oldest 20% of entries
                    sorted_keys = sorted(cache_data.keys(), key=lambda k: cache_data[k][1])
                    for old_key in sorted_keys[:len(sorted_keys)//5]:
                        del cache_data[old_key]
                
            return result
        
        return wrapper
    
    return decorator

@cache_docker_result(cache_type='custom', ttl=10)
def check_docker_available() -> bool:
    """
    Checks if Docker is available with optimized caching.

    Returns:
        bool: True if Docker is available, False otherwise
    """
    if docker_client is None:
        return False

    try:
        # Use a more lightweight ping operation
        docker_client.ping()
        return True
    except DockerException:
        return False
    except Exception as e:
        logging.error(f"Unexpected error checking Docker availability: {str(e)}")
        return False


@cache_docker_result(cache_type='container_status')
def get_container_status(container_name: str) -> Optional[Dict[str, str]]:
    """
    Gets the status of a container with optimized caching and memory usage.

    Args:
        container_name: Name of the container

    Returns:
        Optional[Dict[str, str]]: Container status or None if the container was not found
    """
    if docker_client is None:
        logging.error("Docker client is not initialized")
        return None

    try:
        # Use more efficient filtering with exact name match
        containers = docker_client.containers.list(
            all=True, filters={"name": f"^{container_name}$"}
        )
        if not containers:
            return None

        container = containers[0]
        
        # Process container data more efficiently with lazy evaluation
        def get_image_tag():
            if container.image.tags:
                return container.image.tags[0]
            return container.image.id[:12]
        
        # Process ports only if they exist, with optimized string building
        def get_ports_str():
            if not container.ports:
                return ""
                
            port_mappings = []
            for port in container.ports:
                if 'PublicPort' in port and 'PrivatePort' in port:
                    port_mappings.append(f"{port['PublicPort']}:{port['PrivatePort']}")
            return ", ".join(port_mappings)
        
        # Build result dictionary with minimal processing
        result = {
            "id": container.id[:12],
            "name": container.name,
            "status": container.status,
            "image": get_image_tag(),
            "ports": get_ports_str(),
        }
        
        return result
    except DockerException as e:
        logging.error(f"Error retrieving container status: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error retrieving container status: {str(e)}")
        return None


@cache_docker_result(cache_type='custom', ttl=5)
def get_all_containers_status() -> List[Dict[str, str]]:
    """
    Gets the status of all containers with optimized processing.

    Returns:
        List[Dict[str, str]]: List of container status dictionaries
    """
    if docker_client is None:
        logging.error("Docker client is not initialized")
        return []

    try:
        # Get all containers in a single API call
        containers = docker_client.containers.list(all=True)
        
        # Process containers in batches to reduce memory pressure
        result = []
        batch_size = 10
        
        for i in range(0, len(containers), batch_size):
            batch = containers[i:i+batch_size]
            
            for container in batch:
                # Process container data efficiently
                container_data = {
                    "id": container.id[:12],
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                    "ports": ""
                }
                
                # Only process ports if they exist
                if container.ports:
                    port_mappings = []
                    for port in container.ports:
                        if 'PublicPort' in port and 'PrivatePort' in port:
                            port_mappings.append(f"{port['PublicPort']}:{port['PrivatePort']}")
                    container_data["ports"] = ", ".join(port_mappings)
                
                result.append(container_data)
        
        return result
    except DockerException as e:
        logging.error(f"Error retrieving container status: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error retrieving all container status: {str(e)}")
        return []


def show_container_status() -> None:
    """Displays the status of all containers in a formatted table."""
    # Get container status with better formatting
    table = Table(title="Container-Status")
    table.add_column("Container", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Ports", style="yellow")

    # Get Docker container status
    containers = get_all_containers_status()

    # Sort by name
    containers.sort(key=lambda c: c["name"])

    # Fill table
    for container in containers:
        table.add_row(
            container["name"], container["status"], container["ports"] or "keine"
        )

    # Display table
    console.print(table)


def _build_compose_command(project_name: str, compose_files: str, command: str, service: str = "") -> List[str]:
    """
    Build a Docker Compose command with proper argument handling.
    
    Args:
        project_name: Name of the project
        compose_files: Docker Compose files (e.g., "-f docker-compose.yml")
        command: The compose command to execute (e.g., "up", "down")
        service: Optional service name
        
    Returns:
        List[str]: Command parts as a list
    """
    cmd_parts = ["docker-compose"]
    
    # Split compose_files to handle multiple files correctly
    if compose_files:
        cmd_parts.extend(compose_files.split())
        
    cmd_parts.extend(["-p", project_name, command])
    
    # Add -d flag for up command
    if command == "up":
        cmd_parts.append("-d")
    
    if service:
        cmd_parts.append(service)
        
    return cmd_parts

def _clear_cache(cache_type: Optional[str] = None) -> None:
    """
    Clear the specified cache or all caches.
    
    Args:
        cache_type: Type of cache to clear or None to clear all caches
    """
    with _cache_lock:
        if cache_type is None:
            # Clear all caches
            for cache_name in ['container_status', 'container_health', 'image_exists']:
                _cache[cache_name]['data'].clear()
        elif cache_type in _cache:
            # Clear specific cache
            _cache[cache_type]['data'].clear()

@cache_docker_result(cache_type='custom', ttl=5)
def compose_up(project_name: str, compose_files: str, service: str = "") -> bool:
    """
    Executes 'docker-compose up' with optimized execution and caching.

    Args:
        project_name: Name of the project
        compose_files: Docker Compose files (e.g., "-f docker-compose.yml")
        service: Optional service name

    Returns:
        bool: True if the command was executed successfully, False otherwise
    """
    # Build command
    cmd_parts = _build_compose_command(project_name, compose_files, "up", service)
    
    # Join command parts for logging
    cmd_str = " ".join(cmd_parts)
    logging.debug(f"Executing: {cmd_str}")

    try:
        # Execute command with timeout to prevent hanging
        returncode, stdout, stderr = run_command(cmd_parts)
        
        if returncode == 0:
            logging.debug(f"Output: {stdout}")
            
            # Clear relevant caches
            _clear_cache('container_status')
            _clear_cache('container_health')
                    
            return True
        else:
            logging.error(f"Error executing 'docker-compose up': {stderr}")
            return False
    except Exception as e:
        logging.error(f"Error executing 'docker-compose up': {str(e)}")
        return False

@cache_docker_result(cache_type='custom', ttl=5)
def compose_down(project_name: str, compose_files: str, service: str = "") -> bool:
    """
    Executes 'docker-compose down' with optimized execution and caching.

    Args:
        project_name: Name of the project
        compose_files: Docker Compose files (e.g., "-f docker-compose.yml")
        service: Optional service name

    Returns:
        bool: True if the command was executed successfully, False otherwise
    """
    # Build command
    cmd_parts = _build_compose_command(project_name, compose_files, "down", service)
    
    # Join command parts for logging
    cmd_str = " ".join(cmd_parts)
    logging.debug(f"Executing: {cmd_str}")

    try:
        # Execute command with timeout to prevent hanging
        returncode, stdout, stderr = run_command(cmd_parts)
        
        if returncode == 0:
            logging.debug(f"Output: {stdout}")
            
            # Clear all caches since down operation affects everything
            _clear_cache()
                    
            return True
        else:
            logging.error(f"Error executing 'docker-compose down': {stderr}")
            return False
    except Exception as e:
        logging.error(f"Error executing 'docker-compose down': {str(e)}")
        return False

def _execute_compose_command(cmd_parts: List[str], error_message: str) -> Optional[str]:
    """
    Execute a Docker Compose command and handle errors consistently.
    
    Args:
        cmd_parts: Command parts as a list
        error_message: Error message prefix for logging
        
    Returns:
        Optional[str]: Command output or None if an error occurred
    """
    # Join command parts for logging only
    cmd_str = " ".join(cmd_parts)
    logging.debug(f"Executing: {cmd_str}")

    try:
        # Execute command
        returncode, stdout, stderr = run_command(cmd_parts)
        
        if returncode == 0:
            return stdout
        else:
            logging.error(f"{error_message}: {stderr}")
            return None
    except Exception as e:
        logging.error(f"{error_message}: {str(e)}")
        return None

def compose_logs(
    project_name: str, compose_files: str, service: str = "", tail: int = 100
) -> Optional[str]:
    """
    Executes 'docker-compose logs'.

    Args:
        project_name: Name of the project
        compose_files: Docker Compose files (e.g., "-f docker-compose.yml")
        service: Optional service name
        tail: Number of lines to display

    Returns:
        Optional[str]: Logs or None if an error occurred
    """
    # Build base command
    cmd_parts = ["docker-compose"]
    
    # Split compose_files to handle multiple files correctly
    if compose_files:
        cmd_parts.extend(compose_files.split())
        
    cmd_parts.extend(["-p", project_name, "logs", f"--tail={tail}"])
    
    if service:
        cmd_parts.append(service)
    
    return _execute_compose_command(cmd_parts, "Error executing 'docker-compose logs'")

def compose_exec(
    project_name: str, compose_files: str, service: str, command: str
) -> Optional[str]:
    """
    Executes 'docker-compose exec'.

    Args:
        project_name: Name of the project
        compose_files: Docker Compose files (e.g., "-f docker-compose.yml")
        service: Service name
        command: Command to execute

    Returns:
        Optional[str]: Output or None if an error occurred
    """
    # Build base command
    cmd_parts = ["docker-compose"]
    
    # Split compose_files to handle multiple files correctly
    if compose_files:
        cmd_parts.extend(compose_files.split())
        
    cmd_parts.extend(["-p", project_name, "exec", "-T", service])
    
    # Split the command into arguments for security
    import shlex
    cmd_parts.extend(shlex.split(command))
    
    return _execute_compose_command(cmd_parts, "Error executing 'docker-compose exec'")

def compose_ps(project_name: str, compose_files: str) -> Optional[str]:
    """
    Executes 'docker-compose ps'.

    Args:
        project_name: Name of the project
        compose_files: Docker Compose files (e.g., "-f docker-compose.yml")

    Returns:
        Optional[str]: Output or None if an error occurred
    """
    # Build base command
    cmd_parts = ["docker-compose"]
    
    # Split compose_files to handle multiple files correctly
    if compose_files:
        cmd_parts.extend(compose_files.split())
        
    cmd_parts.extend(["-p", project_name, "ps"])
    
    return _execute_compose_command(cmd_parts, "Error executing 'docker-compose ps'")

@cache_docker_result(cache_type='custom', ttl=5)
def _get_container_object(container_name: str) -> Optional[Any]:
    """
    Get a container object by name, with optimized caching and error handling.
    
    Args:
        container_name: Name of the container
        
    Returns:
        Optional[Any]: Container object or None if not found
    """
    if docker_client is None:
        logging.error("Docker client is not initialized")
        return None
        
    try:
        # Try to get container ID from status cache to avoid duplicate API calls
        container_id = None
        
        with _cache_lock:
            for key, (data, _) in _cache['container_status']['data'].items():
                if container_name in key and data and "id" in data:
                    container_id = data["id"]
                    break
        
        # If we have a container ID, use it for more efficient lookup
        if container_id:
            containers = docker_client.containers.list(
                all=True, filters={"id": container_id}
            )
            if containers:
                return containers[0]
        
        # If we couldn't find by ID, get the container directly by name with exact match
        containers = docker_client.containers.list(
            all=True, filters={"name": f"^{container_name}$"}
        )
        if not containers:
            return None
            
        return containers[0]
    except DockerException as e:
        logging.error(f"Error retrieving container: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error retrieving container: {str(e)}")
        return None

@cache_docker_result(cache_type='container_health')
def check_container_health(container_name: str) -> Optional[str]:
    """
    Checks the health status of a container with optimized caching.

    Args:
        container_name: Name of the container

    Returns:
        Optional[str]: Health status or None if the container was not found
    """
    # Get container object
    container = _get_container_object(container_name)
    if container is None:
        return None

    try:
        # Get health status efficiently with minimal data retrieval
        # Use low-level API to get only the health status information
        inspection = docker_client.api.inspect_container(
            container.id,
            size=False  # Don't calculate size information (more efficient)
        )
        
        # Extract health status with proper error handling
        if "State" in inspection and "Health" in inspection["State"]:
            return inspection["State"]["Health"]["Status"]
        elif "State" in inspection and "Status" in inspection["State"]:
            # If no health check is defined, return status
            return inspection["State"]["Status"]
        else:
            # Fallback to container status
            return container.status
    except DockerException as e:
        logging.error(f"Error retrieving container health status: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error retrieving container health: {str(e)}")
        return None


def wait_for_container_health(
    container_name: str, target_status: str = "healthy", timeout: int = 60
) -> bool:
    """
    Waits until a container reaches a specific health status.

    Args:
        container_name: Name of the container
        target_status: Target status (e.g., "healthy", "running")
        timeout: Timeout in seconds

    Returns:
        bool: True if the container reached the target status, False otherwise
    """
    import time

    logging.info(f"Waiting for container {container_name} ({target_status})...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        health = check_container_health(container_name)
        if health == target_status:
            logging.success(f"Container {container_name} is {target_status}")
            return True

        # Wait briefly before checking again
        time.sleep(1)

    logging.error(
        f"Timeout waiting for container {container_name} ({target_status})"
    )
    return False


def pull_image(image_name: str, tag: str = "latest") -> bool:
    """
    Pulls a Docker image.

    Args:
        image_name: Name of the image
        tag: Tag of the image

    Returns:
        bool: True if the image was successfully pulled, False otherwise
    """
    if docker_client is None:
        logging.error("Docker client is not initialized")
        return False

    try:
        logging.info(f"Pulling image {image_name}:{tag}...")
        docker_client.images.pull(image_name, tag=tag)
        logging.success(f"Image {image_name}:{tag} successfully pulled")
        return True
    except DockerException as e:
        logging.error(f"Error pulling image {image_name}:{tag}: {str(e)}")
        return False


@cache_docker_result(cache_type='image_exists')
def check_image_exists(image_name: str, tag: str = "latest") -> bool:
    """
    Checks if a Docker image exists with optimized caching.

    Args:
        image_name: Name of the image
        tag: Tag of the image

    Returns:
        bool: True if the image exists, False otherwise
    """
    if docker_client is None:
        logging.error("Docker client is not initialized")
        return False

    try:
        # More efficient image checking with filters
        full_name = f"{image_name}:{tag}"
        
        # Use low-level API for more efficient filtering
        images = docker_client.api.images(
            name=full_name,
            filters={"reference": full_name},
            quiet=True  # Only get IDs, not full image data
        )
        
        return len(images) > 0
    except DockerException as e:
        logging.error(f"Error checking image {image_name}:{tag}: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error checking image: {str(e)}")
        return False


@cache_docker_result(cache_type='custom', ttl=2)  # Short TTL for logs as they change frequently
def get_container_logs(container_name: str, tail: int = 100) -> Optional[str]:
    """
    Gets the logs of a container with optimized caching and memory usage.

    Args:
        container_name: Name of the container
        tail: Number of lines to display

    Returns:
        Optional[str]: Logs or None if the container was not found
    """
    # Get container object
    container = _get_container_object(container_name)
    if container is None:
        return None

    try:
        # Get logs with efficient encoding handling and streaming
        # Use timestamps=False to reduce data size
        logs = container.logs(tail=tail, timestamps=False, stream=False)
        
        # Efficient decoding with memory optimization
        if isinstance(logs, bytes):
            # Use a more efficient decoding approach
            return logs.decode("utf-8", errors="replace")
        return logs
    except DockerException as e:
        logging.error(f"Error retrieving container logs: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error retrieving container logs: {str(e)}")
        return None


def check_docker_compose_installed() -> bool:
    """
    Checks if Docker Compose is installed.

    Returns:
        bool: True if Docker Compose is installed, False otherwise
    """
    # Use command_utils.check_command_exists instead of subprocess.run
    return check_command_exists("docker-compose")


# Initialisierungsprüfungen
if not check_docker_available():
    logging.warn(
        "Docker is not available. Some functions will not work."
    )

if not check_docker_compose_installed():
    logging.warn(
        "Docker Compose is not installed. Some functions will not work."
    )

logging.debug("Docker module initialized")
