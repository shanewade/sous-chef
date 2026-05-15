import json


def post_recipe(client, **kwargs):
    data = {"title": "Test Recipe", **kwargs}
    return client.post("/api/recipes", data=json.dumps(data), content_type="application/json")


class TestGetRecipes:
    def test_returns_empty_list_initially(self, client):
        res = client.get("/api/recipes")
        assert res.status_code == 200
        assert res.get_json() == []


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


class TestGetRecipe:
    def test_returns_recipe(self, client):
        recipe_id = post_recipe(client).get_json()["id"]
        res = client.get(f"/api/recipes/{recipe_id}")
        assert res.status_code == 200
        assert res.get_json()["title"] == "Test Recipe"

    def test_missing_recipe_returns_404(self, client):
        res = client.get("/api/recipes/999")
        assert res.status_code == 404
        assert res.get_json() == {"error": "Recipe not found"}


class TestUpdateRecipe:
    def test_updates_single_field(self, client):
        recipe_id = post_recipe(client).get_json()["id"]
        res = client.put(
            f"/api/recipes/{recipe_id}",
            data=json.dumps({"servings": 8}),
            content_type="application/json",
        )
        assert res.status_code == 200
        assert res.get_json()["servings"] == 8

    def test_missing_recipe_returns_404(self, client):
        res = client.put(
            "/api/recipes/999",
            data=json.dumps({"servings": 8}),
            content_type="application/json",
        )
        assert res.status_code == 404
        assert res.get_json() == {"error": "Recipe not found"}


class TestDeleteRecipe:
    def test_deletes_recipe_and_returns_204(self, client):
        recipe_id = post_recipe(client).get_json()["id"]
        res = client.delete(f"/api/recipes/{recipe_id}")
        assert res.status_code == 204

        res = client.get(f"/api/recipes/{recipe_id}")
        assert res.status_code == 404
