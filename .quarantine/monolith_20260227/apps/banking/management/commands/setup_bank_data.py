
from django.core.management.base import BaseCommand
from decimal import Decimal
from apps.banking.models import BankCard


class Command(BaseCommand):
    help = 'Setup mock bank card data for testing payment processing'

    def handle(self, *args, **options):
        self.stdout.write('Setting up mock bank card data...')
        
        # Clear existing data
        BankCard.objects.all().delete()
        
        # Create test cards with different scenarios
        test_cards = [
            {
                'card_number': '4444000022221367',
                'card_holder_name': 'aditi jaiswal',
                'expiry_month': '12',
                'expiry_year': '2030',
                'cvv': '123',
                'card_type': 'visa',
                'status': 'active',
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
                'status': 'active',
                'balance': Decimal('25000.00'),
                'daily_limit': Decimal('5000.00'),
            },
            {
                'card_number': '4000000000000002',
                'card_holder_name': 'jane smith',
                'expiry_month': '03',
                'expiry_year': '2028',
                'cvv': '789',
                'card_type': 'visa',
                'status': 'active',
                'balance': Decimal('100.00'),  # Low balance for testing insufficient funds
                'daily_limit': Decimal('1000.00'),
            },
            {
                'card_number': '4000000000000119',
                'card_holder_name': 'blocked user',
                'expiry_month': '09',
                'expiry_year': '2027',
                'cvv': '321',
                'card_type': 'visa',
                'status': 'blocked',  # Blocked card for testing
                'balance': Decimal('10000.00'),
                'daily_limit': Decimal('2000.00'),
            },
            {
                'card_number': '4000000000000051',
                'card_holder_name': 'expired card',
                'expiry_month': '01',
                'expiry_year': '2020',  # Expired card
                'cvv': '654',
                'card_type': 'visa',
                'status': 'active',
                'balance': Decimal('5000.00'),
                'daily_limit': Decimal('1500.00'),
            },
            {
                'card_number': '4242424242424242',
                'card_holder_name': 'test user',
                'expiry_month': '08',
                'expiry_year': '2026',
                'cvv': '987',
                'card_type': 'visa',
                'status': 'active',
                'balance': Decimal('75000.00'),
                'daily_limit': Decimal('15000.00'),
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
                        f'Created card: {card.get_masked_number()} - {card.card_holder_name}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {created_count} mock bank cards!'
            )
        )
        
        # Display test card information
        self.stdout.write('\n' + '='*60)
        self.stdout.write('TEST CARD INFORMATION FOR PAYMENT TESTING:')
        self.stdout.write('='*60)
        
        self.stdout.write('\n✅ VALID CARDS (Should work):')
        self.stdout.write('Card: 4444000022221367 | Name: aditi jaiswal | CVV: 123 | Exp: 12/2030')
        self.stdout.write('Card: 5555000044442222 | Name: john doe | CVV: 456 | Exp: 06/2029')
        self.stdout.write('Card: 4242424242424242 | Name: test user | CVV: 987 | Exp: 08/2026')
        
        self.stdout.write('\n❌ INVALID CARDS (Should fail):')
        self.stdout.write('Card: 4000000000000002 | Name: jane smith | CVV: 789 | Exp: 03/2028 (Insufficient funds)')
        self.stdout.write('Card: 4000000000000119 | Name: blocked user | CVV: 321 | Exp: 09/2027 (Blocked card)')
        self.stdout.write('Card: 4000000000000051 | Name: expired card | CVV: 654 | Exp: 01/2020 (Expired)')
        
        self.stdout.write('\n💡 Use these cards to test different payment scenarios!')
        self.stdout.write('='*60)