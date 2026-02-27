"""
Tests for apps/loyalty/views.py
Covers: loyalty_dashboard, points_history, tier_info, calculate_points_value
"""
import json
import pytest
import uuid
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


def make_user(prefix="lv"):
    tag = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"{prefix}_{tag}",
        email=f"{prefix}_{tag}@test.com",
        password="testpass123",
    )


@pytest.mark.django_db
class TestLoyaltyDashboardView:
    def test_unauthenticated_redirects(self):
        c = Client()
        resp = c.get(reverse("loyalty:dashboard"))
        assert resp.status_code == 302

    def test_authenticated_returns_200(self):
        c = Client()
        u = make_user("dash")
        c.force_login(u)
        resp = c.get(reverse("loyalty:dashboard"))
        assert resp.status_code == 200

    def test_contains_account_data(self):
        c = Client()
        u = make_user("dash2")
        c.force_login(u)
        resp = c.get(reverse("loyalty:dashboard"))
        assert resp.status_code == 200
        # Either renders points balance or error key in context
        assert "account" in resp.context or "error" in resp.context


@pytest.mark.django_db
class TestPointsHistoryView:
    def test_unauthenticated_redirects(self):
        c = Client()
        resp = c.get(reverse("loyalty:points_history"))
        assert resp.status_code == 302

    def test_authenticated_returns_200(self):
        c = Client()
        u = make_user("phist")
        c.force_login(u)
        resp = c.get(reverse("loyalty:points_history"))
        assert resp.status_code == 200

    def test_shows_transactions_after_earning(self):
        from apps.loyalty.service import LoyaltyService
        c = Client()
        u = make_user("phist2")
        LoyaltyService.earn_points(u, 100)
        c.force_login(u)
        resp = c.get(reverse("loyalty:points_history"))
        assert resp.status_code == 200
        ctx = resp.context
        assert "transactions" in ctx
        assert len(ctx["transactions"]) >= 1


@pytest.mark.django_db
class TestTierInfoView:
    def test_unauthenticated_redirects(self):
        c = Client()
        resp = c.get(reverse("loyalty:tier_info"))
        assert resp.status_code == 302

    def test_authenticated_returns_200(self):
        c = Client()
        u = make_user("tier")
        c.force_login(u)
        resp = c.get(reverse("loyalty:tier_info"))
        assert resp.status_code == 200


@pytest.mark.django_db
class TestCalculatePointsValueView:
    def _url(self):
        return reverse("loyalty:calculate_points_value")

    def test_calculates_value(self):
        c = Client()
        payload = {"points": 500}
        resp = c.post(
            self._url(),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["points"] == 500
        assert data["value"] == 5.0  # 500 * 0.01

    def test_zero_points(self):
        c = Client()
        resp = c.post(
            self._url(),
            data=json.dumps({"points": 0}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json()["value"] == 0.0

    def test_invalid_json_returns_500(self):
        c = Client()
        resp = c.post(
            self._url(),
            data="not json",
            content_type="application/json",
        )
        assert resp.status_code == 500

    def test_large_points(self):
        c = Client()
        resp = c.post(
            self._url(),
            data=json.dumps({"points": 10000}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.json()["value"] == 100.0
