import json


def post_json(client, url, data):
    return client.post(url, data=json.dumps(data), content_type="application/json")


def create_plan(client, name="Week 1", week_start_date="2026-05-19"):
    return post_json(client, "/api/meal-plans", {"name": name, "week_start_date": week_start_date})


def create_recipe(client, title="Test Recipe", **kwargs):
    return post_json(client, "/api/recipes", {"title": title, **kwargs})


class TestCreateMealPlan:
    def test_creates_plan_and_returns_201(self, client):
        res = create_plan(client)
        assert res.status_code == 201
        body = res.get_json()
        assert body["name"] == "Week 1"
        assert body["week_start_date"] == "2026-05-19"
        assert "id" in body


class TestGetMealPlan:
    def test_returns_plan_with_entries(self, client):
        plan_id = create_plan(client).get_json()["id"]
        recipe_id = create_recipe(client).get_json()["id"]
        post_json(client, f"/api/meal-plans/{plan_id}/entries", {
            "recipe_id": recipe_id,
            "day_of_week": "Monday",
            "meal_type": "dinner",
        })

        res = client.get(f"/api/meal-plans/{plan_id}")
        assert res.status_code == 200
        body = res.get_json()
        assert body["id"] == plan_id
        assert len(body["entries"]) == 1
        entry = body["entries"][0]
        assert entry["recipe_id"] == recipe_id
        assert entry["recipe_title"] == "Test Recipe"
        assert entry["day_of_week"] == "Monday"
        assert entry["meal_type"] == "dinner"

    def test_returns_404_for_missing_plan(self, client):
        res = client.get("/api/meal-plans/999")
        assert res.status_code == 404


class TestAddEntry:
    def test_adds_entry_and_returns_201(self, client):
        plan_id = create_plan(client).get_json()["id"]
        recipe_id = create_recipe(client).get_json()["id"]

        res = post_json(client, f"/api/meal-plans/{plan_id}/entries", {
            "recipe_id": recipe_id,
            "day_of_week": "Tuesday",
            "meal_type": "lunch",
        })
        assert res.status_code == 201
        body = res.get_json()
        assert body["recipe_id"] == recipe_id
        assert body["day_of_week"] == "Tuesday"
        assert body["meal_type"] == "lunch"

    def test_returns_400_when_recipe_id_missing(self, client):
        plan_id = create_plan(client).get_json()["id"]
        res = post_json(client, f"/api/meal-plans/{plan_id}/entries", {})
        assert res.status_code == 400

    def test_returns_404_for_missing_plan(self, client):
        res = post_json(client, "/api/meal-plans/999/entries", {"recipe_id": 1})
        assert res.status_code == 404

    def test_returns_404_for_missing_recipe(self, client):
        plan_id = create_plan(client).get_json()["id"]
        res = post_json(client, f"/api/meal-plans/{plan_id}/entries", {"recipe_id": 999})
        assert res.status_code == 404


class TestDeleteEntry:
    def test_deletes_entry_and_returns_204(self, client):
        plan_id = create_plan(client).get_json()["id"]
        recipe_id = create_recipe(client).get_json()["id"]
        entry_id = post_json(client, f"/api/meal-plans/{plan_id}/entries", {
            "recipe_id": recipe_id,
            "day_of_week": "Wednesday",
            "meal_type": "breakfast",
        }).get_json()["id"]

        res = client.delete(f"/api/meal-plans/{plan_id}/entries/{entry_id}")
        assert res.status_code == 204

        body = client.get(f"/api/meal-plans/{plan_id}").get_json()
        assert body["entries"] == []

    def test_returns_404_for_missing_entry(self, client):
        plan_id = create_plan(client).get_json()["id"]
        res = client.delete(f"/api/meal-plans/{plan_id}/entries/999")
        assert res.status_code == 404


class TestShoppingListAPI:
    def test_returns_404_for_missing_plan(self, client):
        res = client.get("/api/meal-plans/999/shopping-list")
        assert res.status_code == 404

    def test_returns_empty_list_when_no_ingredients(self, client):
        plan_id = create_plan(client).get_json()["id"]
        recipe_id = create_recipe(client).get_json()["id"]
        post_json(client, f"/api/meal-plans/{plan_id}/entries", {
            "recipe_id": recipe_id, "day_of_week": "Monday", "meal_type": "dinner",
        })
        res = client.get(f"/api/meal-plans/{plan_id}/shopping-list")
        assert res.status_code == 200
        assert res.get_json() == []

    def test_returns_aggregated_ingredients(self, client):
        plan_id = create_plan(client).get_json()["id"]
        recipe_id = create_recipe(
            client, ingredients_text="2 cups flour\n1 tsp salt"
        ).get_json()["id"]
        post_json(client, f"/api/meal-plans/{plan_id}/entries", {
            "recipe_id": recipe_id, "day_of_week": "Monday", "meal_type": "dinner",
        })
        items = client.get(f"/api/meal-plans/{plan_id}/shopping-list").get_json()
        names = [i["ingredient"] for i in items]
        assert "flour" in names
        assert "salt" in names

    def test_sums_quantities_across_recipes(self, client):
        plan_id = create_plan(client).get_json()["id"]
        for ingredients in ["2 cups flour", "1 cup flour"]:
            recipe_id = create_recipe(client, ingredients_text=ingredients).get_json()["id"]
            post_json(client, f"/api/meal-plans/{plan_id}/entries", {
                "recipe_id": recipe_id, "day_of_week": "Monday", "meal_type": "dinner",
            })
        items = client.get(f"/api/meal-plans/{plan_id}/shopping-list").get_json()
        flour = next(i for i in items if i["ingredient"] == "flour")
        assert flour["quantity"] == "3"


