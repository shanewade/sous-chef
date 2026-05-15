from flask import Blueprint, jsonify, request
from extensions import db
from models import Recipe

api = Blueprint("api", __name__)

def _not_found():
    return jsonify({"error": "Recipe not found"}), 404


def _recipe_dict(r):
    return {
        "id": r.id,
        "title": r.title,
        "description": r.description,
        "cook_time_minutes": r.cook_time_minutes,
        "servings": r.servings,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@api.route("/recipes", methods=["GET"])
def get_recipes():
    recipes = Recipe.query.all()
    return jsonify([_recipe_dict(r) for r in recipes])


@api.route("/recipes", methods=["POST"])
def create_recipe():
    data = request.get_json(silent=True) or {}

    if not data.get("title"):
        return jsonify({"error": "title is required"}), 400

    recipe = Recipe(
        title=data["title"],
        description=data.get("description"),
        ingredients_text=data.get("ingredients_text"),
        steps=data.get("steps"),
        cook_time_minutes=data.get("cook_time_minutes"),
        servings=data.get("servings"),
    )
    db.session.add(recipe)
    db.session.commit()

    return jsonify(_recipe_dict(recipe)), 201


@api.route("/recipes/<int:id>", methods=["GET"])
def get_recipe(id):
    recipe = db.session.get(Recipe, id)
    if recipe is None:
        return _not_found()
    return jsonify(_recipe_dict(recipe))


@api.route("/recipes/<int:id>", methods=["PUT"])
def update_recipe(id):
    recipe = db.session.get(Recipe, id)
    if recipe is None:
        return _not_found()

    data = request.get_json(silent=True) or {}
    for field in ("title", "description", "ingredients_text", "steps", "cook_time_minutes", "servings"):
        if field in data:
            setattr(recipe, field, data[field])

    db.session.commit()
    return jsonify(_recipe_dict(recipe))


@api.route("/recipes/<int:id>", methods=["DELETE"])
def delete_recipe(id):
    recipe = db.session.get(Recipe, id)
    if recipe is None:
        return _not_found()

    db.session.delete(recipe)
    db.session.commit()
    return "", 204
