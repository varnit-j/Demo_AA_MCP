#!/usr/bin/env python3
"""
Export all database data to CSV files in the same format as import files.
This allows the database to be backed up and restored across environments.

Usage:
    python export_db_to_csv.py --db db.sqlite3 --output ./
    python export_db_to_csv.py  # Uses default paths
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
    
    print(f"✓ Exported {len(rows)} places to {filename}")
    return len(rows)


def export_flights_to_csv(cursor, output_dir, filename="domestic_flights.csv"):
    """Export all flights with departure days to CSV"""
    # Get flight data with departure week numbers
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
    
    print(f"✓ Exported {len(rows)} flights to {filename}")
    return len(rows)


def export_international_flights_to_csv(cursor, output_dir, filename="international_flights.csv"):
    """Export international flights (for reference - same format as domestic)"""
    # This is a reference file. For now, export the same as domestic_flights
    # In a real scenario, you might filter by route or other criteria
    return export_flights_to_csv(cursor, output_dir, filename)


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
        writer = csv.writer(f)
        writer.writerow([
            'id', 'username', 'first_name', 'last_name', 'email',
            'is_staff', 'is_active', 'date_joined'
        ])
        writer.writerows(rows)
    
    print(f"✓ Exported {len(rows)} users to {filename}")
    return len(rows)


def export_passengers_to_csv(cursor, output_dir, filename="passengers.csv"):
    """Export all passengers to CSV"""
    cursor.execute('''
        SELECT 
            id, first_name, last_name, gender
        FROM flight_passenger
        ORDER BY id
    ''')
    
    rows = cursor.fetchall()
    
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'first_name', 'last_name', 'gender'])
        writer.writerows(rows)
    
    print(f"✓ Exported {len(rows)} passengers to {filename}")
    return len(rows)


def export_tickets_to_csv(cursor, output_dir, filename="tickets.csv"):
    """Export all tickets to CSV"""
    cursor.execute('''
        SELECT 
            id, user_id, ref_no, flight_id, flight_ddate, flight_adate,
            flight_fare, other_charges, coupon_used, coupon_discount,
            total_fare, seat_class, booking_date, mobile, email, status,
            saga_correlation_id, failed_step
        FROM flight_ticket
        ORDER BY id
    ''')
    
    rows = cursor.fetchall()
    
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'id', 'user_id', 'ref_no', 'flight_id', 'flight_ddate', 'flight_adate',
            'flight_fare', 'other_charges', 'coupon_used', 'coupon_discount',
            'total_fare', 'seat_class', 'booking_date', 'mobile', 'email', 'status',
            'saga_correlation_id', 'failed_step'
        ])
        writer.writerows(rows)
    
    print(f"✓ Exported {len(rows)} tickets to {filename}")
    return len(rows)


def export_orders_to_csv(cursor, output_dir, filename="orders.csv"):
    """Export all orders to CSV"""
    try:
        cursor.execute('''
            SELECT 
                id, user_id, order_number, subtotal, tax_amount, fees_amount,
                total_amount, payment_method, points_used, points_value,
                cash_amount, created_at, updated_at, status
            FROM orders_order
            ORDER BY created_at DESC
        ''')
        
        rows = cursor.fetchall()
        
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'id', 'user_id', 'order_number', 'subtotal', 'tax_amount',
                'fees_amount', 'total_amount', 'payment_method', 'points_used',
                'points_value', 'cash_amount', 'created_at', 'updated_at', 'status'
            ])
            writer.writerows(rows)
        
        print(f"✓ Exported {len(rows)} orders to {filename}")
        return len(rows)
    except sqlite3.OperationalError:
        print("⊘ Orders table not found (may not be initialized)")
        return 0


def export_loyalty_accounts_to_csv(cursor, output_dir, filename="loyalty_accounts.csv"):
    """Export loyalty accounts to CSV"""
    try:
        cursor.execute('''
            SELECT 
                id, user_id, current_tier_id, current_points, lifetime_points,
                tier_upgrade_date, last_activity_date, created_at, updated_at
            FROM loyalty_loyaltyaccount
            ORDER BY id
        ''')
        
        rows = cursor.fetchall()
        
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'id', 'user_id', 'current_tier_id', 'current_points', 'lifetime_points',
                'tier_upgrade_date', 'last_activity_date', 'created_at', 'updated_at'
            ])
            writer.writerows(rows)
        
        print(f"✓ Exported {len(rows)} loyalty accounts to {filename}")
        return len(rows)
    except sqlite3.OperationalError:
        print("⊘ Loyalty accounts table not found (may not be initialized)")
        return 0


def export_loyalty_tiers_to_csv(cursor, output_dir, filename="loyalty_tiers.csv"):
    """Export loyalty tiers to CSV"""
    try:
        cursor.execute('''
            SELECT 
                id, name, display_name, min_points_required, points_multiplier,
                redemption_bonus, created_at, updated_at
            FROM loyalty_loyaltytier
            ORDER BY min_points_required
        ''')
        
        rows = cursor.fetchall()
        
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'id', 'name', 'display_name', 'min_points_required', 'points_multiplier',
                'redemption_bonus', 'created_at', 'updated_at'
            ])
            writer.writerows(rows)
        
        print(f"✓ Exported {len(rows)} loyalty tiers to {filename}")
        return len(rows)
    except sqlite3.OperationalError:
        print("⊘ Loyalty tiers table not found (may not be initialized)")
        return 0


def export_bank_cards_to_csv(cursor, output_dir, filename="bank_cards.csv"):
    """Export bank cards to CSV"""
    try:
        cursor.execute('''
            SELECT 
                id, card_number, card_holder_name, expiry_month, expiry_year,
                cvv, card_type, status, balance, daily_limit, created_at, updated_at
            FROM mock_bank_cards
            ORDER BY id
        ''')
        
        rows = cursor.fetchall()
        
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'id', 'card_number', 'card_holder_name', 'expiry_month', 'expiry_year',
                'cvv', 'card_type', 'status', 'balance', 'daily_limit', 'created_at', 'updated_at'
            ])
            writer.writerows(rows)
        
        print(f"✓ Exported {len(rows)} bank cards to {filename}")
        return len(rows)
    except sqlite3.OperationalError:
        print("⊘ Bank cards table not found (may not be initialized)")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Export database to CSV files for backup and migration"
    )
    parser.add_argument(
        '--db',
        default='db.sqlite3',
        help='Path to the database file (default: db.sqlite3)'
    )
    parser.add_argument(
        '--output',
        default='.',
        help='Output directory for CSV files (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Check if database exists
    if not os.path.exists(args.db):
        print(f"✗ Error: Database file not found at {args.db}")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    try:
        conn = sqlite3.connect(args.db)
        cursor = conn.cursor()
        
        print(f"\n📊 Exporting database from: {args.db}")
        print(f"   Output directory: {args.output}")
        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        total_records = 0
        
        # Export core flight data
        total_records += export_places_to_csv(cursor, args.output)
        total_records += export_flights_to_csv(cursor, args.output)
        
        # Export user and booking data
        total_records += export_users_to_csv(cursor, args.output)
        total_records += export_passengers_to_csv(cursor, args.output)
        total_records += export_tickets_to_csv(cursor, args.output)
        
        # Export optional app data
        total_records += export_orders_to_csv(cursor, args.output)
        total_records += export_loyalty_tiers_to_csv(cursor, args.output)
        total_records += export_loyalty_accounts_to_csv(cursor, args.output)
        total_records += export_bank_cards_to_csv(cursor, args.output)
        
        conn.close()
        
        print(f"\n✓ Export completed successfully!")
        print(f"  Total records exported: {total_records}")
        print(f"  Output location: {os.path.abspath(args.output)}")
        
    except Exception as e:
        print(f"✗ Error during export: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
