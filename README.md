# Sous-Chef

A meal planning web app built with Flask. Plan your week's meals, browse and create recipes, and generate a shopping list aggregated from your plan's ingredients.

## Features

- **Recipes** — create recipes with ingredients, steps, cook time, and servings
- **Meal Plan** — assign recipes to breakfast, lunch, or dinner slots across a 7-day week
- **Shopping List** — auto-generated from the week's planned recipes, grouped by category (Produce, Dairy & Eggs, Meat & Seafood, Grains & Bread, Pantry) with printable view

## Requirements

- Python 3.9

## Setup

**1. Clone the repository**

```bash
git clone https://github.com/shanewade/sous-chef.git
cd sous-chef
```

**2. Activate the virtual environment**

```bash
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Initialise the database**

```bash
flask db upgrade
```

**5. Run the development server**

```bash
python app.py
```

The app will be available at `http://localhost:5001`.

## Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=. --cov-report=term-missing
```

## Project Structure

```
app.py                  # App factory and blueprint registration
models.py               # SQLAlchemy models (Recipe, MealPlan, MealPlanEntry)
shopping_utils.py       # Ingredient parsing and aggregation logic
routes/
  api.py                # REST API for recipes (/api/recipes)
  meal_plan_api.py      # REST API for meal plans (/api/meal-plans)
  views.py              # HTML page routes
templates/
  base.html             # Shared layout and nav
  recipes/              # Recipe list, detail, and new recipe form
  meal_plan/            # Weekly meal plan grid
  shopping_list/        # Shopping list with checkboxes and print view
static/
  style.css             # All styles — no external framework
migrations/             # Alembic database migrations
tests/                  # pytest test suite (99% coverage)
```
