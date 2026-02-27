from django.core.management.base import BaseCommand
from decimal import Decimal
from apps.banking.models import BankCard


class Command(BaseCommand):
    help = 'Set up test bank cards for payment testing'

    def handle(self, *args, **options):
        # Clear existing test cards
        BankCard.objects.all().delete()
        
        # Create test cards with sufficient balance and high daily limits
        test_cards = [
            {
                'card_number': '4242424242424242',
                'card_holder_name': 'test user',
                'expiry_month': '08',
                'expiry_year': '2026',
                'cvv': '987',
                'card_type': 'visa',
                'balance': Decimal('50000.00'),
                'daily_limit': Decimal('10000.00'),
            },
            {
                'card_number': '4444000022221367',
                'card_holder_name': 'aditi jaiswal',
                'expiry_month': '12',
                'expiry_year': '2030',
                'cvv': '123',
                'card_type': 'visa',
                'balance': Decimal('50000.00'),
                'daily_limit': Decimal('10000.00'),
            },
            {
                'card_number': '5555000044442222',
                'card_holder_name': 'john doe',
                'expiry_month': '06',
                'expiry_year': '2029',
                'cvv': '456',
                'card_type': 'mastercard',
                'balance': Decimal('50000.00'),
                'daily_limit': Decimal('10000.00'),
            },
        ]
        
        created_count = 0
        for card_data in test_cards:
            card, created = BankCard.objects.get_or_create(
                card_number=card_data['card_number'],
                defaults=card_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created test card: {card.card_holder_name} - ****{card.card_number[-4:]}'
                    )
                )
            else:
                # Update existing card with new balance and limit
                for key, value in card_data.items():
                    setattr(card, key, value)
                card.save()
                self.stdout.write(
                    self.style.WARNING(
                        f'Updated test card: {card.card_holder_name} - ****{card.card_number[-4:]}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set up {len(test_cards)} test cards for payment testing'
            )
        )
        
        # Display card information
        self.stdout.write('\nTest Cards Available:')
        for card in BankCard.objects.all():
            self.stdout.write(
                f'  • {card.card_number} - {card.card_holder_name} '
                f'(CVV: {card.cvv}, Exp: {card.expiry_month}/{card.expiry_year}) '
                f'Balance: ${card.balance}, Daily Limit: ${card.daily_limit}'
            )