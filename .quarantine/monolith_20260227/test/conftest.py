"""
Pytest configuration and fixtures for AA Flight Booking System tests
"""
import os
import sys
import django
import pytest
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import execute_from_command_line

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capstone.settings')

# Setup Django
django.setup()

from django.test import TestCase, Client
from flight.models import User, Place, Week, Flight, Passenger, Ticket
from apps.loyalty.models import LoyaltyAccount, LoyaltyTier, PointsTransaction
from apps.banking.models import BankCard, PaymentTransaction


@pytest.fixture(scope='session')
def django_db_setup():
    """Setup test database"""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


@pytest.fixture
def client():
    """Django test client"""
    return Client()


@pytest.fixture
def user():
    """Create test user"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def admin_user():
    """Create admin user"""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def place():
    """Create test place"""
    return Place.objects.create(
        city='New York',
        airport='JFK',
        code='NYC',
        country='USA'
    )


@pytest.fixture
def destination_place():
    """Create test destination place"""
    return Place.objects.create(
        city='Los Angeles',
        airport='LAX',
        code='LAX',
        country='USA'
    )


@pytest.fixture
def week():
    """Create test week"""
    return Week.objects.create(number=1)


@pytest.fixture
def flight(place, destination_place, week):
    """Create test flight"""
    return Flight.objects.create(
        origin=place,
        destination=destination_place,
        plane='Boeing 737',
        airline='American Airlines',
        depart_day=week,
        depart_time='10:00',
        duration='5h 30m',
        arrival_time='15:30',
        economy_fare=299.99,
        business_fare=599.99,
        first_fare=999.99
    )


@pytest.fixture
def passenger(user):
    """Create test passenger"""
    return Passenger.objects.create(
        first_name='John',
        last_name='Doe',
        gender='M',
        user=user
    )


@pytest.fixture
def ticket(user, passenger, flight):
    """Create test ticket"""
    return Ticket.objects.create(
        user=user,
        passenger=passenger,
        flight=flight,
        flight_ddate='2024-01-15',
        flight_adate='2024-01-15',
        flight_fare=299.99,
        other_charges=50.00,
        coupon_used='SAVE10',
        coupon_discount=29.99,
        total_fare=320.00,
        seat_class='Economy',
        status='CONFIRMED',
        ref_no='AA123456'
    )


@pytest.fixture
def loyalty_tier():
    """Create test loyalty tier"""
    return LoyaltyTier.objects.create(
        name='gold',
        display_name='Gold',
        min_points_required=5000,
        points_multiplier=1.5,
        redemption_bonus=1.1
    )


@pytest.fixture
def loyalty_account(user, loyalty_tier):
    """Create test loyalty account"""
    return LoyaltyAccount.objects.create(
        user=user,
        current_tier=loyalty_tier,
        total_points_earned=10000,
        current_points_balance=5000,
        lifetime_spending=2500.00
    )


@pytest.fixture
def bank_card():
    """Create test bank card"""
    return BankCard.objects.create(
        card_number='4111111111111111',
        card_holder_name='Test User',
        expiry_month='12',
        expiry_year='2025',
        cvv='123',
        card_type='visa',
        status='active',
        balance=10000.00,
        daily_limit=5000.00
    )


@pytest.fixture
def payment_transaction(bank_card):
    """Create test payment transaction"""
    return PaymentTransaction.objects.create(
        card=bank_card,
        card_number=bank_card.card_number,
        amount=299.99,
        status='approved',
        reference_id='AA123456'
    )


@pytest.fixture
def authenticated_client(client, user):
    """Client with authenticated user"""
    client.force_login(user)
    return client


# Test data factories
class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_multiple_flights(origin, destination, week, count=3):
        """Create multiple test flights"""
        flights = []
        for i in range(count):
            flight = Flight.objects.create(
                origin=origin,
                destination=destination,
                plane=f'Boeing 73{i}',
                airline='American Airlines',
                depart_day=week,
                depart_time=f'{10+i}:00',
                duration=f'{5+i}h 30m',
                arrival_time=f'{15+i}:30',
                economy_fare=299.99 + (i * 50),
                business_fare=599.99 + (i * 100),
                first_fare=999.99 + (i * 200)
            )
            flights.append(flight)
        return flights
    
    @staticmethod
    def create_multiple_places(count=5):
        """Create multiple test places"""
        places_data = [
            ('New York', 'JFK', 'NYC', 'USA'),
            ('Los Angeles', 'LAX', 'LAX', 'USA'),
            ('Chicago', 'ORD', 'CHI', 'USA'),
            ('Miami', 'MIA', 'MIA', 'USA'),
            ('Dallas', 'DFW', 'DFW', 'USA')
        ]
        places = []
        for i in range(min(count, len(places_data))):
            city, airport, code, country = places_data[i]
            place = Place.objects.create(
                city=city,
                airport=airport,
                code=code,
                country=country
            )
            places.append(place)
        return places


@pytest.fixture
def test_data_factory():
    """Test data factory fixture"""
    return TestDataFactory