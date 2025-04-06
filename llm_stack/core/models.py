"""
Modellverwaltung für den LLM Stack.

Dieses Modul stellt Funktionen zur Verwaltung von LLM-Modellen bereit,
einschließlich Auflisten, Hinzufügen und Entfernen von Modellen.
"""

import json
import sys
from typing import Dict, List, Optional, Union

import requests
from rich.console import Console
from rich.table import Table

from llm_stack.core import error, logging

# Rich-Konsole für formatierte Ausgabe
console = Console()


def check_ollama_running(ollama_url: str) -> bool:
    """
    Prüft, ob der Ollama-Dienst läuft.
    
    Args:
        ollama_url: URL des Ollama-Dienstes
        
    Returns:
        bool: True, wenn der Ollama-Dienst läuft, sonst False
    """
    try:
        response = requests.get(f"{ollama_url}/api/version", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def list_models(ollama_url: str) -> List[Dict[str, str]]:
    """
    Listet verfügbare Modelle auf.
    
    Args:
        ollama_url: URL des Ollama-Dienstes
        
    Returns:
        List[Dict[str, str]]: Liste von Modell-Informationen
    """
    logging.info("Liste verfügbare Modelle auf...")
    
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        if response.status_code != 200:
            logging.error(f"Fehler beim Auflisten der Modelle. Ollama API gab einen Fehler zurück: {response.text}")
            return []
        
        data = response.json()
        models = data.get("models", [])
        
        # Modelle in einer Tabelle anzeigen
        table = Table(title="Verfügbare Modelle")
        table.add_column("Name", style="cyan")
        table.add_column("Größe", style="green")
        table.add_column("Modifiziert", style="yellow")
        
        for model in models:
            table.add_row(
                model.get("name", "Unbekannt"),
                format_size(model.get("size", 0)),
                model.get("modified", "Unbekannt")
            )
        
        console.print(table)
        
        # Hilfreiche Tipps anzeigen
        console.print()
        logging.info("Tipp: Fügen Sie ein Modell mit 'llm models add modell_name' hinzu")
        
        return models
    except requests.RequestException as e:
        logging.error(f"Fehler beim Auflisten der Modelle: {str(e)}")
        return []


def add_model(ollama_url: str, model_name: str) -> bool:
    """
    Fügt ein Modell hinzu.
    
    Args:
        ollama_url: URL des Ollama-Dienstes
        model_name: Name des Modells
        
    Returns:
        bool: True, wenn das Modell erfolgreich hinzugefügt wurde, sonst False
    """
    logging.info(f"Füge Modell {model_name} hinzu...")
    logging.warn("Dies kann je nach Modellgröße eine Weile dauern...")
    
    try:
        response = requests.post(
            f"{ollama_url}/api/pull",
            json={"name": model_name},
            timeout=600  # Längeres Timeout für große Modelle
        )
        
        if response.status_code != 200:
            logging.error(f"Fehler beim Hinzufügen des Modells {model_name}. Ollama API gab einen Fehler zurück: {response.text}")
            return False
        
        logging.success(f"Modell {model_name} erfolgreich hinzugefügt.")
        logging.info("Tipp: Verwenden Sie 'llm models list', um alle verfügbaren Modelle anzuzeigen")
        return True
    except requests.RequestException as e:
        logging.error(f"Fehler beim Hinzufügen des Modells {model_name}: {str(e)}")
        return False


def remove_model(ollama_url: str, model_name: str) -> bool:
    """
    Entfernt ein Modell.
    
    Args:
        ollama_url: URL des Ollama-Dienstes
        model_name: Name des Modells
        
    Returns:
        bool: True, wenn das Modell erfolgreich entfernt wurde, sonst False
    """
    logging.info(f"Entferne Modell {model_name}...")
    
    try:
        response = requests.delete(
            f"{ollama_url}/api/delete",
            json={"name": model_name},
            timeout=30
        )
        
        if response.status_code != 200:
            logging.error(f"Fehler beim Entfernen des Modells {model_name}. Ollama API gab einen Fehler zurück: {response.text}")
            return False
        
        logging.success(f"Modell {model_name} erfolgreich entfernt.")
        return True
    except requests.RequestException as e:
        logging.error(f"Fehler beim Entfernen des Modells {model_name}: {str(e)}")
        return False


def get_model_info(ollama_url: str, model_name: str) -> Optional[Dict[str, Union[str, int]]]:
    """
    Ruft Informationen zu einem Modell ab.
    
    Args:
        ollama_url: URL des Ollama-Dienstes
        model_name: Name des Modells
        
    Returns:
        Optional[Dict[str, Union[str, int]]]: Modell-Informationen oder None, wenn das Modell nicht gefunden wurde
    """
    try:
        # Liste aller Modelle abrufen
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        if response.status_code != 200:
            logging.error(f"Fehler beim Abrufen der Modellinformationen. Ollama API gab einen Fehler zurück: {response.text}")
            return None
        
        data = response.json()
        models = data.get("models", [])
        
        # Nach dem angegebenen Modell suchen
        for model in models:
            if model.get("name") == model_name:
                return model
        
        logging.error(f"Modell {model_name} nicht gefunden")
        return None
    except requests.RequestException as e:
        logging.error(f"Fehler beim Abrufen der Modellinformationen: {str(e)}")
        return None


def format_size(size_bytes: int) -> str:
    """
    Formatiert eine Größe in Bytes in eine lesbare Form.
    
    Args:
        size_bytes: Größe in Bytes
        
    Returns:
        str: Formatierte Größe
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def generate_model_completion(ollama_url: str, model_name: str, prompt: str, options: Optional[Dict] = None) -> Optional[str]:
    """
    Generiert eine Vervollständigung mit einem Modell.
    
    Args:
        ollama_url: URL des Ollama-Dienstes
        model_name: Name des Modells
        prompt: Eingabeaufforderung
        options: Optionen für die Generierung
        
    Returns:
        Optional[str]: Generierte Vervollständigung oder None, wenn ein Fehler aufgetreten ist
    """
    if options is None:
        options = {}
    
    try:
        payload = {
            "model": model_name,
            "prompt": prompt,
            **options
        }
        
        response = requests.post(
            f"{ollama_url}/api/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            logging.error(f"Fehler bei der Generierung. Ollama API gab einen Fehler zurück: {response.text}")
            return None
        
        data = response.json()
        return data.get("response", "")
    except requests.RequestException as e:
        logging.error(f"Fehler bei der Generierung: {str(e)}")
        return None


def chat_with_model(ollama_url: str, model_name: str, messages: List[Dict[str, str]], options: Optional[Dict] = None) -> Optional[str]:
    """
    Chattet mit einem Modell.
    
    Args:
        ollama_url: URL des Ollama-Dienstes
        model_name: Name des Modells
        messages: Liste von Nachrichten (jede mit 'role' und 'content')
        options: Optionen für den Chat
        
    Returns:
        Optional[str]: Antwort des Modells oder None, wenn ein Fehler aufgetreten ist
    """
    if options is None:
        options = {}
    
    try:
        payload = {
            "model": model_name,
            "messages": messages,
            **options
        }
        
        response = requests.post(
            f"{ollama_url}/api/chat",
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            logging.error(f"Fehler beim Chat. Ollama API gab einen Fehler zurück: {response.text}")
            return None
        
        data = response.json()
        return data.get("message", {}).get("content", "")
    except requests.RequestException as e:
        logging.error(f"Fehler beim Chat: {str(e)}")
        return None


def create_model(ollama_url: str, model_name: str, modelfile_content: str) -> bool:
    """
    Erstellt ein benutzerdefiniertes Modell.
    
    Args:
        ollama_url: URL des Ollama-Dienstes
        model_name: Name des Modells
        modelfile_content: Inhalt der Modelldatei
        
    Returns:
        bool: True, wenn das Modell erfolgreich erstellt wurde, sonst False
    """
    logging.info(f"Erstelle benutzerdefiniertes Modell {model_name}...")
    
    try:
        response = requests.post(
            f"{ollama_url}/api/create",
            json={"name": model_name, "modelfile": modelfile_content},
            timeout=600  # Längeres Timeout für die Modellerstellung
        )
        
        if response.status_code != 200:
            logging.error(f"Fehler beim Erstellen des Modells {model_name}. Ollama API gab einen Fehler zurück: {response.text}")
            return False
        
        logging.success(f"Modell {model_name} erfolgreich erstellt.")
        return True
    except requests.RequestException as e:
        logging.error(f"Fehler beim Erstellen des Modells {model_name}: {str(e)}")
        return False


logging.debug("Modellverwaltungsmodul initialisiert")