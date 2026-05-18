import json
from unittest.mock import patch
from recipe_scraper import ScraperError


def post_recipe(client, **kwargs):
    data = {"title": "Test Recipe", **kwargs}
    return client.post("/api/recipes", data=json.dumps(data), content_type="application/json")


def put_recipe(client, recipe_id, **kwargs):
    return client.put(
        f"/api/recipes/{recipe_id}",
        data=json.dumps(kwargs),
        content_type="application/json",
    )


class TestGetRecipes:
    def test_returns_empty_list_initially(self, client):
        res = client.get("/api/recipes")
        assert res.status_code == 200
        assert res.get_json() == []

    def test_tags_included_in_response(self, client):
        post_recipe(client, tags=["italian", "dinner"])
        body = client.get("/api/recipes").get_json()
        assert sorted(body[0]["tags"]) == ["dinner", "italian"]

    def test_search_filters_by_title(self, client):
        post_recipe(client, title="Pasta Carbonara")
        post_recipe(client, title="Chicken Soup")
        res = client.get("/api/recipes?search=pasta").get_json()
        assert len(res) == 1
        assert res[0]["title"] == "Pasta Carbonara"

    def test_search_filters_by_description(self, client):
        post_recipe(client, title="Soup", description="hearty tomato broth")
        post_recipe(client, title="Salad", description="fresh greens")
        res = client.get("/api/recipes?search=tomato").get_json()
        assert len(res) == 1
        assert res[0]["title"] == "Soup"

    def test_search_is_case_insensitive(self, client):
        post_recipe(client, title="Beef Tacos")
        res = client.get("/api/recipes?search=BEEF").get_json()
        assert len(res) == 1

    def test_tag_filter_returns_only_matching_recipes(self, client):
        post_recipe(client, title="Tagged", tags=["vegetarian"])
        post_recipe(client, title="Untagged")
        res = client.get("/api/recipes?tag=vegetarian").get_json()
        assert len(res) == 1
        assert res[0]["title"] == "Tagged"

    def test_tag_filter_no_match_returns_empty(self, client):
        post_recipe(client, title="Beef Stew", tags=["dinner"])
        res = client.get("/api/recipes?tag=breakfast").get_json()
        assert res == []


class TestCreateRecipe:
    def test_creates_recipe_and_returns_201(self, client):
        res = post_recipe(client, description="A test", servings=2)
        assert res.status_code == 201
        body = res.get_json()
        assert body["title"] == "Test Recipe"
        assert body["servings"] == 2
        assert "id" in body

    def test_missing_title_returns_400(self, client):
        res = client.post("/api/recipes", data=json.dumps({}), content_type="application/json")
        assert res.status_code == 400
        assert res.get_json() == {"error": "title is required"}

    def test_creates_recipe_with_tags(self, client):
        res = post_recipe(client, tags=["italian", "quick"])
        assert res.status_code == 201
        assert sorted(res.get_json()["tags"]) == ["italian", "quick"]

    def test_blank_tag_names_are_skipped(self, client):
        res = post_recipe(client, tags=["", "dinner", "  "])
        assert res.get_json()["tags"] == ["dinner"]

    def test_tags_reuse_existing_tag_rows(self, client):
        post_recipe(client, title="Recipe A", tags=["vegan"])
        post_recipe(client, title="Recipe B", tags=["vegan"])
        # Both recipes share the same tag — both should appear in the filter
        res = client.get("/api/recipes?tag=vegan").get_json()
        assert len(res) == 2


class TestGetRecipe:
    def test_returns_recipe(self, client):
        recipe_id = post_recipe(client).get_json()["id"]
        res = client.get(f"/api/recipes/{recipe_id}")
        assert res.status_code == 200
        assert res.get_json()["title"] == "Test Recipe"

    def test_returns_ingredients_text_and_steps(self, client):
        recipe_id = post_recipe(
            client, ingredients_text="2 eggs\n1 cup milk", steps="1. Mix.\n2. Cook."
        ).get_json()["id"]
        body = client.get(f"/api/recipes/{recipe_id}").get_json()
        assert body["ingredients_text"] == "2 eggs\n1 cup milk"
        assert body["steps"] == "1. Mix.\n2. Cook."

    def test_missing_recipe_returns_404(self, client):
        res = client.get("/api/recipes/999")
        assert res.status_code == 404
        assert res.get_json() == {"error": "Recipe not found"}


