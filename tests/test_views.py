import json
from datetime import date, timedelta


class TestIndex:
    def test_redirects_to_recipes(self, client):
        res = client.get("/")
        assert res.status_code == 302
        assert res.headers["Location"] == "/recipes"

    def test_favicon_returns_200(self, client):
        res = client.get("/favicon.ico")
        assert res.status_code == 200
        assert res.content_type == "image/x-icon"


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

    def test_form_posts_to_new_route(self, client):
        res = client.get("/recipes/new")
        assert b'action="/recipes/new"' in res.data

    def test_valid_post_redirects_to_detail(self, client):
        res = client.post("/recipes/new", data={"title": "New Dish"})
        assert res.status_code == 302
        assert "/recipes/" in res.headers["Location"]

    def test_valid_post_shows_success_flash(self, client):
        res = client.post("/recipes/new", data={"title": "New Dish"}, follow_redirects=True)
        assert b"Recipe created successfully" in res.data

    def test_valid_post_with_tags_creates_recipe(self, client):
        client.post("/recipes/new", data={"title": "Tagged Dish", "tags": "italian,quick"})
        res = client.get("/api/recipes").get_json()
        assert sorted(res[0]["tags"]) == ["italian", "quick"]

    def test_missing_title_re_renders_form(self, client):
        res = client.post("/recipes/new", data={"title": ""})
        assert res.status_code == 200
        assert b"Title is required" in res.data

    def test_missing_title_shows_error_flash(self, client):
        res = client.post("/recipes/new", data={"title": ""})
        assert b"Please fix the errors below" in res.data

    def test_title_too_long_shows_error(self, client):
        res = client.post("/recipes/new", data={"title": "x" * 201})
        assert res.status_code == 200
        assert b"200 characters" in res.data

    def test_negative_cook_time_shows_error(self, client):
        res = client.post("/recipes/new", data={"title": "Valid", "cook_time_minutes": "-5"})
        assert res.status_code == 200
        assert b"positive" in res.data

    def test_zero_cook_time_shows_error(self, client):
        res = client.post("/recipes/new", data={"title": "Valid", "cook_time_minutes": "0"})
        assert res.status_code == 200
        assert b"positive" in res.data

    def test_valid_cook_time_accepted(self, client):
        res = client.post("/recipes/new", data={"title": "Valid", "cook_time_minutes": "30"})
        assert res.status_code == 302


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

    def test_shows_unit_toggle(self, client):
        recipe_id = create_recipe(client, ingredients_text="2 cups flour").get_json()["id"]
        res = client.get(f"/recipes/{recipe_id}")
        assert b'id="unit-toggle"' in res.data
        assert b'data-system="us"' in res.data
        assert b'data-system="metric"' in res.data

    def test_unit_conversion_js_present(self, client):
        recipe_id = create_recipe(client).get_json()["id"]
        res = client.get(f"/recipes/{recipe_id}")
        assert b'unitSystem' in res.data
        assert b'localStorage' in res.data
        assert b'data-metric' in res.data

    def test_shows_edit_button_linking_to_edit_page(self, client):
        recipe_id = create_recipe(client).get_json()["id"]
        res = client.get(f"/recipes/{recipe_id}")
        assert f"/recipes/{recipe_id}/edit".encode() in res.data

    def test_shows_delete_button(self, client):
        recipe_id = create_recipe(client).get_json()["id"]
        res = client.get(f"/recipes/{recipe_id}")
        assert b'id="delete-btn"' in res.data

    def test_shows_confirmation_modal(self, client):
        recipe_id = create_recipe(client).get_json()["id"]
        res = client.get(f"/recipes/{recipe_id}")
        assert b'id="delete-modal"' in res.data
        assert b'id="confirm-delete"' in res.data
        assert b'id="cancel-delete"' in res.data

    def test_modal_calls_delete_api(self, client):
        recipe_id = create_recipe(client).get_json()["id"]
        res = client.get(f"/recipes/{recipe_id}")
        assert b"method: 'DELETE'" in res.data
        assert f"/api/recipes/{recipe_id}".encode() in res.data


class TestRecipesEdit:
    def test_returns_200_for_existing_recipe(self, client):
        recipe_id = create_recipe(client).get_json()["id"]
        res = client.get(f"/recipes/{recipe_id}/edit")
        assert res.status_code == 200

    def test_returns_404_for_missing_recipe(self, client):
        res = client.get("/recipes/999/edit")
        assert res.status_code == 404

    def test_contains_form_fields(self, client):
        recipe_id = create_recipe(client).get_json()["id"]
        res = client.get(f"/recipes/{recipe_id}/edit")
        for field in [b'name="title"', b'name="cook_time_minutes"', b'name="servings"',
                      b'name="ingredients_text"', b'name="steps"']:
            assert field in res.data

    def test_submits_via_put(self, client):
        recipe_id = create_recipe(client).get_json()["id"]
        res = client.get(f"/recipes/{recipe_id}/edit")
        assert b"method: 'PUT'" in res.data
        assert f"var recipeId = {recipe_id}".encode() in res.data

    def test_cancel_links_back_to_detail(self, client):
        recipe_id = create_recipe(client).get_json()["id"]
        res = client.get(f"/recipes/{recipe_id}/edit")
        assert f'href="/recipes/{recipe_id}"'.encode() in res.data


class TestErrorPages:
    def test_404_returns_correct_status(self, client):
        res = client.get("/recipes/999999")
        assert res.status_code == 404

    def test_404_shows_friendly_message(self, client):
        res = client.get("/recipes/999999")
        assert b"Page Not Found" in res.data

    def test_404_links_back_to_recipes(self, client):
        res = client.get("/recipes/999999")
        assert b'href="/recipes"' in res.data

    def test_500_shows_friendly_message(self, app):
        import app as app_module
        with app.test_request_context():
            html, status = app_module.server_error(Exception("test"))
        assert status == 500
        assert "Something Went Wrong" in html


class TestSettingsView:
    def test_returns_200(self, client):
        res = client.get("/settings")
        assert res.status_code == 200

    def test_shows_all_ten_themes(self, client):
        res = client.get("/settings")
        for theme in [b'default', b'forest', b'sunset', b'ocean', b'lavender',
                      b'slate', b'rose', b'espresso', b'mint', b'midnight']:
            assert theme in res.data

    def test_shows_unit_toggle(self, client):
        res = client.get("/settings")
        assert b'id="unit-toggle"' in res.data
        assert b'data-system="us"' in res.data
        assert b'data-system="metric"' in res.data

    def test_shows_category_order_list(self, client):
        res = client.get("/settings")
        assert b'id="category-order-list"' in res.data
        assert b'categoryOrder' in res.data

    def test_shows_reset_button(self, client):
        res = client.get("/settings")
        assert b'id="reset-btn"' in res.data

    def test_settings_link_in_navbar(self, client):
        res = client.get("/recipes")
        assert b'href="/settings"' in res.data

    def test_theme_script_in_head(self, client):
        res = client.get("/recipes")
        assert b'appSettings' in res.data
        assert b'data-theme' in res.data


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

    def test_metric_conversion_js_present(self, client):
        res = client.get("/shopping-list")
        assert b'unitSystem' in res.data
        assert b'TO_ML' in res.data

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
