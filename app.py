from kroger_app import create_app, scheduler
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

app = create_app()

if __name__ == "__main__":
    from werkzeug.serving import is_running_from_reloader

    if not is_running_from_reloader():
        scheduler.start()
    app.run(debug=True, host="127.0.0.1", port=5000)
