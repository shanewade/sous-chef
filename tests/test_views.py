import json
from datetime import date, timedelta


class TestIndex:
    def test_returns_200(self, client):
        res = client.get("/")
        assert res.status_code == 200


def create_recipe(client, **kwargs):
    data = {"title": "Test Recipe", **kwargs}
    return client.post("/api/recipes", data=json.dumps(data), content_type="application/json")


def post_json(client, url, data):
    return client.post(url, data=json.dumps(data), content_type="application/json")


def current_monday():
    today = date.today()
    return (today - timedelta(days=today.weekday())).isoformat()


class TestRecipesIndex:
    def test_returns_200(self, client):
        res = client.get("/recipes")
        assert res.status_code == 200

    def test_has_search_input(self, client):
        res = client.get("/recipes")
        assert b'id="recipe-search"' in res.data

    def test_shows_new_recipe_button(self, client):
        res = client.get("/recipes")
        assert b"/recipes/new" in res.data

    def test_fetches_from_api(self, client):
        res = client.get("/recipes")
        assert b"/api/recipes" in res.data


class TestRecipesNew:
    def test_returns_200(self, client):
        res = client.get("/recipes/new")
        assert res.status_code == 200

    def test_shows_form_fields(self, client):
        res = client.get("/recipes/new")
        for field in [b'name="title"', b'name="cook_time_minutes"', b'name="servings"',
                      b'name="ingredients_text"', b'name="steps"']:
            assert field in res.data

    def test_posts_to_api_recipes(self, client):
        res = client.get("/recipes/new")
        assert b"/api/recipes" in res.data


class TestRecipesDetail:
    def test_returns_200_for_existing_recipe(self, client):
        recipe_id = create_recipe(client).get_json()["id"]
        res = client.get(f"/recipes/{recipe_id}")
        assert res.status_code == 200

    def test_returns_404_for_missing_recipe(self, client):
        res = client.get("/recipes/999")
        assert res.status_code == 404

    def test_shows_title(self, client):
        recipe_id = create_recipe(client, title="Chicken Soup").get_json()["id"]
        res = client.get(f"/recipes/{recipe_id}")
        assert b"Chicken Soup" in res.data

    def test_shows_cook_time_and_servings(self, client):
        recipe_id = create_recipe(client, cook_time_minutes=30, servings=4).get_json()["id"]
        res = client.get(f"/recipes/{recipe_id}")
        assert b"30" in res.data
        assert b"4" in res.data

    def test_shows_ingredients(self, client):
        recipe_id = create_recipe(client, ingredients_text="2 eggs\n1 cup flour").get_json()["id"]
        res = client.get(f"/recipes/{recipe_id}")
        assert b"2 eggs" in res.data
        assert b"1 cup flour" in res.data

    def test_shows_steps(self, client):
        recipe_id = create_recipe(client, steps="Mix ingredients\nBake at 350").get_json()["id"]
        res = client.get(f"/recipes/{recipe_id}")
        assert b"Mix ingredients" in res.data
        assert b"Bake at 350" in res.data


class TestMealPlanView:
    def test_returns_200(self, client):
        res = client.get("/meal-plan")
        assert res.status_code == 200

    def test_creates_plan_for_current_week_when_none_exists(self, client):
        res = client.get("/meal-plan")
        assert b"Meal Plan" in res.data

    def test_uses_existing_plan_when_present(self, client):
        post_json(client, "/api/meal-plans", {
            "name": "My Week",
            "week_start_date": current_monday(),
        })
        res = client.get("/meal-plan")
        assert res.status_code == 200

    def test_shows_day_headers(self, client):
        res = client.get("/meal-plan")
        for day in [b"Mon", b"Tue", b"Wed", b"Thu", b"Fri", b"Sat", b"Sun"]:
            assert day in res.data

    def test_shows_meal_rows(self, client):
        res = client.get("/meal-plan")
        for meal in [b"Breakfast", b"Lunch", b"Dinner"]:
            assert meal in res.data


class TestShoppingListView:
    def test_returns_200_with_no_plan(self, client):
        res = client.get("/shopping-list")
        assert res.status_code == 200

    def test_shows_empty_state_when_no_plan(self, client):
        res = client.get("/shopping-list")
        assert b"No meal plan" in res.data

    def test_shows_ingredients_from_plan_recipes(self, client):
        recipe_id = create_recipe(
            client,
            title="Pasta",
            ingredients_text="2 cups flour\n1 tsp salt",
        ).get_json()["id"]
        plan_id = post_json(client, "/api/meal-plans", {
            "week_start_date": current_monday(),
        }).get_json()["id"]
        post_json(client, f"/api/meal-plans/{plan_id}/entries", {
            "recipe_id": recipe_id,
            "day_of_week": "Monday",
            "meal_type": "dinner",
        })
        res = client.get("/shopping-list")
        assert res.status_code == 200
        assert b"flour" in res.data
        assert b"salt" in res.data

    def test_shows_empty_state_when_plan_has_no_ingredients(self, client):
        recipe_id = create_recipe(client).get_json()["id"]
        plan_id = post_json(client, "/api/meal-plans", {
            "week_start_date": current_monday(),
        }).get_json()["id"]
        post_json(client, f"/api/meal-plans/{plan_id}/entries", {
            "recipe_id": recipe_id,
            "day_of_week": "Monday",
            "meal_type": "dinner",
        })
        res = client.get("/shopping-list")
        assert res.status_code == 200
        assert b"no recipes with ingredients" in res.data
