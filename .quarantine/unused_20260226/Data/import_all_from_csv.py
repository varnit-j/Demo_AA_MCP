#!/usr/bin/env python3
"""
Comprehensive database import script for Django models.
Imports all CSV data including flights, users, tickets, orders, and loyalty data.

Usage:
    python import_all_from_csv.py --data ./Data  # Uses Django ORM
"""

import os
import sys
import csv
import django
import argparse
from pathlib import Path
from datetime import datetime, time, timedelta


# Setup Django
def setup_django():
    """Configure Django settings"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capstone.settings')
    django.setup()


def import_places(data_dir):
    """Import airports/places from CSV"""
    from flight.models import Place
    
    csv_file = os.path.join(data_dir, 'airports.csv')
    
    if not os.path.exists(csv_file):
        print(f"⚠ airports.csv not found at {csv_file}")
        return 0
    
    count = 0
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            place, created = Place.objects.get_or_create(
                city=row['city'],
                airport=row['airport'],
                code=row['code'],
                country=row['country']
            )
            if created:
                count += 1
    
    print(f"✓ Imported {count} places")
    return count


def parse_duration(duration_str):
    """Parse duration string (HH:MM:SS) to timedelta"""
    if not duration_str:
        return None
    try:
        parts = duration_str.split(':')
        return timedelta(hours=int(parts[0]), minutes=int(parts[1]), seconds=int(parts[2]))
    except:
        return None


def import_flights(data_dir):
    """Import flights from CSV"""
    from flight.models import Flight, Place, Week
    
    csv_file = os.path.join(data_dir, 'domestic_flights.csv')
    
    if not os.path.exists(csv_file):
        print(f"⚠ domestic_flights.csv not found at {csv_file}")
        return 0
    
    count = 0
    flight_dict = {}  # To track flights and their departure days
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                origin = Place.objects.get(code=row['origin'])
                destination = Place.objects.get(code=row['destination'])
                
                # Create a unique key for the flight
                flight_key = (
                    origin.id,
                    destination.id,
                    row['depart_time'],
                    row['arrival_time'],
                    row['airline'],
                    row['flight_no']
                )
                
                # Get or create flight
                flight, created = Flight.objects.get_or_create(
                    origin=origin,
                    destination=destination,
                    depart_time=row['depart_time'],
                    arrival_time=row['arrival_time'],
                    plane=row.get('plane', 'Unknown'),
                    airline=row['airline'],
                    flight_number=row.get('flight_no', ''),
                    defaults={
                        'duration': parse_duration(row.get('duration')),
                        'economy_fare': float(row['economy_fare']) if row.get('economy_fare') else None,
                        'business_fare': float(row['business_fare']) if row.get('business_fare') else None,
                        'first_fare': float(row['first_fare']) if row.get('first_fare') else None,
                    }
                )
                
                if created:
                    count += 1
                
                # Add departure day if not already added
                if flight_key not in flight_dict:
                    flight_dict[flight_key] = flight
                    
                    # Add departure week
                    if row.get('depart_weekday'):
                        try:
                            week = Week.objects.get(number=int(row['depart_weekday']))
                            flight.depart_day.add(week)
                        except Week.DoesNotExist:
                            pass
                
            except Place.DoesNotExist:
                print(f"⚠ Place not found: {row.get('origin')} or {row.get('destination')}")
            except Exception as e:
                print(f"⚠ Error importing flight: {e}")
    
    print(f"✓ Imported {count} flights")
    return count


def import_users(data_dir):
    """Import users from CSV"""
    from django.contrib.auth.models import User
    
    csv_file = os.path.join(data_dir, 'users.csv')
    
    if not os.path.exists(csv_file):
        print(f"⚠ users.csv not found (optional)")
        return 0
    
    count = 0
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            user, created = User.objects.get_or_create(
                username=row['username'],
                defaults={
                    'first_name': row.get('first_name', ''),
                    'last_name': row.get('last_name', ''),
                    'email': row.get('email', ''),
                    'is_staff': row.get('is_staff', 'False').lower() == 'true',
                    'is_active': row.get('is_active', 'True').lower() == 'true',
                }
            )
            if created:
                count += 1
    
    print(f"✓ Imported {count} users")
    return count


def import_passengers(data_dir):
    """Import passengers from CSV"""
    from flight.models import Passenger
    
    csv_file = os.path.join(data_dir, 'passengers.csv')
    
    if not os.path.exists(csv_file):
        print(f"⚠ passengers.csv not found (optional)")
        return 0
    
    count = 0
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            passenger, created = Passenger.objects.get_or_create(
                first_name=row.get('first_name', ''),
                last_name=row.get('last_name', ''),
                gender=row.get('gender', ''),
            )
            if created:
                count += 1
    
    print(f"✓ Imported {count} passengers")
    return count


def import_loyalty_tiers(data_dir):
    """Import loyalty tiers from CSV"""
    try:
        from loyalty.models import LoyaltyTier
        from decimal import Decimal
        
        csv_file = os.path.join(data_dir, 'loyalty_tiers.csv')
        
        if not os.path.exists(csv_file):
            print(f"⚠ loyalty_tiers.csv not found (optional)")
            return 0
        
        count = 0
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tier, created = LoyaltyTier.objects.get_or_create(
                    name=row['name'],
                    defaults={
                        'display_name': row.get('display_name', ''),
                        'min_points_required': int(row.get('min_points_required', 0)),
                        'points_multiplier': Decimal(row.get('points_multiplier', '1.00')),
                        'redemption_bonus': Decimal(row.get('redemption_bonus', '1.00')),
                    }
                )
                if created:
                    count += 1
        
        print(f"✓ Imported {count} loyalty tiers")
        return count
    except ImportError:
        print(f"⚠ Loyalty app not available")
        return 0


def import_loyalty_accounts(data_dir):
    """Import loyalty accounts from CSV"""
    try:
        from loyalty.models import LoyaltyAccount
        from django.contrib.auth.models import User
        
        csv_file = os.path.join(data_dir, 'loyalty_accounts.csv')
        
        if not os.path.exists(csv_file):
            print(f"⚠ loyalty_accounts.csv not found (optional)")
            return 0
        
        count = 0
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    user = User.objects.get(id=row['user_id'])
                    account, created = LoyaltyAccount.objects.get_or_create(
                        user=user,
                        defaults={
                            'current_points': int(row.get('current_points', 0)),
                            'lifetime_points': int(row.get('lifetime_points', 0)),
                        }
                    )
                    if created:
                        count += 1
                except User.DoesNotExist:
                    pass
        
        print(f"✓ Imported {count} loyalty accounts")
        return count
    except ImportError:
        print(f"⚠ Loyalty app not available")
        return 0


def import_bank_cards(data_dir):
    """Import bank cards from CSV"""
    try:
        from banking.models import BankCard
        from decimal import Decimal
        
        csv_file = os.path.join(data_dir, 'bank_cards.csv')
        
        if not os.path.exists(csv_file):
            print(f"⚠ bank_cards.csv not found (optional)")
            return 0
        
        count = 0
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                card, created = BankCard.objects.get_or_create(
                    card_number=row['card_number'],
                    defaults={
                        'card_holder_name': row.get('card_holder_name', ''),
                        'expiry_month': row.get('expiry_month', ''),
                        'expiry_year': row.get('expiry_year', ''),
                        'cvv': row.get('cvv', ''),
                        'card_type': row.get('card_type', 'visa'),
                        'status': row.get('status', 'active'),
                        'balance': Decimal(row.get('balance', '0.00')),
                        'daily_limit': Decimal(row.get('daily_limit', '5000.00')),
                    }
                )
                if created:
                    count += 1
        
        print(f"✓ Imported {count} bank cards")
        return count
    except ImportError:
        print(f"⚠ Banking app not available")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Import all data from CSV files using Django ORM"
    )
    parser.add_argument(
        '--data',
        default='./Data',
        help='Data/CSV directory (default: ./Data)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("IMPORTING DATA FROM CSV FILES")
    print("="*70)
    
    # Setup Django
    try:
        setup_django()
        print("✓ Django configured successfully")
    except Exception as e:
        print(f"✗ Failed to configure Django: {e}")
        sys.exit(1)
    
    total_records = 0
    
    print(f"\n📁 Data directory: {args.data}\n")
    
    # Import data in order of dependencies
    total_records += import_places(args.data)
    total_records += import_flights(args.data)
    total_records += import_users(args.data)
    total_records += import_passengers(args.data)
    total_records += import_loyalty_tiers(args.data)
    total_records += import_loyalty_accounts(args.data)
    total_records += import_bank_cards(args.data)
    
    print(f"\n✓ Import completed!")
    print(f"  Total records imported: {total_records}")


if __name__ == '__main__':
    main()
