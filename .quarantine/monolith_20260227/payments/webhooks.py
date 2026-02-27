
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
import json
import logging

from apps.payments.stripe_client import StripeClient
from apps.orders.models import Order
from apps.orders.service import OrderService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        # Construct and verify the webhook event
        event = StripeClient.construct_webhook_event(payload, sig_header)
        
        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            handle_payment_intent_succeeded(event['data']['object'])
        
        elif event['type'] == 'payment_intent.payment_failed':
            handle_payment_intent_failed(event['data']['object'])
        
        elif event['type'] == 'checkout.session.completed':
            handle_checkout_session_completed(event['data']['object'])
        
        elif event['type'] == 'payment_intent.canceled':
            handle_payment_intent_canceled(event['data']['object'])
        
        else:
            logger.info(f"Unhandled event type: {event['type']}")
        
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return HttpResponse(status=400)


def handle_payment_intent_succeeded(payment_intent):
    """Handle successful payment intent"""
    
    try:
        order_id = payment_intent['metadata'].get('order_id')
        if not order_id:
            logger.warning("No order_id in payment_intent metadata")
            return
        
        order = Order.objects.get(id=order_id)
        
        # DEBUG: Log payment completion for loyalty diagnosis
        print(f"DEBUG: Order payment succeeded for user {order.user.username}, order {order.order_number}, total ${order.total_amount}")
        
        # Update order status
        if order.payment_method == 'hybrid':
            # For hybrid payments, process the points redemption
            OrderService.process_hybrid_payment(order, payment_intent['id'])
        else:
            order.status = 'paid'
        
        # TODO: MISSING LOYALTY INTEGRATION - Points should be awarded here for successful payments!
        print(f"DEBUG: Order marked as paid but NO POINTS AWARDED for ${order.total_amount} purchase")
        # Should add: LoyaltyService.earn_points(order.user, points_amount, order.order_number, ...)
        
        # Store payment information
        order.metadata = order.metadata or {}
        order.metadata['stripe_payment_intent_id'] = payment_intent['id']
        order.metadata['payment_status'] = 'succeeded'
        order.save()
        
        logger.info(f"Payment succeeded for order {order.order_number}")
        
    except Order.DoesNotExist:
        logger.error(f"Order not found for payment_intent {payment_intent['id']}")
    except Exception as e:
        logger.error(f"Error handling payment success: {e}")


def handle_payment_intent_failed(payment_intent):
    """Handle failed payment intent"""
    
    try:
        order_id = payment_intent['metadata'].get('order_id')
        if not order_id:
            return
        
        order = Order.objects.get(id=order_id)
        order.status = 'pending_payment'  # Reset to allow retry
        order.metadata = order.metadata or {}
        order.metadata['payment_status'] = 'failed'
        order.metadata['failure_reason'] = payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
        order.save()
        
        logger.warning(f"Payment failed for order {order.order_number}")
        
    except Order.DoesNotExist:
        logger.error(f"Order not found for failed payment_intent {payment_intent['id']}")
    except Exception as e:
        logger.error(f"Error handling payment failure: {e}")

def handle_checkout_session_completed(session):
    """Handle completed checkout session"""
    
    try:
        order_id = session['metadata'].get('order_id')
        if not order_id:
            return
        
        order = Order.objects.get(id=order_id)
        
        # Update order status based on payment status
        if session['payment_status'] == 'paid':
            if order.payment_method == 'hybrid':
                OrderService.process_hybrid_payment(order)
            else:
                order.status = 'paid'
        
        order.metadata = order.metadata or {}
        order.metadata['stripe_checkout_session_id'] = session['id']
        order.metadata['payment_status'] = session['payment_status']
        order.save()
        
        logger.info(f"Checkout session completed for order {order.order_number}")
        
    except Order.DoesNotExist:
        logger.error(f"Order not found for checkout session {session['id']}")
    except Exception as e:
        logger.error(f"Error handling checkout completion: {e}")


def handle_payment_intent_canceled(payment_intent):
    """Handle canceled payment intent"""
    
    try:
        order_id = payment_intent['metadata'].get('order_id')
        if not order_id:
            return
        
        order = Order.objects.get(id=order_id)
        order.status = 'cancelled'
        order.metadata = order.metadata or {}
        order.metadata['payment_status'] = 'canceled'
        order.save()
        
        logger.info(f"Payment canceled for order {order.order_number}")
        
    except Order.DoesNotExist:
        logger.error(f"Order not found for canceled payment_intent {payment_intent['id']}")
    except Exception as e:
        logger.error(f"Error handling payment cancellation: {e}")
    