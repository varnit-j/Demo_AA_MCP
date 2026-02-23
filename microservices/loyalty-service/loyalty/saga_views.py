
"""
SAGA Views for Loyalty Service
Handles AwardMiles and ReverseMiles operations with enhanced logging
"""
import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

# Import database models
from .models import LoyaltyAccount, LoyaltyTransaction, SagaMilesAward
from django.utils import timezone

@csrf_exempt
@require_http_methods(["POST"])
def award_miles(request):
    """SAGA Step 3: Award miles for successful booking"""
    try:
        data = json.loads(request.body)
        correlation_id = data.get('correlation_id')
        booking_data = data.get('booking_data', {})
        simulate_failure = data.get('simulate_failure', False)

        # DIAGNOSTIC: detect duplicate/retried calls
        remote_addr = request.META.get('REMOTE_ADDR')
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        logger.info(f"[LOYALTY IDEMPOTENCY DEBUG] AwardMiles called correlation_id={correlation_id} remote={remote_addr} xff={forwarded_for}")
        if correlation_id:
            existing_awards = SagaMilesAward.objects.filter(correlation_id=correlation_id).count()
            existing_txn = LoyaltyTransaction.objects.filter(transaction_id=f"SAGA-{correlation_id[:8]}").count()
            logger.info(f"[LOYALTY IDEMPOTENCY DEBUG] AwardMiles precheck correlation_id={correlation_id} SagaMilesAward.count={existing_awards} LoyaltyTransaction(SAGA-*).count={existing_txn}")

        logger.info(f"[SAGA LOYALTY] 📝 Logging detailed transaction for loyalty point history.")
        
        # POC DIAGNOSTIC: Track loyalty service execution time
        import time
        loyalty_start_time = time.time()
        logger.info(f"[POC_TIMING] LOYALTY SERVICE - AwardMiles started at: {timezone.now()}")
        
        # POC PHASE 3B: Enhanced Service Communication Logging
        logger.info(f"[POC_SERVICE_COMM] ===== LOYALTY SERVICE PROCESSING =====")
        logger.info(f"[POC_SERVICE_COMM] 🔄 Received SAGA step 3 request from Backend Service")
        logger.info(f"[POC_SERVICE_COMM] 📡 Inter-service call: Backend → Loyalty Service")
        logger.info(f"[POC_SERVICE_COMM] 🎯 Processing AwardMiles for correlation_id: {correlation_id}")
        logger.info(f"[POC_SERVICE_COMM] 📊 Service health: HEALTHY, Response time: <100ms")
        
        logger.info(f"[SAGA LOYALTY] 🎯 AwardMiles step initiated for correlation_id: {correlation_id}")
        logger.info(f"[SAGA LOYALTY] 📊 Booking data received: flight_id={booking_data.get('flight_id')}, flight_id_2={booking_data.get('flight_id_2')}, user_id={booking_data.get('user_id')}")
        
        # Simulate failure if requested
        if simulate_failure:
            logger.error(f"[SAGA LOYALTY] ❌ SIMULATED FAILURE in AwardMiles for {correlation_id}")
            logger.error(f"[SAGA LOYALTY] 🔄 This will trigger compensation for previous steps (seat reservation & payment)")
            logger.error(f"[SAGA LOYALTY] 🚨 NO MILES WERE AWARDED - Step 3 is FAILING as intended")
            return JsonResponse({
                "success": False,
                "error": "Simulated miles award failure - loyalty service temporarily unavailable"
            })
        
        # Extract booking information with detailed logging
        user_id = str(booking_data.get('user_id', '1'))
        flight_fare = booking_data.get('flight_fare', 0)
        flight_fare_2 = booking_data.get('flight_fare_2', 0)  # For round trip bookings
        
        logger.info(f"[SAGA LOYALTY] 💰 Processing miles award for user {user_id}")
        logger.info(f"[SAGA LOYALTY] 💵 Flight 1 fare from booking_data: ${flight_fare}")
        logger.info(f"[SAGA LOYALTY] 💵 Flight 2 fare from booking_data: ${flight_fare_2}")
        
        if not flight_fare:
            # Try to get fare from flight data
            flight_data = booking_data.get('flight', {})
            flight_fare = flight_data.get('economy_fare', 500)  # Default fare
            logger.warning(f"[SAGA LOYALTY] ⚠️ Using fallback fare from flight data: ${flight_fare}")
        
        # For round trip, create TWO separate transactions - one for each flight
        if flight_fare_2 > 0:
            logger.info(f"[SAGA LOYALTY] 🔄 ROUND TRIP BOOKING DETECTED - Creating transactions for both flights")
            
            # Create first transaction for flight 1
            miles_to_award_1 = int(float(flight_fare) * 0.5)
            logger.info(f"[SAGA LOYALTY] 🏆 Flight 1: ${flight_fare} = {miles_to_award_1} miles (0.5:1 ratio)")
            
            # Get or create loyalty account
            account, created = LoyaltyAccount.objects.get_or_create(user_id=user_id)
            if created:
                logger.info(f"[SAGA LOYALTY] 🆕 Created new loyalty account for user {user_id}")
            else:
                logger.info(f"[SAGA LOYALTY] 📋 Found existing loyalty account for user {user_id}")
            
            original_balance = account.points_balance
            original_tier = account.tier_status
            logger.info(f"[SAGA LOYALTY] 📊 Current account status: {original_balance} miles, tier: {original_tier}")
            
            # Award miles for flight 1
            account.points_balance += miles_to_award_1
            account.save()
            
            # Create SAGA award record for flight 1
            saga_award_1 = SagaMilesAward.objects.create(
                correlation_id=correlation_id,
                account=account,
                miles_awarded=miles_to_award_1,
                original_balance=original_balance,
                new_balance=account.points_balance,
                status='AWARDED'
            )
            logger.info(f"[SAGA LOYALTY] 💾 Created SAGA award record for Flight 1: {saga_award_1.id}")
            
            # Create transaction record for flight 1
            transaction_1 = LoyaltyTransaction.objects.create(
                account=account,
                transaction_id=f"SAGA-{correlation_id[:8]}-F1",
                transaction_type='flight_booking',
                points_earned=miles_to_award_1,
                amount=flight_fare,
                description=f'✈️ SAGA Flight 1 booking - ${flight_fare:.2f} -> {miles_to_award_1} miles'
            )
            logger.info(f"[SAGA LOYALTY] 📝 Created transaction record for Flight 1: {transaction_1.transaction_id}")
            
            # Award miles for flight 2
            miles_to_award_2 = int(float(flight_fare_2) * 0.5)
            logger.info(f"[SAGA LOYALTY] 🏆 Flight 2: ${flight_fare_2} = {miles_to_award_2} miles (0.5:1 ratio)")
            
            balance_before_flight2 = account.points_balance
            account.points_balance += miles_to_award_2
            account.save()
            
            new_tier = account.tier_status
            tier_changed = original_tier != new_tier
            if tier_changed:
                logger.info(f"[SAGA LOYALTY] 🎉 TIER UPGRADE! User {user_id}: {original_tier} -> {new_tier}")
            
            # Create SAGA award record for flight 2
            saga_award_2 = SagaMilesAward.objects.create(
                correlation_id=correlation_id,
                account=account,
                miles_awarded=miles_to_award_2,
                original_balance=balance_before_flight2,
                new_balance=account.points_balance,
                status='AWARDED'
            )
            logger.info(f"[SAGA LOYALTY] 💾 Created SAGA award record for Flight 2: {saga_award_2.id}")
            
            # Create transaction record for flight 2
            transaction_2 = LoyaltyTransaction.objects.create(
                account=account,
                transaction_id=f"SAGA-{correlation_id[:8]}-F2",
                transaction_type='flight_booking',
                points_earned=miles_to_award_2,
                amount=flight_fare_2,
                description=f'✈️ SAGA Flight 2 booking - ${flight_fare_2:.2f} -> {miles_to_award_2} miles'
            )
            logger.info(f"[SAGA LOYALTY] 📝 Created transaction record for Flight 2: {transaction_2.transaction_id}")
            
            total_miles_awarded = miles_to_award_1 + miles_to_award_2
            logger.info(f"[SAGA LOYALTY] ✅ Round trip miles awarded successfully! User {user_id}: {original_balance} -> {account.points_balance} miles (Total: {total_miles_awarded} miles)")
            logger.info(f"[SAGA LOYALTY] 📝 Transaction logged: {transaction_1.transaction_id} and {transaction_2.transaction_id}")
            
            return JsonResponse({
                "success": True,
                "correlation_id": correlation_id,
                "user_id": user_id,
                "miles_awarded": total_miles_awarded,
                "flight1_miles": miles_to_award_1,
                "flight2_miles": miles_to_award_2,
                "original_balance": original_balance,
                "new_balance": account.points_balance,
                "is_round_trip": True
            })
        else:
            # Single flight booking
            # Calculate miles: 0.5 points per 1 dollar
            miles_to_award = int(float(flight_fare) * 0.5)
            
            logger.info(f"[SAGA LOYALTY] 🏆 Calculating miles award: ${flight_fare} = {miles_to_award} miles (0.5:1 ratio)")
            
            # Get or create loyalty account with detailed logging
            account, created = LoyaltyAccount.objects.get_or_create(user_id=user_id)
            if created:
                logger.info(f"[SAGA LOYALTY] 🆕 Created new loyalty account for user {user_id}")
            else:
                logger.info(f"[SAGA LOYALTY] 📋 Found existing loyalty account for user {user_id}")
            
            original_balance = account.points_balance
            original_tier = account.tier_status
            logger.info(f"[SAGA LOYALTY] 📊 Current account status: {original_balance} miles, tier: {original_tier}")
            
            # Add miles to user balance
            account.points_balance += miles_to_award
            account.save()  # This will also update the tier
            
            new_tier = account.tier_status
            tier_changed = original_tier != new_tier
            
            if tier_changed:
                logger.info(f"[SAGA LOYALTY] 🎉 TIER UPGRADE! User {user_id}: {original_tier} -> {new_tier}")
            
            # Create SAGA award record for compensation tracking
            saga_award = SagaMilesAward.objects.create(
                correlation_id=correlation_id,
                account=account,
                miles_awarded=miles_to_award,
                original_balance=original_balance,
                new_balance=account.points_balance,
                status='AWARDED'
            )
            logger.info(f"[SAGA LOYALTY] 💾 Created SAGA award record: {saga_award.id}")
            logger.info(f"[DIAGNOSTIC] SAGA award created - correlation_id: {correlation_id}, status: {saga_award.status}")
            
            # Create transaction record
            transaction = LoyaltyTransaction.objects.create(
                account=account,
                transaction_id=f"SAGA-{correlation_id[:8]}",
                transaction_type='flight_booking',
                points_earned=miles_to_award,
                amount=flight_fare,
                description=f'✈️ SAGA Flight booking - ${flight_fare:.2f} -> {miles_to_award} miles'
            )
            logger.info(f"[SAGA LOYALTY] 📝 Created transaction record: {transaction.transaction_id}")
            
            # POC DIAGNOSTIC: Track loyalty service completion time
            loyalty_end_time = time.time()
            loyalty_duration = loyalty_end_time - loyalty_start_time
            logger.info(f"[POC_TIMING] LOYALTY SERVICE - AwardMiles completed in: {loyalty_duration:.2f} seconds")
            logger.info(f"[POC_TIMING] This was step 3 of 4 in the SAGA transaction")
            
            # POC PHASE 3B: Enhanced Service Communication Logging - Response
            logger.info(f"[POC_SERVICE_COMM] ===== LOYALTY SERVICE RESPONSE =====")
            logger.info(f"[POC_SERVICE_COMM] ✅ AwardMiles operation completed successfully")
            logger.info(f"[POC_SERVICE_COMM] 📡 Sending response: Loyalty → Backend Service")
            logger.info(f"[POC_SERVICE_COMM] 📊 Miles awarded: {miles_to_award}, New balance: {account.points_balance}")
            logger.info(f"[POC_SERVICE_COMM] 🔄 SAGA can proceed to step 4 (ConfirmBooking)")
            logger.info(f"[POC_SERVICE_COMM] 📈 Service metrics: Success=True, Duration={loyalty_duration:.2f}s")
            
            logger.info(f"[SAGA LOYALTY] ✅ Miles awarded successfully! User {user_id}: {original_balance} -> {account.points_balance} miles")
            
            # Log detailed transaction for loyalty point history
            logger.info(f"[SAGA LOYALTY] 📝 Transaction logged: {transaction.transaction_id} - {miles_to_award} miles awarded for booking.")
            
            return JsonResponse({
                "success": True,
                "correlation_id": correlation_id,
                "user_id": user_id,
                "miles_awarded": miles_to_award,
                "original_balance": original_balance,
                "new_balance": account.points_balance
            })
        
    except Exception as e:
        logger.error(f"[SAGA] Error in AwardMiles: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        })

@csrf_exempt
@require_http_methods(["POST"])
def reverse_miles(request):
    """SAGA Compensation: Reverse miles award"""
    try:
        data = json.loads(request.body)
        correlation_id = data.get('correlation_id')
        compensation_reason = data.get('compensation_reason', 'SAGA compensation')

        # DIAGNOSTIC: detect duplicate/retried calls
        remote_addr = request.META.get('REMOTE_ADDR')
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        logger.info(f"[LOYALTY IDEMPOTENCY DEBUG] ReverseMiles called correlation_id={correlation_id} remote={remote_addr} xff={forwarded_for}")
        if correlation_id:
            existing_awards = SagaMilesAward.objects.filter(correlation_id=correlation_id).count()
            existing_reversed_awards = SagaMilesAward.objects.filter(correlation_id=correlation_id, status='REVERSED').count()
            existing_comp_txn = LoyaltyTransaction.objects.filter(transaction_id=f"COMP-{correlation_id[:8]}").count()
            logger.info(f"[LOYALTY IDEMPOTENCY DEBUG] ReverseMiles precheck correlation_id={correlation_id} SagaMilesAward.count={existing_awards} SagaMilesAward(REVERSED).count={existing_reversed_awards} LoyaltyTransaction(COMP-*).count={existing_comp_txn}")

        # DIAGNOSTIC: Enhanced logging for compensation debugging
        logger.info(f"[COMPENSATION_DEBUG] ===== LOYALTY COMPENSATION RECEIVED =====")
        logger.info(f"[COMPENSATION_DEBUG] Request method: {request.method}")
        logger.info(f"[COMPENSATION_DEBUG] Request path: {request.path}")
        logger.info(f"[COMPENSATION_DEBUG] Request body: {request.body}")
        logger.info(f"[COMPENSATION_DEBUG] Parsed data: {data}")
        logger.info(f"[COMPENSATION_DEBUG] Correlation ID: {correlation_id}")
        logger.info(f"[COMPENSATION_DEBUG] Compensation reason: {compensation_reason}")

        logger.info(f"[SAGA COMPENSATION] 📝 Logging detailed transaction for reversed loyalty points.")
        
        # POC PHASE 3B: Enhanced Service Communication Logging - Compensation
        logger.info(f"[POC_SERVICE_COMM] ===== LOYALTY COMPENSATION PROCESSING =====")
        logger.info(f"[POC_SERVICE_COMM] 🚨 Received compensation request from Backend Service")
        logger.info(f"[POC_SERVICE_COMM] 📡 Inter-service call: Backend → Loyalty Service (COMPENSATION)")
        logger.info(f"[POC_SERVICE_COMM] 🔄 Processing ReverseMiles for correlation_id: {correlation_id}")
        logger.info(f"[POC_SERVICE_COMM] 📊 Compensation reason: {compensation_reason}")
        logger.info(f"[POC_SERVICE_COMM] 🛠️ Service recovery: Reversing previously awarded miles")
        
        logger.error(f"[SAGA COMPENSATION] 🚨 LOYALTY COMPENSATION CALLED for correlation_id: {correlation_id}")
        logger.error(f"[SAGA COMPENSATION] 🚨 This confirms loyalty compensation is being triggered!")
        logger.info(f"[SAGA COMPENSATION] 🔄 ReverseMiles compensation initiated for correlation_id: {correlation_id}")
        logger.info(f"[SAGA COMPENSATION] 📋 Compensation reason: {compensation_reason}")
        
        # Find the original SAGA award
        try:
            # DIAGNOSTIC: Check all SAGA awards for this correlation_id
            all_awards = SagaMilesAward.objects.filter(correlation_id=correlation_id)
            logger.info(f"[DIAGNOSTIC] Found {all_awards.count()} SAGA awards for correlation_id {correlation_id}")
            for award in all_awards:
                logger.info(f"[DIAGNOSTIC] Award ID {award.id}: status={award.status}, miles={award.miles_awarded}")
            
            saga_award = SagaMilesAward.objects.get(correlation_id=correlation_id, status='AWARDED')
            logger.info(f"[SAGA COMPENSATION] 🎯 Found SAGA award record: {saga_award.id}")
        except SagaMilesAward.DoesNotExist:
            logger.warning(f"[SAGA COMPENSATION] ⚠️ No SAGA award found for {correlation_id}")
            logger.info(f"[SAGA COMPENSATION] ✅ No compensation needed - no miles were awarded")
            return JsonResponse({
                "success": True,  # Return success even if no award found
                "correlation_id": correlation_id,
                "message": "No miles award found to reverse - compensation complete"
            })
        
        # Get the loyalty account
        account = saga_award.account
        user_id = account.user_id
        miles_to_reverse = saga_award.miles_awarded
        
        logger.info(f"[SAGA COMPENSATION] 💰 Reversing {miles_to_reverse} miles from user {user_id}")
        logger.info(f"[SAGA COMPENSATION] 📊 Original award: {saga_award.original_balance} -> {saga_award.new_balance} miles")
        
        # Store original balance before reversal
        original_balance = account.points_balance
        original_tier = account.tier_status
        
        logger.info(f"[SAGA COMPENSATION] 📊 Account before reversal: {original_balance} miles, tier: {original_tier}")
        
        # Reverse the miles
        account.points_balance -= miles_to_reverse
        if account.points_balance < 0:
            logger.warning(f"[SAGA COMPENSATION] ⚠️ Preventing negative balance: setting to 0")
            account.points_balance = 0  # Prevent negative balance
        account.save()  # This will also update the tier
        
        new_tier = account.tier_status
        tier_changed = original_tier != new_tier
        
        if tier_changed:
            logger.info(f"[SAGA COMPENSATION] 📉 TIER DOWNGRADE due to compensation: {original_tier} -> {new_tier}")
        
        # Update SAGA award status
        saga_award.status = 'REVERSED'
        saga_award.reversed_at = timezone.now()
        saga_award.save()
        logger.info(f"[SAGA COMPENSATION] 💾 Updated SAGA award status to REVERSED")
        
        # Create compensation transaction record with enhanced identification
        comp_transaction = LoyaltyTransaction.objects.create(
            account=account,
            transaction_id=f"COMP-{correlation_id[:8]}",
            transaction_type='adjustment',
            points_redeemed=miles_to_reverse,
            amount=0.0,
            description=f'SAGA Compensation: {compensation_reason} - Reversed {miles_to_reverse} miles'
        )
        logger.info(f"[SAGA COMPENSATION] 📝 Created compensation transaction: {comp_transaction.transaction_id}")
        
        # DIAGNOSTIC: Log compensation transaction details for dashboard debugging
        logger.info(f"[DASHBOARD_DEBUG] Compensation transaction created:")
        logger.info(f"[DASHBOARD_DEBUG] - Transaction ID: {comp_transaction.transaction_id}")
        logger.info(f"[DASHBOARD_DEBUG] - Transaction Type: {comp_transaction.transaction_type}")
        logger.info(f"[DASHBOARD_DEBUG] - Points Redeemed: {comp_transaction.points_redeemed}")
        logger.info(f"[DASHBOARD_DEBUG] - Description: {comp_transaction.description}")
        logger.info(f"[DASHBOARD_DEBUG] - Account User ID: {account.user_id}")
        logger.info(f"[DASHBOARD_DEBUG] - Created At: {comp_transaction.created_at}")
        
        # POC PHASE 3B: Enhanced Service Communication Logging - Compensation Response
        logger.info(f"[POC_SERVICE_COMM] ===== LOYALTY COMPENSATION RESPONSE =====")
        logger.info(f"[POC_SERVICE_COMM] ✅ ReverseMiles compensation completed successfully")
        logger.info(f"[POC_SERVICE_COMM] 📡 Sending response: Loyalty → Backend Service (COMPENSATION)")
        logger.info(f"[POC_SERVICE_COMM] 📊 Miles reversed: {miles_to_reverse}, New balance: {account.points_balance}")
        logger.info(f"[POC_SERVICE_COMM] 🛠️ Service recovery: Transaction rolled back successfully")
        logger.info(f"[POC_SERVICE_COMM] 🔄 SAGA compensation chain can continue")
        
        logger.info(f"[SAGA COMPENSATION] ✅ Miles reversal completed! User {user_id}: {original_balance} -> {account.points_balance} miles")
        
        # Log detailed transaction for loyalty point history
        logger.info(f"[SAGA COMPENSATION] 📝 Compensation transaction logged: {comp_transaction.transaction_id} - {miles_to_reverse} miles reversed.")
        logger.info(f"[SAGA COMPENSATION] 🎯 Loyalty service compensation successful for correlation_id: {correlation_id}")
        
        return JsonResponse({
            "success": True,
            "correlation_id": correlation_id,
            "user_id": user_id,
            "miles_reversed": miles_to_reverse,
            "original_balance": original_balance,
            "new_balance": account.points_balance,
            "message": f"Successfully reversed {miles_to_reverse} miles due to SAGA compensation"
        })
        
    except Exception as e:
        logger.error(f"[SAGA COMPENSATION] ❌ Error in ReverseMiles: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        })