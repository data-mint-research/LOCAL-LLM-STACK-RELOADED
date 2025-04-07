"""
Secrets Management for the LLM Stack.

This module provides functions for generating, storing, and managing secrets.
"""

import os
import re
import secrets
import string
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import yaml

from llm_stack.core import config, error, logging, system, validation

# Default path for the secrets file
SECRETS_FILE = os.path.join(config.CONFIG_DIR, ".secrets")


def init_secrets() -> bool:
    """
    Initializes the secrets management.

    Returns:
        bool: True if initialization was successful, False otherwise
    """
    logging.debug("Initializing secrets management")

    # Ensure that the configuration directory exists
    if not system.ensure_directory(config.CONFIG_DIR):
        logging.error("Error creating configuration directory")
        return False

    # Create secrets file if it doesn't exist
    if not os.path.isfile(SECRETS_FILE):
        logging.debug(f"Creating secrets file: {SECRETS_FILE}")
        try:
            # Create file
            with open(SECRETS_FILE, "w") as f:
                pass

            # Set secure permissions (only for Unix systems)
            if os.name == "posix":
                os.chmod(SECRETS_FILE, 0o600)
        except (OSError, PermissionError) as e:
            logging.error(f"Error creating secrets file: {str(e)}")
            return False

    return True


def get_secret(key: str, default_value: str = "") -> str:
    """
    Retrieves a secret from the secrets file.

    Args:
        key: Key of the secret
        default_value: Default value if the secret is not found

    Returns:
        str: Value of the secret or default value
    """
    logging.debug(f"Retrieving secret: {key}")

    # Check if the secrets file exists
    if not os.path.isfile(SECRETS_FILE):
        logging.warn(f"Secrets file not found: {SECRETS_FILE}")
        return default_value

    try:
        # Retrieve value from the secrets file
        with open(SECRETS_FILE) as f:
            for line in f:
                # Search for line matching the pattern "key=value"
                match = re.match(f"^{re.escape(key)}=(.*)$", line.strip())
                if match:
                    return match.group(1)

        # Secret not found
        return default_value
    except OSError as e:
        logging.error(f"Error reading secrets file: {str(e)}")
        return default_value


def set_secret(key: str, value: str) -> bool:
    """
    Sets a secret in the secrets file.

    Args:
        key: Key of the secret
        value: Value of the secret

    Returns:
        bool: True if the secret was successfully set, False otherwise
    """
    logging.debug(f"Setting secret: {key}")

    # Check if the secrets file exists
    if not os.path.isfile(SECRETS_FILE):
        if not init_secrets():
            return False

    try:
        # Read current secrets
        current_secrets = {}
        if os.path.isfile(SECRETS_FILE) and os.path.getsize(SECRETS_FILE) > 0:
            with open(SECRETS_FILE) as f:
                for line in f:
                    if "=" in line:
                        k, v = line.strip().split("=", 1)
                        current_secrets[k] = v

        # Update secret
        current_secrets[key] = value

        # Write secrets back
        with open(SECRETS_FILE, "w") as f:
            for k, v in current_secrets.items():
                f.write(f"{k}={v}\n")

        return True
    except OSError as e:
        logging.error(f"Error writing secrets file: {str(e)}")
        return False


def generate_random_string(length: int = 32) -> str:
    """
    Generates a random string.

    Args:
        length: Length of the string

    Returns:
        str: Random string
    """
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def generate_hex_string(length: int = 32) -> str:
    """
    Generates a random hex string.

    Args:
        length: Length of the string

    Returns:
        str: Random hex string
    """
    return secrets.token_hex(length // 2)


def generate_password(length: int = 16) -> str:
    """
    Generates a secure password.

    Args:
        length: Length of the password

    Returns:
        str: Secure password
    """
    # Character sets for different character types
    uppercase_chars = string.ascii_uppercase
    lowercase_chars = string.ascii_lowercase
    digit_chars = string.digits
    special_chars = "!@#$%^&*()-_=+[]{}|;:,.<>?"

    # Ensure the password contains at least one character of each type
    password = [
        secrets.choice(uppercase_chars),
        secrets.choice(lowercase_chars),
        secrets.choice(digit_chars),
        secrets.choice(special_chars),
    ]

    # Randomly select remaining characters
    all_chars = uppercase_chars + lowercase_chars + digit_chars + special_chars
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))

    # Shuffle password
    secrets.SystemRandom().shuffle(password)

    return "".join(password)


