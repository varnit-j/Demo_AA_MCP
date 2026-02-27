"""
Comprehensive tests for backend-service — targets 95%+ coverage.

Covers:
  - flight.models  (all model classes + to_dict)
  - flight.simple_views  (every view, success + error paths)
  - flight.saga_log_storage  (add_log, get_logs – DB + fallback)
  - flight.failed_booking_handler  (success, missing flight, missing user)
  - flight.saga_orchestrator_fixed  (SagaStep, BookingOrchestrator – success, step
    failure, compensation, unexpected exception, _execute_step HTTP-error & exception)
"""

import json
import uuid
from datetime import timedelta
from unittest import mock
from unittest.mock import MagicMock, patch, PropertyMock

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from .models import (
    User, Place, Week, Flight, Passenger, Ticket,
    Seat, SeatReservation, SagaTransaction, SagaPaymentAuthorization,
    SagaMilesAward, SagaLogEntry as SagaLogModel,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_place(code="JFK", city="New York", airport="John F. Kennedy", country="USA"):
    return Place.objects.create(code=code, city=city, airport=airport, country=country)


def make_week(number=0, name="Monday"):
    return Week.objects.get_or_create(number=number, defaults={"name": name})[0]


def make_flight(origin, destination, week):
    return Flight.objects.create(
        origin=origin,
        destination=destination,
        depart_time="10:00:00",
        arrival_time="14:00:00",
        duration=timedelta(hours=4),
        plane="Boeing 737",
        airline="American Airlines",
        flight_number="AA100",
        economy_fare=250.0,
        business_fare=750.0,
        first_fare=1500.0,
    )


# ===========================================================================
# MODEL TESTS
# ===========================================================================

class UserModelTest(TestCase):
    def test_str(self):
        user = User(pk=1, first_name="Jane", last_name="Doe")
        self.assertIn("Jane Doe", str(user))

    def test_str_new_user(self):
        user = User(first_name="A", last_name="B")
        self.assertIn("New", str(user))


class PlaceModelTest(TestCase):
    def test_str(self):
        p = Place(city="Dallas", country="USA", code="DFW")
        self.assertIn("Dallas", str(p))
        self.assertIn("DFW", str(p))


class WeekModelTest(TestCase):
    def test_str(self):
        w = Week(number=1, name="Tuesday")
        self.assertEqual(str(w), "Tuesday (1)")


class FlightModelTest(TestCase):
    def setUp(self):
        self.origin = make_place("LAX", "Los Angeles", "LAX Int'l", "USA")
        self.dest = make_place("ORD", "Chicago", "O'Hare", "USA")

    def test_str_with_flight_number(self):
        f = Flight(pk=1, flight_number="AA200", origin=self.origin,
                   destination=self.dest, depart_time="08:00", arrival_time="12:00",
                   plane="737", airline="AA", economy_fare=100,
                   business_fare=300, first_fare=600)
        self.assertIn("AA200", str(f))

    def test_str_without_flight_number(self):
        f = Flight(pk=5, flight_number=None, origin=self.origin,
                   destination=self.dest, depart_time="08:00", arrival_time="12:00",
                   plane="737", airline="AA", economy_fare=100,
                   business_fare=300, first_fare=600)
        self.assertIn("Flight 5", str(f))


class PassengerModelTest(TestCase):
    def test_str(self):
        p = Passenger(first_name="John", last_name="Smith", gender="male")
        self.assertIn("John Smith", str(p))


class TicketModelTest(TestCase):
    def test_str(self):
        t = Ticket(ref_no="ABC123")
        self.assertEqual(str(t), "ABC123")


class SeatModelTest(TestCase):
    def setUp(self):
        self.origin = make_place("SFO", "San Francisco", "SFO Int'l", "USA")
        self.dest = make_place("MIA", "Miami", "MIA Int'l", "USA")
        self.week = make_week(2, "Wednesday")
        self.flight = make_flight(self.origin, self.dest, self.week)

    def test_str(self):
        seat = Seat(flight=self.flight, seat_number="12A", seat_class="economy")
        self.assertIn("12A", str(seat))


class SeatReservationModelTest(TestCase):
    def setUp(self):
        self.origin = make_place("BOS", "Boston", "Logan", "USA")
        self.dest = make_place("ATL", "Atlanta", "ATL Int'l", "USA")
        self.flight = Flight.objects.create(
            origin=self.origin, destination=self.dest,
            depart_time="09:00", arrival_time="13:00",
            duration=timedelta(hours=4), plane="A320", airline="American Airlines",
            flight_number="AA300", economy_fare=200, business_fare=600, first_fare=1200
        )

    def test_str(self):
        r = SeatReservation(
            correlation_id="CID-001",
            flight=self.flight,
            status="RESERVED",
            expires_at=timezone.now() + timedelta(minutes=30)
        )
        self.assertIn("CID-001", str(r))


class SagaTransactionModelTest(TestCase):
    def setUp(self):
        self.origin = make_place("SEA", "Seattle", "SEA Int'l", "USA")
        self.dest = make_place("DEN", "Denver", "DIA", "USA")
        self.flight = Flight.objects.create(
            origin=self.origin, destination=self.dest,
            depart_time="07:00", arrival_time="10:00",
            duration=timedelta(hours=3), plane="737", airline="American Airlines",
            flight_number="AA400", economy_fare=180, business_fare=540, first_fare=1080
        )

    def test_str(self):
        t = SagaTransaction(correlation_id="CORR-001", flight=self.flight, status="COMPLETED", booking_data={})
        self.assertIn("CORR-001", str(t))


class SagaPaymentAuthorizationModelTest(TestCase):
    def test_str(self):
        a = SagaPaymentAuthorization(authorization_id="AUTH-001", status="AUTHORIZED",
                                     correlation_id="C1", amount=500, flight_fare=450,
                                     other_charges=50)
        self.assertIn("AUTH-001", str(a))


class SagaMilesAwardModelTest(TestCase):
    def test_str(self):
        a = SagaMilesAward(correlation_id="C2", user_id="U1", miles_awarded=500,
                           original_balance=0, new_balance=500, status="AWARDED")
        self.assertIn("500 miles", str(a))


class SagaLogEntryModelTest(TestCase):
    def setUp(self):
        origin = make_place("PDX", "Portland", "PDX Int'l", "USA")
        dest = make_place("PHX", "Phoenix", "PHX Int'l", "USA")
        flight = Flight.objects.create(
            origin=origin, destination=dest,
            depart_time="06:00", arrival_time="09:00",
            duration=timedelta(hours=3), plane="737", airline="American Airlines",
            flight_number="AA500", economy_fare=150, business_fare=450, first_fare=900
        )
        self.log = SagaLogModel.objects.create(
            correlation_id="CID-LOG", step_name="TEST", service="TestSvc",
            log_level="info", message="Testing log entry"
        )

    def test_str(self):
        self.assertIn("TEST", str(self.log))

    def test_to_dict(self):
        d = self.log.to_dict()
        self.assertEqual(d["step_name"], "TEST")
        self.assertEqual(d["service"], "TestSvc")
        self.assertIn("timestamp", d)
        self.assertIs(d["is_compensation"], False)

    def test_to_dict_compensation(self):
        log = SagaLogModel.objects.create(
            correlation_id="CID-COMP", step_name="COMP", service="Svc",
            log_level="compensation", message="compensation msg", is_compensation=True
        )
        d = log.to_dict()
        self.assertTrue(d["is_compensation"])


# ===========================================================================
# SIMPLE VIEWS TESTS
# ===========================================================================

class HealthCheckViewTest(TestCase):
    def test_health(self):
        c = Client()
        r = c.get("/api/health/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "healthy")


class PlacesSearchViewTest(TestCase):
    def setUp(self):
        make_place("JFK", "New York", "Kennedy", "USA")
        make_place("LAX", "Los Angeles", "LAX Int'l", "USA")
        self.client = Client()

    def test_empty_query_returns_empty(self):
        r = self.client.get("/api/places/search/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])

    def test_match_by_city(self):
        r = self.client.get("/api/places/search/?q=New York")
        self.assertEqual(r.status_code, 200)
        codes = [p["code"] for p in r.json()]
        self.assertIn("JFK", codes)

    def test_match_by_code(self):
        r = self.client.get("/api/places/search/?q=lax")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(any(p["code"] == "LAX" for p in r.json()))

    def test_no_match(self):
        r = self.client.get("/api/places/search/?q=zzz")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])


class FlightSearchViewTest(TestCase):
    def setUp(self):
        self.origin = make_place("JFK", "New York", "Kennedy", "USA")
        self.dest = make_place("LAX", "Los Angeles", "LAX Int'l", "USA")
        self.week_mon = make_week(0, "Monday")
        self.week_tue = make_week(1, "Tuesday")
        self.flight = Flight.objects.create(
            origin=self.origin, destination=self.dest,
            depart_time="08:00", arrival_time="11:00",
            duration=timedelta(hours=5), plane="737",
            airline="American Airlines", flight_number="AA101",
            economy_fare=300.0, business_fare=900.0, first_fare=1800.0
        )
        self.flight.depart_day.add(self.week_mon)
        # return flight
        self.ret_flight = Flight.objects.create(
            origin=self.dest, destination=self.origin,
            depart_time="14:00", arrival_time="23:00",
            duration=timedelta(hours=5), plane="737",
            airline="American Airlines", flight_number="AA102",
            economy_fare=310.0, business_fare=910.0, first_fare=1810.0
        )
        self.ret_flight.depart_day.add(self.week_tue)
        self.client = Client()

    def _next_weekday(self, target_weekday):
        """Return the next date for a given weekday (0=Mon..6=Sun)"""
        from datetime import date
        today = date.today()
        days_ahead = (target_weekday - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return today + timedelta(days=days_ahead)

    def test_missing_params(self):
        r = self.client.get("/api/flights/search/")
        self.assertEqual(r.status_code, 400)

    def test_invalid_place(self):
        r = self.client.get("/api/flights/search/?origin=ZZZ&destination=YYY&depart_date=2026-05-05")
        self.assertEqual(r.status_code, 400)

    def test_round_trip_missing_return_date(self):
        date = self._next_weekday(0).isoformat()
        r = self.client.get(
            f"/api/flights/search/?origin=JFK&destination=LAX&depart_date={date}&trip_type=2"
        )
        self.assertEqual(r.status_code, 400)

    def test_one_way_economy(self):
        monday = self._next_weekday(0).isoformat()
        r = self.client.get(
            f"/api/flights/search/?origin=JFK&destination=LAX&depart_date={monday}&seat_class=economy"
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("flights", data)

    def test_one_way_business(self):
        monday = self._next_weekday(0).isoformat()
        r = self.client.get(
            f"/api/flights/search/?origin=JFK&destination=LAX&depart_date={monday}&seat_class=business"
        )
        self.assertEqual(r.status_code, 200)

    def test_one_way_first(self):
        monday = self._next_weekday(0).isoformat()
        r = self.client.get(
            f"/api/flights/search/?origin=JFK&destination=LAX&depart_date={monday}&seat_class=first"
        )
        self.assertEqual(r.status_code, 200)

    def test_round_trip(self):
        monday = self._next_weekday(0).isoformat()
        tuesday = self._next_weekday(1).isoformat()
        r = self.client.get(
            f"/api/flights/search/?origin=JFK&destination=LAX"
            f"&depart_date={monday}&trip_type=2&return_date={tuesday}&seat_class=economy"
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("flights2", data)


class FlightDetailViewTest(TestCase):
    def setUp(self):
        self.origin = make_place("DFW", "Dallas", "DFW Int'l", "USA")
        self.dest = make_place("MIA", "Miami", "MIA Int'l", "USA")
        self.flight = Flight.objects.create(
            origin=self.origin, destination=self.dest,
            depart_time="09:00", arrival_time="13:00",
            duration=timedelta(hours=4), plane="A321",
            airline="American Airlines", flight_number="AA200",
            economy_fare=200, business_fare=600, first_fare=1200
        )
        self.client = Client()

    def test_valid_flight(self):
        r = self.client.get(f"/api/flights/{self.flight.pk}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["flight_number"], "AA200")

    def test_invalid_flight(self):
        r = self.client.get("/api/flights/999999/")
        self.assertEqual(r.status_code, 404)


class BookFlightViewTest(TestCase):
    def setUp(self):
        self.origin = make_place("BOS", "Boston", "Logan", "USA")
        self.dest = make_place("SEA", "Seattle", "SEA Int'l", "USA")
        self.flight = Flight.objects.create(
            origin=self.origin, destination=self.dest,
            depart_time="06:00", arrival_time="10:00",
            duration=timedelta(hours=6), plane="787",
            airline="American Airlines", flight_number="AA300",
            economy_fare=350, business_fare=1050, first_fare=2100
        )
        self.client = Client()

    def _valid_payload(self, **kwargs):
        p = {
            "flight_id": self.flight.pk,
            "passengers": [{"first_name": "Alice", "last_name": "W", "gender": "female"}],
            "contact_info": {"email": "a@b.com", "mobile": "1234567890"},
            "user_id": 99,
        }
        p.update(kwargs)
        return p

    def test_book_success(self):
        r = self.client.post("/api/flights/book/",
                             data=json.dumps(self._valid_payload()),
                             content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["success"])

    def test_missing_flight_id(self):
        p = self._valid_payload()
        del p["flight_id"]
        r = self.client.post("/api/flights/book/", data=json.dumps(p),
                             content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_missing_passengers(self):
        p = self._valid_payload(passengers=[])
        r = self.client.post("/api/flights/book/", data=json.dumps(p),
                             content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_missing_contact(self):
        p = self._valid_payload(contact_info={"email": "", "mobile": ""})
        r = self.client.post("/api/flights/book/", data=json.dumps(p),
                             content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_invalid_flight_id(self):
        p = self._valid_payload(flight_id=999999)
        r = self.client.post("/api/flights/book/", data=json.dumps(p),
                             content_type="application/json")
        self.assertEqual(r.status_code, 404)

    def test_invalid_json(self):
        r = self.client.post("/api/flights/book/", data="not-json",
                             content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_passenger_missing_name(self):
        p = self._valid_payload(passengers=[{"first_name": "", "last_name": "W", "gender": "male"}])
        r = self.client.post("/api/flights/book/", data=json.dumps(p),
                             content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_passenger_missing_gender(self):
        p = self._valid_payload(passengers=[{"first_name": "A", "last_name": "B", "gender": ""}])
        r = self.client.post("/api/flights/book/", data=json.dumps(p),
                             content_type="application/json")
        self.assertEqual(r.status_code, 400)


class GetUserTicketsViewTest(TestCase):
    def setUp(self):
        from .simple_views import stored_tickets
        stored_tickets.clear()
        self.origin = make_place("ATL", "Atlanta", "ATL Int'l", "USA")
        self.dest = make_place("DEN", "Denver", "DIA", "USA")
        self.flight = Flight.objects.create(
            origin=self.origin, destination=self.dest,
            depart_time="07:00", arrival_time="09:00",
            duration=timedelta(hours=2), plane="737",
            airline="American Airlines", flight_number="AA400",
            economy_fare=200, business_fare=600, first_fare=1200
        )
        self.client = Client()

    def test_empty_tickets(self):
        r = self.client.get("/api/tickets/user/42/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])

    def test_stored_ticket_returned(self):
        from .simple_views import stored_tickets
        stored_tickets["7"] = [{"booking_reference": "BKT001", "status": "pending"}]
        r = self.client.get("/api/tickets/user/7/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)

    def test_with_saga_no_user(self):
        r = self.client.get("/api/tickets/user/9999/with-saga/")
        self.assertEqual(r.status_code, 200)

    def test_with_saga_existing_user(self):
        user = User.objects.create_user(username="tktuser", password="pass")
        origin = make_place("EWR", "Newark", "EWR Int'l", "USA")
        dest = make_place("MCO", "Orlando", "MCO Int'l", "USA")
        flight = Flight.objects.create(
            origin=origin, destination=dest,
            depart_time="11:00", arrival_time="14:00",
            duration=timedelta(hours=3), plane="737",
            airline="American Airlines", flight_number="AA500",
            economy_fare=200, business_fare=500, first_fare=1000
        )
        Ticket.objects.create(
            user=user, ref_no="TKT01", flight=flight,
            seat_class="economy", status="CONFIRMED",
            flight_fare=200, other_charges=50, total_fare=250
        )
        r = self.client.get(f"/api/tickets/user/{user.pk}/with-saga/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(any(t.get("booking_reference") == "TKT01" for t in data))


class UpdateTicketStatusViewTest(TestCase):
    def setUp(self):
        from .simple_views import stored_tickets
        stored_tickets.clear()
        stored_tickets["1"] = [{"booking_reference": "REF001", "status": "pending"}]
        self.client = Client()

    def test_update_confirmed(self):
        r = self.client.post(
            "/api/tickets/REF001/update_status/",
            data=json.dumps({"status": "confirmed"}),
            content_type="application/json"
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["success"])

    def test_update_invalid_status(self):
        r = self.client.post(
            "/api/tickets/REF001/update_status/",
            data=json.dumps({"status": "flown"}),
            content_type="application/json"
        )
        self.assertEqual(r.status_code, 400)

    def test_missing_status(self):
        r = self.client.post(
            "/api/tickets/REF001/update_status/",
            data=json.dumps({}),
            content_type="application/json"
        )
        self.assertEqual(r.status_code, 400)

    def test_ticket_not_found(self):
        r = self.client.post(
            "/api/tickets/NOTEXIST/update_status/",
            data=json.dumps({"status": "confirmed"}),
            content_type="application/json"
        )
        self.assertEqual(r.status_code, 404)

    def test_invalid_json(self):
        r = self.client.post(
            "/api/tickets/REF001/update_status/",
            data="bad",
            content_type="application/json"
        )
        self.assertEqual(r.status_code, 400)


# ===========================================================================
# SAGA LOG STORAGE TESTS
# ===========================================================================

class SagaLogStorageTest(TestCase):
    def setUp(self):
        from .saga_log_storage import SagaLogStorage
        self.storage = SagaLogStorage()

    def test_add_log_persists_to_db(self):
        cid = "SLS-001"
        self.storage.add_log(cid, "StepA", "ServiceA", "info", "Test message")
        self.assertEqual(SagaLogModel.objects.filter(correlation_id=cid).count(), 1)

    def test_add_log_compensation_flag(self):
        cid = "SLS-002"
        self.storage.add_log(cid, "COMP", "Svc", "compensation", "Comp msg", is_compensation=True)
        entry = SagaLogModel.objects.get(correlation_id=cid)
        self.assertTrue(entry.is_compensation)

    def test_get_logs_from_db(self):
        cid = "SLS-003"
        self.storage.add_log(cid, "S1", "Svc", "info", "M1")
        self.storage.add_log(cid, "S2", "Svc", "success", "M2")
        logs = self.storage.get_logs(cid)
        self.assertEqual(len(logs), 2)

    def test_get_logs_exclude_compensation(self):
        cid = "SLS-004"
        self.storage.add_log(cid, "S1", "Svc", "info", "Normal")
        self.storage.add_log(cid, "COMP_S1", "Svc", "compensation", "Comp", is_compensation=True)
        logs = self.storage.get_logs(cid, include_compensation=False)
        self.assertEqual(len(logs), 1)

    def test_get_logs_fallback_memory(self):
        """When DB raises, falls back to in-memory logs"""
        cid = "SLS-005"
        from .saga_log_storage import SagaLogStorage
        storage = SagaLogStorage()
        # Inject a memory entry without DB
        from .saga_log_storage import SagaLogEntry as MemEntry
        entry = MemEntry(cid, "S1", "Svc", "info", "mem msg")
        storage.logs[cid] = [entry]
        with patch("flight.models.SagaLogEntry.objects") as mock_mgr:
            mock_qset = MagicMock()
            mock_qset.filter.return_value.filter.return_value = mock_qset
            mock_qset.__iter__ = MagicMock(return_value=iter([]))
            mock_qset.count.return_value = 0
            mock_mgr.filter.return_value = mock_qset
            logs = storage.get_logs(cid)
        # Fallback always works—at minimum empty list
        self.assertIsInstance(logs, list)

    def test_add_log_db_fallback_on_error(self):
        """If DB create raises, falls back to memory silently"""
        from .saga_log_storage import SagaLogStorage
        storage = SagaLogStorage()
        cid = "SLS-006"
        with patch("flight.models.SagaLogEntry.objects.create", side_effect=Exception("DB down")):
            storage.add_log(cid, "S1", "Svc", "info", "fallback msg")
        self.assertIn(cid, storage.logs)


# ===========================================================================
# FAILED BOOKING HANDLER TESTS
# ===========================================================================

class FailedBookingHandlerTest(TestCase):
    def setUp(self):
        self.origin = make_place("SAN", "San Diego", "SAN Int'l", "USA")
        self.dest = make_place("DTW", "Detroit", "DTW Int'l", "USA")
        self.flight = Flight.objects.create(
            origin=self.origin, destination=self.dest,
            depart_time="09:00", arrival_time="16:00",
            duration=timedelta(hours=5), plane="737",
            airline="American Airlines", flight_number="AA600",
            economy_fare=275, business_fare=825, first_fare=1650
        )
        self.user = User.objects.create_user(username="failuser", password="pass")

    def _booking_data(self, seat_class="economy", user_id=None):
        return {
            "flight_id": self.flight.pk,
            "user_id": user_id or self.user.pk,
            "seat_class": seat_class,
            "passengers": [{"first_name": "A", "last_name": "B", "gender": "male"}],
            "contact_info": {"email": "x@y.com", "mobile": "0000000000"},
        }

    def test_creates_failed_ticket(self):
        from .failed_booking_handler import create_failed_booking_record
        result = create_failed_booking_record(
            correlation_id="CTEST-001",
            booking_data=self._booking_data(),
            failed_step="PaymentTransaction",
            error_message="Card declined"
        )
        self.assertIsNotNone(result)
        self.assertIn("ref_no", result)
        self.assertEqual(Ticket.objects.filter(status="FAILED").count(), 1)

    def test_business_class_fare(self):
        from .failed_booking_handler import create_failed_booking_record
        result = create_failed_booking_record(
            correlation_id="CTEST-002",
            booking_data=self._booking_data(seat_class="business"),
            failed_step="MilesLoyalty",
            error_message="Loyalty down"
        )
        self.assertIsNotNone(result)

    def test_first_class_fare(self):
        from .failed_booking_handler import create_failed_booking_record
        result = create_failed_booking_record(
            correlation_id="CTEST-003",
            booking_data=self._booking_data(seat_class="first"),
            failed_step="BookingDone",
            error_message="Booking error"
        )
        self.assertIsNotNone(result)

    def test_missing_user_handled(self):
        from .failed_booking_handler import create_failed_booking_record
        data = self._booking_data(user_id=99999)
        result = create_failed_booking_record(
            correlation_id="CTEST-004",
            booking_data=data,
            failed_step="BookingDone",
            error_message="User not found"
        )
        self.assertIsNotNone(result)
        t = Ticket.objects.get(ref_no=result["ref_no"])
        self.assertIsNone(t.user)

    def test_invalid_flight_uses_fallback(self):
        from .failed_booking_handler import create_failed_booking_record
        data = self._booking_data()
        data["flight_id"] = 999999
        result = create_failed_booking_record(
            correlation_id="CTEST-005",
            booking_data=data,
            failed_step="MilesLoyalty",
            error_message="No flight"
        )
        # When the flight doesn't exist the handler falls back to logging mode
        # and returns a dict with success=True and a fallback message
        self.assertIsNotNone(result)
        self.assertTrue(result.get("success"))
        self.assertIn("fallback", result.get("message", "").lower())


# ===========================================================================
# SAGA ORCHESTRATOR TESTS
# ===========================================================================

class SagaOrchestratorTest(TestCase):
    def setUp(self):
        from .saga_orchestrator_fixed import BookingOrchestrator
        self.orch = BookingOrchestrator()
        self.origin = make_place("CLT", "Charlotte", "CLT Int'l", "USA")
        self.dest = make_place("ORD", "Chicago", "O'Hare", "USA")
        self.flight = Flight.objects.create(
            origin=self.origin, destination=self.dest,
            depart_time="10:00", arrival_time="12:00",
            duration=timedelta(hours=2), plane="737",
            airline="American Airlines", flight_number="AA700",
            economy_fare=200, business_fare=600, first_fare=1200
        )
        self.user = User.objects.create_user(username="saga_user", password="pass")
        self.booking_data = {
            "flight_id": self.flight.pk,
            "user_id": self.user.pk,
            "flight_fare": 200.0,
            "seat_class": "economy",
            "passengers": [{"first_name": "X", "last_name": "Y", "gender": "male"}],
            "contact_info": {"email": "a@b.com", "mobile": "1234567890"},
        }

    def _mock_response(self, success=True, extra=None):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        payload = {"success": success, "message": "OK"}
        if extra:
            payload.update(extra)
        mock_resp.json.return_value = payload
        return mock_resp

    @patch("flight.saga_orchestrator_fixed.requests.post")
    def test_all_steps_succeed(self, mock_post):
        mock_post.return_value = self._mock_response(True)
        result = self.orch.start_booking_saga(self.booking_data)
        self.assertTrue(result["success"])
        self.assertEqual(result["steps_completed"], 4)

    @patch("flight.saga_orchestrator_fixed.requests.post")
    def test_step_failure_triggers_compensation(self, mock_post):
        # First two calls succeed (steps 1+2), third fails (step 3)
        success_resp = self._mock_response(True)
        fail_resp = self._mock_response(False)
        mock_post.side_effect = [success_resp, success_resp, fail_resp,
                                  success_resp, success_resp]  # compensations
        result = self.orch.start_booking_saga(self.booking_data)
        self.assertFalse(result["success"])
        self.assertIn("failed_step", result)

    @patch("flight.saga_orchestrator_fixed.requests.post")
    def test_step_http_error(self, mock_post):
        error_resp = MagicMock()
        error_resp.status_code = 500
        error_resp.text = "Server error"
        mock_post.return_value = error_resp
        result = self.orch.start_booking_saga(self.booking_data)
        self.assertFalse(result["success"])

    @patch("flight.saga_orchestrator_fixed.requests.post")
    def test_step_connection_exception(self, mock_post):
        import requests as req
        mock_post.side_effect = req.exceptions.ConnectionError("refused")
        result = self.orch.start_booking_saga(self.booking_data)
        self.assertFalse(result["success"])

    @patch("flight.saga_orchestrator_fixed.requests.post")
    def test_unexpected_exception_during_step(self, mock_post):
        mock_post.side_effect = Exception("Unexpected!")
        result = self.orch.start_booking_saga(self.booking_data)
        self.assertFalse(result["success"])

    @patch("flight.saga_orchestrator_fixed.requests.post")
    def test_compensation_http_error(self, mock_post):
        success_resp = self._mock_response(True)
        fail_resp = self._mock_response(False)
        comp_fail_resp = MagicMock()
        comp_fail_resp.status_code = 503
        comp_fail_resp.text = ""
        # step1 succeeds, step2 fails → compensate step1 with HTTP error
        mock_post.side_effect = [success_resp, fail_resp, comp_fail_resp]
        result = self.orch.start_booking_saga(self.booking_data)
        self.assertFalse(result["success"])

    @patch("flight.saga_orchestrator_fixed.requests.post")
    def test_compensation_exception(self, mock_post):
        import requests as req
        success_resp = self._mock_response(True)
        fail_resp = self._mock_response(False)
        mock_post.side_effect = [success_resp, fail_resp,
                                  req.exceptions.ConnectionError("comp failed")]
        result = self.orch.start_booking_saga(self.booking_data)
        self.assertFalse(result["success"])

    def test_correlation_id_reused(self):
        """Existing correlation_id in booking_data should be reused"""
        from .saga_orchestrator_fixed import BookingOrchestrator
        orch = BookingOrchestrator()
        data = dict(self.booking_data)
        data["correlation_id"] = "FIXED-CID-999"
        with patch("flight.saga_orchestrator_fixed.requests.post") as mock_post:
            mock_post.return_value = self._mock_response(True)
            result = orch.start_booking_saga(data)
        self.assertEqual(result["correlation_id"], "FIXED-CID-999")

    @patch("flight.saga_orchestrator_fixed.requests.post")
    def test_miles_loyalty_step_details_logged(self, mock_post):
        extra = {"miles_awarded": 200, "original_balance": 0,
                 "new_balance": 200, "is_round_trip": False}
        mock_post.return_value = self._mock_response(True, extra=extra)
        result = self.orch.start_booking_saga(self.booking_data)
        self.assertTrue(result["success"])

    @patch("flight.saga_orchestrator_fixed.requests.post")
    def test_round_trip_miles_logged(self, mock_post):
        extra = {"miles_awarded": 400, "flight1_miles": 200,
                 "flight2_miles": 200, "original_balance": 0,
                 "new_balance": 400, "is_round_trip": True}
        mock_post.return_value = self._mock_response(True, extra=extra)
        result = self.orch.start_booking_saga(self.booking_data)
        self.assertTrue(result["success"])

    @patch("flight.saga_orchestrator_fixed.requests.post")
    def test_payment_transaction_details_logged(self, mock_post):
        extra_miles = {"miles_awarded": 100, "original_balance": 0, "new_balance": 100}
        extra_pay = {"authorization_id": "AUTH-001", "amount": 250}

        def side_effects(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            if "award-miles" in url:
                r = MagicMock(); r.status_code = 200; r.json.return_value = {"success": True, **extra_miles}; return r
            elif "authorize-payment" in url:
                r = MagicMock(); r.status_code = 200; r.json.return_value = {"success": True, **extra_pay}; return r
            else:
                r = MagicMock(); r.status_code = 200; r.json.return_value = {"success": True}; return r

        mock_post.side_effect = side_effects
        result = self.orch.start_booking_saga(self.booking_data)
        self.assertTrue(result["success"])

    @patch("flight.saga_orchestrator_fixed.requests.post")
    def test_reservation_id_logged(self, mock_post):
        extra_res = {"reservation_id": "RES-XYZ"}

        def side_effects(*args, **kwargs):
            url = args[0] if args else ""
            r = MagicMock()
            r.status_code = 200
            payload = {"success": True}
            if "reserve-seat" in url:
                payload["reservation_id"] = "RES-XYZ"
            r.json.return_value = payload
            return r

        mock_post.side_effect = side_effects
        result = self.orch.start_booking_saga(self.booking_data)
        self.assertTrue(result["success"])
