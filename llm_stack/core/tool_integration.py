"""
Tool Integration for the LLM Stack.

This module provides functions for the integration and management of tools.
It enables listing, checking, executing, and managing tools.
"""

import os
import shutil
import subprocess
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

from llm_stack.core import config, error, interfaces, logging, system, validation
from llm_stack.knowledge_graph.client import get_client
from llm_stack.knowledge_graph.migration import (
    record_bash_file,
    record_code_transformation,
    record_migration_decision,
    record_python_file,
)

# Constants
TOOLS_DIR = os.path.join(system.get_project_root(), "tools")
CONFIG_DIR = os.path.join(system.get_project_root(), "config")


class ToolError(error.LLMStackError):
    """Exception for tool errors."""

    def __init__(self, message: str):
        """
        Initializes a new tool error exception.

        Args:
            message: Error message
        """
        super().__init__(message, error.ErrorCode.MODULE_ERROR)


class ToolManager:
    """Manager for the integration and management of tools."""

    def __init__(self, tools_dir: str = TOOLS_DIR, config_dir: str = CONFIG_DIR):
        """
        Initializes a new ToolManager.

        Args:
            tools_dir: Directory where tools are stored
            config_dir: Directory where configurations are stored
        """
        self.tools_dir = tools_dir
        self.config_dir = config_dir
        self._tool_instances = {}  # Cache for tool instances
        logging.debug(
            f"ToolManager initialized with tools_dir={tools_dir}, config_dir={config_dir}"
        )

    def get_available_tools(self) -> List[str]:
        """
        Returns a list of all available tools.

        Returns:
            List[str]: List of tool names
        """
        logging.debug("Retrieving available tools")

        try:
            # Find all directories in the tools directory that are not hidden directories
            # and not the template directory
            tools = []
            if os.path.isdir(self.tools_dir):
                for item in os.listdir(self.tools_dir):
                    item_path = os.path.join(self.tools_dir, item)
                    if (
                        os.path.isdir(item_path)
                        and not item.startswith(".")
                        and item != "template"
                    ):
                        tools.append(item)

            # Sort the tools
            tools.sort()

            logging.debug(f"Available tools: {', '.join(tools)}")
            return tools
        except Exception as e:
            logging.error(f"Error retrieving available tools: {str(e)}")
            return []

    def tool_exists(self, tool_name: str) -> bool:
        """
        Checks if a tool exists.

        Args:
            tool_name: Name of the tool

        Returns:
            bool: True if the tool exists, False otherwise
        """
        tool_dir = os.path.join(self.tools_dir, tool_name)
        exists = os.path.isdir(tool_dir)

        if exists:
            logging.debug(f"Tool exists: {tool_name}")
        else:
            logging.debug(f"Tool does not exist: {tool_name}")

        return exists
        
    def implements_interface(self, tool_name: str) -> bool:
        """
        Checks if a tool implements the ToolInterface.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            bool: True if the tool implements the ToolInterface, False otherwise
        """
        if not self.tool_exists(tool_name):
            logging.debug(f"Tool does not exist: {tool_name}")
            return False
            
        try:
            # Try to import the tool
            tool_path = f"llm_stack.tools.{tool_name}"
            try:
                tool_module = __import__(tool_path, fromlist=["__init__"])
                
                # Check if the module has a class that implements ToolInterface
                for attr_name in dir(tool_module):
                    attr = getattr(tool_module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, interfaces.ToolInterface) and attr != interfaces.ToolInterface:
                        logging.debug(f"Tool {tool_name} implements ToolInterface with class {attr_name}")
                        return True
                
                logging.debug(f"Tool {tool_name} does not implement ToolInterface")
                return False
            except ImportError:
                logging.debug(f"Could not import tool {tool_path}")
                return False
        except Exception as e:
            logging.error(f"Error checking if tool {tool_name} implements ToolInterface: {str(e)}")
            return False
            
    def get_tool_instance(self, tool_name: str) -> Optional[interfaces.ToolInterface]:
        """
        Gets an instance of a tool that implements the ToolInterface.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Optional[ToolInterface]: Instance of the tool or None if the tool does not implement the interface
            
        Raises:
            ToolError: If the tool does not exist
        """
        # Check if the tool exists
        if not self.tool_exists(tool_name):
            error_msg = f"Tool does not exist: {tool_name}"
            logging.error(error_msg)
            raise ToolError(error_msg)
            
        # Check if we already have an instance
        if tool_name in self._tool_instances:
            return self._tool_instances[tool_name]
            
        # Check if the tool implements the interface
        if not self.implements_interface(tool_name):
            logging.debug(f"Tool {tool_name} does not implement ToolInterface")
            return None
            
        try:
            # Import the tool
            tool_path = f"llm_stack.tools.{tool_name}"
            tool_module = __import__(tool_path, fromlist=["__init__"])
            
            # Find the class that implements ToolInterface
            for attr_name in dir(tool_module):
                attr = getattr(tool_module, attr_name)
                if isinstance(attr, type) and issubclass(attr, interfaces.ToolInterface) and attr != interfaces.ToolInterface:
                    # Create an instance of the class
                    instance = attr()
                    self._tool_instances[tool_name] = instance
                    logging.debug(f"Created instance of {attr_name} for tool {tool_name}")
                    return instance
                    
            logging.debug(f"No class implementing ToolInterface found in tool {tool_name}")
            return None
        except Exception as e:
            error_msg = f"Error creating instance of tool {tool_name}: {str(e)}"
            logging.error(error_msg)
            return None

    def run_tool(self, tool_name: str, *args: str, **kwargs) -> Union[int, Dict]:
        """
        Executes a tool with arguments.

        Args:
            tool_name: Name of the tool
            *args: Additional arguments for the tool
            **kwargs: Additional keyword arguments for the tool

        Returns:
            Union[int, Dict]: Exit code of the tool or result dictionary if using ToolInterface

        Raises:
            ToolError: If the tool does not exist or cannot be executed
        """
        # Check if the tool exists
        if not self.tool_exists(tool_name):
            error_msg = f"Tool does not exist: {tool_name}"
            logging.error(error_msg)
            raise ToolError(error_msg)
            
        # First try to use the ToolInterface if implemented
        tool_instance = self.get_tool_instance(tool_name)
        if tool_instance:
            try:
                logging.debug(f"Executing tool {tool_name} using ToolInterface")
                
                # Initialize the tool if not already initialized
                if not hasattr(tool_instance, '_initialized') or not tool_instance._initialized:
                    if tool_instance.initialize():
                        tool_instance._initialized = True
                    else:
                        logging.error(f"Failed to initialize tool {tool_name} using ToolInterface")
                        # Fall back to file-based approach
                        
                # Execute the tool
                result = tool_instance.execute(**kwargs)
                if result:
                    logging.success(f"Tool execution completed successfully: {tool_name}")
                    return result
                else:
                    logging.error(f"Failed to execute tool {tool_name} using ToolInterface")
                    # Fall back to file-based approach
            except Exception as e:
                logging.error(f"Error executing tool {tool_name} using ToolInterface: {str(e)}")
                # Fall back to file-based approach

        # Fall back to file-based approach
        # Path to the main script of the tool
        main_script = os.path.join(self.tools_dir, tool_name, "main.sh")

        # Check if the main script exists
        if not os.path.isfile(main_script):
            error_msg = f"Tool has no main script: {tool_name}"
            logging.error(error_msg)
            raise ToolError(error_msg)

        # Check if the main script is executable
        if not os.access(main_script, os.X_OK):
            error_msg = f"Main script of the tool is not executable: {tool_name}"
            logging.error(error_msg)
            raise ToolError(error_msg)

        # Arguments as string for logging
        args_str = " ".join(args)
        logging.info(f"Executing tool: {tool_name} {args_str}")

        try:
            # Execute the tool
            result = subprocess.run([main_script, *args], check=False)
            exit_code = result.returncode

            if exit_code != 0:
                logging.error(
                    f"Tool execution failed: {tool_name} (exit code: {exit_code})"
                )
            else:
                logging.success(
                    f"Tool execution completed successfully: {tool_name}"
                )

            return exit_code
        except Exception as e:
            error_msg = f"Error executing tool {tool_name}: {str(e)}"
            logging.error(error_msg)
            raise ToolError(error_msg)

    def get_tool_help(self, tool_name: str) -> int:
        """
        Gibt die Hilfe für ein Tool aus.

        Args:
            tool_name: Name des Tools

        Returns:
            int: Exit-Code des Tools

        Raises:
            ToolError: Wenn das Tool nicht existiert oder keine Hilfe verfügbar ist
        """
        # Prüfen, ob das Tool existiert
        if not self.tool_exists(tool_name):
            error_msg = f"Tool existiert nicht: {tool_name}"
            logging.error(error_msg)
            raise ToolError(error_msg)

        # Pfad zum Hauptskript des Tools
        main_script = os.path.join(self.tools_dir, tool_name, "main.sh")

        # Prüfen, ob das Hauptskript existiert
        if not os.path.isfile(main_script):
            error_msg = f"Tool hat kein Hauptskript: {tool_name}"
            logging.error(error_msg)
            raise ToolError(error_msg)

        try:
            # Tool mit --help-Option ausführen
            result = subprocess.run([main_script, "--help"], check=False)
            return result.returncode
        except Exception as e:
            error_msg = f"Fehler beim Abrufen der Hilfe für Tool {tool_name}: {str(e)}"
            logging.error(error_msg)
            raise ToolError(error_msg)

    def get_tool_version(self, tool_name: str) -> int:
        """
        Gibt die Version eines Tools aus.

        Args:
            tool_name: Name des Tools

        Returns:
            int: Exit-Code des Tools

        Raises:
            ToolError: Wenn das Tool nicht existiert oder keine Version verfügbar ist
        """
        # Prüfen, ob das Tool existiert
        if not self.tool_exists(tool_name):
            error_msg = f"Tool existiert nicht: {tool_name}"
            logging.error(error_msg)
            raise ToolError(error_msg)

        # Pfad zum Hauptskript des Tools
        main_script = os.path.join(self.tools_dir, tool_name, "main.sh")

        # Prüfen, ob das Hauptskript existiert
        if not os.path.isfile(main_script):
            error_msg = f"Tool hat kein Hauptskript: {tool_name}"
            logging.error(error_msg)
            raise ToolError(error_msg)

        try:
            # Tool mit --version-Option ausführen
            result = subprocess.run([main_script, "--version"], check=False)
            return result.returncode
        except Exception as e:
            error_msg = (
                f"Fehler beim Abrufen der Version für Tool {tool_name}: {str(e)}"
            )
            logging.error(error_msg)
            raise ToolError(error_msg)

    def get_tool_config(
        self, tool_name: str, config_key: Optional[str] = None
    ) -> Optional[Union[str, Dict]]:
        """
        Gibt die Konfiguration eines Tools zurück.

        Args:
            tool_name: Name des Tools
            config_key: Optionaler Konfigurationsschlüssel

        Returns:
            Optional[Union[str, Dict]]: Konfigurationswert oder None, wenn ein Fehler aufgetreten ist

        Raises:
            ToolError: Wenn das Tool nicht existiert oder keine Konfiguration verfügbar ist
        """
        # Prüfen, ob das Tool existiert
        if not self.tool_exists(tool_name):
            error_msg = f"Tool existiert nicht: {tool_name}"
            logging.error(error_msg)
            raise ToolError(error_msg)

        # Pfad zur Konfigurationsdatei
        config_file = os.path.join(self.tools_dir, tool_name, "config", "config.yaml")

        # Prüfen, ob die Konfigurationsdatei existiert
        if not os.path.isfile(config_file):
            error_msg = f"Tool hat keine Konfigurationsdatei: {tool_name}"
            logging.error(error_msg)
            raise ToolError(error_msg)

        try:
            # YAML-Datei lesen
            with open(config_file) as f:
                config_data = yaml.safe_load(f)

            # Wenn ein Konfigurationsschlüssel angegeben ist, nur diesen Wert zurückgeben
            if config_key:
                # Schlüssel aufteilen, um verschachtelte Werte zu unterstützen
                keys = config_key.split(".")
                value = config_data

                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        error_msg = (
                            f"Konfigurationsschlüssel nicht gefunden: {config_key}"
                        )
                        logging.error(error_msg)
                        return None

                return value
            else:
                # Gesamte Konfiguration zurückgeben
                return config_data
        except Exception as e:
            error_msg = (
                f"Fehler beim Abrufen der Konfiguration für Tool {tool_name}: {str(e)}"
            )
            logging.error(error_msg)
            raise ToolError(error_msg)

    def set_tool_config(
        self, tool_name: str, config_key: str, config_value: Any
    ) -> bool:
        """
        Setzt einen Konfigurationswert für ein Tool.

        Args:
            tool_name: Name des Tools
            config_key: Konfigurationsschlüssel
            config_value: Konfigurationswert

        Returns:
            bool: True, wenn der Wert erfolgreich gesetzt wurde, sonst False

        Raises:
            ToolError: Wenn das Tool nicht existiert oder die Konfiguration nicht gesetzt werden kann
        """
        # Prüfen, ob das Tool existiert
        if not self.tool_exists(tool_name):
            error_msg = f"Tool existiert nicht: {tool_name}"
            logging.error(error_msg)
            raise ToolError(error_msg)

        # Prüfen, ob ein Konfigurationsschlüssel angegeben ist
        if not config_key:
            error_msg = "Konfigurationsschlüssel ist erforderlich"
            logging.error(error_msg)
            raise ToolError(error_msg)

        # Pfad zur Konfigurationsdatei
        config_file = os.path.join(self.tools_dir, tool_name, "config", "config.yaml")

        # Prüfen, ob die Konfigurationsdatei existiert
        if not os.path.isfile(config_file):
            error_msg = f"Tool hat keine Konfigurationsdatei: {tool_name}"
            logging.error(error_msg)
            raise ToolError(error_msg)

        try:
            # YAML-Datei lesen
            with open(config_file) as f:
                config_data = yaml.safe_load(f)

            # Konfigurationswert setzen
            # Schlüssel aufteilen, um verschachtelte Werte zu unterstützen
            keys = config_key.split(".")
            current = config_data

            # Durch die Schlüssel navigieren, bis auf den letzten
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            # Letzten Schlüssel setzen
            current[keys[-1]] = config_value

            # YAML-Datei schreiben
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            logging.info(
                f"Tool-Konfiguration aktualisiert: {tool_name}.{config_key}={config_value}"
            )
            return True
        except Exception as e:
            error_msg = (
                f"Fehler beim Setzen der Konfiguration für Tool {tool_name}: {str(e)}"
            )
            logging.error(error_msg)
            raise ToolError(error_msg)

    def initialize_tool(self, tool_name: str) -> bool:
        """
        Initialisiert ein neues Tool.

        Args:
            tool_name: Name des Tools

        Returns:
            bool: True, wenn das Tool erfolgreich initialisiert wurde, sonst False

        Raises:
            ToolError: Wenn das Tool bereits existiert oder nicht initialisiert werden kann
        """
        # Prüfen, ob ein Tool-Name angegeben ist
        if not tool_name:
            error_msg = "Tool-Name ist erforderlich"
            logging.error(error_msg)
            raise ToolError(error_msg)

        # Prüfen, ob das Tool bereits existiert
        if self.tool_exists(tool_name):
            error_msg = f"Tool existiert bereits: {tool_name}"
            logging.error(error_msg)
            raise ToolError(error_msg)

        logging.info(f"Initialisiere neues Tool: {tool_name}")

        try:
            # Tool-Verzeichnis erstellen
            tool_dir = os.path.join(self.tools_dir, tool_name)
            os.makedirs(tool_dir, exist_ok=True)

            # Template-Dateien kopieren
            template_dir = os.path.join(self.tools_dir, "template")
            if not os.path.isdir(template_dir):
                error_msg = "Template-Verzeichnis nicht gefunden"
                logging.error(error_msg)
                raise ToolError(error_msg)

            # Alle Dateien und Verzeichnisse aus dem Template-Verzeichnis kopieren
            for item in os.listdir(template_dir):
                source = os.path.join(template_dir, item)
                destination = os.path.join(tool_dir, item)

                if os.path.isdir(source):
                    shutil.copytree(source, destination)
                else:
                    shutil.copy2(source, destination)

            # Tool-Namen in Dateien aktualisieren
            for root, _, files in os.walk(tool_dir):
                for file in files:
                    file_path = os.path.join(root, file)

                    # Nur Textdateien bearbeiten
                    try:
                        with open(file_path) as f:
                            content = f.read()

                        # "template" durch den Tool-Namen ersetzen
                        content = content.replace("template", tool_name)

                        with open(file_path, "w") as f:
                            f.write(content)
                    except UnicodeDecodeError:
                        # Binärdateien überspringen
                        pass

            # Hauptskript ausführbar machen
            main_script = os.path.join(tool_dir, "main.sh")
            if os.path.isfile(main_script):
                os.chmod(main_script, 0o755)

            logging.success(f"Tool erfolgreich initialisiert: {tool_name}")
            return True
        except Exception as e:
            error_msg = (
                f"Fehler bei der Initialisierung des Tools {tool_name}: {str(e)}"
            )
            logging.error(error_msg)

            # Aufräumen bei Fehler
            tool_dir = os.path.join(self.tools_dir, tool_name)
            if os.path.isdir(tool_dir):
                shutil.rmtree(tool_dir)

            raise ToolError(error_msg)

    def run_tool_tests(self, tool_name: str, test_type: str = "all") -> int:
        """
        Führt Tests für ein Tool aus.

        Args:
            tool_name: Name des Tools
            test_type: Typ der Tests (unit, integration, all)

        Returns:
            int: Exit-Code der Tests

        Raises:
            ToolError: Wenn das Tool nicht existiert oder die Tests nicht ausgeführt werden können
        """
        # Prüfen, ob das Tool existiert
        if not self.tool_exists(tool_name):
            error_msg = f"Tool existiert nicht: {tool_name}"
            logging.error(error_msg)
            raise ToolError(error_msg)

        logging.info(f"Führe {test_type}-Tests für Tool aus: {tool_name}")

        # Pfad zum Test-Verzeichnis
        test_dir = os.path.join(self.tools_dir, tool_name, "tests")
        exit_code = 0

        try:
            # Unit-Tests ausführen
            if test_type == "unit" or test_type == "all":
                unit_test_dir = os.path.join(test_dir, "unit")
                if os.path.isdir(unit_test_dir):
                    logging.info("Führe Unit-Tests aus...")

                    # Alle Test-Skripte finden und ausführen
                    for test_script in Path(unit_test_dir).glob("test_*.sh"):
                        if os.access(test_script, os.X_OK):
                            logging.debug(f"Führe Test-Skript aus: {test_script}")
                            result = subprocess.run([str(test_script)], check=False)

                            if result.returncode != 0:
                                logging.error(
                                    f"Unit-Test fehlgeschlagen: {test_script} (Exit-Code: {result.returncode})"
                                )
                                exit_code = result.returncode
                else:
                    logging.warning(f"Keine Unit-Tests gefunden für Tool: {tool_name}")

            # Integrationstests ausführen
            if test_type == "integration" or test_type == "all":
                integration_test_dir = os.path.join(test_dir, "integration")
                if os.path.isdir(integration_test_dir):
                    logging.info("Führe Integrationstests aus...")

                    # Alle Test-Skripte finden und ausführen
                    for test_script in Path(integration_test_dir).glob("test_*.sh"):
                        if os.access(test_script, os.X_OK):
                            logging.debug(f"Führe Test-Skript aus: {test_script}")
                            result = subprocess.run([str(test_script)], check=False)

                            if result.returncode != 0:
                                logging.error(
                                    f"Integrationstest fehlgeschlagen: {test_script} (Exit-Code: {result.returncode})"
                                )
                                exit_code = result.returncode
                else:
                    logging.warning(
                        f"Keine Integrationstests gefunden für Tool: {tool_name}"
                    )

            if exit_code == 0:
                logging.success(f"Alle Tests bestanden für Tool: {tool_name}")
            else:
                logging.error(f"Tests fehlgeschlagen für Tool: {tool_name}")

            return exit_code
        except Exception as e:
            error_msg = (
                f"Fehler bei der Ausführung der Tests für Tool {tool_name}: {str(e)}"
            )
            logging.error(error_msg)
            raise ToolError(error_msg)

    def get_tool_metadata(self, tool_name: str) -> Optional[Dict]:
        """
        Gets metadata for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Optional[Dict]: Metadata of the tool or None if an error occurred

        Raises:
            ToolError: If the tool does not exist or no metadata is available
        """
        # Check if the tool exists
        if not self.tool_exists(tool_name):
            error_msg = f"Tool does not exist: {tool_name}"
            logging.error(error_msg)
            raise ToolError(error_msg)
            
        # First try to use the ToolInterface if implemented
        tool_instance = self.get_tool_instance(tool_name)
        if tool_instance:
            try:
                logging.debug(f"Getting metadata for tool {tool_name} using ToolInterface")
                info = tool_instance.get_info()
                if info:
                    # Add path to the metadata
                    info["path"] = os.path.join(self.tools_dir, tool_name)
                    return info
            except Exception as e:
                logging.error(f"Error getting metadata for tool {tool_name} using ToolInterface: {str(e)}")
                # Fall back to file-based approach

        # Fall back to file-based approach
        # Path to the configuration file
        config_file = os.path.join(self.tools_dir, tool_name, "config", "config.yaml")

        # Check if the configuration file exists
        if not os.path.isfile(config_file):
            error_msg = f"Tool has no configuration file: {tool_name}"
            logging.error(error_msg)
            raise ToolError(error_msg)

        try:
            # Read YAML file
            with open(config_file) as f:
                config_data = yaml.safe_load(f)

            # Extract metadata
            tool_version = config_data.get("tool", {}).get("version", "")
            tool_description = config_data.get("tool", {}).get("description", "")
            tool_author = config_data.get("tool", {}).get("author", "")

            # Return metadata as dictionary
            metadata = {
                "name": tool_name,
                "version": tool_version,
                "description": tool_description,
                "author": tool_author,
                "path": os.path.join(self.tools_dir, tool_name),
            }

            return metadata
        except Exception as e:
            error_msg = f"Error getting metadata for tool {tool_name}: {str(e)}"
            logging.error(error_msg)
            raise ToolError(error_msg)


