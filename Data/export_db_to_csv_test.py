#!/usr/bin/env python3
"""
Export all database data to CSV files in the same format as import files.
This allows the database to be backed up and restored across environments.

Usage:
    python export_db_to_csv_test.py --db db.sqlite3 --output ./
    python export_db_to_csv_test.py  # Uses default paths
"""

import os
import sys
import csv
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path


def export_places_to_csv(cursor, output_dir, filename="airports.csv"):
    """Export all places to CSV"""
    cursor.execute('SELECT city, airport, code, country FROM flight_place ORDER BY id')
    rows = cursor.fetchall()
    
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['city', 'airport', 'code', 'country'])
        writer.writerows(rows)
    
    print(f"[OK] Exported {len(rows)} places to {filename}")
    return len(rows)


def export_flights_to_csv(cursor, output_dir, filename="domestic_flights.csv"):
    """Export all flights with departure days to CSV"""
    cursor.execute('''
        SELECT 
            f.id,
            origin_place.code as origin,
            dest_place.code as destination,
            f.depart_time,
            w.number as depart_weekday,
            f.duration,
            f.arrival_time,
            w.number as arrival_weekday,
            f.flight_number,
            SUBSTR(f.airline, 1, 2) as airline_code,
            f.airline,
            f.economy_fare,
            f.business_fare,
            f.first_fare
        FROM flight_flight f
        JOIN flight_place origin_place ON f.origin_id = origin_place.id
        JOIN flight_place dest_place ON f.destination_id = dest_place.id
        LEFT JOIN flight_flight_depart_day fd ON f.id = fd.flight_id
        LEFT JOIN flight_week w ON fd.week_id = w.id
        ORDER BY f.id, w.number
    ''')
    
    rows = cursor.fetchall()
    
    # Create index for rows
    indexed_rows = []
    for idx, row in enumerate(rows):
        indexed_rows.append((idx,) + row[1:])  # Add index as first column
    
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            '', 'origin', 'destination', 'depart_time', 'depart_weekday',
            'duration', 'arrival_time', 'arrival_weekday', 'flight_no',
            'airline_code', 'airline', 'economy_fare', 'business_fare', 'first_fare'
        ])
        writer.writerows(indexed_rows)
    
    print(f"[OK] Exported {len(rows)} flights to {filename}")
    return len(rows)


def export_users_to_csv(cursor, output_dir, filename="users.csv"):
    """Export all users to CSV"""
    cursor.execute('''
        SELECT 
            id, username, first_name, last_name, email, 
            is_staff, is_active, date_joined
        FROM auth_user
        ORDER BY id
    ''')
    
    rows = cursor.fetchall()
    
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        pass