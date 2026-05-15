from flask import Blueprint, jsonify, request
from extensions import db
from models import MealPlan, MealPlanEntry, Recipe
from shopping_utils import aggregate

meal_plan_bp = Blueprint("meal_plan_api", __name__)


def _entry_dict(entry):
    return {
        "id": entry.id,
        "recipe_id": entry.recipe_id,
        "recipe_title": entry.recipe.title if entry.recipe else None,
        "day_of_week": entry.day_of_week,
        "meal_type": entry.meal_type,
    }


def _plan_dict(plan, include_entries=False):
    d = {
        "id": plan.id,
        "name": plan.name,
        "week_start_date": plan.week_start_date.isoformat() if plan.week_start_date else None,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
    }
    if include_entries:
        d["entries"] = [_entry_dict(e) for e in plan.entries]
    return d


@meal_plan_bp.route("/meal-plans", methods=["POST"])
def create_meal_plan():
    data = request.get_json(silent=True) or {}

    week_start = None
    if data.get("week_start_date"):
        from datetime import date
        week_start = date.fromisoformat(data["week_start_date"])

    plan = MealPlan(name=data.get("name"), week_start_date=week_start)
    db.session.add(plan)
    db.session.commit()
    return jsonify(_plan_dict(plan)), 201


@meal_plan_bp.route("/meal-plans/<int:id>", methods=["GET"])
def get_meal_plan(id):
    plan = db.session.get(MealPlan, id)
    if plan is None:
        return jsonify({"error": "Meal plan not found"}), 404
    return jsonify(_plan_dict(plan, include_entries=True))


@meal_plan_bp.route("/meal-plans/<int:id>/entries", methods=["POST"])
def add_entry(id):
    plan = db.session.get(MealPlan, id)
    if plan is None:
        return jsonify({"error": "Meal plan not found"}), 404

    data = request.get_json(silent=True) or {}
    recipe_id = data.get("recipe_id")

    if not recipe_id:
        return jsonify({"error": "recipe_id is required"}), 400
    if db.session.get(Recipe, recipe_id) is None:
        return jsonify({"error": "Recipe not found"}), 404

    entry = MealPlanEntry(
        meal_plan_id=id,
        recipe_id=recipe_id,
        day_of_week=data.get("day_of_week"),
        meal_type=data.get("meal_type"),
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify(_entry_dict(entry)), 201


@meal_plan_bp.route("/meal-plans/<int:plan_id>/entries/<int:entry_id>", methods=["DELETE"])
def delete_entry(plan_id, entry_id):
    entry = db.session.get(MealPlanEntry, entry_id)
    if entry is None or entry.meal_plan_id != plan_id:
        return jsonify({"error": "Entry not found"}), 404

    db.session.delete(entry)
    db.session.commit()
    return "", 204


@meal_plan_bp.route("/meal-plans/<int:id>/shopping-list", methods=["GET"])
def shopping_list(id):
    plan = db.session.get(MealPlan, id)
    if plan is None:
        return jsonify({"error": "Meal plan not found"}), 404

    recipes = {e.recipe_id: e.recipe for e in plan.entries if e.recipe}.values()
    return jsonify(aggregate(recipes))