# Globale Instanz des ToolManagers
_tool_manager = None


def get_tool_manager() -> ToolManager:
    """
    Gibt eine Instanz des ToolManagers zurück.

    Returns:
        ToolManager: Instanz des ToolManagers
    """
    global _tool_manager

    if _tool_manager is None:
        _tool_manager = ToolManager()

    return _tool_manager


# Hilfsfunktionen für einfachen Zugriff auf ToolManager-Methoden


def get_available_tools() -> List[str]:
    """
    Gibt eine Liste aller verfügbaren Tools zurück.

    Returns:
        List[str]: Liste der Tool-Namen
    """
    return get_tool_manager().get_available_tools()


def tool_exists(tool_name: str) -> bool:
    """
    Prüft, ob ein Tool existiert.

    Args:
        tool_name: Name des Tools

    Returns:
        bool: True, wenn das Tool existiert, sonst False
    """
    return get_tool_manager().tool_exists(tool_name)


def run_tool(tool_name: str, *args: str, **kwargs) -> Union[int, Dict]:
    """
    Executes a tool with arguments.

    Args:
        tool_name: Name of the tool
        *args: Additional arguments for the tool
        **kwargs: Additional keyword arguments for the tool

    Returns:
        Union[int, Dict]: Exit code of the tool or result dictionary if using ToolInterface

    Raises:
        ToolError: If the tool does not exist or cannot be executed
    """
    return get_tool_manager().run_tool(tool_name, *args, **kwargs)


