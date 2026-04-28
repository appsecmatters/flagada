from flask import Flask

from db import close_db, init_db
from routes.flags import bp as flags_bp
from routes.validate_flag import bp as validate_bp

init_db()

app = Flask(__name__)
app.teardown_appcontext(close_db)
app.register_blueprint(flags_bp)
app.register_blueprint(validate_bp)

if __name__ == "__main__":
    app.run(debug=True)
