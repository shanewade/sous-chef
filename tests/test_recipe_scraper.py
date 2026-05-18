"""Unit tests for recipe_scraper.py — no real HTTP calls."""
import json
from unittest.mock import patch, MagicMock

import pytest

from recipe_scraper import (
    scrape_recipe, ScraperError,
    _parse_iso_duration, _extract_instructions, _extract_tags,
    _extract_servings, _find_recipe_jsonld, _strip_html,
)
from bs4 import BeautifulSoup


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_html(jsonld=None, og_title=None, og_description=None, page_title=None):
    """Build a minimal HTML page with optional JSON-LD and meta tags."""
    metas = ""
    if og_title:
        metas += f'<meta property="og:title" content="{og_title}">'
    if og_description:
        metas += f'<meta property="og:description" content="{og_description}">'

    ld = ""
    if jsonld:
        ld = f'<script type="application/ld+json">{json.dumps(jsonld)}</script>'

    title_tag = f"<title>{page_title}</title>" if page_title else ""

    return f"<html><head>{title_tag}{metas}{ld}</head><body></body></html>"


FULL_JSONLD = {
    "@context": "https://schema.org",
    "@type": "Recipe",
    "name": "Spaghetti Carbonara",
    "description": "A classic Roman pasta dish.",
    "recipeIngredient": ["400g spaghetti", "200g pancetta", "4 eggs"],
    "recipeInstructions": [
        {"@type": "HowToStep", "text": "Boil pasta."},
        {"@type": "HowToStep", "text": "Fry pancetta."},
        {"@type": "HowToStep", "text": "Combine and serve."},
    ],
    "totalTime": "PT35M",
    "recipeYield": "4 servings",
    "recipeCuisine": "Italian",
    "suitableForDiet": "https://schema.org/GlutenFreeDiet",
    "keywords": "pasta, quick dinner",
}


# ── _parse_iso_duration ───────────────────────────────────────────────────────

class TestParseIsoDuration:
    def test_minutes_only(self):
        assert _parse_iso_duration("PT30M") == 30

    def test_hours_and_minutes(self):
        assert _parse_iso_duration("PT1H30M") == 90

    def test_hours_only(self):
        assert _parse_iso_duration("PT2H") == 120

    def test_days_and_hours(self):
        assert _parse_iso_duration("P1DT2H") == 1560  # 1440 + 120

    def test_none_input(self):
        assert _parse_iso_duration(None) is None

    def test_invalid_string(self):
        assert _parse_iso_duration("not-a-duration") is None


# ── _extract_instructions ─────────────────────────────────────────────────────

class TestExtractInstructions:
    def test_string_passthrough(self):
        assert _extract_instructions("Mix well.") == "Mix well."

    def test_list_of_strings(self):
        result = _extract_instructions(["Step 1.", "Step 2."])
        assert result == "Step 1.\nStep 2."

    def test_howto_step_objects(self):
        steps = [{"@type": "HowToStep", "text": "Boil water."}, {"@type": "HowToStep", "text": "Add pasta."}]
        result = _extract_instructions(steps)
        assert result == "Boil water.\nAdd pasta."

    def test_none_input(self):
        assert _extract_instructions(None) is None

    def test_empty_list(self):
        assert _extract_instructions([]) is None

    def test_decodes_html_entities_in_steps(self):
        steps = [{"@type": "HowToStep", "text": "Use an 8&#215;4-inch pan and don&#8217;t over-mix."}]
        result = _extract_instructions(steps)
        assert "×" in result
        assert "’" in result  # right single quotation mark
        assert "&#" not in result

    def test_decodes_html_entities_in_string_step(self):
        result = _extract_instructions("Bake at 350&#176;F.")
        assert "°" in result
        assert "&#" not in result


# ── _extract_servings ─────────────────────────────────────────────────────────

class TestExtractServings:
    def test_plain_integer_string(self):
        assert _extract_servings("4") == 4

    def test_string_with_word(self):
        assert _extract_servings("4 servings") == 4

    def test_list_input(self):
        assert _extract_servings(["2-4 servings"]) == 2

    def test_none_input(self):
        assert _extract_servings(None) is None

    def test_no_digits(self):
        assert _extract_servings("a few") is None


