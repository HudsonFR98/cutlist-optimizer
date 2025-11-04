#!/bin/bash

# Application Rename Script
# This script renames the entire template application by replacing template names with new app names
# in both file contents and filenames.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Cross-platform sed -i helper (GNU/BSD)
sed_inplace() {
    # Usage: sed_inplace 's/old/new/g' file
    if sed --version >/dev/null 2>&1; then
        sed -i "$1" "$2"
    else
        sed -i '' "$1" "$2"
    fi
}

# Title-case converter using python3 for portability
to_title_case() {
    python3 - "$1" <<'PY'
import sys, string
s = sys.argv[1]
print(string.capwords(s.replace('-', ' ')))
PY
}

# Function to validate input
validate_input() {
    local input="$1"
    local name="$2"
    
    if [[ -z "$input" ]]; then
        print_error "$name cannot be empty"
        return 1
    fi
    
    # Check for valid characters (alphanumeric, hyphens, underscores)
    if [[ ! "$input" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        print_error "$name contains invalid characters. Only alphanumeric, hyphens, and underscores are allowed."
        return 1
    fi
    
    return 0
}

# Main script
main() {
    echo "=========================================="
    echo "    Application Rename Script"
    echo "=========================================="
    echo ""
    
    # Get old names
    echo "Please provide the OLD names:"
    read -p "Old short name (e.g., nsft): " old_short
    read -p "Old full name (e.g., nath-standalone-flask-template): " old_name
    
    # Validate old names
    if ! validate_input "$old_short" "Old short name"; then
        exit 1
    fi
    if ! validate_input "$old_name" "Old full name"; then
        exit 1
    fi
    
    echo ""
    echo "Please provide the NEW names:"
    read -p "New short name (e.g., myapp): " new_short
    read -p "New full name (e.g., my-awesome-application): " new_name
    
    # Validate new names
    if ! validate_input "$new_short" "New short name"; then
        exit 1
    fi
    if ! validate_input "$new_name" "New full name"; then
        exit 1
    fi
    
    # Convert names to different formats
    local old_name_underscore=$(echo "$old_name" | tr '-' '_')
    local new_name_underscore=$(echo "$new_name" | tr '-' '_')
    local old_name_upper=$(echo "$old_name_underscore" | tr '[:lower:]' '[:upper:]')
    local new_name_upper=$(echo "$new_name_underscore" | tr '[:lower:]' '[:upper:]')
    local old_name_title=$(to_title_case "$old_name")
    local new_name_title=$(to_title_case "$new_name")
    
    echo ""
    echo "=========================================="
    echo "    Rename Summary"
    echo "=========================================="
    echo "Old short name: $old_short -> New short name: $new_short"
    echo "Old full name: $old_name -> New full name: $new_name"
    echo "Old underscore name: $old_name_underscore -> New underscore name: $new_name_underscore"
    echo "Old upper name: $old_name_upper -> New upper name: $new_name_upper"
    echo "Old title name: $old_name_title -> New title name: $new_name_title"
    echo ""
    
    read -p "Do you want to proceed with the rename? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        print_info "Rename cancelled"
        exit 0
    fi
    
    echo ""
    read -p "Do you want to create a backup before proceeding? (Y/n): " backup_confirm
    if [[ ! "$backup_confirm" =~ ^[Nn]$ ]]; then
        local backup_dir="backup_$(date +%Y%m%d_%H%M%S)"
        print_info "Creating backup in $backup_dir..."
        if cp -r . "../$backup_dir"; then
            print_success "Backup created successfully in ../$backup_dir"
        else
            print_error "Failed to create backup"
            exit 1
        fi
    fi
    
    echo ""
    print_info "Starting rename process..."
    
    # Step 1: Replace content in all text files
    print_info "Replacing content in files..."
    local files=$(find . \
        \( -path "./.git" -o -path "./.git/*" -o \
           -path "./node_modules" -o -path "./node_modules/*" -o \
           -path "./__pycache__" -o -path "./**/__pycache__" -o \
           -path "./.pytest_cache" -o -path "./.pytest_cache/*" -o \
           -name "backup_*" -o -path "./backup_*/*" -o \
           -name ".DS_Store" -o -name "Thumbs.db" -o \
           -name ".coverage" \) -prune -o \
        -type f -print 2>/dev/null | sort)
    
    echo "$files" | while read -r file; do
        if [[ -f "$file" ]] && file "$file" | grep -Eq 'text|empty'; then
            # Replace all variations in file content
            sed_inplace "s/$old_short/$new_short/g" "$file" 2>/dev/null || true
            sed_inplace "s/$old_name/$new_name/g" "$file" 2>/dev/null || true
            sed_inplace "s/$old_name_underscore/$new_name_underscore/g" "$file" 2>/dev/null || true
            sed_inplace "s/$old_name_upper/$new_name_upper/g" "$file" 2>/dev/null || true
            sed_inplace "s/$old_name_title/$new_name_title/g" "$file" 2>/dev/null || true
        fi
    done
    print_success "Content replacement completed"
    
    # Step 2: Rename files and directories
    print_info "Renaming files and directories..."
    local items_to_rename=$(find . \
        \( -path "./.git" -o -path "./.git/*" -o \
           -path "./node_modules" -o -path "./node_modules/*" -o \
           -path "./__pycache__" -o -path "./**/__pycache__" -o \
           -path "./.pytest_cache" -o -path "./.pytest_cache/*" -o \
           -name "backup_*" -o -path "./backup_*/*" \) -prune -o \
        \( -name "*$old_short*" -o -name "*$old_name*" -o -name "*$old_name_underscore*" -o -name "*$old_name_title*" \) \
        -print 2>/dev/null | sort -r)
    
    echo "$items_to_rename" | while read -r item; do
        if [[ -e "$item" ]]; then
            local new_item="$item"
            new_item=$(echo "$new_item" | sed "s/$old_short/$new_short/g")
            new_item=$(echo "$new_item" | sed "s/$old_name/$new_name/g")
            new_item=$(echo "$new_item" | sed "s/$old_name_underscore/$new_name_underscore/g")
            new_item=$(echo "$new_item" | sed "s/$old_name_title/$new_name_title/g")
            
            if [[ "$item" != "$new_item" ]]; then
                print_info "Renaming: $item -> $new_item"
                mv "$item" "$new_item" 2>/dev/null || print_warning "Could not rename $item"
            fi
        fi
    done
    print_success "File and directory renaming completed"
    
    echo ""
    print_success "Application rename completed successfully!"
    echo ""
    print_warning "Please review the changes and test the application before committing."
    print_warning "You may need to update additional configuration files manually."
    echo ""
    print_info "Next steps:"
    echo "1. Review the changes with: git status"
    echo "2. Test the application"
    echo "3. Update any external references (CI/CD, documentation, etc.)"
    echo "4. Commit the changes"
}

# Run the main function
main "$@" 