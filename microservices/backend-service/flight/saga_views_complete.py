

"""
Complete SAGA Views for Backend Service
Integrates SAGA pattern with existing booking system
"""
import logging
import json
import uuid
import requests
import threading
from typing import Dict, Any
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Flight, Place, Week, SagaTransaction, SagaPaymentAuthorization, SagaMilesAward, SeatReservation, Ticket, Passenger
from .simple_views import stored_tickets
from .saga_log_storage import saga_log_storage
from .failed_booking_handler import create_failed_booking_record
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

# SAGA-specific storage - FIXED: Use database instead of memory
# saga_reservations = {}  # REMOVED: This was causing persistence issues
saga_orchestrator = None

def get_or_create_seat_reservation(correlation_id: str, booking_data: Dict[str, Any]) -> 'SeatReservation':
    """
    Database-backed seat reservation instead of memory dictionary
    """
    try:
        from .models import Flight
        flight = Flight.objects.get(id=booking_data.get('flight_id'))
        
        # CRITICAL FIX: Handle user validation to prevent FOREIGN KEY constraint error
        user_id = booking_data.get('user_id')
        user = None
        
        if user_id:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(id=user_id)
                logger.info(f"[PAYMENT_FLOW_DEBUG] ✓ Valid user found for seat reservation: {user_id}")
            except User.DoesNotExist:
                logger.error(f"[PAYMENT_FLOW_DEBUG] ❌ User {user_id} not found - creating seat reservation without user")
                user = None
        
        reservation, created = SeatReservation.objects.get_or_create(
            correlation_id=correlation_id,
            defaults={
                'flight': flight,
                'user': user,  # Use user object instead of user_id
                'status': 'RESERVED',
                'expires_at': timezone.now() + timedelta(minutes=30)  # 30 min expiry
            }
        )
        
        if created:
            logger.info(f"[SAGA DB] Created seat reservation in database: {correlation_id}")
        else:
            logger.info(f"[SAGA DB] Found existing seat reservation: {correlation_id}")
            
        return reservation
        
    except Exception as e:
        logger.error(f"[SAGA DB] Error creating seat reservation: {e}")
        raise

def cancel_seat_reservation(correlation_id: str) -> bool:
    """
    Database-backed seat cancellation instead of memory deletion
    """
    try:
        reservation = SeatReservation.objects.get(correlation_id=correlation_id)
        reservation.status = 'CANCELLED'
        reservation.save()
        logger.info(f"[SAGA DB] Cancelled seat reservation in database: {correlation_id}")
        return True
    except SeatReservation.DoesNotExist:
        logger.warning(f"[SAGA DB] No seat reservation found to cancel: {correlation_id}")
        return False
    except Exception as e:
        logger.error(f"[SAGA DB] Error cancelling seat reservation: {e}")
        return False

# Initialize orchestrator
def get_orchestrator():
    global saga_orchestrator
    if saga_orchestrator is None:
        try:
            from .saga_orchestrator_fixed import BookingOrchestrator
            saga_orchestrator = BookingOrchestrator()
            logger.info("[SAGA] Orchestrator initialized successfully")
        except ImportError as e:
            logger.error(f"[SAGA] Failed to import orchestrator: {e}")
            # Fallback to alternative orchestrator
            try:
                from .saga_orchestrator import BookingOrchestrator
                saga_orchestrator = BookingOrchestrator()
                logger.warning("[SAGA] Using fallback orchestrator")
            except ImportError as e2:
                logger.error(f"[SAGA] Failed to import any orchestrator: {e2}")
                saga_orchestrator = None
    return saga_orchestrator

