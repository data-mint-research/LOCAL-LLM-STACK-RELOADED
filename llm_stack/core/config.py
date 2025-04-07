"""
Configuration management for the LLM Stack.

This module provides functions for loading, validating, and managing the configuration
for the LOCAL-LLM-STACK-RELOADED project. It includes functionality for:

1. Loading and saving configuration from .env files
2. Validating configuration values
3. Generating and managing secure secrets
4. Managing LibreChat secrets
5. Creating backups of configuration files

The module implements a singleton ConfigManager class to maintain configuration state
and provides module-level functions for backward compatibility.

Examples:
    Loading configuration:
    ```python
    from llm_stack.core import config
    
    # Load configuration from default .env file
    config.load_config()
    
    # Get a configuration value
    port = config.get_config("HOST_PORT_OLLAMA", "11434")
    ```
    
    Generating secrets:
    ```python
    from llm_stack.core import config
    
    # Generate secure secrets
    config.generate_secrets()
    
    # Update LibreChat secrets from main configuration
    config.update_librechat_secrets()
    ```
    
    Validating configuration:
    ```python
    from llm_stack.core import config
    
    # Validate configuration
    if config.validate_config():
        print("Configuration is valid")
    else:
        print("Configuration is invalid")
    ```
"""

import os
import shutil
import subprocess
import tempfile
import threading
import functools
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

import yaml
from pydantic import BaseModel, Field

from llm_stack.core import logging

