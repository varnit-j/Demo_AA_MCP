
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def process_payment(request):
    """Process payment through Stripe or mock banking system"""
    try:
        data = json.loads(request.body)
        
        # Basic payment processing logic
        payment_method = data.get('payment_method', 'stripe')
        amount = data.get('amount')
        currency = data.get('currency', 'usd')
        
        if not amount:
            return JsonResponse({'error': 'Amount is required'}, status=400)
        
        # Mock payment processing
        return JsonResponse({
            'success': True,
            'payment_id': 'pay_mock_123456',
            'status': 'succeeded',
            'amount': amount,
            'currency': currency
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Payment processing error: {e}")
        return JsonResponse({'error': 'Payment processing failed'}, status=500)

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    try:
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        # Mock webhook processing
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return HttpResponse(status=400)

def payment_status(request, payment_id):
    """Get payment status"""
    try:
        # Mock payment status lookup
        return JsonResponse({
            'payment_id': payment_id,
            'status': 'succeeded',
            'amount': 100.00,
            'currency': 'usd'
        })
    except Exception as e:
        logger.error(f"Payment status error: {e}")
        return JsonResponse({'error': 'Payment not found'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
def process_refund(request):
    """Process payment refund"""
    try:
        data = json.loads(request.body)
        payment_id = data.get('payment_id')
        amount = data.get('amount')
        
        if not payment_id:
            return JsonResponse({'error': 'Payment ID is required'}, status=400)
        
        # Mock refund processing
        return JsonResponse({
            'success': True,
            'refund_id': 'ref_mock_123456',
            'status': 'succeeded',
            'amount': amount,
            'payment_id': payment_id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Refund processing error: {e}")
        return JsonResponse({'error': 'Refund processing failed'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def validate_card(request):
    """Validate card through mock banking system"""
    try:
        data = json.loads(request.body)
        card_number = data.get('card_number')
        cvv = data.get('cvv')
        expiry_month = data.get('expiry_month')
        expiry_year = data.get('expiry_year')
        
        if not all([card_number, cvv, expiry_month, expiry_year]):
            return JsonResponse({'error': 'All card details are required'}, status=400)
        
        # Mock card validation
        return JsonResponse({
            'valid': True,
            'card_type': 'visa',
            'last_four': card_number[-4:] if len(card_number) >= 4 else '****'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Card validation error: {e}")
        return JsonResponse({'error': 'Card validation failed'}, status=500)