#!/bin/bash
# Database Manager Bash Script for Linux/Mac
# Quick commands for database operations

set -e

if [ -z "$1" ]; then
    echo ""
    echo "Flight Booking System - Database Manager"
    echo "========================================"
    echo ""
    echo "Usage: ./database_manager.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  export      - Export database to CSV"
    echo "  setup       - Setup fresh database"
    echo "  import      - Import from CSV"
    echo "  full-setup  - Complete workflow"
    echo ""
    echo "Examples:"
    echo "  ./database_manager.sh setup"
    echo "  ./database_manager.sh export --output ./backup"
    echo "  ./database_manager.sh full-setup"
    echo ""
    echo "For more help: python database_manager.py --help"
    echo ""
    exit 0
fi

# Check if Python is available
if ! command -v python3.12 &> /dev/null; then
    if ! command -v python3 &> /dev/null; then
        if ! command -v python &> /dev/null; then
            echo "Error: Python not found. Please install Python 3.12+"
            exit 1
        fi
    fi
fi

# Run the Python script
python database_manager.py "$@"
