"""
Konfigurationsmanagement für den LLM Stack.

Dieses Modul stellt Funktionen zum Laden, Validieren und Verwalten der Konfiguration bereit.
"""

import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import yaml
from pydantic import BaseModel, Field

from llm_stack.core import logging

# Standardkonfigurationswerte
DEFAULT_CONFIG_DIR = "config"
DEFAULT_ENV_FILE = f"{DEFAULT_CONFIG_DIR}/.env"
DEFAULT_CORE_PROJECT = "local-llm-stack"
DEFAULT_DEBUG_PROJECT = f"{DEFAULT_CORE_PROJECT}-debug"
DEFAULT_CORE_COMPOSE = "-f docker/core/docker-compose.yml"
DEFAULT_DEBUG_COMPOSE = f"{DEFAULT_CORE_COMPOSE} -f docker/core/docker-compose.debug.yml"

# Globale Konfigurationsvariablen
CONFIG_DIR = DEFAULT_CONFIG_DIR
ENV_FILE = DEFAULT_ENV_FILE
CORE_PROJECT = DEFAULT_CORE_PROJECT
DEBUG_PROJECT = DEFAULT_DEBUG_PROJECT
CORE_COMPOSE = DEFAULT_CORE_COMPOSE
DEBUG_COMPOSE = DEFAULT_DEBUG_COMPOSE

# Konfigurationsmodell
class LLMStackConfig(BaseModel):
    """Konfigurationsmodell für den LLM Stack."""
    
    # Allgemeine Konfiguration
    HOST_PORT_LIBRECHAT: int = Field(3080, description="Port für LibreChat")
    HOST_PORT_OLLAMA: int = Field(11434, description="Port für Ollama")
    
    # Ressourcenbeschränkungen
    OLLAMA_CPU_LIMIT: float = Field(0.75, description="CPU-Limit für Ollama")
    OLLAMA_MEMORY_LIMIT: str = Field("16G", description="Speicherlimit für Ollama")
    MONGODB_MEMORY_LIMIT: str = Field("2G", description="Speicherlimit für MongoDB")
    MEILISEARCH_MEMORY_LIMIT: str = Field("1G", description="Speicherlimit für Meilisearch")
    LIBRECHAT_CPU_LIMIT: float = Field(0.50, description="CPU-Limit für LibreChat")
    LIBRECHAT_MEMORY_LIMIT: str = Field("4G", description="Speicherlimit für LibreChat")
    
    # Versionen
    OLLAMA_VERSION: str = Field("0.1.27", description="Ollama-Version")
    MONGODB_VERSION: str = Field("6.0.6", description="MongoDB-Version")
    MEILISEARCH_VERSION: str = Field("latest", description="Meilisearch-Version")
    LIBRECHAT_VERSION: str = Field("latest", description="LibreChat-Version")
    
    # Sicherheit
    JWT_SECRET: str = Field("", description="JWT-Secret für LibreChat")
    JWT_REFRESH_SECRET: str = Field("", description="JWT-Refresh-Secret für LibreChat")
    SESSION_SECRET: str = Field("", description="Session-Secret für LibreChat")
    CRYPT_SECRET: str = Field("", description="Verschlüsselungs-Secret für LibreChat")
    CREDS_KEY: str = Field("", description="Credentials-Key für LibreChat")
    CREDS_IV: str = Field("", description="Credentials-IV für LibreChat")
    
    # LibreChat-Konfiguration
    ADMIN_EMAIL: str = Field("admin@local.host", description="Admin-E-Mail für LibreChat")
    ADMIN_PASSWORD: str = Field("", description="Admin-Passwort für LibreChat")
    ENABLE_AUTH: bool = Field(True, description="Authentifizierung aktivieren")
    ALLOW_REGISTRATION: bool = Field(True, description="Registrierung erlauben")
    ALLOW_SOCIAL_LOGIN: bool = Field(False, description="Social-Login erlauben")
    DEFAULT_MODELS: str = Field("tinyllama", description="Standardmodelle für Ollama")
    
    # Debug-Konfiguration
    DEBUG_MODE: bool = Field(False, description="Debug-Modus aktivieren")