# Configuration class to replace global variables
class ConfigManager:
    """
    Configuration manager for the LLM Stack.
    
    This class implements a singleton pattern to maintain configuration state
    across the application. It provides methods for loading, saving, validating,
    and managing configuration values, as well as generating and managing secure
    secrets.
    
    The ConfigManager maintains default values for configuration paths and project
    names, and provides methods to override these defaults.
    
    Attributes:
        DEFAULT_CONFIG_DIR (str): Default configuration directory
        DEFAULT_ENV_FILE (str): Default environment file path
        DEFAULT_CORE_PROJECT (str): Default core project name
        DEFAULT_DEBUG_PROJECT (str): Default debug project name
        DEFAULT_CORE_COMPOSE (str): Default core Docker Compose command
        DEFAULT_DEBUG_COMPOSE (str): Default debug Docker Compose command
    """
    
    # Default configuration values
    DEFAULT_CONFIG_DIR = "config"
    DEFAULT_ENV_FILE = f"{DEFAULT_CONFIG_DIR}/.env"
    DEFAULT_CORE_PROJECT = "local-llm-stack"
    DEFAULT_DEBUG_PROJECT = f"{DEFAULT_CORE_PROJECT}-debug"
    DEFAULT_CORE_COMPOSE = "-f docker/core/docker-compose.yml"
    DEFAULT_DEBUG_COMPOSE = (
        f"{DEFAULT_CORE_COMPOSE} -f docker/core/docker-compose.debug.yml"
    )
    
    # Singleton instance
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """
        Implement thread-safe singleton pattern.
        
        Returns:
            ConfigManager: The singleton instance of the ConfigManager
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """
        Initialize the configuration manager with default values.
        
        This method sets up the default configuration paths and values.
        It is only executed once due to the singleton pattern.
        """
        # Only initialize once
        if getattr(self, '_initialized', False):
            return
            
        self.config_dir = self.DEFAULT_CONFIG_DIR
        self.env_file = self.DEFAULT_ENV_FILE
        self.core_project = self.DEFAULT_CORE_PROJECT
        self.debug_project = self.DEFAULT_DEBUG_PROJECT
        self.core_compose = self.DEFAULT_CORE_COMPOSE
        self.debug_compose = self.DEFAULT_DEBUG_COMPOSE
        self.config_values = {}
        
        self._initialized = True
        logging.debug("Configuration manager initialized with default values")


# Configuration model
class LLMStackConfig(BaseModel):
    """
    Configuration model for the LLM Stack.
    
    This Pydantic model defines the configuration schema for the LLM Stack,
    including default values and descriptions for each configuration parameter.
    
    Attributes:
        HOST_PORT_LIBRECHAT (int): Port for LibreChat
        HOST_PORT_OLLAMA (int): Port for Ollama
        OLLAMA_CPU_LIMIT (float): CPU limit for Ollama
        OLLAMA_MEMORY_LIMIT (str): Memory limit for Ollama
        MONGODB_MEMORY_LIMIT (str): Memory limit for MongoDB
        MEILISEARCH_MEMORY_LIMIT (str): Memory limit for Meilisearch
        LIBRECHAT_CPU_LIMIT (float): CPU limit for LibreChat
        LIBRECHAT_MEMORY_LIMIT (str): Memory limit for LibreChat
        OLLAMA_VERSION (str): Ollama version
        MONGODB_VERSION (str): MongoDB version
        MEILISEARCH_VERSION (str): Meilisearch version
        LIBRECHAT_VERSION (str): LibreChat version
        JWT_SECRET (str): JWT secret for LibreChat
        JWT_REFRESH_SECRET (str): JWT refresh secret for LibreChat
        SESSION_SECRET (str): Session secret for LibreChat
        CRYPT_SECRET (str): Encryption secret for LibreChat
        CREDS_KEY (str): Credentials key for LibreChat
        CREDS_IV (str): Credentials IV for LibreChat
        ADMIN_EMAIL (str): Admin email for LibreChat
        ADMIN_PASSWORD (str): Admin password for LibreChat
        ENABLE_AUTH (bool): Enable authentication
        ALLOW_REGISTRATION (bool): Allow registration
        ALLOW_SOCIAL_LOGIN (bool): Allow social login
        DEFAULT_MODELS (str): Default models for Ollama
        DEBUG_MODE (bool): Enable debug mode
    """

    # General configuration
    HOST_PORT_LIBRECHAT: int = Field(3080, description="Port for LibreChat")
    HOST_PORT_OLLAMA: int = Field(11434, description="Port for Ollama")

    # Resource limitations
    OLLAMA_CPU_LIMIT: float = Field(0.75, description="CPU limit for Ollama")
    OLLAMA_MEMORY_LIMIT: str = Field("16G", description="Memory limit for Ollama")
    MONGODB_MEMORY_LIMIT: str = Field("2G", description="Memory limit for MongoDB")
    MEILISEARCH_MEMORY_LIMIT: str = Field(
        "1G", description="Memory limit for Meilisearch"
    )
    LIBRECHAT_CPU_LIMIT: float = Field(0.50, description="CPU limit for LibreChat")
    LIBRECHAT_MEMORY_LIMIT: str = Field("4G", description="Memory limit for LibreChat")

    # Versions
    OLLAMA_VERSION: str = Field("0.1.27", description="Ollama version")
    MONGODB_VERSION: str = Field("6.0.6", description="MongoDB version")
    MEILISEARCH_VERSION: str = Field("latest", description="Meilisearch version")
    LIBRECHAT_VERSION: str = Field("latest", description="LibreChat version")

    # Security
    JWT_SECRET: str = Field("", description="JWT secret for LibreChat")
    JWT_REFRESH_SECRET: str = Field("", description="JWT refresh secret for LibreChat")
    SESSION_SECRET: str = Field("", description="Session secret for LibreChat")
    CRYPT_SECRET: str = Field("", description="Encryption secret for LibreChat")
    CREDS_KEY: str = Field("", description="Credentials key for LibreChat")
    CREDS_IV: str = Field("", description="Credentials IV for LibreChat")

    # LibreChat configuration
    ADMIN_EMAIL: str = Field(
        "admin@local.host", description="Admin email for LibreChat"
    )
    ADMIN_PASSWORD: str = Field("", description="Admin password for LibreChat")
    ENABLE_AUTH: bool = Field(True, description="Enable authentication")
    ALLOW_REGISTRATION: bool = Field(True, description="Allow registration")
    ALLOW_SOCIAL_LOGIN: bool = Field(False, description="Allow social login")
    DEFAULT_MODELS: str = Field("tinyllama", description="Default models for Ollama")

    # Debug configuration
    DEBUG_MODE: bool = Field(False, description="Enable debug mode")

    def reset_to_defaults(self) -> None:
        """
        Reset configuration to default values.
        
        This method resets all configuration parameters to their default values
        as defined in the ConfigManager class.
        
        Example:
            ```python
            config = LLMStackConfig()
            config.reset_to_defaults()
            ```
        """
        self.config_dir = self.DEFAULT_CONFIG_DIR
        self.env_file = self.DEFAULT_ENV_FILE
        self.core_project = self.DEFAULT_CORE_PROJECT
        self.debug_project = self.DEFAULT_DEBUG_PROJECT
        self.core_compose = self.DEFAULT_CORE_COMPOSE
        self.debug_compose = self.DEFAULT_DEBUG_COMPOSE
        logging.debug("Configuration reset to default values")
    
    # Cache decorator for methods
    @staticmethod
    def cache_method(func: Callable) -> Callable:
        """
        Decorator to cache method results.
        
        This decorator caches the results of method calls to improve performance
        for frequently called methods. The cache is keyed by the method name and
        arguments.
        
        Args:
            func: The method to decorate
            
        Returns:
            Callable: The decorated method with caching capability
            
        Example:
            ```python
            @LLMStackConfig.cache_method
            def get_config(self, key, default_value=""):
                # Method implementation
                return value
            ```
        """
        cache = {}
        
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Create a cache key from the method name and arguments
            key = (func.__name__, args, frozenset(kwargs.items()))
            if key not in cache:
                cache[key] = func(self, *args, **kwargs)
            return cache[key]
        
        # Add a method to clear the cache
        wrapper.clear_cache = lambda: cache.clear()
        return wrapper
    
    def load_config(self, env_file: Optional[str] = None) -> bool:
        """
        Load configuration from an .env file.

        This method loads configuration values from an environment file and
        exports them to the environment. It also stores the loaded values
        in the config_values dictionary.

        Args:
            env_file: Path to the .env file (defaults to the configured env_file)

        Returns:
            bool: True if the configuration was successfully loaded, False otherwise
            
        Example:
            ```python
            from llm_stack.core import config
            
            # Load configuration from default .env file
            config_manager = config.get_config_manager()
            if config_manager.load_config():
                print("Configuration loaded successfully")
            else:
                print("Failed to load configuration")
                
            # Load configuration from a specific file
            if config_manager.load_config("custom/.env"):
                print("Custom configuration loaded successfully")
            ```
        """
        if env_file is None:
            env_file = self.env_file
            
        logging.debug(f"Loading configuration from {env_file}")

        # Check if file exists
        if not os.path.isfile(env_file):
            logging.warn(f"Configuration file not found: {env_file}")
            return False

        # Check if file is readable
        if not os.access(env_file, os.R_OK):
            logging.error(f"Configuration file is not readable: {env_file}")
            return False

        # Load variables
        config_dict = {}
        logging.debug("Parsing configuration file")

        try:
            # Use context manager for file operations
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue

                    # Split key and value
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]

                        # Export variable to environment
                        os.environ[key] = value
                        config_dict[key] = value
                        logging.debug(f"Configuration loaded: {key}={value}")

            # Store loaded configuration
            self.config_values = config_dict
            
            logging.success(f"Configuration loaded from {env_file}")
            return True
        except Exception as e:
            logging.error(f"Error loading configuration: {str(e)}")
            return False
    def _generate_random_secret(self, length: int, include_punctuation: bool = False) -> str:
        """
        Generate a random secret string of specified length.
        
        Args:
            length: Length of the secret string
            include_punctuation: Whether to include punctuation characters
            
        Returns:
            str: Random secret string
        """
        import secrets
        import string
        
        chars = string.ascii_letters + string.digits
        if include_punctuation:
            chars += string.punctuation
            
        return "".join(secrets.choice(chars) for _ in range(length))
    
    def _create_backup_if_needed(self) -> None:
        """Create a backup of the configuration file if it exists."""
        if os.path.isfile(self.env_file):
            backup_file = self.backup_config_file()
            if backup_file:
                logging.info(f"Backup created: {backup_file}")
    
    def _ensure_config_directory(self) -> None:
        """Ensure that the configuration directory exists."""
        os.makedirs(os.path.dirname(self.env_file), exist_ok=True)
    
    def _write_variables_to_file(self, file_path: str, variables: List[Tuple[str, str]]) -> None:
        """
        Write variables to a configuration file.
        
        Args:
            file_path: Path to the configuration file
            variables: List of (key, value) tuples to write
        """
        with open(file_path, "w") as f:
            for key, value in variables:
                f.write(f"{key}={value}\n")
    
    def generate_secrets(self) -> bool:
        """
        Generate secure secrets for the configuration.

        Returns:
            bool: True if the secrets were successfully generated, False otherwise
        """
        logging.info("Generating secure secrets")

        # Prepare the environment
        self._create_backup_if_needed()
        self._ensure_config_directory()

        # Generate random secrets
        jwt_secret = self._generate_random_secret(64)
        jwt_refresh_secret = self._generate_random_secret(64)
        session_secret = self._generate_random_secret(64)
        crypt_secret = self._generate_random_secret(32)
        creds_key = self._generate_random_secret(32)
        creds_iv = self._generate_random_secret(16)
        admin_password = self._generate_random_secret(16, include_punctuation=True)

        # Variables for the configuration file
        variables = [
            ("JWT_SECRET", jwt_secret),
            ("JWT_REFRESH_SECRET", jwt_refresh_secret),
            ("SESSION_SECRET", session_secret),
            ("CRYPT_SECRET", crypt_secret),
            ("CREDS_KEY", creds_key),
            ("CREDS_IV", creds_iv),
            ("ADMIN_PASSWORD", admin_password),
        ]

        # Update or create configuration file
        if os.path.isfile(self.env_file):
            # Update existing configuration
            self.update_env_vars(self.env_file, variables)
        else:
            # Create new configuration file
            self._write_variables_to_file(self.env_file, variables)

        # Update LibreChat secrets
        self.update_librechat_secrets()

        logging.success("Secure secrets generated")
        logging.info(
            f"Admin password: {admin_password} (save this in a secure location)"
        )

        return True
        
    def update_librechat_secrets(self) -> bool:
        """
        Update LibreChat secrets from the main configuration.

        Returns:
            bool: True if the secrets were successfully updated, False otherwise
        """
        logging.info("Updating LibreChat secrets from the main configuration")

        # LibreChat .env file
        librechat_env = f"{self.config_dir}/librechat/.env"

        # Ensure that the LibreChat configuration directory exists
        os.makedirs(os.path.dirname(librechat_env), exist_ok=True)

        # Get secrets from the main configuration
        jwt_secret = self.get_config("JWT_SECRET", "")
        jwt_refresh_secret = self.get_config("JWT_REFRESH_SECRET", "")
        session_secret = self.get_config("SESSION_SECRET", "")
        crypt_secret = self.get_config("CRYPT_SECRET", "")
        creds_key = self.get_config("CREDS_KEY", "")
        creds_iv = self.get_config("CREDS_IV", "")
        admin_password = self.get_config("ADMIN_PASSWORD", "")

        # Variables for the LibreChat configuration file
        variables = [
            ("JWT_SECRET", jwt_secret),
            ("JWT_REFRESH_SECRET", jwt_refresh_secret),
            ("SESSION_SECRET", session_secret),
            ("CRYPT_SECRET", crypt_secret),
            ("CREDS_KEY", creds_key),
            ("CREDS_IV", creds_iv),
            ("ADMIN_PASSWORD", admin_password),
        ]

        # Update or create LibreChat configuration file
        if os.path.isfile(librechat_env):
            # Create backup
            backup_file = self.backup_config_file(librechat_env)
            if backup_file:
                logging.info(f"Backup created: {backup_file}")

            # Update existing configuration
            self.update_env_vars(librechat_env, variables)
        else:
            # Create new configuration file
            with open(librechat_env, "w") as f:
                for key, value in variables:
                    f.write(f"{key}={value}\n")

        logging.success("LibreChat secrets updated")
        return True
        
    def show_config(self) -> None:
        """Show the current configuration."""
        try:
            if os.path.isfile(self.env_file):
                with open(self.env_file) as f:
                    print(f.read())
            else:
                logging.error(f"Configuration file not found: {self.env_file}")
        except Exception as e:
            logging.error(f"Error showing configuration: {str(e)}")
    
    def edit_config(self) -> None:
        """Open the configuration file in the default editor."""
        editor = os.environ.get("EDITOR", "nano")
        subprocess.run([editor, self.env_file])
    def validate_config(self) -> bool:
        """
        Validate the configuration.

        Returns:
            bool: True if the configuration is valid, False otherwise
        """
        logging.debug("Validating configuration")

        # Check if required configuration files exist
        if not os.path.isfile(self.env_file):
            logging.error(f"Main configuration file not found: {self.env_file}")
            return False

        # Validate port configurations
        host_port_ollama = self.get_config("HOST_PORT_OLLAMA", "11434")
        if not host_port_ollama.isdigit():
            logging.error(f"HOST_PORT_OLLAMA must be a number: {host_port_ollama}")
            return False

        host_port_librechat = self.get_config("HOST_PORT_LIBRECHAT", "3080")
        if not host_port_librechat.isdigit():
            logging.error(f"HOST_PORT_LIBRECHAT must be a number: {host_port_librechat}")
            return False

        # Validate resource limitations
        ollama_cpu_limit = self.get_config("OLLAMA_CPU_LIMIT", "0.75")
        try:
            float(ollama_cpu_limit)
        except ValueError:
            logging.error(
                f"OLLAMA_CPU_LIMIT must be a decimal number: {ollama_cpu_limit}"
            )
            return False

        # Validate memory limitations (ensure they have the G suffix)
        ollama_memory_limit = self.get_config("OLLAMA_MEMORY_LIMIT", "16G")
        if not ollama_memory_limit.endswith("G"):
            logging.error(
                f"OLLAMA_MEMORY_LIMIT must be in the format '16G': {ollama_memory_limit}"
            )
            return False

        # Validate security settings
        jwt_secret = self.get_config("JWT_SECRET", "")
        if not jwt_secret:
            logging.error("JWT_SECRET is not set")
            return False

        jwt_refresh_secret = self.get_config("JWT_REFRESH_SECRET", "")
        if not jwt_refresh_secret:
            logging.error("JWT_REFRESH_SECRET is not set")
            return False

        logging.success("Configuration validation passed")
        return True
        
    def check_secrets(self) -> bool:
        """
        Check if secrets are generated and generate them if needed.

        Returns:
            bool: True if all required secrets are set, False otherwise
        """
        logging.info("Checking if secrets are generated")

        # Check if config/.env exists
        if not os.path.isfile(self.env_file):
            logging.warn("Configuration file not found. Generating secrets...")
            self.generate_secrets()
            return True

        # Check if required secrets in the main configuration file are empty
        jwt_secret = self.get_config("JWT_SECRET", "")
        jwt_refresh_secret = self.get_config("JWT_REFRESH_SECRET", "")
        session_secret = self.get_config("SESSION_SECRET", "")

        # Also check the LibreChat .env file if it exists
        librechat_jwt_secret = ""
        librechat_jwt_refresh_secret = ""
        librechat_needs_update = False
        librechat_env = f"{self.config_dir}/librechat/.env"

        if os.path.isfile(librechat_env):
            logging.debug("LibreChat .env file found")

            # Get LibreChat JWT secrets
            with open(librechat_env) as f:
                for line in f:
                    if line.startswith("JWT_SECRET="):
                        librechat_jwt_secret = line.split("=", 1)[1].strip()
                    elif line.startswith("JWT_REFRESH_SECRET="):
                        librechat_jwt_refresh_secret = line.split("=", 1)[1].strip()

            # Check if LibreChat secrets are empty
            if not librechat_jwt_secret:
                logging.warn("LibreChat JWT_SECRET is empty")
                librechat_needs_update = True

            if not librechat_jwt_refresh_secret:
                logging.warn("LibreChat JWT_REFRESH_SECRET is empty")
                librechat_needs_update = True

        # Check if main secrets need to be generated
        if not jwt_secret or not jwt_refresh_secret or not session_secret:
            logging.warn(
                "Some required secrets are not set in the main configuration. Generating secrets..."
            )
            self.generate_secrets()
        elif librechat_needs_update:
            logging.warn(
                "LibreChat JWT secrets need to be updated. Updating from main configuration..."
            )

            # Update LibreChat secrets from main configuration
            self.update_librechat_secrets()
        else:
            logging.success("All required secrets are set")

        return True
    def save_config(
        self, env_file: Optional[str] = None, variables: Optional[List[Tuple[str, str]]] = None
    ) -> bool:
        """
        Save configuration to an .env file.

        Args:
            env_file: Path to the .env file (defaults to the configured env_file)
            variables: List of (key, value) tuples to be saved

        Returns:
            bool: True if the configuration was successfully saved, False otherwise
        """
        if env_file is None:
            env_file = self.env_file
            
        logging.debug(f"Saving configuration to {env_file}")

        # Ensure that the configuration directory exists
        config_dir = os.path.dirname(env_file)
        os.makedirs(config_dir, exist_ok=True)

        # Create backup if the file exists
        if os.path.isfile(env_file):
            backup_file = self.backup_config_file(env_file)
            if backup_file:
                logging.info(f"Backup created: {backup_file}")
            else:
                logging.warn("Could not create backup of configuration file")

        # If no variables are specified, don't change the file
        if not variables:
            logging.debug("No variables specified, configuration file not changed")
            return True

        # Update configuration file
        try:
            # If the file doesn't exist, create a new file
            if not os.path.isfile(env_file):
                with open(env_file, "w") as f:
                    for key, value in variables:
                        f.write(f"{key}={value}\n")
            else:
                # Update existing file
                self.update_env_vars(env_file, variables)

            # Update the config values
            if variables:
                for key, value in variables:
                    self.config_values[key] = value
                    
            logging.success(f"Configuration saved to {env_file}")
            return True
        except Exception as e:
            logging.error(f"Error saving configuration: {str(e)}")
            return False
            
    def _create_new_env_file(self, env_file: str, variables: List[Tuple[str, str]]) -> bool:
        """
        Create a new environment file with the given variables.
        
        Args:
            env_file: Path to the .env file
            variables: List of (key, value) tuples to be written
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._write_variables_to_file(env_file, variables)
            return True
        except Exception as e:
            logging.error(f"Could not write to {env_file}: {str(e)}")
            return False
    
    def _update_existing_env_file(self, env_file: str, variables: List[Tuple[str, str]]) -> bool:
        """
        Update an existing environment file with the given variables.
        
        Args:
            env_file: Path to the .env file
            variables: List of (key, value) tuples to be updated
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
                # Variables to track which keys were found
                found_keys = set()

                # Read and update existing file
                with open(env_file) as f:
                    for line in f:
                        line = line.strip()
                        # Keep comments and empty lines
                        if not line or line.startswith("#"):
                            tmp_file.write(f"{line}\n")
                            continue

                        # Split key and value
                        if "=" in line:
                            key, _ = line.split("=", 1)
                            key = key.strip()

                            # Check if the key should be updated
                            for var_key, var_value in variables:
                                if key == var_key:
                                    tmp_file.write(f"{var_key}={var_value}\n")
                                    found_keys.add(var_key)
                                    break
                            else:
                                # If the key should not be updated, keep the line
                                tmp_file.write(f"{line}\n")
                        else:
                            # Keep lines without "="
                            tmp_file.write(f"{line}\n")

                # Add keys that were not found
                for var_key, var_value in variables:
                    if var_key not in found_keys:
                        tmp_file.write(f"{var_key}={var_value}\n")

            # Copy temporary file to original file
            shutil.move(tmp_file.name, env_file)
            return True
        except Exception as e:
            logging.error(f"Could not update {env_file}: {str(e)}")
            # Delete temporary file if it could not be moved
            if 'tmp_file' in locals() and os.path.exists(tmp_file.name):
                os.unlink(tmp_file.name)
            return False
    
    def update_env_vars(self, env_file: str, variables: List[Tuple[str, str]]) -> bool:
        """
        Update environment variables in an .env file.

        Args:
            env_file: Path to the .env file
            variables: List of (key, value) tuples to be updated

        Returns:
            bool: True if the update was successful, False otherwise
        """
        logging.debug(f"Updating environment variables in {env_file}")

        # Check if file exists and is writable
        if not os.path.isfile(env_file):
            logging.debug(f"Creating new file: {env_file}")
            return self._create_new_env_file(env_file, variables)

        # Check if file is writable
        if not os.access(env_file, os.W_OK):
            logging.error(f"File {env_file} is not writable")
            return False

        return self._update_existing_env_file(env_file, variables)
            
    def _validate_port_config(self, port_name: str, default_value: str) -> bool:
        """
        Validate that a port configuration is a valid number.
        
        Args:
            port_name: Name of the port configuration
            default_value: Default value for the port
            
        Returns:
            bool: True if valid, False otherwise
        """
        port_value = self.get_config(port_name, default_value)
        if not port_value.isdigit():
            logging.error(f"{port_name} must be a number: {port_value}")
            return False
        return True
    
    def _validate_resource_limit(self, limit_name: str, default_value: str, validation_func: callable) -> bool:
        """
        Validate a resource limit using the provided validation function.
        
        Args:
            limit_name: Name of the resource limit
            default_value: Default value for the limit
            validation_func: Function to validate the limit value
            
        Returns:
            bool: True if valid, False otherwise
        """
        limit_value = self.get_config(limit_name, default_value)
        if not validation_func(limit_value):
            return False
        return True
    
    @cache_method
    def validate_config(self) -> bool:
        """
        Validate the configuration.

        Returns:
            bool: True if the configuration is valid, False otherwise
        """
        logging.debug("Validating configuration")

        try:
            # Check if required configuration files exist
            if not os.path.isfile(self.env_file):
                logging.error(f"Main configuration file not found: {self.env_file}")
                return False

            # Validate port configurations
            if not self._validate_port_config("HOST_PORT_OLLAMA", "11434"):
                return False
                
            if not self._validate_port_config("HOST_PORT_LIBRECHAT", "3080"):
                return False

            # Validate resource limitations
            def validate_cpu_limit(value):
                try:
                    float(value)
                    return True
                except ValueError:
                    logging.error(f"OLLAMA_CPU_LIMIT must be a decimal number: {value}")
                    return False
                    
            if not self._validate_resource_limit("OLLAMA_CPU_LIMIT", "0.75", validate_cpu_limit):
                return False

            # Validate memory limitations
            def validate_memory_limit(value):
                if not value.endswith("G"):
                    logging.error(f"OLLAMA_MEMORY_LIMIT must be in the format '16G': {value}")
                    return False
                return True
                
            if not self._validate_resource_limit("OLLAMA_MEMORY_LIMIT", "16G", validate_memory_limit):
                return False

            # Validate security settings
            jwt_secret = self.get_config("JWT_SECRET", "")
            if not jwt_secret:
                logging.error("JWT_SECRET is not set")
                return False

            jwt_refresh_secret = self.get_config("JWT_REFRESH_SECRET", "")
            if not jwt_refresh_secret:
                logging.error("JWT_REFRESH_SECRET is not set")
                return False

            logging.success("Configuration validation passed")
            return True
        except Exception as e:
            logging.error(f"Error validating configuration: {str(e)}")
            return False
    def _check_librechat_secrets(self) -> Tuple[bool, bool]:
        """
        Check if LibreChat secrets are set and valid.
        
        Returns:
            Tuple[bool, bool]: (LibreChat env exists, LibreChat needs update)
        """
        librechat_jwt_secret = ""
        librechat_jwt_refresh_secret = ""
        librechat_needs_update = False
        librechat_env = f"{self.config_dir}/librechat/.env"
        librechat_exists = False

        if os.path.isfile(librechat_env):
            librechat_exists = True
            logging.debug("LibreChat .env file found")

            # Get LibreChat JWT secrets - use context manager
            with open(librechat_env) as f:
                for line in f:
                    if line.startswith("JWT_SECRET="):
                        librechat_jwt_secret = line.split("=", 1)[1].strip()
                    elif line.startswith("JWT_REFRESH_SECRET="):
                        librechat_jwt_refresh_secret = line.split("=", 1)[1].strip()

            # Check if LibreChat secrets are empty
            if not librechat_jwt_secret:
                logging.warn("LibreChat JWT_SECRET is empty")
                librechat_needs_update = True

            if not librechat_jwt_refresh_secret:
                logging.warn("LibreChat JWT_REFRESH_SECRET is empty")
                librechat_needs_update = True
                
        return librechat_exists, librechat_needs_update
    
    @cache_method
    def check_secrets(self) -> bool:
        """
        Check if secrets are generated and generate them if needed.

        Returns:
            bool: True if all required secrets are set, False otherwise
        """
        logging.info("Checking if secrets are generated")

        try:
            # Check if config/.env exists
            if not os.path.isfile(self.env_file):
                logging.warn("Configuration file not found. Generating secrets...")
                self.generate_secrets()
                return True

            # Check if required secrets in the main configuration file are empty
            jwt_secret = self.get_config("JWT_SECRET", "")
            jwt_refresh_secret = self.get_config("JWT_REFRESH_SECRET", "")
            session_secret = self.get_config("SESSION_SECRET", "")

            # Check LibreChat secrets
            librechat_exists, librechat_needs_update = self._check_librechat_secrets()

            # Check if main secrets need to be generated
            if not jwt_secret or not jwt_refresh_secret or not session_secret:
                logging.warn(
                    "Some required secrets are not set in the main configuration. Generating secrets..."
                )
                self.generate_secrets()
            elif librechat_exists and librechat_needs_update:
                logging.warn(
                    "LibreChat JWT secrets need to be updated. Updating from main configuration..."
                )
                # Update LibreChat secrets from main configuration
                self.update_librechat_secrets()
            else:
                logging.success("All required secrets are set")

            return True
        except Exception as e:
            logging.error(f"Error checking secrets: {str(e)}")
            return False
        
    def generate_secrets(self) -> bool:
        """
        Generate secure secrets for the configuration.

        Returns:
            bool: True if the secrets were successfully generated, False otherwise
        """
        import secrets
        import string

        logging.info("Generating secure secrets")

        # Create backup of current configuration if it exists
        if os.path.isfile(self.env_file):
            backup_file = self.backup_config_file()
            if backup_file:
                logging.info(f"Backup created: {backup_file}")

        # Ensure that the configuration directory exists
        os.makedirs(os.path.dirname(self.env_file), exist_ok=True)

        # Generate random secrets
        jwt_secret = "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(64)
        )
        jwt_refresh_secret = "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(64)
        )
        session_secret = "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(64)
        )
        crypt_secret = "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(32)
        )
        creds_key = "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(32)
        )
        creds_iv = "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(16)
        )
        admin_password = "".join(
            secrets.choice(string.ascii_letters + string.digits + string.punctuation)
            for _ in range(16)
        )

        # Variables for the configuration file
        variables = [
            ("JWT_SECRET", jwt_secret),
            ("JWT_REFRESH_SECRET", jwt_refresh_secret),
            ("SESSION_SECRET", session_secret),
            ("CRYPT_SECRET", crypt_secret),
            ("CREDS_KEY", creds_key),
            ("CREDS_IV", creds_iv),
            ("ADMIN_PASSWORD", admin_password),
        ]

        # Update or create configuration file
        if os.path.isfile(self.env_file):
            # Update existing configuration
            self.update_env_vars(self.env_file, variables)
        else:
            # Create new configuration file
            with open(self.env_file, "w") as f:
                for key, value in variables:
                    f.write(f"{key}={value}\n")

        # Update LibreChat secrets
        self.update_librechat_secrets()

        logging.success("Secure secrets generated")
        logging.info(
            f"Admin password: {admin_password} (save this in a secure location)"
        )

        return True
        
    def update_librechat_secrets(self) -> bool:
        """
        Update LibreChat secrets from the main configuration.

        Returns:
            bool: True if the secrets were successfully updated, False otherwise
        """
        logging.info("Updating LibreChat secrets from the main configuration")

        # LibreChat .env file
        librechat_env = f"{self.config_dir}/librechat/.env"

        # Ensure that the LibreChat configuration directory exists
        os.makedirs(os.path.dirname(librechat_env), exist_ok=True)

        # Get secrets from the main configuration
        jwt_secret = self.get_config("JWT_SECRET", "")
        jwt_refresh_secret = self.get_config("JWT_REFRESH_SECRET", "")
        session_secret = self.get_config("SESSION_SECRET", "")
        crypt_secret = self.get_config("CRYPT_SECRET", "")
        creds_key = self.get_config("CREDS_KEY", "")
        creds_iv = self.get_config("CREDS_IV", "")
        admin_password = self.get_config("ADMIN_PASSWORD", "")

        # Variables for the LibreChat configuration file
        variables = [
            ("JWT_SECRET", jwt_secret),
            ("JWT_REFRESH_SECRET", jwt_refresh_secret),
            ("SESSION_SECRET", session_secret),
            ("CRYPT_SECRET", crypt_secret),
            ("CREDS_KEY", creds_key),
            ("CREDS_IV", creds_iv),
            ("ADMIN_PASSWORD", admin_password),
        ]

        # Update or create LibreChat configuration file
        if os.path.isfile(librechat_env):
            # Create backup
            backup_file = self.backup_config_file(librechat_env)
            if backup_file:
                logging.info(f"Backup created: {backup_file}")

            # Update existing configuration
            self.update_env_vars(librechat_env, variables)
        else:
            # Create new configuration file
            with open(librechat_env, "w") as f:
                for key, value in variables:
                    f.write(f"{key}={value}\n")

        logging.success("LibreChat secrets updated")
        return True
        
    def backup_config_file(self, file_path: Optional[str] = None) -> Optional[str]:
        """
        Create a backup of a configuration file.

        Args:
            file_path: Path to the configuration file (defaults to the configured env_file)

        Returns:
            Optional[str]: Path to the backup file or None if an error occurred
        """
        try:
            if file_path is None:
                file_path = self.env_file
            if not os.path.isfile(file_path):
                logging.error(f"File not found: {file_path}")
                return None

            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup_path = f"{file_path}.{timestamp}.bak"

            # Use shutil.copy2 to preserve metadata
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            logging.error(f"Error creating backup: {str(e)}")
            return None
    
    def show_config(self) -> None:
        """Show the current configuration."""
        if os.path.isfile(self.env_file):
            with open(self.env_file) as f:
                print(f.read())
        else:
            logging.error(f"Configuration file not found: {self.env_file}")
    
    def edit_config(self) -> None:
        """Open the configuration file in the default editor."""
        editor = os.environ.get("EDITOR", "nano")
        subprocess.run([editor, self.env_file])


# Get the singleton instance of the configuration manager
def get_config_manager() -> ConfigManager:
    """
    Get the singleton instance of the configuration manager.
    
    Returns:
        ConfigManager: The configuration manager instance
    """
    return ConfigManager()

# Initialize configuration
def init_config() -> None:
    """Initialize the configuration with default values."""
    config_manager = get_config_manager()
    config_manager.reset_to_defaults()
    logging.debug("Configuration initialized with default values")



# Load configuration from .env file (wrapper for backward compatibility)
def load_config(env_file: Optional[str] = None) -> bool:
    """
    Load configuration from an .env file.

    Args:
        env_file: Path to the .env file (defaults to the configured env_file)

    Returns:
        bool: True if the configuration was successfully loaded, False otherwise
    """
# Check if secrets are generated and generate them if needed (wrapper for backward compatibility)
def check_secrets() -> bool:
    """
    Check if secrets are generated and generate them if needed.

    Returns:
        bool: True if all required secrets are set, False otherwise
    """
    return get_config_manager().check_secrets()


# Generate secure secrets (wrapper for backward compatibility)
def generate_secrets() -> bool:
    """
    Generate secure secrets for the configuration.

    Returns:
        bool: True if the secrets were successfully generated, False otherwise
    """
    return get_config_manager().generate_secrets()


# Update LibreChat secrets from the main configuration (wrapper for backward compatibility)
def update_librechat_secrets() -> bool:
    """
    Update LibreChat secrets from the main configuration.

    Returns:
        bool: True if the secrets were successfully updated, False otherwise
    """
    return get_config_manager().update_librechat_secrets()


# Create a backup of a configuration file (wrapper for backward compatibility)
def backup_config_file(file_path: Optional[str] = None) -> Optional[str]:
    """
    Create a backup of a configuration file.

    Args:
        file_path: Path to the configuration file (defaults to the configured env_file)

    Returns:
        Optional[str]: Path to the backup file or None if an error occurred
    """
    return get_config_manager().backup_config_file(file_path)


# Show configuration (wrapper for backward compatibility)
def show_config() -> None:
    """Show the current configuration."""
    get_config_manager().show_config()


# Edit configuration (wrapper for backward compatibility)
def edit_config() -> None:
    """Open the configuration file in the default editor."""
    get_config_manager().edit_config()
    return get_config_manager().load_config(env_file)


# Save configuration to .env file
def save_config(
    env_file: Optional[str] = None, variables: Optional[List[Tuple[str, str]]] = None
) -> bool:
    """
    Save configuration to an .env file.

    Args:
        env_file: Path to the .env file (defaults to the configured env_file)
        variables: List of (key, value) tuples to be saved

    Returns:
        bool: True if the configuration was successfully saved, False otherwise
    """
    config_manager = get_config_manager()
    
    if env_file is None:
        env_file = config_manager.env_file
        
    logging.debug(f"Saving configuration to {env_file}")

    # Ensure that the configuration directory exists
    config_dir = os.path.dirname(env_file)
    os.makedirs(config_dir, exist_ok=True)

    # Create backup if the file exists
    if os.path.isfile(env_file):
        backup_file = backup_config_file(env_file)
        if backup_file:
            logging.info(f"Backup created: {backup_file}")
        else:
            logging.warn("Could not create backup of configuration file")

    # If no variables are specified, don't change the file
    if not variables:
        logging.debug("No variables specified, configuration file not changed")
        return True

    # Update configuration file
    try:
        # If the file doesn't exist, create a new file
        if not os.path.isfile(env_file):
            with open(env_file, "w") as f:
                for key, value in variables:
                    f.write(f"{key}={value}\n")
        else:
            # Update existing file
            update_env_vars(env_file, variables)

        # Update the manager's config values
        if variables:
            for key, value in variables:
                config_manager.config_values[key] = value
                
        logging.success(f"Configuration saved to {env_file}")
        return True
    except Exception as e:
        logging.error(f"Error saving configuration: {str(e)}")
        return False


# Get configuration value with caching (wrapper for backward compatibility)
@functools.lru_cache(maxsize=128)
def get_config(key: str, default_value: str = "") -> str:
    """
    Get a configuration value with caching.

    Args:
        key: Key of the configuration value
        default_value: Default value if the key doesn't exist

    Returns:
        str: Configuration value or default value
    """
    return get_config_manager().get_config(key, default_value)


# Set configuration value (wrapper for backward compatibility)
def set_config(key: str, value: str) -> None:
    """
    Set a configuration value.

    Args:
        key: Key of the configuration value
        value: Value to set
    """
    get_config_manager().set_config(key, value)


# Update environment variables in a file (wrapper for backward compatibility)
def update_env_vars(env_file: str, variables: List[Tuple[str, str]]) -> bool:
    """
    Update environment variables in an .env file.

    Args:
        env_file: Path to the .env file
        variables: List of (key, value) tuples to be updated

    Returns:
        bool: True if the update was successful, False otherwise
    """
    return get_config_manager().update_env_vars(env_file, variables)


# Validate configuration (wrapper for backward compatibility)
def validate_config() -> bool:
    """
    Validate the configuration.

    Returns:
        bool: True if the configuration is valid, False otherwise
    """
    return get_config_manager().validate_config()


# Check if secrets are generated and generate them if needed (wrapper for backward compatibility)
@functools.lru_cache(maxsize=1)
def check_secrets() -> bool:
    """
    Check if secrets are generated and generate them if needed.

    Returns:
        bool: True if all required secrets are set, False otherwise
    """
    return get_config_manager().check_secrets()


# Generate secure secrets
def generate_secrets() -> bool:
    """
    Generate secure secrets for the configuration.

    Returns:
        bool: True if the secrets were successfully generated, False otherwise
    """
    import secrets
    import string

    logging.info("Generating secure secrets")
    
    config_manager = get_config_manager()

    # Create backup of current configuration if it exists
    if os.path.isfile(config_manager.env_file):
        backup_file = backup_config_file()
        if backup_file:
            logging.info(f"Backup created: {backup_file}")

    # Ensure that the configuration directory exists
    os.makedirs(os.path.dirname(config_manager.env_file), exist_ok=True)

    # Generate random secrets
    jwt_secret = "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(64)
    )
    jwt_refresh_secret = "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(64)
    )
    session_secret = "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(64)
    )
    crypt_secret = "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(32)
    )
    creds_key = "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(32)
    )
    creds_iv = "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(16)
    )
    admin_password = "".join(
        secrets.choice(string.ascii_letters + string.digits + string.punctuation)
        for _ in range(16)
    )

    # Variables for the configuration file
    variables = [
        ("JWT_SECRET", jwt_secret),
        ("JWT_REFRESH_SECRET", jwt_refresh_secret),
        ("SESSION_SECRET", session_secret),
        ("CRYPT_SECRET", crypt_secret),
        ("CREDS_KEY", creds_key),
        ("CREDS_IV", creds_iv),
        ("ADMIN_PASSWORD", admin_password),
    ]

    # Update or create configuration file
    if os.path.isfile(config_manager.env_file):
        # Update existing configuration
        update_env_vars(config_manager.env_file, variables)
    else:
        # Create new configuration file
        with open(config_manager.env_file, "w") as f:
            for key, value in variables:
                f.write(f"{key}={value}\n")

    # Update LibreChat secrets
    update_librechat_secrets()

    logging.success("Secure secrets generated")
    logging.info(
        f"Admin password: {admin_password} (save this in a secure location)"
    )

    return True


# Update LibreChat secrets from the main configuration
def update_librechat_secrets() -> bool:
    """
    Update LibreChat secrets from the main configuration.

    Returns:
        bool: True if the secrets were successfully updated, False otherwise
    """
    logging.info("Updating LibreChat secrets from the main configuration")
    
    config_manager = get_config_manager()

    # LibreChat .env file
    librechat_env = f"{config_manager.config_dir}/librechat/.env"

    # Ensure that the LibreChat configuration directory exists
    os.makedirs(os.path.dirname(librechat_env), exist_ok=True)

    # Get secrets from the main configuration
    jwt_secret = get_config("JWT_SECRET", "")
    jwt_refresh_secret = get_config("JWT_REFRESH_SECRET", "")
    session_secret = get_config("SESSION_SECRET", "")
    crypt_secret = get_config("CRYPT_SECRET", "")
    creds_key = get_config("CREDS_KEY", "")
    creds_iv = get_config("CREDS_IV", "")
    admin_password = get_config("ADMIN_PASSWORD", "")

    # Variables for the LibreChat configuration file
    variables = [
        ("JWT_SECRET", jwt_secret),
        ("JWT_REFRESH_SECRET", jwt_refresh_secret),
        ("SESSION_SECRET", session_secret),
        ("CRYPT_SECRET", crypt_secret),
        ("CREDS_KEY", creds_key),
        ("CREDS_IV", creds_iv),
        ("ADMIN_PASSWORD", admin_password),
    ]

    # Update or create LibreChat configuration file
    if os.path.isfile(librechat_env):
        # Create backup
        backup_file = backup_config_file(librechat_env)
        if backup_file:
            logging.info(f"Backup created: {backup_file}")

        # Update existing configuration
        update_env_vars(librechat_env, variables)
    else:
        # Create new configuration file
        with open(librechat_env, "w") as f:
            for key, value in variables:
                f.write(f"{key}={value}\n")

    logging.success("LibreChat secrets updated")
    return True


# Create a backup of a configuration file (wrapper for backward compatibility)
def backup_config_file(file_path: Optional[str] = None) -> Optional[str]:
    """
    Create a backup of a configuration file.

    Args:
        file_path: Path to the configuration file (defaults to the configured env_file)

    Returns:
        Optional[str]: Path to the backup file or None if an error occurred
    """
    return get_config_manager().backup_config_file(file_path)


# Show configuration
def show_config() -> None:
    """Show the current configuration."""
    config_manager = get_config_manager()
    
    if os.path.isfile(config_manager.env_file):
        with open(config_manager.env_file) as f:
            print(f.read())
    else:
        logging.error(f"Configuration file not found: {config_manager.env_file}")


# Edit configuration
def edit_config() -> None:
    """Open the configuration file in the default editor."""
    config_manager = get_config_manager()
    
    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, config_manager.env_file])


# Initialize configuration
init_config()

logging.debug("Configuration module initialized")
