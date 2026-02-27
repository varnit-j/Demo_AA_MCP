
from django.db import transaction
from django.contrib.auth import get_user_model
from decimal import Decimal
import logging

from .models import Order
from flight.models import Ticket
from apps.loyalty.service import LoyaltyService

User = get_user_model()
logger = logging.getLogger(__name__)


class OrderService:
    """Service layer for order management and hybrid pricing calculations"""
    
    @staticmethod
    @transaction.atomic
    def create_order_from_tickets(user, tickets, payment_method='cash_only', points_to_use=0):
        """Create order from existing flight tickets"""
        
        # Create the order
        order = Order.objects.create(
            user=user,
            payment_method=payment_method,
            status='draft'
        )
        
        # Calculate totals from tickets
        subtotal = Decimal('0.00')
        
        for ticket in tickets:
            if ticket.total_fare:
                subtotal += ticket.total_fare
        
        # Add fees
        fees_amount = Decimal('100.00')  # From flight.constant.FEE
        
        # Update order totals
        order.subtotal = subtotal
        order.fees_amount = fees_amount
        order.total_amount = subtotal + fees_amount
        
        # Handle points redemption if hybrid payment
        if payment_method in ['hybrid', 'points_only'] and points_to_use > 0:
            points_value = OrderService._calculate_points_value(user, points_to_use)
            order.points_used = points_to_use
            order.points_value = points_value
            order.cash_amount = max(Decimal('0.00'), order.total_amount - points_value)
        else:
            order.cash_amount = order.total_amount
        
        order.save()
        
        logger.info(f"Created order {order.order_number} for user {user.username}")
        
        return order
    
    @staticmethod
    def calculate_hybrid_pricing(user, total_amount, points_to_use):
        """Calculate hybrid pricing breakdown"""
        
        # Get user's available points
        available_points = LoyaltyService.get_points_balance(user)
        
        # Validate points amount
        actual_points_to_use = min(points_to_use, available_points)
        
        # Calculate points value
        points_value = OrderService._calculate_points_value(user, actual_points_to_use)
        
        # Calculate remaining cash amount
        cash_amount = max(Decimal('0.00'), total_amount - points_value)
        
        return {
            'total_amount': total_amount,
            'points_used': actual_points_to_use,
            'points_value': points_value,
            'cash_amount': cash_amount,
            'savings': points_value
        }
    
    @staticmethod
    def _calculate_points_value(user, points_amount):
        """Calculate currency value of points for user"""
        if points_amount <= 0:
            return Decimal('0.00')
        
        # Base rate: 1 point = $0.01
        base_rate = Decimal('0.01')
        
        # Get user's tier bonus if available
        try:
            account = user.loyalty_account
            if account.current_tier:
                return Decimal(points_amount) * base_rate * account.current_tier.redemption_bonus
        except:
            pass
        
        return Decimal(points_amount) * base_rate
    
    @staticmethod
    @transaction.atomic
    def process_hybrid_payment(order, stripe_payment_intent_id=None):
        """Process hybrid payment for order"""
        
        if not order.is_hybrid_payment:
            raise ValueError("Order is not configured for hybrid payment")
        
        # Redeem points first
        if order.points_used > 0:
            LoyaltyService.redeem_points(
                user=order.user,
                points_amount=order.points_used,
                reference_id=order.order_number,
                description=f"Flight booking payment (USD) - Order {order.order_number}"
            )
        
        # Update order status
        if order.cash_amount > 0:
            order.status = 'partially_paid' if stripe_payment_intent_id else 'pending_payment'
        else:
            order.status = 'paid'
        
        order.save()
        
        logger.info(f"Processed hybrid payment for order {order.order_number}")
        
        return order
    
    @staticmethod
    def get_order_summary(order):
        """Get order summary for display"""
        return {
            'order_number': order.order_number,
            'total_amount': order.total_amount,
            'payment_method': order.get_payment_method_display(),
            'points_used': order.points_used,
            'points_value': order.points_value,
            'cash_amount': order.cash_amount,
            'status': order.get_status_display(),
            'created_at': order.created_at
        }