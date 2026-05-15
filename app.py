from flask import Flask
from extensions import db, migrate

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///recipe_app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate.init_app(app, db)

import models  # noqa: E402 — must come after db is initialized

from routes.api import api  # noqa: E402
from routes.views import views  # noqa: E402
from routes.meal_plan_api import meal_plan_bp  # noqa: E402
app.register_blueprint(api, url_prefix="/api")
app.register_blueprint(meal_plan_bp, url_prefix="/api")
app.register_blueprint(views)

@app.route("/")
def index():
    return "<h1>Hello World</h1>"

if __name__ == "__main__":
    app.run(debug=True, port=5001)
