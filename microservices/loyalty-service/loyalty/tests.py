"""
Comprehensive tests for loyalty-service -- targets 95%+ coverage.

Covers:
  - loyalty.models  (LoyaltyAccount tier logic, miles_to_next_tier, save; LoyaltyTransaction; SagaMilesAward)
  - loyalty.views   (loyalty_status, add_transaction_points, get_transaction_history)
  - loyalty.saga_views   (award_miles - idempotent, simulate_failure, one-way, round-trip)
  - loyalty.saga_compensation  (reverse_miles - success, no record, insufficient balance)
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from .models import LoyaltyAccount, LoyaltyTransaction, SagaMilesAward


def make_account(user_id="U1", balance=0):
    account, _ = LoyaltyAccount.objects.get_or_create(user_id=user_id)
    account.points_balance = balance
    account.save()
    return LoyaltyAccount.objects.get(user_id=user_id)


# ===========================================================================
# MODEL TESTS
# ===========================================================================

class LoyaltyAccountTierTest(TestCase):
    def _tier(self, balance):
        a = LoyaltyAccount(user_id="T1", points_balance=balance)
        return a.calculate_tier()

    def test_regular(self):
        self.assertEqual(self._tier(0), "Regular")
        self.assertEqual(self._tier(1000), "Regular")

    def test_gold(self):
        self.assertEqual(self._tier(25000), "Gold")
        self.assertEqual(self._tier(40000), "Gold")

    def test_platinum(self):
        self.assertEqual(self._tier(50000), "Platinum")

    def test_platinum_pro(self):
        self.assertEqual(self._tier(75000), "Platinum Pro")

    def test_executive_platinum(self):
        self.assertEqual(self._tier(100000), "Executive Platinum")

    def test_concierge_key(self):
        self.assertEqual(self._tier(125000), "ConciergeKey")

    def test_save_updates_tier(self):
        a = LoyaltyAccount.objects.create(user_id="TSAVE", points_balance=50000)
        self.assertEqual(a.tier_status, "Platinum")

    def test_str(self):
        a = LoyaltyAccount(user_id="TSTR", points_balance=100, tier_status="Regular")
        self.assertIn("TSTR", str(a))
        self.assertIn("Regular", str(a))


class LoyaltyAccountMilesToNextTest(TestCase):
    def _miles(self, balance):
        a = LoyaltyAccount(user_id="M1", points_balance=balance)
        return a.miles_to_next_tier()

    def test_regular_band(self):
        self.assertEqual(self._miles(0), 25000)
        self.assertEqual(self._miles(10000), 15000)

    def test_gold_band(self):
        self.assertEqual(self._miles(25000), 25000)

    def test_platinum_band(self):
        self.assertEqual(self._miles(50000), 25000)

    def test_platinum_pro_band(self):
        self.assertEqual(self._miles(75000), 25000)

    def test_exec_plat_band(self):
        self.assertEqual(self._miles(100000), 25000)

    def test_concierge_key(self):
        self.assertEqual(self._miles(125000), 0)


class LoyaltyTransactionStrTest(TestCase):
    def test_earned_str(self):
        account = make_account("TRN1", 100)
        t = LoyaltyTransaction(account=account, transaction_id="T1",
                               transaction_type="flight_booking",
                               points_earned=50, amount=50.0,
                               description="Flight")
        self.assertIn("earned 50", str(t))

    def test_redeemed_str(self):
        account = make_account("TRN2", 100)
        t = LoyaltyTransaction(account=account, transaction_id="T2",
                               transaction_type="miles_redemption",
                               points_earned=0, points_redeemed=30,
                               description="Redemption")
        self.assertIn("redeemed 30", str(t))


class SagaMilesAwardStrTest(TestCase):
    def test_str(self):
        account = make_account("SMA1", 0)
        a = SagaMilesAward(correlation_id="C1", account=account,
                           miles_awarded=100, original_balance=0,
                           new_balance=100, status="AWARDED")
        self.assertIn("100 miles", str(a))


# ===========================================================================
# VIEWS TESTS
# ===========================================================================

class LoyaltyStatusViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_status_creates_account(self):
        r = self.client.get("/loyalty/status/?user_id=NEWUSER1")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["status"], "active")
        self.assertIn("points_balance", data)
        self.assertIn("user_tier", data)

    def test_status_existing_account(self):
        make_account("EXISTUSER", 500)
        r = self.client.get("/loyalty/status/?user_id=EXISTUSER")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["points_balance"], 500)

    def test_default_user_id(self):
        r = self.client.get("/loyalty/status/")
        self.assertEqual(r.status_code, 200)

    def test_miles_to_next_tier_in_response(self):
        make_account("TIER_U", 24000)
        r = self.client.get("/loyalty/status/?user_id=TIER_U")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["miles_to_next_tier"], 1000)


class AddTransactionPointsViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def _post(self, data):
        return self.client.post(
            "/loyalty/add-points/",
            data=json.dumps(data),
            content_type="application/json"
        )

    def test_adds_points(self):
        r = self._post({"user_id": "PAY_U1", "amount": 150.0, "transaction_id": "T_001"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["points_earned"], 150)

    def test_uses_one_to_one_ratio(self):
        r = self._post({"user_id": "PAY_U2", "amount": 75.9, "transaction_id": "T_002"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["points_earned"], 75)

    def test_creates_account_if_not_exists(self):
        r = self._post({"user_id": "NEW_PAY", "amount": 50.0})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(LoyaltyAccount.objects.filter(user_id="NEW_PAY").exists())

    def test_creates_transaction_record(self):
        self._post({"user_id": "TXN_U1", "amount": 100.0, "transaction_id": "T_003"})
        account = LoyaltyAccount.objects.get(user_id="TXN_U1")
        self.assertEqual(LoyaltyTransaction.objects.filter(account=account).count(), 1)

    def test_total_points_accumulated(self):
        self._post({"user_id": "ACC_U1", "amount": 100.0})
        self._post({"user_id": "ACC_U1", "amount": 200.0})
        account = LoyaltyAccount.objects.get(user_id="ACC_U1")
        self.assertEqual(account.points_balance, 300)


class GetTransactionHistoryViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.account = make_account("HIST_U1", 500)
        LoyaltyTransaction.objects.create(
            account=self.account, transaction_id="TH_001",
            transaction_type="flight_booking",
            points_earned=100, amount=100.0,
            description="Flight booking"
        )
        LoyaltyTransaction.objects.create(
            account=self.account, transaction_id="TH_002",
            transaction_type="miles_redemption",
            points_redeemed=50, points_value=0.5,
            description="Redemption"
        )

    def test_history_returned(self):
        r = self.client.get("/loyalty/transactions/HIST_U1/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["total_transactions"], 2)

    def test_creates_account_if_missing(self):
        r = self.client.get("/loyalty/transactions/NOHIST_U/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["total_transactions"], 0)

    def test_points_earned_transaction_format(self):
        r = self.client.get("/loyalty/transactions/HIST_U1/")
        txns = r.json()["transactions"]
        earned = [t for t in txns if "points_earned" in t]
        self.assertTrue(len(earned) >= 1)
        self.assertIn("amount", earned[0])

    def test_points_redeemed_transaction_format(self):
        r = self.client.get("/loyalty/transactions/HIST_U1/")
        txns = r.json()["transactions"]
        redeemed = [t for t in txns if "points_redeemed" in t]
        self.assertTrue(len(redeemed) >= 1)
        self.assertIn("points_value", redeemed[0])


# ===========================================================================
# SAGA VIEWS TESTS (award_miles)
# ===========================================================================

class AwardMilesViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("award_miles")
        self.user_id = "AW_U1"
        self.correlation_id = "AW_CID_001"

    def _post(self, data):
        return self.client.post(self.url, json.dumps(data), content_type="application/json")

    def test_award_miles_one_way(self):
        r = self._post({
            "correlation_id": self.correlation_id,
            "booking_data": {"user_id": self.user_id, "flight_fare": 300.0}
        })
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["success"])
        self.assertGreater(data["miles_awarded"], 0)
        self.assertEqual(SagaMilesAward.objects.filter(correlation_id=self.correlation_id).count(), 1)
        acct = LoyaltyAccount.objects.get(user_id=self.user_id)
        self.assertGreater(acct.points_balance, 0)

    def test_award_miles_simulate_failure(self):
        r = self._post({
            "correlation_id": "AW_CID_FAIL",
            "booking_data": {"user_id": self.user_id, "flight_fare": 300.0},
            "simulate_failure": True
        })
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertFalse(data["success"])
        self.assertIn("error", data)

    def test_award_miles_idempotent(self):
        self._post({
            "correlation_id": "AW_IDEM_001",
            "booking_data": {"user_id": "IDEM_U", "flight_fare": 200.0}
        })
        r2 = self._post({
            "correlation_id": "AW_IDEM_001",
            "booking_data": {"user_id": "IDEM_U", "flight_fare": 200.0}
        })
        self.assertEqual(r2.status_code, 200)
        data = r2.json()
        self.assertTrue(data["success"])
        self.assertEqual(SagaMilesAward.objects.filter(correlation_id="AW_IDEM_001").count(), 1)
        acct = LoyaltyAccount.objects.get(user_id="IDEM_U")
        expected = int(200.0 * 0.5)
        self.assertEqual(acct.points_balance, expected)

    def test_award_miles_round_trip(self):
        r = self._post({
            "correlation_id": "AW_RT_001",
            "booking_data": {
                "user_id": "RT_U1",
                "flight_fare": 250.0,
                "flight_fare_2": 250.0
            }
        })
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["success"])
        self.assertTrue(data.get("is_round_trip"))
        self.assertIn("flight1_miles", data)
        self.assertIn("flight2_miles", data)
        self.assertEqual(SagaMilesAward.objects.filter(correlation_id="AW_RT_001").count(), 2)

    def test_award_miles_fallback_fare(self):
        r = self._post({
            "correlation_id": "AW_FALL_001",
            "booking_data": {
                "user_id": "FALL_U1",
                "flight_fare": 0,
                "flight": {"economy_fare": 400}
            }
        })
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["success"])

    def test_creates_loyalty_transaction(self):
        self._post({
            "correlation_id": "AW_TXN_001",
            "booking_data": {"user_id": "TXN_AW_U", "flight_fare": 200.0}
        })
        acct = LoyaltyAccount.objects.get(user_id="TXN_AW_U")
        self.assertEqual(LoyaltyTransaction.objects.filter(account=acct).count(), 1)


# ===========================================================================
# SAGA COMPENSATION TESTS (reverse_miles)
# ===========================================================================

class ReverseMilesViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("reverse_miles")

    def _post(self, data):
        return self.client.post(self.url, json.dumps(data), content_type="application/json")

    def _create_award(self, cid, balance=500, awarded=200, user_id="REV_U1"):
        account = make_account(user_id, balance)
        return SagaMilesAward.objects.create(
            correlation_id=cid,
            account=account,
            miles_awarded=awarded,
            original_balance=balance - awarded,
            new_balance=balance,
            status="AWARDED"
        )

    def test_reverse_success(self):
        self._create_award("REV_CID_001")
        r = self._post({"correlation_id": "REV_CID_001"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["miles_reversed"], 200)
        award = SagaMilesAward.objects.get(correlation_id="REV_CID_001")
        self.assertEqual(award.status, "REVERSED")
        acct = LoyaltyAccount.objects.get(user_id="REV_U1")
        self.assertEqual(acct.points_balance, 300)

    def test_reverse_no_award_record(self):
        r = self._post({"correlation_id": "REV_NO_RECORD"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["success"])
        # Actual message from saga_views: "No miles award found to reverse - compensation complete"
        self.assertIn("No miles", data["message"])

    def test_reverse_insufficient_balance(self):
        account = make_account("REV_LOW_U", balance=50)
        SagaMilesAward.objects.create(
            correlation_id="REV_LOW_CID",
            account=account,
            miles_awarded=200,
            original_balance=0,
            new_balance=200,
            status="AWARDED"
        )
        r = self._post({"correlation_id": "REV_LOW_CID"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["success"])
        # The handler reverses the full awarded amount (200) regardless of current balance;
        # balance is floored at 0 (50 -> 0), miles_reversed == 200
        self.assertEqual(data["miles_reversed"], 200)
        acct = LoyaltyAccount.objects.get(user_id="REV_LOW_U")
        self.assertEqual(acct.points_balance, 0)

    def test_reverse_creates_compensation_transaction(self):
        self._create_award("REV_TXN_001", user_id="REV_TXN_U", awarded=100, balance=100)
        self._post({"correlation_id": "REV_TXN_001"})
        acct = LoyaltyAccount.objects.get(user_id="REV_TXN_U")
        comp_txns = LoyaltyTransaction.objects.filter(account=acct, transaction_type="adjustment")
        self.assertEqual(comp_txns.count(), 1)
        self.assertIn("COMP", comp_txns.first().transaction_id)

    def test_reverse_updates_reversed_at_timestamp(self):
        self._create_award("REV_TS_001", user_id="REV_TS_U")
        self._post({"correlation_id": "REV_TS_001"})
        award = SagaMilesAward.objects.get(correlation_id="REV_TS_001")
        self.assertIsNotNone(award.reversed_at)
