import os
import logging
from flask import Flask, session
from apscheduler.schedulers.background import BackgroundScheduler

from .models import db
from .services.kroger_api import (
    fetch_products,
    get_access_token,
    fetch_nearest_location,
)
from .utils import save_token, get_saved_token
from .routes.products import products_bp, monitor_watched_products
from .routes.cart import cart_bp

scheduler = BackgroundScheduler()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Interval for polling watched products
POLL_INTERVAL_MINUTES = 10


def create_app():
    global app
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kroger.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Defaults to "dev_secret_key" if not found (secure for dev, not for prod!).
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = 1800
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_COOKIE_SECURE"] = False  # Should be True in production
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
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