# Konfiguration initialisieren
def init_config() -> None:
    """Initialisiert die Konfiguration mit Standardwerten."""
    global CONFIG_DIR, ENV_FILE, CORE_PROJECT, DEBUG_PROJECT, CORE_COMPOSE, DEBUG_COMPOSE
    
    logging.debug("Initialisiere Konfiguration mit Standardwerten")
    
    # Standardwerte setzen
    CONFIG_DIR = DEFAULT_CONFIG_DIR
    ENV_FILE = DEFAULT_ENV_FILE
    CORE_PROJECT = DEFAULT_CORE_PROJECT
    DEBUG_PROJECT = DEFAULT_DEBUG_PROJECT
    CORE_COMPOSE = DEFAULT_CORE_COMPOSE
    DEBUG_COMPOSE = DEFAULT_DEBUG_COMPOSE


# Konfiguration aus .env-Datei laden
def load_config(env_file: str = ENV_FILE) -> bool:
    """
    Lädt die Konfiguration aus einer .env-Datei.
    
    Args:
        env_file: Pfad zur .env-Datei
        
    Returns:
        bool: True, wenn die Konfiguration erfolgreich geladen wurde, sonst False
    """
    logging.debug(f"Lade Konfiguration aus {env_file}")
    
    # Prüfen, ob Datei existiert
    if not os.path.isfile(env_file):
        logging.warn(f"Konfigurationsdatei nicht gefunden: {env_file}")
        return False
    
    # Prüfen, ob Datei lesbar ist
    if not os.access(env_file, os.R_OK):
        logging.error(f"Konfigurationsdatei ist nicht lesbar: {env_file}")
        return False
    
    # Variablen laden
    config_dict = {}
    logging.debug("Konfigurationsdatei wird geparst")
    
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            # Kommentare und leere Zeilen überspringen
            if not line or line.startswith("#"):
                continue
                
            # Schlüssel und Wert trennen
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                
                # Anführungszeichen entfernen, wenn vorhanden
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                
                # Variable in die Umgebung exportieren
                os.environ[key] = value
                config_dict[key] = value
                logging.debug(f"Konfiguration geladen: {key}={value}")
    
    logging.success(f"Konfiguration aus {env_file} geladen")
    return True


# Konfiguration in .env-Datei speichern
def save_config(env_file: str = ENV_FILE, variables: Optional[List[Tuple[str, str]]] = None) -> bool:
    """
    Speichert die Konfiguration in einer .env-Datei.
    
    Args:
        env_file: Pfad zur .env-Datei
        variables: Liste von (Schlüssel, Wert)-Tupeln, die gespeichert werden sollen
        
    Returns:
        bool: True, wenn die Konfiguration erfolgreich gespeichert wurde, sonst False
    """
    logging.debug(f"Speichere Konfiguration in {env_file}")
    
    # Sicherstellen, dass das Konfigurationsverzeichnis existiert
    config_dir = os.path.dirname(env_file)
    os.makedirs(config_dir, exist_ok=True)
    
    # Backup erstellen, wenn die Datei existiert
    if os.path.isfile(env_file):
        backup_file = backup_config_file(env_file)
        if backup_file:
            logging.info(f"Backup erstellt: {backup_file}")
        else:
            logging.warn("Konnte kein Backup der Konfigurationsdatei erstellen")
    
    # Wenn keine Variablen angegeben sind, Datei nicht ändern
    if not variables:
        logging.debug("Keine Variablen angegeben, Konfigurationsdatei nicht geändert")
        return True
    
    # Konfigurationsdatei aktualisieren
    try:
        # Wenn die Datei nicht existiert, neue Datei erstellen
        if not os.path.isfile(env_file):
            with open(env_file, "w") as f:
                for key, value in variables:
                    f.write(f"{key}={value}\n")
        else:
            # Bestehende Datei aktualisieren
            update_env_vars(env_file, variables)
        
        logging.success(f"Konfiguration in {env_file} gespeichert")
        return True
    except Exception as e:
        logging.error(f"Fehler beim Speichern der Konfiguration: {str(e)}")
        return False


# Konfigurationswert abrufen
def get_config(key: str, default_value: str = "") -> str:
    """
    Ruft einen Konfigurationswert ab.
    
    Args:
        key: Schlüssel des Konfigurationswerts
        default_value: Standardwert, falls der Schlüssel nicht existiert
        
    Returns:
        str: Konfigurationswert oder Standardwert
    """
    logging.debug(f"Rufe Konfigurationswert für {key} ab")
    
    # Wert aus der Umgebung abrufen
    value = os.environ.get(key, default_value)
    
    return value


# Konfigurationswert setzen
def set_config(key: str, value: str) -> None:
    """
    Setzt einen Konfigurationswert.
    
    Args:
        key: Schlüssel des Konfigurationswerts
        value: Wert, der gesetzt werden soll
    """
    logging.debug(f"Setze Konfigurationswert: {key}={value}")
    
    # Variable in die Umgebung exportieren
    os.environ[key] = value


