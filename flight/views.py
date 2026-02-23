from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
import json
from decimal import Decimal

from datetime import datetime
import math
from .models import *
from capstone.utils import render_to_pdf, createticket

# Import loyalty and order services
try:
    from apps.loyalty.service import LoyaltyService
    from apps.orders.service import OrderService
except ImportError:
    # Fallback if apps are not available
    LoyaltyService = None
    OrderService = None


# Fee and Surcharge variable
try:
    from .constant import FEE
except ImportError:
    FEE = 50.0  # Default fee if constant file is missing

try:
    from flight.utils import createWeekDays, addPlaces, addDomesticFlights, addInternationalFlights
except ImportError:
    # Create dummy functions if utils are missing
    def createWeekDays():
        pass
    def addPlaces():
        pass
    def addDomesticFlights():
        pass
    def addInternationalFlights():
        pass

try:
    if len(Week.objects.all()) == 0:
        createWeekDays()

    if len(Place.objects.all()) == 0:
        addPlaces()

    if len(Flight.objects.all()) == 0:
        print("Do you want to add flights in the Database? (y/n)")
        if input().lower() in ['y', 'yes']:
            addDomesticFlights()
            addInternationalFlights()
except:
    pass

# Create your views here.

def index(request):
    min_date = f"{datetime.now().date().year}-{datetime.now().date().month}-{datetime.now().date().day}"
    max_date = f"{datetime.now().date().year if (datetime.now().date().month+3)<=12 else datetime.now().date().year+1}-{(datetime.now().date().month + 3) if (datetime.now().date().month+3)<=12 else (datetime.now().date().month+3-12)}-{datetime.now().date().day}"
    if request.method == 'POST':
        origin = request.POST.get('Origin')
        destination = request.POST.get('Destination')
        depart_date = request.POST.get('DepartDate')
        seat = request.POST.get('SeatClass')
        trip_type = request.POST.get('TripType')
        if(trip_type == '1'):
            return render(request, 'flight/index.html', {
            'origin': origin,
            'destination': destination,
            'depart_date': depart_date,
            'seat': seat.lower(),
            'trip_type': trip_type
        })
        elif(trip_type == '2'):
            return_date = request.POST.get('ReturnDate')
            return render(request, 'flight/index.html', {
            'min_date': min_date,
            'max_date': max_date,
            'origin': origin,
            'destination': destination,
            'depart_date': depart_date,
            'seat': seat.lower(),
            'trip_type': trip_type,
            'return_date': return_date
        })
    else:
        return render(request, 'flight/index.html', {
            'min_date': min_date,
            'max_date': max_date
        })

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
            
        else:
            return render(request, "flight/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, "flight/login.html")

def register_view(request):
    if request.method == "POST":
        fname = request.POST['firstname']
        lname = request.POST['lastname']
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensuring password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "flight/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.first_name = fname
            user.last_name = lname
            user.save()
        except:
            return render(request, "flight/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "flight/register.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def query(request, q):
    places = Place.objects.all()
    filters = []
    q = q.lower()
    for place in places:
        if (q in place.city.lower()) or (q in place.airport.lower()) or (q in place.code.lower()) or (q in place.country.lower()):
            filters.append(place)
    return JsonResponse([{'code':place.code, 'city':place.city, 'country': place.country} for place in filters], safe=False)

@csrf_exempt
def flight(request):
    o_place = request.GET.get('Origin')
    d_place = request.GET.get('Destination')
    trip_type = request.GET.get('TripType')
    departdate = request.GET.get('DepartDate')
    depart_date = datetime.strptime(departdate, "%Y-%m-%d")
    return_date = None
    
    print(f"[FLIGHT SEARCH] Origin: {o_place}, Destination: {d_place}, TripType: {trip_type}, DepartDate: {departdate}")
    
    # Initialize variables
    flights2 = []
    origin2 = None
    destination2 = None
    flightday2 = None
    max_price2 = 0
    min_price2 = 0
    
    # Get common flight details
    seat = request.GET.get('SeatClass')
    flightday = Week.objects.get(number=depart_date.weekday())
    destination = Place.objects.get(code=d_place.upper())
    origin = Place.objects.get(code=o_place.upper())
    
    print(f"[OUTBOUND] FlightDay: {flightday}, Origin: {origin}, Destination: {destination}, Seat: {seat}")
    
    # Handle round trip - set return flight details
    if trip_type == '2':
        returndate = request.GET.get('ReturnDate')
        return_date = datetime.strptime(returndate, "%Y-%m-%d")
        flightday2 = Week.objects.get(number=return_date.weekday())
        origin2 = Place.objects.get(code=d_place.upper())  # Return: from destination to origin
        destination2 = Place.objects.get(code=o_place.upper())
        print(f"[ROUND TRIP] Return Date: {returndate}, FlightDay2: {flightday2}, Origin2: {origin2}, Destination2: {destination2}")
    
    if seat == 'economy':
        flights = Flight.objects.filter(depart_day=flightday,origin=origin,destination=destination,airline__icontains='American Airlines').exclude(economy_fare=0).order_by('economy_fare')
        print(f"[OUTBOUND ECONOMY] Found {flights.count()} flights")
        try:
            last_flight = flights.last()
            first_flight = flights.first()
            max_price = last_flight.economy_fare if last_flight else 0
            min_price = first_flight.economy_fare if first_flight else 0
        except:
            max_price = 0
            min_price = 0

        if trip_type == '2':
            flights2 = Flight.objects.filter(depart_day=flightday2,origin=origin2,destination=destination2,airline__icontains='American Airlines').exclude(economy_fare=0).order_by('economy_fare')
            print(f"[RETURN ECONOMY] Found {flights2.count()} flights")
            try:
                last_flight2 = flights2.last()
                first_flight2 = flights2.first()
                max_price2 = last_flight2.economy_fare if last_flight2 else 0
                min_price2 = first_flight2.economy_fare if first_flight2 else 0
            except:
                max_price2 = 0
                min_price2 = 0
                
    elif seat == 'business':
        flights = Flight.objects.filter(depart_day=flightday,origin=origin,destination=destination,airline__icontains='American Airlines').exclude(business_fare=0).order_by('business_fare')
        print(f"[OUTBOUND BUSINESS] Found {flights.count()} flights")
        try:
            last_flight = flights.last()
            first_flight = flights.first()
            max_price = last_flight.business_fare if last_flight else 0
            min_price = first_flight.business_fare if first_flight else 0
        except:
            max_price = 0
            min_price = 0

        if trip_type == '2':
            flights2 = Flight.objects.filter(depart_day=flightday2,origin=origin2,destination=destination2,airline__icontains='American Airlines').exclude(business_fare=0).order_by('business_fare')
            print(f"[RETURN BUSINESS] Found {flights2.count()} flights")
            try:
                last_flight2 = flights2.last()
                first_flight2 = flights2.first()
                max_price2 = last_flight2.business_fare if last_flight2 else 0
                min_price2 = first_flight2.business_fare if first_flight2 else 0
            except:
                max_price2 = 0
                min_price2 = 0

    elif seat == 'first':
        flights = Flight.objects.filter(depart_day=flightday,origin=origin,destination=destination,airline__icontains='American Airlines').exclude(first_fare=0).order_by('first_fare')
        print(f"[OUTBOUND FIRST] Found {flights.count()} flights")
        try:
            last_flight = flights.last()
            first_flight = flights.first()
            max_price = last_flight.first_fare if last_flight else 0
            min_price = first_flight.first_fare if first_flight else 0
        except:
            max_price = 0
            min_price = 0
            
        if trip_type == '2':
            flights2 = Flight.objects.filter(depart_day=flightday2,origin=origin2,destination=destination2,airline__icontains='American Airlines').exclude(first_fare=0).order_by('first_fare')
            print(f"[RETURN FIRST] Found {flights2.count()} flights")
            try:
                last_flight2 = flights2.last()
                first_flight2 = flights2.first()
                max_price2 = last_flight2.first_fare if last_flight2 else 0
                min_price2 = first_flight2.first_fare if first_flight2 else 0
            except:
                max_price2 = 0
                min_price2 = 0

    context = {
        'flights': flights,
        'origin': origin,
        'destination': destination,
        'seat': seat.capitalize(),
        'trip_type': trip_type,
        'depart_date': depart_date,
        'return_date': return_date,
        'max_price': math.ceil((max_price or 0)/100)*100 if (max_price or 0) > 0 else 0,
        'min_price': math.floor((min_price or 0)/100)*100 if (min_price or 0) > 0 else 0,
    }
    
    if trip_type == '2':
        print(f"[ROUND TRIP] Adding flights2 to context. flights2 type: {type(flights2)}, count: {flights2.count() if hasattr(flights2, 'count') else len(flights2)}")
        context.update({
            'flights2': flights2,
            'origin2': origin2,
            'destination2': destination2,
            'max_price2': math.ceil((max_price2 or 0)/100)*100 if (max_price2 or 0) > 0 else 0,
            'min_price2': math.floor((min_price2 or 0)/100)*100 if (min_price2 or 0) > 0 else 0
        })
        print(f"[CONTEXT AFTER UPDATE] 'flights2' in context: {'flights2' in context}")
    else:
        print(f"[NOT ROUND TRIP] Trip type: {trip_type}, flights2 will NOT be added")
    
    print(f"[CONTEXT] Trip Type: {trip_type}, Flights: {flights.count()}, Flights2: {context.get('flights2').count() if 'flights2' in context else 'NOT IN CONTEXT'}")
    print(f"[CONTEXT KEYS] {list(context.keys())}")
    
    return render(request, "flight/search.html", context)

def review(request):
    flight_1 = request.GET.get('flight1Id')
    date1 = request.GET.get('flight1Date')
    seat = request.GET.get('seatClass')
    round_trip = False
    if request.GET.get('flight2Id'):
        round_trip = True

    if round_trip:
        flight_2 = request.GET.get('flight2Id')
        date2 = request.GET.get('flight2Date')

    if request.user.is_authenticated:
        flight1 = Flight.objects.get(id=flight_1)
        flight1ddate = datetime(int(date1.split('-')[2]),int(date1.split('-')[1]),int(date1.split('-')[0]),flight1.depart_time.hour,flight1.depart_time.minute)
        flight1adate = (flight1ddate + flight1.duration) if flight1.duration else flight1ddate
        flight2 = None
        flight2ddate = None
        flight2adate = None
        if round_trip:
            flight2 = Flight.objects.get(id=flight_2)
            flight2ddate = datetime(int(date2.split('-')[2]),int(date2.split('-')[1]),int(date2.split('-')[0]),flight2.depart_time.hour,flight2.depart_time.minute)
            flight2adate = (flight2ddate + flight2.duration) if flight2.duration else flight2ddate
        #print("//////////////////////////////////")
        #print(f"flight1ddate: {flight1adate-flight1ddate}")
        #print("//////////////////////////////////")
        if round_trip:
            return render(request, "flight/book.html", {
                'flight1': flight1,
                'flight2': flight2,
                "flight1ddate": flight1ddate,
                "flight1adate": flight1adate,
                "flight2ddate": flight2ddate,
                "flight2adate": flight2adate,
                "seat": seat,
                "fee": FEE
            })
        return render(request, "flight/book.html", {
            'flight1': flight1,
            "flight1ddate": flight1ddate,
            "flight1adate": flight1adate,
            "seat": seat,
            "fee": FEE
        })
    else:
        return HttpResponseRedirect(reverse("login"))

def book(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            flight_1 = request.POST.get('flight1')
            flight_1date = request.POST.get('flight1Date')
            flight_1class = request.POST.get('flight1Class')
            f2 = False
            if request.POST.get('flight2'):
                flight_2 = request.POST.get('flight2')
                flight_2date = request.POST.get('flight2Date')
                flight_2class = request.POST.get('flight2Class')
                f2 = True
            countrycode = request.POST['countryCode']
            mobile = request.POST['mobile']
            email = request.POST['email']
            
            # Server-side validation
            import re
            
            # Validate mobile number (exactly 10 digits)
            if not re.match(r'^[0-9]{10}$', mobile):
                return HttpResponse("Invalid mobile number. Please enter exactly 10 digits.", status=400)
            
            # Validate email format
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                return HttpResponse("Invalid email format. Please enter a valid email address.", status=400)
            flight1 = Flight.objects.get(id=flight_1)
            if f2:
                flight2 = Flight.objects.get(id=flight_2)
            passengerscount = request.POST['passengersCount']
            passengers=[]
            for i in range(1,int(passengerscount)+1):
                fname = request.POST[f'passenger{i}FName']
                lname = request.POST[f'passenger{i}LName']
                gender = request.POST[f'passenger{i}Gender']
                
                # Validate passenger names (2-50 characters, letters only)
                if not re.match(r'^[A-Za-z\s]{2,50}$', fname):
                    return HttpResponse(f"Invalid first name for passenger {i}. Please enter 2-50 characters, letters only.", status=400)
                if not re.match(r'^[A-Za-z\s]{2,50}$', lname):
                    return HttpResponse(f"Invalid last name for passenger {i}. Please enter 2-50 characters, letters only.", status=400)
                
                passengers.append(Passenger.objects.create(first_name=fname,last_name=lname,gender=gender.lower()))
            coupon = request.POST.get('coupon')
            
            try:
                ticket1 = createticket(request.user,passengers,passengerscount,flight1,flight_1date,flight_1class,coupon,countrycode,email,mobile)
                if f2:
                    ticket2 = createticket(request.user,passengers,passengerscount,flight2,flight_2date,flight_2class,coupon,countrycode,email,mobile)

                if(flight_1class == 'Economy'):
                    if f2:
                        fare = ((flight1.economy_fare or 0)*int(passengerscount))+((flight2.economy_fare or 0)*int(passengerscount))
                    else:
                        fare = (flight1.economy_fare or 0)*int(passengerscount)
                elif (flight_1class == 'Business'):
                    if f2:
                        fare = ((flight1.business_fare or 0)*int(passengerscount))+((flight2.business_fare or 0)*int(passengerscount))
                    else:
                        fare = (flight1.business_fare or 0)*int(passengerscount)
                elif (flight_1class == 'First'):
                    if f2:
                        fare = ((flight1.first_fare or 0)*int(passengerscount))+((flight2.first_fare or 0)*int(passengerscount))
                    else:
                        fare = (flight1.first_fare or 0)*int(passengerscount)
            except Exception as e:
                return HttpResponse(e)
            

            # Get user's loyalty points for payment page
            user_points = 0
            points_value = 0
            if LoyaltyService:
                try:
                    account = LoyaltyService.get_or_create_account(request.user)
                    user_points = account.current_points_balance
                    points_value = user_points * 0.01  # 1 point = $0.01
                except Exception as e:
                    print(f"DEBUG: Error getting loyalty data: {e}")

            if f2:    ##
                return render(request, "flight/payment.html", { ##
                    'fare': fare+FEE,   ##
                    'ticket': ticket1.pk,
                    'ticket2': ticket2.pk,
                    'user_points': user_points,
                    'points_value': points_value
                })  ##
            return render(request, "flight/payment.html", {
                'fare': fare+FEE,
                'ticket': ticket1.pk,
                'user_points': user_points,
                'points_value': points_value
            })
        else:
            return HttpResponseRedirect(reverse("login"))
    else:
        return HttpResponse("Method must be post.")

def payment(request):
    # Safe print function that handles Unicode encoding errors
    def safe_print(message):
        try:
            print(message)
        except UnicodeEncodeError:
            # If Unicode error, print ASCII-safe version
            safe_message = message.encode('ascii', errors='replace').decode('ascii')
            print(f"[UNICODE_SAFE] {safe_message}")
    
    safe_print(f"DEBUG: Payment view accessed - Method: {request.method}, User authenticated: {request.user.is_authenticated}")
    safe_print(f"DEBUG: Request path: {request.path}")
    safe_print(f"DEBUG: Request GET params: {request.GET}")
    
    # DEBUG: Check for Unicode encoding issues in POST data
    if request.method == 'POST':
        try:
            safe_print(f"DEBUG: Raw POST body encoding: {request.encoding}")
            safe_print(f"DEBUG: POST data keys: {list(request.POST.keys())}")
            for key, value in request.POST.items():
                try:
                    # Test if each field can be encoded to ASCII
                    key.encode('ascii')
                    str(value).encode('ascii')
                    safe_print(f"DEBUG: Field '{key}' = '{value}' - ASCII OK")
                except UnicodeEncodeError as e:
                    safe_print(f"DEBUG: UNICODE ERROR in field '{key}' = '{repr(value)}': {e}")
                    # Clean the value by removing non-ASCII characters
                    cleaned_value = ''.join(char for char in str(value) if ord(char) < 128)
                    safe_print(f"DEBUG: Cleaned value: '{cleaned_value}'")
        except Exception as e:
            safe_print(f"DEBUG: Error analyzing POST data: {e}")
    
    if request.user.is_authenticated:
        if request.method == 'POST':
            safe_print("DEBUG: Processing POST request for authenticated user")
            try:
                ticket_id = request.POST['ticket']
                t2 = False
                if request.POST.get('ticket2'):
                    ticket2_id = request.POST['ticket2']
                    t2 = True
                fare = request.POST.get('fare')
                payment_method = request.POST.get('payment_method', 'card')
                
                # Handle card payment - only validate if payment method is card
                if payment_method == 'card':
                    card_number = request.POST['cardNumber']
                    card_holder_name = request.POST['cardHolderName']
                    exp_month = request.POST['expMonth']
                    exp_year = request.POST['expYear']
                    cvv = request.POST['cvv']
                    
                    # Server-side validation for payment details
                    import re
                    
                    # Validate card number (exactly 16 digits)
                    if not re.match(r'^[0-9]{16}$', card_number):
                        return HttpResponse("Invalid card number. Please enter exactly 16 digits.", status=400)
                    
                    # Validate card holder name (2-50 characters, letters only)
                    if not re.match(r'^[A-Za-z\s]{2,50}$', card_holder_name):
                        return HttpResponse("Invalid card holder name. Please enter 2-50 characters, letters only.", status=400)
                    
                    # Validate CVV (exactly 3 digits)
                    if not re.match(r'^[0-9]{3}$', cvv):
                        return HttpResponse("Invalid CVV. Please enter exactly 3 digits.", status=400)
                else:
                    # For counter payment, set dummy values to avoid errors
                    card_number = ''
                    card_holder_name = ''
                    exp_month = ''
                    exp_year = ''
                    cvv = ''
                
                # BANKING INTEGRATION - Process payment through mock banking system (only for card payments)
                if payment_method == 'card':
                    try:
                        from apps.banking.service import MockBankingService
                        
                        # Get ticket to determine payment amount
                        ticket = Ticket.objects.get(id=ticket_id)
                        payment_amount = float(ticket.total_fare) if ticket.total_fare else 0
                        
                        # Process payment through mock banking system
                        payment_success, payment_message, transaction_id, bank_transaction = MockBankingService.process_payment(
                            card_number=card_number,
                            card_holder_name=card_holder_name,
                            expiry_month=exp_month,
                            expiry_year=exp_year,
                            cvv=cvv,
                            amount=payment_amount,
                            reference_id=ticket.ref_no
                        )
                        
                        safe_print(f"DEBUG: Banking payment result - Success: {payment_success}, Message: {payment_message}, Transaction ID: {transaction_id}")
                        
                        if not payment_success:
                            # Payment failed - return error to user
                            return HttpResponse(f"Payment failed: {payment_message}", status=400)
                        
                        safe_print(f"DEBUG: Payment approved by banking system - Transaction ID: {transaction_id}")
                        
                    except ImportError:
                        safe_print("DEBUG: Banking service not available - proceeding with basic validation")
                    except Exception as banking_error:
                        safe_print(f"DEBUG: Banking service error: {banking_error}")
                        return HttpResponse(f"Payment processing error: {banking_error}", status=500)
                else:
                    safe_print("DEBUG: Counter payment selected - skipping banking service")
                
                # Handle points redemption - fix empty string issue
                points_to_use_raw = request.POST.get('points_to_use', '0')
                points_to_use = int(points_to_use_raw) if points_to_use_raw and points_to_use_raw.strip() else 0
                safe_print(f"DEBUG: Payment form data extracted successfully - Ticket ID: {ticket_id}, Points to use: {points_to_use}")
                
                # Handle counter payment
                if payment_method == 'counter':
                    safe_print(f"DEBUG: Processing counter payment for ticket {ticket_id}")
                    return handle_counter_payment(request, ticket_id, t2, ticket2_id if t2 else None, points_to_use)
            except UnicodeDecodeError as e:
                safe_print(f"DEBUG: Unicode decode error in payment form data: {e}")
                return HttpResponse("Payment form contains invalid characters", status=400)
            except KeyError as e:
                safe_print(f"DEBUG: Missing required form field: {e}")
                return HttpResponse(f"Missing required field: {e}", status=400)
            except Exception as e:
                safe_print(f"DEBUG: Unexpected error extracting form data: {e}")
                return HttpResponse(f"Form data error: {e}", status=400)

            try:
                ticket = Ticket.objects.get(id=ticket_id)
                
                # For round trips, get total fare from both tickets for points calculation
                total_booking_fare = float(ticket.total_fare) if ticket.total_fare else 0
                if t2:
                    ticket2 = Ticket.objects.get(id=ticket2_id)
                    total_booking_fare += float(ticket2.total_fare) if ticket2.total_fare else 0
                
                # LOYALTY INTEGRATION - Handle points redemption BEFORE confirming ticket
                if LoyaltyService and points_to_use > 0:
                    try:
                        safe_print(f"DEBUG: Processing points redemption: {points_to_use} points for user {request.user.username}")
                        
                        # Redeem points from user's account
                        LoyaltyService.redeem_points(
                            user=request.user,
                            points_amount=points_to_use,
                            reference_id=ticket.ref_no,
                            description=f"Points redemption for flight booking - {ticket.ref_no}"
                        )
                        safe_print(f"DEBUG: Successfully redeemed {points_to_use} points from {request.user.username}")
                        
                    except Exception as redemption_error:
                        safe_print(f"DEBUG: Points redemption error: {redemption_error}")
                        # If redemption fails, we should probably return an error
                        return HttpResponse(f"Points redemption failed: {redemption_error}", status=400)
                
                # Confirm the ticket after successful points redemption
                ticket.status = 'CONFIRMED'
                ticket.booking_date = timezone.now()
                ticket.save()
                
                # DEBUG: Log payment completion for loyalty diagnosis
                safe_print(f"DEBUG: Payment completed for user {request.user.username}, ticket {ticket.ref_no}, fare ${ticket.total_fare}")
                safe_print(f"DEBUG: LoyaltyService available: {LoyaltyService is not None}")
                
                # LOYALTY INTEGRATION - Award points based on TOTAL PAYMENT (both flights + fee)
                if LoyaltyService:
                    try:
                        # Calculate TOTAL points from complete payment (not per ticket)
                        # This ensures points are awarded once for the entire booking transaction
                        
                        if t2:
                            # Round trip: both tickets
                            ticket2 = Ticket.objects.get(id=ticket2_id)
                            total_payment = float(ticket.total_fare) + float(ticket2.total_fare)
                        else:
                            # One way: single ticket
                            total_payment = float(ticket.total_fare)
                        
                        # Convert to USD for points calculation (2% of amount spent = points)
                        usd_total_payment = total_payment / 82.5  # Convert INR to USD
                        total_points_to_award = int(usd_total_payment * 2)  # 2% of USD payment as points
                        
                        safe_print(f"DEBUG: LOYALTY - Total Payment: ₹{total_payment:.2f} (${usd_total_payment:.2f})")
                        safe_print(f"DEBUG: LOYALTY - Awarding {total_points_to_award} points (2% of ${usd_total_payment:.2f})")
                        
                        # Award ALL points in a SINGLE transaction for the entire booking
                        booking_reference = f"{ticket.ref_no}"
                        if t2:
                            booking_reference += f" + {ticket2.ref_no}"
                        
                        LoyaltyService.earn_points(
                            user=request.user,
                            points_amount=total_points_to_award,
                            reference_id=booking_reference,
                            description=f"Flight booking - {booking_reference} (2% of ${usd_total_payment:.2f}) [TOTAL_PAYMENT]"
                        )
                        safe_print(f"DEBUG: LOYALTY - Successfully awarded {total_points_to_award} points to {request.user.username} for booking: {booking_reference}")
                        
                    except Exception as loyalty_error:
                        safe_print(f"DEBUG: LOYALTY ERROR: {loyalty_error}")
                else:
                    safe_print("DEBUG: LoyaltyService not available - no points awarded")
                
                if t2:
                    ticket2 = Ticket.objects.get(id=ticket2_id)
                    ticket2.status = 'CONFIRMED'
                    ticket2.save()
                    return render(request, 'flight/payment_process.html', {
                        'ticket1': ticket,
                        'ticket2': ticket2
                    })
                return render(request, 'flight/payment_process.html', {
                    'ticket1': ticket,
                    'ticket2': ""
                })
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be post.")
    else:
        return HttpResponseRedirect(reverse('login'))


def ticket_data(request, ref):
    ticket = Ticket.objects.get(ref_no=ref)
    return JsonResponse({
        'ref': ticket.ref_no,
        'from': ticket.flight.origin.code if ticket.flight and ticket.flight.origin else '',
        'to': ticket.flight.destination.code if ticket.flight and ticket.flight.destination else '',
        'flight_date': ticket.flight_ddate,
        'status': ticket.status
    })

@csrf_exempt
def get_ticket(request):
    ref = request.GET.get("ref")
    ticket1 = Ticket.objects.get(ref_no=ref)
    data = {
        'ticket1':ticket1,
        'current_year': datetime.now().year
    }
    pdf = render_to_pdf('flight/ticket.html', data)
    return HttpResponse(pdf, content_type='application/pdf')


def bookings(request):
    if request.user.is_authenticated:
        tickets = Ticket.objects.filter(user=request.user).order_by('-booking_date')
        
        # DEBUG LOGGING: Check what tickets are being displayed
        print(f"[BOOKINGS DEBUG] 🔍 User {request.user.username} (ID: {request.user.id}) requesting bookings")
        print(f"[BOOKINGS DEBUG] 📊 Total tickets found: {tickets.count()}")
        
        for ticket in tickets:
            print(f"[BOOKINGS DEBUG] 🎫 Ticket {ticket.ref_no}: Status={ticket.status}, User={ticket.user_id}, SAGA_ID={ticket.saga_correlation_id}")
            if ticket.status == 'FAILED':
                print(f"[BOOKINGS DEBUG] ❌ FAILED ticket details: Step={ticket.failed_step}, Reason={ticket.failure_reason}, Compensation={ticket.compensation_executed}")
        
        # Also check for any failed tickets that might not be associated with user
        all_failed_tickets = Ticket.objects.filter(status='FAILED').order_by('-booking_date')
        print(f"[BOOKINGS DEBUG] 🚨 Total FAILED tickets in system: {all_failed_tickets.count()}")
        
        for failed_ticket in all_failed_tickets:
            print(f"[BOOKINGS DEBUG] 🚨 System FAILED ticket {failed_ticket.ref_no}: User={failed_ticket.user_id}, SAGA_ID={failed_ticket.saga_correlation_id}")
        
        return render(request, 'flight/bookings.html', {
            'page': 'bookings',
            'tickets': tickets
        })
    else:
        return HttpResponseRedirect(reverse('login'))

@csrf_exempt
def cancel_ticket(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            ref = request.POST['ref']
            
            # Import and use the new cancellation service
            from .cancellation_service import process_ticket_cancellation
            
            # Process the cancellation with refund and loyalty points reversal
            result = process_ticket_cancellation(request.user, ref)
            
            return JsonResponse(result)
        else:
            return HttpResponse("User unauthorised")
    else:
        return HttpResponse("Method must be POST.")

def resume_booking(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            ref = request.POST['ref']
            ticket = Ticket.objects.get(ref_no=ref)
            if ticket.user == request.user:
                return render(request, "flight/payment.html", {
                    'fare': ticket.total_fare,
                    'ticket': ticket.pk
                })
            else:
                return HttpResponse("User unauthorised")
        else:
            return HttpResponseRedirect(reverse("login"))
    else:
        return HttpResponse("Method must be post.")

def contact(request):
    return render(request, 'flight/contact.html')

def privacy_policy(request):
    return render(request, 'flight/privacy-policy.html')

def terms_and_conditions(request):
    return render(request, 'flight/terms.html')

def about_us(request):
    return render(request, 'flight/about.html')


def saga_test(request):
    """View for testing SAGA orchestrator with different failure scenarios"""
    from .saga_orchestrator_enhanced import EnhancedBookingSAGAOrchestrator
    from datetime import datetime
    
    result = None
    
    if request.method == 'POST':
        test_type = request.POST.get('test_type', 'success')
        
        # Prepare failure scenarios
        failure_scenarios = {
            'reserve_seat': request.POST.get('fail_reserve_seat') == 'true',
            'deduct_loyalty_points': request.POST.get('fail_deduct_points') == 'true',
            'process_payment': request.POST.get('fail_payment') == 'true',
            'confirm_booking': request.POST.get('fail_confirm') == 'true'
        }
        
        # For success scenario, clear all failures
        if test_type == 'success':
            failure_scenarios = {}
        
        # Prepare booking data
        booking_data = {
            'flight_id': 123,
            'user_id': 1,
            'total_fare': 500.00,
            'loyalty_points_to_use': 1000,
            'payment_method': 'card',
            'passengers': [
                {
                    'first_name': 'John',
                    'last_name': 'Test',
                    'gender': 'male'
                }
            ]
        }
        
        # Execute enhanced SAGA
        orchestrator = EnhancedBookingSAGAOrchestrator()
        result = orchestrator.start_booking_saga(booking_data, failure_scenarios=failure_scenarios)
        
        # If failure, redirect to failure page
        if not result.get('success'):
            return render(request, 'flight/saga_failure_result.html', {
                'result': result,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
    
    return render(request, 'flight/saga_test.html', {'result': result})


def handle_counter_payment(request, ticket_id, t2, ticket2_id, points_to_use):
    """Handle counter payment - redeem points and put ticket on hold"""
    # Safe print function that handles Unicode encoding errors
    def safe_print(message):
        try:
            print(message)
        except UnicodeEncodeError:
            safe_message = message.encode('ascii', errors='replace').decode('ascii')
            print(f"[UNICODE_SAFE] {safe_message}")
    
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        
        # LOYALTY INTEGRATION - Handle points redemption BEFORE putting ticket on hold
        if LoyaltyService and points_to_use > 0:
            try:
                safe_print(f"DEBUG: Processing points redemption for counter payment: {points_to_use} points for user {request.user.username}")
                
                # Redeem points from user's account
                LoyaltyService.redeem_points(
                    user=request.user,
                    points_amount=points_to_use,
                    reference_id=ticket.ref_no,
                    description=f"Points redemption for flight booking (Counter Payment) - {ticket.ref_no}"
                )
                safe_print(f"DEBUG: Successfully redeemed {points_to_use} points from {request.user.username}")
                
            except Exception as redemption_error:
                safe_print(f"DEBUG: Points redemption error: {redemption_error}")
                return HttpResponse(f"Points redemption failed: {redemption_error}", status=400)
        
        # Set ticket status to ON_HOLD for counter payment
        ticket.status = 'ON_HOLD'
        ticket.booking_date = timezone.now()
        ticket.save()
        
        safe_print(f"DEBUG: Ticket {ticket.ref_no} placed on hold for counter payment")
        
        # Handle second ticket if round trip
        if t2 and ticket2_id:
            ticket2 = Ticket.objects.get(id=ticket2_id)
            ticket2.status = 'ON_HOLD'
            ticket2.save()
            safe_print(f"DEBUG: Ticket {ticket2.ref_no} also placed on hold for counter payment")
            
            return render(request, 'flight/counter_payment_confirmation.html', {
                'ticket1': ticket,
                'ticket2': ticket2,
                'points_redeemed': points_to_use,
                'remaining_amount': float(ticket.total_fare) - (points_to_use * 0.01) if ticket.total_fare else 0
            })
        
        # Calculate remaining amount after points redemption
        remaining_amount = float(ticket.total_fare) - (points_to_use * 0.01) if ticket.total_fare else 0
        
        return render(request, 'flight/counter_payment_confirmation.html', {
            'ticket1': ticket,
            'ticket2': None,
            'points_redeemed': points_to_use,
            'remaining_amount': remaining_amount
        })
        
    except Exception as e:
        safe_print(f"DEBUG: Counter payment error: {e}")
        return HttpResponse(f"Counter payment processing error: {e}", status=500)
