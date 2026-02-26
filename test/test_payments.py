"""
Tests for payments/views.py and payments/webhooks.py

Uses unittest.mock to patch all Stripe calls so no real API keys are needed.
"""
import json
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.orders.models import Order

User = get_user_model()


# ──────────────────────────────────────────────────────────────
#  Helpers / Fixtures
# ──────────────────────────────────────────────────────────────

@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='payuser',
        email='pay@example.com',
        password='pass1234',
        first_name='Pay',
        last_name='User'
    )


@pytest.fixture
def auth_client(user):
    c = Client()
    c.login(username='payuser', password='pass1234')
    return c


def _make_order(user, status='pending_payment', payment_method='cash_only',
                total_amount='200.00', cash_amount='200.00', points_used=0,
                points_value='0.00'):
    return Order.objects.create(
        user=user,
        status=status,
        payment_method=payment_method,
        total_amount=Decimal(total_amount),
        cash_amount=Decimal(cash_amount),
        points_used=points_used,
        points_value=Decimal(points_value),
        subtotal=Decimal(total_amount),
        tax_amount=Decimal('0.00'),
        fees_amount=Decimal('0.00'),
    )


# ──────────────────────────────────────────────────────────────
#  payments/views.py  –  create_payment_intent
# ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCreatePaymentIntent:

    _url = '/payments/create-payment-intent/'

    # helper: fake Stripe response
    _fake_intent = {
        'id': 'pi_test_123',
        'client_secret': 'pi_test_123_secret_abc',
        'amount': Decimal('200.00'),
        'currency': 'usd',
        'status': 'requires_payment_method',
        'metadata': {}
    }

    def test_unauthenticated_redirects(self, client):
        resp = client.post(self._url, data='{}', content_type='application/json')
        # login_required → 302 redirect to login
        assert resp.status_code == 302

    def test_missing_order_id_returns_400(self, auth_client):
        resp = auth_client.post(self._url, data='{}', content_type='application/json')
        assert resp.status_code == 400
        assert 'error' in resp.json()

    def test_order_not_found_returns_404(self, auth_client):
        import uuid
        payload = json.dumps({'order_id': str(uuid.uuid4())})
        resp = auth_client.post(self._url, data=payload, content_type='application/json')
        assert resp.status_code == 404

    def test_order_wrong_status_returns_400(self, user, auth_client):
        order = _make_order(user, status='paid')
        payload = json.dumps({'order_id': str(order.id)})
        resp = auth_client.post(self._url, data=payload, content_type='application/json')
        assert resp.status_code == 400
        assert 'cannot be paid' in resp.json()['error']

    def test_zero_amount_returns_400(self, user, auth_client):
        order = _make_order(user, status='pending_payment', total_amount='0.00', cash_amount='0.00')
        payload = json.dumps({'order_id': str(order.id)})
        resp = auth_client.post(self._url, data=payload, content_type='application/json')
        assert resp.status_code == 400
        assert 'No payment required' in resp.json()['error']

    @patch('payments.views.StripeClient.create_payment_intent')
    def test_successful_cash_payment_intent(self, mock_pi, user, auth_client):
        mock_pi.return_value = self._fake_intent
        order = _make_order(user, status='pending_payment')
        payload = json.dumps({'order_id': str(order.id)})
        resp = auth_client.post(self._url, data=payload, content_type='application/json')
        assert resp.status_code == 200
        data = resp.json()
        assert data['client_secret'] == 'pi_test_123_secret_abc'
        assert data['payment_intent_id'] == 'pi_test_123'
        assert 'order_number' in data

        # Order should now be pending_payment with intent id in metadata
        order.refresh_from_db()
        assert order.status == 'pending_payment'
        assert order.metadata.get('stripe_payment_intent_id') == 'pi_test_123'

    @patch('payments.views.StripeClient.create_payment_intent')
    def test_hybrid_uses_cash_amount(self, mock_pi, user, auth_client):
        mock_pi.return_value = self._fake_intent
        order = _make_order(
            user, status='pending_payment', payment_method='hybrid',
            total_amount='300.00', cash_amount='150.00',
            points_used=1500, points_value='150.00'
        )
        payload = json.dumps({'order_id': str(order.id)})
        resp = auth_client.post(self._url, data=payload, content_type='application/json')
        assert resp.status_code == 200
        # Stripe was called with cash_amount, not total_amount
        called_amount = mock_pi.call_args[1]['amount']
        assert called_amount == Decimal('150.00')

    @patch('payments.views.StripeClient.create_payment_intent', side_effect=Exception("Stripe down"))
    def test_stripe_exception_returns_500(self, mock_pi, user, auth_client):
        order = _make_order(user, status='pending_payment')
        payload = json.dumps({'order_id': str(order.id)})
        resp = auth_client.post(self._url, data=payload, content_type='application/json')
        assert resp.status_code == 500
        assert 'error' in resp.json()


