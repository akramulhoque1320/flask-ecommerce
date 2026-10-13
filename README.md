# Flask E-commerce Shop (ShopEase)

A small online shop built with **Python, Flask and SQLite**.

## Features

- Product catalogue with categories and search
- Product detail pages with stock levels
- Session-based shopping cart: add, update quantity, remove (capped at available stock)
- Checkout with form validation and cash on delivery
- Orders and order items saved to SQLite, with stock reduced on purchase
- Order confirmation page (visible only to the session that placed the order)
- Responsive UI, and prices shown in Bangladeshi taka (৳)
- Test suite with `pytest` and Flask's test client

## Getting started

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
flask --app shop run --debug
```

Open http://127.0.0.1:5000. The database is created with sample products on first run.
To reset it: `flask --app shop init-db`.

Set a real `SECRET_KEY` environment variable before deploying.

## Run the tests

```bash
pytest -v
```

## Project structure

```
shop/
  __init__.py     # app factory
  db.py           # SQLite connection, schema and sample data
  routes.py       # catalogue, cart, checkout and order views
  templates/      # Jinja2 templates
  static/         # CSS
tests/
  test_shop.py
```
