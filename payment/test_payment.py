import sys
from unittest.mock import MagicMock

# Block side-effectful imports before loading payment module
sys.modules['instana'] = MagicMock()
sys.modules['rabbitmq'] = MagicMock()

import pytest
from unittest.mock import patch
from payment import app, countItems


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# countItems
# ---------------------------------------------------------------------------

def test_countItems_empty_list():
    assert countItems([]) == 0


def test_countItems_skips_SHIP_item():
    items = [{'sku': 'SHIP', 'qty': 1}]
    assert countItems(items) == 0


def test_countItems_multiple_items_excludes_SHIP():
    items = [
        {'sku': 'SKU001', 'qty': 2},
        {'sku': 'SKU002', 'qty': 3},
        {'sku': 'SHIP',   'qty': 1},
    ]
    assert countItems(items) == 5


# ---------------------------------------------------------------------------
# HTTP endpoints
# ---------------------------------------------------------------------------

def test_health_returns_ok(client):
    res = client.get('/health')
    assert res.status_code == 200
    assert res.data == b'OK'


def test_pay_invalid_cart_returns_400(client):
    # Cart with total=0 and no items → fails validation before any external call
    with patch('payment.requests.get') as mock_get:
        mock_get.return_value.status_code = 404  # user not found → anonymous
        res = client.post(
            '/pay/anonymous-1',
            json={'total': 0, 'items': []},
            content_type='application/json',
        )
    assert res.status_code == 400