def generate_secret(key: str, length: int = 32, secret_type: str = "random") -> bool:
    """
    Generiert ein neues Secret.

    Args:
        key: Schlüssel des Secrets
        length: Länge des Secrets
        secret_type: Typ des Secrets (random, hex, password)

    Returns:
        bool: True, wenn das Secret erfolgreich generiert wurde, sonst False
    """
    logging.debug(f"Generiere Secret: {key} (Länge: {length}, Typ: {secret_type})")

    # Secret-Wert generieren
    value = ""
    if secret_type == "random":
        value = generate_random_string(length)
    elif secret_type == "hex":
        value = generate_hex_string(length)
    elif secret_type == "password":
        value = generate_password(length)
    else:
        logging.error(f"Unbekannter Secret-Typ: {secret_type}")
        return False

    # Secret setzen
    return set_secret(key, value)


def generate_all_secrets() -> bool:
    """
    Generiert alle erforderlichen Secrets.

    Returns:
        bool: True, wenn alle Secrets erfolgreich generiert wurden, sonst False
    """
    logging.info("Generiere alle erforderlichen Secrets")

    # Secrets-Verwaltung initialisieren
    if not init_secrets():
        return False

    # Admin-Passwörter generieren
    if not generate_secret("ADMIN_PASSWORD", 16, "password"):
        return False
    if not generate_secret("GRAFANA_ADMIN_PASSWORD", 16, "password"):
        return False

    # JWT-Secrets generieren
    if not generate_secret("JWT_SECRET", 64, "random"):
        return False
    if not generate_secret("JWT_REFRESH_SECRET", 64, "random"):
        return False

    # Session- und Verschlüsselungs-Secrets generieren
    if not generate_secret("SESSION_SECRET", 64, "random"):
        return False
    if not generate_secret("CRYPT_SECRET", 64, "random"):
        return False
    if not generate_secret("CREDS_KEY", 64, "hex"):
        return False
    if not generate_secret("CREDS_IV", 32, "hex"):
        return False

    # Meilisearch-Master-Key generieren
    if not generate_secret("MEILI_MASTER_KEY", 32, "random"):
        return False

    # Traefik Basic Auth generieren
    admin_password = get_secret("ADMIN_PASSWORD")
    try:
        # htpasswd verwenden, wenn verfügbar
        if system.command_exists("htpasswd"):
            result, stdout, stderr = system.execute_command(
                f"htpasswd -nb admin {admin_password}"
            )
            if result == 0:
                hashed_password = stdout.strip()
                if not set_secret("TRAEFIK_BASIC_AUTH", hashed_password):
                    return False
            else:
                logging.warn(f"Fehler bei der Ausführung von htpasswd: {stderr}")
                if not set_secret("TRAEFIK_BASIC_AUTH", f"admin:{admin_password}"):
                    return False
        else:
            # Fallback, wenn htpasswd nicht verfügbar ist
            if not set_secret("TRAEFIK_BASIC_AUTH", f"admin:{admin_password}"):
                return False
    except Exception as e:
        logging.error(f"Fehler beim Generieren des Traefik Basic Auth: {str(e)}")
        return False

    logging.success("Alle Secrets erfolgreich generiert")
    return True