def get_tool_help(tool_name: str) -> Union[int, Dict]:
    """
    Gets help information for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Union[int, Dict]: Exit code of the tool or help information if using ToolInterface

    Raises:
        ToolError: If the tool does not exist or no help is available
    """
    return get_tool_manager().get_tool_help(tool_name)


def get_tool_version(tool_name: str) -> Union[int, str]:
    """
    Gets the version of a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Union[int, str]: Exit code of the tool or version string if using ToolInterface

    Raises:
        ToolError: If the tool does not exist or no version is available
    """
    return get_tool_manager().get_tool_version(tool_name)


def get_tool_config(
    tool_name: str, config_key: Optional[str] = None
) -> Optional[Union[str, Dict]]:
    """
    Gibt die Konfiguration eines Tools zurück.

    Args:
        tool_name: Name des Tools
        config_key: Optionaler Konfigurationsschlüssel

    Returns:
        Optional[Union[str, Dict]]: Konfigurationswert oder None, wenn ein Fehler aufgetreten ist

    Raises:
        ToolError: Wenn das Tool nicht existiert oder keine Konfiguration verfügbar ist
    """
    return get_tool_manager().get_tool_config(tool_name, config_key)


def set_tool_config(tool_name: str, config_key: str, config_value: Any) -> bool:
    """
    Setzt einen Konfigurationswert für ein Tool.

    Args:
        tool_name: Name des Tools
        config_key: Konfigurationsschlüssel
        config_value: Konfigurationswert

    Returns:
        bool: True, wenn der Wert erfolgreich gesetzt wurde, sonst False

    Raises:
        ToolError: Wenn das Tool nicht existiert oder die Konfiguration nicht gesetzt werden kann
    """
    return get_tool_manager().set_tool_config(tool_name, config_key, config_value)