class TestShoppingItems:
    def test_add_item_returns_201(self, client):
        plan_id = create_plan(client).get_json()["id"]
        res = post_json(client, f"/api/meal-plans/{plan_id}/shopping-items", {"text": "2 cups milk"})
        assert res.status_code == 201
        body = res.get_json()
        assert body["ingredient"] == "milk"
        assert body["quantity"] == "2"
        assert body["unit"] == "cup"
        assert body["category"] == "Dairy & Eggs"

    def test_add_item_missing_text_returns_400(self, client):
        plan_id = create_plan(client).get_json()["id"]
        res = post_json(client, f"/api/meal-plans/{plan_id}/shopping-items", {})
        assert res.status_code == 400

    def test_add_item_invalid_plan_returns_404(self, client):
        res = post_json(client, "/api/meal-plans/999/shopping-items", {"text": "milk"})
        assert res.status_code == 404

    def test_add_item_no_unit_accepted(self, client):
        plan_id = create_plan(client).get_json()["id"]
        res = post_json(client, f"/api/meal-plans/{plan_id}/shopping-items", {"text": "dish soap"})
        assert res.status_code == 201
        assert res.get_json()["ingredient"] == "dish soap"

    def test_delete_item_returns_204(self, client):
        plan_id = create_plan(client).get_json()["id"]
        item_id = post_json(client, f"/api/meal-plans/{plan_id}/shopping-items", {"text": "milk"}).get_json()["id"]
        res = client.delete(f"/api/meal-plans/{plan_id}/shopping-items/{item_id}")
        assert res.status_code == 204

    def test_delete_item_wrong_plan_returns_404(self, client):
        plan_id = create_plan(client).get_json()["id"]
        other_id = create_plan(client, week_start_date="2026-05-26").get_json()["id"]
        item_id = post_json(client, f"/api/meal-plans/{plan_id}/shopping-items", {"text": "milk"}).get_json()["id"]
        res = client.delete(f"/api/meal-plans/{other_id}/shopping-items/{item_id}")
        assert res.status_code == 404

    def test_delete_missing_item_returns_404(self, client):
        plan_id = create_plan(client).get_json()["id"]
        res = client.delete(f"/api/meal-plans/{plan_id}/shopping-items/999")
        assert res.status_code == 404


class TestScaleFactor:
    def test_entry_defaults_scale_factor_to_1(self, client):
        plan_id = create_plan(client).get_json()["id"]
        recipe_id = create_recipe(client).get_json()["id"]
        res = post_json(client, f"/api/meal-plans/{plan_id}/entries", {
            "recipe_id": recipe_id, "day_of_week": "Monday", "meal_type": "dinner",
        })
        assert res.status_code == 201
        assert res.get_json()["scale_factor"] == 1.0

    def test_entry_stores_custom_scale_factor(self, client):
        plan_id = create_plan(client).get_json()["id"]
        recipe_id = create_recipe(client).get_json()["id"]
        res = post_json(client, f"/api/meal-plans/{plan_id}/entries", {
            "recipe_id": recipe_id, "day_of_week": "Monday", "meal_type": "dinner",
            "scale_factor": 2.0,
        })
        assert res.get_json()["scale_factor"] == 2.0

    def test_shopping_list_applies_scale_to_quantities(self, client):
        plan_id = create_plan(client).get_json()["id"]
        recipe_id = create_recipe(client, ingredients_text="1 cup flour").get_json()["id"]
        post_json(client, f"/api/meal-plans/{plan_id}/entries", {
            "recipe_id": recipe_id, "day_of_week": "Monday", "meal_type": "dinner",
            "scale_factor": 2.0,
        })
        items = client.get(f"/api/meal-plans/{plan_id}/shopping-list").get_json()
        flour = next(i for i in items if i["ingredient"] == "flour")
        assert flour["quantity"] == "2"

    def test_shopping_list_sums_same_recipe_at_different_scales(self, client):
        plan_id = create_plan(client).get_json()["id"]
        recipe_id = create_recipe(client, ingredients_text="1 cup flour").get_json()["id"]
        # Add the same recipe twice: 1× on Monday, 2× on Wednesday
        post_json(client, f"/api/meal-plans/{plan_id}/entries", {
            "recipe_id": recipe_id, "day_of_week": "Monday", "meal_type": "dinner",
            "scale_factor": 1.0,
        })
        post_json(client, f"/api/meal-plans/{plan_id}/entries", {
            "recipe_id": recipe_id, "day_of_week": "Wednesday", "meal_type": "dinner",
            "scale_factor": 2.0,
        })
        items = client.get(f"/api/meal-plans/{plan_id}/shopping-list").get_json()
        flour = next(i for i in items if i["ingredient"] == "flour")
        assert flour["quantity"] == "3"  # 1 + 2 = 3 cups
