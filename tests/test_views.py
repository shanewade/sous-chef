import json


def create_recipe(client, **kwargs):
    data = {"title": "Test Recipe", **kwargs}
    return client.post("/api/recipes", data=json.dumps(data), content_type="application/json")


class TestRecipesIndex:
    def test_returns_200(self, client):
        res = client.get("/recipes")
        assert res.status_code == 200

    def test_shows_recipe_titles(self, client):
        create_recipe(client, title="Pasta Carbonara")
        res = client.get("/recipes")
        assert b"Pasta Carbonara" in res.data

    def test_shows_new_recipe_button(self, client):
        res = client.get("/recipes")
        assert b"/recipes/new" in res.data

    def test_shows_empty_state_when_no_recipes(self, client):
        res = client.get("/recipes")
        assert b"No recipes yet" in res.data


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