# Umgebungsvariablen in einer Datei aktualisieren
def update_env_vars(env_file: str, variables: List[Tuple[str, str]]) -> bool:
    """
    Aktualisiert Umgebungsvariablen in einer .env-Datei.
    
    Args:
        env_file: Pfad zur .env-Datei
        variables: Liste von (Schlüssel, Wert)-Tupeln, die aktualisiert werden sollen
        
    Returns:
        bool: True, wenn die Aktualisierung erfolgreich war, sonst False
    """
    logging.debug(f"Aktualisiere Umgebungsvariablen in {env_file}")
    
    # Prüfen, ob Datei existiert und schreibbar ist
    if not os.path.isfile(env_file):
        logging.debug(f"Erstelle neue Datei: {env_file}")
        # Neue Datei mit den Variablen erstellen
        try:
            with open(env_file, "w") as f:
                for key, value in variables:
                    f.write(f"{key}={value}\n")
            return True
        except Exception as e:
            logging.error(f"Konnte nicht in {env_file} schreiben: {str(e)}")
            return False
    
    # Prüfen, ob Datei schreibbar ist
    if not os.access(env_file, os.W_OK):
        logging.error(f"Datei {env_file} ist nicht schreibbar")
        return False
    
    # Temporäre Datei erstellen
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
        # Variablen zum Verfolgen, welche Schlüssel gefunden wurden
        found_keys = set()
        
        # Bestehende Datei lesen und aktualisieren
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                # Kommentare und leere Zeilen beibehalten
                if not line or line.startswith("#"):
                    tmp_file.write(f"{line}\n")
                    continue
                
                # Schlüssel und Wert trennen
                if "=" in line:
                    key, _ = line.split("=", 1)
                    key = key.strip()
                    
                    # Prüfen, ob der Schlüssel aktualisiert werden soll
                    for var_key, var_value in variables:
                        if key == var_key:
                            tmp_file.write(f"{var_key}={var_value}\n")
                            found_keys.add(var_key)
                            break
                    else:
                        # Wenn der Schlüssel nicht aktualisiert werden soll, Zeile beibehalten
                        tmp_file.write(f"{line}\n")
                else:
                    # Zeilen ohne "=" beibehalten
                    tmp_file.write(f"{line}\n")
        
        # Nicht gefundene Schlüssel hinzufügen
        for var_key, var_value in variables:
            if var_key not in found_keys:
                tmp_file.write(f"{var_key}={var_value}\n")
    
    # Temporäre Datei in die Originaldatei kopieren
    try:
        shutil.move(tmp_file.name, env_file)
        return True
    except Exception as e:
        logging.error(f"Konnte {env_file} nicht aktualisieren: {str(e)}")
        # Temporäre Datei löschen, wenn sie nicht verschoben werden konnte
        if os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)
        return False


# Konfiguration validieren
def validate_config() -> bool:
    """
    Validiert die Konfiguration.
    
    Returns:
        bool: True, wenn die Konfiguration gültig ist, sonst False
    """
    logging.debug("Validiere Konfiguration")
    
    # Prüfen, ob erforderliche Konfigurationsdateien existieren
    if not os.path.isfile(ENV_FILE):
        logging.error(f"Hauptkonfigurationsdatei nicht gefunden: {ENV_FILE}")
        return False
    
    # Port-Konfigurationen validieren
    host_port_ollama = get_config("HOST_PORT_OLLAMA", "11434")
    if not host_port_ollama.isdigit():
        logging.error(f"HOST_PORT_OLLAMA muss eine Zahl sein: {host_port_ollama}")
        return False
    
    host_port_librechat = get_config("HOST_PORT_LIBRECHAT", "3080")
    if not host_port_librechat.isdigit():
        logging.error(f"HOST_PORT_LIBRECHAT muss eine Zahl sein: {host_port_librechat}")
        return False
    
    # Ressourcenbeschränkungen validieren
    ollama_cpu_limit = get_config("OLLAMA_CPU_LIMIT", "0.75")
    try:
        float(ollama_cpu_limit)
    except ValueError:
        logging.error(f"OLLAMA_CPU_LIMIT muss eine Dezimalzahl sein: {ollama_cpu_limit}")
        return False
    
    # Speicherbeschränkungen validieren (sicherstellen, dass sie das G-Suffix haben)
    ollama_memory_limit = get_config("OLLAMA_MEMORY_LIMIT", "16G")
    if not ollama_memory_limit.endswith("G"):
        logging.error(f"OLLAMA_MEMORY_LIMIT muss im Format '16G' sein: {ollama_memory_limit}")
        return False
    
    # Sicherheitseinstellungen validieren
    jwt_secret = get_config("JWT_SECRET", "")
    if not jwt_secret:
        logging.error("JWT_SECRET ist nicht gesetzt")
        return False
    
    jwt_refresh_secret = get_config("JWT_REFRESH_SECRET", "")
    if not jwt_refresh_secret:
        logging.error("JWT_REFRESH_SECRET ist nicht gesetzt")
        return False
    
    logging.success("Konfigurationsvalidierung bestanden")
    return True


