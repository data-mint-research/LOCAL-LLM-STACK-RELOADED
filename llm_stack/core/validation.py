"""
Validierungsfunktionen für den LLM Stack.

Dieses Modul stellt Funktionen zur Validierung von Konfigurationswerten und anderen Eingaben bereit.
"""

import ipaddress
import os
import re
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, Union

from llm_stack.core import error, logging


def validate_port(port: Union[str, int], name: str = "Port") -> bool:
    """
    Validiert einen Port.
    
    Args:
        port: Der zu validierende Port
        name: Name des Ports für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Port gültig ist, sonst False
    """
    try:
        port_int = int(port)
        if port_int < 1 or port_int > 65535:
            logging.error(f"{name} muss zwischen 1 und 65535 liegen: {port}")
            return False
        return True
    except ValueError:
        logging.error(f"{name} muss eine Zahl sein: {port}")
        return False


def validate_is_decimal(value: Union[str, float], name: str = "Wert") -> bool:
    """
    Validiert, ob ein Wert eine Dezimalzahl ist.
    
    Args:
        value: Der zu validierende Wert
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert eine Dezimalzahl ist, sonst False
    """
    try:
        float(value)
        return True
    except ValueError:
        logging.error(f"{name} muss eine Dezimalzahl sein: {value}")
        return False


def validate_is_integer(value: Union[str, int], name: str = "Wert") -> bool:
    """
    Validiert, ob ein Wert eine Ganzzahl ist.
    
    Args:
        value: Der zu validierende Wert
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert eine Ganzzahl ist, sonst False
    """
    try:
        int(value)
        return True
    except ValueError:
        logging.error(f"{name} muss eine Ganzzahl sein: {value}")
        return False


def validate_is_boolean(value: Union[str, bool], name: str = "Wert") -> bool:
    """
    Validiert, ob ein Wert ein boolescher Wert ist.
    
    Args:
        value: Der zu validierende Wert
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert ein boolescher Wert ist, sonst False
    """
    if isinstance(value, bool):
        return True
    
    if isinstance(value, str):
        value_lower = value.lower()
        if value_lower in ["true", "false", "yes", "no", "1", "0", "y", "n"]:
            return True
    
    logging.error(f"{name} muss ein boolescher Wert sein: {value}")
    return False


