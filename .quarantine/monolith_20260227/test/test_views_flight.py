"""
Tests for flight/views.py – HTTP layer
Coverage target: major view functions via Django test client
"""
import pytest
import uuid
from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


# ─── Helpers ────────────────────────────────────────────────────────────────

def make_user(prefix=""):
    tag = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"{prefix}user_{tag}",
        email=f"{prefix}{tag}@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


# ─── Index view ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestIndexView:
    def test_get_returns_200(self):
        c = Client()
        resp = c.get(reverse("index"))
        assert resp.status_code == 200

    def test_post_one_way_returns_200(self):
        c = Client()
        resp = c.post(reverse("index"), {
            "Origin": "JFK", "Destination": "LAX",
            "DepartDate": "2026-06-01", "SeatClass": "economy",
            "TripType": "1",
        })
        assert resp.status_code == 200

    def test_post_round_trip_returns_200(self):
        c = Client()
        resp = c.post(reverse("index"), {
            "Origin": "JFK", "Destination": "LAX",
            "DepartDate": "2026-06-01", "ReturnDate": "2026-06-10",
            "SeatClass": "economy", "TripType": "2",
        })
        assert resp.status_code == 200


# ─── Login view ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLoginView:
    def test_get_unauthenticated_returns_200(self):
        c = Client()
        resp = c.get(reverse("login"))
        assert resp.status_code == 200

    def test_get_authenticated_redirects(self):
        c = Client()
        u = make_user("login_")
        c.force_login(u)
        resp = c.get(reverse("login"))
        assert resp.status_code == 302

    def test_post_valid_credentials_redirects(self):
        c = Client()
        u = make_user("loginpost_")
        resp = c.post(reverse("login"), {"username": u.username, "password": "testpass123"})
        assert resp.status_code == 302

    def test_post_invalid_credentials_returns_200_with_message(self):
        c = Client()
        resp = c.post(reverse("login"), {"username": "nobody", "password": "wrong"})
        assert resp.status_code == 200
        assert b"Invalid" in resp.content


# ─── Register view ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRegisterView:
    def test_get_returns_200(self):
        c = Client()
        resp = c.get(reverse("register"))
        assert resp.status_code == 200

    def test_post_creates_user_and_redirects(self):
        c = Client()
        tag = uuid.uuid4().hex[:8]
        resp = c.post(reverse("register"), {
            "firstname": "Alice", "lastname": "Smith",
            "username": f"alice_{tag}", "email": f"alice_{tag}@test.com",
            "password": "secret123", "confirmation": "secret123",
        })
        assert resp.status_code == 302

    def test_post_passwords_mismatch_returns_message(self):
        c = Client()
        tag = uuid.uuid4().hex[:8]
        resp = c.post(reverse("register"), {
            "firstname": "Bob", "lastname": "Jones",
            "username": f"bob_{tag}", "email": "bob@test.com",
            "password": "aaa", "confirmation": "bbb",
        })
        assert resp.status_code == 200
        assert b"Passwords" in resp.content or b"match" in resp.content

    def test_post_duplicate_username_returns_message(self):
        c = Client()
        u = make_user("dup_")
        resp = c.post(reverse("register"), {
            "firstname": "Dup", "lastname": "User",
            "username": u.username, "email": "dup@test.com",
            "password": "pass", "confirmation": "pass",
        })
        assert resp.status_code == 200
        assert b"taken" in resp.content or b"already" in resp.content


# ─── Logout view ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLogoutView:
    def test_logout_redirects(self):
        c = Client()
        u = make_user("logout_")
        c.force_login(u)
        resp = c.get(reverse("logout"))
        assert resp.status_code == 302


# ─── Query (places autocomplete) ─────────────────────────────────────────────

@pytest.mark.django_db
class TestQueryView:
    def test_returns_json(self):
        from flight.models import Place
        Place.objects.get_or_create(
            code="TST", defaults={"city": "Testville", "airport": "Test Airport", "country": "USA"}
        )
        c = Client()
        resp = c.get(reverse("query", kwargs={"q": "test"}))
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_empty_query_returns_list(self):
        c = Client()
        resp = c.get(reverse("query", kwargs={"q": "zzznomatch"}))
        assert resp.status_code == 200
        assert resp.json() == []


# ─── Contact / Static pages ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestStaticPages:
    def test_contact_returns_200(self):
        c = Client()
        resp = c.get(reverse("contact"))
        assert resp.status_code == 200

    def test_privacy_policy_returns_200(self):
        c = Client()
        resp = c.get(reverse("privacypolicy"))
        assert resp.status_code == 200

    def test_terms_returns_200(self):
        c = Client()
        resp = c.get(reverse("termsandconditions"))
        assert resp.status_code == 200

    def test_about_returns_200(self):
        c = Client()
        resp = c.get(reverse("aboutus"))
        assert resp.status_code == 200


# ─── Bookings view (auth-gated) ──────────────────────────────────────────────

@pytest.mark.django_db
class TestBookingsView:
    def test_authenticated_returns_200(self):
        c = Client()
        u = make_user("book_")
        c.force_login(u)
        resp = c.get(reverse("bookings"))
        assert resp.status_code in (200, 302)  # 302 if no tickets

    def test_unauthenticated_redirects(self):
        c = Client()
        resp = c.get(reverse("bookings"))
        assert resp.status_code == 302