# Prüfen, ob Secrets generiert sind und sie bei Bedarf generieren
def check_secrets() -> bool:
    """
    Prüft, ob Secrets generiert sind und generiert sie bei Bedarf.
    
    Returns:
        bool: True, wenn alle erforderlichen Secrets gesetzt sind, sonst False
    """
    logging.info("Prüfe, ob Secrets generiert sind")
    
    # Prüfen, ob config/.env existiert
    if not os.path.isfile(ENV_FILE):
        logging.warn("Konfigurationsdatei nicht gefunden. Generiere Secrets...")
        generate_secrets()
        return True
    
    # Prüfen, ob erforderliche Secrets in der Hauptkonfigurationsdatei leer sind
    jwt_secret = get_config("JWT_SECRET", "")
    jwt_refresh_secret = get_config("JWT_REFRESH_SECRET", "")
    session_secret = get_config("SESSION_SECRET", "")
    
    # Auch die LibreChat .env-Datei prüfen, wenn sie existiert
    librechat_jwt_secret = ""
    librechat_jwt_refresh_secret = ""
    librechat_needs_update = False
    librechat_env = f"{CONFIG_DIR}/librechat/.env"
    
    if os.path.isfile(librechat_env):
        logging.debug("LibreChat .env-Datei gefunden")
        
        # LibreChat JWT-Secrets abrufen
        with open(librechat_env, "r") as f:
            for line in f:
                if line.startswith("JWT_SECRET="):
                    librechat_jwt_secret = line.split("=", 1)[1].strip()
                elif line.startswith("JWT_REFRESH_SECRET="):
                    librechat_jwt_refresh_secret = line.split("=", 1)[1].strip()
        
        # Prüfen, ob LibreChat-Secrets leer sind
        if not librechat_jwt_secret:
            logging.warn("LibreChat JWT_SECRET ist leer")
            librechat_needs_update = True
        
        if not librechat_jwt_refresh_secret:
            logging.warn("LibreChat JWT_REFRESH_SECRET ist leer")
            librechat_needs_update = True
    
    # Prüfen, ob Hauptsecrets generiert werden müssen
    if not jwt_secret or not jwt_refresh_secret or not session_secret:
        logging.warn("Einige erforderliche Secrets sind in der Hauptkonfiguration nicht gesetzt. Generiere Secrets...")
        generate_secrets()
    elif librechat_needs_update:
        logging.warn("LibreChat JWT-Secrets müssen aktualisiert werden. Aktualisiere aus der Hauptkonfiguration...")
        
        # LibreChat-Secrets aus der Hauptkonfiguration aktualisieren
        update_librechat_secrets()
    else:
        logging.success("Alle erforderlichen Secrets sind gesetzt")
    
    return True


# Sichere Secrets generieren
def generate_secrets() -> bool:
    """
    Generiert sichere Secrets für die Konfiguration.
    
    Returns:
        bool: True, wenn die Secrets erfolgreich generiert wurden, sonst False
    """
    import secrets
    import string
    
    logging.info("Generiere sichere Secrets")
    
    # Backup der aktuellen Konfiguration erstellen, wenn sie existiert
    if os.path.isfile(ENV_FILE):
        backup_file = backup_config_file()
        if backup_file:
            logging.info(f"Backup erstellt: {backup_file}")
    
    # Sicherstellen, dass das Konfigurationsverzeichnis existiert
    os.makedirs(os.path.dirname(ENV_FILE), exist_ok=True)
    
    # Zufällige Secrets generieren
    jwt_secret = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))
    jwt_refresh_secret = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))
    session_secret = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))
    crypt_secret = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    creds_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    creds_iv = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
    admin_password = ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(16))
    
    # Variablen für die Konfigurationsdatei
    variables = [
        ("JWT_SECRET", jwt_secret),
        ("JWT_REFRESH_SECRET", jwt_refresh_secret),
        ("SESSION_SECRET", session_secret),
        ("CRYPT_SECRET", crypt_secret),
        ("CREDS_KEY", creds_key),
        ("CREDS_IV", creds_iv),
        ("ADMIN_PASSWORD", admin_password)
    ]
    
    # Konfigurationsdatei aktualisieren oder erstellen
    if os.path.isfile(ENV_FILE):
        # Bestehende Konfiguration aktualisieren
        update_env_vars(ENV_FILE, variables)
    else:
        # Neue Konfigurationsdatei erstellen
        with open(ENV_FILE, "w") as f:
            for key, value in variables:
                f.write(f"{key}={value}\n")
    
    # LibreChat-Secrets aktualisieren
    update_librechat_secrets()
    
    logging.success("Sichere Secrets generiert")
    logging.info(f"Admin-Passwort: {admin_password} (speichern Sie dies an einem sicheren Ort)")
    
    return True


