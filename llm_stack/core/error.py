"""
Fehlerbehandlung für den LLM Stack.

Dieses Modul definiert Fehlercodes, Ausnahmen und Funktionen zur Fehlerbehandlung.
"""

import sys
import traceback
from enum import Enum
from typing import Any, Callable, Dict, Optional, Type, TypeVar, cast

from llm_stack.core import logging

# Typ-Variable für generische Funktionen
T = TypeVar('T')


# Fehlercodes
class ErrorCode(Enum):
    """Fehlercodes für den LLM Stack."""
    SUCCESS = 0
    GENERAL_ERROR = 1
    CONFIG_ERROR = 2
    FILE_NOT_FOUND = 3
    PERMISSION_DENIED = 4
    NETWORK_ERROR = 5
    DOCKER_ERROR = 6
    MODULE_ERROR = 7
    VALIDATION_ERROR = 8
    SECURITY_ERROR = 9
    DATABASE_ERROR = 10
    API_ERROR = 11
    TIMEOUT_ERROR = 12
    RESOURCE_ERROR = 13
    DEPENDENCY_ERROR = 14
    USER_INPUT_ERROR = 15
    INTERNAL_ERROR = 99


# Benutzerdefinierte Ausnahmen
class LLMStackError(Exception):
    """Basisklasse für alle LLM Stack-Ausnahmen."""
    
    def __init__(self, message: str, code: ErrorCode = ErrorCode.GENERAL_ERROR):
        """
        Initialisiert eine neue LLM Stack-Ausnahme.
        
        Args:
            message: Fehlermeldung
            code: Fehlercode
        """
        self.message = message
        self.code = code
        super().__init__(f"[{code.name}] {message}")


class ConfigError(LLMStackError):
    """Ausnahme für Konfigurationsfehler."""
    
    def __init__(self, message: str):
        """
        Initialisiert eine neue Konfigurationsfehler-Ausnahme.
        
        Args:
            message: Fehlermeldung
        """
        super().__init__(message, ErrorCode.CONFIG_ERROR)


class FileNotFoundError(LLMStackError):
    """Ausnahme für Datei-nicht-gefunden-Fehler."""
    
    def __init__(self, message: str):
        """
        Initialisiert eine neue Datei-nicht-gefunden-Ausnahme.
        
        Args:
            message: Fehlermeldung
        """
        super().__init__(message, ErrorCode.FILE_NOT_FOUND)


class PermissionDeniedError(LLMStackError):
    """Ausnahme für Berechtigungsverweigerungs-Fehler."""
    
    def __init__(self, message: str):
        """
        Initialisiert eine neue Berechtigungsverweigerungs-Ausnahme.
        
        Args:
            message: Fehlermeldung
        """
        super().__init__(message, ErrorCode.PERMISSION_DENIED)


class NetworkError(LLMStackError):
    """Ausnahme für Netzwerkfehler."""
    
    def __init__(self, message: str):
        """
        Initialisiert eine neue Netzwerkfehler-Ausnahme.
        
        Args:
            message: Fehlermeldung
        """
        super().__init__(message, ErrorCode.NETWORK_ERROR)


class DockerError(LLMStackError):
    """Ausnahme für Docker-Fehler."""
    
    def __init__(self, message: str):
        """
        Initialisiert eine neue Docker-Fehler-Ausnahme.
        
        Args:
            message: Fehlermeldung
        """
        super().__init__(message, ErrorCode.DOCKER_ERROR)


class ModuleError(LLMStackError):
    """Ausnahme für Modulfehler."""
    
    def __init__(self, message: str):
        """
        Initialisiert eine neue Modulfehler-Ausnahme.
        
        Args:
            message: Fehlermeldung
        """
        super().__init__(message, ErrorCode.MODULE_ERROR)


class ValidationError(LLMStackError):
    """Ausnahme für Validierungsfehler."""
    
    def __init__(self, message: str):
        """
        Initialisiert eine neue Validierungsfehler-Ausnahme.
        
        Args:
            message: Fehlermeldung
        """
        super().__init__(message, ErrorCode.VALIDATION_ERROR)


class SecurityError(LLMStackError):
    """Ausnahme für Sicherheitsfehler."""
    
    def __init__(self, message: str):
        """
        Initialisiert eine neue Sicherheitsfehler-Ausnahme.
        
        Args:
            message: Fehlermeldung
        """
        super().__init__(message, ErrorCode.SECURITY_ERROR)


# Fehlerbehandlungsfunktionen
def handle_error(error: LLMStackError, exit_on_error: bool = True) -> None:
    """
    Behandelt einen LLM Stack-Fehler.
    
    Args:
        error: Der zu behandelnde Fehler
        exit_on_error: Ob das Programm bei einem Fehler beendet werden soll
    """
    logging.error(f"{error.message} (Code: {error.code.value})")
    
    if exit_on_error:
        sys.exit(error.code.value)


