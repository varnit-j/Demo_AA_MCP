from django.urls import path
from . import views, webhooks

app_name = 'payments'

urlpatterns = [
    path('create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('webhook/', webhooks.stripe_webhook, name='stripe_webhook'),
]