def initialize_tool(tool_name: str) -> bool:
    """
    Initialisiert ein neues Tool.

    Args:
        tool_name: Name des Tools

    Returns:
        bool: True, wenn das Tool erfolgreich initialisiert wurde, sonst False

    Raises:
        ToolError: Wenn das Tool bereits existiert oder nicht initialisiert werden kann
    """
    return get_tool_manager().initialize_tool(tool_name)


def run_tool_tests(tool_name: str, test_type: str = "all") -> int:
    """
    Führt Tests für ein Tool aus.

    Args:
        tool_name: Name des Tools
        test_type: Typ der Tests (unit, integration, all)

    Returns:
        int: Exit-Code der Tests

    Raises:
        ToolError: Wenn das Tool nicht existiert oder die Tests nicht ausgeführt werden können
    """
    return get_tool_manager().run_tool_tests(tool_name, test_type)


def get_tool_metadata(tool_name: str) -> Optional[Dict]:
    """
    Gets metadata for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Optional[Dict]: Metadata of the tool or None if an error occurred

    Raises:
        ToolError: If the tool does not exist or no metadata is available
    """
    return get_tool_manager().get_tool_metadata(tool_name)


# Migrationsentscheidungen im Knowledge Graph aufzeichnen
try:
    client = get_client()

    # Migrationsentscheidungen aufzeichnen
    record_migration_decision(
        decision="Objektorientierter Ansatz mit ToolManager-Klasse",
        rationale="Die Verwendung einer ToolManager-Klasse ermöglicht eine bessere Kapselung der Funktionalität und erleichtert das Testen.",
        bash_file_path="lib/core/tool_integration.sh",
        python_file_path="llm_stack/core/tool_integration.py",
        alternatives=[
            "Funktionaler Ansatz wie in der Bash-Datei",
            "Singleton-Muster ohne globale Funktionen",
        ],
        impact="Verbesserte Wartbarkeit und Testbarkeit, konsistenter mit anderen Python-Modulen",
    )

    record_migration_decision(
        decision="Verwendung von YAML statt yq für Konfigurationsverarbeitung",
        rationale="Python hat mit PyYAML eine native Unterstützung für YAML-Verarbeitung, was die Abhängigkeit von externen Tools reduziert.",
        bash_file_path="lib/core/tool_integration.sh",
        python_file_path="llm_stack/core/tool_integration.py",
        alternatives=[
            "Verwendung von subprocess für yq-Aufrufe",
            "Verwendung von JSON statt YAML",
        ],
        impact="Reduzierte externe Abhängigkeiten, bessere Typsicherheit und Fehlerbehandlung",
    )
    
    record_migration_decision(
        decision="Integration with ToolInterface for tool operations",
        rationale="Using the ToolInterface provides a standardized way to interact with tools, reducing reliance on file structure and conventions.",
        bash_file_path="lib/core/tool_integration.sh",
        python_file_path="llm_stack/core/tool_integration.py",
        alternatives=[
            "Continue using only file-based approach",
            "Replace file-based approach entirely with interface-based approach",
        ],
        impact="Improved flexibility, maintainability, and adherence to the specification manifest while maintaining backward compatibility",
    )

    record_migration_decision(
        decision="Einführung einer spezifischen ToolError-Klasse",
        rationale="Eine spezifische Fehlerklasse ermöglicht eine bessere Fehlerbehandlung und -unterscheidung.",
        bash_file_path="lib/core/tool_integration.sh",
        python_file_path="llm_stack/core/tool_integration.py",
        alternatives=[
            "Verwendung allgemeiner Exceptions",
            "Rückgabe von Fehlercodes wie in der Bash-Version",
        ],
        impact="Verbesserte Fehlerbehandlung und -diagnose",
    )

    # Bash-Datei aufzeichnen
    record_bash_file(
        "lib/core/tool_integration.sh",
        """#!/bin/bash
# lib/core/tool_integration.sh
# Standardized tool integration library for LOCAL-LLM-Stack

# Guard against multiple inclusion
if [[ -n "$_CORE_TOOL_INTEGRATION_SH_INCLUDED" ]]; then
  return 0
fi
_CORE_TOOL_INTEGRATION_SH_INCLUDED=1

# Get the absolute path of the script directory
TOOL_INTEGRATION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$TOOL_INTEGRATION_DIR/../.." && pwd)"

# Source dependencies
source "$TOOL_INTEGRATION_DIR/logging.sh"
source "$TOOL_INTEGRATION_DIR/error.sh"
source "$TOOL_INTEGRATION_DIR/validation.sh"
source "$TOOL_INTEGRATION_DIR/config.sh"

# Tool directories
readonly TOOLS_DIR="$ROOT_DIR/tools"
readonly CONFIG_DIR="$ROOT_DIR/config"

# Get a list of all available tools
#
# Returns:
#   Space-separated list of tool names
function get_available_tools() {
  find "$TOOLS_DIR" -mindepth 1 -maxdepth 1 -type d -not -path "*/\\.*" -not -path "*/template" | sort | xargs -n1 basename
}

# Check if a tool exists
#
# Parameters:
#   $1 - Tool name
#
# Returns:
#   0 - Tool exists
#   1 - Tool does not exist
function tool_exists() {
  local tool_name=$1
  
  if [[ -d "$TOOLS_DIR/$tool_name" ]]; then
    return 0
  else
    return 1
  fi
}

# Run a tool with arguments
#
# Parameters:
#   $1 - Tool name
#   $@ - Additional arguments to pass to the tool
#
# Returns:
#   Tool exit code
function run_tool() {
  local tool_name=$1
  shift
  
  # Check if tool exists
  if ! tool_exists "$tool_name"; then
    log_error "Tool does not exist: $tool_name"
    return $ERR_NOT_FOUND
  fi
  
  # Check if tool has a main script
  local main_script="$TOOLS_DIR/$tool_name/main.sh"
  if [[ ! -f "$main_script" ]]; then
    log_error "Tool has no main script: $tool_name"
    return $ERR_NOT_IMPLEMENTED
  fi
  
  # Check if main script is executable
  if [[ ! -x "$main_script" ]]; then
    log_error "Tool main script is not executable: $tool_name"
    return $ERR_PERMISSION_DENIED
  fi
  
  log_info "Running tool: $tool_name $@"
  
  # Run the tool
  "$main_script" "$@"
  local result=$?
  
  if [[ $result -ne 0 ]]; then
    log_error "Tool execution failed: $tool_name (exit code: $result)"
  else
    log_success "Tool execution completed successfully: $tool_name"
  fi
  
  return $result
}

# Get tool help
#
# Parameters:
#   $1 - Tool name
#
# Returns:
#   Tool help text
function get_tool_help() {
  local tool_name=$1
  
  # Check if tool exists
  if ! tool_exists "$tool_name"; then
    log_error "Tool does not exist: $tool_name"
    return $ERR_NOT_FOUND
  fi
  
  # Check if tool has a main script
  local main_script="$TOOLS_DIR/$tool_name/main.sh"
  if [[ ! -f "$main_script" ]]; then
    log_error "Tool has no main script: $tool_name"
    return $ERR_NOT_IMPLEMENTED
  fi
  
  # Run the tool with --help
  "$main_script" --help
  return $?
}

# Get tool version
#
# Parameters:
#   $1 - Tool name
#
# Returns:
#   Tool version
function get_tool_version() {
  local tool_name=$1
  
  # Check if tool exists
  if ! tool_exists "$tool_name"; then
    log_error "Tool does not exist: $tool_name"
    return $ERR_NOT_FOUND
  fi
  
  # Check if tool has a main script
  local main_script="$TOOLS_DIR/$tool_name/main.sh"
  if [[ ! -f "$main_script" ]]; then
    log_error "Tool has no main script: $tool_name"
    return $ERR_NOT_IMPLEMENTED
  fi
  
  # Run the tool with --version
  "$main_script" --version
  return $?
}

# Get tool configuration
#
# Parameters:
#   $1 - Tool name
#   $2 - Configuration key (optional)
#
# Returns:
#   Tool configuration
function get_tool_config() {
  local tool_name=$1
  local config_key=$2
  
  # Check if tool exists
  if ! tool_exists "$tool_name"; then
    log_error "Tool does not exist: $tool_name"
    return $ERR_NOT_FOUND
  fi
  
  # Check if tool has a configuration file
  local config_file="$TOOLS_DIR/$tool_name/config/config.yaml"
  if [[ ! -f "$config_file" ]]; then
    log_error "Tool has no configuration file: $tool_name"
    return $ERR_NOT_FOUND
  fi
  
  # Check if yq is available
  if ! command -v yq &> /dev/null; then
    log_error "yq is required to read YAML configuration"
    return $ERR_DEPENDENCY_MISSING
  fi
  
  # Get configuration
  if [[ -n "$config_key" ]]; then
    yq eval ".$config_key" "$config_file"
  else
    cat "$config_file"
  fi
  
  return $ERR_SUCCESS
}

# Set tool configuration
#
# Parameters:
#   $1 - Tool name
#   $2 - Configuration key
#   $3 - Configuration value
#
# Returns:
#   0 - Success
#   Non-zero - Error code
function set_tool_config() {
  local tool_name=$1
  local config_key=$2
  local config_value=$3
  
  # Check if tool exists
  if ! tool_exists "$tool_name"; then
    log_error "Tool does not exist: $tool_name"
    return $ERR_NOT_FOUND
  fi
  
  # Check if configuration key is provided
  if [[ -z "$config_key" ]]; then
    log_error "Configuration key is required"
    return $ERR_INVALID_ARGUMENT
  fi
  
  # Check if tool has a configuration file
  local config_file="$TOOLS_DIR/$tool_name/config/config.yaml"
  if [[ ! -f "$config_file" ]]; then
    log_error "Tool has no configuration file: $tool_name"
    return $ERR_NOT_FOUND
  fi
  
  # Check if yq is available
  if ! command -v yq &> /dev/null; then
    log_error "yq is required to modify YAML configuration"
    return $ERR_DEPENDENCY_MISSING
  fi
  
  # Update configuration
  yq eval -i ".$config_key = \"$config_value\"" "$config_file"
  local result=$?
  
  if [[ $result -ne 0 ]]; then
    log_error "Failed to update tool configuration: $tool_name.$config_key"
    return $ERR_GENERAL
  }
  
  log_info "Updated tool configuration: $tool_name.$config_key=$config_value"
  return $ERR_SUCCESS
}

# Initialize a new tool
#
# Parameters:
#   $1 - Tool name
#
# Returns:
#   0 - Success
#   Non-zero - Error code
function initialize_tool() {
  local tool_name=$1
  
  # Check if tool name is provided
  if [[ -z "$tool_name" ]]; then
    log_error "Tool name is required"
    return $ERR_INVALID_ARGUMENT
  fi
  
  # Check if tool already exists
  if tool_exists "$tool_name"; then
    log_error "Tool already exists: $tool_name"
    return $ERR_ALREADY_EXISTS
  fi
  
  log_info "Initializing new tool: $tool_name"
  
  # Create tool directory
  local tool_dir="$TOOLS_DIR/$tool_name"
  mkdir -p "$tool_dir"
  
  # Copy template files
  cp -r "$TOOLS_DIR/template/"* "$tool_dir/"
  
  # Update tool name in files
  find "$tool_dir" -type f -exec sed -i "s/template/$tool_name/g" {} \\;
  
  # Make scripts executable
  chmod +x "$tool_dir/main.sh"
  
  log_success "Tool initialized successfully: $tool_name"
  return $ERR_SUCCESS
}

# Run tool tests
#
# Parameters:
#   $1 - Tool name
#   $2 - Test type (unit, integration, all) (default: all)
#
# Returns:
#   0 - Success
#   Non-zero - Error code
function run_tool_tests() {
  local tool_name=$1
  local test_type=${2:-all}
  
  # Check if tool exists
  if ! tool_exists "$tool_name"; then
    log_error "Tool does not exist: $tool_name"
    return $ERR_NOT_FOUND
  fi
  
  log_info "Running $test_type tests for tool: $tool_name"
  
  local test_dir="$TOOLS_DIR/$tool_name/tests"
  local exit_code=0
  
  # Run unit tests
  if [[ "$test_type" == "unit" || "$test_type" == "all" ]]; then
    if [[ -d "$test_dir/unit" ]]; then
      log_info "Running unit tests..."
      find "$test_dir/unit" -name "test_*.sh" -type f -executable | while read -r test_script; do
        log_debug "Running test script: $test_script"
        "$test_script"
        local result=$?
        if [[ $result -ne 0 ]]; then
          log_error "Unit test failed: $test_script (exit code: $result)"
          exit_code=$result
        fi
      done
    else
      log_warning "No unit tests found for tool: $tool_name"
    fi
  fi
  
  # Run integration tests
  if [[ "$test_type" == "integration" || "$test_type" == "all" ]]; then
    if [[ -d "$test_dir/integration" ]]; then
      log_info "Running integration tests..."
      find "$test_dir/integration" -name "test_*.sh" -type f -executable | while read -r test_script; do
        log_debug "Running test script: $test_script"
        "$test_script"
        local result=$?
        if [[ $result -ne 0 ]]; then
          log_error "Integration test failed: $test_script (exit code: $result)"
          exit_code=$result
        fi
      done
    else
      log_warning "No integration tests found for tool: $tool_name"
    fi
  fi
  
  if [[ $exit_code -eq 0 ]]; then
    log_success "All tests passed for tool: $tool_name"
  else
    log_error "Tests failed for tool: $tool_name"
  fi
  
  return $exit_code
}

# Get tool metadata
#
# Parameters:
#   $1 - Tool name
#
# Returns:
#   Tool metadata in JSON format
function get_tool_metadata() {
  local tool_name=$1
  
  # Check if tool exists
  if ! tool_exists "$tool_name"; then
    log_error "Tool does not exist: $tool_name"
    return $ERR_NOT_FOUND
  fi
  
  # Check if tool has a configuration file
  local config_file="$TOOLS_DIR/$tool_name/config/config.yaml"
  if [[ ! -f "$config_file" ]]; then
    log_error "Tool has no configuration file: $tool_name"
    return $ERR_NOT_FOUND
  fi
  
  # Check if yq is available
  if ! command -v yq &> /dev/null; then
    log_error "yq is required to read YAML configuration"
    return $ERR_DEPENDENCY_MISSING
  fi
  
  # Get tool metadata
  local tool_version=$(yq eval '.tool.version' "$config_file")
  local tool_description=$(yq eval '.tool.description' "$config_file")
  local tool_author=$(yq eval '.tool.author' "$config_file")
  
  # Output metadata as JSON
  echo "{"
  echo "  \"name\": \"$tool_name\","
  echo "  \"version\": \"$tool_version\","
  echo "  \"description\": \"$tool_description\","
  echo "  \"author\": \"$tool_author\","
  echo "  \"path\": \"$TOOLS_DIR/$tool_name\""
  echo "}"
  
  return $ERR_SUCCESS
}

# Log initialization of the tool integration library
log_debug "Tool integration library initialized"
""",
    )

    # Python-Datei aufzeichnen
    record_python_file(
        "llm_stack/core/tool_integration.py",
        open(__file__).read(),
        "lib/core/tool_integration.sh",
    )

    # Code-Transformationen aufzeichnen
    record_code_transformation(
        transformation_type="function_to_class_method",
        before=r"""function get_available_tools() {
  find "$TOOLS_DIR" -mindepth 1 -maxdepth 1 -type d -not -path "*/\.*" -not -path "*/template" | sort | xargs -n1 basename
}""",
        after="""def get_available_tools(self) -> List[str]:
        \"\"\"
        Gibt eine Liste aller verfügbaren Tools zurück.
        
        Returns:
            List[str]: Liste der Tool-Namen
        \"\"\"
        logging.debug("Rufe verfügbare Tools ab")
        
        try:
            # Alle Verzeichnisse im Tools-Verzeichnis finden, die keine versteckten Verzeichnisse sind
            # und nicht das Template-Verzeichnis sind
            tools = []
            if os.path.isdir(self.tools_dir):
                for item in os.listdir(self.tools_dir):
                    item_path = os.path.join(self.tools_dir, item)
                    if (os.path.isdir(item_path) and
                        not item.startswith('.') and
                        item != 'template'):
                        tools.append(item)
            
            # Sortieren der Tools
            tools.sort()
            
            logging.debug(f"Verfügbare Tools: {', '.join(tools)}")
            return tools
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der verfügbaren Tools: {str(e)}")
            return []""",
        bash_file_path="lib/core/tool_integration.sh",
        python_file_path="llm_stack/core/tool_integration.py",
    )

    record_code_transformation(
        transformation_type="yaml_processing",
        before="""  # Check if yq is available
  if ! command -v yq &> /dev/null; then
    log_error "yq is required to read YAML configuration"
    return $ERR_DEPENDENCY_MISSING
  fi
  
  # Get configuration
  if [[ -n "$config_key" ]]; then
    yq eval ".$config_key" "$config_file"
  else
    cat "$config_file"
  fi""",
        after="""            # YAML-Datei lesen
            with open(config_file, "r") as f:
                config_data = yaml.safe_load(f)
            
            # Wenn ein Konfigurationsschlüssel angegeben ist, nur diesen Wert zurückgeben
            if config_key:
                # Schlüssel aufteilen, um verschachtelte Werte zu unterstützen
                keys = config_key.split(".")
                value = config_data
                
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        error_msg = f"Konfigurationsschlüssel nicht gefunden: {config_key}"
                        logging.error(error_msg)
                        return None
                
                return value
            else:
                # Gesamte Konfiguration zurückgeben
                return config_data""",
        bash_file_path="lib/core/tool_integration.sh",
        python_file_path="llm_stack/core/tool_integration.py",
    )

    record_code_transformation(
        transformation_type="error_handling",
        before="""  # Check if tool exists
  if ! tool_exists "$tool_name"; then
    log_error "Tool does not exist: $tool_name"
    return $ERR_NOT_FOUND
  fi""",
        after="""        # Prüfen, ob das Tool existiert
        if not self.tool_exists(tool_name):
            error_msg = f"Tool existiert nicht: {tool_name}"
            logging.error(error_msg)
            raise ToolError(error_msg)""",
        bash_file_path="lib/core/tool_integration.sh",
        python_file_path="llm_stack/core/tool_integration.py",
    )

except Exception as e:
    logging.error(f"Fehler beim Aufzeichnen der Migration im Knowledge Graph: {str(e)}")


# Modul initialisieren
logging.debug("Tool-Integration-Modul initialisiert")
