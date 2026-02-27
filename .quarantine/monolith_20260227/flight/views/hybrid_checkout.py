
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from decimal import Decimal
import json
import logging

from flight.models import Ticket
from apps.orders.models import Order
from apps.orders.service import OrderService
from apps.loyalty.service import LoyaltyService
from apps.payments.stripe_client import StripeClient

logger = logging.getLogger(__name__)


@login_required
def hybrid_checkout_page(request, ticket_id):
    """Display hybrid checkout page for a ticket"""
    
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    
    # Get user's loyalty account and points balance
    loyalty_account = LoyaltyService.get_or_create_account(request.user)
    available_points = loyalty_account.current_points_balance
    
    # Calculate base pricing
    base_amount = ticket.total_fare or Decimal('0.00')
    
    # Calculate maximum points that can be used (e.g., up to 50% of total)
    max_points_usable = min(available_points, int(base_amount * 50))  # 50 points per dollar max
    
    context = {
        'ticket': ticket,
        'loyalty_account': loyalty_account,
        'available_points': available_points,
        'max_points_usable': max_points_usable,
        'base_amount': base_amount,
        'points_value_rate': Decimal('0.01'),  # 1 point = $0.01
    }
    
    return render(request, 'flight/hybrid_checkout.html', context)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def calculate_hybrid_pricing(request):
    """Calculate hybrid pricing breakdown via AJAX"""
    
    try:
        data = json.loads(request.body)
        ticket_id = data.get('ticket_id')
        points_to_use = int(data.get('points_to_use', 0))
        
        if not ticket_id:
            return JsonResponse({'error': 'Ticket ID is required'}, status=400)
        
        # Get the ticket
        ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
        total_amount = ticket.total_fare or Decimal('0.00')
        
        # Calculate hybrid pricing
        pricing = OrderService.calculate_hybrid_pricing(
            user=request.user,
            total_amount=total_amount,
            points_to_use=points_to_use
        )
        
        return JsonResponse({
            'success': True,
            'pricing': {
                'total_amount': float(pricing['total_amount']),
                'points_used': pricing['points_used'],
                'points_value': float(pricing['points_value']),
                'cash_amount': float(pricing['cash_amount']),
                'savings': float(pricing['savings'])
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating hybrid pricing: {e}")
        return JsonResponse({'error': 'Calculation error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def process_hybrid_redemption(request):
    """Process points redemption and create order"""
    
    try:
        data = json.loads(request.body)
        ticket_id = data.get('ticket_id')
        points_to_use = int(data.get('points_to_use', 0))
        
        if not ticket_id:
            return JsonResponse({'error': 'Ticket ID is required'}, status=400)
        
        # Get the ticket
        ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
        
        # Validate points amount
        available_points = LoyaltyService.get_points_balance(request.user)
        if points_to_use > available_points:
            return JsonResponse({'error': 'Insufficient points'}, status=400)
        
        # Create order with hybrid payment
        order = OrderService.create_order_from_tickets(
            user=request.user,
            tickets=[ticket],
            payment_method='hybrid',
            points_to_use=points_to_use
        )
        
        # If there's a cash amount remaining, create payment intent
        payment_intent = None
        if order.cash_amount > 0:
            payment_intent = StripeClient.create_payment_intent(
                amount=order.cash_amount,
                currency='usd',
                metadata={
                    'order_id': str(order.id),
                    'order_number': order.order_number,
                    'user_id': str(request.user.id)
                },
                customer_email=request.user.email,
                description=f"Hybrid payment for order {order.order_number}"
            )
            
            # Update order with payment intent
            order.metadata = order.metadata or {}
            order.metadata['stripe_payment_intent_id'] = payment_intent['id']
            order.save()
        
        return JsonResponse({
            'success': True,
            'order_id': str(order.id),
            'order_number': order.order_number,
            'points_used': order.points_used,
            'points_value': float(order.points_value),
            'cash_amount': float(order.cash_amount),
            'payment_intent': {
                'client_secret': payment_intent['client_secret'] if payment_intent else None,
                'amount': float(order.cash_amount)
            } if payment_intent else None
        })
        
    except Exception as e:
        logger.error(f"Error processing hybrid redemption: {e}")
        return JsonResponse({'error': 'Processing error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def confirm_hybrid_payment(request):
    """Confirm hybrid payment completion"""
    
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        payment_intent_id = data.get('payment_intent_id')
        
        if not order_id:
            return JsonResponse({'error': 'Order ID is required'}, status=400)
        
        # Get the order
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Process the hybrid payment
        OrderService.process_hybrid_payment(order, payment_intent_id)
        
        return JsonResponse({
            'success': True,
            'order_number': order.order_number,
            'status': order.status,
            'message': 'Payment completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error confirming hybrid payment: {e}")
        return JsonResponse({'error': 'Confirmation error'}, status=500)