"""
Tests for flight/views.py – flight search, bookings, ticket_data
These require Week + Place DB fixtures.
"""
import pytest
import uuid
from datetime import datetime
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from flight.models import Place, Week, Flight, Ticket

User = get_user_model()


# ─── DB Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def test_places():
    """Create origin and destination places"""
    origin, _ = Place.objects.get_or_create(
        code="SRC",
        defaults={"city": "Source City", "airport": "Source Airport", "country": "USA"},
    )
    dest, _ = Place.objects.get_or_create(
        code="DST",
        defaults={"city": "Dest City", "airport": "Dest Airport", "country": "USA"},
    )
    return origin, dest


@pytest.fixture
def all_weeks():
    """Create all 7 week days"""
    days = [
        (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"),
        (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
    ]
    weeks = {}
    for num, name in days:
        w, _ = Week.objects.get_or_create(number=num, defaults={"name": name})
        weeks[num] = w
    return weeks


@pytest.fixture
def test_flights(test_places, all_weeks):
    """Create American Airlines flights for every day of the week"""
    origin, dest = test_places
    created = []
    for day_num, week in all_weeks.items():
        tag = uuid.uuid4().hex[:4]
        f = Flight.objects.create(
            flight_number=f"AA{tag}",
            airline="American Airlines",
            plane="Boeing 737",
            origin=origin,
            destination=dest,
            depart_time="09:00:00",
            arrival_time="12:00:00",
            economy_fare=200,
            business_fare=500,
            first_fare=900,
        )
        f.depart_day.set([week])
        created.append(f)
    # Also create return-direction flights
    for day_num, week in all_weeks.items():
        tag = uuid.uuid4().hex[:4]
        r = Flight.objects.create(
            flight_number=f"AA{tag}R",
            airline="American Airlines",
            plane="Boeing 737",
            origin=dest,
            destination=origin,
            depart_time="14:00:00",
            arrival_time="17:00:00",
            economy_fare=210,
            business_fare=510,
            first_fare=910,
        )
        r.depart_day.set([week])
        created.append(r)
    return created


def make_user(prefix="sv"):
    tag = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"{prefix}_{tag}",
        password="testpass123",
    )


def _pick_future_monday():
    """Return the next Monday's date string YYYY-MM-DD"""
    today = datetime.now().date()
    days_until_monday = (7 - today.weekday()) % 7 or 7
    from datetime import timedelta
    monday = today + timedelta(days=days_until_monday)
    return str(monday)


def _pick_future_friday():
    """Return a date far enough out to reliably be a Friday"""
    today = datetime.now().date()
    from datetime import timedelta
    days_until_friday = (4 - today.weekday()) % 7 or 7
    friday = today + timedelta(days=days_until_friday)
    return str(friday)


# ─── Flight Search View ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFlightSearchView:
    def test_economy_one_way_returns_200(self, test_flights):
        c = Client()
        monday = _pick_future_monday()
        resp = c.get(reverse("flight"), {
            "Origin": "SRC", "Destination": "DST",
            "TripType": "1", "DepartDate": monday, "SeatClass": "economy",
        })
        assert resp.status_code == 200

    def test_business_one_way_returns_200(self, test_flights):
        c = Client()
        monday = _pick_future_monday()
        resp = c.get(reverse("flight"), {
            "Origin": "SRC", "Destination": "DST",
            "TripType": "1", "DepartDate": monday, "SeatClass": "business",
        })
        assert resp.status_code == 200

    def test_first_one_way_returns_200(self, test_flights):
        c = Client()
        monday = _pick_future_monday()
        resp = c.get(reverse("flight"), {
            "Origin": "SRC", "Destination": "DST",
            "TripType": "1", "DepartDate": monday, "SeatClass": "first",
        })
        assert resp.status_code == 200

    def test_economy_round_trip_returns_200(self, test_flights):
        c = Client()
        monday = _pick_future_monday()
        friday = _pick_future_friday()
        if friday <= monday:
            from datetime import timedelta, date
            friday = str(date.fromisoformat(monday) + timedelta(days=4))
        resp = c.get(reverse("flight"), {
            "Origin": "SRC", "Destination": "DST",
            "TripType": "2", "DepartDate": monday,
            "ReturnDate": friday, "SeatClass": "economy",
        })
        assert resp.status_code == 200

    def test_business_round_trip_returns_200(self, test_flights):
        c = Client()
        monday = _pick_future_monday()
        from datetime import timedelta, date
        return_date = str(date.fromisoformat(monday) + timedelta(days=3))
        resp = c.get(reverse("flight"), {
            "Origin": "SRC", "Destination": "DST",
            "TripType": "2", "DepartDate": monday,
            "ReturnDate": return_date, "SeatClass": "business",
        })
        assert resp.status_code == 200

    def test_first_round_trip_returns_200(self, test_flights):
        c = Client()
        monday = _pick_future_monday()
        from datetime import timedelta, date
        return_date = str(date.fromisoformat(monday) + timedelta(days=5))
        resp = c.get(reverse("flight"), {
            "Origin": "SRC", "Destination": "DST",
            "TripType": "2", "DepartDate": monday,
            "ReturnDate": return_date, "SeatClass": "first",
        })
        assert resp.status_code == 200

    def test_flights_in_context(self, test_flights):
        c = Client()
        monday = _pick_future_monday()
        resp = c.get(reverse("flight"), {
            "Origin": "SRC", "Destination": "DST",
            "TripType": "1", "DepartDate": monday, "SeatClass": "economy",
        })
        assert resp.status_code == 200
        ctx = resp.context
        assert "flights" in ctx
        assert "origin" in ctx
        assert "destination" in ctx

    def test_round_trip_context_has_flights2(self, test_flights):
        c = Client()
        monday = _pick_future_monday()
        from datetime import timedelta, date
        return_date = str(date.fromisoformat(monday) + timedelta(days=4))
        resp = c.get(reverse("flight"), {
            "Origin": "SRC", "Destination": "DST",
            "TripType": "2", "DepartDate": monday,
            "ReturnDate": return_date, "SeatClass": "economy",
        })
        assert resp.status_code == 200
        assert "flights2" in resp.context


# ─── Bookings View ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBookingsViewDetailed:
    def test_shows_confirmed_tickets(self, test_places, test_flights):
        u = make_user("bk")
        origin, dest = test_places
        flight = test_flights[0]
        Ticket.objects.create(
            user=u, ref_no=uuid.uuid4().hex[:6].upper(),
            flight=flight,
            status="CONFIRMED",
            seat_class="economy",
            booking_date=datetime.now(),
        )
        c = Client()
        c.force_login(u)
        resp = c.get(reverse("bookings"))
        assert resp.status_code == 200

    def test_shows_failed_tickets(self, test_places, test_flights):
        u = make_user("bkf")
        flight = test_flights[0]
        Ticket.objects.create(
            user=u, ref_no=uuid.uuid4().hex[:6].upper(),
            flight=flight,
            status="FAILED",
            seat_class="economy",
        )
        c = Client()
        c.force_login(u)
        resp = c.get(reverse("bookings"))
        assert resp.status_code == 200


# ─── Ticket Data API ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTicketDataView:
    def test_returns_ticket_json(self, test_places, test_flights):
        u = make_user("td")
        flight = test_flights[0]
        ref = uuid.uuid4().hex[:6].upper()
        Ticket.objects.create(
            user=u, ref_no=ref, flight=flight,
            status="CONFIRMED", seat_class="economy",
        )
        c = Client()
        resp = c.get(reverse("ticketdata", kwargs={"ref": ref}))
        assert resp.status_code == 200
        data = resp.json()
        assert data["ref"] == ref
        assert data["status"] == "CONFIRMED"
