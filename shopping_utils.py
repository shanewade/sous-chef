import re
from collections import defaultdict

# Canonical unit names keyed by every alias we recognise.
_UNITS = {
    'cup': 'cup', 'cups': 'cup',
    'tbsp': 'tbsp', 'tablespoon': 'tbsp', 'tablespoons': 'tbsp',
    'tsp': 'tsp', 'teaspoon': 'tsp', 'teaspoons': 'tsp',
    'oz': 'oz', 'ounce': 'oz', 'ounces': 'oz',
    'lb': 'lb', 'lbs': 'lb', 'pound': 'lb', 'pounds': 'lb',
    'g': 'g', 'gram': 'g', 'grams': 'g',
    'kg': 'kg', 'kilogram': 'kg', 'kilograms': 'kg',
    'ml': 'ml', 'l': 'l', 'liter': 'l', 'liters': 'l', 'litre': 'l',
    'clove': 'clove', 'cloves': 'clove',
    'can': 'can', 'cans': 'can',
    'slice': 'slice', 'slices': 'slice',
    'bunch': 'bunch', 'bunches': 'bunch',
    'piece': 'piece', 'pieces': 'piece',
    'stick': 'stick', 'sticks': 'stick',
    'head': 'head', 'heads': 'head',
    'sprig': 'sprig', 'sprigs': 'sprig',
    'pinch': 'pinch', 'pinches': 'pinch',
    'pkg': 'pkg', 'package': 'pkg', 'packages': 'pkg',
}

# ── Unit conversion ────────────────────────────────────────────────────────────
# Volume: base unit is tsp
_VOLUME_TO_TSP = {
    'tsp':  1.0,
    'tbsp': 3.0,
    'cup':  48.0,
    'ml':   1.0 / 4.92892,
    'l':    1000.0 / 4.92892,
    'stick': 24.0,   # 1 stick butter = 8 tbsp = 24 tsp
}

# Weight: base unit is g
_WEIGHT_TO_G = {
    'g':  1.0,
    'kg': 1000.0,
    'oz': 28.3495,
    'lb': 453.592,
}

def _unit_family(unit):
    """Return 'volume', 'weight', or None for count/unknown units."""
    if unit in _VOLUME_TO_TSP:
        return 'volume'
    if unit in _WEIGHT_TO_G:
        return 'weight'
    return None


def _to_base(qty, unit):
    """Convert qty+unit to (base_qty, family). Returns (None, None) if not convertible."""
    if unit in _VOLUME_TO_TSP:
        return qty * _VOLUME_TO_TSP[unit], 'volume'
    if unit in _WEIGHT_TO_G:
        return qty * _WEIGHT_TO_G[unit], 'weight'
    return None, None


def _from_base(base_qty, family, source_units):
    """Convert base quantity back to a human-friendly (qty, unit) pair."""
    if family == 'volume':
        use_metric = (
            any(u in ('ml', 'l') for u in source_units)
            and not any(u in ('tsp', 'tbsp', 'cup', 'stick') for u in source_units)
        )
        if use_metric:
            ml = round(base_qty * 4.92892)   # round to nearest ml
            return (ml / 1000, 'l') if ml >= 1000 else (ml, 'ml')
        if base_qty >= 48:
            return base_qty / 48, 'cup'
        if base_qty >= 3:
            return base_qty / 3, 'tbsp'
        return base_qty, 'tsp'
    else:  # weight
        use_metric = (
            any(u in ('g', 'kg') for u in source_units)
            and not any(u in ('oz', 'lb') for u in source_units)
        )
        if use_metric:
            g = round(base_qty)              # round to nearest gram
            return (g / 1000, 'kg') if g >= 1000 else (g, 'g')
        oz = base_qty / 28.3495
        return (oz / 16, 'lb') if oz >= 16 else (oz, 'oz')


# ── Name normalisation ─────────────────────────────────────────────────────────
_MODIFIERS = frozenset({
    'unsalted', 'salted', 'softened', 'melted', 'chopped', 'diced', 'minced',
    'sliced', 'grated', 'shredded', 'crushed', 'peeled', 'trimmed', 'deveined',
    'fresh', 'dried', 'frozen', 'canned', 'cooked', 'raw', 'ripe',
    'large', 'medium', 'small', 'extra',
    'whole', 'halved', 'quartered',
    'roughly', 'finely', 'thinly', 'lightly', 'loosely', 'packed',
    'boneless', 'skinless', 'lean', 'ground',
    'room', 'temperature', 'cold', 'warm',
    'heaping', 'level', 'about', 'and',
})


