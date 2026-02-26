#!/usr/bin/env python3
"""
Import flights data from CSV to database
Can connect to different databases for testing without affecting current DB
"""

import os
import sys
import csv
import sqlite3
from datetime import datetime, time, timedelta
import argparse

def create_dummy_database(db_path):
    """Create a dummy database with the same structure as the main database"""
    print(f"Creating dummy database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create Places table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flight_place (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city VARCHAR(64) NOT NULL,
            airport VARCHAR(64) NOT NULL,
            code VARCHAR(3) NOT NULL,
            country VARCHAR(64) NOT NULL
        )
    ''')
    
    # Create Week table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flight_week (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number INTEGER NOT NULL,
            name VARCHAR(16) NOT NULL
        )
    ''')
    
    # Create Flight table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flight_flight (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin_id INTEGER NOT NULL,
            destination_id INTEGER NOT NULL,
            depart_time TIME NOT NULL,
            duration TEXT,
            arrival_time TIME NOT NULL,
            plane VARCHAR(24) NOT NULL,
            airline VARCHAR(64) NOT NULL,
            flight_number VARCHAR(10),
            economy_fare REAL,
            business_fare REAL,
            first_fare REAL,
            FOREIGN KEY (origin_id) REFERENCES flight_place (id),
            FOREIGN KEY (destination_id) REFERENCES flight_place (id)
        )
    ''')
    
    # Create Flight-Week relationship table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flight_flight_depart_day (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_id INTEGER NOT NULL,
            week_id INTEGER NOT NULL,
            FOREIGN KEY (flight_id) REFERENCES flight_flight (id),
            FOREIGN KEY (week_id) REFERENCES flight_week (id)
        )
    ''')
    
    # Insert week data
    weeks = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'),
        (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    ]
    
    cursor.executemany('INSERT OR IGNORE INTO flight_week (number, name) VALUES (?, ?)', weeks)
    
    conn.commit()
    conn.close()
    print("Dummy database structure created successfully")

def get_or_create_place(cursor, city, airport, code, country):
    """Get existing place or create new one"""
    cursor.execute('''
        SELECT id FROM flight_place 
        WHERE city = ? AND airport = ? AND code = ? AND country = ?
    ''', (city, airport, code, country))
    
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute('''
        INSERT INTO flight_place (city, airport, code, country) 
        VALUES (?, ?, ?, ?)
    ''', (city, airport, code, country))
    
    return cursor.lastrowid

def get_week_id(cursor, day_name):
    """Get week ID by day name"""
    cursor.execute('SELECT id FROM flight_week WHERE name = ?', (day_name,))
    result = cursor.fetchone()
    return result[0] if result else None