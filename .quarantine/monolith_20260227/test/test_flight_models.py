"""
Comprehensive unit tests for Flight app models
Testing: User, Place, Week, Flight, Passenger, Ticket models
Coverage goal: 100%
"""
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from datetime import datetime, time, timedelta, date
from decimal import Decimal
import uuid

from flight.models import User, Place, Week, Flight, Passenger, Ticket, GENDER, SEAT_CLASS, TICKET_STATUS


@pytest.mark.django_db
class TestUserModel:
    """Test custom User model"""
    
    def test_user_creation(self):
        """Test basic user creation"""
        username = f'testuser_{uuid.uuid4().hex[:8]}'
        user = User.objects.create_user(
            username=username,
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        assert user.username == username
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.check_password('testpass123')
    
    def test_user_str_representation(self):
        """Test User __str__ method"""
        username = f'testuser_{uuid.uuid4().hex[:8]}'
        user = User.objects.create_user(
            username=username,
            first_name='John',
            last_name='Doe'
        )
        expected = f"{user.pk}: John Doe"
        assert str(user) == expected
    
    def test_user_str_representation_new_user(self):
        """Test User __str__ method for unsaved user"""
        user = User(first_name='John', last_name='Doe')
        assert str(user) == "New: John Doe"


@pytest.mark.django_db
class TestPlaceModel:
    """Test Place model"""
    
    def test_place_creation(self):
        """Test basic place creation"""
        place = Place.objects.create(
            city='New York',
            airport='JFK',
            code='NYC',
            country='USA'
        )
        assert place.city == 'New York'
        assert place.airport == 'JFK'
        assert place.code == 'NYC'
        assert place.country == 'USA'
    
    def test_place_str_representation(self):
        """Test Place __str__ method"""
        place = Place.objects.create(
            city='New York',
            airport='JFK',
            code='NYC',
            country='USA'
        )
        expected = "New York, USA (NYC)"
        assert str(place) == expected


@pytest.mark.django_db
class TestWeekModel:
    """Test Week model"""
    
    def test_week_creation(self):
        """Test basic week creation"""
        week = Week.objects.create(number=1, name='Monday')
        assert week.number == 1
        assert week.name == 'Monday'
    
    def test_week_str_representation(self):
        """Test Week __str__ method"""
        week = Week.objects.create(number=1, name='Monday')
        expected = "Monday (1)"
        assert str(week) == expected


@pytest.mark.django_db
class TestFlightModel:
    """Test Flight model"""
    
    def test_flight_creation(self):
        """Test basic flight creation"""
        origin = Place.objects.create(city='New York', airport='JFK', code='NYC', country='USA')
        destination = Place.objects.create(city='Los Angeles', airport='LAX', code='LAX', country='USA')
        week = Week.objects.create(number=1, name='Monday')