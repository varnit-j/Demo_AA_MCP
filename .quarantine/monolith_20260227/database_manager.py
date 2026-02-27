#!/usr/bin/env python3
"""
Master Database Migration and Setup Script
==========================================

This script automates the complete database workflow:
1. Export current database to CSV files (backup)
2. Set up a new database with Python 3.12
3. Import all data from CSV files

Usage:
    python database_manager.py export             # Export current DB to CSV
    python database_manager.py setup              # Setup fresh DB with Python 3.12
    python database_manager.py import             # Import data from CSV files
    python database_manager.py full-restore       # Complete backup and restore workflow
    python database_manager.py full-setup         # Export current, setup new, import all

Options:
    python database_manager.py export --output ./backups/2024-01-27
    python database_manager.py setup --db mydb.sqlite3 --skip-requirements
    python database_manager.py full-restore --backup-dir ./backups/2024-01-27
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
from datetime import datetime


class DatabaseManager:
    def __init__(self, django_dir='.', db_path='db.sqlite3', data_dir='./Data'):
        self.django_dir = django_dir
        self.db_path = db_path
        self.data_dir = data_dir
        self.backup_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.backup_dir = f'backups/db_backup_{self.backup_timestamp}'
    
    def run_script(self, script_path, args=None, cwd=None):
        """Run a Python script"""
        cmd = f'python "{script_path}"'
        if args:
            cmd += ' ' + args
        
        print(f"\n▶ Running: {os.path.basename(script_path)}")
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd or self.django_dir,
                capture_output=False,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    def export_database(self, output_dir=None):
        """Export database to CSV files"""
        print("\n" + "="*70)
        print("EXPORTING DATABASE TO CSV")
        print("="*70)
        
        if output_dir is None:
            output_dir = f'data_exports/export_{self.backup_timestamp}'
        
        os.makedirs(output_dir, exist_ok=True)
        
        export_script = os.path.join(self.data_dir, 'export_db_to_csv.py')
        
        if not os.path.exists(export_script):
            print(f"✗ Export script not found at {export_script}")
            return False
        
        args = f'--db "{self.db_path}" --output "{output_dir}"'
        
        if self.run_script(export_script, args):
            print(f"\n✓ Export completed to: {output_dir}")
            return True
        return False
    
    def setup_database(self, skip_requirements=False, skip_import=False):
        """Setup fresh database with migrations"""
        print("\n" + "="*70)
        print("SETTING UP DATABASE FOR PYTHON 3.12")
        print("="*70)
        
        setup_script = os.path.join(self.django_dir, 'setup_db_py312.py')
        
        if not os.path.exists(setup_script):
            print(f"✗ Setup script not found at {setup_script}")
            return False
        
        args = f'--django-dir "{self.django_dir}" --db "{self.db_path}" --data "{self.data_dir}"'
        
        if skip_requirements:
            args += ' --skip-requirements'
        if skip_import:
            args += ' --skip-import'
        
        return self.run_script(setup_script, args)
    
    def import_data(self):
        """Import data from CSV files"""
        print("\n" + "="*70)
        print("IMPORTING DATA FROM CSV FILES")
        print("="*70)
        
        import_script = os.path.join(self.data_dir, 'import_all_from_csv.py')
        
        if not os.path.exists(import_script):
            print(f"✗ Import script not found at {import_script}")
            return False
        
        # We need to be in Django directory to import
        os.chdir(self.django_dir)
        
        args = f'--data "{self.data_dir}"'
        
        return self.run_script(import_script, args, cwd=self.django_dir)
    
    def backup_database(self):
        """Create a backup of the current database"""
        print("\n" + "="*70)
        print("CREATING DATABASE BACKUP")
        print("="*70)
        
        if not os.path.exists(self.db_path):
            print(f"⚠ Database not found at {self.db_path}")
            return False
        
        os.makedirs(self.backup_dir, exist_ok=True)
        
        backup_db = os.path.join(self.backup_dir, 'db.sqlite3')
        
        try:
            shutil.copy2(self.db_path, backup_db)
            print(f"✓ Database backed up to: {self.backup_dir}")
            return True
        except Exception as e:
            print(f"✗ Backup failed: {e}")
            return False
    
    def full_workflow(self, with_backup=True):
        """Execute complete workflow: backup -> export -> setup -> import"""
        print("\n" + "="*70)
        print("COMPLETE DATABASE MIGRATION WORKFLOW")
        print("="*70)
        
        # Step 1: Backup current database
        if with_backup:
            if not self.backup_database():
                print("\n⚠ Warning: Backup failed, continuing anyway...")
        
        # Step 2: Export current data
        export_dir = f'data_exports/export_{self.backup_timestamp}'
        if not self.export_database(export_dir):
            print("\n✗ Export failed")
            return False
        
        # Step 3: Remove old database
        if os.path.exists(self.db_path):
            print(f"\n▶ Removing old database...")
            os.remove(self.db_path)
            print(f"✓ Old database removed")
        
        # Step 4: Setup fresh database
        if not self.setup_database(skip_import=True):
            print("\n✗ Setup failed")
            return False
        
        # Step 5: Import data
        if not self.import_data():
            print("\n⚠ Warning: Import completed with issues")
        
        print("\n" + "="*70)
        print("✓ COMPLETE WORKFLOW SUCCESSFUL")
        print("="*70)
        print(f"\nBackup location:   {self.backup_dir if with_backup else 'N/A'}")
        print(f"Export location:   {export_dir}")
        print(f"New database:      {self.db_path}")
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Master database management tool for Flight Booking System"
    )
    
    # Main command
    parser.add_argument(
        'command',
        choices=['export', 'setup', 'import', 'full-restore', 'full-setup'],
        help='Command to execute'
    )
    
    # Common options
    parser.add_argument(
        '--django-dir',
        default='.',
        help='Django project directory (default: current directory)'
    )
    parser.add_argument(
        '--db',
        default='db.sqlite3',
        help='Database file path (default: db.sqlite3)'
    )
    parser.add_argument(
        '--data',
        default='./Data',
        help='Data/CSV directory (default: ./Data)'
    )
    
    # Export options
    parser.add_argument(
        '--output',
        help='Output directory for export'
    )
    
    # Setup options
    parser.add_argument(
        '--skip-requirements',
        action='store_true',
        help='Skip installing requirements'
    )
    parser.add_argument(
        '--skip-import',
        action='store_true',
        help='Skip importing data during setup'
    )
    
    # Restore options
    parser.add_argument(
        '--backup-dir',
        help='Backup directory to restore from'
    )
    
    # Workflow options
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating backup during full workflow'
    )
    
    args = parser.parse_args()
    
    manager = DatabaseManager(
        django_dir=args.django_dir,
        db_path=args.db,
        data_dir=args.data
    )
    
    success = False
    
    if args.command == 'export':
        success = manager.export_database(args.output)
    
    elif args.command == 'setup':
        success = manager.setup_database(
            skip_requirements=args.skip_requirements,
            skip_import=args.skip_import
        )
    
    elif args.command == 'import':
        success = manager.import_data()
    
    elif args.command == 'full-restore':
        # Restore from specific backup
        if not args.backup_dir:
            print("✗ Error: --backup-dir required for full-restore")
            sys.exit(1)
        
        print("\n" + "="*70)
        print("FULL DATABASE RESTORE FROM BACKUP")
        print("="*70)
        
        # Remove old database
        if os.path.exists(manager.db_path):
            os.remove(manager.db_path)
        
        # Setup fresh database
        if not manager.setup_database(skip_import=True):
            print("✗ Setup failed")
            sys.exit(1)
        
        # Import from backup data
        manager.data_dir = args.backup_dir
        success = manager.import_data()
    
    elif args.command == 'full-setup':
        success = manager.full_workflow(with_backup=not args.no_backup)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
