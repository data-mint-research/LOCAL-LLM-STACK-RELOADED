"""
Module Integration for the LLM Stack.

This module provides functions for the integration and management of modules.
It enables listing, checking, starting, stopping, and managing modules.
"""

import json
import os
import shutil
import subprocess
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from llm_stack.core import config, docker, error, interfaces, logging, system, validation
from llm_stack.knowledge_graph.client import get_client
from llm_stack.knowledge_graph.migration import (
    record_bash_file,
    record_code_transformation,
    record_migration_decision,
    record_python_file,
)

# Constants
MODULES_DIR = os.path.join(system.get_project_root(), "modules")
CONFIG_DIR = os.path.join(system.get_project_root(), "config")
DATA_DIR = os.path.join(system.get_project_root(), "data")


class ModuleStatus(Enum):
    """Status of a module."""

    UNKNOWN = 0
    STOPPED = 1
    STARTING = 2
    RUNNING = 3
    STOPPING = 4
    ERROR = 5


class ModuleError(error.LLMStackError):
    """Exception for module errors."""

    def __init__(self, message: str):
        """
        Initializes a new module error exception.

        Args:
            message: Error message
        """
        super().__init__(message, error.ErrorCode.MODULE_ERROR)


class ModuleManager:
    """Manager for the integration and management of modules."""

    def __init__(
        self,
        modules_dir: str = MODULES_DIR,
        config_dir: str = CONFIG_DIR,
        data_dir: str = DATA_DIR,
    ):
        """
        Initializes a new ModuleManager.

        Args:
            modules_dir: Directory where modules are stored
            config_dir: Directory where configurations are stored
            data_dir: Directory where data is stored
        """
        self.modules_dir = modules_dir
        self.config_dir = config_dir
        self.data_dir = data_dir
        self._module_instances = {}  # Cache for module instances
        logging.debug(
            f"ModuleManager initialized with modules_dir={modules_dir}, config_dir={config_dir}, data_dir={data_dir}"
        )

    def get_available_modules(self) -> List[str]:
        """
        Returns a list of all available modules.

        Returns:
            List[str]: List of module names
        """
        logging.debug("Retrieving available modules")

        try:
            # Find all directories in the modules directory that are not hidden directories
            # and not the template directory
            modules = []
            if os.path.isdir(self.modules_dir):
                for item in os.listdir(self.modules_dir):
                    item_path = os.path.join(self.modules_dir, item)
                    if (
                        os.path.isdir(item_path)
                        and not item.startswith(".")
                        and item != "template"
                    ):
                        modules.append(item)

            # Sort the modules
            modules.sort()

            logging.debug(f"Available modules: {', '.join(modules)}")
            return modules
        except Exception as e:
            logging.error(f"Error retrieving available modules: {str(e)}")
            return []

    def module_exists(self, module_name: str) -> bool:
        """
        Checks if a module exists.

        Args:
            module_name: Name of the module

        Returns:
            bool: True if the module exists, False otherwise
        """
        module_dir = os.path.join(self.modules_dir, module_name)
        exists = os.path.isdir(module_dir)

        if exists:
            logging.debug(f"Module exists: {module_name}")
        else:
            logging.debug(f"Module does not exist: {module_name}")

        return exists
        
    def implements_interface(self, module_name: str) -> bool:
        """
        Checks if a module implements the ModuleInterface.
        
        Args:
            module_name: Name of the module
            
        Returns:
            bool: True if the module implements the ModuleInterface, False otherwise
        """
        if not self.module_exists(module_name):
            logging.debug(f"Module does not exist: {module_name}")
            return False
            
        try:
            # Try to import the module
            module_path = f"llm_stack.modules.{module_name}"
            try:
                module = __import__(module_path, fromlist=["module"])
                
                # Check if the module has a class that implements ModuleInterface
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, interfaces.ModuleInterface) and attr != interfaces.ModuleInterface:
                        logging.debug(f"Module {module_name} implements ModuleInterface with class {attr_name}")
                        return True
                
                logging.debug(f"Module {module_name} does not implement ModuleInterface")
                return False
            except ImportError:
                logging.debug(f"Could not import module {module_path}")
                return False
        except Exception as e:
            logging.error(f"Error checking if module {module_name} implements ModuleInterface: {str(e)}")
            return False

    def get_module_status(self, module_name: str) -> ModuleStatus:
        """
        Returns the status of a module.

        Args:
            module_name: Name of the module

        Returns:
            ModuleStatus: Status of the module

        Raises:
            ModuleError: If the module does not exist
        """
        # Check if the module exists
        if not self.module_exists(module_name):
            error_msg = f"Module does not exist: {module_name}"
            logging.error(error_msg)
            return ModuleStatus.UNKNOWN

        # Check if Docker is running
        if not docker.is_docker_running():
            return ModuleStatus.UNKNOWN

        # Check if the module has a docker-compose.yml file
        docker_compose_file = os.path.join(
            self.modules_dir, module_name, "docker-compose.yml"
        )
        if not os.path.isfile(docker_compose_file):
            # If no docker-compose.yml, check if the module has a setup script
            setup_script = os.path.join(
                self.modules_dir, module_name, "scripts", "setup.sh"
            )
            if os.path.isfile(setup_script) and os.access(setup_script, os.X_OK):
                # Module has a setup script but no docker-compose.yml
                # Consider it running if setup was executed
                if os.path.isdir(os.path.join(self.data_dir, module_name)):
                    return ModuleStatus.RUNNING
                else:
                    return ModuleStatus.STOPPED
            else:
                # Module has neither docker-compose.yml nor setup script
                return ModuleStatus.UNKNOWN

        try:
            # Get the number of running containers for this module
            running_containers = docker.get_running_containers_count(
                docker_compose_file
            )
            total_containers = docker.get_total_containers_count(docker_compose_file)

            # Determine status based on container count
            if total_containers == 0:
                return ModuleStatus.UNKNOWN
            elif running_containers == 0:
                return ModuleStatus.STOPPED
            elif running_containers < total_containers:
                # Some containers are running, but not all
                return ModuleStatus.ERROR
            else:
                # All containers are running
                return ModuleStatus.RUNNING
        except Exception as e:
            logging.error(
                f"Error retrieving module status for {module_name}: {str(e)}"
            )
            return ModuleStatus.ERROR
            
    def get_module_instance(self, module_name: str) -> Optional[interfaces.ModuleInterface]:
        """
        Gets an instance of a module that implements the ModuleInterface.
        
        Args:
            module_name: Name of the module
            
        Returns:
            Optional[interfaces.ModuleInterface]: Instance of the module or None if the module does not implement the interface
            
        Raises:
            ModuleError: If the module does not exist
        """
        # Check if the module exists
        if not self.module_exists(module_name):
            error_msg = f"Module does not exist: {module_name}"
            logging.error(error_msg)
            raise ModuleError(error_msg)
            
        # Check if we already have an instance
        if module_name in self._module_instances:
            return self._module_instances[module_name]
            
        # Check if the module implements the interface
        if not self.implements_interface(module_name):
            logging.debug(f"Module {module_name} does not implement ModuleInterface")
            return None
            
        try:
            # Import the module
            module_path = f"llm_stack.modules.{module_name}"
            module = __import__(module_path, fromlist=["module"])
            
            # Find the class that implements ModuleInterface
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, interfaces.ModuleInterface) and attr != interfaces.ModuleInterface:
                    # Create an instance of the class
                    instance = attr()
                    self._module_instances[module_name] = instance
                    logging.debug(f"Created instance of {attr_name} for module {module_name}")
                    return instance
                    
            logging.debug(f"No class implementing ModuleInterface found in module {module_name}")
            return None
        except Exception as e:
            error_msg = f"Error creating instance of module {module_name}: {str(e)}"
            logging.error(error_msg)
            return None
            if not self.module_exists(module_name):
                error_msg = f"Module does not exist: {module_name}"
                logging.error(error_msg)
                raise ModuleError(error_msg)
                
            # Check if we already have an instance
            if module_name in self._module_instances:
                return self._module_instances[module_name]
                
            # Check if the module implements the interface
            if not self.implements_interface(module_name):
                logging.debug(f"Module {module_name} does not implement ModuleInterface")
                return None
                
            try:
                # Import the module
                module_path = f"llm_stack.modules.{module_name}"
                module = __import__(module_path, fromlist=["module"])
                
                # Find the class that implements ModuleInterface
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, interfaces.ModuleInterface) and attr != interfaces.ModuleInterface:
                        # Create an instance of the class
                        instance = attr()
                        self._module_instances[module_name] = instance
                        logging.debug(f"Created instance of {attr_name} for module {module_name}")
                        return instance
                        
                logging.debug(f"No class implementing ModuleInterface found in module {module_name}")
                return None
            except Exception as e:
                error_msg = f"Error creating instance of module {module_name}: {str(e)}"
                logging.error(error_msg)
                return None
            else:
                # All containers are running
                return ModuleStatus.RUNNING
        except Exception as e:
            logging.error(
                f"Error retrieving module status for {module_name}: {str(e)}"
            )
            return ModuleStatus.ERROR

    def get_module_status_text(self, module_name: str) -> str:
        """
        Returns the status of a module as text.

        Args:
            module_name: Name of the module

        Returns:
            str: Status of the module as text
        """
        status = self.get_module_status(module_name)

        status_texts = {
            ModuleStatus.UNKNOWN: "Unknown",
            ModuleStatus.STOPPED: "Stopped",
            ModuleStatus.STARTING: "Starting",
            ModuleStatus.RUNNING: "Running",
            ModuleStatus.STOPPING: "Stopping",
            ModuleStatus.ERROR: "Error",
        }

        return status_texts.get(status, "Invalid status")

    def start_module(self, module_name: str) -> bool:
        """
        Starts a module.

        Args:
            module_name: Name of the module

        Returns:
            bool: True if the module was successfully started, False otherwise

        Raises:
            ModuleError: If the module does not exist or cannot be started
        """
        # Check if the module exists
        if not self.module_exists(module_name):
            error_msg = f"Module does not exist: {module_name}"
            logging.error(error_msg)
            raise ModuleError(error_msg)

        logging.info(f"Starting module: {module_name}")

        # Check if the module is already running
        status = self.get_module_status(module_name)

        if status == ModuleStatus.RUNNING:
            logging.warning(f"Module is already running: {module_name}")
            return True

        # Check if the module has a docker-compose.yml file
        docker_compose_file = os.path.join(
            self.modules_dir, module_name, "docker-compose.yml"
        )
        if os.path.isfile(docker_compose_file):
            # Start module with Docker Compose
            logging.debug(f"Starting module with Docker Compose: {module_name}")
            try:
                docker.docker_compose_up(docker_compose_file, ["-d"])
            except Exception as e:
                error_msg = f"Error starting module {module_name}: {str(e)}"
                logging.error(error_msg)
                raise ModuleError(error_msg)
        else:
            # Check if the module has a setup script
            setup_script = os.path.join(
                self.modules_dir, module_name, "scripts", "setup.sh"
            )
            if os.path.isfile(setup_script) and os.access(setup_script, os.X_OK):
                # Execute setup script
                logging.debug(f"Executing module setup script: {module_name}")
                try:
                    result = subprocess.run([setup_script], check=True)
                    if result.returncode != 0:
                        error_msg = f"Error executing setup script for module {module_name}"
                        logging.error(error_msg)
                        raise ModuleError(error_msg)
                except subprocess.CalledProcessError as e:
                    error_msg = f"Error executing setup script for module {module_name}: {str(e)}"
                    logging.error(error_msg)
                    raise ModuleError(error_msg)
            else:
                error_msg = f"Module has no docker-compose.yml or setup script: {module_name}"
                logging.error(error_msg)
                raise ModuleError(error_msg)

        logging.success(f"Module successfully started: {module_name}")
        return True

    def stop_module(self, module_name: str) -> bool:
        """
        Stops a module.

        Args:
            module_name: Name of the module

        Returns:
            bool: True if the module was successfully stopped, False otherwise

        Raises:
            ModuleError: If the module does not exist or cannot be stopped
        """
        # Check if the module exists
        if not self.module_exists(module_name):
            error_msg = f"Module does not exist: {module_name}"
            logging.error(error_msg)
            raise ModuleError(error_msg)

        logging.info(f"Stopping module: {module_name}")

        # Check if the module is already stopped
        status = self.get_module_status(module_name)

        if status == ModuleStatus.STOPPED:
            logging.warning(f"Module is already stopped: {module_name}")
            return True

        # Check if the module has a docker-compose.yml file
        docker_compose_file = os.path.join(
            self.modules_dir, module_name, "docker-compose.yml"
        )
        if os.path.isfile(docker_compose_file):
            # Stop module with Docker Compose
            logging.debug(f"Stopping module with Docker Compose: {module_name}")
            try:
                docker.docker_compose_down(docker_compose_file)
            except Exception as e:
                error_msg = f"Error stopping module {module_name}: {str(e)}"
                logging.error(error_msg)
                raise ModuleError(error_msg)
        else:
            # Check if the module has a teardown script
            teardown_script = os.path.join(
                self.modules_dir, module_name, "scripts", "teardown.sh"
            )
            if os.path.isfile(teardown_script) and os.access(teardown_script, os.X_OK):
                # Execute teardown script
                logging.debug(f"Executing module teardown script: {module_name}")
                try:
                    result = subprocess.run([teardown_script], check=True)
                    if result.returncode != 0:
                        error_msg = f"Error executing teardown script for module {module_name}"
                        logging.error(error_msg)
                        raise ModuleError(error_msg)
                except subprocess.CalledProcessError as e:
                    error_msg = f"Error executing teardown script for module {module_name}: {str(e)}"
                    logging.error(error_msg)
                    raise ModuleError(error_msg)
            else:
                logging.warning(
                    f"Module has no docker-compose.yml or teardown script: {module_name}"
                )
                return True

        logging.success(f"Module successfully stopped: {module_name}")
        return True

    def restart_module(self, module_name: str) -> bool:
        """
        Restarts a module.

        Args:
            module_name: Name of the module

        Returns:
            bool: True if the module was successfully restarted, False otherwise

        Raises:
            ModuleError: If the module does not exist or cannot be restarted
        """
        # Check if the module exists
        if not self.module_exists(module_name):
            error_msg = f"Module does not exist: {module_name}"
            logging.error(error_msg)
            raise ModuleError(error_msg)

        logging.info(f"Restarting module: {module_name}")
        
        # First try to use the ModuleInterface if implemented
        module_instance = self.get_module_instance(module_name)
        if module_instance:
            try:
                logging.debug(f"Restarting module {module_name} using ModuleInterface")
                # Stop and then start using the interface
                if module_instance.stop() and module_instance.start():
                    logging.success(f"Module successfully restarted: {module_name}")
                    return True
                else:
                    logging.error(f"Failed to restart module {module_name} using ModuleInterface")
                    # Fall back to file-based approach
            except Exception as e:
                logging.error(f"Error restarting module {module_name} using ModuleInterface: {str(e)}")
                # Fall back to file-based approach

        # Fall back to file-based approach
        # Stop module
        try:
            self.stop_module(module_name)
        except ModuleError as e:
            error_msg = f"Error stopping module during restart: {module_name}: {str(e)}"
            logging.error(error_msg)
            raise ModuleError(error_msg)

        # Start module
        try:
            self.start_module(module_name)
        except ModuleError as e:
            error_msg = f"Error starting module during restart: {module_name}: {str(e)}"
            logging.error(error_msg)
            raise ModuleError(error_msg)

        logging.success(f"Module successfully restarted: {module_name}")
        return True

    def get_module_logs(
        self, module_name: str, service_name: Optional[str] = None, lines: int = 100
    ) -> str:
        """
        Returns the logs of a module.

        Args:
            module_name: Name of the module
            service_name: Name of the service (optional)
            lines: Number of lines (optional, default: 100)

        Returns:
            str: Logs of the module

        Raises:
            ModuleError: If the module does not exist or no logs are available
        """
        # Check if the module exists
        if not self.module_exists(module_name):
            error_msg = f"Module does not exist: {module_name}"
            logging.error(error_msg)
            raise ModuleError(error_msg)
            
        # First try to use the ModuleInterface if implemented
        # Note: The ModuleInterface doesn't have a direct method for logs,
        # but we could potentially add this to the get_status() method in the future
        module_instance = self.get_module_instance(module_name)
        if module_instance:
            logging.debug(f"ModuleInterface doesn't support getting logs directly yet")

        # Check if the module has a docker-compose.yml file
        docker_compose_file = os.path.join(
            self.modules_dir, module_name, "docker-compose.yml"
        )
        if not os.path.isfile(docker_compose_file):
            error_msg = f"Module has no docker-compose.yml file: {module_name}"
            logging.error(error_msg)
            raise ModuleError(error_msg)

        # Retrieve logs
        try:
            if service_name:
                return docker.docker_compose_logs(
                    docker_compose_file, service_name, lines
                )
            else:
                return docker.docker_compose_logs(docker_compose_file, None, lines)
        except Exception as e:
            error_msg = (
                f"Error retrieving logs for module {module_name}: {str(e)}"
            )
            logging.error(error_msg)
            raise ModuleError(error_msg)

    def get_module_health(
        self, module_name: str, service_name: Optional[str] = None
    ) -> Dict:
        """
        Returns the health status of a module.

        Args:
            module_name: Name of the module
            service_name: Name of the service (optional)

        Returns:
            Dict: Health status of the module as a dictionary

        Raises:
            ModuleError: If the module does not exist or no health status is available
        """
        # Check if the module exists
        if not self.module_exists(module_name):
            error_msg = f"Module does not exist: {module_name}"
            logging.error(error_msg)
            raise ModuleError(error_msg)
            
        # First try to use the ModuleInterface if implemented
        module_instance = self.get_module_instance(module_name)
        if module_instance:
            try:
                logging.debug(f"Getting health status for module {module_name} using ModuleInterface")
                status = module_instance.get_status()
                if status:
                    # Convert the status to the expected format
                    health_data = {
                        "module": module_name,
                        "status": self.get_module_status_text(module_name),
                        "services": [],
                        "interface_status": status
                    }
                    return health_data
            except Exception as e:
                logging.error(f"Error getting health status for module {module_name} using ModuleInterface: {str(e)}")
                # Fall back to file-based approach

        # Fall back to file-based approach
        # Check if the module has a docker-compose.yml file
        docker_compose_file = os.path.join(
            self.modules_dir, module_name, "docker-compose.yml"
        )
        if not os.path.isfile(docker_compose_file):
            error_msg = f"Module has no docker-compose.yml file: {module_name}"
            logging.error(error_msg)
            raise ModuleError(error_msg)

        # Get list of services
        services = []
        try:
            if service_name:
                services = [service_name]
            else:
                services = docker.get_docker_compose_services(docker_compose_file)
        except Exception as e:
            error_msg = (
                f"Error retrieving services for module {module_name}: {str(e)}"
            )
            logging.error(error_msg)
            raise ModuleError(error_msg)

        # Check health status for each service
        health_data = {
            "module": module_name,
            "status": self.get_module_status_text(module_name),
            "services": [],
        }

        for service in services:
            # Get container ID
            try:
                container_id = docker.get_container_id(docker_compose_file, service)
                if not container_id:
                    continue

                # Get health status
                health = docker.get_container_health(container_id)

                # Add service health status
                health_data["services"].append(
                    {"name": service, "health": health, "container_id": container_id}
                )
            except Exception as e:
                logging.warning(
                    f"Error retrieving health status for service {service} in module {module_name}: {str(e)}"
                )
                continue

        return health_data

    def get_module_config(
        self, module_name: str, config_key: Optional[str] = None
    ) -> Optional[Union[str, Dict[str, str]]]:
        """
        Returns the configuration of a module.

        Args:
            module_name: Name of the module
            config_key: Configuration key (optional)

        Returns:
            Optional[Union[str, Dict[str, str]]]: Configuration value or dictionary with all configuration values

        Raises:
            ModuleError: If the module does not exist or no configuration is available
        """
        # Check if the module exists
        if not self.module_exists(module_name):
            error_msg = f"Module does not exist: {module_name}"
            logging.error(error_msg)
            raise ModuleError(error_msg)
            
        # First try to use the ModuleInterface if implemented
        module_instance = self.get_module_instance(module_name)
        if module_instance:
            try:
                logging.debug(f"Getting configuration for module {module_name} using ModuleInterface")
                info = module_instance.get_info()
                if info and 'config' in info:
                    if config_key:
                        # Try to get the specific config key
                        if config_key in info['config']:
                            return info['config'][config_key]
                        else:
                            logging.debug(f"Configuration key {config_key} not found in module info")
                    else:
                        # Return all config
                        return info['config']
            except Exception as e:
                logging.error(f"Error getting configuration for module {module_name} using ModuleInterface: {str(e)}")
                # Fall back to file-based approach

        # Check if the module has a configuration file
        config_file = os.path.join(self.config_dir, module_name, "env.conf")
        if not os.path.isfile(config_file):
            error_msg = f"Module has no configuration file: {module_name}"
            logging.error(error_msg)
            raise ModuleError(error_msg)

        try:
            # Read configuration
            config_data = {}
            with open(config_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        config_data[key] = value

            # If a configuration key is specified, return only this value
            if config_key:
                if config_key in config_data:
                    return config_data[config_key]
                else:
                    error_msg = f"Configuration key not found: {config_key}"
                    logging.error(error_msg)
                    return None
            else:
                # Return complete configuration
                return config_data
        except Exception as e:
            error_msg = f"Error retrieving configuration for module {module_name}: {str(e)}"
            logging.error(error_msg)
            raise ModuleError(error_msg)

    def set_module_config(
        self, module_name: str, config_key: str, config_value: str
    ) -> bool:
        """
        Sets a configuration value for a module.

        Args:
            module_name: Name of the module
            config_key: Configuration key
            config_value: Configuration value

        Returns:
            bool: True if the value was successfully set, False otherwise

        Raises:
            ModuleError: If the module does not exist or the configuration cannot be set
        """
        # Check if the module exists
        if not self.module_exists(module_name):
            error_msg = f"Module does not exist: {module_name}"
            logging.error(error_msg)
            raise ModuleError(error_msg)

        # Check if a configuration key is specified
        if not config_key:
            error_msg = "Configuration key is required"
            logging.error(error_msg)
            raise ModuleError(error_msg)
            
        # First try to use the ModuleInterface if implemented
        # Note: The ModuleInterface doesn't have a direct method for setting config,
        # but we could potentially add this in the future
        module_instance = self.get_module_instance(module_name)
        if module_instance:
            logging.debug(f"ModuleInterface doesn't support setting config directly yet")

        # Ensure that the module configuration directory exists
        config_dir = os.path.join(self.config_dir, module_name)
        os.makedirs(config_dir, exist_ok=True)

        # Check if the module has a configuration file
        config_file = os.path.join(config_dir, "env.conf")
        if not os.path.isfile(config_file):
            # Create configuration file if it doesn't exist
            open(config_file, "a").close()

        try:
            # Read configuration
            config_data = {}
            with open(config_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        config_data[key] = value

            # Set configuration value
            config_data[config_key] = config_value

            # Write configuration
            with open(config_file, "w") as f:
                for key, value in config_data.items():
                    f.write(f"{key}={value}\n")

            logging.info(
                f"Module configuration updated: {module_name}.{config_key}={config_value}"
            )
            return True
        except Exception as e:
            error_msg = f"Error setting configuration for module {module_name}: {str(e)}"
            logging.error(error_msg)
            raise ModuleError(error_msg)

    def initialize_module(self, module_name: str) -> bool:
        """
        Initializes a new module.

        Args:
            module_name: Name of the module

        Returns:
            bool: True if the module was successfully initialized, False otherwise

        Raises:
            ModuleError: If the module already exists or cannot be initialized
        """
        # Check if a module name is specified
        if not module_name:
            error_msg = "Module name is required"
            logging.error(error_msg)
            raise ModuleError(error_msg)

        # Check if the module already exists
        if self.module_exists(module_name):
            error_msg = f"Module already exists: {module_name}"
            logging.error(error_msg)
            raise ModuleError(error_msg)

        logging.info(f"Initializing new module: {module_name}")

        try:
            # Create module directory
            module_dir = os.path.join(self.modules_dir, module_name)
            os.makedirs(module_dir, exist_ok=True)

            # Copy template files
            template_dir = os.path.join(self.modules_dir, "template")
            if not os.path.isdir(template_dir):
                error_msg = "Template directory not found"
                logging.error(error_msg)
                raise ModuleError(error_msg)

            # Copy all files and directories from the template directory
            for item in os.listdir(template_dir):
                source = os.path.join(template_dir, item)
                destination = os.path.join(module_dir, item)

                if os.path.isdir(source):
                    shutil.copytree(source, destination)
                else:
                    shutil.copy2(source, destination)

            # Update module name in files
            for root, _, files in os.walk(module_dir):
                for file in files:
                    file_path = os.path.join(root, file)

                    # Only edit text files
                    try:
                        with open(file_path) as f:
                            content = f.read()

                        # Replace "template" with the module name
                        content = content.replace("template", module_name)

                        with open(file_path, "w") as f:
                            f.write(content)
                    except UnicodeDecodeError:
                        # Skip binary files
                        pass

            # Create module data directory
            os.makedirs(os.path.join(self.data_dir, module_name), exist_ok=True)

            # Create module configuration directory
            os.makedirs(os.path.join(self.config_dir, module_name), exist_ok=True)

            # Copy default configuration
            config_source = os.path.join(module_dir, "config", "env.conf")
            config_dest = os.path.join(self.config_dir, module_name, "env.conf")
            if os.path.isfile(config_source):
                shutil.copy2(config_source, config_dest)

            # Make scripts executable
            scripts_dir = os.path.join(module_dir, "scripts")
            if os.path.isdir(scripts_dir):
                for script in Path(scripts_dir).glob("*.sh"):
                    os.chmod(script, 0o755)

            logging.success(f"Module successfully initialized: {module_name}")
            return True
        except Exception as e:
            error_msg = (
                f"Error initializing module {module_name}: {str(e)}"
            )
            logging.error(error_msg)

            # Clean up on error
            module_dir = os.path.join(self.modules_dir, module_name)
            if os.path.isdir(module_dir):
                shutil.rmtree(module_dir)

            data_dir = os.path.join(self.data_dir, module_name)
            if os.path.isdir(data_dir):
                shutil.rmtree(data_dir)

            config_dir = os.path.join(self.config_dir, module_name)
            if os.path.isdir(config_dir):
                shutil.rmtree(config_dir)

            raise ModuleError(error_msg)


# Global instance of ModuleManager
_module_manager = None


def get_module_manager() -> ModuleManager:
    """
    Returns an instance of the ModuleManager.

    Returns:
        ModuleManager: Instance of the ModuleManager
    """
    global _module_manager

    if _module_manager is None:
        _module_manager = ModuleManager()

    return _module_manager


# Helper functions for easy access to ModuleManager methods


def get_available_modules() -> List[str]:
    """
    Returns a list of all available modules.

    Returns:
        List[str]: List of module names
    """
    return get_module_manager().get_available_modules()


def module_exists(module_name: str) -> bool:
    """
    Checks if a module exists.

    Args:
        module_name: Name of the module

    Returns:
        bool: True if the module exists, False otherwise
    """
    return get_module_manager().module_exists(module_name)


def get_module_status(module_name: str) -> ModuleStatus:
    """
    Returns the status of a module.

    Args:
        module_name: Name of the module

    Returns:
        ModuleStatus: Status of the module

    Raises:
        ModuleError: If the module does not exist
    """
    return get_module_manager().get_module_status(module_name)


def get_module_status_text(module_name: str) -> str:
    """
    Returns the status of a module as text.

    Args:
        module_name: Name of the module

    Returns:
        str: Status of the module as text
    """
    return get_module_manager().get_module_status_text(module_name)


def start_module(module_name: str) -> bool:
    """
    Starts a module.

    Args:
        module_name: Name of the module

    Returns:
        bool: True if the module was successfully started, False otherwise

    Raises:
        ModuleError: If the module does not exist or cannot be started
    """
    return get_module_manager().start_module(module_name)


def stop_module(module_name: str) -> bool:
    """
    Stops a module.

    Args:
        module_name: Name of the module

    Returns:
        bool: True if the module was successfully stopped, False otherwise

    Raises:
        ModuleError: If the module does not exist or cannot be stopped
    """
    return get_module_manager().stop_module(module_name)


def restart_module(module_name: str) -> bool:
    """
    Restarts a module.

    Args:
        module_name: Name of the module

    Returns:
        bool: True if the module was successfully restarted, False otherwise

    Raises:
        ModuleError: If the module does not exist or cannot be restarted
    """
    return get_module_manager().restart_module(module_name)


def get_module_logs(
    module_name: str, service_name: Optional[str] = None, lines: int = 100
) -> str:
    """
    Returns the logs of a module.

    Args:
        module_name: Name of the module
        service_name: Name of the service (optional)
        lines: Number of lines (optional, default: 100)

    Returns:
        str: Logs of the module

    Raises:
        ModuleError: If the module does not exist or no logs are available
    """
    return get_module_manager().get_module_logs(module_name, service_name, lines)


def get_module_health(module_name: str, service_name: Optional[str] = None) -> Dict:
    """
    Returns the health status of a module.

    Args:
        module_name: Name of the module
        service_name: Name of the service (optional)

    Returns:
        Dict: Health status of the module as a dictionary

    Raises:
        ModuleError: If the module does not exist or no health status is available
    """
    return get_module_manager().get_module_health(module_name, service_name)


def get_module_config(
    module_name: str, config_key: Optional[str] = None
) -> Optional[Union[str, Dict[str, str]]]:
    """
    Returns the configuration of a module.

    Args:
        module_name: Name of the module
        config_key: Configuration key (optional)

    Returns:
        Optional[Union[str, Dict[str, str]]]: Configuration value or dictionary with all configuration values

    Raises:
        ModuleError: If the module does not exist or no configuration is available
    """
    return get_module_manager().get_module_config(module_name, config_key)


def set_module_config(module_name: str, config_key: str, config_value: str) -> bool:
    """
    Sets a configuration value for a module.

    Args:
        module_name: Name of the module
        config_key: Configuration key
        config_value: Configuration value

    Returns:
        bool: True if the value was successfully set, False otherwise

    Raises:
        ModuleError: If the module does not exist or the configuration cannot be set
    """
    return get_module_manager().set_module_config(module_name, config_key, config_value)


def initialize_module(module_name: str) -> bool:
    """
    Initializes a new module.

    Args:
        module_name: Name of the module

    Returns:
        bool: True if the module was successfully initialized, False otherwise

    Raises:
        ModuleError: If the module already exists or cannot be initialized
    """
    return get_module_manager().initialize_module(module_name)


# Migrationsentscheidungen im Knowledge Graph aufzeichnen
try:
    client = get_client()

    # Migrationsentscheidungen aufzeichnen
    record_migration_decision(
        decision="Object-oriented approach with ModuleManager class",
        rationale="Using a ModuleManager class enables better encapsulation of functionality and facilitates testing.",
        bash_file_path="lib/core/module_integration.sh",
        python_file_path="llm_stack/core/module_integration.py",
        alternatives=[
            "Functional approach as in the Bash file",
            "Singleton pattern without global functions",
        ],
        impact="Improved maintainability and testability, more consistent with other Python modules",
    )

    record_migration_decision(
        decision="Use of ModuleStatus enum for module status",
        rationale="An enum provides a type-safe way to represent the status of a module.",
        bash_file_path="lib/core/module_integration.sh",
        python_file_path="llm_stack/core/module_integration.py",
        alternatives=[
            "Use of integer constants as in the Bash version",
            "Use of string constants",
        ],
        impact="Improved type safety and code readability",
    )
    
    record_migration_decision(
        decision="Integration with ModuleInterface for module operations",
        rationale="Using the ModuleInterface provides a standardized way to interact with modules, reducing reliance on file structure and conventions.",
        bash_file_path="lib/core/module_integration.sh",
        python_file_path="llm_stack/core/module_integration.py",
        alternatives=[
            "Continue using only file-based approach",
            "Replace file-based approach entirely with interface-based approach",
        ],
        impact="Improved flexibility, maintainability, and adherence to the specification manifest while maintaining backward compatibility",
    )

    record_migration_decision(
        decision="Introduction of a specific ModuleError class",
        rationale="A specific error class enables better error handling and differentiation.",
        bash_file_path="lib/core/module_integration.sh",
        python_file_path="llm_stack/core/module_integration.py",
        alternatives=[
            "Use of general exceptions",
            "Return of error codes as in the Bash version",
        ],
        impact="Improved error handling and diagnosis",
    )

    # Record Bash file
    record_bash_file(
        "lib/core/module_integration.sh",
        open("local-llm-stack/lib/core/module_integration.sh").read(),
    )

    # Record Python file
    record_python_file(
        "llm_stack/core/module_integration.py",
        open(__file__).read(),
        "lib/core/module_integration.sh",
    )

    # Record code transformations
    record_code_transformation(
        transformation_type="function_to_class_method",
        before=r"""function get_available_modules() {
  find "$MODULES_DIR" -mindepth 1 -maxdepth 1 -type d -not -path "*/\.*" -not -path "*/template" | sort | xargs -n1 basename
}""",
        after="""def get_available_modules(self) -> List[str]:
        \"\"\"
        Returns a list of all available modules.
        
        Returns:
            List[str]: List of module names
        \"\"\"
        logging.debug("Retrieving available modules")
        
        try:
            # Find all directories in the modules directory that are not hidden directories
            # and not the template directory
            modules = []
            if os.path.isdir(self.modules_dir):
                for item in os.listdir(self.modules_dir):
                    item_path = os.path.join(self.modules_dir, item)
                    if (os.path.isdir(item_path) and
                        not item.startswith('.') and
                        item != 'template'):
                        modules.append(item)
            
            # Sort the modules
            modules.sort()
            
            logging.debug(f"Available modules: {', '.join(modules)}")
            return modules
        except Exception as e:
            logging.error(f"Error retrieving available modules: {str(e)}")
            return []""",
        bash_file_path="lib/core/module_integration.sh",
        python_file_path="llm_stack/core/module_integration.py",
    )

    record_code_transformation(
        transformation_type="constants_to_enum",
        before="""# Module status constants
readonly MODULE_STATUS_UNKNOWN=0
readonly MODULE_STATUS_STOPPED=1
readonly MODULE_STATUS_STARTING=2
readonly MODULE_STATUS_RUNNING=3
readonly MODULE_STATUS_STOPPING=4
readonly MODULE_STATUS_ERROR=5""",
        after="""class ModuleStatus(Enum):
    \"\"\"Status of a module.\"\"\"
    UNKNOWN = 0
    STOPPED = 1
    STARTING = 2
    RUNNING = 3
    STOPPING = 4
    ERROR = 5""",
        bash_file_path="lib/core/module_integration.sh",
        python_file_path="llm_stack/core/module_integration.py",
    )

    record_code_transformation(
        transformation_type="error_handling",
        before="""  # Check if module exists
  if ! module_exists "$module_name"; then
    log_error "Module does not exist: $module_name"
    return $ERR_NOT_FOUND
  fi""",
        after="""        # Prüfen, ob das Modul existiert
        if not self.module_exists(module_name):
            error_msg = f"Module does not exist: {module_name}"
            logging.error(error_msg)
            raise ModuleError(error_msg)""",
        bash_file_path="lib/core/module_integration.sh",
        python_file_path="llm_stack/core/module_integration.py",
    )

except Exception as e:
    logging.error(f"Error recording migration in Knowledge Graph: {str(e)}")


# Initialize module
logging.debug("Module Integration module initialized")
