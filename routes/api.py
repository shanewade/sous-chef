from flask import Blueprint, jsonify, request
from extensions import db
from models import Recipe

api = Blueprint("api", __name__)


@api.route("/recipes", methods=["GET"])
def get_recipes():
    recipes = Recipe.query.all()
    return jsonify([
        {
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "cook_time_minutes": r.cook_time_minutes,
            "servings": r.servings,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in recipes
    ])


@api.route("/recipes", methods=["POST"])
def create_recipe():
    data = request.get_json(silent=True) or {}

    if not data.get("title"):
        return jsonify({"error": "title is required"}), 400

    recipe = Recipe(
        title=data["title"],
        description=data.get("description"),
        cook_time_minutes=data.get("cook_time_minutes"),
        servings=data.get("servings"),
    )
    db.session.add(recipe)
    db.session.commit()

    return jsonify({
        "id": recipe.id,
        "title": recipe.title,
        "description": recipe.description,
        "cook_time_minutes": recipe.cook_time_minutes,
        "servings": recipe.servings,
        "created_at": recipe.created_at.isoformat() if recipe.created_at else None,
    }), 201
