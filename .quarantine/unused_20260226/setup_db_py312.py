#!/usr/bin/env python3
"""
Complete database setup script for Python 3.12 environment.
This script:
1. Creates Django migrations
2. Initializes the database
3. Imports all data from CSV files
4. Sets up default configurations

Usage:
    python setup_db_py312.py  # Uses default paths
    python setup_db_py312.py --db mydb.sqlite3 --data ./data/
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Execute a shell command and report status"""
    print(f"\n▶ {description or ' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"✗ Error: {result.stderr}")
            return False
        print(f"✓ {description or 'Command executed'} successfully")
        return True
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"\n📌 Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 12):
        print("⚠ Warning: Python 3.12 or higher is recommended for optimal compatibility")
    else:
        print("✓ Python version is compatible")


def check_django_setup(django_project_dir):
    """Check if Django project structure exists"""
    required_files = [
        'manage.py',
        'capstone/settings.py',
        'capstone/__init__.py',
    ]
    
    print("\n📁 Checking Django project structure...")
    for file in required_files:
        path = os.path.join(django_project_dir, file)
        if os.path.exists(path):
            print(f"  ✓ Found: {file}")
        else:
            print(f"  ✗ Missing: {file}")
            return False
    
    return True


def install_requirements(django_project_dir):
    """Install Python requirements"""
    req_file = os.path.join(django_project_dir, 'requirements.txt')
    
    if not os.path.exists(req_file):
        print(f"⚠ requirements.txt not found at {req_file}")
        return False
    
    print("\n📦 Installing Python dependencies...")
    return run_command(
        f'pip install -r "{req_file}" --upgrade',
        "Installing requirements"
    )


def migrate_database(django_project_dir, db_path):
    """Run Django migrations"""
    print("\n🔄 Running Django migrations...")
    
    os.chdir(django_project_dir)
    
    # Make migrations
    if not run_command(
        f'python manage.py makemigrations',
        "Creating migrations"
    ):
        print("⚠ Warning: makemigrations completed with warnings")
    
    # Apply migrations
    if not run_command(
        f'python manage.py migrate --no-input',
        "Applying migrations"
    ):
        print("✗ Error: Failed to apply migrations")
        return False
    
    return True


def import_data(django_project_dir, data_dir):
    """Import data from CSV files"""
    print(f"\n📥 Importing data from CSV files in {data_dir}...")
    
    os.chdir(django_project_dir)
    
    # Import flights and places
    import_script = os.path.join(data_dir, 'import_flights_from_csv.py')
    
    if os.path.exists(import_script):
        if not run_command(
            f'python "{import_script}" --db "{os.path.join(django_project_dir, "db.sqlite3")}"',
            "Importing flights data"
        ):
            print("⚠ Warning: Flight import completed with issues")
    else:
        print(f"⚠ Import script not found at {import_script}")
    
    return True


def create_superuser(django_project_dir):
    """Create a default superuser"""
    print("\n👤 Creating superuser...")
    
    os.chdir(django_project_dir)
    
    # Check if superuser already exists
    check_cmd = (
        'python -c "from django.contrib.auth.models import User; '
        'print(User.objects.filter(username=\'admin\').exists())"'
    )
    
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    
    if 'True' in result.stdout:
        print("✓ Superuser 'admin' already exists")
        return True
    
    # Create superuser with predefined password
    create_cmd = (
        'python manage.py shell -c '
        '"from django.contrib.auth.models import User; '
        'User.objects.create_superuser(\'admin\', \'admin@example.com\', \'admin123\')"'
    )
    
    return run_command(create_cmd, "Creating superuser 'admin'")


def verify_database(django_project_dir, db_path):
    """Verify database is properly set up"""
    print("\n✅ Verifying database...")
    
    if not os.path.exists(db_path):
        print(f"✗ Database file not found at {db_path}")
        return False
    
    print(f"✓ Database exists at {db_path}")
    print(f"✓ Database size: {os.path.getsize(db_path) / (1024*1024):.2f} MB")
    
    return True


def generate_summary(django_project_dir, db_path, data_dir):
    """Generate setup summary"""
    print("\n" + "="*70)
    print("DATABASE SETUP SUMMARY")
    print("="*70)
    print(f"Django Project:    {django_project_dir}")
    print(f"Database File:     {db_path}")
    print(f"Data Directory:    {data_dir}")
    print(f"Database Size:     {os.path.getsize(db_path) / (1024*1024):.2f} MB")
    print("\nDefault Credentials:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\nNext Steps:")
    print("  1. Start the development server: python manage.py runserver")
    print("  2. Access admin panel: http://localhost:8000/admin/")
    print("  3. Access application: http://localhost:8000/")
    print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="Complete database setup for Python 3.12"
    )
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
    parser.add_argument(
        '--skip-requirements',
        action='store_true',
        help='Skip installing requirements'
    )
    parser.add_argument(
        '--skip-import',
        action='store_true',
        help='Skip importing CSV data'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("FLIGHT BOOKING DATABASE SETUP - Python 3.12")
    print("="*70)
    
    # Check Python version
    check_python_version()
    
    # Verify Django setup
    if not check_django_setup(args.django_dir):
        print("\n✗ Django project structure verification failed")
        sys.exit(1)
    
    # Install requirements
    if not args.skip_requirements:
        if not install_requirements(args.django_dir):
            print("\n⚠ Warning: Some requirements may not have been installed")
    
    # Run migrations
    if not migrate_database(args.django_dir, args.db):
        print("\n✗ Database migration failed")
        sys.exit(1)
    
    # Import CSV data
    if not args.skip_import:
        if not import_data(args.django_dir, args.data):
            print("\n⚠ Warning: Data import completed with issues")
    
    # Create superuser
    if not create_superuser(args.django_dir):
        print("\n⚠ Warning: Superuser creation may have issues")
    
    # Verify database
    if not verify_database(args.django_dir, args.db):
        print("\n✗ Database verification failed")
        sys.exit(1)
    
    # Generate summary
    generate_summary(args.django_dir, args.db, args.data)
    
    print("\n✓ Setup completed successfully!")
    sys.exit(0)


if __name__ == '__main__':
    main()
