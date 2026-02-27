"""
Comprehensive tests for payment-service -- targets 95%+ coverage.

Covers:
  - payment.models        (PaymentAuthorization __str__)
  - payment.saga_views    (authorize_payment, cancel_payment)
  - payment.saga_compensation (cancel_payment_complete)
  - payment.views         (process_payment, stripe_webhook, payment_status,
                           process_refund, validate_card, health_check)
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from .models import PaymentAuthorization


# ============================================================================
# MODEL TESTS
# ============================================================================

class PaymentAuthorizationStrTest(TestCase):
    def test_str(self):
        auth = PaymentAuthorization(
            correlation_id="CID1",
            authorization_id="AUTH-CID1",
            amount=550.0,
            flight_fare=500.0,
            other_charges=50.0,
            status="AUTHORIZED"
        )
        s = str(auth)
        self.assertIn("AUTH-CID1", s)
        self.assertIn("AUTHORIZED", s)

    def test_str_cancelled(self):
        auth = PaymentAuthorization(
            correlation_id="CID2",
            authorization_id="AUTH-CID2",
            amount=300.0,
            flight_fare=250.0,
            other_charges=50.0,
            status="CANCELLED"
        )
        self.assertIn("CANCELLED", str(auth))


# ============================================================================
# SAGA VIEWS TESTS
# ============================================================================

class AuthorizePaymentTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("saga_authorize_payment")
        # clear shared dict between tests
        from payment.saga_views import saga_payment_authorizations
        saga_payment_authorizations.clear()

    def _post(self, data):
        return self.client.post(
            self.url, json.dumps(data), content_type="application/json"
        )

    def test_authorize_success(self):
        r = self._post({
            "correlation_id": "AP_CID_001",
            "booking_data": {"flight_fare": 300.0}
        })
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["correlation_id"], "AP_CID_001")
        # authorization_id = f"AUTH-{correlation_id[:8]}" → "AUTH-AP_CID_0"
        self.assertEqual(data["authorization_id"], "AUTH-AP_CID_0")
        self.assertAlmostEqual(data["flight_fare"], 300.0)
        self.assertAlmostEqual(data["other_charges"], 50.0)
        self.assertAlmostEqual(data["amount"], 350.0)
        self.assertEqual(data["status"], "AUTHORIZED")

    def test_authorize_simulate_failure(self):
        r = self._post({
            "correlation_id": "AP_FAIL_001",
            "booking_data": {"flight_fare": 300.0},
            "simulate_failure": True
        })
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertFalse(data["success"])
        self.assertIn("error", data)

    def test_authorize_fallback_fare(self):
        r = self._post({
            "correlation_id": "AP_FALL_001",
            "booking_data": {
                "flight_fare": 0,
                "flight": {"economy_fare": 400}
            }
        })
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["success"])
        self.assertAlmostEqual(data["flight_fare"], 400)

    def test_authorize_no_flight_fare_uses_default(self):
        r = self._post({
            "correlation_id": "AP_DEF_001",
            "booking_data": {}
        })
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["success"])
        # default fare = 500 from flight data fallback
        self.assertAlmostEqual(data["flight_fare"], 500)

    def test_stores_in_saga_dict(self):
        from payment.saga_views import saga_payment_authorizations
        self._post({
            "correlation_id": "AP_STORE_001",
            "booking_data": {"flight_fare": 200.0}
        })
        self.assertIn("AP_STORE_001", saga_payment_authorizations)
        self.assertEqual(saga_payment_authorizations["AP_STORE_001"]["status"], "AUTHORIZED")


class CancelPaymentTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("saga_cancel_payment")
        from payment.saga_views import saga_payment_authorizations
        saga_payment_authorizations.clear()

    def _post(self, data):
        return self.client.post(
            self.url, json.dumps(data), content_type="application/json"
        )

    def _authorize(self, cid, fare=300.0):
        from payment.saga_views import saga_payment_authorizations
        saga_payment_authorizations[cid] = {
            "authorization_id": f"AUTH-{cid[:8]}",
            "amount": fare + 50.0,
            "flight_fare": fare,
            "other_charges": 50.0,
            "currency": "USD",
            "status": "AUTHORIZED",
            "payment_method": "mock_card"
        }

    def test_cancel_existing(self):
        self._authorize("CP_CID_001")
        r = self._post({"correlation_id": "CP_CID_001"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["status"], "CANCELLED")
        self.assertIn("authorization_id", data)
        self.assertAlmostEqual(data["amount"], 350.0)

    def test_cancel_no_record(self):
        r = self._post({"correlation_id": "CP_NONE_001"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["success"])
        self.assertIn("No payment authorization", data["message"])

    def test_cancel_updates_dict_status(self):
        self._authorize("CP_STATUS_001")
        self._post({"correlation_id": "CP_STATUS_001"})
        from payment.saga_views import saga_payment_authorizations
        self.assertEqual(saga_payment_authorizations["CP_STATUS_001"]["status"], "CANCELLED")


class CancelPaymentCompleteTest(TestCase):
    def setUp(self):
        from payment.saga_views import saga_payment_authorizations
        saga_payment_authorizations.clear()

    def _call(self, cid):
        from django.test import RequestFactory
        import json as _j
        from payment.saga_compensation import cancel_payment_complete
        rf = RequestFactory()
        req = rf.post("/", _j.dumps({"correlation_id": cid}), content_type="application/json")
        return cancel_payment_complete(req)

    def _authorize(self, cid, fare=200.0):
        from payment.saga_views import saga_payment_authorizations
        saga_payment_authorizations[cid] = {
            "authorization_id": f"AUTH-{cid[:8]}",
            "amount": fare + 50.0,
            "flight_fare": fare,
            "other_charges": 50.0,
            "currency": "USD",
            "status": "AUTHORIZED",
            "payment_method": "mock_card"
        }

    def test_no_record(self):
        resp = self._call("CPC_NONE_001")
        data = json.loads(resp.content)
        self.assertTrue(data["success"])
        self.assertIn("No payment authorization", data["message"])

    def test_cancels_existing(self):
        self._authorize("CPC_CID_001")
        resp = self._call("CPC_CID_001")
        data = json.loads(resp.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["status"], "CANCELLED")
        from payment.saga_views import saga_payment_authorizations
        self.assertEqual(saga_payment_authorizations["CPC_CID_001"]["status"], "CANCELLED")


# ============================================================================
# VIEWS TESTS (Stripe-backed — mock stripe calls)
# ============================================================================

class ProcessPaymentViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("process_payment")

    def _post(self, data):
        return self.client.post(
            self.url, json.dumps(data), content_type="application/json"
        )

    def test_missing_amount_returns_400(self):
        r = self._post({"payment_method_id": "pm_xxx"})
        self.assertEqual(r.status_code, 400)

    def test_missing_payment_method_returns_400(self):
        r = self._post({"amount": 100.0})
        self.assertEqual(r.status_code, 400)

    @patch("payment.views.stripe.PaymentIntent.create")
    def test_successful_payment(self, mock_create):
        mock_intent = MagicMock()
        mock_intent.id = "pi_test_001"
        mock_intent.status = "succeeded"
        mock_create.return_value = mock_intent
        r = self._post({"amount": 150.0, "payment_method_id": "pm_test"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["payment_id"], "pi_test_001")

    @patch("payment.views.stripe.PaymentIntent.create")
    def test_card_error_returns_400(self, mock_create):
        mock_create.side_effect = Exception("Your card was declined")
        r = self._post({"amount": 100.0, "payment_method_id": "pm_test"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("card", r.json()["error"].lower())

    @patch("payment.views.stripe.PaymentIntent.create")
    def test_payment_gateway_error_returns_500(self, mock_create):
        mock_create.side_effect = Exception("Gateway timeout")
        r = self._post({"amount": 100.0, "payment_method_id": "pm_test"})
        self.assertEqual(r.status_code, 500)


class StripeWebhookViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("stripe_webhook")

    def _post(self, payload):
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )

    def test_webhook_payment_succeeded(self):
        r = self._post({
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_001"}}
        })
        self.assertEqual(r.status_code, 200)

    def test_webhook_payment_failed(self):
        r = self._post({
            "type": "payment_intent.payment_failed",
            "data": {"object": {"id": "pi_002"}}
        })
        self.assertEqual(r.status_code, 200)

    def test_webhook_unknown_event(self):
        r = self._post({
            "type": "unknown.event",
            "data": {"object": {}}
        })
        self.assertEqual(r.status_code, 200)

    @patch("payment.views.stripe.Webhook.construct_event")
    def test_invalid_signature_returns_400(self, mock_construct):
        import os
        with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "whsec_test"}):
            mock_construct.side_effect = Exception("Invalid signature")
            r = self.client.post(
                self.url,
                data=b"rawpayload",
                content_type="application/octet-stream",
                HTTP_STRIPE_SIGNATURE="bad_sig"
            )
            self.assertEqual(r.status_code, 400)


class PaymentStatusViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    @patch("payment.views.stripe.PaymentIntent.retrieve")
    def test_payment_status_success(self, mock_retrieve):
        mock_intent = MagicMock()
        mock_intent.status = "succeeded"
        mock_intent.amount = 15000
        mock_intent.currency = "usd"
        mock_retrieve.return_value = mock_intent
        r = self.client.get(reverse("payment_status", kwargs={"payment_id": "pi_test"}))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["payment_id"], "pi_test")
        self.assertEqual(data["status"], "succeeded")
        self.assertAlmostEqual(data["amount"], 150.0)

    @patch("payment.views.stripe.PaymentIntent.retrieve")
    def test_payment_not_found_returns_404(self, mock_retrieve):
        mock_retrieve.side_effect = Exception("No such payment intent")
        r = self.client.get(reverse("payment_status", kwargs={"payment_id": "pi_invalid"}))
        self.assertEqual(r.status_code, 404)


class ProcessRefundViewTest(TestCase):
    """
    The refund URL /api/payments/refund/ is shadowed by the <payment_id> catch-all
    route above it in payment/urls.py.  We call the view function directly via
    RequestFactory to test its logic independently of that routing quirk.
    """

    def _rf_post(self, data):
        from django.test import RequestFactory
        from payment.views import process_refund
        rf = RequestFactory()
        req = rf.post("/", json.dumps(data), content_type="application/json")
        return process_refund(req)

    def _json(self, resp):
        import json as _j
        return _j.loads(resp.content)

    def test_missing_payment_id_returns_400(self):
        resp = self._rf_post({"amount": 50.0})
        self.assertEqual(resp.status_code, 400)

    @patch("payment.views.stripe.Refund.create")
    def test_successful_refund(self, mock_refund):
        mock_r = MagicMock()
        mock_r.id = "re_test_001"
        mock_r.status = "succeeded"
        mock_r.amount = 5000
        mock_refund.return_value = mock_r
        resp = self._rf_post({"payment_id": "pi_test", "amount": 50.0})
        self.assertEqual(resp.status_code, 200)
        data = self._json(resp)
        self.assertTrue(data["success"])
        self.assertEqual(data["refund_id"], "re_test_001")

    @patch("payment.views.stripe.Refund.create")
    def test_refund_error_returns_500(self, mock_refund):
        mock_refund.side_effect = Exception("Refund failed")
        resp = self._rf_post({"payment_id": "pi_test"})
        self.assertEqual(resp.status_code, 500)


class ValidateCardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("validate_card")

    def _post(self, data):
        return self.client.post(
            self.url, json.dumps(data), content_type="application/json"
        )

    def test_missing_field_returns_400(self):
        r = self._post({"card_number": "4111111111111111", "cvv": "123"})
        self.assertEqual(r.status_code, 400)

    def test_valid_card(self):
        r = self._post({
            "card_number": "4111111111111111",
            "cvv": "123",
            "expiry_month": "12",
            "expiry_year": "2027"
        })
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["valid"])
        self.assertEqual(data["last_four"], "1111")
        self.assertEqual(data["card_type"], "visa")


class HealthCheckViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check(self):
        r = self.client.get(reverse("health_check"))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "payment-service")
