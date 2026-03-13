
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import LoyaltyAccount, LoyaltyTransaction, SagaMilesAward
import json
from datetime import datetime
import pytz

def loyalty_status(request):
    """Basic loyalty status endpoint for AAdvantage dashboard"""
    user_id = request.GET.get('user_id', '1')  # Default to user 1 for demo
    
    print(f"[DEBUG] Loyalty status request for user_id: {user_id}")
    
    try:
        # Get or create loyalty account
        account, created = LoyaltyAccount.objects.get_or_create(user_id=user_id)
        if created:
            print(f"[DEBUG] Created new loyalty account for user {user_id}")
        
        current_points = account.points_balance
        tier = account.tier_status
        miles_to_next = account.miles_to_next_tier()
        
        print(f"[DEBUG] Points for user {user_id}: {current_points} (tier: {tier})")
        
        return JsonResponse({
            'status': 'active',
            'service': 'loyalty-service',
            'message': 'AAdvantage loyalty program is active',
            'user_tier': tier,
            'points_balance': current_points,
            'miles_to_next_tier': miles_to_next,
            'benefits': [
                'Priority boarding',
                'Free checked bags',
                'Lounge access',
                'Upgrade eligibility'
            ]
        })
    except Exception as e:
        print(f"[ERROR] Loyalty status error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_transaction_points(request):
    """Add points for a transaction (1 dollar = 0.5 points)"""
    try:
        data = json.loads(request.body)
        user_id = str(data.get('user_id', '1'))
        transaction_amount = float(data.get('amount', 0))
        transaction_id = data.get('transaction_id', '')
        
        print(f"[DEBUG] Received transaction data: {data}")
        print(f"[DEBUG] Transaction amount: ${transaction_amount}")
        
        # Calculate points: 0.5 points per dollar (SCRUM-1)
        points_earned = int(transaction_amount * 0.5)
        print(f"[DEBUG] Points calculation: ${transaction_amount} = {points_earned} points (0.5:1 ratio)")
        
        # Get or create loyalty account
        account, created = LoyaltyAccount.objects.get_or_create(user_id=user_id)
        if created:
            print(f"[DEBUG] Created new loyalty account for user {user_id}")
        
        # Add points to user balance
        account.points_balance += points_earned
        account.save()  # This will also update the tier
        
        # Create transaction record
        LoyaltyTransaction.objects.create(
            account=account,
            transaction_id=transaction_id,
            transaction_type='flight_booking',
            points_earned=points_earned,
            amount=transaction_amount,
            description=f'Flight booking - ${transaction_amount:.2f}'
        )
        
        print(f"[DEBUG] Added {points_earned} points for user {user_id}, transaction ${transaction_amount}")
        
        return JsonResponse({
            'success': True,
            'points_earned': points_earned,
            'total_points': account.points_balance,
            'message': f'Earned {points_earned} points from transaction'
        })
        
    except Exception as e:
        print(f"[ERROR] Add transaction points error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_transaction_history(request, user_id):
    """Get transaction history for a user"""
    try:
        # Get or create loyalty account
        account, created = LoyaltyAccount.objects.get_or_create(user_id=str(user_id))
        
        # Get transactions from database
        transactions = LoyaltyTransaction.objects.filter(account=account).order_by('-created_at')
        
        # DIAGNOSTIC: Log transaction types and compensation entries
        print(f"[DASHBOARD_DEBUG] Transaction history requested for user_id: {user_id}")
        print(f"[DASHBOARD_DEBUG] Total transactions found: {transactions.count()}")
        compensation_count = sum(1 for t in transactions if 'compensation' in t.description.lower() or 'comp-' in t.transaction_id.lower())
        adjustment_count = sum(1 for t in transactions if t.transaction_type == 'adjustment')
        print(f"[DASHBOARD_DEBUG] Compensation transactions: {compensation_count}")
        print(f"[DASHBOARD_DEBUG] Adjustment transactions: {adjustment_count}")
        
        # Format transactions for response
        transaction_list = []
        for trans in transactions:
            transaction_data = {
                'transaction_id': trans.transaction_id,
                'type': trans.transaction_type,
                'date': trans.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'date_utc': trans.created_at.isoformat(),
                'date_local': trans.created_at.astimezone(pytz.timezone('Asia/Calcutta')).strftime('%Y-%m-%d %H:%M:%S IST'),
                'description': trans.description
            }
            
            if trans.points_earned > 0:
                transaction_data.update({
                    'points_earned': trans.points_earned,
                    'amount': trans.amount
                })
            else:
                transaction_data.update({
                    'points_redeemed': trans.points_redeemed,
                    'points_value': trans.points_value
                })
            
            transaction_list.append(transaction_data)
        
        return JsonResponse({
            'user_id': user_id,
            'transactions': transaction_list,
            'total_transactions': len(transaction_list)
        })
    except Exception as e:
        print(f"[ERROR] Get transaction history error: {e}")
        import traceback
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def redeem_points(request):
    """Redeem points for payment (deduct from user balance)"""
    try:
        data = json.loads(request.body)
        user_id = str(data.get('user_id', '1'))
        points_to_redeem = int(data.get('points_to_redeem', 0))
        transaction_id = data.get('transaction_id', '')
        
        print(f"[DEBUG] Points redemption request: {data}")
        
        # Get or create loyalty account
        account, created = LoyaltyAccount.objects.get_or_create(user_id=user_id)
        
        # Check if user has enough points
        if points_to_redeem > account.points_balance:
            return JsonResponse({
                'error': f'Insufficient points. Available: {account.points_balance}, Requested: {points_to_redeem}'
            }, status=400)
        
        # Deduct points from user balance
        account.points_balance -= points_to_redeem
        account.save()  # This will also update the tier
        
        points_value = points_to_redeem * 0.01  # 1 point = $0.01
        
        # Create redemption transaction record
        LoyaltyTransaction.objects.create(
            account=account,
            transaction_id=transaction_id,
            transaction_type='miles_redemption',
            points_redeemed=points_to_redeem,
            points_value=points_value,
            description=f'Points redemption - {points_to_redeem} points'
        )
        
        print(f"[DEBUG] Redeemed {points_to_redeem} points (${points_value:.2f}) for user {user_id}")
        
        return JsonResponse({
            'success': True,
            'points_redeemed': points_to_redeem,
            'points_value': points_value,
            'remaining_points': account.points_balance,
                        'message': f'Redeemed {points_to_redeem} points worth ${points_value:.2f}'  
        })  
  
    except Exception as e:  
        print(f"[ERROR] Points redemption error: {e}")  
        return JsonResponse({'error': str(e)}, status=500) 
