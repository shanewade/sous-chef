import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///recipe_app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

import models  # noqa: E402 — must come after db is defined

@app.route("/")
def index():
    return "<h1>Hello World</h1>"

if __name__ == "__main__":
    app.run(debug=True, port=5001)