def update_env_with_secrets(env_file: Optional[str] = None) -> bool:
    """
    Aktualisiert eine Umgebungsdatei mit Secrets.

    Args:
        env_file: Pfad zur Umgebungsdatei

    Returns:
        bool: True, wenn die Umgebungsdatei erfolgreich aktualisiert wurde, sonst False
    """
    if env_file is None:
        env_file = config.ENV_FILE

    logging.info(f"Aktualisiere Umgebungsdatei mit Secrets: {env_file}")

    # Prüfen, ob die Umgebungsdatei existiert
    if not os.path.isfile(env_file):
        logging.error(f"Umgebungsdatei nicht gefunden: {env_file}")
        return False

    # Backup der Umgebungsdatei erstellen
    backup_file = system.backup_file(env_file)
    if backup_file is None:
        logging.warn("Konnte kein Backup der Umgebungsdatei erstellen")
    else:
        logging.info(f"Backup erstellt: {backup_file}")

    # Secrets abrufen
    admin_password = get_secret("ADMIN_PASSWORD")
    grafana_admin_password = get_secret("GRAFANA_ADMIN_PASSWORD")
    jwt_secret = get_secret("JWT_SECRET")
    jwt_refresh_secret = get_secret("JWT_REFRESH_SECRET")
    session_secret = get_secret("SESSION_SECRET")
    crypt_secret = get_secret("CRYPT_SECRET")
    creds_key = get_secret("CREDS_KEY")
    creds_iv = get_secret("CREDS_IV")

    # Umgebungsvariablen aktualisieren
    variables = {
        "ADMIN_PASSWORD": admin_password,
        "GRAFANA_ADMIN_USER": "admin",
        "GRAFANA_ADMIN_PASSWORD": grafana_admin_password,
        "JWT_SECRET": jwt_secret,
        "JWT_REFRESH_SECRET": jwt_refresh_secret,
        "SESSION_SECRET": session_secret,
        "CRYPT_SECRET": crypt_secret,
        "CREDS_KEY": creds_key,
        "CREDS_IV": creds_iv,
        "ENABLE_AUTH": "true",
    }

    try:
        # Aktuelle Umgebungsvariablen lesen
        current_vars = {}
        if os.path.isfile(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        current_vars[key] = value

        # Umgebungsvariablen aktualisieren
        for key, value in variables.items():
            current_vars[key] = value

        # Umgebungsdatei schreiben
        with open(env_file, "w") as f:
            for key, value in current_vars.items():
                f.write(f"{key}={value}\n")

        logging.success(f"Umgebungsdatei aktualisiert mit Secrets: {env_file}")
        return True
    except OSError as e:
        logging.error(f"Fehler beim Aktualisieren der Umgebungsdatei: {str(e)}")
        return False


def update_librechat_config() -> bool:
    """
    Aktualisiert die LibreChat-Konfiguration mit Secrets.

    Returns:
        bool: True, wenn die Konfiguration erfolgreich aktualisiert wurde, sonst False
    """
    librechat_env = os.path.join(config.CONFIG_DIR, "librechat", ".env")
    librechat_yaml = os.path.join(config.CONFIG_DIR, "librechat", "librechat.yaml")

    logging.info("Aktualisiere LibreChat-Konfiguration mit Secrets")

    # LibreChat .env-Datei aktualisieren, wenn sie existiert
    if os.path.isfile(librechat_env):
        logging.info(f"Aktualisiere LibreChat-Umgebungsdatei: {librechat_env}")

        # Backup der LibreChat .env-Datei erstellen
        backup_file = system.backup_file(librechat_env)
        if backup_file is None:
            logging.warn("Konnte kein Backup der LibreChat-Umgebungsdatei erstellen")
        else:
            logging.info(f"Backup erstellt: {backup_file}")

        # JWT-Secrets abrufen
        jwt_secret = get_secret("JWT_SECRET")
        jwt_refresh_secret = get_secret("JWT_REFRESH_SECRET")

        try:
            # Aktuelle Umgebungsvariablen lesen
            current_vars = {}
            with open(librechat_env) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        current_vars[key] = value

            # JWT-Secrets aktualisieren
            current_vars["JWT_SECRET"] = jwt_secret
            current_vars["JWT_REFRESH_SECRET"] = jwt_refresh_secret

            # Umgebungsdatei schreiben
            with open(librechat_env, "w") as f:
                for key, value in current_vars.items():
                    f.write(f"{key}={value}\n")

            logging.success("LibreChat-Umgebungsdatei aktualisiert mit Secrets")
        except OSError as e:
            logging.error(
                f"Fehler beim Aktualisieren der LibreChat-Umgebungsdatei: {str(e)}"
            )
            return False

    # LibreChat YAML-Datei aktualisieren, wenn sie existiert
    if os.path.isfile(librechat_yaml):
        logging.info(f"Aktualisiere LibreChat-YAML-Datei: {librechat_yaml}")

        # Backup der LibreChat YAML-Datei erstellen
        backup_file = system.backup_file(librechat_yaml)
        if backup_file is None:
            logging.warn("Konnte kein Backup der LibreChat-YAML-Datei erstellen")
        else:
            logging.info(f"Backup erstellt: {backup_file}")

        # Neuen API-Schlüssel für Ollama generieren
        ollama_api_key = generate_random_string(32)

        try:
            # YAML-Datei lesen
            with open(librechat_yaml) as f:
                yaml_data = yaml.safe_load(f)

            # API-Schlüssel aktualisieren
            if (
                yaml_data
                and "endpoints" in yaml_data
                and "custom" in yaml_data["endpoints"]
                and len(yaml_data["endpoints"]["custom"]) > 0
            ):
                yaml_data["endpoints"]["custom"][0]["apiKey"] = ollama_api_key

            # YAML-Datei schreiben
            with open(librechat_yaml, "w") as f:
                yaml.dump(yaml_data, f)

            logging.success("LibreChat-YAML-Datei aktualisiert mit Secrets")
        except (OSError, yaml.YAMLError) as e:
            logging.error(
                f"Fehler beim Aktualisieren der LibreChat-YAML-Datei: {str(e)}"
            )
            return False

    return True


def update_meilisearch_config() -> bool:
    """
    Aktualisiert die Meilisearch-Konfiguration mit Secrets.

    Returns:
        bool: True, wenn die Konfiguration erfolgreich aktualisiert wurde, sonst False
    """
    meilisearch_yml = "core/meilisearch.yml"

    logging.info("Aktualisiere Meilisearch-Konfiguration mit Secrets")

    # Prüfen, ob die Meilisearch-YAML-Datei existiert
    if not os.path.isfile(meilisearch_yml):
        logging.error(f"Meilisearch-YAML-Datei nicht gefunden: {meilisearch_yml}")
        return False

    # Backup der Meilisearch-YAML-Datei erstellen
    backup_file = system.backup_file(meilisearch_yml)
    if backup_file is None:
        logging.warn("Konnte kein Backup der Meilisearch-YAML-Datei erstellen")
    else:
        logging.info(f"Backup erstellt: {backup_file}")

    # Meilisearch-Master-Key abrufen
    meili_master_key = get_secret("MEILI_MASTER_KEY")

    try:
        # YAML-Datei lesen
        with open(meilisearch_yml) as f:
            yaml_data = yaml.safe_load(f)

        # Master-Key aktualisieren
        if (
            yaml_data
            and "services" in yaml_data
            and "meilisearch" in yaml_data["services"]
            and "environment" in yaml_data["services"]["meilisearch"]
        ):
            # Umgebungsvariablen durchsuchen und aktualisieren
            env_vars = yaml_data["services"]["meilisearch"]["environment"]
            for i, var in enumerate(env_vars):
                if var.startswith("MEILI_MASTER_KEY="):
                    env_vars[i] = f"MEILI_MASTER_KEY={meili_master_key}"
                    break
            else:
                # Wenn nicht gefunden, hinzufügen
                env_vars.append(f"MEILI_MASTER_KEY={meili_master_key}")

        # YAML-Datei schreiben
        with open(meilisearch_yml, "w") as f:
            yaml.dump(yaml_data, f)

        logging.success("Meilisearch-YAML-Datei aktualisiert mit Secrets")
        return True
    except (OSError, yaml.YAMLError) as e:
        logging.error(f"Fehler beim Aktualisieren der Meilisearch-YAML-Datei: {str(e)}")
        return False


def update_traefik_config() -> bool:
    """
    Aktualisiert die Traefik-Konfiguration mit Secrets.

    Returns:
        bool: True, wenn die Konfiguration erfolgreich aktualisiert wurde, sonst False
    """
    traefik_yml = "modules/security/config/traefik/traefik.yml"
    services_yml = "modules/security/config/traefik/dynamic/services.yml"

    logging.info("Aktualisiere Traefik-Konfiguration mit Secrets")

    # Traefik-Hauptkonfiguration aktualisieren, wenn sie existiert
    if os.path.isfile(traefik_yml):
        logging.info(f"Aktualisiere Traefik-Hauptkonfiguration: {traefik_yml}")

        # Backup der Traefik-YAML-Datei erstellen
        backup_file = system.backup_file(traefik_yml)
        if backup_file is None:
            logging.warn("Konnte kein Backup der Traefik-YAML-Datei erstellen")
        else:
            logging.info(f"Backup erstellt: {backup_file}")

        try:
            # YAML-Datei lesen
            with open(traefik_yml) as f:
                yaml_data = yaml.safe_load(f)

            # Insecure-Einstellung auf False setzen
            if yaml_data and "api" in yaml_data:
                yaml_data["api"]["insecure"] = False

            # E-Mail-Adresse aktualisieren
            admin_email = config.get_config("ADMIN_EMAIL", "admin@local.host")
            if (
                yaml_data
                and "certificatesResolvers" in yaml_data
                and "default" in yaml_data["certificatesResolvers"]
                and "acme" in yaml_data["certificatesResolvers"]["default"]
            ):
                yaml_data["certificatesResolvers"]["default"]["acme"][
                    "email"
                ] = admin_email

            # TLS für websecure-Einstiegspunkt aktivieren
            if (
                yaml_data
                and "entryPoints" in yaml_data
                and "websecure" in yaml_data["entryPoints"]
                and "http" in yaml_data["entryPoints"]["websecure"]
            ):
                yaml_data["entryPoints"]["websecure"]["http"]["tls"] = {}

            # YAML-Datei schreiben
            with open(traefik_yml, "w") as f:
                yaml.dump(yaml_data, f)

            logging.success("Traefik-Hauptkonfiguration aktualisiert")
        except (OSError, yaml.YAMLError) as e:
            logging.error(
                f"Fehler beim Aktualisieren der Traefik-Hauptkonfiguration: {str(e)}"
            )
            return False

    # Traefik-Dynamische-Konfiguration aktualisieren, wenn sie existiert
    if os.path.isfile(services_yml):
        logging.info(f"Aktualisiere Traefik-Dynamische-Konfiguration: {services_yml}")

        # Backup der Traefik-Services-YAML-Datei erstellen
        backup_file = system.backup_file(services_yml)
        if backup_file is None:
            logging.warn("Konnte kein Backup der Traefik-Services-YAML-Datei erstellen")
        else:
            logging.info(f"Backup erstellt: {backup_file}")

        # Traefik Basic Auth abrufen
        traefik_basic_auth = get_secret("TRAEFIK_BASIC_AUTH")

        try:
            # YAML-Datei lesen
            with open(services_yml) as f:
                yaml_data = yaml.safe_load(f)

            # Basic Auth-Anmeldedaten aktualisieren
            if yaml_data and "http" in yaml_data and "middlewares" in yaml_data["http"]:
                middlewares = yaml_data["http"]["middlewares"]

                # Ollama-Auth aktualisieren
                if (
                    "ollama-auth" in middlewares
                    and "basicAuth" in middlewares["ollama-auth"]
                    and "users" in middlewares["ollama-auth"]["basicAuth"]
                ):
                    middlewares["ollama-auth"]["basicAuth"]["users"] = [
                        traefik_basic_auth
                    ]

                # Traefik-Auth aktualisieren
                if (
                    "traefik-auth" in middlewares
                    and "basicAuth" in middlewares["traefik-auth"]
                    and "users" in middlewares["traefik-auth"]["basicAuth"]
                ):
                    middlewares["traefik-auth"]["basicAuth"]["users"] = [
                        traefik_basic_auth
                    ]

            # TLS für alle Router aktivieren
            if yaml_data and "http" in yaml_data and "routers" in yaml_data["http"]:
                routers = yaml_data["http"]["routers"]

                # LibreChat-Router aktualisieren
                if "librechat" in routers:
                    routers["librechat"]["tls"] = {}

                # Ollama-Router aktualisieren
                if "ollama" in routers:
                    routers["ollama"]["tls"] = {}

                # Traefik-Dashboard-Router aktualisieren
                if "traefik-dashboard" in routers:
                    routers["traefik-dashboard"]["tls"] = {}

            # YAML-Datei schreiben
            with open(services_yml, "w") as f:
                yaml.dump(yaml_data, f)

            logging.success("Traefik-Dynamische-Konfiguration aktualisiert")
        except (OSError, yaml.YAMLError) as e:
            logging.error(
                f"Fehler beim Aktualisieren der Traefik-Dynamischen-Konfiguration: {str(e)}"
            )
            return False

    return True


def update_research_env() -> bool:
    """
    Aktualisiert die Research-Umgebungsdatei mit sicheren Standardwerten.

    Returns:
        bool: True, wenn die Umgebungsdatei erfolgreich aktualisiert wurde, sonst False
    """
    research_env = os.path.join(config.CONFIG_DIR, "research.env")

    logging.info("Aktualisiere Research-Umgebungsdatei mit sicheren Standardwerten")

    # Prüfen, ob die Research-Umgebungsdatei existiert
    if not os.path.isfile(research_env):
        logging.warn(f"Research-Umgebungsdatei nicht gefunden: {research_env}")
        return False

    # Backup der Research-Umgebungsdatei erstellen
    backup_file = system.backup_file(research_env)
    if backup_file is None:
        logging.warn("Konnte kein Backup der Research-Umgebungsdatei erstellen")
    else:
        logging.info(f"Backup erstellt: {backup_file}")

    try:
        # Datei lesen
        with open(research_env) as f:
            content = f.read()

        # ENABLE_AUTH-Einstellung auf true setzen
        content = re.sub(r"ENABLE_AUTH=false", "ENABLE_AUTH=true", content)

        # Datei schreiben
        with open(research_env, "w") as f:
            f.write(content)

        logging.success(
            "Research-Umgebungsdatei aktualisiert mit sicheren Standardwerten"
        )
        return True
    except OSError as e:
        logging.error(
            f"Fehler beim Aktualisieren der Research-Umgebungsdatei: {str(e)}"
        )
        return False


def update_all_configs() -> bool:
    """
    Aktualisiert alle Konfigurationsdateien mit Secrets.

    Returns:
        bool: True, wenn alle Konfigurationsdateien erfolgreich aktualisiert wurden, sonst False
    """
    logging.info("Aktualisiere alle Konfigurationsdateien mit Secrets")

    # Alle erforderlichen Secrets generieren, wenn sie nicht existieren
    if not generate_all_secrets():
        logging.error("Fehler beim Generieren der Secrets")
        return False

    # Haupt-Umgebungsdatei aktualisieren
    if not update_env_with_secrets():
        logging.error("Fehler beim Aktualisieren der Haupt-Umgebungsdatei")
        return False

    # LibreChat-Konfiguration aktualisieren
    if not update_librechat_config():
        logging.error("Fehler beim Aktualisieren der LibreChat-Konfiguration")
        return False

    # Meilisearch-Konfiguration aktualisieren
    if not update_meilisearch_config():
        logging.error("Fehler beim Aktualisieren der Meilisearch-Konfiguration")
        return False

    # Traefik-Konfiguration aktualisieren
    if not update_traefik_config():
        logging.error("Fehler beim Aktualisieren der Traefik-Konfiguration")
        return False

    # Research-Umgebungsdatei aktualisieren
    if not update_research_env():
        logging.warn("Fehler beim Aktualisieren der Research-Umgebungsdatei")

    logging.success("Alle Konfigurationsdateien aktualisiert mit Secrets")
    return True


# Secrets-Verwaltung initialisieren
init_secrets()

logging.debug("Secrets-Management-Modul initialisiert")
