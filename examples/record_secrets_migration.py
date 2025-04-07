#!/usr/bin/env python3
"""
Example for recording the migration of the secrets.sh file in the Knowledge Graph.

This script demonstrates how the migration of the secrets.sh file to Python
can be recorded in the Knowledge Graph.
"""

import os
import sys

# Add path to project directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llm_stack.modules.knowledge_graph.module import get_module as get_kg_module


def main():
    """Main function."""
    # Knowledge Graph Modul abrufen
    try:
        kg_module = get_kg_module()

        # Migrationsentscheidung aufzeichnen
        decision_result = kg_module.record_migration_decision(
            decision="secrets.sh nach Python migrieren",
            rationale="Verbesserte Sicherheit und Wartbarkeit durch Verwendung von Python-Kryptografie-Bibliotheken",
            bash_file_path="lib/core/secrets.sh",
            python_file_path="llm_stack/core/secrets.py",
            alternatives=[
                "Bash-Skript beibehalten",
                "Teilweise Migration mit Python-Hilfsfunktionen",
            ],
            impact="Verbesserte Sicherheit, bessere Typsicherheit und einfachere Integration mit anderen Python-Modulen",
        )

        if decision_result:
            print("Migrationsentscheidung erfolgreich aufgezeichnet")
            decision_id = decision_result.get("id")
        else:
            print("Error recording migration decision")
            return

        # Bash-Datei im Knowledge Graph aufzeichnen
        with open("../local-llm-stack/lib/core/secrets.sh") as f:
            bash_content = f.read()
            bash_result = kg_module.record_bash_file(
                "lib/core/secrets.sh", bash_content
            )

        if bash_result:
            print("Bash file successfully recorded")
        else:
            print("Error recording bash file")

        # Python-Datei im Knowledge Graph aufzeichnen
        with open("../LOCAL-LLM-STACK-RELOADED/llm_stack/core/secrets.py") as f:
            python_content = f.read()
            python_result = kg_module.record_python_file(
                "llm_stack/core/secrets.py", python_content, "lib/core/secrets.sh"
            )

        if python_result:
            print("Python file successfully recorded")
        else:
            print("Error recording Python file")

        # Code-Transformation für die init_secrets-Funktion aufzeichnen
        BASH_INIT_SECRETS = """# Initialize secrets management
init_secrets() {
  log_debug "Initializing secrets management"
  
  # Ensure the config directory exists
  ensure_directory "$CONFIG_DIR"
  if [[ $? -ne 0 ]]; then
    handle_error $ERR_PERMISSION_DENIED "Failed to create config directory"
  fi
  
  # Create the secrets file if it doesn't exist
  if [[ ! -f "$SECRETS_FILE" ]]; then
    log_debug "Creating secrets file: $SECRETS_FILE"
    touch "$SECRETS_FILE" 2>/dev/null
    if [[ $? -ne 0 ]]; then
      handle_error $ERR_PERMISSION_DENIED "Failed to create secrets file"
    fi
    
    # Set secure permissions on the secrets file
    chmod 600 "$SECRETS_FILE" 2>/dev/null
    if [[ $? -ne 0 ]]; then
      log_warn "Failed to set secure permissions on secrets file"
    fi
  fi
  
  return $ERR_SUCCESS
}"""

        PYTHON_INIT_SECRETS = """def init_secrets() -> bool:
    '''
    Initializes the secrets management.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    '''
    logging.debug("Initializing secrets management")
    
    # Ensure the configuration directory exists
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
        except (IOError, PermissionError) as e:
            logging.error(f"Error creating secrets file: {str(e)}")
            return False
    
    return True"""

        transformation_result = kg_module.record_code_transformation(
            transformation_type="function_migration",
            before=BASH_INIT_SECRETS,
            after=PYTHON_INIT_SECRETS,
            bash_file_path="lib/core/secrets.sh",
            python_file_path="llm_stack/core/secrets.py",
            decision_id=decision_id,
        )

        if transformation_result:
            print("Code transformation successfully recorded")
        else:
            print("Error recording code transformation")

        # Code-Transformation für die generate_password-Funktion aufzeichnen
        BASH_GENERATE_PASSWORD = """# Generate a secure password
generate_password() {
  local length=$1
  local chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+[]{}|;:,.<>?"
  
  # Ensure we have at least one of each character type
  local password=$(generate_random_string $length)
  
  # Ensure we have at least one uppercase letter
  if ! [[ "$password" =~ [A-Z] ]]; then
    local pos=$((RANDOM % length))
    local upper_char=${chars:$((RANDOM % 26)):1}
    password="${password:0:$pos}$upper_char${password:$((pos+1))}"
  fi
  
  # Ensure we have at least one lowercase letter
  if ! [[ "$password" =~ [a-z] ]]; then
    local pos=$((RANDOM % length))
    local lower_char=${chars:$((26 + RANDOM % 26)):1}
    password="${password:0:$pos}$lower_char${password:$((pos+1))}"
  fi
  
  # Ensure we have at least one number
  if ! [[ "$password" =~ [0-9] ]]; then
    local pos=$((RANDOM % length))
    local num_char=${chars:$((52 + RANDOM % 10)):1}
    password="${password:0:$pos}$num_char${password:$((pos+1))}"
  fi
  
  # Ensure we have at least one special character
  if ! [[ "$password" =~ [^A-Za-z0-9] ]]; then
    local pos=$((RANDOM % length))
    local special_char=${chars:$((62 + RANDOM % (${#chars} - 62))):1}
    password="${password:0:$pos}$special_char${password:$((pos+1))}"
  fi
  
  echo "$password"
}"""

        PYTHON_GENERATE_PASSWORD = """def generate_password(length: int = 16) -> str:
    '''
    Generates a secure password.
    
    Args:
        length: Length of the password
        
    Returns:
        str: Secure password
    '''
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
        secrets.choice(special_chars)
    ]
    
    # Randomly select remaining characters
    all_chars = uppercase_chars + lowercase_chars + digit_chars + special_chars
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))
    
    # Shuffle password
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)"""

        transformation_result = kg_module.record_code_transformation(
            transformation_type="function_migration",
            before=BASH_GENERATE_PASSWORD,
            after=PYTHON_GENERATE_PASSWORD,
            bash_file_path="lib/core/secrets.sh",
            python_file_path="llm_stack/core/secrets.py",
            decision_id=decision_id,
        )

        if transformation_result:
            print("Code transformation for generate_password successfully recorded")
        else:
            print(
                "Error recording code transformation for generate_password"
            )

        # Migrationsstatistiken anzeigen
        stats = kg_module.get_migration_statistics()
        print("\nMigration statistics:")
        print(f"Total bash files: {stats['total_bash_files']}")
        print(f"Total Python files: {stats['total_python_files']}")
        print(f"Migrated files: {stats['migrated_files']}")
        print(f"Migration progress: {stats['migration_progress']:.2f}%")
        print(f"Total decisions: {stats['total_decisions']}")
        print(f"Total transformations: {stats['total_transformations']}")

    except ImportError:
        print("Knowledge Graph module not available")
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
