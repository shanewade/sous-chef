from datetime import date, timedelta
from flask import Blueprint, render_template, abort
from extensions import db
from models import MealPlan, Recipe

views = Blueprint("views", __name__)


@views.route("/recipes")
def recipes_index():
    recipes = Recipe.query.all()
    return render_template("recipes/index.html", recipes=recipes)


@views.route("/recipes/new")
def recipes_new():
    return render_template("recipes/new.html")


@views.route("/recipes/<int:id>")
def recipes_detail(id):
    recipe = db.session.get(Recipe, id)
    if recipe is None:
        abort(404)
    return render_template("recipes/detail.html", recipe=recipe)


@views.route("/meal-plan")
def meal_plan():
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    plan = MealPlan.query.filter_by(week_start_date=monday).first()
    if plan is None:
        plan = MealPlan(
            name=f"Week of {monday.strftime('%b')} {monday.day}",
            week_start_date=monday,
        )
        db.session.add(plan)
        db.session.commit()

    slots = {(e.day_of_week, e.meal_type): e for e in plan.entries}
    return render_template("meal_plan/index.html", plan=plan, slots=slots)
