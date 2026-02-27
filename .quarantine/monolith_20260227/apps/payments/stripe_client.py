
import stripe
import os
import logging
from decimal import Decimal
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')


class StripeClient:
    """Stripe payment processing client"""
    
    @staticmethod
    def create_payment_intent(
        amount: Decimal,
        currency: str = 'usd',
        metadata: Optional[Dict[str, Any]] = None,
        customer_email: Optional[str] = None,
        description: Optional[str] = None,
        automatic_payment_methods: bool = True
    ) -> Dict[str, Any]:
        """Create a Stripe PaymentIntent"""
        
        try:
            # Convert amount to cents (Stripe expects integer cents)
            amount_cents = int(amount * 100)
            
            intent_data = {
                'amount': amount_cents,
                'currency': currency,
                'metadata': metadata or {},
            }
            
            if description:
                intent_data['description'] = description
            
            if customer_email:
                intent_data['receipt_email'] = customer_email
            
            if automatic_payment_methods:
                intent_data['automatic_payment_methods'] = {'enabled': True}
            
            payment_intent = stripe.PaymentIntent.create(**intent_data)
            
            logger.info(f"Created PaymentIntent {payment_intent.id} for ${amount}")
            
            return {
                'id': payment_intent.id,
                'client_secret': payment_intent.client_secret,
                'amount': amount,
                'currency': currency,
                'status': payment_intent.status,
                'metadata': payment_intent.metadata
            }
            
        except Exception as e:
            logger.error(f"Stripe error creating PaymentIntent: {e}")
            raise Exception(f"Payment processing error: {str(e)}")
    
    @staticmethod
    def create_checkout_session(
        line_items: list,
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        mode: str = 'payment'
    ) -> Dict[str, Any]:
        """Create a Stripe Checkout Session"""
        
        try:
            session_data = {
                'line_items': line_items,
                'mode': mode,
                'success_url': success_url,
                'cancel_url': cancel_url,
                'metadata': metadata or {},
            }
            
            if customer_email:
                session_data['customer_email'] = customer_email
            
            session = stripe.checkout.Session.create(**session_data)
            
            logger.info(f"Created Checkout Session {session.id}")
            
            return {
                'id': session.id,
                'url': session.url,
                'payment_status': session.payment_status,
                'metadata': session.metadata
            }
            
        except Exception as e:
            logger.error(f"Stripe error creating Checkout Session: {e}")
            raise Exception(f"Checkout creation error: {str(e)}")
    
    @staticmethod
    def retrieve_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
        """Retrieve a PaymentIntent by ID"""
        
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                'id': payment_intent.id,
                'amount': Decimal(payment_intent.amount) / 100,  # Convert from cents
                'currency': payment_intent.currency,
                'status': payment_intent.status,
                'metadata': payment_intent.metadata,
                'charges': getattr(payment_intent, 'charges', {}).get('data', [])
            }
            
        except Exception as e:
            logger.error(f"Stripe error retrieving PaymentIntent: {e}")
            raise Exception(f"Payment retrieval error: {str(e)}")
    
    @staticmethod
    def confirm_payment_intent(payment_intent_id: str, payment_method: Optional[str] = None) -> Dict[str, Any]:
        """Confirm a PaymentIntent"""
        
        try:
            confirm_data = {}
            if payment_method:
                confirm_data['payment_method'] = payment_method
            
            payment_intent = stripe.PaymentIntent.confirm(payment_intent_id, **confirm_data)
            
            logger.info(f"Confirmed PaymentIntent {payment_intent.id}")
            
            return {
                'id': payment_intent.id,
                'status': payment_intent.status,
                'amount': Decimal(payment_intent.amount) / 100,
                'currency': payment_intent.currency
            }
            
        except Exception as e:
            logger.error(f"Stripe error confirming PaymentIntent: {e}")
            raise Exception(f"Payment confirmation error: {str(e)}")
    
    @staticmethod
    def cancel_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
        """Cancel a PaymentIntent"""
        
        try:
            payment_intent = stripe.PaymentIntent.cancel(payment_intent_id)
            
            logger.info(f"Cancelled PaymentIntent {payment_intent.id}")
            
            return {
                'id': payment_intent.id,
                'status': payment_intent.status,
                'cancellation_reason': payment_intent.cancellation_reason
            }
            
        except Exception as e:
            logger.error(f"Stripe error cancelling PaymentIntent: {e}")
            raise Exception(f"Payment cancellation error: {str(e)}")
    
    @staticmethod
    def construct_webhook_event(payload: bytes, sig_header: str) -> Any:
        """Construct and verify webhook event"""
        
        endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        if not endpoint_secret:
            raise Exception("Stripe webhook secret not configured")
        
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
            logger.info(f"Received webhook event: {event['type']}")
            return event
            
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise Exception("Invalid payload")
        except Exception as e:
            logger.error(f"Invalid signature: {e}")
            raise Exception("Invalid signature")