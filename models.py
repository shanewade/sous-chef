from datetime import datetime
from app import db

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    ingredients = db.Column(db.Text)
    steps = db.Column(db.Text)
    cook_time_minutes = db.Column(db.Integer)
    servings = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
