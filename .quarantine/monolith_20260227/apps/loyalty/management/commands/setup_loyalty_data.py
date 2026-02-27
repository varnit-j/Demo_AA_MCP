from django.core.management.base import BaseCommand
from decimal import Decimal
from apps.loyalty.models import LoyaltyTier


class Command(BaseCommand):
    help = 'Set up initial loyalty tiers and data'

    def handle(self, *args, **options):
        self.stdout.write('Setting up loyalty tiers...')
        
        # Create loyalty tiers if they don't exist
        tiers_data = [
            {
                'name': 'bronze',
                'display_name': 'Bronze',
                'min_points_required': 0,
                'points_multiplier': Decimal('1.00'),
                'redemption_bonus': Decimal('1.00'),
            },
            {
                'name': 'silver',
                'display_name': 'Silver',
                'min_points_required': 5000,
                'points_multiplier': Decimal('1.25'),
                'redemption_bonus': Decimal('1.10'),
            },
            {
                'name': 'gold',
                'display_name': 'Gold',
                'min_points_required': 15000,
                'points_multiplier': Decimal('1.50'),
                'redemption_bonus': Decimal('1.20'),
            },
            {
                'name': 'platinum',
                'display_name': 'Platinum',
                'min_points_required': 50000,
                'points_multiplier': Decimal('2.00'),
                'redemption_bonus': Decimal('1.30'),
            },
        ]
        
        for tier_data in tiers_data:
            tier, created = LoyaltyTier.objects.get_or_create(
                name=tier_data['name'],
                defaults=tier_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created tier: {tier.display_name}')
                )
            else:
                self.stdout.write(f'Tier already exists: {tier.display_name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up loyalty data!')
        )