# ── _extract_tags ─────────────────────────────────────────────────────────────

class TestExtractTags:
    def test_cuisine_tag(self):
        tags = _extract_tags({"recipeCuisine": "Italian"}, None)
        assert "italian" in tags

    def test_diet_normalised(self):
        tags = _extract_tags({"suitableForDiet": "https://schema.org/VegetarianDiet"}, None)
        assert "vegetarian" in tags

    def test_keywords_split_on_comma(self):
        tags = _extract_tags({"keywords": "pasta, quick dinner"}, None)
        assert "pasta" in tags
        assert "quick dinner" in tags

    def test_quick_inferred_for_short_cook_time(self):
        tags = _extract_tags({}, 25)
        assert "quick" in tags

    def test_quick_not_inferred_for_long_cook_time(self):
        tags = _extract_tags({}, 90)
        assert "quick" not in tags

    def test_keywords_as_list(self):
        tags = _extract_tags({"keywords": ["soup", "comfort food"]}, None)
        assert "soup" in tags
        assert "comfort food" in tags

    def test_unknown_diet_ignored(self):
        tags = _extract_tags({"suitableForDiet": "https://schema.org/UnknownDiet"}, None)
        assert len(tags) == 0


# ── _find_recipe_jsonld ───────────────────────────────────────────────────────

class TestFindRecipeJsonld:
    def test_finds_recipe_type(self):
        html = _make_html(jsonld={"@type": "Recipe", "name": "Test"})
        soup = BeautifulSoup(html, "html.parser")
        data = _find_recipe_jsonld(soup)
        assert data is not None
        assert data["name"] == "Test"

    def test_finds_recipe_in_graph(self):
        ld = {"@graph": [{"@type": "WebPage"}, {"@type": "Recipe", "name": "Graph Recipe"}]}
        html = _make_html(jsonld=ld)
        soup = BeautifulSoup(html, "html.parser")
        data = _find_recipe_jsonld(soup)
        assert data["name"] == "Graph Recipe"

    def test_returns_none_when_no_recipe(self):
        html = _make_html(jsonld={"@type": "Article", "name": "Not a recipe"})
        soup = BeautifulSoup(html, "html.parser")
        assert _find_recipe_jsonld(soup) is None

    def test_returns_none_when_no_jsonld(self):
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        assert _find_recipe_jsonld(soup) is None

    def test_handles_malformed_json_gracefully(self):
        html = '<html><head><script type="application/ld+json">{bad json}</script></head></html>'
        soup = BeautifulSoup(html, "html.parser")
        assert _find_recipe_jsonld(soup) is None

    def test_finds_recipe_in_top_level_list(self):
        ld = [{"@type": "WebSite"}, {"@type": "Recipe", "name": "List Recipe"}]
        html = _make_html(jsonld=ld)
        soup = BeautifulSoup(html, "html.parser")
        data = _find_recipe_jsonld(soup)
        assert data["name"] == "List Recipe"

    def test_skips_non_dict_items_in_list(self):
        ld = ["not a dict", {"@type": "Recipe", "name": "Valid"}]
        html = _make_html(jsonld=ld)
        soup = BeautifulSoup(html, "html.parser")
        data = _find_recipe_jsonld(soup)
        assert data["name"] == "Valid"


# ── _strip_html ───────────────────────────────────────────────────────────────

class TestStripHtml:
    def test_strips_tags(self):
        result = _strip_html("<p>Hello <b>world</b></p>")
        assert result == "Hello world"

    def test_plain_text_unchanged(self):
        assert _strip_html("plain text") == "plain text"

    def test_none_returns_none(self):
        assert _strip_html(None) is None


# ── scrape_recipe (integration, mocked HTTP) ──────────────────────────────────

def _mock_response(html, status=200):
    mock = MagicMock()
    mock.text = html
    mock.status_code = status
    mock.raise_for_status = MagicMock()
    return mock