# LibreChat-Secrets aus der Hauptkonfiguration aktualisieren
def update_librechat_secrets() -> bool:
    """
    Aktualisiert LibreChat-Secrets aus der Hauptkonfiguration.
    
    Returns:
        bool: True, wenn die Secrets erfolgreich aktualisiert wurden, sonst False
    """
    logging.info("Aktualisiere LibreChat-Secrets aus der Hauptkonfiguration")
    
    # LibreChat .env-Datei
    librechat_env = f"{CONFIG_DIR}/librechat/.env"
    
    # Sicherstellen, dass das LibreChat-Konfigurationsverzeichnis existiert
    os.makedirs(os.path.dirname(librechat_env), exist_ok=True)
    
    # Secrets aus der Hauptkonfiguration abrufen
    jwt_secret = get_config("JWT_SECRET", "")
    jwt_refresh_secret = get_config("JWT_REFRESH_SECRET", "")
    session_secret = get_config("SESSION_SECRET", "")
    crypt_secret = get_config("CRYPT_SECRET", "")
    creds_key = get_config("CREDS_KEY", "")
    creds_iv = get_config("CREDS_IV", "")
    admin_password = get_config("ADMIN_PASSWORD", "")
    
    # Variablen für die LibreChat-Konfigurationsdatei
    variables = [
        ("JWT_SECRET", jwt_secret),
        ("JWT_REFRESH_SECRET", jwt_refresh_secret),
        ("SESSION_SECRET", session_secret),
        ("CRYPT_SECRET", crypt_secret),
        ("CREDS_KEY", creds_key),
        ("CREDS_IV", creds_iv),
        ("ADMIN_PASSWORD", admin_password)
    ]
    
    # LibreChat-Konfigurationsdatei aktualisieren oder erstellen
    if os.path.isfile(librechat_env):
        # Backup erstellen
        backup_file = backup_config_file(librechat_env)
        if backup_file:
            logging.info(f"Backup erstellt: {backup_file}")
        
        # Bestehende Konfiguration aktualisieren
        update_env_vars(librechat_env, variables)
    else:
        # Neue Konfigurationsdatei erstellen
        with open(librechat_env, "w") as f:
            for key, value in variables:
                f.write(f"{key}={value}\n")
    
    logging.success("LibreChat-Secrets aktualisiert")
    return True


# Backup einer Konfigurationsdatei erstellen
def backup_config_file(file_path: str = ENV_FILE) -> Optional[str]:
    """
    Erstellt ein Backup einer Konfigurationsdatei.
    
    Args:
        file_path: Pfad zur Konfigurationsdatei
        
    Returns:
        Optional[str]: Pfad zur Backup-Datei oder None, wenn ein Fehler aufgetreten ist
    """
    if not os.path.isfile(file_path):
        logging.error(f"Datei nicht gefunden: {file_path}")
        return None
    
    # Backup-Dateinamen mit Zeitstempel erstellen
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    
    try:
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception as e:
        logging.error(f"Fehler beim Erstellen des Backups: {str(e)}")
        return None


# Konfiguration anzeigen
def show_config() -> None:
    """Zeigt die aktuelle Konfiguration an."""
    if os.path.isfile(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            print(f.read())
    else:
        logging.error(f"Konfigurationsdatei nicht gefunden: {ENV_FILE}")


# Konfiguration bearbeiten
def edit_config() -> None:
    """Öffnet die Konfigurationsdatei im Standardeditor."""
    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, ENV_FILE])


# Konfiguration initialisieren
init_config()

logging.debug("Konfigurationsmodul initialisiert")