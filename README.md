# Sous-Chef

A meal planning web app built with Flask. Plan your week's meals, browse and create recipes, and generate a shopping list aggregated from your plan's ingredients.

## Features

- **Recipes** — create, edit, and delete recipes with ingredients, steps, cook time, servings, and tags
- **Search & filter** — search recipes by title or description, filter by tag
- **Meal Plan** — assign recipes to breakfast, lunch, or dinner slots across a 7-day week
- **Shopping List** — auto-generated from the week's planned recipes, grouped by category (Produce, Dairy & Eggs, Meat & Seafood, Grains & Bread, Pantry) with printable view

## Requirements

- Python 3.9+
- make (optional, for Makefile shortcuts)

## Quick Start (Makefile)

```bash
git clone https://github.com/shanewade/sous-chef.git
cd sous-chef
make install       # install dependencies into the checked-in venv
make reset         # drop DB, run migrations, and seed 10 sample recipes
make run           # start the dev server at http://localhost:5001
```

## Makefile Targets

| Target | Description |
|---|---|
| `make run` | Start the Flask dev server on port 5001 |
| `make test` | Run the full test suite with `pytest -v` |
| `make seed` | Populate the DB with 10 sample recipes |
| `make reset` | Drop and recreate the DB, then seed it |
| `make install` | Install dependencies from `requirements.txt` |

## Manual Setup

**1. Clone and activate the virtual environment**

```bash
git clone https://github.com/shanewade/sous-chef.git
cd sous-chef
source venv/bin/activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Initialise the database**

```bash
flask db upgrade
```

**4. (Optional) Seed sample recipes**

```bash
python seed.py
```

**5. Run the development server**

```bash
python app.py
```

The app will be available at `http://localhost:5001`.

## Running Tests

```bash
pytest -v
```

With coverage:

```bash
pytest --cov=. --cov-report=term-missing
```

## Project Structure

```
app.py                  # Flask app, blueprint registration, error handlers
models.py               # SQLAlchemy models (Recipe, Tag, MealPlan, MealPlanEntry)
forms.py                # WTForms form definitions (RecipeForm)
seed.py                 # DB seeding script — 10 varied sample recipes
shopping_utils.py       # Ingredient parsing and aggregation logic
Makefile                # Common dev shortcuts (run, test, seed, reset, install)
routes/
  api.py                # REST API for recipes (/api/recipes)
  meal_plan_api.py      # REST API for meal plans (/api/meal-plans)
  views.py              # HTML page routes with WTForms validation
templates/
  base.html             # Shared layout, nav, and flash message display
  404.html              # Custom 404 page
  500.html              # Custom 500 page
  recipes/              # Recipe list, detail, new, and edit forms
  meal_plan/            # Weekly meal plan grid
  shopping_list/        # Shopping list with checkboxes and print view
static/
  style.css             # All styles — no external framework
migrations/             # Alembic database migrations
tests/                  # pytest test suite (99% coverage)
```
