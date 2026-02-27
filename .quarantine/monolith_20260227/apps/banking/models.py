
from django.db import models
from decimal import Decimal
import uuid


class BankCard(models.Model):
    """Mock bank card database for payment simulation"""
    
    CARD_TYPES = [
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex', 'American Express'),
        ('discover', 'Discover'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('blocked', 'Blocked'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]
    
    card_number = models.CharField(max_length=19, unique=True)
    card_holder_name = models.CharField(max_length=100)
    expiry_month = models.CharField(max_length=2)
    expiry_year = models.CharField(max_length=4)
    cvv = models.CharField(max_length=4)
    card_type = models.CharField(max_length=20, choices=CARD_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('10000.00'))
    daily_limit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('5000.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'mock_bank_cards'
        indexes = [
            models.Index(fields=['card_number']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.card_holder_name} - ****{self.card_number[-4:]}"
    
    def get_masked_number(self):
        """Return masked card number for display"""
        return f"****-****-****-{self.card_number[-4:]}"


class PaymentTransaction(models.Model):
    """Mock payment transaction records"""
    
    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
        ('failed', 'Failed'),
    ]
    
    DECLINE_REASONS = [
        ('insufficient_funds', 'Insufficient Funds'),
        ('invalid_card', 'Invalid Card'),
        ('expired_card', 'Expired Card'),
        ('blocked_card', 'Blocked Card'),
        ('limit_exceeded', 'Daily Limit Exceeded'),
        ('invalid_cvv', 'Invalid CVV'),
        ('network_error', 'Network Error'),
    ]
    
    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    card = models.ForeignKey(BankCard, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    card_number = models.CharField(max_length=19)  # Store even if card not found
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='pending')
    decline_reason = models.CharField(max_length=50, choices=DECLINE_REASONS, null=True, blank=True)
    reference_id = models.CharField(max_length=100, blank=True)  # Ticket reference
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'mock_payment_transactions'
        indexes = [
            models.Index(fields=['card_number']),
            models.Index(fields=['status']),
            models.Index(fields=['reference_id']),
        ]
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.status} - ${self.amount}"