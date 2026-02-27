"""
Utility functions for the flight booking application
"""

from .models import Week, Place, Flight
from datetime import time, timedelta


def createWeekDays():
    """Create week days in the database"""
    week_days = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday')
    ]
    
    for number, name in week_days:
        week, created = Week.objects.get_or_create(
            number=number,
            defaults={'name': name}
        )
        if created:
            print(f"Created week day: {name}")


def addPlaces():
    """Add default places to the database"""
    default_places = [
        {'city': 'Mumbai', 'airport': 'Chhatrapati Shivaji International', 'code': 'BOM', 'country': 'India'},
        {'city': 'Delhi', 'airport': 'Indira Gandhi International', 'code': 'DEL', 'country': 'India'},
        {'city': 'Bangalore', 'airport': 'Kempegowda International', 'code': 'BLR', 'country': 'India'},
        {'city': 'Chennai', 'airport': 'Chennai International', 'code': 'MAA', 'country': 'India'},
        {'city': 'Kolkata', 'airport': 'Netaji Subhas Chandra Bose International', 'code': 'CCU', 'country': 'India'},
        {'city': 'Hyderabad', 'airport': 'Rajiv Gandhi International', 'code': 'HYD', 'country': 'India'},
    ]
    
    for place_data in default_places:
        place, created = Place.objects.get_or_create(
            code=place_data['code'],
            defaults=place_data
        )
        if created:
            print(f"Created place: {place}")


def addDomesticFlights():
    """Add default domestic flights to the database"""
    print("Adding domestic flights...")


def addInternationalFlights():
    """Add default international flights to the database"""
    print("Adding international flights...")
