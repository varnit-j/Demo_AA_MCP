from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import pytz

from .service import LoyaltyService
from .models import LoyaltyTier


@login_required
def loyalty_status(request):
    """API endpoint to fetch loyalty status for a user"""
    user_id = request.GET.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'User ID is required'}, status=400)
    try:
        account = LoyaltyService.get_account_by_user_id(user_id)
        if not account:
            raise Http404("Loyalty account not found")
        return JsonResponse({
            'user_id': user_id,
            'points_balance': account.current_points_balance,
            'tier': account.current_tier.display_name if account.current_tier else 'No Tier'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def loyalty_history(request, user_id):
    """API endpoint to fetch loyalty transaction history for a user"""
    try:
        transactions = LoyaltyService.get_transaction_history_by_user_id(user_id)
        if not transactions:
            raise Http404("No transactions found for the user")
        return JsonResponse({
            'user_id': user_id,
            'transactions': [
                {
                    'transaction_type': t.transaction_type,
                    'points_amount': t.points_amount,
                    'status': t.status,
                    'date': t.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'date_utc': t.created_at.isoformat(),
                    'date_local': t.created_at.astimezone(pytz.timezone('Asia/Calcutta')).strftime('%Y-%m-%d %H:%M:%S IST'),
                } for t in transactions
            ]
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def loyalty_dashboard(request):
    """Dashboard view for loyalty program"""
    try:
        account = LoyaltyService.get_or_create_account(request.user)
        return render(request, 'loyalty/dashboard.html', {
            'account': account,
            'points_balance': account.current_points_balance,
            'tier': account.current_tier
        })
    except Exception as e:
        return render(request, 'loyalty/dashboard.html', {
            'error': str(e)
        })


@login_required
def points_history(request):
    """Points history view"""
    try:
        transactions = LoyaltyService.get_transaction_history(request.user)
        return render(request, 'loyalty/points_history.html', {
            'transactions': transactions
        })
    except Exception as e:
        return render(request, 'loyalty/points_history.html', {
            'error': str(e)
        })


@login_required
def tier_info(request):
    """Tier information view"""
    try:
        tiers = LoyaltyTier.objects.all().order_by('points_required')
        account = LoyaltyService.get_or_create_account(request.user)
        return render(request, 'loyalty/tier_info.html', {
            'tiers': tiers,
            'current_tier': account.current_tier,
            'current_points': account.current_points_balance
        })
    except Exception as e:
        return render(request, 'loyalty/tier_info.html', {
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["POST"])
def calculate_points_value(request):
    """Calculate points value for redemption"""
    try:
        data = json.loads(request.body)
        points = int(data.get('points', 0))
        value = LoyaltyService.calculate_points_value(points)
        return JsonResponse({
            'points': points,
            'value': float(value),
            'rate': 0.01  # 1 point = $0.01
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)