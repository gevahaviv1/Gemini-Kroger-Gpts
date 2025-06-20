import os
import logging
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from .models import db
from .routes.products import products_bp
from .routes.cart import cart_bp

scheduler = BackgroundScheduler()

logger = logging.getLogger(__name__)

# Interval for polling watched products
POLL_INTERVAL_MINUTES = 10


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kroger.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = 1800
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_COOKIE_SECURE"] = False  # Should be True in production
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Defaults to "dev_secret_key" if not found (secure for dev, not for prod!).
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")
    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)

    scheduler.add_job(
        func=lambda: monitor_watched_products(app),
        trigger="interval",
        minutes=POLL_INTERVAL_MINUTES,
        id="kroger_watchlist_job",
        replace_existing=True,
    )

    return app
