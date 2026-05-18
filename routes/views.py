from datetime import date, timedelta
from flask import Blueprint, render_template, abort, flash, redirect, url_for, request
from extensions import db
from models import MealPlan, Recipe, Tag, ShoppingListItem
from shopping_utils import aggregate, _fmt_qty
from forms import RecipeForm

views = Blueprint("views", __name__)


@views.route("/recipes")
def recipes_index():
    recipes = Recipe.query.all()
    return render_template("recipes/index.html", recipes=recipes)


@views.route("/recipes/new", methods=["GET", "POST"])
def recipes_new():
    form = RecipeForm()
    if form.validate_on_submit():
        tag_names = [t.strip().lower() for t in (form.tags.data or "").split(",") if t.strip()]
        recipe = Recipe(
            title=form.title.data,
            description=form.description.data or None,
            cook_time_minutes=form.cook_time_minutes.data,
            servings=form.servings.data,
            ingredients_text=form.ingredients_text.data or None,
            steps=form.steps.data or None,
        )
        tags = []
        for name in tag_names:
            tag = Tag.query.filter_by(name=name).first()
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
            tags.append(tag)
        recipe.tags = tags
        db.session.add(recipe)
        db.session.commit()
        flash("Recipe created successfully!", "success")
        return redirect(url_for("views.recipes_detail", id=recipe.id))
    if request.method == "POST":
        flash("Please fix the errors below.", "error")
    return render_template("recipes/new.html", form=form)


@views.route("/recipes/<int:id>")
def recipes_detail(id):
    recipe = db.session.get(Recipe, id)
    if recipe is None:
        abort(404)
    return render_template("recipes/detail.html", recipe=recipe)


@views.route("/recipes/<int:id>/edit")
def recipes_edit(id):
    recipe = db.session.get(Recipe, id)
    if recipe is None:
        abort(404)
    return render_template("recipes/edit.html", recipe=recipe)


@views.route("/settings")
def settings_page():
    return render_template("settings.html")


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


@views.route("/shopping-list")
def shopping_list():
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    plan = MealPlan.query.filter_by(week_start_date=monday).first()

    if plan is None:
        items, grouped, plan_id = [], {}, None
    else:
        recipes = {e.recipe_id: e.recipe for e in plan.entries if e.recipe}.values()
        items = aggregate(recipes)
        grouped = {}
        for item in items:
            item['manual'] = False
            grouped.setdefault(item['category'], []).append(item)

        # Merge manually added items
        from routes.meal_plan_api import _parse_shopping_item
        manual_items = ShoppingListItem.query.filter_by(meal_plan_id=plan.id).order_by(ShoppingListItem.created_at).all()
        for mi in manual_items:
            qty, unit, name, category = _parse_shopping_item(mi.raw_text)
            grouped.setdefault(category, []).append({
                'ingredient': name,
                'quantity': _fmt_qty(qty),
                'unit': unit or '',
                'category': category,
                'manual': True,
                'item_id': mi.id,
            })

        plan_id = plan.id

    return render_template(
        "shopping_list/index.html",
        grouped=grouped,
        plan_id=plan_id,
        week_label=monday.strftime('%b %-d'),
    )
