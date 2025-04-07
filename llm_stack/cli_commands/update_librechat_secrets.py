"""
Aktualisiert LibreChat-Secrets aus der Hauptkonfiguration.

Dieses Modul stellt Funktionen zum Aktualisieren der LibreChat-Secrets aus der Hauptkonfiguration bereit.
"""

import argparse
import os
import re
import sys
from typing import Optional

from llm_stack.cli_commands import register_command
from llm_stack.core import config, error, logging, secrets, system


@register_command("update-librechat-secrets")
def update_librechat_secrets(args: Optional[argparse.Namespace] = None) -> int:
    """
    Aktualisiert LibreChat-Secrets aus der Hauptkonfiguration.

    Args:
        args: Argumente für den Befehl

    Returns:
        int: Exit-Code (0 bei Erfolg, 1 bei Fehler)
    """
    logging.info("Prüfe LibreChat-Secrets...")

    # Prüfen, ob config/.env existiert
    if not os.path.isfile(config.ENV_FILE):
        error.handle_error(
            error.ERR_FILE_NOT_FOUND, "Hauptkonfigurationsdatei nicht gefunden"
        )
        return 1

    # Prüfen, ob config/librechat/.env existiert
    librechat_env = os.path.join(config.CONFIG_DIR, "librechat", ".env")
    if not os.path.isfile(librechat_env):
        error.handle_error(
            error.ERR_FILE_NOT_FOUND, "LibreChat-Konfigurationsdatei nicht gefunden"
        )
        return 1

    # Secrets aus der Hauptkonfiguration abrufen
    jwt_secret = config.get_config("JWT_SECRET")
    jwt_refresh_secret = config.get_config("JWT_REFRESH_SECRET")

    # Secrets aus der LibreChat-Konfiguration abrufen
    librechat_jwt_secret = ""
    librechat_jwt_refresh_secret = ""

    try:
        with open(librechat_env) as f:
            for line in f:
                if line.startswith("JWT_SECRET="):
                    librechat_jwt_secret = line.split("=", 1)[1].strip()
                elif line.startswith("JWT_REFRESH_SECRET="):
                    librechat_jwt_refresh_secret = line.split("=", 1)[1].strip()
    except Exception as e:
        error.handle_error(
            error.ERR_FILE_NOT_FOUND,
            f"Fehler beim Lesen der LibreChat-Konfigurationsdatei: {str(e)}",
        )
        return 1

    # Debug-Ausgabe
    logging.debug(f"Haupt-JWT_SECRET: '{jwt_secret}'")
    logging.debug(f"LibreChat-JWT_SECRET: '{librechat_jwt_secret}'")

    # Prüfen, ob LibreChat-Secrets aktualisiert werden müssen
    if not librechat_jwt_secret or not librechat_jwt_refresh_secret:
        logging.warn(
            "LibreChat JWT-Secrets sind nicht gesetzt. Aktualisiere aus der Hauptkonfiguration..."
        )

        # Backup der LibreChat .env-Datei erstellen
        librechat_backup = system.backup_file(librechat_env)
        if librechat_backup:
            logging.info(f"Backup erstellt: {librechat_backup}")

        # LibreChat-Konfiguration aktualisieren
        if not secrets.update_librechat_config():
            error.handle_error(
                error.ERR_GENERAL,
                "Fehler beim Aktualisieren der LibreChat-Konfiguration mit Secrets",
            )
            return 1

        # Aktualisierung überprüfen
        try:
            updated_jwt_secret = ""
            with open(librechat_env) as f:
                for line in f:
                    if line.startswith("JWT_SECRET="):
                        updated_jwt_secret = line.split("=", 1)[1].strip()
                        break

            logging.debug(f"Aktualisiertes JWT_SECRET: {updated_jwt_secret}")
        except Exception as e:
            logging.warn(f"Konnte aktualisiertes JWT_SECRET nicht überprüfen: {str(e)}")

        logging.success("LibreChat JWT-Secrets aktualisiert.")
    else:
        logging.success("LibreChat JWT-Secrets sind bereits gesetzt.")

    return 0


def setup_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    Richtet den Parser für den update-librechat-secrets-Befehl ein.

    Args:
        subparsers: Subparser-Aktion, zu der der Parser hinzugefügt werden soll
    """
    parser = subparsers.add_parser(
        "update-librechat-secrets",
        help="Aktualisiert LibreChat-Secrets aus der Hauptkonfiguration",
        description="Aktualisiert die JWT-Secrets in der LibreChat-Konfiguration aus der Hauptkonfiguration",
    )


def main() -> int:
    """
    Hauptfunktion für die direkte Ausführung des Skripts.

    Returns:
        int: Exit-Code (0 bei Erfolg, 1 bei Fehler)
    """
    return update_librechat_secrets()


if __name__ == "__main__":
    sys.exit(main())