# ──────────────────────────────────────────────────────────────
#  payments/views.py  –  create_checkout_session (direct call)
# ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCreateCheckoutSession:
    """
    create_checkout_session is not wired into urls.py yet, so we call the
    view directly via Django's RequestFactory.
    """

    _fake_session = {
        'id': 'cs_test_abc',
        'url': 'https://checkout.stripe.com/pay/cs_test_abc',
    }

    def _call(self, user, body, authenticated=True):
        from django.test import RequestFactory
        from payments.views import create_checkout_session
        rf = RequestFactory()
        req = rf.post(
            '/payments/create-checkout-session/',
            data=body,
            content_type='application/json'
        )
        req.user = user
        if not authenticated:
            from django.contrib.auth.models import AnonymousUser
            req.user = AnonymousUser()
        return create_checkout_session(req)

    def test_missing_order_id_returns_400(self, user):
        resp = self._call(user, '{}')
        assert resp.status_code == 400

    def test_order_not_found_returns_404(self, user):
        import uuid
        payload = json.dumps({'order_id': str(uuid.uuid4())})
        resp = self._call(user, payload)
        assert resp.status_code == 404

    def test_zero_amount_returns_400(self, user):
        order = _make_order(user, status='pending_payment', total_amount='0.00', cash_amount='0.00')
        payload = json.dumps({'order_id': str(order.id)})
        resp = self._call(user, payload)
        assert resp.status_code == 400

    @patch('payments.views.StripeClient.create_checkout_session')
    def test_successful_session_creation(self, mock_cs, user):
        mock_cs.return_value = self._fake_session
        order = _make_order(user, status='draft')
        payload = json.dumps({'order_id': str(order.id)})
        resp = self._call(user, payload)
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data['session_id'] == 'cs_test_abc'
        assert 'checkout_url' in data
        order.refresh_from_db()
        assert order.status == 'pending_payment'
        assert order.metadata.get('stripe_checkout_session_id') == 'cs_test_abc'

    @patch('payments.views.StripeClient.create_checkout_session', side_effect=Exception("Stripe error"))
    def test_stripe_exception_returns_500(self, mock_cs, user):
        order = _make_order(user, status='pending_payment')
        payload = json.dumps({'order_id': str(order.id)})
        resp = self._call(user, payload)
        assert resp.status_code == 500


# ──────────────────────────────────────────────────────────────
#  payments/webhooks.py  –  stripe_webhook
# ──────────────────────────────────────────────────────────────

WEBHOOK_URL = '/payments/webhook/'


