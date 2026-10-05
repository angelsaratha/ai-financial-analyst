"""
Unit tests for the pure-Python calculation tool — no API key needed to run these.
    python -m pytest tests/test_calc_tool.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools.calc_tool import (
    growth_rate, profit_margin, cagr, debt_ratio, current_ratio, roi,
)


def test_growth_rate():
    assert growth_rate(100, 110) == 10.0
    assert growth_rate(12_400_000, 13_100_000) == 5.65


def test_profit_margin():
    assert profit_margin(13_100_000, 1_700_000) == 12.98


def test_cagr():
    assert cagr(100, 200, 5) == 14.87


def test_debt_ratio():
    assert debt_ratio(8_000_000, 19_100_000) == 0.419


def test_current_ratio():
    assert current_ratio(19_100_000, 8_000_000) == 2.388


def test_roi():
    assert roi(150, 100) == 50.0


def test_zero_division_raises():
    import pytest
    with pytest.raises(ValueError):
        growth_rate(0, 100)