@csrf_exempt
@require_http_methods(["POST"])
def start_booking_saga(request):
    """Start the complete SAGA booking process"""
    try:
        data = json.loads(request.body)
        logger.info(f"[SAGA] Starting booking SAGA with data: {data}")
        
        # Validate required fields
        flight_id = data.get('flight_id')
        passengers = data.get('passengers', [])
        contact_info = data.get('contact_info', {})
        
        if not flight_id or not passengers or not contact_info:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: flight_id, passengers, contact_info'
            }, status=400)
        
        # Get flight details
        try:
            flight = Flight.objects.get(id=flight_id)
        except Flight.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Flight {flight_id} not found'
            }, status=404)
        
        # FLIGHT DATA DEBUG: Log flight data preparation for SAGA
        logger.info(f"[FLIGHT_DATA_DEBUG] ===== SAGA BOOKING DATA PREPARATION =====")
        logger.info(f"[FLIGHT_DATA_DEBUG] Flight ID: {flight_id}")
        logger.info(f"[FLIGHT_DATA_DEBUG] Flight details: {flight.flight_number} from {flight.origin} to {flight.destination}")
        logger.info(f"[FLIGHT_DATA_DEBUG] Economy fare: {flight.economy_fare}")
        logger.info(f"[FLIGHT_DATA_DEBUG] Business fare: {flight.business_fare}")
        logger.info(f"[FLIGHT_DATA_DEBUG] First fare: {flight.first_fare}")
        logger.info(f"[FLIGHT_DATA_DEBUG] User ID: {data.get('user_id', 1)}")
        logger.info(f"[FLIGHT_DATA_DEBUG] Passengers count: {len(passengers)}")
        
        # Check for round trip (flight_id_2)
        flight_id_2 = data.get('flight_id_2')
        flight_fare_2 = 0
        
        if flight_id_2:
            try:
                flight_2 = Flight.objects.get(id=flight_id_2)
                flight_fare_2 = float(flight_2.economy_fare)
                logger.info(f"[FLIGHT_DATA_DEBUG] Round trip detected - Flight 2 ID: {flight_id_2}")
                logger.info(f"[FLIGHT_DATA_DEBUG] Flight 2 details: {flight_2.flight_number} from {flight_2.origin} to {flight_2.destination}")
                logger.info(f"[FLIGHT_DATA_DEBUG] Flight 2 Economy fare: {flight_fare_2}")
            except Flight.DoesNotExist:
                logger.warning(f"[FLIGHT_DATA_DEBUG] Flight 2 ID {flight_id_2} not found - treating as single flight")
                flight_id_2 = None
                flight_fare_2 = 0
        
        # Prepare booking data for SAGA - INCLUDE BOTH FLIGHTS FOR ROUND TRIP
        booking_data = {
            'flight_id': flight_id,
            'flight_id_2': flight_id_2,  # Add flight_id_2 for round trip
            'user_id': data.get('user_id', 1),
            'passengers': passengers,
            'contact_info': contact_info,
            'flight_fare': float(flight.economy_fare),
            'flight_fare_2': flight_fare_2,  # Add flight_fare_2 for round trip miles calculation
            'flight': {
                'id': flight.id,
                'flight_number': flight.flight_number,
                'economy_fare': float(flight.economy_fare),
                'origin': str(flight.origin),
                'destination': str(flight.destination)
            },
            # Failure simulation flags (RESTRUCTURED step order)
            # NOTE: Keep existing flag keys for backwards compatibility; orchestrator maps these to new step names.
            'simulate_awardmiles_fail': data.get('simulate_awardmiles_fail', False),            # Step 1: Miles Loyalty
            'simulate_authorizepayment_fail': data.get('simulate_authorizepayment_fail', False),# Step 2: Payment Transaction
            'simulate_confirmbooking_fail': data.get('simulate_confirmbooking_fail', False),    # Step 3: Booking Done
            'simulate_reserveseat_fail': data.get('simulate_reserveseat_fail', False)           # Step 4: Reservation Done
        }
        
        # Get orchestrator and start SAGA
        orchestrator = get_orchestrator()
        if not orchestrator:
            return JsonResponse({
                'success': False,
                'error': 'SAGA orchestrator not available'
            }, status=500)
        
        # Create SAGA transaction record in database
        try:
            flight = Flight.objects.get(id=flight_id)
            
            # CRITICAL FIX: Handle user_id validation to prevent FOREIGN KEY constraint error
            user_id = booking_data.get('user_id')
            user = None
            
            if user_id:
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    user = User.objects.get(id=user_id)
                    logger.info(f"[PAYMENT_FLOW_DEBUG] ✓ Valid user found: {user_id}")
                except User.DoesNotExist:
                    logger.error(f"[PAYMENT_FLOW_DEBUG] ❌ User {user_id} not found - creating SAGA without user")
                    user = None
            else:
                logger.warning(f"[PAYMENT_FLOW_DEBUG] ⚠️ No user_id provided in booking_data")
            
            saga_transaction = SagaTransaction.objects.create(
                correlation_id=str(uuid.uuid4()),
                user=user,  # Use user object instead of user_id
                flight=flight,
                booking_data=booking_data,
                status='STARTED'
            )
            
            logger.info(f"[PAYMENT_FLOW_DEBUG] ✓ SAGA transaction created: {saga_transaction.correlation_id}")
            
            # Update booking data with correlation ID
            booking_data['correlation_id'] = saga_transaction.correlation_id
            
            # Start SAGA process
            result = orchestrator.start_booking_saga(booking_data)
            
            # Update SAGA transaction status based on result
            if result.get('success'):
                saga_transaction.status = 'COMPLETED'
                saga_transaction.steps_completed = result.get('steps_completed', 0)
                saga_transaction.error_message = 'PAYMENT_REQUIRED'
            else:
                saga_transaction.status = 'FAILED'
                saga_transaction.failed_step = result.get('failed_step')
                saga_transaction.error_message = result.get('error')
                saga_transaction.compensation_executed = bool(result.get('compensation_result'))
            
            saga_transaction.save()
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"[SAGA] Error creating SAGA transaction: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Failed to create SAGA transaction: {str(e)}'
            })
        
    except Exception as e:
        logger.error(f"[SAGA] Error starting booking SAGA: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_http_methods(["POST"])
def reserve_seat(request):
    """SAGA Step 1: Reserve seat for booking"""
    try:
        data = json.loads(request.body)
        correlation_id = data.get('correlation_id')
        booking_data = data.get('booking_data', {})
        simulate_failure = data.get('simulate_failure', False)
        
        logger.info(f"[SAGA BACKEND] 💺 ReserveSeat step initiated for correlation_id: {correlation_id}")
        logger.info(f"[SAGA BACKEND] 📊 Processing seat reservation for flight_id: {booking_data.get('flight_id')}")
        
        # Add detailed log entry
        saga_log_storage.add_log(
            correlation_id=correlation_id,
            step_name="ReserveSeat",
            service="SAGA BACKEND",
            log_level="info",
            message=f"💺 ReserveSeat step initiated for correlation_id: {correlation_id}",
            is_compensation=False
        )
        
        # Simulate failure if requested
        if simulate_failure:
            logger.error(f"[SAGA BACKEND] ❌ Simulated failure in ReserveSeat for {correlation_id}")
            logger.error(f"[SAGA BACKEND] 🔄 This is the first step - no compensation needed")
            return JsonResponse({
                "success": False,
                "error": "Simulated seat reservation failure - seat management system unavailable"
            })
        
        # Store reservation in database instead of memory
        try:
            reservation = get_or_create_seat_reservation(correlation_id, booking_data)
            
            logger.info(f"[SAGA BACKEND] ✅ Seat reservation successful for {correlation_id}")
            logger.info(f"[SAGA BACKEND] 💾 Created reservation record: {reservation.id}")
            logger.info(f"[SAGA BACKEND] 🎯 Backend service step 1 complete")
            
            # Add success log entry
            saga_log_storage.add_log(
                correlation_id=correlation_id,
                step_name="ReserveSeat",
                service="SAGA BACKEND",
                log_level="success",
                message=f"✅ Seat reservation successful for {correlation_id}",
                is_compensation=False
            )
            
            return JsonResponse({
                "success": True,
                "correlation_id": correlation_id,
                "reservation_id": reservation.id,
                "message": "Seat reserved successfully in database"
            })
        except Exception as e:
            logger.error(f"[SAGA BACKEND] ❌ Failed to create seat reservation: {e}")
            return JsonResponse({
                "success": False,
                "error": f"Failed to reserve seat: {str(e)}"
            })
        
    except Exception as e:
        logger.error(f"[SAGA] Error in ReserveSeat: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        })

@csrf_exempt
@require_http_methods(["POST"])
def confirm_booking(request):
    """SAGA Step 4: Confirm booking and create proper Ticket record"""
    try:
        data = json.loads(request.body)
        correlation_id = data.get('correlation_id')
        booking_data = data.get('booking_data', {})
        simulate_failure = data.get('simulate_failure', False)
        
        logger.info(f"[SAGA BACKEND] 🎫 ConfirmBooking step initiated for correlation_id: {correlation_id}")
        logger.info(f"[SAGA BACKEND] 📋 Final step - creating ticket and confirming booking")
        
        # Add detailed log entry
        saga_log_storage.add_log(
            correlation_id=correlation_id,
            step_name="ConfirmBooking",
            service="SAGA BACKEND",
            log_level="info",
            message=f"📋 ConfirmBooking step initiated for correlation_id: {correlation_id}",
            is_compensation=False
        )
        
        # Simulate failure if requested
        if simulate_failure:
            logger.error(f"[SAGA BACKEND] ❌ Simulated failure in ConfirmBooking for {correlation_id}")
            logger.error(f"[SAGA BACKEND] 🔄 This will trigger compensation for all previous steps")
            
            # Add failure log entry
            saga_log_storage.add_log(
                correlation_id=correlation_id,
                step_name="ConfirmBooking",
                service="SAGA BACKEND",
                log_level="error",
                message=f"❌ Simulated failure in ConfirmBooking for {correlation_id}",
                is_compensation=False
            )
            
            return JsonResponse({
                "success": False,
                "error": "Simulated booking confirmation failure - booking system unavailable"
            })
        
        # Get flight details
        flight_id = booking_data.get('flight_id')
        try:
            flight = Flight.objects.get(id=flight_id)
        except Flight.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": f"Flight {flight_id} not found"
            })
        
        # Generate unique reference number
        import secrets
        ref_no = secrets.token_hex(3).upper()
        
        # Calculate proper flight dates based on actual flight schedule
        from datetime import datetime, timedelta, time
        booking_date = timezone.now()
        
        # Get actual flight departure date from flight schedule
        # Business Rule: Use flight's actual schedule, not arbitrary dates
        if hasattr(flight, 'depart_day') and flight.depart_day.exists():
            # Find next occurrence of flight's scheduled day
            today_weekday = booking_date.weekday()  # 0=Monday, 6=Sunday
            flight_days = [day.number for day in flight.depart_day.all()]
            
            # Find next available flight day (minimum 2 hours advance booking)
            days_ahead = 1
            for i in range(7):  # Check next 7 days
                check_date = booking_date + timedelta(days=i)
                check_weekday = check_date.weekday()
                
                # Check if flight operates on this day and booking is at least 2 hours in advance
                if check_weekday in flight_days:
                    flight_datetime = timezone.make_aware(datetime.combine(check_date.date(), flight.depart_time))
                    if flight_datetime > booking_date + timedelta(hours=2):
                        days_ahead = i
                        break
            
            flight_ddate = (booking_date + timedelta(days=days_ahead)).date()
        else:
            # Fallback: Next day if no schedule defined
            flight_ddate = (booking_date + timedelta(days=1)).date()
        
        # Calculate arrival date based on flight duration
        if flight.duration:
            departure_datetime = datetime.combine(flight_ddate, flight.depart_time)
            arrival_datetime = departure_datetime + flight.duration
            flight_adate = arrival_datetime.date()
        else:
            # Fallback: Same day arrival
            flight_adate = flight_ddate
        
        # Business Validation: Check advance booking requirements
        min_advance_hours = 2  # Business rule: minimum 2 hours advance booking
        
        # Fix timezone issue: make flight_datetime timezone-aware
        flight_datetime = timezone.make_aware(datetime.combine(flight_ddate, flight.depart_time))
        booking_deadline = booking_date + timedelta(hours=min_advance_hours)
        
        if flight_datetime <= booking_deadline:
            return JsonResponse({
                "success": False,
                "error": f"Booking must be made at least {min_advance_hours} hours in advance"
            })
        
        # Get or create user for proper business tracking
        user_id = booking_data.get('user_id')
        user = None
        if user_id:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning(f"User {user_id} not found, creating ticket without user association")
        
        # Create Passenger records with business validation
        passengers_data = booking_data.get('passengers', [])
        if not passengers_data:
            return JsonResponse({
                "success": False,
                "error": "At least one passenger is required"
            })
        
        passenger_objects = []
        for i, passenger_data in enumerate(passengers_data):
            # Business validation for passenger data
            first_name = passenger_data.get('first_name', '').strip()
            last_name = passenger_data.get('last_name', '').strip()
            
            if not first_name or not last_name:
                return JsonResponse({
                    "success": False,
                    "error": f"Passenger {i+1}: First name and last name are required"
                })
            
            passenger = Passenger.objects.create(
                first_name=first_name,
                last_name=last_name,
                gender=passenger_data.get('gender', 'male')
            )
            passenger_objects.append(passenger)
        
        # Calculate business-appropriate pricing
        contact_info = booking_data.get('contact_info', {})
        seat_class = booking_data.get('seat_class', 'economy')
        
        # Get fare based on seat class (business rule)
        if seat_class == 'business' and flight.business_fare:
            base_fare = flight.business_fare
        elif seat_class == 'first' and flight.first_fare:
            base_fare = flight.first_fare
        else:
            base_fare = flight.economy_fare
            seat_class = 'economy'  # Default to economy if class not available
        
        # Calculate total fare with business charges
        passenger_count = len(passenger_objects)
        flight_fare = base_fare * passenger_count
        
        # Business charges (taxes, fees, etc.)
        tax_rate = 0.08  # 8% tax
        service_fee = 25.0  # Fixed service fee
        other_charges = (flight_fare * tax_rate) + service_fee
        total_fare = flight_fare + other_charges
        
        # Validate contact information (business requirement)
        email = contact_info.get('email', '').strip()
        mobile = contact_info.get('mobile', '').strip()
        
        if not email or '@' not in email:
            return JsonResponse({
                "success": False,
                "error": "Valid email address is required"
            })
        
        if not mobile or len(mobile) < 10:
            return JsonResponse({
                "success": False,
                "error": "Valid mobile number is required"
            })
        
        # Create proper Ticket record with business validation
        ticket = Ticket.objects.create(
            user=user,  # Proper user association
            ref_no=ref_no,
            flight=flight,
            flight_ddate=flight_ddate,
            flight_adate=flight_adate,
            flight_fare=flight_fare,
            other_charges=other_charges,
            total_fare=total_fare,
            seat_class=seat_class,
            booking_date=booking_date,
            mobile=mobile,
            email=email,
            status='CONFIRMED'
        )
        
        # Add passengers to ticket
        ticket.passengers.set(passenger_objects)
        
        # Calculate cancellation policy (business rule)
        cancellation_deadline = flight_datetime - timedelta(hours=24)  # 24 hours before flight
        refund_policy = "Full refund available until 24 hours before departure"
        
        if booking_date > cancellation_deadline:
            refund_policy = "No refund available - within 24 hours of departure"
        
        logger.info(f"[SAGA BACKEND] ✅ Business-compliant booking confirmed: {ref_no} for {passenger_count} passengers")
        logger.info(f"[SAGA BACKEND] 🎫 Created ticket ID: {ticket.id}")
        logger.info(f"[SAGA BACKEND] 💰 Total fare: ${total_fare}")
        logger.info(f"[SAGA BACKEND] 🎯 Backend service final step complete - SAGA transaction successful!")
        
        return JsonResponse({
            "success": True,
            "correlation_id": correlation_id,
            "booking_reference": ref_no,
            "ticket_id": ticket.id,
            "flight_number": flight.flight_number,
            "flight_ddate": flight_ddate.strftime('%Y-%m-%d'),
            "flight_adate": flight_adate.strftime('%Y-%m-%d'),
            "departure_time": flight.depart_time.strftime('%H:%M'),
            "arrival_time": flight.arrival_time.strftime('%H:%M'),
            "seat_class": seat_class,
            "passenger_count": passenger_count,
            "total_fare": total_fare,
            "cancellation_deadline": cancellation_deadline.strftime('%Y-%m-%d %H:%M'),
            "refund_policy": refund_policy,
            "message": "Booking confirmed successfully"
        })
        
    except Exception as e:
        logger.error(f"[SAGA] Error in ConfirmBooking: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        })

@csrf_exempt
@require_http_methods(["POST"])
def cancel_seat(request):
    """SAGA Compensation: Cancel seat reservation"""
    try:
        data = json.loads(request.body)
        correlation_id = data.get('correlation_id')
        
        logger.info(f"[SAGA BACKEND COMPENSATION] 🔄 CancelSeat compensation initiated for correlation_id: {correlation_id}")
        saga_log_storage.add_log(
            correlation_id=correlation_id,
            step_name="CancelSeat",
            service="SAGA BACKEND COMPENSATION",
            log_level="INFO",
            message="CancelSeat compensation initiated",
            is_compensation=True
        )
        
        # Cancel reservation in database instead of memory
        success = cancel_seat_reservation(correlation_id)
        
        if success:
            logger.info(f"[SAGA BACKEND COMPENSATION] ✅ Seat reservation cancelled for {correlation_id}")
            logger.info(f"[SAGA BACKEND COMPENSATION] 🎯 Backend service compensation complete")
            saga_log_storage.add_log(
                correlation_id=correlation_id,
                step_name="CancelSeat",
                service="SAGA BACKEND COMPENSATION",
                log_level="INFO",
                message="Seat reservation cancelled successfully",
                is_compensation=True
            )
            return JsonResponse({
                "success": True,
                "correlation_id": correlation_id,
                "message": "Seat reservation cancelled successfully in database"
            })
        else:
            logger.warning(f"[SAGA BACKEND COMPENSATION] ⚠️ No seat reservation found to cancel for {correlation_id}")
            logger.info(f"[SAGA BACKEND COMPENSATION] ✅ No compensation needed - no seat was reserved")
            saga_log_storage.add_log(
                correlation_id=correlation_id,
                step_name="CancelSeat",
                service="SAGA BACKEND COMPENSATION",
                log_level="INFO",
                message="No seat reservation found to cancel - compensation complete",
                is_compensation=True
            )
            return JsonResponse({
                "success": True,  # Still return success for compensation
                "correlation_id": correlation_id,
                "message": "No seat reservation found to cancel - compensation complete"
            })
        
    except Exception as e:
        logger.error(f"[SAGA] Error in CancelSeat compensation: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        })

@csrf_exempt
@require_http_methods(["POST"])
def cancel_booking(request):
    """SAGA Compensation: Cancel booking"""
    try:
        data = json.loads(request.body)
        correlation_id = data.get('correlation_id')
        compensation_reason = data.get('compensation_reason', 'SAGA compensation')
        
        logger.info(f"[SAGA BACKEND COMPENSATION] 🔄 CancelBooking compensation initiated for correlation_id: {correlation_id}")
        logger.info(f"[SAGA BACKEND COMPENSATION] 📋 Compensation reason: {compensation_reason}")
        
        # Try to find and cancel any tickets created for this SAGA transaction
        try:
            # Look for tickets with this correlation ID in the reference number
            tickets = Ticket.objects.filter(ref_no__icontains=correlation_id[:8])
            
            if tickets.exists():
                logger.info(f"[SAGA BACKEND COMPENSATION] 🎫 Found {tickets.count()} tickets to cancel")
                for ticket in tickets:
                    logger.info(f"[SAGA BACKEND COMPENSATION] 🎫 Cancelling ticket {ticket.ref_no} due to SAGA failure")
                    ticket.status = 'CANCELLED_SAGA'
                    ticket.cancellation_reason = f'SAGA Compensation: {compensation_reason}'
                    ticket.save()
                    
                logger.info(f"[SAGA BACKEND COMPENSATION] ✅ Successfully cancelled {tickets.count()} tickets for {correlation_id}")
                
                return JsonResponse({
                    "success": True,
                    "correlation_id": correlation_id,
                    "tickets_cancelled": tickets.count(),
                    "message": f"Successfully cancelled {tickets.count()} tickets due to SAGA compensation"
                })
            else:
                logger.info(f"[SAGA COMPENSATION] ℹ️ No tickets found to cancel for {correlation_id}")
                return JsonResponse({
                    "success": True,
                    "correlation_id": correlation_id,
                    "tickets_cancelled": 0,
                    "message": "No tickets found to cancel"
                })
                
        except Exception as e:
            logger.error(f"[SAGA COMPENSATION] ❌ Error finding/cancelling tickets: {e}")
            # Still return success for compensation, but log the error
            return JsonResponse({
                "success": True,
                "correlation_id": correlation_id,
                "message": f"Booking cancellation logged (error accessing tickets: {str(e)})"
            })
        
    except Exception as e:
        logger.error(f"[SAGA COMPENSATION] ❌ Error in CancelBooking compensation: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        })

@csrf_exempt
@require_http_methods(["GET"])
def get_saga_logs(request, correlation_id):
    """Get SAGA execution logs for display"""
    try:
        # DIAGNOSTIC: Add comprehensive logging for API debugging
        logger.info(f"[SAGA API DIAGNOSTIC] ===== GET_SAGA_LOGS API CALLED =====")
        logger.info(f"[SAGA API DIAGNOSTIC] Requested correlation_id: {correlation_id}")
        logger.info(f"[SAGA API DIAGNOSTIC] Request method: {request.method}")
        logger.info(f"[SAGA API DIAGNOSTIC] Request path: {request.path}")
        
        # Get logs from centralized storage
        logs = saga_log_storage.get_logs(correlation_id)
        
        logger.info(f"[SAGA API DIAGNOSTIC] Retrieved {len(logs)} logs from storage")
        logger.info(f"[SAGA API DIAGNOSTIC] Returning success response with {len(logs)} logs")
        
        return JsonResponse({
            "success": True,
            "correlation_id": correlation_id,
            "logs": logs,
            "total_logs": len(logs)
        })
        
    except Exception as e:
        logger.error(f"[SAGA API DIAGNOSTIC] ❌ ERROR in get_saga_logs: {e}")
        logger.error(f"[SAGA API DIAGNOSTIC] Exception type: {type(e)}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        })

@csrf_exempt
@require_http_methods(["POST"])
def demo_saga_failure(request):
    """Demo endpoint to trigger SAGA with simulated failure"""
    try:
        # Create demo booking data with multiple failure simulation options
        demo_booking_data = {
            'flight_id': 37972,  # Updated to use a valid flight ID
            'user_id': 1,
            'passengers': [{'first_name': 'Demo', 'last_name': 'User', 'gender': 'male'}],
            'contact_info': {'email': 'demo@example.com', 'mobile': '1234567890'},
            'seat_class': 'economy',
            # Failure simulation flags (RESTRUCTURED step order)
            'simulate_awardmiles_fail': False,  # Step 1: Miles Loyalty
            'simulate_authorizepayment_fail': False,  # Step 2: Payment Transaction
            'simulate_confirmbooking_fail': True,  # Step 3: Booking Done (tests payment+miles compensation)
            'simulate_reserveseat_fail': False,  # Step 4: Reservation Done
        }
        
        # Get orchestrator and start SAGA
        orchestrator = get_orchestrator()
        if not orchestrator:
            return JsonResponse({
                'success': False,
                'error': 'SAGA orchestrator not available'
            }, status=500)
        
        # Start SAGA with simulated failure
        result = orchestrator.start_booking_saga(demo_booking_data)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"[SAGA] Error in demo failure: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        })

@csrf_exempt
@require_http_methods(["POST"])
def create_demo_log(request):
    """Create demo log entry for correlation IDs that don't have real logs"""
    try:
        data = json.loads(request.body)
        correlation_id = data.get('correlation_id')
        step_name = data.get('step_name', 'DemoStep')
        service = data.get('service', 'Demo Service')
        log_level = data.get('log_level', 'info')
        message = data.get('message', 'Demo log entry')
        is_compensation = data.get('is_compensation', False)
        
        logger.info(f"[SAGA DEMO LOG] Creating demo log for correlation_id: {correlation_id}")
        
        # Add log using the storage system
        saga_log_storage.add_log(
            correlation_id=correlation_id,
            step_name=step_name,
            service=service,
            log_level=log_level,
            message=message,
            is_compensation=is_compensation
        )
        
        logger.info(f"[SAGA DEMO LOG] Demo log created successfully for {correlation_id}")
        
        return JsonResponse({
            "success": True,
            "correlation_id": correlation_id,
            "message": "Demo log created successfully"
        })
        
    except Exception as e:
        logger.error(f"[SAGA DEMO LOG] Error creating demo log: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        })

@csrf_exempt
@require_http_methods(["GET"])
def get_saga_status(request, correlation_id):
    """Get SAGA transaction status"""
    try:
        saga_transaction = SagaTransaction.objects.get(correlation_id=correlation_id)
        
        return JsonResponse({
            "success": True,
            "correlation_id": correlation_id,
            "status": saga_transaction.status,
            "steps_completed": saga_transaction.steps_completed,
            "failed_step": saga_transaction.failed_step,
            "error_message": saga_transaction.error_message,
            "created_at": saga_transaction.created_at.isoformat(),
            "updated_at": saga_transaction.updated_at.isoformat()
        })
        
    except SagaTransaction.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": f"SAGA transaction {correlation_id} not found"
        }, status=404)
    except Exception as e:
        logger.error(f"[SAGA] Error getting SAGA status: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        })

@csrf_exempt
@require_http_methods(["POST"])
def start_booking_saga_async(request):
    """Start the SAGA booking process asynchronously - returns 202 immediately and runs SAGA in background"""
    try:
        data = json.loads(request.body)
        logger.info(f"[SAGA ASYNC] Starting async booking SAGA with data: {data}")
        
        # Validate required fields
        flight_id = data.get('flight_id')
        passengers = data.get('passengers', [])
        contact_info = data.get('contact_info', {})
        
        if not flight_id or not passengers or not contact_info:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: flight_id, passengers, contact_info'
            }, status=400)
        
        # Get flight details for validation
        try:
            flight = Flight.objects.get(id=flight_id)
        except Flight.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Flight {flight_id} not found'
            }, status=404)
        
        # Generate ONE correlation_id and use it for BOTH:
        # - the 202 Accepted response (what UI polls)
        # - the actual orchestrator run (what writes step logs)
        correlation_id = str(uuid.uuid4())
        logger.info(f"[SAGA ASYNC] Generated correlation_id (UI + Orchestrator): {correlation_id}")

        # Initial log entry so UI sees logs right away
        try:
            saga_log_storage.add_log(
                correlation_id=correlation_id,
                step_name="SAGA_START",
                service="SAGA BACKEND",
                log_level="info",
                message=f"Async SAGA accepted for correlation_id: {correlation_id}",
                is_compensation=False
            )
            logger.info(f"[SAGA ASYNC] Initial log entry created for {correlation_id}")
        except Exception as e:
            logger.warning(f"[SAGA ASYNC] Failed to write initial log: {e}")
        
        # Return 202 Accepted immediately with correlation_id
        logger.info(f"[SAGA ASYNC] Returning 202 Accepted immediately for correlation_id: {correlation_id}")
        
        # Start background SAGA (simplified for immediate response)
        def run_saga_background():
            try:
                orchestrator = get_orchestrator()
                if orchestrator:
                    booking_data = {
                        'flight_id': flight_id,
                        'user_id': data.get('user_id', 1),
                        'passengers': passengers,
                        'contact_info': contact_info,
                        'flight_fare': float(flight.economy_fare),
                        'correlation_id': correlation_id,
                        'simulate_reserveseat_fail': data.get('simulate_reserveseat_fail', False),
                        'simulate_authorizepayment_fail': data.get('simulate_authorizepayment_fail', False),
                        'simulate_awardmiles_fail': data.get('simulate_awardmiles_fail', False),
                        'simulate_confirmbooking_fail': data.get('simulate_confirmbooking_fail', False)
                    }
                    logger.info(f"[SAGA ASYNC DEBUG] simulate_reserveseat_fail flag: {booking_data.get('simulate_reserveseat_fail')}")
                    result = orchestrator.start_booking_saga(booking_data)
                    logger.info(f"[SAGA ASYNC] Background SAGA completed: {result.get('success')}")
            except Exception as e:
                logger.error(f"[SAGA ASYNC] Background SAGA error: {e}")
        
        # Start background thread
        thread = threading.Thread(target=run_saga_background)
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'accepted': True,
            'correlation_id': correlation_id,
            'message': 'SAGA booking started in background'
        }, status=202)
        
    except Exception as e:
        logger.error(f"[SAGA ASYNC] Error starting async booking SAGA: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)