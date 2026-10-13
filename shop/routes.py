import re

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from .db import get_db

bp = Blueprint("shop", __name__)

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def get_product_or_404(product_id):
    product = get_db().execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        abort(404)
    return product


def cart_items():
    """Return ([{product, quantity, subtotal}], total) for the session cart."""
    cart = session.get("cart", {})
    if not cart:
        return [], 0
    ids = list(cart)
    placeholders = ",".join("?" * len(ids))
    rows = get_db().execute(f"SELECT * FROM products WHERE id IN ({placeholders})", ids).fetchall()

    items, total = [], 0
    for product in rows:
        quantity = cart[str(product["id"])]
        subtotal = quantity * product["price"]
        total += subtotal
        items.append({"product": product, "quantity": quantity, "subtotal": subtotal})
    return items, total


def set_cart_quantity(product, quantity):
    cart = session.get("cart", {})
    key = str(product["id"])
    if quantity <= 0:
        cart.pop(key, None)
    else:
        cart[key] = min(quantity, product["stock"])
    session["cart"] = cart


@bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "")

    sql = "SELECT * FROM products WHERE 1 = 1"
    params = []
    if q:
        sql += " AND (name LIKE ? OR description LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if category:
        sql += " AND category = ?"
        params.append(category)

    db = get_db()
    products = db.execute(sql + " ORDER BY name", params).fetchall()
    categories = [row["category"] for row in db.execute("SELECT DISTINCT category FROM products ORDER BY category")]
    return render_template("index.html", products=products, categories=categories, q=q, category=category)


@bp.route("/product/<int:product_id>")
def product(product_id):
    return render_template("product.html", product=get_product_or_404(product_id))


@bp.post("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    product = get_product_or_404(product_id)
    if product["stock"] <= 0:
        flash(f"Sorry, {product['name']} is out of stock.", "error")
        return redirect(url_for("shop.product", product_id=product_id))

    quantity = max(1, request.form.get("quantity", 1, type=int))
    current = session.get("cart", {}).get(str(product_id), 0)
    set_cart_quantity(product, current + quantity)
    flash(f"Added {product['name']} to your cart.", "success")
    return redirect(url_for("shop.cart"))


@bp.post("/cart/update/<int:product_id>")
def update_cart(product_id):
    product = get_product_or_404(product_id)
    set_cart_quantity(product, request.form.get("quantity", 0, type=int))
    return redirect(url_for("shop.cart"))


@bp.post("/cart/remove/<int:product_id>")
def remove_from_cart(product_id):
    set_cart_quantity(get_product_or_404(product_id), 0)
    return redirect(url_for("shop.cart"))


@bp.route("/cart")
def cart():
    items, total = cart_items()
    return render_template("cart.html", items=items, total=total)


@bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, total = cart_items()
    if not items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("shop.index"))

    form = {"name": "", "email": "", "address": ""}
    if request.method == "POST":
        form = {key: request.form.get(key, "").strip() for key in form}
        errors = []
        if len(form["name"]) < 2:
            errors.append("Please enter your name.")
        if not EMAIL_RE.match(form["email"]):
            errors.append("Please enter a valid email address.")
        if len(form["address"]) < 5:
            errors.append("Please enter your delivery address.")
        for item in items:
            if item["quantity"] > item["product"]["stock"]:
                errors.append(f"Only {item['product']['stock']} of {item['product']['name']} left in stock.")

        if errors:
            for error in errors:
                flash(error, "error")
        else:
            db = get_db()
            cur = db.execute(
                "INSERT INTO orders (customer_name, email, address, total) VALUES (?, ?, ?, ?)",
                (form["name"], form["email"], form["address"], total),
            )
            order_id = cur.lastrowid
            for item in items:
                product = item["product"]
                db.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                    (order_id, product["id"], item["quantity"], product["price"]),
                )
                db.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (item["quantity"], product["id"]))
            db.commit()

            session["cart"] = {}
            session["orders"] = session.get("orders", []) + [order_id]
            return redirect(url_for("shop.order", order_id=order_id))

    return render_template("checkout.html", items=items, total=total, form=form)


@bp.route("/order/<int:order_id>")
def order(order_id):
    # Customers can only see orders placed from their own session.
    if order_id not in session.get("orders", []):
        abort(404)
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    items = db.execute(
        """SELECT oi.quantity, oi.price, p.name, p.emoji
           FROM order_items oi JOIN products p ON p.id = oi.product_id
           WHERE oi.order_id = ?""",
        (order_id,),
    ).fetchall()
    return render_template("order.html", order=order, items=items)
