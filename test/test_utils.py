"""
Tests for flight/utils.py
Coverage target: 100% of utility functions
"""
import pytest
from django.test import TestCase


@pytest.mark.django_db
class TestCreateWeekDays:
    def test_creates_7_days(self):
        from flight.utils import createWeekDays
        from flight.models import Week
        Week.objects.all().delete()
        createWeekDays()
        assert Week.objects.count() == 7

    def test_idempotent_on_second_call(self):
        from flight.utils import createWeekDays
        from flight.models import Week
        createWeekDays()
        createWeekDays()  # second call should not duplicate
        assert Week.objects.count() == 7

    def test_day_names_correct(self):
        from flight.utils import createWeekDays
        from flight.models import Week
        Week.objects.all().delete()
        createWeekDays()
        assert Week.objects.filter(name='Monday').exists()
        assert Week.objects.filter(name='Sunday').exists()


@pytest.mark.django_db
class TestAddPlaces:
    def test_creates_default_places(self):
        from flight.utils import addPlaces
        from flight.models import Place
        Place.objects.all().delete()
        addPlaces()
        assert Place.objects.count() >= 6

    def test_places_have_codes(self):
        from flight.utils import addPlaces
        from flight.models import Place
        Place.objects.all().delete()
        addPlaces()
        assert Place.objects.filter(code='BOM').exists()
        assert Place.objects.filter(code='DEL').exists()

    def test_idempotent(self):
        from flight.utils import addPlaces
        from flight.models import Place
        addPlaces()
        count_first = Place.objects.count()
        addPlaces()
        assert Place.objects.count() == count_first


@pytest.mark.django_db
class TestAddDomesticFlights:
    def test_runs_without_error(self, capsys):
        from flight.utils import addDomesticFlights
        addDomesticFlights()  # Should just print and return
        captured = capsys.readouterr()
        assert "domestic" in captured.out.lower()


@pytest.mark.django_db
class TestAddInternationalFlights:
    def test_runs_without_error(self, capsys):
        from flight.utils import addInternationalFlights
        addInternationalFlights()
        captured = capsys.readouterr()
        assert "international" in captured.out.lower()
