"""
Docker-Funktionen für den LLM Stack.

Dieses Modul stellt Funktionen zur Interaktion mit Docker und zur Verwaltung
von Docker Compose-Operationen bereit.
"""

import os
import subprocess
from typing import Dict, List, Optional, Tuple, Union

import docker
from docker.errors import DockerException
from rich.console import Console
from rich.table import Table

from llm_stack.core import error, logging

# Docker-Client
try:
    docker_client = docker.from_env()
except DockerException as e:
    logging.error(f"Fehler beim Initialisieren des Docker-Clients: {str(e)}")
    docker_client = None

# Rich-Konsole für formatierte Ausgabe
console = Console()


def check_docker_available() -> bool:
    """
    Prüft, ob Docker verfügbar ist.
    
    Returns:
        bool: True, wenn Docker verfügbar ist, sonst False
    """
    if docker_client is None:
        return False
    
    try:
        docker_client.ping()
        return True
    except DockerException:
        return False


def get_container_status(container_name: str) -> Optional[Dict[str, str]]:
    """
    Ruft den Status eines Containers ab.
    
    Args:
        container_name: Name des Containers
        
    Returns:
        Optional[Dict[str, str]]: Container-Status oder None, wenn der Container nicht gefunden wurde
    """
    if docker_client is None:
        logging.error("Docker-Client ist nicht initialisiert")
        return None
    
    try:
        containers = docker_client.containers.list(all=True, filters={"name": container_name})
        if not containers:
            return None
        
        container = containers[0]
        return {
            "id": container.id[:12],
            "name": container.name,
            "status": container.status,
            "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
            "ports": ", ".join([f"{port['PublicPort']}:{port['PrivatePort']}" for port in container.ports]) if container.ports else ""
        }
    except DockerException as e:
        logging.error(f"Fehler beim Abrufen des Container-Status: {str(e)}")
        return None


def get_all_containers_status() -> List[Dict[str, str]]:
    """
    Ruft den Status aller Container ab.
    
    Returns:
        List[Dict[str, str]]: Liste von Container-Status-Dictionaries
    """
    if docker_client is None:
        logging.error("Docker-Client ist nicht initialisiert")
        return []
    
    try:
        containers = docker_client.containers.list(all=True)
        return [
            {
                "id": container.id[:12],
                "name": container.name,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                "ports": ", ".join([f"{port['PublicPort']}:{port['PrivatePort']}" for port in container.ports]) if container.ports else ""
            }
            for container in containers
        ]
    except DockerException as e:
        logging.error(f"Fehler beim Abrufen des Container-Status: {str(e)}")
        return []


