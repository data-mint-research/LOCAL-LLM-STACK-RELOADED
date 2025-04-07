"""
CLI-Befehle für den LLM Stack.

Dieses Paket enthält die Implementierungen der CLI-Befehle für den LLM Stack.
"""

from typing import Any, Callable, Dict, List

# Registrierung der verfügbaren CLI-Befehle
CLI_COMMANDS: Dict[str, Callable] = {}


def register_command(name: str) -> Callable:
    """
    Dekorator zum Registrieren eines CLI-Befehls.

    Args:
        name: Name des Befehls

    Returns:
        Callable: Dekorator-Funktion
    """

    def decorator(func: Callable) -> Callable:
        CLI_COMMANDS[name] = func
        return func

    return decorator


def get_available_commands() -> List[str]:
    """
    Gibt eine Liste der verfügbaren CLI-Befehle zurück.

    Returns:
        List[str]: Liste der verfügbaren Befehle
    """
    return list(CLI_COMMANDS.keys())


def execute_command(name: str, *args: Any, **kwargs: Any) -> int:
    """
    Führt einen CLI-Befehl aus.

    Args:
        name: Name des Befehls
        *args: Positionsargumente für den Befehl
        **kwargs: Schlüsselwortargumente für den Befehl

    Returns:
        int: Exit-Code des Befehls
    """
    if name not in CLI_COMMANDS:
        from llm_stack.core import logging

        logging.error(f"Unbekannter Befehl: {name}")
        return 1

    return CLI_COMMANDS[name](*args, **kwargs)
