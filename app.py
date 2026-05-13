import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///recipe_app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

@app.cli.command("db-init")
def db_init():
    import models
    db.create_all()
    click.echo("Database tables created.")

@app.route("/")
def index():
    return "<h1>Hello World</h1>"

if __name__ == "__main__":
    app.run(debug=True, port=5001)