def show_container_status() -> None:
    """Zeigt den Status aller Container in einer formatierten Tabelle an."""
    # Container-Status mit besserer Formatierung abrufen
    table = Table(title="Container-Status")
    table.add_column("Container", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Ports", style="yellow")
    
    # Docker-Container-Status abrufen
    containers = get_all_containers_status()
    
    # Nach Namen sortieren
    containers.sort(key=lambda c: c["name"])
    
    # Tabelle füllen
    for container in containers:
        table.add_row(
            container["name"],
            container["status"],
            container["ports"] or "keine"
        )
    
    # Tabelle anzeigen
    console.print(table)


def compose_up(project_name: str, compose_files: str, service: str = "") -> bool:
    """
    Führt 'docker-compose up' aus.
    
    Args:
        project_name: Name des Projekts
        compose_files: Docker Compose-Dateien (z.B. "-f docker-compose.yml")
        service: Optionaler Dienstname
        
    Returns:
        bool: True, wenn der Befehl erfolgreich ausgeführt wurde, sonst False
    """
    cmd = f"docker-compose {compose_files} -p {project_name} up -d"
    if service:
        cmd += f" {service}"
    
    logging.debug(f"Führe aus: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.debug(f"Ausgabe: {result.stdout.decode('utf-8')}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Fehler beim Ausführen von 'docker-compose up': {e.stderr.decode('utf-8')}")
        return False


def compose_down(project_name: str, compose_files: str, service: str = "") -> bool:
    """
    Führt 'docker-compose down' aus.
    
    Args:
        project_name: Name des Projekts
        compose_files: Docker Compose-Dateien (z.B. "-f docker-compose.yml")
        service: Optionaler Dienstname
        
    Returns:
        bool: True, wenn der Befehl erfolgreich ausgeführt wurde, sonst False
    """
    cmd = f"docker-compose {compose_files} -p {project_name} down"
    if service:
        cmd += f" {service}"
    
    logging.debug(f"Führe aus: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.debug(f"Ausgabe: {result.stdout.decode('utf-8')}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Fehler beim Ausführen von 'docker-compose down': {e.stderr.decode('utf-8')}")
        return False


def compose_logs(project_name: str, compose_files: str, service: str = "", tail: int = 100) -> Optional[str]:
    """
    Führt 'docker-compose logs' aus.
    
    Args:
        project_name: Name des Projekts
        compose_files: Docker Compose-Dateien (z.B. "-f docker-compose.yml")
        service: Optionaler Dienstname
        tail: Anzahl der anzuzeigenden Zeilen
        
    Returns:
        Optional[str]: Logs oder None, wenn ein Fehler aufgetreten ist
    """
    cmd = f"docker-compose {compose_files} -p {project_name} logs --tail={tail}"
    if service:
        cmd += f" {service}"
    
    logging.debug(f"Führe aus: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        logging.error(f"Fehler beim Ausführen von 'docker-compose logs': {e.stderr.decode('utf-8')}")
        return None


def compose_exec(project_name: str, compose_files: str, service: str, command: str) -> Optional[str]:
    """
    Führt 'docker-compose exec' aus.
    
    Args:
        project_name: Name des Projekts
        compose_files: Docker Compose-Dateien (z.B. "-f docker-compose.yml")
        service: Dienstname
        command: Auszuführender Befehl
        
    Returns:
        Optional[str]: Ausgabe oder None, wenn ein Fehler aufgetreten ist
    """
    cmd = f"docker-compose {compose_files} -p {project_name} exec -T {service} {command}"
    
    logging.debug(f"Führe aus: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        logging.error(f"Fehler beim Ausführen von 'docker-compose exec': {e.stderr.decode('utf-8')}")
        return None


def compose_ps(project_name: str, compose_files: str) -> Optional[str]:
    """
    Führt 'docker-compose ps' aus.
    
    Args:
        project_name: Name des Projekts
        compose_files: Docker Compose-Dateien (z.B. "-f docker-compose.yml")
        
    Returns:
        Optional[str]: Ausgabe oder None, wenn ein Fehler aufgetreten ist
    """
    cmd = f"docker-compose {compose_files} -p {project_name} ps"
    
    logging.debug(f"Führe aus: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        logging.error(f"Fehler beim Ausführen von 'docker-compose ps': {e.stderr.decode('utf-8')}")
        return None


def check_container_health(container_name: str) -> Optional[str]:
    """
    Prüft den Gesundheitszustand eines Containers.
    
    Args:
        container_name: Name des Containers
        
    Returns:
        Optional[str]: Gesundheitszustand oder None, wenn der Container nicht gefunden wurde
    """
    if docker_client is None:
        logging.error("Docker-Client ist nicht initialisiert")
        return None
    
    try:
        containers = docker_client.containers.list(all=True, filters={"name": container_name})
        if not containers:
            return None
        
        container = containers[0]
        
        # Gesundheitszustand abrufen
        inspection = docker_client.api.inspect_container(container.id)
        if "Health" in inspection["State"]:
            return inspection["State"]["Health"]["Status"]
        
        # Wenn kein Gesundheitscheck definiert ist, Status zurückgeben
        return container.status
    except DockerException as e:
        logging.error(f"Fehler beim Abrufen des Container-Gesundheitszustands: {str(e)}")
        return None


def wait_for_container_health(container_name: str, target_status: str = "healthy", timeout: int = 60) -> bool:
    """
    Wartet, bis ein Container einen bestimmten Gesundheitszustand erreicht hat.
    
    Args:
        container_name: Name des Containers
        target_status: Zielstatus (z.B. "healthy", "running")
        timeout: Timeout in Sekunden
        
    Returns:
        bool: True, wenn der Container den Zielstatus erreicht hat, sonst False
    """
    import time
    
    logging.info(f"Warte auf Container {container_name} ({target_status})...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        health = check_container_health(container_name)
        if health == target_status:
            logging.success(f"Container {container_name} ist {target_status}")
            return True
        
        # Kurz warten, bevor erneut geprüft wird
        time.sleep(1)
    
    logging.error(f"Timeout beim Warten auf Container {container_name} ({target_status})")
    return False


def pull_image(image_name: str, tag: str = "latest") -> bool:
    """
    Zieht ein Docker-Image.
    
    Args:
        image_name: Name des Images
        tag: Tag des Images
        
    Returns:
        bool: True, wenn das Image erfolgreich gezogen wurde, sonst False
    """
    if docker_client is None:
        logging.error("Docker-Client ist nicht initialisiert")
        return False
    
    try:
        logging.info(f"Ziehe Image {image_name}:{tag}...")
        docker_client.images.pull(image_name, tag=tag)
        logging.success(f"Image {image_name}:{tag} erfolgreich gezogen")
        return True
    except DockerException as e:
        logging.error(f"Fehler beim Ziehen des Images {image_name}:{tag}: {str(e)}")
        return False


def check_image_exists(image_name: str, tag: str = "latest") -> bool:
    """
    Prüft, ob ein Docker-Image existiert.
    
    Args:
        image_name: Name des Images
        tag: Tag des Images
        
    Returns:
        bool: True, wenn das Image existiert, sonst False
    """
    if docker_client is None:
        logging.error("Docker-Client ist nicht initialisiert")
        return False
    
    try:
        images = docker_client.images.list(name=f"{image_name}:{tag}")
        return len(images) > 0
    except DockerException as e:
        logging.error(f"Fehler beim Prüfen des Images {image_name}:{tag}: {str(e)}")
        return False


def get_container_logs(container_name: str, tail: int = 100) -> Optional[str]:
    """
    Ruft die Logs eines Containers ab.
    
    Args:
        container_name: Name des Containers
        tail: Anzahl der anzuzeigenden Zeilen
        
    Returns:
        Optional[str]: Logs oder None, wenn der Container nicht gefunden wurde
    """
    if docker_client is None:
        logging.error("Docker-Client ist nicht initialisiert")
        return None
    
    try:
        containers = docker_client.containers.list(all=True, filters={"name": container_name})
        if not containers:
            return None
        
        container = containers[0]
        return container.logs(tail=tail).decode('utf-8')
    except DockerException as e:
        logging.error(f"Fehler beim Abrufen der Container-Logs: {str(e)}")
        return None


def check_docker_compose_installed() -> bool:
    """
    Prüft, ob Docker Compose installiert ist.
    
    Returns:
        bool: True, wenn Docker Compose installiert ist, sonst False
    """
    try:
        result = subprocess.run(["docker-compose", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except FileNotFoundError:
        return False


# Initialisierungsprüfungen
if not check_docker_available():
    logging.warn("Docker ist nicht verfügbar. Einige Funktionen werden nicht funktionieren.")

if not check_docker_compose_installed():
    logging.warn("Docker Compose ist nicht installiert. Einige Funktionen werden nicht funktionieren.")

logging.debug("Docker-Modul initialisiert")