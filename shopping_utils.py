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

    # qty + name only
    m = re.match(r'^(\d[\d ./]*?)\s+(.+)$', line)
    if m:
        qty_s, rest = m.group(1).strip(), m.group(2).strip()
        try:
            qty = _parse_qty(qty_s)
        except (ValueError, ZeroDivisionError):
            qty = None
        return qty, None, rest.lower()

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
    """
    totals = defaultdict(lambda: {'qty': None, 'unit': None})

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
            bucket = totals[(name, unit or '')]
            bucket['unit'] = unit
            if qty is not None:
                bucket['qty'] = (bucket['qty'] or 0) + qty

    result = [
        {
            'ingredient': name,
            'quantity': _fmt_qty(data['qty']),
            'unit': data['unit'] or '',
            'category': categorize(name),
        }
        for (name, _unit), data in totals.items()
    ]
    result.sort(key=lambda x: (x['category'], x['ingredient']))
    return result
