
from django.utils import timezone
from decimal import Decimal
import random
from datetime import datetime
from .models import BankCard, PaymentTransaction


class MockBankingService:
    """Mock banking service to simulate real payment processing"""
    
    @staticmethod
    def validate_card(card_number, card_holder_name, expiry_month, expiry_year, cvv):
        """
        Validate card details against mock bank database
        Returns: (is_valid, error_message, card_object)
        """
        try:
            # Remove spaces and dashes from card number
            clean_card_number = card_number.replace(' ', '').replace('-', '')
            
            # Find card in mock database
            try:
                card = BankCard.objects.get(card_number=clean_card_number)
            except BankCard.DoesNotExist:
                # Provide helpful error message with available test cards
                available_cards = BankCard.objects.filter(status='active')[:3]
                if available_cards:
                    card_examples = ", ".join([f"{c.card_number}" for c in available_cards])
                    return False, f"Card not found in mock database. Try these test cards: {card_examples}", None
                else:
                    return False, "Invalid card number - no test cards available", None
            
            # Check card status
            if card.status != 'active':
                if card.status == 'blocked':
                    return False, "Card is blocked", None
                elif card.status == 'expired':
                    return False, "Card has expired", None
                elif card.status == 'suspended':
                    return False, "Card is suspended", None
            
            # Check expiry date
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            if int(expiry_year) < current_year or (int(expiry_year) == current_year and int(expiry_month) < current_month):
                return False, "Card has expired", None
            
            # Check expiry date matches
            if card.expiry_month != expiry_month or card.expiry_year != expiry_year:
                return False, "Invalid expiry date", None
            
            # Check CVV
            if card.cvv != cvv:
                return False, "Invalid CVV", None
            
            # Check card holder name (case insensitive)
            if card.card_holder_name.lower().strip() != card_holder_name.lower().strip():
                return False, "Card holder name does not match", None
            
            return True, "Card validated successfully", card
            
        except Exception as e:
            return False, f"Validation error: {str(e)}", None
    
    @staticmethod
    def process_payment(card_number, card_holder_name, expiry_month, expiry_year, cvv, amount, reference_id=""):
        """
        Process payment through mock banking system
        Returns: (success, message, transaction_id, transaction_object)
        """
        try:
            # Validate card first
            is_valid, error_message, card = MockBankingService.validate_card(
                card_number, card_holder_name, expiry_month, expiry_year, cvv
            )
            
            if not is_valid:
                # Create failed transaction record
                transaction = PaymentTransaction.objects.create(
                    card=card,
                    card_number=card_number.replace(' ', '').replace('-', ''),
                    amount=Decimal(str(amount)),
                    status='declined',
                    decline_reason='invalid_card',
                    reference_id=reference_id,
                    processed_at=timezone.now()
                )
                return False, error_message, str(transaction.transaction_id), transaction
            
            # Check sufficient funds
            if card.balance < Decimal(str(amount)):
                transaction = PaymentTransaction.objects.create(
                    card=card,
                    card_number=card.card_number,
                    amount=Decimal(str(amount)),
                    status='declined',
                    decline_reason='insufficient_funds',
                    reference_id=reference_id,
                    processed_at=timezone.now()
                )
                return False, "Insufficient funds", str(transaction.transaction_id), transaction
            
            # Check daily limit
            today = timezone.now().date()
            daily_transactions = PaymentTransaction.objects.filter(
                card=card,
                status='approved',
                created_at__date=today
            )
            daily_spent = sum(t.amount for t in daily_transactions)
            
            if daily_spent + Decimal(str(amount)) > card.daily_limit:
                transaction = PaymentTransaction.objects.create(
                    card=card,
                    card_number=card.card_number,
                    amount=Decimal(str(amount)),
                    status='declined',
                    decline_reason='limit_exceeded',
                    reference_id=reference_id,
                    processed_at=timezone.now()
                )
                return False, "Daily limit exceeded", str(transaction.transaction_id), transaction
            
            # Simulate random network failures (5% chance)
            if random.randint(1, 100) <= 5:
                transaction = PaymentTransaction.objects.create(
                    card=card,
                    card_number=card.card_number,
                    amount=Decimal(str(amount)),
                    status='failed',
                    decline_reason='network_error',
                    reference_id=reference_id,
                    processed_at=timezone.now()
                )
                return False, "Network error occurred. Please try again.", str(transaction.transaction_id), transaction
            
            # Process successful payment
            transaction = PaymentTransaction.objects.create(
                card=card,
                card_number=card.card_number,
                amount=Decimal(str(amount)),
                status='approved',
                reference_id=reference_id,
                processed_at=timezone.now()
            )
            
            # Deduct amount from card balance
            card.balance -= Decimal(str(amount))
            card.save()
            
            return True, "Payment processed successfully", str(transaction.transaction_id), transaction
            
        except Exception as e:
            # Create failed transaction for any unexpected errors
            try:
                transaction = PaymentTransaction.objects.create(
                    card_number=card_number.replace(' ', '').replace('-', ''),
                    amount=Decimal(str(amount)),
                    status='failed',
                    decline_reason='network_error',
                    reference_id=reference_id,
                    processed_at=timezone.now()
                )
                return False, f"Payment processing error: {str(e)}", str(transaction.transaction_id), transaction
            except:
                return False, f"Payment processing error: {str(e)}", None, None