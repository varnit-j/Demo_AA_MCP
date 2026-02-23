from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from datetime import datetime
import json
import uuid

from .models import Place, Flight, Week

# Simple in-memory storage for demo purposes
# In production, this would be a database
stored_tickets = {}


@require_http_methods(["GET"])
def flight_search(request):
    """Simple flight search API without DRF"""
    try:
        # Get parameters
        origin_code = request.GET.get('origin', '').upper()
        destination_code = request.GET.get('destination', '').upper()
        depart_date_str = request.GET.get('depart_date', '')
        seat_class = request.GET.get('seat_class', 'economy')
        trip_type = request.GET.get('trip_type', '1')  # '1' for one-way, '2' for round-trip
        return_date_str = request.GET.get('return_date', '')  # For round-trip
        
        print(f"[DEBUG] Flight search params: origin={origin_code}, dest={destination_code}, date={depart_date_str}, class={seat_class}, trip_type={trip_type}")
        
        # Basic validation
        if not origin_code or not destination_code or not depart_date_str:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        # Validate return date for round trip
        if trip_type == '2' and not return_date_str:
            return JsonResponse({'error': 'Return date is required for round trip'}, status=400)
        
        # Parse dates
        depart_date = datetime.strptime(depart_date_str, '%Y-%m-%d').date()
        return_date = None
        if trip_type == '2':
            return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
        
        # Get places
        try:
            origin = Place.objects.get(code=origin_code)
            destination = Place.objects.get(code=destination_code)
        except Place.DoesNotExist:
            return JsonResponse({'error': 'Invalid origin or destination'}, status=400)
        
        # Get flight day
        try:
            flight_day = Week.objects.get(number=depart_date.weekday())
        except Week.DoesNotExist:
            return JsonResponse({'error': 'Invalid date'}, status=400)
        
        # Search outbound flights - limit to American Airlines only
        flights = Flight.objects.filter(
            origin=origin,
            destination=destination,
            depart_day=flight_day,
            airline__icontains='American Airlines'
        )
        
        # Filter by seat class
        if seat_class == 'economy':
            flights = flights.exclude(economy_fare=0).order_by('economy_fare')
        elif seat_class == 'business':
            flights = flights.exclude(business_fare=0).order_by('business_fare')
        elif seat_class == 'first':
            flights = flights.exclude(first_fare=0).order_by('first_fare')
        
        # Convert to JSON
        flights_data = []
        for flight in flights:
            flights_data.append({
                'id': flight.id,
                'plane': flight.plane,
                'airline': flight.airline,
                'flight_number': flight.flight_number,  # Added flight number
                'origin': {
                    'code': flight.origin.code,
                    'city': flight.origin.city,
                    'airport': flight.origin.airport
                },
                'destination': {
                    'code': flight.destination.code,
                    'city': flight.destination.city,
                    'airport': flight.destination.airport
                },
                'depart_time': str(flight.depart_time),
                'arrival_time': str(flight.arrival_time),
                'economy_fare': float(flight.economy_fare),
                'business_fare': float(flight.business_fare),
                'first_fare': float(flight.first_fare),
                'duration': str(flight.duration)
            })
        
        # Search return flights for round trip
        flights2_data = []
        origin2_data = None
        destination2_data = None
        if trip_type == '2' and return_date:
            print(f"[DEBUG] Processing return flights for trip_type={trip_type}, return_date={return_date}")
            try:
                return_flight_day = Week.objects.get(number=return_date.weekday())
                
                # Search return flights (swapped origin and destination)
                flights2 = Flight.objects.filter(
                    origin=destination,  # Return flight starts from destination
                    destination=origin,   # Return flight ends at origin
                    depart_day=return_flight_day,
                    airline__icontains='American Airlines'
                )
                
                # Filter by seat class
                if seat_class == 'economy':
                    flights2 = flights2.exclude(economy_fare=0).order_by('economy_fare')
                elif seat_class == 'business':
                    flights2 = flights2.exclude(business_fare=0).order_by('business_fare')
                elif seat_class == 'first':
                    flights2 = flights2.exclude(first_fare=0).order_by('first_fare')
                
                print(f"[DEBUG] Found {flights2.count()} return flights")
                
                # Convert return flights to JSON
                for flight in flights2:
                    flights2_data.append({
                        'id': flight.id,
                        'plane': flight.plane,
                        'airline': flight.airline,
                        'flight_number': flight.flight_number,
                        'origin': {
                            'code': flight.origin.code,
                            'city': flight.origin.city,
                            'airport': flight.origin.airport
                        },
                        'destination': {
                            'code': flight.destination.code,
                            'city': flight.destination.city,
                            'airport': flight.destination.airport
                        },
                        'depart_time': str(flight.depart_time),
                        'arrival_time': str(flight.arrival_time),
                        'economy_fare': float(flight.economy_fare),
                        'business_fare': float(flight.business_fare),
                        'first_fare': float(flight.first_fare),
                        'duration': str(flight.duration)
                    })
                
                # Prepare origin2 and destination2 (swapped for return leg)
                origin2_data = {
                    'code': destination.code,
                    'city': destination.city,
                    'airport': destination.airport
                }
                destination2_data = {
                    'code': origin.code,
                    'city': origin.city,
                    'airport': origin.airport
                }
            except Week.DoesNotExist:
                print(f"[DEBUG] Invalid return date: {return_date}")
        
        # Build response
        response_data = {
            'flights': flights_data,
            'origin': {
                'code': origin.code,
                'city': origin.city,
                'airport': origin.airport
            },
            'destination': {
                'code': destination.code,
                'city': destination.city,
                'airport': destination.airport
            },
            'depart_date': str(depart_date),
            'seat_class': seat_class,
            'trip_type': trip_type
        }
        
        # Add return flight data for round trip
        if trip_type == '2':
            response_data.update({
                'flights2': flights2_data,
                'origin2': origin2_data,
                'destination2': destination2_data,
                'return_date': str(return_date)
            })
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"[ERROR] Flight search exception: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def book_flight(request):
    """Book a flight - simplified booking endpoint"""
    try:
        # Parse JSON data
        data = json.loads(request.body)
        print(f"[DEBUG] Booking request data: {data}")
        
        # Extract required fields
        flight_id = data.get('flight_id')
        passengers = data.get('passengers', [])
        contact_info = data.get('contact_info', {})
        
        # Validate required fields
        if not flight_id:
            return JsonResponse({'error': 'Flight ID is required'}, status=400)
        
        if not passengers:
            return JsonResponse({'error': 'At least one passenger is required'}, status=400)
        
        # Validate contact info
        if not contact_info.get('email') or not contact_info.get('mobile'):
            return JsonResponse({'error': 'Contact email and mobile are required'}, status=400)
        
        # Get flight details
        try:
            flight = Flight.objects.get(id=flight_id)
        except Flight.DoesNotExist:
            return JsonResponse({'error': 'Flight not found'}, status=404)
        
        # Validate passengers
        for i, passenger in enumerate(passengers):
            if not passenger.get('first_name') or not passenger.get('last_name'):
                return JsonResponse({'error': f'Passenger {i+1}: First name and last name are required'}, status=400)
            if not passenger.get('gender'):
                return JsonResponse({'error': f'Passenger {i+1}: Gender is required'}, status=400)
        
        # Generate booking reference
        booking_reference = f"BK{uuid.uuid4().hex[:8].upper()}"
        
        # Prepare flight data for response
        flight_data = {
            'id': flight.id,
            'plane': flight.plane,
            'airline': flight.airline,
            'flight_number': flight.flight_number,  # Added flight number
            'origin': {
                'code': flight.origin.code,
                'city': flight.origin.city,
                'airport': flight.origin.airport
            },
            'destination': {
                'code': flight.destination.code,
                'city': flight.destination.city,
                'airport': flight.destination.airport
            },
            'depart_time': str(flight.depart_time),
            'arrival_time': str(flight.arrival_time),
            'economy_fare': float(flight.economy_fare),
            'business_fare': float(flight.business_fare),
            'first_fare': float(flight.first_fare),
            'duration': str(flight.duration)
        }
        
        print(f"[DEBUG] Booking successful - Reference: {booking_reference}")
        
        # Store the ticket for later retrieval
        user_id = str(data.get('user_id', '1'))  # Get user_id from request data
        print(f"[DEBUG] Using user_id: {user_id} for ticket storage")
        
        if user_id not in stored_tickets:
            stored_tickets[user_id] = []
        
        # Create ticket record
        ticket_record = {
            'booking_reference': booking_reference,
            'flight': flight_data,
            'passengers': passengers,
            'contact_info': contact_info,
            'booking_date': '2026-01-15',  # Simplified for demo
            'status': 'pending'  # Initial status is pending until payment is processed
        }
        
        stored_tickets[user_id].append(ticket_record)
        print(f"[DEBUG] Stored ticket for user {user_id}: {booking_reference}")
        
        # Return success response
        return JsonResponse({
            'success': True,
            'booking_reference': booking_reference,
            'flight': flight_data,
            'passengers': passengers,
            'contact_info': contact_info,
            'message': 'Flight booked successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"[ERROR] Booking exception: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_user_tickets(request, user_id):
    """Get tickets for a specific user"""
    try:
        # Get stored tickets for the user
        user_tickets = stored_tickets.get(str(user_id), [])
        print(f"[DEBUG] BOOKING DISPLAY ISSUE - Getting tickets for user {user_id}: found {len(user_tickets)} tickets")
        print(f"[DEBUG] BOOKING DISPLAY ISSUE - stored_tickets contents: {stored_tickets}")
        print(f"[DEBUG] BOOKING DISPLAY ISSUE - This endpoint only reads from stored_tickets dictionary")
        print(f"[DEBUG] BOOKING DISPLAY ISSUE - SAGA bookings are NOT stored here, they use database tables")
        return JsonResponse(user_tickets, safe=False)
        
    except Exception as e:
        print(f"[ERROR] Get user tickets exception: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_user_tickets_with_saga(request, user_id):
    """Get tickets for a specific user including SAGA bookings from database"""
    try:
        from .models import Ticket, SagaTransaction
        
        # Get stored tickets for the user (simple bookings)
        user_tickets = stored_tickets.get(str(user_id), [])
        print(f"[DEBUG] SAGA FIX - Simple bookings for user {user_id}: {len(user_tickets)} tickets")
        
        # Get SAGA bookings from database
        try:
            # CRITICAL FIX: Handle both user objects and user IDs properly
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Try to get tickets by user object first, then by user_id if user exists
            saga_tickets = []
            try:
                user_obj = User.objects.get(id=user_id)
                saga_tickets = Ticket.objects.filter(user=user_obj)
                print(f"[DEBUG] BOOKING DISPLAY FIX - Found user object {user_id}, querying tickets by user")
            except User.DoesNotExist:
                print(f"[DEBUG] BOOKING DISPLAY FIX - User {user_id} not found, checking tickets without user")
                # Also check for tickets that might have been created without user association
                saga_tickets = Ticket.objects.filter(user__isnull=True)
            
            print(f"[DEBUG] BOOKING DISPLAY FIX - Database tickets for user {user_id}: {len(saga_tickets)} tickets")
            
            # Convert database tickets to the same format as simple tickets
            for ticket in saga_tickets:
                ticket_data = {
                    'booking_reference': ticket.ref_no,
                    'flight': {
                        'id': ticket.flight.id,
                        'plane': ticket.flight.plane,
                        'airline': ticket.flight.airline,
                        'flight_number': ticket.flight.flight_number,
                        'origin': {
                            'code': ticket.flight.origin.code,
                            'city': ticket.flight.origin.city,
                            'airport': ticket.flight.origin.airport
                        },
                        'destination': {
                            'code': ticket.flight.destination.code,
                            'city': ticket.flight.destination.city,
                            'airport': ticket.flight.destination.airport
                        },
                        'depart_time': str(ticket.flight.depart_time),
                        'arrival_time': str(ticket.flight.arrival_time),
                        'economy_fare': float(ticket.flight.economy_fare),
                        'business_fare': float(ticket.flight.business_fare),
                        'first_fare': float(ticket.flight.first_fare),
                    },
                    'passengers': [
                        {
                            'first_name': p.first_name,
                            'last_name': p.last_name,
                            'gender': p.gender
                        } for p in ticket.passengers.all()
                    ],
                    'contact_info': {
                        'email': ticket.email,
                        'mobile': ticket.mobile
                    },
                    'booking_date': ticket.booking_date.strftime('%Y-%m-%d'),
                    'status': ticket.status.lower()
                }
                user_tickets.append(ticket_data)
                
        except Exception as db_error:
            print(f"[DEBUG] SAGA FIX - Database query error: {db_error}")
        
        print(f"[DEBUG] SAGA FIX - Total tickets for user {user_id}: {len(user_tickets)} tickets")
        return JsonResponse(user_tickets, safe=False)
        
    except Exception as e:
        print(f"[ERROR] Get user tickets with SAGA exception: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def places_search(request):
    """Search places by query string"""
    try:
        query = request.GET.get('q', '').strip()
        print(f"[DEBUG] Places search query: '{query}'")
        
        if not query:
            # Return empty list if no query
            return JsonResponse([], safe=False)
        
        # Search places by city, airport, code, or country
        places = Place.objects.filter(
            Q(city__icontains=query) |
            Q(airport__icontains=query) |
            Q(code__icontains=query) |
            Q(country__icontains=query)
        )[:10]  # Limit to 10 results
        
        # Convert to JSON
        places_data = []
        for place in places:
            places_data.append({
                'id': place.id,
                'city': place.city,
                'airport': place.airport,
                'code': place.code,
                'country': place.country,
                'display_name': f"{place.city}, {place.country} ({place.code})"
            })
        
        print(f"[DEBUG] Found {len(places_data)} places for query '{query}'")
        return JsonResponse(places_data, safe=False)
        
    except Exception as e:
        print(f"[ERROR] Places search exception: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({'status': 'healthy', 'service': 'backend-service'})


@require_http_methods(["GET"])
def get_flight_detail(request, flight_id):
    """Get detailed information about a specific flight"""
    try:
        flight = Flight.objects.get(id=flight_id)
        
        flight_data = {
            'id': flight.id,
            'plane': flight.plane,
            'airline': flight.airline,
            'flight_number': flight.flight_number,  # Added flight number
            'origin': {
                'code': flight.origin.code,
                'city': flight.origin.city,
                'airport': flight.origin.airport
            },
            'destination': {
                'code': flight.destination.code,
                'city': flight.destination.city,
                'airport': flight.destination.airport
            },
            'depart_time': str(flight.depart_time),
            'arrival_time': str(flight.arrival_time) if flight.arrival_time else '00:00:00',
            'economy_fare': float(flight.economy_fare) if flight.economy_fare else 0.0,
            'business_fare': float(flight.business_fare) if flight.business_fare else 0.0,
            'first_fare': float(flight.first_fare) if flight.first_fare else 0.0,
            'duration': str(flight.duration)
        }
        
        return JsonResponse(flight_data)
        
    except Flight.DoesNotExist:
        return JsonResponse({'error': 'Flight not found'}, status=404)
    except Exception as e:
        print(f"[ERROR] Flight detail exception: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_ticket_status(request, booking_ref):
    """Update ticket status by booking reference"""
    try:
        # Parse JSON data
        data = json.loads(request.body)
        new_status = data.get('status')
        
        print(f"[DEBUG] Updating ticket {booking_ref} status to: {new_status}")
        
        if not new_status:
            return JsonResponse({'error': 'Status is required'}, status=400)
        
        # Valid status values
        valid_statuses = ['pending', 'confirmed', 'on_hold', 'cancelled']
        if new_status not in valid_statuses:
            return JsonResponse({'error': f'Invalid status. Must be one of: {valid_statuses}'}, status=400)
        
        # Find and update the ticket in stored_tickets
        ticket_found = False
        for user_id, tickets in stored_tickets.items():
            for ticket in tickets:
                if ticket['booking_reference'] == booking_ref:
                    ticket['status'] = new_status
                    ticket_found = True
                    print(f"[DEBUG] Updated ticket {booking_ref} status to {new_status} for user {user_id}")
                    break
            if ticket_found:
                break
        
        if not ticket_found:
            return JsonResponse({'error': 'Ticket not found'}, status=404)
        
        return JsonResponse({
            'success': True,
            'booking_reference': booking_ref,
            'status': new_status,
            'message': f'Ticket status updated to {new_status}'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"[ERROR] Update ticket status exception: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)