def _normalize_name(name):
    """Return a canonical grouping key for an ingredient name.

    Strips parenthetical notes, comma-separated modifiers, and known
    modifier words so that e.g. 'unsalted butter' and 'butter, softened'
    both resolve to 'butter'.
    """
    name = re.sub(r'\(.*?\)', '', name)       # drop "(optional)", "(about 200g)", etc.
    name = name.split(',')[0]                  # "butter, softened" → "butter"
    words = [w for w in name.split() if w not in _MODIFIERS]
    return ' '.join(words).strip() or name.strip()


# ── Quantity / unit formatting ────────────────────────────────────────────────
# (category, keywords) — first match wins.
_CATEGORIES = [
    ('Produce',          ['lettuce', 'tomato', 'onion', 'garlic', 'carrot', 'potato',
                          'pepper', 'celery', 'broccoli', 'spinach', 'mushroom', 'lemon',
                          'lime', 'orange', 'apple', 'avocado', 'zucchini', 'cucumber',
                          'kale', 'cabbage', 'ginger', 'parsley', 'cilantro', 'basil',
                          'thyme', 'rosemary', 'scallion', 'shallot', 'leek', 'herb',
                          'bean', 'pea', 'corn', 'squash', 'eggplant', 'artichoke']),
    ('Dairy & Eggs',     ['milk', 'cream', 'butter', 'cheese', 'yogurt', 'egg',
                          'parmesan', 'pecorino', 'mozzarella', 'cheddar', 'ricotta',
                          'sour cream', 'brie', 'gouda', 'feta']),
    ('Meat & Seafood',   ['chicken', 'beef', 'pork', 'turkey', 'salmon', 'shrimp',
                          'fish', 'lamb', 'bacon', 'sausage', 'ham', 'tuna', 'crab',
                          'anchovy', 'pancetta', 'prosciutto', 'steak', 'mince']),
    ('Grains & Bread',   ['flour', 'bread', 'pasta', 'rice', 'oat', 'noodle',
                          'tortilla', 'spaghetti', 'penne', 'fettuccine', 'quinoa',
                          'couscous', 'barley', 'panko', 'breadcrumb', 'cracker']),
    ('Pantry',           ['oil', 'vinegar', 'soy sauce', 'fish sauce', 'broth', 'stock',
                          'tomato', 'coconut milk', 'honey', 'maple', 'sugar', 'salt',
                          'pepper', 'cumin', 'paprika', 'oregano', 'cinnamon', 'turmeric',
                          'curry', 'chili', 'cayenne', 'nutmeg', 'vanilla', 'baking',
                          'mustard', 'ketchup', 'hot sauce', 'worcestershire']),
]


def _parse_qty(s):
    s = s.strip()
    if ' ' in s:                        # "1 1/2"
        whole, frac = s.split(None, 1)
        n, d = frac.split('/')
        return float(whole) + float(n) / float(d)
    if '/' in s:                        # "1/2"
        n, d = s.split('/')
        return float(n) / float(d)
    return float(s)


# Matches: optional_qty  optional_unit  ingredient_name
_LINE_RE = re.compile(
    r'^(?:(\d[\d\s/]*?)\s+)?'   # group 1: quantity (lazy)
    r'([a-zA-Z]+\.?)?\s+'       # group 2: possible unit word
    r'(.+)$'                    # group 3: rest
)


