"""
Common implementation of the Module API.

This module provides a common implementation of the Module API
that can be reused by different modules.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from llm_stack.core import config, docker, error, logging, system, validation


def get_module_api_help(module_name: str, module_api_version: str) -> str:
    """
    Returns the help text for the Module API.

    Args:
        module_name: Name of the module
        module_api_version: Version of the Module API

    Returns:
        str: Help text for the Module API
    """
    return f"""
Module API for {module_name} (v{module_api_version})

This API provides a standardized interface for interacting with the {module_name} module.

Available functions:

module_start()
  Starts the module services.
  
  Parameters:
    None
    
  Raises:
    ModuleAlreadyRunningError - If the module is already running
    ModuleStartError - If there was an error starting the module

module_stop()
  Stops the module services.
  
  Parameters:
    None
    
  Raises:
    ModuleAlreadyStoppedError - If the module is already stopped
    ModuleStopError - If there was an error stopping the module

module_restart()
  Restarts the module services.
  
  Parameters:
    None
    
  Raises:
    ModuleError - If there was an error restarting the module

module_status()
  Gets the current status of the module.
  
  Parameters:
    None
    
  Returns:
    Status code (0-5)
    0 - Unknown
    1 - Stopped
    2 - Starting
    3 - Running
    4 - Stopping
    5 - Error

module_get_status_text()
  Gets the current status of the module as text.
  
  Parameters:
    None
    
  Returns:
    Status text (string)
    
  Raises:
    ModuleError - If the status code is invalid

module_get_config()
  Gets the current configuration of the module.
  
  Parameters:
    config_key - Configuration key (optional)
    
  Returns:
    Configuration value(s)
    
  Raises:
    FileNotFoundError - If the configuration file does not exist
    ConfigError - If there was an error reading the configuration

module_set_config()
  Sets a configuration value for the module.
  
  Parameters:
    config_key - Configuration key
    config_value - Configuration value
    
  Raises:
    InvalidArgumentError - If the configuration key is empty
    FileNotFoundError - If the configuration file does not exist
    ConfigUpdateError - If there was an error updating the configuration

module_get_logs()
  Gets the logs for the module services.
  
  Parameters:
    service_name - Service name (optional)
    lines - Number of lines (optional, default: 100)
    
  Returns:
    Log output
    
  Raises:
    ModuleError - If there was an error retrieving the logs

module_get_health()
  Gets the health status of the module services.
  
  Parameters:
    service_name - Service name (optional)
    
  Returns:
    Health status (JSON)
    
  Raises:
    ModuleError - If there was an error retrieving the health status

module_get_version()
  Gets the version of the module.
  
  Parameters:
    None
    
  Returns:
    Module version (string)
    
  Raises:
    ModuleError - If there was an error retrieving the module version

module_get_api_version()
  Gets the version of the module API.
  
  Parameters:
    None
    
  Returns:
    API version (string)
    
  Raises:
    InvalidArgumentError - If the module API version is empty or invalid