def validate_is_url(value: str, name: str = "URL") -> bool:
    """
    Validiert, ob ein Wert eine gültige URL ist.
    
    Args:
        value: Der zu validierende Wert
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert eine gültige URL ist, sonst False
    """
    url_pattern = re.compile(
        r'^(?:http|https)://'  # http:// oder https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # Domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # Port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    if url_pattern.match(value):
        return True
    
    logging.error(f"{name} muss eine gültige URL sein: {value}")
    return False


def validate_is_email(value: str, name: str = "E-Mail") -> bool:
    """
    Validiert, ob ein Wert eine gültige E-Mail-Adresse ist.
    
    Args:
        value: Der zu validierende Wert
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert eine gültige E-Mail-Adresse ist, sonst False
    """
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    if email_pattern.match(value):
        return True
    
    logging.error(f"{name} muss eine gültige E-Mail-Adresse sein: {value}")
    return False


def validate_is_ip_address(value: str, name: str = "IP-Adresse") -> bool:
    """
    Validiert, ob ein Wert eine gültige IP-Adresse ist.
    
    Args:
        value: Der zu validierende Wert
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert eine gültige IP-Adresse ist, sonst False
    """
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        logging.error(f"{name} muss eine gültige IP-Adresse sein: {value}")
        return False


def validate_is_ip_network(value: str, name: str = "IP-Netzwerk") -> bool:
    """
    Validiert, ob ein Wert ein gültiges IP-Netzwerk ist.
    
    Args:
        value: Der zu validierende Wert
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert ein gültiges IP-Netzwerk ist, sonst False
    """
    try:
        ipaddress.ip_network(value, strict=False)
        return True
    except ValueError:
        logging.error(f"{name} muss ein gültiges IP-Netzwerk sein: {value}")
        return False


def validate_is_hostname(value: str, name: str = "Hostname") -> bool:
    """
    Validiert, ob ein Wert ein gültiger Hostname ist.
    
    Args:
        value: Der zu validierende Wert
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert ein gültiger Hostname ist, sonst False
    """
    hostname_pattern = re.compile(r'^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$')
    
    if hostname_pattern.match(value):
        return True
    
    logging.error(f"{name} muss ein gültiger Hostname sein: {value}")
    return False


def validate_is_path(value: str, name: str = "Pfad") -> bool:
    """
    Validiert, ob ein Wert ein gültiger Pfad ist.
    
    Args:
        value: Der zu validierende Wert
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert ein gültiger Pfad ist, sonst False
    """
    try:
        os.path.normpath(value)
        return True
    except Exception:
        logging.error(f"{name} muss ein gültiger Pfad sein: {value}")
        return False


def validate_is_file(value: str, name: str = "Datei") -> bool:
    """
    Validiert, ob ein Wert eine existierende Datei ist.
    
    Args:
        value: Der zu validierende Wert
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert eine existierende Datei ist, sonst False
    """
    if os.path.isfile(value):
        return True
    
    logging.error(f"{name} muss eine existierende Datei sein: {value}")
    return False


def validate_is_directory(value: str, name: str = "Verzeichnis") -> bool:
    """
    Validiert, ob ein Wert ein existierendes Verzeichnis ist.
    
    Args:
        value: Der zu validierende Wert
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert ein existierendes Verzeichnis ist, sonst False
    """
    if os.path.isdir(value):
        return True
    
    logging.error(f"{name} muss ein existierendes Verzeichnis sein: {value}")
    return False


def validate_is_in_list(value: Any, valid_values: List[Any], name: str = "Wert") -> bool:
    """
    Validiert, ob ein Wert in einer Liste gültiger Werte enthalten ist.
    
    Args:
        value: Der zu validierende Wert
        valid_values: Liste gültiger Werte
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert in der Liste enthalten ist, sonst False
    """
    if value in valid_values:
        return True
    
    logging.error(f"{name} muss einer der folgenden Werte sein: {', '.join(map(str, valid_values))}")
    return False


def validate_matches_pattern(value: str, pattern: Union[str, Pattern], name: str = "Wert") -> bool:
    """
    Validiert, ob ein Wert einem Muster entspricht.
    
    Args:
        value: Der zu validierende Wert
        pattern: Regex-Muster oder kompiliertes Muster
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert dem Muster entspricht, sonst False
    """
    if isinstance(pattern, str):
        pattern = re.compile(pattern)
    
    if pattern.match(value):
        return True
    
    logging.error(f"{name} muss dem Muster {pattern.pattern} entsprechen: {value}")
    return False


def validate_length(value: Union[str, List, Dict], min_length: Optional[int] = None, max_length: Optional[int] = None, name: str = "Wert") -> bool:
    """
    Validiert die Länge eines Werts.
    
    Args:
        value: Der zu validierende Wert
        min_length: Minimale Länge
        max_length: Maximale Länge
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert die Längenbedingungen erfüllt, sonst False
    """
    length = len(value)
    
    if min_length is not None and length < min_length:
        logging.error(f"{name} muss mindestens {min_length} Zeichen lang sein: {value}")
        return False
    
    if max_length is not None and length > max_length:
        logging.error(f"{name} darf höchstens {max_length} Zeichen lang sein: {value}")
        return False
    
    return True


def validate_range(value: Union[int, float], min_value: Optional[Union[int, float]] = None, max_value: Optional[Union[int, float]] = None, name: str = "Wert") -> bool:
    """
    Validiert, ob ein Wert in einem Bereich liegt.
    
    Args:
        value: Der zu validierende Wert
        min_value: Minimalwert
        max_value: Maximalwert
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert im Bereich liegt, sonst False
    """
    try:
        value_float = float(value)
        
        if min_value is not None and value_float < min_value:
            logging.error(f"{name} muss mindestens {min_value} sein: {value}")
            return False
        
        if max_value is not None and value_float > max_value:
            logging.error(f"{name} darf höchstens {max_value} sein: {value}")
            return False
        
        return True
    except ValueError:
        logging.error(f"{name} muss eine Zahl sein: {value}")
        return False


def validate_with_function(value: Any, validation_func: Callable[[Any], bool], error_message: str, name: str = "Wert") -> bool:
    """
    Validiert einen Wert mit einer benutzerdefinierten Funktion.
    
    Args:
        value: Der zu validierende Wert
        validation_func: Validierungsfunktion, die True zurückgibt, wenn der Wert gültig ist
        error_message: Fehlermeldung, wenn der Wert ungültig ist
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert gültig ist, sonst False
    """
    if validation_func(value):
        return True
    
    logging.error(f"{name}: {error_message}")
    return False


def validate_all(validations: List[Tuple[Callable, List, Dict]]) -> bool:
    """
    Führt mehrere Validierungen aus und gibt True zurück, wenn alle erfolgreich sind.
    
    Args:
        validations: Liste von Tupeln (Validierungsfunktion, Argumente, Schlüsselwortargumente)
        
    Returns:
        bool: True, wenn alle Validierungen erfolgreich sind, sonst False
    """
    for validation_func, args, kwargs in validations:
        if not validation_func(*args, **kwargs):
            return False
    
    return True


def validate_any(validations: List[Tuple[Callable, List, Dict]]) -> bool:
    """
    Führt mehrere Validierungen aus und gibt True zurück, wenn mindestens eine erfolgreich ist.
    
    Args:
        validations: Liste von Tupeln (Validierungsfunktion, Argumente, Schlüsselwortargumente)
        
    Returns:
        bool: True, wenn mindestens eine Validierung erfolgreich ist, sonst False
    """
    for validation_func, args, kwargs in validations:
        if validation_func(*args, **kwargs):
            return True
    
    logging.error("Keine der Validierungen war erfolgreich")
    return False


def validate_memory_format(value: str, name: str = "Speicherwert") -> bool:
    """
    Validiert, ob ein Wert ein gültiges Speicherformat hat (z.B. "16G", "512M").
    
    Args:
        value: Der zu validierende Wert
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert ein gültiges Speicherformat hat, sonst False
    """
    memory_pattern = re.compile(r'^(\d+)([KMGTkmgt])[Bb]?$')
    match = memory_pattern.match(value)
    
    if match:
        return True
    
    logging.error(f"{name} muss im Format '16G' oder '512M' sein: {value}")
    return False


def validate_cpu_format(value: Union[str, float], name: str = "CPU-Wert") -> bool:
    """
    Validiert, ob ein Wert ein gültiges CPU-Format hat (z.B. "0.5", "2").
    
    Args:
        value: Der zu validierende Wert
        name: Name des Werts für Fehlermeldungen
        
    Returns:
        bool: True, wenn der Wert ein gültiges CPU-Format hat, sonst False
    """
    try:
        cpu_value = float(value)
        if cpu_value <= 0:
            logging.error(f"{name} muss größer als 0 sein: {value}")
            return False
        return True
    except ValueError:
        logging.error(f"{name} muss eine Dezimalzahl sein: {value}")
        return False


logging.debug("Validierungsmodul initialisiert")