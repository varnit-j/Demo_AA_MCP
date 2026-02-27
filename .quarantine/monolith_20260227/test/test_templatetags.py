"""
Tests for flight.templatetags.currency_filters
Coverage target: 100% of templatetags module
"""
import pytest
from decimal import Decimal


# Import the filters directly (not through Django template engine)
from flight.templatetags.currency_filters import (
    inr_to_usd,
    format_usd,
    format_inr,
    format_inr_decimal,
    format_usd_from_inr,
    mul,
    INR_TO_USD_RATE,
)


class TestInrToUsd:
    def test_normal_conversion(self):
        result = inr_to_usd(825)
        assert result == round(825 / INR_TO_USD_RATE, 2)

    def test_zero_returns_zero(self):
        assert inr_to_usd(0) == 0

    def test_none_returns_zero(self):
        assert inr_to_usd(None) == 0

    def test_string_numeric(self):
        result = inr_to_usd("165")
        assert isinstance(result, float)

    def test_invalid_string_returns_zero(self):
        assert inr_to_usd("abc") == 0

    def test_decimal_input(self):
        result = inr_to_usd(Decimal("82.5"))
        assert result == round(82.5 / INR_TO_USD_RATE, 2)


class TestFormatUsd:
    def test_normal_value(self):
        assert format_usd(10.5) == "10.50"

    def test_integer(self):
        assert format_usd(100) == "100.00"

    def test_none_returns_default(self):
        assert format_usd(None) == "0.00"

    def test_string_numeric(self):
        assert format_usd("25.5") == "25.50"

    def test_invalid_string(self):
        assert format_usd("bad") == "0.00"

    def test_zero(self):
        assert format_usd(0) == "0.00"


class TestFormatInr:
    def test_normal_value(self):
        result = format_inr(1000)
        assert result == "₹1,000"

    def test_none_returns_default(self):
        assert format_inr(None) == "₹0"

    def test_invalid_string(self):
        assert format_inr("bad") == "₹0"

    def test_decimal_rounds_down(self):
        result = format_inr(1000.99)
        assert "₹" in result

    def test_zero(self):
        assert format_inr(0) == "₹0"


class TestFormatInrDecimal:
    def test_normal_value(self):
        result = format_inr_decimal(1000)
        assert result == "₹1,000.00"

    def test_none_returns_default(self):
        assert format_inr_decimal(None) == "₹0.00"

    def test_invalid_string(self):
        assert format_inr_decimal("bad") == "₹0.00"

    def test_float_input(self):
        result = format_inr_decimal(1500.5)
        assert "₹" in result and "1,500.50" in result


class TestFormatUsdFromInr:
    def test_normal_conversion(self):
        result = format_usd_from_inr(825)
        assert result.startswith("$")
        assert "10" in result  # 825/82.5 = 10

    def test_none_returns_default(self):
        assert format_usd_from_inr(None) == "$0.00"

    def test_invalid_string(self):
        assert format_usd_from_inr("bad") == "$0.00"

    def test_zero(self):
        result = format_usd_from_inr(0)
        assert result == "$0.00"


class TestMul:
    def test_integer_multiplication(self):
        assert mul(5, 3) == 15.0

    def test_float_multiplication(self):
        assert abs(mul(2.5, 4) - 10.0) < 0.001

    def test_string_numbers(self):
        assert mul("3", "4") == 12.0

    def test_invalid_returns_zero(self):
        assert mul("bad", 2) == 0

    def test_zero_multiplier(self):
        assert mul(100, 0) == 0.0