def parse_line(line):
    """Return (qty_float|None, unit_str|None, name_str) or None if blank."""
    line = line.strip().lstrip('•·-–*').strip()
    if not line:
        return None

    # Full pattern: qty + word + rest
    m = re.match(
        r'^(\d[\d ./]*?)\s+([a-zA-Z]+\.?)\s+(.+)$', line
    )
    if m:
        qty_s, word, rest = m.group(1).strip(), m.group(2), m.group(3).strip()
        unit = _UNITS.get(word.lower().rstrip('.'))
        try:
            qty = _parse_qty(qty_s)
        except (ValueError, ZeroDivisionError):
            qty = None
        if unit:
            return qty, unit, rest.lower()
        # word not a unit — treat as part of the name
        return qty, None, f"{word} {rest}".lower()

    # qty + name only (space-separated, no unit)
    m = re.match(r'^(\d[\d ./]*?)\s+(.+)$', line)
    if m:
        qty_s, rest = m.group(1).strip(), m.group(2).strip()
        try:
            qty = _parse_qty(qty_s)
        except (ValueError, ZeroDivisionError):
            qty = None
        return qty, None, rest.lower()

    # qty+unit with no space, e.g. "100g flour", "500ml milk", "1kg chicken"
    m = re.match(r'^(\d[\d./]*)\s*([a-zA-Z]+)\s+(.+)$', line)
    if m:
        qty_s, word, rest = m.group(1), m.group(2), m.group(3).strip()
        unit = _UNITS.get(word.lower())
        try:
            qty = _parse_qty(qty_s)
        except (ValueError, ZeroDivisionError):
            qty = None
        if unit:
            return qty, unit, rest.lower()
        return qty, None, f"{word} {rest}".lower()

    return None, None, line.lower()


def _fmt_qty(qty):
    if qty is None:
        return ''
    FRACS = [(0.25, '¼'), (0.5, '½'), (0.75, '¾'), (0.33, '⅓'), (0.67, '⅔')]
    whole = int(qty)
    frac = qty - whole
    for val, sym in FRACS:
        if abs(frac - val) < 0.04:
            return (f"{whole} " if whole else '') + sym
    if abs(frac) < 0.01:
        return str(whole)
    return f"{qty:.1f}"


def categorize(name):
    lower = name.lower()
    for category, keywords in _CATEGORIES:
        if any(kw in lower for kw in keywords):
            return category
    return 'Other'


def aggregate(recipes):
    """
    Given an iterable of Recipe objects return a list of dicts:
      {ingredient, quantity, unit, category}
    sorted by category then ingredient name.

    Ingredients with the same normalised name are merged across unit
    families (volume or weight) using conversion to a common base unit.
    Name modifiers (unsalted, chopped, softened, etc.) are stripped
    before grouping so that e.g. 'butter' and 'unsalted butter' combine.
    """
    # groups keyed by (normalised_name, family_or_exact_unit)
    # each value: { base_qty, family, source_units, raw_names, unit }
    groups = {}

    for recipe in recipes:
        if not recipe.ingredients_text:
            continue
        for line in recipe.ingredients_text.splitlines():
            parsed = parse_line(line)
            if parsed is None:
                continue
            qty, unit, name = parsed
            if not name:
                continue

            norm = _normalize_name(name)
            family = _unit_family(unit) if unit else None

            # Group convertible units by family; count/no-unit by exact unit
            group_key = (norm, family if family else unit)

            if group_key not in groups:
                groups[group_key] = {
                    'base_qty': None,
                    'family': family,
                    'source_units': set(),
                    'raw_names': [],
                    'unit': unit,
                }

            g = groups[group_key]
            g['raw_names'].append(name)

            if qty is not None:
                if family:
                    base, _ = _to_base(qty, unit)
                    g['base_qty'] = (g['base_qty'] or 0.0) + base
                    g['source_units'].add(unit)
                else:
                    # Count unit (e.g. eggs, cloves) or no unit — sum directly
                    g['base_qty'] = (g['base_qty'] or 0.0) + qty
                    if unit:
                        g['source_units'].add(unit)

    result = []
    for (norm, _), g in groups.items():
        # Use the shortest raw name as the display name (most concise form)
        display_name = min(g['raw_names'], key=len)

        if g['family'] and g['base_qty'] is not None:
            disp_qty, disp_unit = _from_base(g['base_qty'], g['family'], g['source_units'])
        else:
            disp_qty = g['base_qty']
            disp_unit = g['unit']

        result.append({
            'ingredient': display_name,
            'quantity': _fmt_qty(disp_qty),
            'unit': disp_unit or '',
            'category': categorize(display_name),
        })

    result.sort(key=lambda x: (x['category'], x['ingredient']))
    return result
