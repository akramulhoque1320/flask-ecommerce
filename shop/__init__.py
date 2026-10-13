import os

from flask import Flask, session

from . import db, routes


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-me"),
        DATABASE=os.path.join(app.instance_path, "shop.sqlite"),
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    # Create and seed the database on first run.
    if not os.path.exists(app.config["DATABASE"]):
        with app.app_context():
            db.init_db()

    app.register_blueprint(routes.bp)

    @app.template_filter("taka")
    def taka(amount):
        return f"৳{amount:,}"

    @app.context_processor
    def inject_cart_count():
        return {"cart_count": sum(session.get("cart", {}).values())}

    return app
