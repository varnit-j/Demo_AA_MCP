from django import template
from decimal import Decimal

register = template.Library()

# Exchange rate: 1 USD = 82.5 INR (updated rate as of 2026)
INR_TO_USD_RATE = 82.5

@register.filter
def inr_to_usd(value):
    """Convert INR amount to USD"""
    if value is None or value == 0:
        return 0
    try:
        inr_amount = float(value)
        usd_amount = inr_amount / INR_TO_USD_RATE
        return round(usd_amount, 2)
    except (ValueError, TypeError):
        return 0

@register.filter
def format_usd(value):
    """Format USD amount with proper decimal places"""
    if value is None:
        return "0.00"
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return "0.00"

@register.filter
def format_inr(value):
    """Format INR amount with proper formatting"""
    if value is None:
        return "₹0"
    try:
        amount = float(value)
        return f"₹{amount:,.0f}"
    except (ValueError, TypeError):
        return "₹0"

@register.filter
def format_inr_decimal(value):
    """Format INR amount with decimal places"""
    if value is None:
        return "₹0.00"
    try:
        amount = float(value)
        return f"₹{amount:,.2f}"
    except (ValueError, TypeError):
        return "₹0.00"

@register.filter
def format_usd_from_inr(value):
    """Convert INR to USD and format with USD symbol"""
    if value is None:
        return "$0.00"
    try:
        inr_amount = float(value)
        usd_amount = inr_amount / INR_TO_USD_RATE
        return f"${usd_amount:,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

@register.filter
def mul(value, arg):
    """Multiply value by argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0