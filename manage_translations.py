#!/usr/bin/env python3
"""
Translation management script for Cutlist Optimizer application.

This script helps with:
1. Extracting translatable strings from the codebase
2. Updating existing translation files
3. Adding new languages
4. Compiling translation files

Usage:
    python manage_translations.py extract          # Extract strings to messages.pot
    python manage_translations.py update          # Update existing translation files
    python manage_translations.py compile         # Compile all translation files
    python manage_translations.py init <lang>     # Initialize new language
    python manage_translations.py all             # Run extract, update, and compile
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed:")
        print(f"  Error: {e.stderr}")
        return False


def extract_strings():
    """Extract translatable strings from the codebase"""
    return run_command(
        "pybabel extract -F babel.cfg -k _ -o cutlist_optimizer/translations/messages.pot cutlist_optimizer",
        "Extracting translatable strings"
    )


def update_translations():
    """Update existing translation files with new strings"""
    success = True
    for lang in ['en', 'fr']:
        lang_dir = f"cutlist_optimizer/translations/{lang}/LC_MESSAGES"
        if os.path.exists(lang_dir):
            success &= run_command(
                f"pybabel update -i cutlist_optimizer/translations/messages.pot -d cutlist_optimizer/translations -l {lang}",
                f"Updating {lang} translations"
            )
    return success


def compile_translations():
    """Compile all translation files"""
    return run_command(
        "pybabel compile -d cutlist_optimizer/translations",
        "Compiling translation files"
    )


def init_language(lang):
    """Initialize a new language"""
    if not lang:
        print("Error: Language code required (e.g., 'es' for Spanish)")
        return False
    
    # Create language directory
    lang_dir = f"cutlist_optimizer/translations/{lang}/LC_MESSAGES"
    os.makedirs(lang_dir, exist_ok=True)
    
    # Initialize translation file
    return run_command(
        f"pybabel init -i cutlist_optimizer/translations/messages.pot -d cutlist_optimizer/translations -l {lang}",
        f"Initializing {lang} translation file"
    )


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1]
    
    if command == "extract":
        extract_strings()
    elif command == "update":
        update_translations()
    elif command == "compile":
        compile_translations()
    elif command == "init":
        if len(sys.argv) < 3:
            print("Error: Language code required for init command")
            return
        init_language(sys.argv[2])
    elif command == "all":
        extract_strings()
        update_translations()
        compile_translations()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main() 