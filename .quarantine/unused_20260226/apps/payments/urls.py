from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment processing endpoints
    path('process/', views.process_payment, name='process_payment'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('status/<str:payment_id>/', views.payment_status, name='payment_status'),
    path('refund/', views.process_refund, name='process_refund'),
    
    # Banking validation endpoints
    path('banking/validate/', views.validate_card, name='validate_card'),
]