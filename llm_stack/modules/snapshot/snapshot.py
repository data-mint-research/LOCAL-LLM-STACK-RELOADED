"""
Snapshot-Funktionalität für den LLM Stack.

Dieses Modul stellt Funktionen zum Erstellen von Snapshots des LLM Stacks bereit.
"""

import datetime
import os
import shutil
import subprocess
import tarfile
from pathlib import Path
from typing import List, Optional, Tuple, Union

import psutil

from llm_stack.core import error, logging, system


def create_snapshot(
    source_dir: Optional[str] = None, exclude_dirs: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """
    Erstellt einen Snapshot des LLM Stacks.

    Args:
        source_dir: Quellverzeichnis (optional, Standard: Projektverzeichnis)
        exclude_dirs: Liste von Verzeichnissen, die ausgeschlossen werden sollen (optional)

    Returns:
        Tuple[bool, str]: (Erfolg, Pfad zur Archivdatei oder Fehlermeldung)
    """
    # Aktuelles Datum im Format YYYY-MM-DD
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # Quell- und Zielverzeichnisse/Dateien definieren
    if source_dir is None:
        source_dir = system.get_project_root()

    snapshots_dir = os.path.join(source_dir, "data", "snapshots")
    archive_file = os.path.join(snapshots_dir, f"snapshot-{current_date}.tar.gz")

    # Standardmäßig auszuschließende Verzeichnisse
    if exclude_dirs is None:
        exclude_dirs = [
            "./data/snapshots",  # Snapshots-Verzeichnis selbst ausschließen, um Rekursion zu vermeiden
            "./data/models",  # Große Modelldateien ausschließen, die neu heruntergeladen werden können
        ]

    # Snapshots-Verzeichnis erstellen, falls es nicht existiert
    logging.info(f"Erstelle Snapshots-Verzeichnis: {snapshots_dir}")
    if not system.ensure_directory(snapshots_dir):
        return (
            False,
            f"Fehler: Konnte Snapshots-Verzeichnis nicht erstellen: {snapshots_dir}",
        )

    # Prüfen, ob genügend Speicherplatz vorhanden ist (mindestens 1 GB)
    disk_usage = system.get_disk_usage(source_dir)
    free_space_gb = disk_usage["free"] / (1024**3)

    if free_space_gb < 1:
        return (
            False,
            f"Fehler: Nicht genügend Speicherplatz. Mindestens 1 GB freier Speicherplatz erforderlich.",
        )

    # Prüfen, ob sudo benötigt wird (wenn wir nicht Eigentümer einiger Dateien sind)
    need_sudo = _need_sudo(source_dir)

    # Archiv erstellen
    logging.info("Erstelle Snapshot-Archiv des LLM Stacks...")

    try:
        if need_sudo:
            logging.warn("Dies erfordert möglicherweise Ihr sudo-Passwort...")

            # Ausschlussoptionen für tar erstellen
            exclude_opts = " ".join([f"--exclude={dir}" for dir in exclude_dirs])

            # Archiv mit sudo erstellen
            cmd = f"sudo tar -czf {archive_file} {exclude_opts} -C {source_dir} ."
            result, stdout, stderr = system.execute_command(cmd)

            if result != 0:
                return False, f"Fehler beim Erstellen des Snapshot-Archivs: {stderr}"

            # Eigentümerschaft des Archivs ändern
            cmd = f"sudo chown $(whoami):$(whoami) {archive_file}"
            result, stdout, stderr = system.execute_command(cmd)

            if result != 0:
                return (
                    False,
                    f"Fehler beim Ändern der Eigentümerschaft des Snapshot-Archivs: {stderr}",
                )
        else:
            # Archiv ohne sudo erstellen
            with tarfile.open(archive_file, "w:gz") as tar:
                # Zum Quellverzeichnis wechseln
                original_dir = os.getcwd()
                os.chdir(source_dir)

                try:
                    # Alle Dateien und Verzeichnisse hinzufügen, außer den ausgeschlossenen
                    for root, dirs, files in os.walk(".", topdown=True):
                        # Ausgeschlossene Verzeichnisse überspringen
                        dirs[:] = [
                            d for d in dirs if os.path.join(root, d) not in exclude_dirs
                        ]

                        for file in files:
                            file_path = os.path.join(root, file)
                            # Prüfen, ob die Datei in einem ausgeschlossenen Verzeichnis liegt
                            if not any(
                                file_path.startswith(exclude_dir)
                                for exclude_dir in exclude_dirs
                            ):
                                tar.add(file_path)
                finally:
                    # Zurück zum ursprünglichen Verzeichnis wechseln
                    os.chdir(original_dir)
    except Exception as e:
        return False, f"Fehler beim Erstellen des Snapshot-Archivs: {str(e)}"

    # Archivgröße abrufen
    archive_size = system.get_file_size(archive_file)
    if archive_size is None:
        return False, "Fehler: Konnte Archivgröße nicht ermitteln"

    archive_size_formatted = _format_size(archive_size)

    logging.success(f"Snapshot-Archiv erfolgreich erstellt: {archive_file}")
    logging.info(f"Archivgröße: {archive_size_formatted}")

    return True, archive_file


def _need_sudo(directory: str) -> bool:
    """
    Prüft, ob sudo für Dateioperationen benötigt wird.

    Args:
        directory: Zu prüfendes Verzeichnis

    Returns:
        bool: True, wenn sudo benötigt wird, sonst False
    """
    # Prüfen, ob wir Schreibrechte auf das Verzeichnis haben
    if not os.access(directory, os.W_OK):
        return True

    # Prüfen, ob es Dateien gibt, für die wir keine Schreibrechte haben
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.exists(file_path) and not os.access(file_path, os.W_OK):
                return True

    return False


def _format_size(size_bytes: int) -> str:
    """
    Formatiert eine Größe in Bytes in eine lesbare Form.

    Args:
        size_bytes: Größe in Bytes

    Returns:
        str: Formatierte Größe
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def list_snapshots(snapshots_dir: Optional[str] = None) -> List[Tuple[str, str, str]]:
    """
    Listet alle vorhandenen Snapshots auf.

    Args:
        snapshots_dir: Verzeichnis mit Snapshots (optional)

    Returns:
        List[Tuple[str, str, str]]: Liste von (Dateiname, Datum, Größe)
    """
    if snapshots_dir is None:
        source_dir = system.get_project_root()
        snapshots_dir = os.path.join(source_dir, "data", "snapshots")

    if not os.path.isdir(snapshots_dir):
        logging.warn(f"Snapshots-Verzeichnis nicht gefunden: {snapshots_dir}")
        return []

    snapshots = []
    for file in os.listdir(snapshots_dir):
        if file.startswith("snapshot-") and file.endswith(".tar.gz"):
            file_path = os.path.join(snapshots_dir, file)
            file_size = system.get_file_size(file_path)
            file_date = file.replace("snapshot-", "").replace(".tar.gz", "")

            if file_size is not None:
                snapshots.append((file, file_date, _format_size(file_size)))

    return sorted(snapshots, key=lambda x: x[1], reverse=True)


def restore_snapshot(
    snapshot_file: str, target_dir: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Stellt einen Snapshot wieder her.

    Args:
        snapshot_file: Pfad zur Snapshot-Datei
        target_dir: Zielverzeichnis (optional)

    Returns:
        Tuple[bool, str]: (Erfolg, Erfolgsmeldung oder Fehlermeldung)
    """
    if not os.path.isfile(snapshot_file):
        return False, f"Fehler: Snapshot-Datei nicht gefunden: {snapshot_file}"

    if target_dir is None:
        target_dir = system.get_project_root()

    # Prüfen, ob genügend Speicherplatz vorhanden ist
    snapshot_size = system.get_file_size(snapshot_file)
    if snapshot_size is None:
        return (
            False,
            f"Fehler: Konnte Größe der Snapshot-Datei nicht ermitteln: {snapshot_file}",
        )

    disk_usage = system.get_disk_usage(target_dir)
    free_space = disk_usage["free"]

    # Wir benötigen mindestens die doppelte Größe des Snapshots
    if free_space < snapshot_size * 2:
        return (
            False,
            f"Fehler: Nicht genügend Speicherplatz. Benötigt: {_format_size(snapshot_size * 2)}, Verfügbar: {_format_size(free_space)}",
        )

    # Backup des Zielverzeichnisses erstellen
    backup_dir = (
        f"{target_dir}.backup-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    )
    logging.info(f"Erstelle Backup des Zielverzeichnisses: {backup_dir}")

    try:
        shutil.copytree(target_dir, backup_dir, symlinks=True)
    except Exception as e:
        return False, f"Fehler beim Erstellen des Backups: {str(e)}"

    # Snapshot wiederherstellen
    logging.info(f"Stelle Snapshot wieder her: {snapshot_file}")

    try:
        with tarfile.open(snapshot_file, "r:gz") as tar:
            tar.extractall(path=target_dir)

        logging.success(f"Snapshot erfolgreich wiederhergestellt: {snapshot_file}")
        return True, f"Snapshot erfolgreich wiederhergestellt: {snapshot_file}"
    except Exception as e:
        # Bei Fehler das Backup wiederherstellen
        logging.error(f"Fehler beim Wiederherstellen des Snapshots: {str(e)}")
        logging.info(f"Stelle Backup wieder her: {backup_dir}")

        try:
            shutil.rmtree(target_dir)
            shutil.copytree(backup_dir, target_dir, symlinks=True)
            return (
                False,
                f"Fehler beim Wiederherstellen des Snapshots: {str(e)}. Backup wurde wiederhergestellt.",
            )
        except Exception as e2:
            return (
                False,
                f"Fehler beim Wiederherstellen des Snapshots: {str(e)}. Fehler beim Wiederherstellen des Backups: {str(e2)}",
            )


def main() -> int:
    """
    Hauptfunktion für die direkte Ausführung des Skripts.

    Returns:
        int: Exit-Code (0 bei Erfolg, 1 bei Fehler)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Snapshot-Funktionalität für den LLM Stack"
    )
    subparsers = parser.add_subparsers(dest="command", help="Befehl")

    # Befehl: create
    create_parser = subparsers.add_parser("create", help="Erstellt einen Snapshot")
    create_parser.add_argument("--source-dir", help="Quellverzeichnis")
    create_parser.add_argument(
        "--exclude", nargs="+", help="Auszuschließende Verzeichnisse"
    )

    # Befehl: list
    list_parser = subparsers.add_parser("list", help="Listet alle Snapshots auf")
    list_parser.add_argument("--snapshots-dir", help="Verzeichnis mit Snapshots")

    # Befehl: restore
    restore_parser = subparsers.add_parser(
        "restore", help="Stellt einen Snapshot wieder her"
    )
    restore_parser.add_argument("snapshot_file", help="Pfad zur Snapshot-Datei")
    restore_parser.add_argument("--target-dir", help="Zielverzeichnis")

    args = parser.parse_args()

    if args.command == "create":
        success, result = create_snapshot(args.source_dir, args.exclude)
        if success:
            logging.success("Snapshot-Prozess abgeschlossen")
            return 0
        else:
            logging.error(result)
            return 1
    elif args.command == "list":
        snapshots = list_snapshots(args.snapshots_dir)
        if snapshots:
            print("Verfügbare Snapshots:")
            for file, date, size in snapshots:
                print(f"  {file} ({date}, {size})")
        else:
            print("Keine Snapshots gefunden.")
        return 0
    elif args.command == "restore":
        success, result = restore_snapshot(args.snapshot_file, args.target_dir)
        if success:
            logging.success(result)
            return 0
        else:
            logging.error(result)
            return 1
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
