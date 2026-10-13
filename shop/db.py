import sqlite3

import click
from flask import current_app, g

SCHEMA = """
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price INTEGER NOT NULL,          -- whole taka
    stock INTEGER NOT NULL DEFAULT 0,
    description TEXT NOT NULL DEFAULT '',
    emoji TEXT NOT NULL DEFAULT '📦'
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    email TEXT NOT NULL,
    address TEXT NOT NULL,
    total INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders (id),
    product_id INTEGER NOT NULL REFERENCES products (id),
    quantity INTEGER NOT NULL,
    price INTEGER NOT NULL
);
"""

SAMPLE_PRODUCTS = [
    ("Wireless Headphones", "Electronics", 3500, 15, "Over-ear Bluetooth headphones with 30-hour battery life.", "🎧"),
    ("Smart Watch", "Electronics", 5200, 8, "Fitness tracking, heart-rate monitor and notifications.", "⌚"),
    ("Mechanical Keyboard", "Electronics", 4800, 10, "RGB backlit keyboard with tactile switches.", "⌨️"),
    ("Cotton T-Shirt", "Clothing", 650, 40, "Soft 100% cotton crew-neck t-shirt.", "👕"),
    ("Denim Jeans", "Clothing", 1800, 25, "Slim-fit stretch denim jeans.", "👖"),
    ("Running Shoes", "Clothing", 3200, 12, "Lightweight, breathable running shoes.", "👟"),
    ("Coffee Mug", "Home", 350, 50, "Ceramic mug, 350 ml, dishwasher safe.", "☕"),
    ("Desk Lamp", "Home", 1500, 18, "LED desk lamp with adjustable brightness.", "💡"),
    ("Python Crash Course", "Books", 1200, 20, "A hands-on, project-based introduction to programming.", "📘"),
    ("Clean Code", "Books", 1400, 0, "A handbook of agile software craftsmanship.", "📗"),
]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    db.executemany(
        "INSERT INTO products (name, category, price, stock, description, emoji) VALUES (?, ?, ?, ?, ?, ?)",
        SAMPLE_PRODUCTS,
    )
    db.commit()


@click.command("init-db")
def init_db_command():
    """Drop all data and recreate the tables with sample products."""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