def handle_exception(
    exc: Exception, 
    error_code: ErrorCode = ErrorCode.GENERAL_ERROR, 
    exit_on_error: bool = True
) -> None:
    """
    Behandelt eine allgemeine Ausnahme.
    
    Args:
        exc: Die zu behandelnde Ausnahme
        error_code: Der zu verwendende Fehlercode
        exit_on_error: Ob das Programm bei einem Fehler beendet werden soll
    """
    # Wenn es sich um eine LLMStackError handelt, verwende deren Code
    if isinstance(exc, LLMStackError):
        error_code = exc.code
    
    # Fehlermeldung protokollieren
    logging.error(f"{str(exc)} (Code: {error_code.value})")
    
    # Im Debug-Modus Stack-Trace ausgeben
    if logging.get_log_level() == logging.LogLevel.DEBUG:
        logging.debug(f"Stack-Trace:\n{''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))}")
    
    if exit_on_error:
        sys.exit(error_code.value)


def try_except(
    func: Callable[..., T], 
    error_map: Optional[Dict[Type[Exception], ErrorCode]] = None,
    exit_on_error: bool = True,
    *args: Any, 
    **kwargs: Any
) -> Optional[T]:
    """
    Führt eine Funktion aus und fängt Ausnahmen ab.
    
    Args:
        func: Die auszuführende Funktion
        error_map: Zuordnung von Ausnahmetypen zu Fehlercodes
        exit_on_error: Ob das Programm bei einem Fehler beendet werden soll
        *args: Positionsargumente für die Funktion
        **kwargs: Schlüsselwortargumente für die Funktion
        
    Returns:
        Optional[T]: Rückgabewert der Funktion oder None, wenn ein Fehler aufgetreten ist
    """
    if error_map is None:
        error_map = {}
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        # Fehlercode basierend auf Ausnahmetyp bestimmen
        error_code = ErrorCode.GENERAL_ERROR
        for exc_type, code in error_map.items():
            if isinstance(e, exc_type):
                error_code = code
                break
        
        # Ausnahme behandeln
        handle_exception(e, error_code, exit_on_error)
        return None


def assert_condition(condition: bool, message: str, error_code: ErrorCode = ErrorCode.GENERAL_ERROR) -> None:
    """
    Prüft eine Bedingung und wirft eine Ausnahme, wenn sie nicht erfüllt ist.
    
    Args:
        condition: Die zu prüfende Bedingung
        message: Fehlermeldung, wenn die Bedingung nicht erfüllt ist
        error_code: Der zu verwendende Fehlercode
    
    Raises:
        LLMStackError: Wenn die Bedingung nicht erfüllt ist
    """
    if not condition:
        raise LLMStackError(message, error_code)


# Fehlerbehandlungs-Dekorator
def error_handler(
    error_map: Optional[Dict[Type[Exception], ErrorCode]] = None,
    exit_on_error: bool = True
) -> Callable[[Callable[..., T]], Callable[..., Optional[T]]]:
    """
    Dekorator für Fehlerbehandlung.
    
    Args:
        error_map: Zuordnung von Ausnahmetypen zu Fehlercodes
        exit_on_error: Ob das Programm bei einem Fehler beendet werden soll
        
    Returns:
        Callable: Dekorierte Funktion
    """
    if error_map is None:
        error_map = {}
    
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        def wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            return try_except(func, error_map, exit_on_error, *args, **kwargs)
        return wrapper
    
    return decorator


# Fehlercode-zu-Ausnahme-Zuordnung
ERROR_CODE_TO_EXCEPTION: Dict[ErrorCode, Type[LLMStackError]] = {
    ErrorCode.CONFIG_ERROR: ConfigError,
    ErrorCode.FILE_NOT_FOUND: FileNotFoundError,
    ErrorCode.PERMISSION_DENIED: PermissionDeniedError,
    ErrorCode.NETWORK_ERROR: NetworkError,
    ErrorCode.DOCKER_ERROR: DockerError,
    ErrorCode.MODULE_ERROR: ModuleError,
    ErrorCode.VALIDATION_ERROR: ValidationError,
    ErrorCode.SECURITY_ERROR: SecurityError,
}


def raise_error(code: ErrorCode, message: str) -> None:
    """
    Wirft eine Ausnahme basierend auf einem Fehlercode.
    
    Args:
        code: Der Fehlercode
        message: Die Fehlermeldung
        
    Raises:
        LLMStackError: Die entsprechende Ausnahme für den Fehlercode
    """
    exception_class = ERROR_CODE_TO_EXCEPTION.get(code, LLMStackError)
    if code == ErrorCode.GENERAL_ERROR:
        raise LLMStackError(message, code)
    else:
        # Wir wissen, dass die Ausnahme einen einzelnen String-Parameter erwartet
        raise cast(Any, exception_class)(message)


logging.debug("Fehlerbehandlungsmodul initialisiert")