def _mock_scraper(response=None, side_effect=None):
    """Return a mock for cloudscraper.create_scraper() that returns a scraper
    whose .get() returns *response* or raises *side_effect*."""
    mock_session = MagicMock()
    if side_effect is not None:
        mock_session.get.side_effect = side_effect
    else:
        mock_session.get.return_value = response
    return MagicMock(return_value=mock_session)


_PATCH = "recipe_scraper.cloudscraper.create_scraper"


class TestScrapeRecipe:
    def test_extracts_full_recipe_from_jsonld(self):
        html = _make_html(jsonld=FULL_JSONLD)
        with patch(_PATCH, _mock_scraper(_mock_response(html))):
            result = scrape_recipe("http://example.com/recipe")
        assert result["title"] == "Spaghetti Carbonara"
        assert result["description"] == "A classic Roman pasta dish."
        assert "400g spaghetti" in result["ingredients_text"]
        assert "Boil pasta." in result["steps"]
        assert result["cook_time_minutes"] == 35
        assert result["servings"] == 4
        assert "italian" in result["tags"]
        assert "gluten-free" in result["tags"]

    def test_infers_quick_tag(self):
        ld = {**FULL_JSONLD, "totalTime": "PT20M"}
        html = _make_html(jsonld=ld)
        with patch(_PATCH, _mock_scraper(_mock_response(html))):
            result = scrape_recipe("http://example.com/recipe")
        assert "quick" in result["tags"]

    def test_falls_back_to_og_tags_when_no_jsonld(self):
        html = _make_html(og_title="No-Schema Recipe", og_description="A simple dish.")
        with patch(_PATCH, _mock_scraper(_mock_response(html))):
            result = scrape_recipe("http://example.com/recipe")
        assert result["title"] == "No-Schema Recipe"
        assert result["description"] == "A simple dish."
        assert result["ingredients_text"] is None
        assert len(result["warnings"]) > 0

    def test_falls_back_to_page_title(self):
        html = _make_html(page_title="My Delicious Soup")
        with patch(_PATCH, _mock_scraper(_mock_response(html))):
            result = scrape_recipe("http://example.com/recipe")
        assert result["title"] == "My Delicious Soup"

    def test_partial_jsonld_adds_warnings(self):
        ld = {"@type": "Recipe", "name": "Partial Recipe"}
        html = _make_html(jsonld=ld)
        with patch(_PATCH, _mock_scraper(_mock_response(html))):
            result = scrape_recipe("http://example.com/recipe")
        assert result["title"] == "Partial Recipe"
        assert len(result["warnings"]) > 0

    def test_raises_scraper_error_on_connection_error(self):
        import requests as req
        with patch(_PATCH, _mock_scraper(side_effect=req.exceptions.ConnectionError)):
            with pytest.raises(ScraperError, match="Could not connect"):
                scrape_recipe("http://bad-url.example.com")

    def test_raises_scraper_error_on_timeout(self):
        import requests as req
        with patch(_PATCH, _mock_scraper(side_effect=req.exceptions.Timeout)):
            with pytest.raises(ScraperError, match="timed out"):
                scrape_recipe("http://slow.example.com")

    def test_raises_scraper_error_on_http_error(self):
        import requests as req
        mock = _mock_response("", status=404)
        mock.raise_for_status.side_effect = req.exceptions.HTTPError(response=mock)
        with patch(_PATCH, _mock_scraper(mock)):
            with pytest.raises(ScraperError, match="404"):
                scrape_recipe("http://example.com/notfound")

    def test_raises_scraper_error_on_generic_request_exception(self):
        import requests as req
        with patch(_PATCH, _mock_scraper(side_effect=req.exceptions.RequestException)):
            with pytest.raises(ScraperError, match="Could not fetch"):
                scrape_recipe("http://example.com")

    def test_warns_when_title_missing_from_jsonld(self):
        ld = {"@type": "Recipe", "recipeIngredient": ["1 egg"]}
        html = _make_html(jsonld=ld)
        with patch(_PATCH, _mock_scraper(_mock_response(html))):
            result = scrape_recipe("http://example.com/recipe")
        warnings_text = " ".join(result["warnings"])
        assert "title" in warnings_text.lower()
