import json


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
