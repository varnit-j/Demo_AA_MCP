#!/usr/bin/env python3
"""
Complete CSV to Database Import Script
Imports flights data from CSV to a dummy database for testing
"""

import os
import csv
import sqlite3
from datetime import timedelta
import argparse

def create_dummy_database(db_path):
    """Create a dummy database with flight tables"""
    print(f"Creating dummy database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city VARCHAR(64) NOT NULL,
            airport VARCHAR(64) NOT NULL,
            code VARCHAR(3) NOT NULL,
            country VARCHAR(64) NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_number VARCHAR(10),
            airline VARCHAR(64) NOT NULL,
            plane VARCHAR(24) NOT NULL,
            origin_id INTEGER NOT NULL,
            destination_id INTEGER NOT NULL,
            depart_time VARCHAR(8),
            arrival_time VARCHAR(8),
            duration_hours REAL,
            operating_days TEXT,
            economy_fare REAL,
            business_fare REAL,
            first_fare REAL,
            route_type VARCHAR(20),
            distance_category VARCHAR(20),
            FOREIGN KEY (origin_id) REFERENCES places (id),
            FOREIGN KEY (destination_id) REFERENCES places (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Dummy database created successfully")

def get_or_create_place(cursor, city, airport, code, country):
    """Get existing place or create new one"""
    cursor.execute('''
        SELECT id FROM places 
        WHERE city = ? AND airport = ? AND code = ? AND country = ?
    ''', (city, airport, code, country))
    
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute('''
        INSERT INTO places (city, airport, code, country) 
        VALUES (?, ?, ?, ?)
    ''', (city, airport, code, country))
    
    return cursor.lastrowid

def import_csv_to_database(csv_file, db_path, limit=None):
    """Import CSV data to database"""
    print(f"Importing from: {csv_file}")
    print(f"Target database: {db_path}")
    
    if not os.path.exists(csv_file):
        print(f"Error: CSV file not found: {csv_file}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        imported_count = 0
        skipped_count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, 1):
                if limit and imported_count >= limit:
                    print(f"Reached import limit of {limit} records")
                    break
                
                try:
                    # Get or create origin place
                    origin_id = get_or_create_place(
                        cursor,
                        row['Origin City'],
                        row['Origin Airport'], 
                        row['Origin Code'],
                        row['Origin Country']
                    )
                    
                    # Get or create destination place
                    dest_id = get_or_create_place(
                        cursor,
                        row['Destination City'],
                        row['Destination Airport'],
                        row['Destination Code'],
                        row['Destination Country']
                    )
                    
                    # Parse fares
                    economy_fare = float(row['Economy Fare (USD)']) if row['Economy Fare (USD)'] else None
                    business_fare = float(row['Business Fare (USD)']) if row['Business Fare (USD)'] else None
                    first_fare = float(row['First Fare (USD)']) if row['First Fare (USD)'] else None
                    
                    # Parse duration
                    duration_hours = float(row['Duration (Hours)']) if row['Duration (Hours)'] else None
                    
                    # Insert flight
                    cursor.execute('''
                        INSERT INTO flights (
                            flight_number, airline, plane, origin_id, destination_id,
                            depart_time, arrival_time, duration_hours, operating_days,
                            economy_fare, business_fare, first_fare, route_type, distance_category
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row['Flight Number'], row['Airline'], row['Plane'],
                        origin_id, dest_id, row['Departure Time'], row['Arrival Time'],
                        duration_hours, row['Operating Days'], economy_fare, business_fare,
                        first_fare, row['Route Type'], row['Distance Category']
                    ))
                    
                    imported_count += 1
                    
                    if imported_count % 1000 == 0:
                        print(f"Imported {imported_count} flights...")
                        conn.commit()  # Commit every 1000 records
                        
                except Exception as e:
                    print(f"Error importing row {row_num}: {e}")
                    skipped_count += 1
                    continue
        
        conn.commit()
        print(f"Import completed!")
        print(f"Successfully imported: {imported_count} flights")
        print(f"Skipped: {skipped_count} flights")
        
        return True
        
    except Exception as e:
        print(f"Error during import: {e}")
        return False
    finally:
        conn.close()

def verify_import(db_path):
    """Verify the imported data"""
    print(f"Verifying imported data in: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Count records
        cursor.execute('SELECT COUNT(*) FROM places')
        places_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM flights')
        flights_count = cursor.fetchone()[0]
        
        print(f"Places imported: {places_count}")
        print(f"Flights imported: {flights_count}")
        
        # Show sample data
        cursor.execute('SELECT * FROM flights LIMIT 3')
        sample_flights = cursor.fetchall()
        
        print(f"\nSample flights:")
        for flight in sample_flights:
            print(f"  ID: {flight[0]}, Flight: {flight[1]}, Airline: {flight[2]}")
        
    except Exception as e:
        print(f"Error verifying data: {e}")
    finally:
        conn.close()

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='Import flights from CSV to database')
    parser.add_argument('csv_file', help='Path to CSV file to import')
    parser.add_argument('--db', default='test_flights.db', help='Database file path (default: test_flights.db)')
    parser.add_argument('--limit', type=int, help='Limit number of records to import')
    parser.add_argument('--verify', action='store_true', help='Verify imported data')
    
    args = parser.parse_args()
    
    print("CSV to Database Import Tool")
    print("=" * 40)
    
    # Create dummy database
    create_dummy_database(args.db)
    
    # Import data
    success = import_csv_to_database(args.csv_file, args.db, args.limit)
    
    if success and args.verify:
        verify_import(args.db)
    
    if success:
        print(f"\nImport completed successfully!")
        print(f"Database saved as: {args.db}")
    else:
        print(f"\nImport failed!")
if __name__ == "__main__":
    main()
                    