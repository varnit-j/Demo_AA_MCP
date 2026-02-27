"""
Tests for apps/loyalty/service.py and apps/orders/service.py
Coverage target: service/business-logic layer
"""
import pytest
import uuid
from decimal import Decimal
from django.contrib.auth import get_user_model

User = get_user_model()


def make_user():
    tag = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"loyuser_{tag}",
        email=f"loyuser_{tag}@test.com",
        password="pass123",
    )


# ─── LoyaltyService tests ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLoyaltyServiceGetOrCreate:
    def test_creates_account_on_first_call(self):
        from apps.loyalty.service import LoyaltyService
        u = make_user()
        acct = LoyaltyService.get_or_create_account(u)
        assert acct is not None
        assert acct.user == u

    def test_returns_same_account_on_second_call(self):
        from apps.loyalty.service import LoyaltyService
        u = make_user()
        a1 = LoyaltyService.get_or_create_account(u)
        a2 = LoyaltyService.get_or_create_account(u)
        assert a1.pk == a2.pk


@pytest.mark.django_db
class TestLoyaltyServiceEarnPoints:
    def test_earn_positive_points(self):
        from apps.loyalty.service import LoyaltyService
        u = make_user()
        txn = LoyaltyService.earn_points(u, 100, reference_id="ref_001", description="booking")
        assert txn is not None
        assert txn.points_amount >= 100

    def test_earn_zero_points_raises(self):
        from apps.loyalty.service import LoyaltyService
        u = make_user()
        with pytest.raises(ValueError):
            LoyaltyService.earn_points(u, 0)

    def test_earn_negative_points_raises(self):
        from apps.loyalty.service import LoyaltyService
        u = make_user()
        with pytest.raises(ValueError):
            LoyaltyService.earn_points(u, -50)

    def test_balance_increases_after_earn(self):
        from apps.loyalty.service import LoyaltyService
        u = make_user()
        LoyaltyService.earn_points(u, 500)
        balance = LoyaltyService.get_points_balance(u)
        assert balance >= 500


@pytest.mark.django_db
class TestLoyaltyServiceRedeemPoints:
    def test_redeem_within_balance_succeeds(self):
        from apps.loyalty.service import LoyaltyService
        u = make_user()
        LoyaltyService.earn_points(u, 200)
        txn = LoyaltyService.redeem_points(u, 100, reference_id="redeem_001")
        assert txn is not None
        assert txn.points_amount == 100

    def test_redeem_more_than_balance_raises(self):
        from apps.loyalty.service import LoyaltyService
        u = make_user()
        LoyaltyService.earn_points(u, 50)
        with pytest.raises(ValueError, match="Insufficient"):
            LoyaltyService.redeem_points(u, 1000)

    def test_redeem_zero_raises(self):
        from apps.loyalty.service import LoyaltyService
        u = make_user()
        with pytest.raises(ValueError):
            LoyaltyService.redeem_points(u, 0)

    def test_balance_decreases_after_redeem(self):
        from apps.loyalty.service import LoyaltyService
        u = make_user()
        LoyaltyService.earn_points(u, 300)
        before = LoyaltyService.get_points_balance(u)
        LoyaltyService.redeem_points(u, 100)
        after = LoyaltyService.get_points_balance(u)
        assert after == before - 100


@pytest.mark.django_db
class TestLoyaltyServiceGetBalance:
    def test_zero_for_new_user_without_account(self):
        from apps.loyalty.service import LoyaltyService
        u = make_user()
        assert LoyaltyService.get_points_balance(u) == 0

    def test_reflects_earned_points(self):
        from apps.loyalty.service import LoyaltyService
        u = make_user()
        LoyaltyService.earn_points(u, 250)
        assert LoyaltyService.get_points_balance(u) >= 250


@pytest.mark.django_db
class TestLoyaltyServiceCalculatePointsValue:
    def test_base_rate_calculation(self):
        from apps.loyalty.service import LoyaltyService
        value = LoyaltyService.calculate_points_value(100)
        assert value == Decimal("1.00")

    def test_zero_points(self):
        from apps.loyalty.service import LoyaltyService
        assert LoyaltyService.calculate_points_value(0) == Decimal("0.00")


@pytest.mark.django_db
class TestLoyaltyServiceTransactionHistory:
    def test_empty_history_for_new_user(self):
        from apps.loyalty.service import LoyaltyService
        u = make_user()
        history = LoyaltyService.get_transaction_history(u)
        assert history == []

    def test_history_grows_after_earn(self):
        from apps.loyalty.service import LoyaltyService
        u = make_user()
        LoyaltyService.earn_points(u, 100)
        LoyaltyService.earn_points(u, 200)
        history = LoyaltyService.get_transaction_history(u)
        assert len(history) == 2


# ─── OrderService tests ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestOrderServiceCalculateHybridPricing:
    def test_cash_only_no_points(self):
        from apps.orders.service import OrderService
        u = make_user()
        result = OrderService.calculate_hybrid_pricing(u, Decimal("500.00"), 0)
        assert result["cash_amount"] == Decimal("500.00")
        assert result["points_used"] == 0

    def test_hybrid_with_points(self):
        from apps.orders.service import OrderService
        from apps.loyalty.service import LoyaltyService
        u = make_user()
        LoyaltyService.earn_points(u, 5000)
        result = OrderService.calculate_hybrid_pricing(u, Decimal("500.00"), 1000)
        assert result["points_used"] <= 1000
        assert "cash_amount" in result


@pytest.mark.django_db
class TestOrderServiceCreateOrder:
    def test_create_order_with_empty_tickets(self):
        from apps.orders.service import OrderService
        u = make_user()
        order = OrderService.create_order_from_tickets(u, [])
        assert order is not None
        assert order.user == u
        assert order.status == "draft"
