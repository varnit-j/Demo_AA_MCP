from django.urls import path
from . import views  # type: ignore
from . import api_views

# Import hybrid checkout views directly
try:
    from flight.views.hybrid_checkout import (
        hybrid_checkout_page,
        calculate_hybrid_pricing,
        process_hybrid_redemption,
        confirm_hybrid_payment
    )
    HYBRID_CHECKOUT_AVAILABLE = True
except ImportError:
    HYBRID_CHECKOUT_AVAILABLE = False

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register_view, name="register"),
    path("query/places/<str:q>", views.query, name="query"),
    path("flight", views.flight, name="flight"),
    path("review", views.review, name="review"),
    path("flight/ticket/book", views.book, name="book"),
    path("flight/ticket/payment", views.payment, name="payment"),
    path('flight/ticket/api/<str:ref>', views.ticket_data, name="ticketdata"),
    path('flight/ticket/print',views.get_ticket, name="getticket"),
    path('flight/bookings', views.bookings, name="bookings"),
    path('flight/ticket/cancel', views.cancel_ticket, name="cancelticket"),
    path('flight/ticket/resume', views.resume_booking, name="resumebooking"),
    path('contact', views.contact, name="contact"),
    path('privacy-policy', views.privacy_policy, name="privacypolicy"),
    path('terms-and-conditions', views.terms_and_conditions, name="termsandconditions"),
    path('about-us', views.about_us, name="aboutus"),
    path('saga/test', views.saga_test, name="saga_test"),
    path('api/create-failed-booking/', api_views.create_failed_booking, name="create_failed_booking"),
]

# Add hybrid checkout URLs if available
if HYBRID_CHECKOUT_AVAILABLE:
    urlpatterns += [
        path('hybrid-checkout/<int:ticket_id>/', hybrid_checkout_page, name="hybrid_checkout"),
        path('api/calculate-hybrid-pricing/', calculate_hybrid_pricing, name="calculate_hybrid_pricing"),
        path('api/process-hybrid-redemption/', process_hybrid_redemption, name="process_hybrid_redemption"),
        path('api/confirm-hybrid-payment/', confirm_hybrid_payment, name="confirm_hybrid_payment"),
    ]