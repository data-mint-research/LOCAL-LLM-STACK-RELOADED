#!/usr/bin/env python3
"""
Initialisiert das LOCAL-LLM-STACK-RELOADED Repository und pusht es auf GitHub.

Dieses Skript initialisiert das Git-Repository, fügt alle Dateien hinzu,
erstellt einen initialen Commit und pusht das Repository auf GitHub.
"""

import os
import subprocess
import sys
from typing import List, Optional, Tuple


def run_command(command: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """
    Führt einen Befehl aus und gibt den Rückgabecode, stdout und stderr zurück.
    
    Args:
        command: Auszuführender Befehl als Liste von Strings
        cwd: Arbeitsverzeichnis für den Befehl
        
    Returns:
        Tuple[int, str, str]: Rückgabecode, stdout, stderr
    """
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        universal_newlines=True
    )
    
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr


def init_git_repo(repo_dir: str) -> bool:
    """
    Initialisiert ein Git-Repository.
    
    Args:
        repo_dir: Pfad zum Repository-Verzeichnis
        
    Returns:
        bool: True, wenn die Initialisierung erfolgreich war, sonst False
    """
    print(f"Initialisiere Git-Repository in {repo_dir}...")
    
    # Git-Repository initialisieren
    returncode, stdout, stderr = run_command(["git", "init"], cwd=repo_dir)
    if returncode != 0:
        print(f"Fehler beim Initialisieren des Git-Repositories: {stderr}")
        return False
    
    print("Git-Repository erfolgreich initialisiert.")
    return True


def add_files(repo_dir: str) -> bool:
    """
    Fügt alle Dateien zum Git-Repository hinzu.
    
    Args:
        repo_dir: Pfad zum Repository-Verzeichnis
        
    Returns:
        bool: True, wenn das Hinzufügen erfolgreich war, sonst False
    """
    print("Füge Dateien zum Git-Repository hinzu...")
    
    # Dateien hinzufügen
    returncode, stdout, stderr = run_command(["git", "add", "."], cwd=repo_dir)
    if returncode != 0:
        print(f"Fehler beim Hinzufügen der Dateien: {stderr}")
        return False
    
    print("Dateien erfolgreich hinzugefügt.")
    return True


def create_initial_commit(repo_dir: str) -> bool:
    """
    Erstellt einen initialen Commit.
    
    Args:
        repo_dir: Pfad zum Repository-Verzeichnis
        
    Returns:
        bool: True, wenn der Commit erfolgreich war, sonst False
    """
    print("Erstelle initialen Commit...")
    
    # Commit erstellen
    commit_message = "Initial commit: Python-Migration des LOCAL-LLM-STACK mit neo4j-Knowledge-Graph-Integration"
    returncode, stdout, stderr = run_command(
        ["git", "commit", "-m", commit_message],
        cwd=repo_dir
    )
    if returncode != 0:
        print(f"Fehler beim Erstellen des Commits: {stderr}")
        return False
    
    print("Initialer Commit erfolgreich erstellt.")
    return True


def add_github_remote(repo_dir: str, github_url: str) -> bool:
    """
    Fügt einen GitHub-Remote hinzu.
    
    Args:
        repo_dir: Pfad zum Repository-Verzeichnis
        github_url: URL des GitHub-Repositories
        
    Returns:
        bool: True, wenn das Hinzufügen erfolgreich war, sonst False
    """
    print(f"Füge GitHub-Remote hinzu: {github_url}...")
    
    # Remote hinzufügen
    returncode, stdout, stderr = run_command(
        ["git", "remote", "add", "origin", github_url],
        cwd=repo_dir
    )
    if returncode != 0:
        print(f"Fehler beim Hinzufügen des GitHub-Remotes: {stderr}")
        return False
    
    print("GitHub-Remote erfolgreich hinzugefügt.")
    return True


def push_to_github(repo_dir: str) -> bool:
    """
    Pusht das Repository auf GitHub.
    
    Args:
        repo_dir: Pfad zum Repository-Verzeichnis
        
    Returns:
        bool: True, wenn der Push erfolgreich war, sonst False
    """
    print("Pushe Repository auf GitHub...")
    
    # Push durchführen
    returncode, stdout, stderr = run_command(
        ["git", "push", "-u", "origin", "main"],
        cwd=repo_dir
    )
    if returncode != 0:
        print(f"Fehler beim Pushen auf GitHub: {stderr}")
        return False
    
    print("Repository erfolgreich auf GitHub gepusht.")
    return True


def main() -> int:
    """
    Hauptfunktion.
    
    Returns:
        int: Exit-Code (0 für Erfolg, 1 für Fehler)
    """
    # Repository-Verzeichnis
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    
    # GitHub-URL abfragen
    github_url = input("Bitte geben Sie die GitHub-Repository-URL ein: ")
    if not github_url:
        print("Keine GitHub-URL angegeben. Abbruch.")
        return 1
    
    # Git-Repository initialisieren
    if not init_git_repo(repo_dir):
        return 1
    
    # Dateien hinzufügen
    if not add_files(repo_dir):
        return 1
    
    # Initialen Commit erstellen
    if not create_initial_commit(repo_dir):
        return 1
    
    # GitHub-Remote hinzufügen
    if not add_github_remote(repo_dir, github_url):
        return 1
    
    # Auf GitHub pushen
    if not push_to_github(repo_dir):
        return 1
    
    print("\nRepository erfolgreich initialisiert und auf GitHub gepusht!")
    print(f"GitHub-URL: {github_url}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())