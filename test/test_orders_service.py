"""
Tests for apps/orders/service.py – additional edge cases
Covers: process_hybrid_payment, get_order_summary, _calculate_points_value
"""
import pytest
import uuid
from decimal import Decimal
from django.contrib.auth import get_user_model

User = get_user_model()


def make_user(prefix="os"):
    tag = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"{prefix}_{tag}",
        email=f"{prefix}_{tag}@test.com",
        password="pass123",
    )


# ─── Hybrid pricing edge cases ────────────────────────────────────────────────

@pytest.mark.django_db
class TestOrderServiceHybridPricingEdgeCases:
    def test_points_capped_at_available_balance(self):
        from apps.orders.service import OrderService
        from apps.loyalty.service import LoyaltyService
        u = make_user("hce")
        LoyaltyService.earn_points(u, 100)  # Only 100 pts available
        result = OrderService.calculate_hybrid_pricing(u, Decimal("500.00"), 99999)
        # Should only use what's available
        assert result["points_used"] <= 100

    def test_cash_amount_never_negative(self):
        from apps.orders.service import OrderService
        from apps.loyalty.service import LoyaltyService
        u = make_user("hcn")
        # Give huge amount of points worth more than the total
        LoyaltyService.earn_points(u, 100000)
        result = OrderService.calculate_hybrid_pricing(u, Decimal("50.00"), 100000)
        assert result["cash_amount"] >= Decimal("0.00")

    def test_zero_points_gives_full_cash(self):
        from apps.orders.service import OrderService
        u = make_user("hcz")
        result = OrderService.calculate_hybrid_pricing(u, Decimal("300.00"), 0)
        assert result["cash_amount"] == Decimal("300.00")
        assert result["points_used"] == 0


# ─── process_hybrid_payment ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestProcessHybridPayment:
    def test_process_non_hybrid_order_raises(self):
        from apps.orders.service import OrderService
        from apps.orders.models import Order
        u = make_user("php")
        order = Order.objects.create(
            user=u,
            payment_method="cash_only",
            status="draft",
            total_amount=Decimal("100.00"),
            cash_amount=Decimal("100.00"),
        )
        with pytest.raises(ValueError, match="not configured for hybrid"):
            OrderService.process_hybrid_payment(order)

    def test_process_hybrid_points_only_marks_paid(self):
        from apps.orders.service import OrderService
        from apps.orders.models import Order
        from apps.loyalty.service import LoyaltyService
        u = make_user("phpok")
        LoyaltyService.earn_points(u, 10000)
        order = Order.objects.create(
            user=u,
            payment_method="hybrid",
            status="draft",
            total_amount=Decimal("50.00"),
            points_used=5000,
            points_value=Decimal("50.00"),
            cash_amount=Decimal("0.00"),  # zero cash → should mark as paid
        )
        result = OrderService.process_hybrid_payment(order)
        assert result.status == "paid"

    def test_process_hybrid_with_cash_marks_pending(self):
        from apps.orders.service import OrderService
        from apps.orders.models import Order
        from apps.loyalty.service import LoyaltyService
        u = make_user("phppc")
        LoyaltyService.earn_points(u, 1000)
        order = Order.objects.create(
            user=u,
            payment_method="hybrid",
            status="draft",
            total_amount=Decimal("100.00"),
            points_used=1000,
            points_value=Decimal("10.00"),
            cash_amount=Decimal("90.00"),
        )
        result = OrderService.process_hybrid_payment(order)
        assert result.status in ("pending_payment", "partially_paid")


# ─── get_order_summary ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGetOrderSummary:
    def test_summary_has_all_keys(self):
        from apps.orders.service import OrderService
        from apps.orders.models import Order
        u = make_user("gos")
        order = Order.objects.create(
            user=u,
            payment_method="cash_only",
            status="draft",
            total_amount=Decimal("250.00"),
            cash_amount=Decimal("250.00"),
        )
        summary = OrderService.get_order_summary(order)
        required = ["order_number", "total_amount", "payment_method",
                    "points_used", "points_value", "cash_amount", "status", "created_at"]
        for key in required:
            assert key in summary, f"Missing key: {key}"

    def test_summary_values_match_order(self):
        from apps.orders.service import OrderService
        from apps.orders.models import Order
        u = make_user("gos2")
        order = Order.objects.create(
            user=u,
            payment_method="cash_only",
            status="paid",
            total_amount=Decimal("150.00"),
            cash_amount=Decimal("150.00"),
        )
        summary = OrderService.get_order_summary(order)
        assert summary["total_amount"] == Decimal("150.00")


# ─── create_order_from_tickets with real fare ────────────────────────────────

@pytest.mark.django_db
class TestCreateOrderFromTicketsWithFare:
    def test_total_includes_fees(self):
        from apps.orders.service import OrderService
        from flight.models import Ticket
        import uuid as _uuid
        u = make_user("coft")

        # Create a mock ticket with a fare
        ticket = Ticket.__new__(Ticket)
        ticket.total_fare = Decimal("300.00")

        order = OrderService.create_order_from_tickets(u, [ticket])
        assert order.subtotal == Decimal("300.00")
        assert order.fees_amount > Decimal("0.00")
        assert order.total_amount == order.subtotal + order.fees_amount

    def test_cash_only_no_points(self):
        from apps.orders.service import OrderService
        u = make_user("coftnp")
        order = OrderService.create_order_from_tickets(u, [], payment_method="cash_only")
        assert order.points_used == 0
        assert order.cash_amount == order.total_amount

    def test_hybrid_with_points_updates_cash(self):
        from apps.orders.service import OrderService
        from apps.loyalty.service import LoyaltyService
        u = make_user("cofthybrid")
        LoyaltyService.earn_points(u, 5000)

        class FakeTicket:
            total_fare = Decimal("200.00")

        order = OrderService.create_order_from_tickets(
            u, [FakeTicket()], payment_method="hybrid", points_to_use=5000
        )
        assert order.points_used == min(5000, LoyaltyService.get_points_balance(u) + 5000)
        assert order.cash_amount >= Decimal("0.00")
