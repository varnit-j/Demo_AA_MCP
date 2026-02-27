"""
Constants for the flight booking application
"""

# Fee and surcharge constants
FEE = 50.0  # Base booking fee
TAX_RATE = 0.18  # 18% GST
SERVICE_CHARGE = 25.0  # Service charge

# Flight class multipliers
CLASS_MULTIPLIERS = {
    'economy': 1.0,
    'business': 2.5,
    'first': 4.0
}

# Coupon discount rates
COUPON_DISCOUNTS = {
    'SAVE10': 0.10,
    'SAVE20': 0.20,
    'FIRSTFLIGHT': 0.15,
    'STUDENT': 0.25
}

# Maximum discount percentage
MAX_DISCOUNT = 0.30

# Points conversion rate (1 point = $0.01)
POINTS_TO_CURRENCY = 0.01

# Cancellation charges (percentage of fare)
CANCELLATION_CHARGES = {
    'economy': 0.10,
    'business': 0.15,
    'first': 0.20
}