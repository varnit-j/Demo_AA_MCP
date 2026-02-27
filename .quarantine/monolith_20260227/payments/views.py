
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings
import json
import logging
from decimal import Decimal

from apps.payments.stripe_client import StripeClient
from apps.orders.models import Order
from apps.orders.service import OrderService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_payment_intent(request):
    """Create a Stripe PaymentIntent for order payment"""
    
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        
        if not order_id:
            return JsonResponse({'error': 'Order ID is required'}, status=400)
        
        # Get the order
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
        
        # Validate order status
        if order.status not in ['draft', 'pending_payment', 'partially_paid']:
            return JsonResponse({'error': 'Order cannot be paid'}, status=400)
        
        # Calculate amount to charge (remaining balance for hybrid payments)
        amount_to_charge = order.cash_amount if order.payment_method == 'hybrid' else order.total_amount
        
        if amount_to_charge <= 0:
            return JsonResponse({'error': 'No payment required'}, status=400)
        
        # Create PaymentIntent
        payment_intent = StripeClient.create_payment_intent(
            amount=amount_to_charge,
            currency='usd',
            metadata={
                'order_id': str(order.id),
                'order_number': order.order_number,
                'user_id': str(request.user.id),
                'payment_method': order.payment_method
            },
            customer_email=request.user.email,
            description=f"Flight booking payment - Order {order.order_number}"
        )
        
        # Update order with payment intent
        order.metadata = order.metadata or {}
        order.metadata['stripe_payment_intent_id'] = payment_intent['id']
        order.status = 'pending_payment'
        order.save()
        
        logger.info(f"Created PaymentIntent for order {order.order_number}")
        
        return JsonResponse({
            'client_secret': payment_intent['client_secret'],
            'payment_intent_id': payment_intent['id'],
            'amount': float(amount_to_charge),
            'order_number': order.order_number
        })
        
    except Exception as e:
        logger.error(f"Error creating PaymentIntent: {e}")
        return JsonResponse({'error': 'Payment processing error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def create_checkout_session(request):
    """Create a Stripe Checkout Session for order payment"""
    
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        
        if not order_id:
            return JsonResponse({'error': 'Order ID is required'}, status=400)
        
        # Get the order
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
        
        # Calculate amount to charge
        amount_to_charge = order.cash_amount if order.payment_method == 'hybrid' else order.total_amount
        
        if amount_to_charge <= 0:
            return JsonResponse({'error': 'No payment required'}, status=400)
        
        # Prepare line items for Stripe Checkout
        line_items = [{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f'Flight Booking - Order {order.order_number}',
                    'description': 'Flight ticket payment'
                },
                'unit_amount': int(amount_to_charge * 100),  # Convert to cents
            },
            'quantity': 1,
        }]
        
        # Create success and cancel URLs
        success_url = request.build_absolute_uri(f'/payments/success?session_id={{CHECKOUT_SESSION_ID}}')
        cancel_url = request.build_absolute_uri(f'/payments/cancel?order_id={order.id}')
        
        # Create Checkout Session
        session = StripeClient.create_checkout_session(
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=request.user.email,
            metadata={
                'order_id': str(order.id),
                'order_number': order.order_number,
                'user_id': str(request.user.id)
            }
        )
        
        # Update order with session info
        order.metadata = order.metadata or {}
        order.metadata['stripe_checkout_session_id'] = session['id']
        order.status = 'pending_payment'
        order.save()
        
        logger.info(f"Created Checkout Session for order {order.order_number}")
        
        return JsonResponse({
            'checkout_url': session['url'],
            'session_id': session['id'],
            'order_number': order.order_number
        })
        
    except Exception as e:
        logger.error(f"Error creating Checkout Session: {e}")
        return JsonResponse({'error': 'Checkout creation error'}, status=500)