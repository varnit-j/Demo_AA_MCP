
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import timedelta
from typing import Optional, Dict, Any
import logging

from .models import LoyaltyAccount, LoyaltyTier, PointsTransaction

User = get_user_model()
logger = logging.getLogger(__name__)


class LoyaltyService:
    """Service layer for loyalty program operations"""
    
    @staticmethod
    def get_or_create_account(user) -> 'LoyaltyAccount':
        """Get or create loyalty account for user"""
        account, created = LoyaltyAccount.objects.get_or_create(
            user=user,
            defaults={
                'current_tier': LoyaltyTier.objects.filter(name='bronze').first(),
                'total_points_earned': 0,
                'current_points_balance': 0,
                'lifetime_spending': Decimal('0.00'),
            }
        )
        
        if created:
            logger.info(f"Created new loyalty account for user {user.username}")
        
        return account
    
    @staticmethod
    @transaction.atomic
    def earn_points(
        user,
        points_amount: int,
        reference_id: str = "",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        expires_in_days: int = 365
    ) -> PointsTransaction:
        """Award points to user account"""
        
        if points_amount <= 0:
            raise ValueError("Points amount must be positive")
        
        account = LoyaltyService.get_or_create_account(user)
        
        # Apply tier multiplier
        effective_multiplier = account.get_effective_multiplier()
        final_points = int(points_amount * effective_multiplier)
        
        # Create transaction
        expires_at = timezone.now() + timedelta(days=expires_in_days)
        
        points_transaction = PointsTransaction.objects.create(
            account=account,
            transaction_type='earn',
            points_amount=final_points,
            status='completed',
            reference_id=reference_id,
            description=description or f"Earned {final_points} points from flight booking",
            metadata=metadata or {},
            expires_at=expires_at,
            processed_at=timezone.now()
        )
        
        # Update account balance
        account.total_points_earned += final_points
        account.current_points_balance += final_points
        account.save()
        
        # Check for tier upgrade
        LoyaltyService._check_tier_upgrade(account)
        
        logger.info(f"Awarded {final_points} points to {user.username} (ref: {reference_id})")
        
        return points_transaction
    
    @staticmethod
    @transaction.atomic
    def redeem_points(
        user,
        points_amount: int,
        reference_id: str = "",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> PointsTransaction:
        """Redeem points from user account"""
        
        if points_amount <= 0:
            raise ValueError("Points amount must be positive")
        
        account = LoyaltyService.get_or_create_account(user)
        
        if account.current_points_balance < points_amount:
            raise ValueError(f"Insufficient points balance. Available: {account.current_points_balance}, Required: {points_amount}")
        # Create transaction
        points_transaction = PointsTransaction.objects.create(
            account=account,
            transaction_type='redeem',
            points_amount=points_amount,
            status='completed',
            reference_id=reference_id,
            description=description or f"Redeemed {points_amount} points for flight booking payment",
            metadata=metadata or {},
            processed_at=timezone.now()
        )
        
        # Update account balance
        account.current_points_balance -= points_amount
        account.save()
        
        logger.info(f"Redeemed {points_amount} points from {user.username} (ref: {reference_id})")
        
        return points_transaction
    
    @staticmethod
    def calculate_points_value(points_amount: int, tier: Optional['LoyaltyTier'] = None) -> Decimal:
        """Calculate currency value of points"""
        base_rate = Decimal('0.01')  # 1 point = $0.01 by default
        
        if tier and tier.redemption_bonus:
            return Decimal(points_amount) * base_rate * tier.redemption_bonus
        
        return Decimal(points_amount) * base_rate
    
    @staticmethod
    def _check_tier_upgrade(account: LoyaltyAccount) -> bool:
        """Check if user qualifies for tier upgrade"""
        current_tier = account.current_tier
        
        # Find the highest tier user qualifies for
        qualifying_tier = LoyaltyTier.objects.filter(
            min_points_required__lte=account.total_points_earned
        ).order_by('-min_points_required').first()
        
        if qualifying_tier and (not current_tier or qualifying_tier.min_points_required > current_tier.min_points_required):
            account.current_tier = qualifying_tier
            account.tier_qualification_date = timezone.now()
            account.save()
            
            logger.info(f"User {account.user.username} upgraded to {qualifying_tier.display_name}")
            return True
        
        return False
    
    @staticmethod
    def get_points_balance(user) -> int:
        """Get current points balance for user"""
        try:
            account = LoyaltyAccount.objects.get(user=user)
            return account.current_points_balance
        except LoyaltyAccount.DoesNotExist:
            return 0
    
    @staticmethod
    def get_transaction_history(user, limit: int = 50) -> list:
        """Get transaction history for user"""
        try:
            account = LoyaltyAccount.objects.get(user=user)
            return list(account.transactions.filter(status='completed')[:limit])  # type: ignore
        except LoyaltyAccount.DoesNotExist:
            return []
            