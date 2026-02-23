
"""
SAGA Views for Payment Service
Handles AuthorizePayment and CancelPayment operations
"""
import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

# SAGA-specific storage for tracking payment authorizations
saga_payment_authorizations = {}

@csrf_exempt
@require_http_methods(["POST"])
def authorize_payment(request):
    """SAGA Step 2: Authorize payment for booking"""
    try:
        data = json.loads(request.body)
        correlation_id = data.get('correlation_id')
        booking_data = data.get('booking_data', {})
        simulate_failure = data.get('simulate_failure', False)
        
        logger.info(f"[SAGA PAYMENT] 💳 AuthorizePayment step initiated for correlation_id: {correlation_id}")
        logger.info(f"[SAGA PAYMENT] 📊 Processing payment authorization for booking")
        
        # Simulate failure if requested
        if simulate_failure:
            logger.error(f"[SAGA PAYMENT] ❌ Simulated failure in AuthorizePayment for {correlation_id}")
            logger.error(f"[SAGA PAYMENT] 🔄 This will trigger compensation for seat reservation")
            return JsonResponse({
                "success": False,
                "error": "Simulated payment authorization failure - payment gateway unavailable"
            })
        
        # FLIGHT DATA DEBUG: Log payment authorization data
        logger.info(f"[FLIGHT_DATA_DEBUG] ===== PAYMENT AUTHORIZATION =====")
        logger.info(f"[FLIGHT_DATA_DEBUG] Correlation ID: {correlation_id}")
        logger.info(f"[FLIGHT_DATA_DEBUG] Booking data keys: {list(booking_data.keys())}")
        
        # Extract payment information
        flight_fare = booking_data.get('flight_fare', 0)
        logger.info(f"[FLIGHT_DATA_DEBUG] Flight fare from booking_data: {flight_fare}")
        
        if not flight_fare:
            # Try to get fare from flight data
            flight_data = booking_data.get('flight', {})
            flight_fare = flight_data.get('economy_fare', 500)  # Default fare
            logger.info(f"[FLIGHT_DATA_DEBUG] ⚠️ Using fallback fare from flight data: {flight_fare}")
            logger.info(f"[FLIGHT_DATA_DEBUG] Flight data available: {flight_data}")
        else:
            logger.info(f"[FLIGHT_DATA_DEBUG] ✓ Using flight_fare from booking_data: {flight_fare}")
        
        other_charges = 50.0  # Standard charges
        total_amount = float(flight_fare) + other_charges
        
        # Mock payment authorization
        authorization_id = f"AUTH-{correlation_id[:8]}"
        
        # Store authorization record
        saga_payment_authorizations[correlation_id] = {
            "authorization_id": authorization_id,
            "amount": total_amount,
            "flight_fare": flight_fare,
            "other_charges": other_charges,
            "currency": "USD",
            "status": "AUTHORIZED",
            "payment_method": "mock_card"
        }
        
        logger.info(f"[SAGA PAYMENT] ✅ Payment authorized successfully! Amount: ${total_amount}")
        logger.info(f"[SAGA PAYMENT] 🎯 Authorization ID: {authorization_id}")
        logger.info(f"[SAGA PAYMENT] [INTER-SERVICE] -> UI should now prompt payment details for correlation_id={correlation_id} (not mark BOOKED yet)")
        
        return JsonResponse({
            "success": True,
            "correlation_id": correlation_id,
            "authorization_id": authorization_id,
            "amount": total_amount,
            "flight_fare": flight_fare,
            "other_charges": other_charges,
            "currency": "USD",
            "status": "AUTHORIZED"
        })
        
    except Exception as e:
        logger.error(f"[SAGA] Error in AuthorizePayment: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        })

@csrf_exempt
@require_http_methods(["POST"])
def cancel_payment(request):
    """SAGA Compensation: Cancel payment authorization"""
    try:
        data = json.loads(request.body)
        correlation_id = data.get('correlation_id')
        
        logger.info(f"[SAGA PAYMENT COMPENSATION] 🔄 CancelPayment compensation initiated for correlation_id: {correlation_id}")
        
        # Check if we have an authorization record
        if correlation_id not in saga_payment_authorizations:
            logger.warning(f"[SAGA PAYMENT COMPENSATION] ⚠️ No payment authorization found for {correlation_id}")
            logger.info(f"[SAGA PAYMENT COMPENSATION] ✅ No compensation needed - no payment was authorized")
            return JsonResponse({
                "success": True,  # Return success even if no record found
                "message": "No payment authorization to cancel - compensation complete",
                "correlation_id": correlation_id
            })
        
        auth_record = saga_payment_authorizations[correlation_id]
        authorization_id = auth_record['authorization_id']
        amount = auth_record['amount']
        
        logger.info(f"[SAGA PAYMENT COMPENSATION] 💳 Found authorization to cancel: {authorization_id}")
        logger.info(f"[SAGA PAYMENT COMPENSATION] 💰 Cancelling payment authorization for ${amount}")
        
        # Mock payment cancellation
        # In real implementation, this would call payment gateway to void/cancel authorization
        logger.info(f"[SAGA PAYMENT COMPENSATION] 🏦 Calling payment gateway to void authorization...")
        
        # Update authorization record
        saga_payment_authorizations[correlation_id]['status'] = 'CANCELLED'
        saga_payment_authorizations[correlation_id]['cancelled_at'] = '2026-01-22T15:14:00Z'
        
        logger.info(f"[SAGA PAYMENT COMPENSATION] ✅ Payment authorization cancelled successfully!")
        logger.info(f"[SAGA PAYMENT COMPENSATION] 🎯 Payment service compensation complete for correlation_id: {correlation_id}")
        
        return JsonResponse({
            "success": True,
            "correlation_id": correlation_id,
            "authorization_id": authorization_id,
            "amount": amount,
            "status": "CANCELLED",
            "message": "Payment authorization cancelled successfully"
        })
        
    except Exception as e:
        logger.error(f"[SAGA] Error in CancelPayment: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        })