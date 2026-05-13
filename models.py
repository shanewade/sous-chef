from datetime import datetime
from app import db

recipe_ingredients = db.Table(
    "recipe_ingredients",
    db.Column("recipe_id", db.Integer, db.ForeignKey("recipe.id"), primary_key=True),
    db.Column("ingredient_id", db.Integer, db.ForeignKey("ingredient.id"), primary_key=True),
    db.Column("quantity", db.String(100)),
)

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    unit = db.Column(db.String(50))

    def __repr__(self):
        return f"<Ingredient {self.name}>"

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    ingredients = db.Column(db.Text)
    steps = db.Column(db.Text)
    cook_time_minutes = db.Column(db.Integer)
    servings = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ingredient_list = db.relationship("Ingredient", secondary=recipe_ingredients, backref="recipes")

    def __repr__(self):
        return f"<Recipe {self.title}>"

class MealPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    week_start_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    entries = db.relationship("MealPlanEntry", backref="meal_plan", lazy=True)

class MealPlanEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meal_plan_id = db.Column(db.Integer, db.ForeignKey("meal_plan.id"), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    day_of_week = db.Column(db.String(10))
    meal_type = db.Column(db.String(50))
