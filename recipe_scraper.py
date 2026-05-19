"""
Fetch a URL and extract recipe fields from schema.org JSON-LD markup,
with fallbacks to Open Graph meta tags.
"""
import json
import re
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup


class ScraperError(Exception):
    """Raised when a URL cannot be fetched or contains no usable recipe data."""

# Diet schema.org values → simple tag names
_DIET_MAP = {
    "vegetariandiet": "vegetarian",
    "vegandiet": "vegan",
    "glutenfreediet": "gluten-free",
    "dairyfreediet": "dairy-free",
    "lowcaloriediet": "low-calorie",
    "lowfatdiet": "low-fat",
    "lowlactosediet": "low-lactose",
    "lowsaltdiet": "low-salt",
}


# ── ISO 8601 duration parsing ─────────────────────────────────────────────────

def _parse_iso_duration(value):
    """Convert an ISO 8601 duration string to total minutes (int), or None."""
    if not value:
        return None
    m = re.match(
        r'P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?',
        str(value).strip().upper(),
    )
    if not m:
        return None
    days, hours, minutes, seconds = (int(g or 0) for g in m.groups())
    total = days * 1440 + hours * 60 + minutes + (1 if seconds >= 30 else 0)
    return total or None


# ── Instruction extraction ────────────────────────────────────────────────────

def _extract_instructions(instructions):
    """Normalise recipeInstructions to a plain-text block (one step per line)."""
    if not instructions:
        return None
    if isinstance(instructions, str):
        return _strip_html(instructions) or None
    steps = []
    for item in instructions:
        if isinstance(item, str):
            text = _strip_html(item)
        elif isinstance(item, dict):
            text = _strip_html(item.get("text") or item.get("name") or "")
        else:
            continue
        if text:
            steps.append(text)
    return "\n".join(steps) or None


# ── Tag inference ─────────────────────────────────────────────────────────────

def _extract_tags(data, cook_minutes):
    """Build a normalised tag list from schema.org recipe fields."""
    tags = set()

    # recipeCuisine
    cuisine = data.get("recipeCuisine")
    if cuisine:
        for c in (cuisine if isinstance(cuisine, list) else [cuisine]):
            tags.add(c.strip().lower())

    # suitableForDiet
    diets = data.get("suitableForDiet") or []
    if isinstance(diets, str):
        diets = [diets]
    for d in diets:
        # strip namespace prefix e.g. "https://schema.org/VegetarianDiet"
        key = d.strip().split("/")[-1].lower()
        mapped = _DIET_MAP.get(key)
        if mapped:
            tags.add(mapped)

    # keywords
    keywords = data.get("keywords") or ""
    if isinstance(keywords, list):
        keywords = ",".join(keywords)
    for kw in re.split(r"[,;]", keywords):
        kw = kw.strip().lower()
        if kw:
            tags.add(kw)

    # quick inference
    if cook_minutes and cook_minutes <= 30:
        tags.add("quick")

    return sorted(tags)


# ── Servings extraction ───────────────────────────────────────────────────────

def _extract_servings(value):
    """Pull the first integer from a recipeYield value."""
    if value is None:
        return None
    text = " ".join(value) if isinstance(value, list) else str(value)
    m = re.search(r'\d+', text)
    return int(m.group()) if m else None


# ── HTML tag stripping ────────────────────────────────────────────────────────

def _strip_html(text):
    if not text:
        return None
    raw = BeautifulSoup(str(text), "html.parser").get_text()
    return re.sub(r'\s+', ' ', raw).strip() or None


# ── JSON-LD extraction ────────────────────────────────────────────────────────

def _find_recipe_jsonld(soup):
    """Return the first schema.org Recipe object found in JSON-LD blocks, or None."""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue

        # Unwrap @graph arrays
        if isinstance(data, dict) and "@graph" in data:
            candidates = data["@graph"]
        elif isinstance(data, list):
            candidates = data
        else:
            candidates = [data]

        for item in candidates:
            if not isinstance(item, dict):
                continue
            type_val = item.get("@type", "")
            types = type_val if isinstance(type_val, list) else [type_val]
            if any(t.lower().rstrip("/") in ("recipe", "https://schema.org/recipe") for t in types):
                return item

    return None


# ── Meta fallbacks ────────────────────────────────────────────────────────────

def _meta(soup, prop):
    tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
    return (tag.get("content") or "").strip() if tag else None


# ── Image extraction ──────────────────────────────────────────────────────────

def _extract_image_url(data, soup):
    """Return the first usable image URL from JSON-LD or og:image meta tag."""
    img = data.get("image")
    if img:
        if isinstance(img, str):
            return img or None
        if isinstance(img, dict):
            return img.get("url") or img.get("contentUrl") or None
        if isinstance(img, list) and img:
            first = img[0]
            if isinstance(first, str):
                return first or None
            if isinstance(first, dict):
                return first.get("url") or first.get("contentUrl") or None
    return _meta(soup, "og:image") or None


# ── Public API ────────────────────────────────────────────────────────────────

def scrape_recipe(url, timeout=15):
    """
    Fetch *url* and extract recipe fields.

    Returns a dict:
        title, description, ingredients_text, steps,
        cook_time_minutes, servings, tags, warnings

    Raises ScraperError on network failure or HTTP error.
    """
    try:
        resp = cffi_requests.get(url, impersonate="chrome124", timeout=timeout)
        resp.raise_for_status()
    except Exception as e:
        msg = str(e)
        if "timed out" in msg.lower() or "timeout" in msg.lower():
            raise ScraperError("The request timed out — the site may be too slow to import from.")
        if "connection" in msg.lower():
            raise ScraperError("Could not connect to that URL — check the address and try again.")
        status = getattr(getattr(e, "response", None), "status_code", None)
        if status:
            raise ScraperError(f"The site returned an error ({status}) — it may block automated access.")
        raise ScraperError("Could not fetch that URL.")

    soup = BeautifulSoup(resp.text, "html.parser")
    warnings = []

    data = _find_recipe_jsonld(soup)

    if data:
        title = _strip_html(data.get("name"))
        description = _strip_html(data.get("description"))

        ingredients = data.get("recipeIngredient") or []
        ingredients_text = "\n".join(
            _strip_html(i) for i in ingredients if _strip_html(i)
        ) or None

        steps = _extract_instructions(data.get("recipeInstructions"))

        duration = data.get("totalTime") or data.get("cookTime")
        cook_minutes = _parse_iso_duration(duration)

        servings = _extract_servings(data.get("recipeYield"))
        tags = _extract_tags(data, cook_minutes)
        image_url = _extract_image_url(data, soup)

        if not title:
            warnings.append("Could not find recipe title.")
        if not ingredients_text:
            warnings.append("Could not find ingredients.")
        if not steps:
            warnings.append("Could not find recipe steps.")
        if cook_minutes is None:
            warnings.append("Could not find cook time.")

    else:
        # No JSON-LD — fall back to meta tags for title/description only
        warnings.append("No structured recipe data found on this page — only basic details were imported.")
        title = (
            _meta(soup, "og:title")
            or _meta(soup, "twitter:title")
            or (soup.title.string.strip() if soup.title else None)
        )
        description = _meta(soup, "og:description") or _meta(soup, "twitter:description")
        ingredients_text = None
        steps = None
        cook_minutes = None
        servings = None
        tags = []
        image_url = _meta(soup, "og:image") or None

    return {
        "title": title,
        "description": description,
        "ingredients_text": ingredients_text,
        "steps": steps,
        "cook_time_minutes": cook_minutes,
        "servings": servings,
        "tags": tags,
        "image_url": image_url,
        "warnings": warnings,
    }
