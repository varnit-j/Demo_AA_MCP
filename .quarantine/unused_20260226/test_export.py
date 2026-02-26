#!/usr/bin/env python3
"""
Simple test to check if export_db_to_csv.py creates exact database copies
"""

import os
import sqlite3
import csv

def analyze_export_script():
    """Analyze the export_db_to_csv.py script functionality"""
    
    print("=== ANALYSIS OF export_db_to_csv.py ===\n")
    
    # Check if database exists
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"[ERROR] Database file not found: {db_path}")
        return False
    
    print(f"[OK] Database found: {db_path}")
    
    # Connect to database and analyze tables
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"\n[INFO] Database contains {len(tables)} tables:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} records")
        
        # Check specific tables that the export script handles
        export_tables = {
            'flight_place': 'Places/Airports',
            'flight_flight': 'Flights', 
            'auth_user': 'Users',
            'flight_passenger': 'Passengers',
            'flight_ticket': 'Tickets'
        }
        
        print(f"\n[INFO] Tables handled by export script:")
        total_exportable_records = 0
        
        for table_name, description in export_tables.items():
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                total_exportable_records += count
                print(f"  - {description} ({table_name}): {count} records")
            except sqlite3.OperationalError:
                print(f"  - {description} ({table_name}): Table not found")
        
        print(f"\n[SUMMARY] Total exportable records: {total_exportable_records}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Database analysis failed: {e}")
        return False

def check_export_completeness():
    """Check if the export script covers all database data"""
    
    print("\n=== EXPORT COMPLETENESS ANALYSIS ===\n")
    
    # Read the export script to analyze what it exports
    script_path = "Data/export_db_to_csv.py"
    if not os.path.exists(script_path):
        print(f"[ERROR] Export script not found: {script_path}")
        return False
    
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check what tables are exported
    exported_tables = []
    if 'flight_place' in content:
        exported_tables.append('Places (flight_place)')
    if 'flight_flight' in content:
        exported_tables.append('Flights (flight_flight)')
    if 'auth_user' in content:
        exported_tables.append('Users (auth_user)')
    if 'flight_passenger' in content:
        exported_tables.append('Passengers (flight_passenger)')
    if 'flight_ticket' in content:
        exported_tables.append('Tickets (flight_ticket)')
    if 'orders_order' in content:
        exported_tables.append('Orders (orders_order)')
    if