def _post_webhook(client, event_type, obj_data):
    """Helper: POST a fake Stripe webhook event."""
    event = {
        'type': event_type,
        'data': {'object': obj_data}
    }
    with patch('payments.webhooks.StripeClient.construct_webhook_event', return_value=event):
        return client.post(
            WEBHOOK_URL,
            data=json.dumps({'payload': 'x'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=1,v1=abc'
        )


@pytest.mark.django_db
class TestStripeWebhook:

    def test_invalid_signature_returns_400(self, client):
        with patch('payments.webhooks.StripeClient.construct_webhook_event',
                   side_effect=Exception("Invalid signature")):
            resp = client.post(
                WEBHOOK_URL,
                data=b'bad payload',
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='invalid'
            )
        assert resp.status_code == 400

    def test_unhandled_event_type_returns_200(self, client):
        resp = _post_webhook(client, 'customer.created', {'id': 'cus_123'})
        assert resp.status_code == 200

    # ── payment_intent.succeeded ──

    def test_payment_succeeded_no_metadata_order_id(self, client):
        obj = {'id': 'pi_123', 'metadata': {}}
        resp = _post_webhook(client, 'payment_intent.succeeded', obj)
        assert resp.status_code == 200  # handler swallows the error gracefully

    def test_payment_succeeded_order_not_found(self, client):
        import uuid
        obj = {'id': 'pi_123', 'metadata': {'order_id': str(uuid.uuid4())}}
        resp = _post_webhook(client, 'payment_intent.succeeded', obj)
        assert resp.status_code == 200

    def test_payment_succeeded_cash_order_marked_paid(self, user, client):
        order = _make_order(user, status='pending_payment', payment_method='cash_only')
        obj = {'id': 'pi_123', 'metadata': {'order_id': str(order.id)}}
        resp = _post_webhook(client, 'payment_intent.succeeded', obj)
        assert resp.status_code == 200
        order.refresh_from_db()
        assert order.status == 'paid'
        assert order.metadata.get('stripe_payment_intent_id') == 'pi_123'
        assert order.metadata.get('payment_status') == 'succeeded'

    @patch('payments.webhooks.OrderService.process_hybrid_payment')
    def test_payment_succeeded_hybrid_calls_service(self, mock_ph, user, client):
        order = _make_order(
            user, status='pending_payment', payment_method='hybrid',
            total_amount='300.00', cash_amount='150.00',
            points_used=1500, points_value='150.00'
        )
        obj = {'id': 'pi_hyb', 'metadata': {'order_id': str(order.id)}}
        resp = _post_webhook(client, 'payment_intent.succeeded', obj)
        assert resp.status_code == 200
        mock_ph.assert_called_once_with(order, 'pi_hyb')

    # ── payment_intent.payment_failed ──

    def test_payment_failed_resets_status(self, user, client):
        order = _make_order(user, status='pending_payment')
        obj = {
            'id': 'pi_fail',
            'metadata': {'order_id': str(order.id)},
            'last_payment_error': {'message': 'Card declined'}
        }
        resp = _post_webhook(client, 'payment_intent.payment_failed', obj)
        assert resp.status_code == 200
        order.refresh_from_db()
        assert order.status == 'pending_payment'
        assert order.metadata.get('payment_status') == 'failed'
        assert order.metadata.get('failure_reason') == 'Card declined'

    def test_payment_failed_no_order_id(self, client):
        obj = {'id': 'pi_fail', 'metadata': {}, 'last_payment_error': {}}
        resp = _post_webhook(client, 'payment_intent.payment_failed', obj)
        assert resp.status_code == 200

    # ── checkout.session.completed ──

    def test_checkout_completed_marks_paid(self, user, client):
        order = _make_order(user, status='pending_payment')
        obj = {
            'id': 'cs_done',
            'metadata': {'order_id': str(order.id)},
            'payment_status': 'paid'
        }
        resp = _post_webhook(client, 'checkout.session.completed', obj)
        assert resp.status_code == 200
        order.refresh_from_db()
        assert order.status == 'paid'
        assert order.metadata.get('stripe_checkout_session_id') == 'cs_done'

    def test_checkout_completed_unpaid_skips_status_update(self, user, client):
        order = _make_order(user, status='pending_payment')
        obj = {
            'id': 'cs_unpaid',
            'metadata': {'order_id': str(order.id)},
            'payment_status': 'unpaid'
        }
        resp = _post_webhook(client, 'checkout.session.completed', obj)
        assert resp.status_code == 200
        order.refresh_from_db()
        # status should remain unchanged
        assert order.status == 'pending_payment'

    def test_checkout_completed_no_order_id(self, client):
        obj = {'id': 'cs_noid', 'metadata': {}, 'payment_status': 'paid'}
        resp = _post_webhook(client, 'checkout.session.completed', obj)
        assert resp.status_code == 200

    # ── payment_intent.canceled ──

    def test_payment_canceled_sets_cancelled_status(self, user, client):
        order = _make_order(user, status='pending_payment')
        obj = {'id': 'pi_cancel', 'metadata': {'order_id': str(order.id)}}
        resp = _post_webhook(client, 'payment_intent.canceled', obj)
        assert resp.status_code == 200
        order.refresh_from_db()
        assert order.status == 'cancelled'
        assert order.metadata.get('payment_status') == 'canceled'

    def test_payment_canceled_no_order_id(self, client):
        obj = {'id': 'pi_cancel', 'metadata': {}}
        resp = _post_webhook(client, 'payment_intent.canceled', obj)
        assert resp.status_code == 200

    def test_payment_canceled_order_not_found(self, client):
        import uuid
        obj = {'id': 'pi_cancel', 'metadata': {'order_id': str(uuid.uuid4())}}
        resp = _post_webhook(client, 'payment_intent.canceled', obj)
        assert resp.status_code == 200