"""

def module_start(
    module_name: str, module_status_func: Callable[[], int], module_status_running: int
) -> None:
    """
    Starts the module services.

    Args:
        module_name: Name of the module
        module_status_func: Function to retrieve the module status
        module_status_running: Status code for "Running"

    Raises:
        ModuleAlreadyRunningError: If the module is already running
        ModuleStartError: If there was an error starting the module
    """
    logging.info(f"Starting {module_name} module...")

    # Check if the module is already running
    if module_status_func() == module_status_running:
        logging.warn(f"{module_name} module is already running.")
        raise error.ModuleAlreadyRunningError(module_name)

    # Determine module directory
    module_dir = os.path.join("modules", module_name)

    # Start module services with Docker Compose
    compose_file = os.path.join(module_dir, "docker-compose.yml")
    try:
        result = docker.compose_up(
            f"{config.CORE_PROJECT}-{module_name}", f"-f {compose_file}", ""
        )

        if result != 0:
            raise error.ModuleStartError(module_name, f"Docker compose returned error code {result}")
            
        logging.success(f"{module_name} module successfully started.")
    except Exception as e:
        error_msg = f"Error starting the {module_name} module: {str(e)}"
        logging.error(error_msg)
        raise error.ModuleStartError(module_name, str(e)) from e
    return error.ERR_SUCCESS


def module_stop(
    module_name: str, module_status_func: Callable[[], int], module_status_stopped: int
) -> None:
    """
    Stops the module services.

    Args:
        module_name: Name of the module
        module_status_func: Function to retrieve the module status
        module_status_stopped: Status code for "Stopped"

    Raises:
        ModuleAlreadyStoppedError: If the module is already stopped
        ModuleStopError: If there was an error stopping the module
    """
    logging.info(f"Stopping {module_name} module...")

    # Check if the module is already stopped
    if module_status_func() == module_status_stopped:
        logging.warn(f"{module_name} module is already stopped.")
        raise error.ModuleAlreadyStoppedError(module_name)

    # Determine module directory
    module_dir = os.path.join("modules", module_name)

    # Stop module services with Docker Compose
    compose_file = os.path.join(module_dir, "docker-compose.yml")
    try:
        result = docker.compose_down(
            f"{config.CORE_PROJECT}-{module_name}", f"-f {compose_file}", ""
        )

        if result != 0:
            raise error.ModuleStopError(module_name, f"Docker compose returned error code {result}")
            
        logging.success(f"{module_name} module successfully stopped.")
    except Exception as e:
        error_msg = f"Error stopping the {module_name} module: {str(e)}"
        logging.error(error_msg)
        raise error.ModuleStopError(module_name, str(e)) from e


def module_restart(
    module_name: str,
    module_stop_func: Callable[[], None],
    module_start_func: Callable[[], None],
) -> None:
    """
    Restarts the module services.

    Args:
        module_name: Name of the module
        module_stop_func: Function to stop the module
        module_start_func: Function to start the module

    Raises:
        ModuleError: If there was an error restarting the module
    """
    logging.info(f"Restarting {module_name} module...")

    try:
        # Stop module
        try:
            module_stop_func()
        except error.ModuleAlreadyStoppedError:
            # If the module is already stopped, that's fine for a restart
            logging.info(f"{module_name} module was already stopped.")
        except Exception as e:
            error_msg = f"Error stopping the {module_name} module during restart: {str(e)}"
            logging.error(error_msg)
            raise error.ModuleError(error_msg) from e

        # Start module
        try:
            module_start_func()
        except Exception as e:
            error_msg = f"Error starting the {module_name} module during restart: {str(e)}"
            logging.error(error_msg)
            raise error.ModuleError(error_msg) from e

        logging.success(f"{module_name} module successfully restarted.")
    except Exception as e:
        if not isinstance(e, error.LLMStackError):
            error_msg = f"Unexpected error restarting the {module_name} module: {str(e)}"
            logging.error(error_msg)
            raise error.ModuleError(error_msg) from e
        raise


def module_status(
    module_name: str,
    module_status_unknown: int,
    module_status_stopped: int,
    module_status_error: int,
    module_status_running: int,
) -> int:
    """
    Determines the current status of the module.

    Args:
        module_name: Name of the module
        module_status_unknown: Status code for "Unknown"
        module_status_stopped: Status code for "Stopped"
        module_status_error: Status code for "Error"
        module_status_running: Status code for "Running"

    Returns:
        int: Status code
    """
    # Check if Docker is running
    if not docker.is_docker_running():
        logging.warn(f"Docker is not running, module {module_name} status is unknown")
        return module_status_unknown

    # Determine module directory
    module_dir = os.path.join("modules", module_name)
    compose_file = os.path.join(module_dir, "docker-compose.yml")

    # Determine the number of running containers for this module
    try:
        # Get all services
        services_cmd = f"docker-compose -f {compose_file} ps --services"
        services_result = subprocess.run(
            services_cmd, shell=True, capture_output=True, text=True
        )
        if services_result.returncode != 0:
            error_msg = f"Error getting services for module {module_name}: {services_result.stderr}"
            logging.error(error_msg)
            return module_status_unknown
            
        all_services = services_result.stdout.strip().split("\n")
        total_containers = len([s for s in all_services if s])

        # Get running services
        running_cmd = (
            f"docker-compose -f {compose_file} ps --services --filter status=running"
        )
        running_result = subprocess.run(
            running_cmd, shell=True, capture_output=True, text=True
        )
        if running_result.returncode != 0:
            error_msg = f"Error getting running services for module {module_name}: {running_result.stderr}"
            logging.error(error_msg)
            return module_status_unknown
            
        running_services = running_result.stdout.strip().split("\n")
        running_containers = len([s for s in running_services if s])

        # Determine status based on container count
        if total_containers == 0:
            logging.debug(f"No containers found for module {module_name}")
            return module_status_unknown
        elif running_containers == 0:
            logging.debug(f"No running containers for module {module_name}")
            return module_status_stopped
        elif running_containers < total_containers:
            # Some containers are running, but not all
            logging.warn(f"Only {running_containers}/{total_containers} containers running for module {module_name}")
            return module_status_error
        else:
            # All containers are running
            logging.debug(f"All containers ({total_containers}) running for module {module_name}")
            return module_status_running
    except Exception as e:
        error_msg = f"Error determining module status for {module_name}: {str(e)}"
        logging.error(error_msg)
        # Log the full exception in debug mode
        if logging.get_log_level() == logging.LogLevel.DEBUG:
            import traceback
            logging.debug(f"Stack trace: {traceback.format_exc()}")
        return module_status_unknown


def module_get_status_text(
    module_status_func: Callable[[], int], module_status_text: Dict[int, str]
) -> str:
    """
    Returns the current status of the module as text.

    Args:
        module_status_func: Function to retrieve the module status
        module_status_text: Mapping of status codes to status texts

    Returns:
        str: Status text

    Raises:
        ModuleError: If the status code is invalid
    """
    status = module_status_func()
    status_text = module_status_text.get(status)
    if status_text is None:
        error_msg = f"Invalid module status code: {status}"
        logging.error(error_msg)
        raise error.ModuleError(error_msg)
    return status_text


def module_get_config(
    module_name: str, config_key: Optional[str] = None
) -> Union[str, List[str]]:
    """
    Returns the current configuration of the module.

    Args:
        module_name: Name of the module
        config_key: Configuration key (optional)

    Returns:
        Union[str, List[str]]: Configuration value(s)

    Raises:
        FileNotFoundError: If the configuration file does not exist
        ConfigError: If there was an error reading the configuration
    """
    config_file = os.path.join(config.CONFIG_DIR, module_name, "env.conf")

    # Check if the configuration file exists
    if not os.path.isfile(config_file):
        error_msg = f"Configuration file not found: {config_file}"
        logging.error(error_msg)
        raise error.FileNotFoundError(error_msg)

    try:
        # If a specific key is requested, return its value
        if config_key:
            with open(config_file) as f:
                for line in f:
                    if line.startswith(f"{config_key}="):
                        return line.split("=", 1)[1].strip()
            # If the key is not found, raise an exception
            error_msg = f"Configuration key not found: {config_key}"
            logging.error(error_msg)
            raise error.ConfigError(error_msg)
        else:
            # Otherwise return all configuration values
            with open(config_file) as f:
                config_values = [
                    line.strip()
                    for line in f
                    if "=" in line and not line.startswith("#")
                ]
                if not config_values:
                    logging.warn(f"No configuration values found in {config_file}")
                return config_values
    except error.LLMStackError:
        # Re-raise LLMStackError exceptions
        raise
    except Exception as e:
        error_msg = f"Error reading configuration file: {str(e)}"
        logging.error(error_msg)
        raise error.ConfigError(error_msg) from e


def module_set_config(module_name: str, config_key: str, config_value: str) -> None:
    """
    Sets a configuration value for the module.

    Args:
        module_name: Name of the module
        config_key: Configuration key
        config_value: Configuration value

    Raises:
        InvalidArgumentError: If the configuration key is empty
        FileNotFoundError: If the configuration file does not exist
        ConfigUpdateError: If there was an error updating the configuration
    """
    config_file = os.path.join(config.CONFIG_DIR, module_name, "env.conf")

    # Validate input
    if not config_key:
        error_msg = "Configuration key is required."
        logging.error(error_msg)
        raise error.InvalidArgumentError(error_msg)

    # Check if the configuration file exists
    if not os.path.isfile(config_file):
        error_msg = f"Configuration file not found: {config_file}"
        logging.error(error_msg)
        raise error.FileNotFoundError(error_msg)

    try:
        # Read current configuration
        with open(config_file) as f:
            lines = f.readlines()

        # Check if the key exists in the configuration file
        key_exists = False
        for i, line in enumerate(lines):
            if line.startswith(f"{config_key}="):
                # Update existing key
                lines[i] = f"{config_key}={config_value}\n"
                key_exists = True
                break

        # If the key doesn't exist, add it
        if not key_exists:
            lines.append(f"{config_key}={config_value}\n")

        # Write configuration file
        with open(config_file, "w") as f:
            f.writelines(lines)

        logging.info(f"Configuration updated: {config_key}={config_value}")
    except Exception as e:
        error_msg = f"Error updating configuration file: {str(e)}"
        logging.error(error_msg)
        raise error.ConfigUpdateError(config_key, config_value, str(e)) from e


def module_get_logs(
    module_name: str, service_name: Optional[str] = None, lines: int = 100
) -> str:
    """
    Returns the logs for the module services.

    Args:
        module_name: Name of the module
        service_name: Service name (optional)
        lines: Number of lines (optional, default: 100)

    Returns:
        str: Log output

    Raises:
        ModuleError: If there was an error retrieving the logs
    """
    # Determine module directory
    module_dir = os.path.join("modules", module_name)
    compose_file = os.path.join(module_dir, "docker-compose.yml")

    try:
        # Create command to retrieve logs
        if service_name:
            # Get logs for a specific service
            cmd = f"docker-compose -f {compose_file} logs --tail={lines} {service_name}"
        else:
            # Get logs for all services
            cmd = f"docker-compose -f {compose_file} logs --tail={lines}"

        # Execute command
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        return result.stdout
    except Exception as e:
        error_msg = f"Error retrieving logs for module {module_name}: {str(e)}"
        logging.error(error_msg)
        raise error.ModuleError(error_msg) from e


def module_get_health(
    module_name: str,
    module_get_status_text_func: Callable[[], str],
    service_name: Optional[str] = None,
) -> str:
    """
    Returns the health status of the module services.

    Args:
        module_name: Name of the module
        module_get_status_text_func: Function to retrieve the module status as text
        service_name: Service name (optional)

    Returns:
        str: Health status (JSON)

    Raises:
        ModuleError: If there was an error retrieving the health status
    """
    # Determine module directory
    module_dir = os.path.join("modules", module_name)
    compose_file = os.path.join(module_dir, "docker-compose.yml")

    try:
        # Get list of services
        services = []
        if service_name:
            services = [service_name]
        else:
            cmd = f"docker-compose -f {compose_file} ps --services"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            services = [s for s in result.stdout.strip().split("\n") if s]

        # Check health status for each service
        health_data = {
            "module": module_name,
            "status": module_get_status_text_func(),
            "services": [],
        }

        for service in services:
            # Get container ID
            cmd = f"docker-compose -f {compose_file} ps -q {service}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            container_id = result.stdout.strip()

            # If no container exists, skip
            if not container_id:
                continue

            # Get health status
            cmd = f"docker inspect --format='{{{{if .State.Health}}}}{{{{.State.Health.Status}}}}{{{{else}}}}{{{{.State.Status}}}}{{{{end}}}}' {container_id}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            health = result.stdout.strip()

            # Add service health
            health_data["services"].append(
                {"name": service, "health": health, "container_id": container_id}
            )

        return json.dumps(health_data, indent=2)
    except Exception as e:
        error_msg = f"Error retrieving health status for module {module_name}: {str(e)}"
        logging.error(error_msg)
        raise error.ModuleError(error_msg) from e


def module_get_version(module_name: str) -> str:
    """
    Returns the version of the module.

    Args:
        module_name: Name of the module

    Returns:
        str: Module version

    Raises:
        ModuleError: If there was an error retrieving the module version
    """
    # Determine module directory
    module_dir = os.path.join("modules", module_name)

    try:
        # Try to read version from a version file
        version_file = os.path.join(module_dir, "VERSION")
        if os.path.isfile(version_file):
            with open(version_file) as f:
                return f.read().strip()

        # If no version file exists, try to read from docker-compose.yml
        compose_file = os.path.join(module_dir, "docker-compose.yml")
        if os.path.isfile(compose_file):
            try:
                with open(compose_file) as f:
                    for line in f:
                        if "version:" in line:
                            version = line.split(":", 1)[1].strip().strip("\"'")
                            if version:
                                return version
            except Exception as e:
                logging.warn(f"Error parsing docker-compose.yml for version: {str(e)}")

        # Default version if not found
        logging.warn(f"No version information found for module {module_name}, using default")
        return "1.0.0"
    except Exception as e:
        error_msg = f"Error retrieving version for module {module_name}: {str(e)}"
        logging.error(error_msg)
        raise error.ModuleError(error_msg) from e


def module_get_api_version(module_api_version: str) -> str:
    """
    Returns the version of the Module API.

    Args:
        module_api_version: Version of the Module API

    Returns:
        str: API version

    Raises:
        InvalidArgumentError: If the module API version is empty or invalid
    """
    if not module_api_version:
        error_msg = "Module API version cannot be empty"
        logging.error(error_msg)
        raise error.InvalidArgumentError(error_msg)
        
    # Optional: Add version format validation if needed
    # if not re.match(r'^\d+\.\d+\.\d+$', module_api_version):
    #     error_msg = f"Invalid module API version format: {module_api_version}"
    #     logging.error(error_msg)
    #     raise error.InvalidArgumentError(error_msg)
        
    return module_api_version
