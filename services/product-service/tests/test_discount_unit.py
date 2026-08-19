"""
Unit tests for product-service's app/main.py::get_active_discount.

This targets the real bug found and fixed during this project:
"TypeError: can't compare offset-naive and offset-aware datetimes", which
crashed the entire product listing page once the frontend started sending
correctly UTC-formatted ('Z'-suffixed) promotion timestamps. These tests
exist so that specific bug class can never silently regress.

No DynamoDB, no network — the Promotions table is mocked.

Place this file at services/product-service/tests/test_discount_unit.py and
run from services/product-service/: pytest tests/test_discount_unit.py -v
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _mock_table(item):
    table = MagicMock()
    table.get_item.return_value = {"Item": item} if item else {}
    return table


def test_no_promotion_on_record_returns_none():
    from app.main import get_active_discount

    with patch("app.main.get_promotions_table", return_value=_mock_table(None)):
        assert get_active_discount("prod-1") is None


def test_active_promotion_with_naive_timestamps_returns_the_discount():
    """The original working case: both start/end stored without timezone info."""
    from app.main import get_active_discount

    now = datetime.utcnow()
    item = {
        "product_id": "prod-1",
        "start_time": (now - timedelta(hours=1)).isoformat(),
        "end_time": (now + timedelta(hours=1)).isoformat(),
        "discount_percentage": "20",
    }
    with patch("app.main.get_promotions_table", return_value=_mock_table(item)):
        assert get_active_discount("prod-1") == 20.0


def test_active_promotion_with_utc_z_suffix_does_not_crash():
    """Regression test for the real production bug: once the frontend
    started sending timezone-aware timestamps, comparing them against a
    naive datetime.utcnow() crashed list_products for every product on the
    page, not just the one with the new-format promotion. Must return the
    discount cleanly here, not raise TypeError."""
    from app.main import get_active_discount

    now = datetime.now(timezone.utc)
    item = {
        "product_id": "prod-1",
        "start_time": (now - timedelta(hours=1)).isoformat(),  # timezone-aware
        "end_time": (now + timedelta(hours=1)).isoformat(),    # timezone-aware
        "discount_percentage": "15",
    }
    with patch("app.main.get_promotions_table", return_value=_mock_table(item)):
        assert get_active_discount("prod-1") == 15.0


def test_mixed_naive_and_aware_boundary_does_not_crash():
    """Edge case beyond what was manually tested during development: a
    promotion created before the frontend fix (naive start_time) and edited
    after it (aware end_time). Must still normalize cleanly rather than
    assume both fields match."""
    from app.main import get_active_discount

    now_naive = datetime.utcnow()
    now_aware = datetime.now(timezone.utc)
    item = {
        "product_id": "prod-1",
        "start_time": (now_naive - timedelta(hours=1)).isoformat(),  # naive
        "end_time": (now_aware + timedelta(hours=1)).isoformat(),    # aware
        "discount_percentage": "10",
    }
    with patch("app.main.get_promotions_table", return_value=_mock_table(item)):
        assert get_active_discount("prod-1") == 10.0


def test_promotion_not_yet_started_returns_none():
    from app.main import get_active_discount

    now = datetime.utcnow()
    item = {
        "product_id": "prod-1",
        "start_time": (now + timedelta(hours=1)).isoformat(),
        "end_time": (now + timedelta(hours=2)).isoformat(),
        "discount_percentage": "20",
    }
    with patch("app.main.get_promotions_table", return_value=_mock_table(item)):
        assert get_active_discount("prod-1") is None


def test_expired_promotion_returns_none():
    from app.main import get_active_discount

    now = datetime.utcnow()
    item = {
        "product_id": "prod-1",
        "start_time": (now - timedelta(hours=2)).isoformat(),
        "end_time": (now - timedelta(hours=1)).isoformat(),
        "discount_percentage": "20",
    }
    with patch("app.main.get_promotions_table", return_value=_mock_table(item)):
        assert get_active_discount("prod-1") is None
