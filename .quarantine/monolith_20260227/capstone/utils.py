"""
Utility functions for the capstone project
"""

from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
import secrets
from flight.models import Ticket
from django.utils import timezone


def render_to_pdf(template_src, context_dict={}):
    """Render a template to PDF"""
    try:
        template = get_template(template_src)
        html = template.render(context_dict)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
        if result.getvalue():
            return HttpResponse(result.getvalue(), content_type='application/pdf')
        return HttpResponse("Error generating PDF", content_type='text/plain')
    except Exception as e:
        return HttpResponse(f"PDF generation error: {str(e)}", content_type='text/plain')


def createticket(user, passengers, passenger_count, flight, flight_date, flight_class, coupon, country_code, email, mobile):
    """Create a ticket for the flight booking"""
    
    # Generate unique reference number
    ref_no = secrets.token_hex(3).upper()
    while Ticket.objects.filter(ref_no=ref_no).exists():
        ref_no = secrets.token_hex(3).upper()
    
    # Calculate fare based on class
    if flight_class.lower() == 'economy':
        base_fare = flight.economy_fare or 0
    elif flight_class.lower() == 'business':
        base_fare = flight.business_fare or 0
    elif flight_class.lower() == 'first':
        base_fare = flight.first_fare or 0
    else:
        base_fare = flight.economy_fare or 0
    
    # Calculate total fare
    flight_fare = base_fare * int(passenger_count)
    other_charges = 50.0  # Default fee
    coupon_discount = 0.0
    
    # Apply coupon discount if provided
    if coupon:
        coupon_discounts = {
            'SAVE10': 0.10,
            'SAVE20': 0.20,
            'FIRSTFLIGHT': 0.15,
            'STUDENT': 0.25
        }
        if coupon.upper() in coupon_discounts:
            coupon_discount = flight_fare * coupon_discounts[coupon.upper()]
    
    total_fare = flight_fare + other_charges - coupon_discount
    
    # Parse flight date
    from datetime import datetime
    if isinstance(flight_date, str):
        # Assuming format is DD-MM-YYYY
        day, month, year = flight_date.split('-')
        flight_ddate = datetime(int(year), int(month), int(day)).date()
    else:
        flight_ddate = flight_date
    
    # Calculate arrival date (same day for now)
    flight_adate = flight_ddate
    
    # Create ticket
    ticket = Ticket.objects.create(
        user=user,
        ref_no=ref_no,
        flight=flight,
        flight_ddate=flight_ddate,
        flight_adate=flight_adate,
        flight_fare=flight_fare,
        other_charges=other_charges,
        coupon_used=coupon or '',
        coupon_discount=coupon_discount,
        total_fare=total_fare,
        seat_class=flight_class.lower(),
        booking_date=timezone.now(),
        mobile=f"{country_code}{mobile}",
        email=email,
        status='PENDING'
    )
    
    # Add passengers to ticket
    for passenger in passengers:
        ticket.passengers.add(passenger)
    
    return ticket