"""
Generiert sichere Secrets für den LLM Stack.

Dieses Modul stellt Funktionen zum Generieren sicherer Secrets für den LLM Stack bereit.
"""

import argparse
import os
import sys
from typing import Dict, List, Optional, Tuple

from llm_stack.cli_commands import register_command
from llm_stack.core import config, error, logging, secrets, system


@register_command("generate-secrets")
def generate_secrets(args: Optional[argparse.Namespace] = None) -> int:
    """
    Generiert sichere Secrets für den LLM Stack.

    Args:
        args: Argumente für den Befehl

    Returns:
        int: Exit-Code (0 bei Erfolg, 1 bei Fehler)
    """
    logging.info("Generiere sichere Secrets...")

    # Alle erforderlichen Secrets generieren
    if not secrets.generate_all_secrets():
        error.handle_error(error.ERR_GENERAL, "Fehler beim Generieren der Secrets")
        return 1

    # Generierte Secrets für die .env-Datei abrufen
    admin_password = secrets.get_secret("ADMIN_PASSWORD")
    grafana_admin_password = secrets.get_secret("GRAFANA_ADMIN_PASSWORD")
    jwt_secret = secrets.get_secret("JWT_SECRET")
    jwt_refresh_secret = secrets.get_secret("JWT_REFRESH_SECRET")
    session_secret = secrets.get_secret("SESSION_SECRET")
    crypt_secret = secrets.get_secret("CRYPT_SECRET")
    creds_key = secrets.get_secret("CREDS_KEY")
    creds_iv = secrets.get_secret("CREDS_IV")

    # Backup erstellen, wenn die Datei existiert
    backup_file = None
    if os.path.isfile(config.ENV_FILE):
        backup_file = system.backup_file(config.ENV_FILE)
        if backup_file:
            logging.success(f"Backup erstellt: {backup_file}")
        else:
            logging.warn("Konnte kein Backup erstellen")
            backup_file = "Kein Backup erstellt"
    else:
        logging.warn("Keine existierende Konfigurationsdatei zum Sichern")
        backup_file = "Kein Backup benötigt"

    # .env-Datei mit den Secrets erstellen
    env_content = """# LOCAL-LLM-Stack Konfiguration

# Komponentenversionen
OLLAMA_VERSION=0.1.27
MONGODB_VERSION=6.0.6
MEILISEARCH_VERSION=latest
LIBRECHAT_VERSION=latest
TRAEFIK_VERSION=v2.10.4
NGINX_VERSION=1.25.3
PROMETHEUS_VERSION=v2.45.0
GRAFANA_VERSION=10.0.3

# Port-Konfiguration
HOST_PORT_OLLAMA=11434
HOST_PORT_LIBRECHAT=3080
HOST_PORT_LOAD_BALANCER=8080
HOST_PORT_PROMETHEUS=9090
HOST_PORT_GRAFANA=3000

# Ressourcenbeschränkungen
OLLAMA_CPU_LIMIT=0.75
OLLAMA_MEMORY_LIMIT=16G
MONGODB_MEMORY_LIMIT=2G
MEILISEARCH_MEMORY_LIMIT=1G
LIBRECHAT_CPU_LIMIT=0.50
LIBRECHAT_MEMORY_LIMIT=4G

# Standardmodelle
DEFAULT_MODELS=tinyllama

# Sicherheitseinstellungen
ADMIN_PASSWORD={admin_password}
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD={grafana_admin_password}
JWT_SECRET={jwt_secret}
JWT_REFRESH_SECRET={jwt_refresh_secret}
SESSION_SECRET={session_secret}
CRYPT_SECRET={crypt_secret}
CREDS_KEY={creds_key}
CREDS_IV={creds_iv}

# Authentifizierungseinstellungen
ENABLE_AUTH=true
ALLOW_SOCIAL_LOGIN=false
ALLOW_REGISTRATION=true
ADMIN_EMAIL=admin@local.host
""".format(
        admin_password=admin_password,
        grafana_admin_password=grafana_admin_password,
        jwt_secret=jwt_secret,
        jwt_refresh_secret=jwt_refresh_secret,
        session_secret=session_secret,
        crypt_secret=crypt_secret,
        creds_key=creds_key,
        creds_iv=creds_iv,
    )

    try:
        # Sicherstellen, dass das Konfigurationsverzeichnis existiert
        os.makedirs(os.path.dirname(config.ENV_FILE), exist_ok=True)

        # .env-Datei schreiben
        with open(config.ENV_FILE, "w") as f:
            f.write(env_content)

        logging.success(
            f"Sichere Secrets generiert und in {config.ENV_FILE} gespeichert"
        )

        # Alle Konfigurationsdateien mit den neuen Secrets aktualisieren
        if not secrets.update_all_configs():
            error.handle_error(
                error.ERR_GENERAL,
                "Fehler beim Aktualisieren der Konfigurationsdateien mit Secrets",
            )
            return 1

        logging.success(
            "Alle Konfigurationsdateien mit den neuen Secrets aktualisiert."
        )

        logging.warn(
            f"WICHTIG: Bewahren Sie Ihre Secrets sicher auf! Sie sind in {secrets.SECRETS_FILE} gespeichert"
        )
        logging.warn(f"LibreChat Admin-Passwort: {admin_password}")
        logging.warn(f"Grafana Admin-Passwort: {grafana_admin_password}")

        if backup_file not in ["Kein Backup benötigt", "Kein Backup erstellt"]:
            logging.warn(
                "Wenn Sie die ursprüngliche Konfiguration wiederherstellen möchten, verwenden Sie:"
            )
            logging.warn(f"cp {backup_file} {config.ENV_FILE}")

        logging.info(
            f"Um Ihr Admin-Passwort anzuzeigen, führen Sie aus: grep ADMIN_PASSWORD {secrets.SECRETS_FILE}"
        )

        return 0
    except Exception as e:
        error.handle_error(
            error.ERR_CONFIG_ERROR,
            f"Fehler beim Schreiben der Konfigurationsdatei: {str(e)}",
        )
        return 1


def setup_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    Richtet den Parser für den generate-secrets-Befehl ein.

    Args:
        subparsers: Subparser-Aktion, zu der der Parser hinzugefügt werden soll
    """
    parser = subparsers.add_parser(
        "generate-secrets",
        help="Generiert sichere Secrets für den LLM Stack",
        description="Generiert sichere Secrets für den LLM Stack und aktualisiert alle Konfigurationsdateien",
    )


def main() -> int:
    """
    Hauptfunktion für die direkte Ausführung des Skripts.

    Returns:
        int: Exit-Code (0 bei Erfolg, 1 bei Fehler)
    """
    return generate_secrets()


if __name__ == "__main__":
    sys.exit(main())
