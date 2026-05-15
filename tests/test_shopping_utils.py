from shopping_utils import parse_line, categorize, aggregate, _fmt_qty


class TestParseLine:
    def test_blank_line_returns_none(self):
        assert parse_line("") is None
        assert parse_line("   ") is None

    def test_bullet_prefix_stripped(self):
        qty, unit, name = parse_line("• 2 cups flour")
        assert qty == 2.0
        assert unit == "cup"
        assert name == "flour"

    def test_qty_unit_name(self):
        qty, unit, name = parse_line("2 cups flour")
        assert qty == 2.0
        assert unit == "cup"
        assert name == "flour"

    def test_unit_aliases_normalised(self):
        _, unit, _ = parse_line("1 tablespoon olive oil")
        assert unit == "tbsp"
        _, unit, _ = parse_line("3 ounces cheese")
        assert unit == "oz"
        _, unit, _ = parse_line("2 pounds chicken")
        assert unit == "lb"

    def test_simple_fraction(self):
        qty, unit, name = parse_line("1/2 tsp salt")
        assert abs(qty - 0.5) < 0.001
        assert unit == "tsp"
        assert name == "salt"

    def test_mixed_fraction(self):
        qty, unit, name = parse_line("1 1/2 cups milk")
        assert abs(qty - 1.5) < 0.001
        assert unit == "cup"
        assert name == "milk"

    def test_qty_only_no_unit(self):
        qty, unit, name = parse_line("3 eggs")
        assert qty == 3.0
        assert unit is None
        assert name == "eggs"

    def test_no_qty_no_unit(self):
        qty, unit, name = parse_line("salt and pepper")
        assert qty is None
        assert unit is None
        assert name == "salt and pepper"

    def test_non_unit_word_stays_in_name(self):
        qty, unit, name = parse_line("2 large eggs")
        assert qty == 2.0
        assert unit is None
        assert "large eggs" in name

    def test_name_lowercased(self):
        _, _, name = parse_line("1 cup All-Purpose Flour")
        assert name == name.lower()


class TestFmtQty:
    def test_none_returns_empty_string(self):
        assert _fmt_qty(None) == ''

    def test_whole_number(self):
        assert _fmt_qty(2.0) == '2'

    def test_half(self):
        assert _fmt_qty(0.5) == '½'

    def test_quarter(self):
        assert _fmt_qty(0.25) == '¼'

    def test_three_quarters(self):
        assert _fmt_qty(0.75) == '¾'

    def test_one_and_a_half(self):
        assert _fmt_qty(1.5) == '1 ½'

    def test_decimal_fallback(self):
        assert _fmt_qty(0.6) == '0.6'


class TestCategorize:
    def test_produce(self):
        assert categorize("garlic cloves") == "Produce"
        assert categorize("cherry tomatoes") == "Produce"

    def test_dairy(self):
        assert categorize("parmesan, grated") == "Dairy & Eggs"
        assert categorize("ricotta cheese") == "Dairy & Eggs"
        assert categorize("eggs") == "Dairy & Eggs"

    def test_meat(self):
        assert categorize("chicken breast") == "Meat & Seafood"
        assert categorize("italian sausage") == "Meat & Seafood"
        assert categorize("pancetta") == "Meat & Seafood"

    def test_grains(self):
        assert categorize("spaghetti") == "Grains & Bread"
        assert categorize("penne pasta") == "Grains & Bread"

    def test_pantry(self):
        assert categorize("olive oil") == "Pantry"
        assert categorize("salt") == "Pantry"

    def test_other(self):
        assert categorize("xanthan gum") == "Other"


class TestAggregate:
    class FakeRecipe:
        def __init__(self, ingredients_text):
            self.ingredients_text = ingredients_text

    def test_empty_list(self):
        assert aggregate([]) == []

    def test_recipe_with_no_ingredients_text(self):
        r = self.FakeRecipe(None)
        assert aggregate([r]) == []

    def test_parses_ingredients(self):
        r = self.FakeRecipe("2 cups flour\n1 tsp salt")
        result = aggregate([r])
        names = [item['ingredient'] for item in result]
        assert 'flour' in names
        assert 'salt' in names

    def test_sums_quantities_across_recipes(self):
        r1 = self.FakeRecipe("2 cups flour")
        r2 = self.FakeRecipe("1 cup flour")
        result = aggregate([r1, r2])
        flour = next(i for i in result if i['ingredient'] == 'flour')
        assert flour['quantity'] == '3'

    def test_units_included_in_output(self):
        r = self.FakeRecipe("1/2 tsp salt")
        result = aggregate([r])
        salt = next(i for i in result if i['ingredient'] == 'salt')
        assert salt['unit'] == 'tsp'
        assert salt['quantity'] == '½'

    def test_ingredient_without_qty(self):
        r = self.FakeRecipe("salt and pepper")
        result = aggregate([r])
        item = next(i for i in result if 'salt' in i['ingredient'])
        assert item['quantity'] == ''

    def test_skips_blank_lines(self):
        r = self.FakeRecipe("2 cups flour\n\n1 tsp salt\n")
        result = aggregate([r])
        assert len(result) == 2

    def test_sorted_by_category_then_name(self):
        r = self.FakeRecipe("1 cup flour\n1 tbsp olive oil\n2 cups broccoli florets")
        result = aggregate([r])
        categories = [i['category'] for i in result]
        assert categories == sorted(categories)
