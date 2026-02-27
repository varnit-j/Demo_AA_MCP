"""
Basic tests to verify test setup is working
"""
import pytest
import django
from django.test import TestCase
from django.contrib.auth import get_user_model

# Ensure Django is configured
django.setup()

User = get_user_model()


@pytest.mark.django_db
class TestBasicSetup:
    """Basic tests to verify setup"""
    
    def test_django_setup(self):
        """Test that Django is properly configured"""
        from django.conf import settings
        assert settings.configured
    
    def test_user_model_import(self):
        """Test that User model can be imported"""
        assert User is not None
    
    def test_database_connection(self):
        """Test database connection works"""
        user_count = User.objects.count()
        assert user_count >= 0  # Should be able to query database
    
    def test_user_creation(self):
        """Test basic user creation"""
        import uuid
        username = f'testuser_{uuid.uuid4().hex[:8]}'
        user = User.objects.create_user(
            username=username,
            email='test@example.com',
            password='testpass123'
        )
        assert user.username == username
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')


def test_simple_math():
    """Simple test to verify pytest is working"""
    assert 1 + 1 == 2


def test_string_operations():
    """Test string operations"""
    test_string = "Hello World"
    assert test_string.lower() == "hello world"
    assert len(test_string) == 11


class TestPythonBasics:
    """Test basic Python functionality"""
    
    def test_list_operations(self):
        """Test list operations"""
        test_list = [1, 2, 3, 4, 5]
        assert len(test_list) == 5
        assert sum(test_list) == 15
        assert max(test_list) == 5
    
    def test_dict_operations(self):
        """Test dictionary operations"""
        test_dict = {'a': 1, 'b': 2, 'c': 3}
        assert len(test_dict) == 3
        assert test_dict['a'] == 1
        assert 'b' in test_dict
    
    def test_exception_handling(self):
        """Test exception handling"""
        with pytest.raises(ZeroDivisionError):
            result = 1 / 0