import os

from flask import Flask, send_from_directory

from db import close_db, init_db
from routes.applications import bp as applications_bp
from routes.flags import bp as flags_bp
from routes.validate_flag import bp as validate_bp

init_db()

app = Flask(__name__)
app.teardown_appcontext(close_db)
app.register_blueprint(applications_bp)
app.register_blueprint(flags_bp)
app.register_blueprint(validate_bp)

_DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")


@app.get("/docs")
def serve_docs():
    return send_from_directory(_DOCS_DIR, "index.html")


if __name__ == "__main__":
    app.run(debug=True)
