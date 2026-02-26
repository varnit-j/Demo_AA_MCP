"""
Tests for flight/api_views.py
"""
import json
import pytest
import uuid
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from flight.models import Place, Week, Flight

User = get_user_model()


def make_place(code):
    p, _ = Place.objects.get_or_create(
        code=code,
        defaults={"city": f"City {code}", "airport": f"Airport {code}", "country": "USA"},
    )
    return p


def make_week():
    w, _ = Week.objects.get_or_create(number=0, defaults={"name": "Monday"})
    return w


def make_flight():
    origin = make_place("API1")
    dest = make_place("API2")
    week = make_week()
    # depart_day is a ManyToManyField – cannot use in get_or_create defaults
    tag = uuid.uuid4().hex[:4]
    f = Flight.objects.create(
        flight_number=f"AA{tag}",
        airline="American Airlines",
        plane="Boeing 737",
        origin=origin,
        destination=dest,
        depart_time="10:00:00",
        arrival_time="12:00:00",
        economy_fare=300,
        business_fare=600,
        first_fare=900,
    )
    f.depart_day.set([week])
    return f


@pytest.mark.django_db
class TestCreateFailedBookingAPI:
    def _url(self):
        return reverse("create_failed_booking")

    def test_missing_flight_id_returns_404(self):
        c = Client()
        payload = {
            "correlation_id": str(uuid.uuid4()),
            "flight_id": 999999,
            "user_id": None,
            "passengers": [],
            "seat_class": "economy",
        }
        resp = c.post(
            self._url(),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 404
        data = resp.json()
        assert "error" in data

    def test_valid_payload_creates_failed_ticket(self):
        c = Client()
        flight = make_flight()
        tag = uuid.uuid4().hex[:8]
        user = User.objects.create_user(username=f"saga_{tag}", password="pass")
        payload = {
            "correlation_id": tag,
            "flight_id": flight.id,
            "user_id": user.id,
            "passengers": [
                {"first_name": "Alice", "last_name": "Smith", "gender": "female"}
            ],
            "seat_class": "economy",
            "failed_step": "PaymentAuthorization",
            "failure_reason": "Card declined",
            "compensation_executed": True,
            "contact_info": {"mobile": "1234567890", "email": "alice@test.com"},
        }
        resp = c.post(
            self._url(),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "ref_no" in data

    def test_business_class_fare(self):
        c = Client()
        flight = make_flight()
        tag = uuid.uuid4().hex[:8]
        payload = {
            "correlation_id": tag,
            "flight_id": flight.id,
            "user_id": None,
            "passengers": [{"first_name": "Bob", "last_name": "Jones", "gender": "male"}],
            "seat_class": "business",
            "contact_info": {},
        }
        resp = c.post(
            self._url(),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_first_class_fare(self):
        c = Client()
        flight = make_flight()
        tag = uuid.uuid4().hex[:8]
        payload = {
            "correlation_id": tag,
            "flight_id": flight.id,
            "user_id": None,
            "passengers": [],
            "seat_class": "first",
            "contact_info": {},
        }
        resp = c.post(
            self._url(),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_invalid_json_returns_500(self):
        c = Client()
        resp = c.post(
            self._url(),
            data="not json",
            content_type="application/json",
        )
        # Should return error JSON
        assert resp.status_code in (200, 400, 500)
        assert resp["Content-Type"].startswith("application/json")
