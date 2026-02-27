
"""
API views for flight booking system
"""
import json
import secrets
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Flight, Ticket, Passenger, User


@csrf_exempt
@require_http_methods(["POST"])
def create_failed_booking(request):
    """API endpoint to create failed booking records from SAGA microservice"""
    try:
        data = json.loads(request.body)
        
        correlation_id = data.get('correlation_id')
        flight_id = data.get('flight_id')
        user_id = data.get('user_id')
        passengers_data = data.get('passengers', [])
        contact_info = data.get('contact_info', {})
        seat_class = data.get('seat_class', 'economy')
        failed_step = data.get('failed_step')
        failure_reason = data.get('failure_reason')
        compensation_executed = data.get('compensation_executed', False)
        compensation_details = data.get('compensation_details')
        
        print(f"[API] Creating failed booking for correlation_id: {correlation_id}")
        
        # Get flight
        try:
            flight = Flight.objects.get(id=flight_id)
        except Flight.DoesNotExist:
            return JsonResponse({'error': f'Flight {flight_id} not found'}, status=404)
        
        # Get user
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                print(f"[API] User {user_id} not found")
        
        # Generate reference number
        ref_no = f"F{secrets.token_hex(2).upper()}{correlation_id[:3].upper()}"
        
        # Calculate fare
        passenger_count = len(passengers_data)
        if seat_class == 'business' and flight.business_fare:
            base_fare = flight.business_fare
        elif seat_class == 'first' and flight.first_fare:
            base_fare = flight.first_fare
        else:
            base_fare = flight.economy_fare
            seat_class = 'economy'
        
        flight_fare = base_fare * passenger_count if base_fare else 0
        other_charges = flight_fare * 0.08 + 25.0
        total_fare = flight_fare + other_charges
        
        # Create failed ticket
        failed_ticket = Ticket.objects.create(
            user=user,
            ref_no=ref_no,
            flight=flight,
            flight_ddate=None,
            flight_adate=None,
            flight_fare=flight_fare,
            other_charges=other_charges,
            total_fare=total_fare,
            seat_class=seat_class,
            booking_date=timezone.now(),
            mobile=contact_info.get('mobile', ''),
            email=contact_info.get('email', ''),
            status='FAILED',
            saga_correlation_id=correlation_id,
            failed_step=failed_step,
            failure_reason=failure_reason,
            compensation_executed=compensation_executed,
            compensation_details=compensation_details
        )
        
        # Create passengers
        for passenger_data in passengers_data:
            passenger = Passenger.objects.create(
                first_name=passenger_data.get('first_name', ''),
                last_name=passenger_data.get('last_name', ''),
                gender=passenger_data.get('gender', 'male')
            )
            failed_ticket.passengers.add(passenger)
        
        print(f"[API] Successfully created failed booking: {ref_no}")
        
        return JsonResponse({
            'success': True,
            'ref_no': ref_no,
            'ticket_id': failed_ticket.id,
            'correlation_id': correlation_id,
            'message': 'Failed booking record created successfully'
        })
        
    except Exception as e:
        print(f"[API] Error creating failed booking: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)