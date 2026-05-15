from flask import Blueprint, render_template, abort
from models import Recipe

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
    recipe = Recipe.query.get_or_404(id)
    return render_template("recipes/detail.html", recipe=recipe)
