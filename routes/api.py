from flask import Blueprint, jsonify, request
from extensions import db
from models import Recipe, Tag
from recipe_scraper import scrape_recipe, ScraperError

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
        "ingredients_text": r.ingredients_text,
        "steps": r.steps,
        "tags": [t.name for t in r.tags],
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _resolve_tags(names):
    """Return Tag objects for a list of tag name strings, creating missing ones."""
    tags = []
    for name in names:
        name = name.strip().lower()
        if not name:
            continue
        tag = Tag.query.filter_by(name=name).first()
        if tag is None:
            tag = Tag(name=name)
            db.session.add(tag)
        tags.append(tag)
    return tags


@api.route("/recipes", methods=["GET"])
def get_recipes():
    q = Recipe.query
    search = request.args.get("search", "").strip()
    tag = request.args.get("tag", "").strip()
    if search:
        like = f"%{search}%"
        q = q.filter(
            db.or_(Recipe.title.ilike(like), Recipe.description.ilike(like))
        )
    if tag:
        q = q.filter(Recipe.tags.any(Tag.name == tag))
    return jsonify([_recipe_dict(r) for r in q.all()])


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
    if "tags" in data:
        recipe.tags = _resolve_tags(data["tags"])
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
    if "tags" in data:
        recipe.tags = _resolve_tags(data["tags"])

    db.session.commit()
    return jsonify(_recipe_dict(recipe))


@api.route("/recipes/import-url", methods=["POST"])
def import_recipe_url():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "url is required"}), 400
    try:
        result = scrape_recipe(url)
    except ScraperError as e:
        return jsonify({"error": str(e)}), 422
    return jsonify(result), 200


@api.route("/recipes/<int:id>", methods=["DELETE"])
def delete_recipe(id):
    recipe = db.session.get(Recipe, id)
    if recipe is None:
        return _not_found()

    db.session.delete(recipe)
    db.session.commit()
    return "", 204