class TestUpdateRecipe:
    def test_updates_single_field(self, client):
        recipe_id = post_recipe(client).get_json()["id"]
        res = put_recipe(client, recipe_id, servings=8)
        assert res.status_code == 200
        assert res.get_json()["servings"] == 8

    def test_updates_tags(self, client):
        recipe_id = post_recipe(client, tags=["italian"]).get_json()["id"]
        res = put_recipe(client, recipe_id, tags=["vegan", "quick"])
        assert res.status_code == 200
        assert sorted(res.get_json()["tags"]) == ["quick", "vegan"]

    def test_update_tags_replaces_existing(self, client):
        recipe_id = post_recipe(client, tags=["italian", "dinner"]).get_json()["id"]
        put_recipe(client, recipe_id, tags=["breakfast"])
        res = client.get(f"/api/recipes/{recipe_id}").get_json()
        assert res["tags"] == ["breakfast"]

    def test_missing_recipe_returns_404(self, client):
        res = put_recipe(client, 999, servings=8)
        assert res.status_code == 404
        assert res.get_json() == {"error": "Recipe not found"}


class TestDeleteRecipe:
    def test_deletes_recipe_and_returns_204(self, client):
        recipe_id = post_recipe(client).get_json()["id"]
        res = client.delete(f"/api/recipes/{recipe_id}")
        assert res.status_code == 204

        res = client.get(f"/api/recipes/{recipe_id}")
        assert res.status_code == 404

    def test_missing_recipe_returns_404(self, client):
        res = client.delete("/api/recipes/999")
        assert res.status_code == 404
        assert res.get_json() == {"error": "Recipe not found"}


class TestImportRecipeUrl:
    def _post(self, client, body):
        return client.post(
            "/api/recipes/import-url",
            data=json.dumps(body),
            content_type="application/json",
        )

    def test_missing_url_returns_400(self, client):
        res = self._post(client, {})
        assert res.status_code == 400
        assert res.get_json()["error"] == "url is required"

    def test_empty_url_returns_400(self, client):
        res = self._post(client, {"url": "  "})
        assert res.status_code == 400

    def test_scraper_error_returns_422(self, client):
        with patch("routes.api.scrape_recipe", side_effect=ScraperError("timed out")):
            res = self._post(client, {"url": "http://example.com"})
        assert res.status_code == 422
        assert "timed out" in res.get_json()["error"]

    def test_returns_recipe_data_on_success(self, client):
        fake = {
            "title": "Test Soup",
            "description": "A nice soup.",
            "ingredients_text": "1 onion\n2 cups broth",
            "steps": "Chop and simmer.",
            "cook_time_minutes": 25,
            "servings": 4,
            "tags": ["quick", "vegetarian"],
            "warnings": [],
        }
        with patch("routes.api.scrape_recipe", return_value=fake):
            res = self._post(client, {"url": "http://example.com/soup"})
        assert res.status_code == 200
        body = res.get_json()
        assert body["title"] == "Test Soup"
        assert body["cook_time_minutes"] == 25
        assert "quick" in body["tags"]

    def test_partial_result_with_warnings_returns_200(self, client):
        fake = {
            "title": "Partial Recipe",
            "description": None,
            "ingredients_text": None,
            "steps": None,
            "cook_time_minutes": None,
            "servings": None,
            "tags": [],
            "warnings": ["Could not find ingredients.", "Could not find steps."],
        }
        with patch("routes.api.scrape_recipe", return_value=fake):
            res = self._post(client, {"url": "http://example.com/partial"})
        assert res.status_code == 200
        assert len(res.get_json()["warnings"]) == 2
