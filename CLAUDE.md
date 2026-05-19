# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Sous-chef is a Flask meal-planning app. It lets users browse and create recipes, assign them to a weekly meal plan, and generate a shopping list aggregated from the plan's ingredients. The project is in early development. A virtual environment is checked in at `venv/` (Python 3.9).

## Commands

```bash
# Activate the virtualenv before running anything
source venv/bin/activate

# Run the dev server (port 5001)
python app.py

# Run all tests
pytest

# Run a single test file
pytest tests/test_recipes_api.py

# Run a single test by name
pytest tests/test_recipes_api.py::TestCreateRecipe::test_creates_recipe_and_returns_201

# Run tests with coverage
pytest --cov=. --cov-report=term-missing

# Apply database migrations
flask db upgrade

# Generate a new migration after changing models.py
flask db migrate -m "description"
```

## Architecture

**Entry point:** `app.py` creates the Flask app, initialises SQLAlchemy and Flask-Migrate via `extensions.py`, then registers three blueprints:
- `routes/api.py` (`api`) — JSON CRUD for recipes, mounted at `/api`
- `routes/meal_plan_api.py` (`meal_plan_bp`) — JSON CRUD for meal plans, entries, and shopping list, mounted at `/api`
- `routes/views.py` (`views`) — HTML page routes, no prefix

**Models** (`models.py`): `Recipe`, `Ingredient`, `MealPlan`, `MealPlanEntry`. `db` and `migrate` are singletons in `extensions.py` to avoid circular imports — `models.py` must be imported after `db.init_app(app)`.

**Shopping list pipeline** (`shopping_utils.py`): `parse_line()` extracts quantity/unit/name from a free-text ingredient line. `aggregate()` iterates all recipes in a plan, calls `parse_line()` on each line of `ingredients_text`, sums quantities by `(name, unit)` key, and returns a sorted list of dicts. `categorize()` does keyword matching against five hardcoded category lists (first match wins). The view and the API endpoint both call `aggregate()` directly — there is no internal HTTP call.

**Ingredient format:** `Recipe.ingredients_text` is a plain text blob, one ingredient per line, e.g. `"2 cups flour\n1 tsp salt"`. The parser handles integer, decimal, and fractional quantities (`1/2`, `1 1/2`), normalises unit aliases to canonical forms, and treats any unrecognised word as part of the ingredient name.

**Meal plan date logic:** both `/meal-plan` and `/shopping-list` views automatically find or create the plan whose `week_start_date` is the Monday of the current week. There is only ever one plan per week.

**Templates** extend `templates/base.html`. Each feature area has its own subdirectory: `templates/recipes/`, `templates/meal_plan/`, `templates/shopping_list/`. There is no JavaScript framework — interactivity on the meal plan grid and new-recipe form is vanilla JS using `fetch`.

## Test Setup

Tests use an in-memory SQLite database. Because Flask-SQLAlchemy 3.1 caches its engine at `init_app` time and blocks a second `init_app` call, `conftest.py` injects a fresh `StaticPool` in-memory engine directly into `_db._app_engines[flask_app][None]` for each test. `StaticPool` is required so the fixture's app context and the test client's request context share the same in-memory database. The `db` fixture is `autouse=True` and calls `create_all` / `drop_all` around every test.

## Database

SQLite file lives at `instance/recipe_app.db`. Migrations are managed with Flask-Migrate (Alembic). The initial migration (`migrations/versions/f8f2af88bbdf`) creates all tables — if the DB file is missing or empty, run `flask db upgrade` to recreate them. Do not use `db.create_all()` in production; use migrations.

## Workflow

- Run tests before every commit (`pytest -q`)
- Commit and push together unless the user asks for them separately
- Close the GitHub issue when a feature ships (`gh issue close <n>`)
- Kill port 5001 before starting the dev server: `kill $(lsof -ti:5001) 2>/dev/null`
- Screenshots dropped in the project root can be read directly with the Read tool
- Work directly on `main` — no feature branches

## Project Context

- Single-user personal app — no auth, no multi-tenancy, no need to design for scale
- Primary device is iPad used while cooking — UI should be touch-friendly and fast to load
- Deployment target is Fly.io with a persistent SQLite volume (Issue #20); currently runs locally on port 5001

## Environment Notes

- `brotli` is not installed in the venv — never add `Accept-Encoding: br` to outgoing HTTP headers (causes servers to send responses the app cannot decompress)
- Always activate the venv before running any Python or Flask commands: `source venv/bin/activate`
