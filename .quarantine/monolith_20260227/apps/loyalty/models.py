from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class LoyaltyTier(models.Model):
    """Loyalty tier definitions with benefits and requirements"""
    
    TIER_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    ]
    
    name = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    display_name = models.CharField(max_length=50)
    min_points_required = models.PositiveIntegerField(default=0)
    points_multiplier = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=Decimal('1.00'),
        help_text="Multiplier for points earned (e.g., 1.5 for 50% bonus)"
    )
    redemption_bonus = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text="Bonus when redeeming points (e.g., 1.1 for 10% bonus value)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['min_points_required']
    
    def __str__(self):
        return f"{self.display_name} (min: {self.min_points_required} pts)"


class LoyaltyAccount(models.Model):
    """User's loyalty account with current tier and points balance"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty_account')
    current_tier = models.ForeignKey(
        LoyaltyTier, 
        on_delete=models.PROTECT, 
        related_name='members',
        null=True, 
        blank=True
    )
    total_points_earned = models.PositiveIntegerField(default=0)
    current_points_balance = models.PositiveIntegerField(default=0)
    lifetime_spending = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tier_qualification_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['current_tier']),
        ]
    
    def __str__(self):
        tier_name = self.current_tier.display_name if self.current_tier else "No Tier"
        return f"{self.user.username} - {tier_name} ({self.current_points_balance} pts)"
    
    def get_effective_multiplier(self):
        """Get the points earning multiplier for current tier"""
        if self.current_tier:
            return self.current_tier.points_multiplier
        return Decimal('1.00')
    
    def get_redemption_bonus(self):
        """Get the redemption bonus for current tier"""
        if self.current_tier:
            return self.current_tier.redemption_bonus
        return Decimal('1.00')


class PointsTransaction(models.Model):
    """Ledger for all points transactions (earn/burn)"""
    
    TRANSACTION_TYPES = [
        ('earn', 'Earn Points'),
        ('redeem', 'Redeem Points'),
        ('expire', 'Points Expired'),
        ('bonus', 'Bonus Points'),
        ('adjustment', 'Manual Adjustment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    points_amount = models.IntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Transaction context
    reference_id = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Expiry tracking
    expires_at = models.DateTimeField(null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['account', 'transaction_type']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['reference_id']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.account.user.username} - {self.transaction_type} {self.points_amount} pts"
    
    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.processed_at:
            self.processed_at = timezone.now()
        super().save(*args, **kwargs)