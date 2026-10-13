import pytest

from shop import create_app
from shop.db import get_db


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite"), "SECRET_KEY": "test"})


@pytest.fixture
def client(app):
    return app.test_client()


def stock_of(app, product_id):
    with app.app_context():
        return get_db().execute("SELECT stock FROM products WHERE id = ?", (product_id,)).fetchone()["stock"]


def test_index_lists_products(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Wireless Headphones" in res.data


def test_search_and_category_filter(client):
    assert b"Smart Watch" not in client.get("/?q=headphones").data
    res = client.get("/?category=Books")
    assert b"Clean Code" in res.data and b"Coffee Mug" not in res.data


def test_product_page_and_404(client):
    assert b"30-hour battery" in client.get("/product/1").data
    assert client.get("/product/999").status_code == 404


def test_add_update_remove_cart(client):
    client.post("/cart/add/1", data={"quantity": 2})
    res = client.get("/cart")
    assert "৳7,000".encode() in res.data

    client.post("/cart/update/1", data={"quantity": 1})
    assert "৳3,500".encode() in client.get("/cart").data

    client.post("/cart/remove/1")
    assert b"Your cart is empty" in client.get("/cart").data


def test_cart_quantity_capped_at_stock(client):
    client.post("/cart/add/2", data={"quantity": 100})  # Smart Watch, 8 in stock
    with client.session_transaction() as sess:
        assert sess["cart"]["2"] == 8


def test_out_of_stock_cannot_be_added(client):
    client.post("/cart/add/10")  # Clean Code has 0 stock
    with client.session_transaction() as sess:
        assert "10" not in sess.get("cart", {})


def test_checkout_requires_items(client):
    res = client.get("/checkout")
    assert res.status_code == 302


def test_checkout_validation(client):
    client.post("/cart/add/1")
    res = client.post("/checkout", data={"name": "A", "email": "bad", "address": ""})
    assert b"valid email" in res.data


def test_checkout_places_order(app, client):
    client.post("/cart/add/1", data={"quantity": 2})
    client.post("/cart/add/7")
    res = client.post(
        "/checkout",
        data={"name": "Ahnaf", "email": "ahnaf@example.com", "address": "House 1, Uttara, Dhaka"},
    )
    assert res.status_code == 302
    order_page = client.get(res.headers["Location"])
    assert b"Thank you, Ahnaf" in order_page.data
    assert "৳7,350".encode() in order_page.data
    assert stock_of(app, 1) == 13
    with client.session_transaction() as sess:
        assert sess["cart"] == {}


def test_order_hidden_from_other_sessions(app, client):
    client.post("/cart/add/1")
    res = client.post("/checkout", data={"name": "Ahnaf", "email": "a@b.co", "address": "Dhaka 1230"})
    other = app.test_client()
    assert other.get(res.headers["Location"]).status_code == 404
