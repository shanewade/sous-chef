from shopping_utils import parse_line, categorize, aggregate, _fmt_qty, _normalize_name


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

    def test_no_space_between_qty_and_unit(self):
        qty, unit, name = parse_line("100g parmesan, grated")
        assert qty == 100.0
        assert unit == "g"
        assert name == "parmesan, grated"

    def test_no_space_qty_unit_ml(self):
        qty, unit, name = parse_line("500ml coconut milk")
        assert qty == 500.0
        assert unit == "ml"
        assert name == "coconut milk"

    def test_division_by_zero_qty_with_unit_returns_none_qty(self):
        qty, unit, name = parse_line("1/0 cups flour")
        assert qty is None
        assert unit == "cup"
        assert name == "flour"

    def test_division_by_zero_qty_without_unit_returns_none_qty(self):
        qty, unit, name = parse_line("1/0 eggs")
        assert qty is None
        assert unit is None
        assert name == "eggs"


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
        assert categorize("red bell pepper") == "Produce"
        assert categorize("jalapeño") == "Produce"

    def test_pepper_spice_is_pantry(self):
        assert categorize("pepper") == "Pantry"
        assert categorize("black pepper") == "Pantry"
        assert categorize("red pepper flakes") == "Pantry"

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


class TestExpandIngredient:
    def test_splits_salt_and_pepper(self):
        from shopping_utils import _expand_ingredient
        result = _expand_ingredient(None, None, "salt and pepper to taste")
        assert result == [(None, None, "salt"), (None, None, "pepper")]

    def test_splits_salt_and_black_pepper(self):
        from shopping_utils import _expand_ingredient
        result = _expand_ingredient(None, None, "salt and black pepper to taste")
        assert result == [(None, None, "salt"), (None, None, "black pepper")]

    def test_strips_to_taste_without_splitting(self):
        from shopping_utils import _expand_ingredient
        result = _expand_ingredient(None, None, "salt to taste")
        assert result == [(None, None, "salt")]

    def test_strips_as_needed(self):
        from shopping_utils import _expand_ingredient
        result = _expand_ingredient(None, None, "olive oil as needed")
        assert result == [(None, None, "olive oil")]

    def test_does_not_split_when_qty_present(self):
        from shopping_utils import _expand_ingredient
        # "bread and butter" with a quantity should stay together
        result = _expand_ingredient(1.0, "cup", "bread and butter")
        assert len(result) == 1


class TestNormalizeName:
    def test_strips_comma_modifier(self):
        assert _normalize_name("butter, softened") == "butter"

    def test_strips_prefix_modifier(self):
        assert _normalize_name("unsalted butter") == "butter"

    def test_strips_parenthetical(self):
        assert _normalize_name("chicken (about 500g)") == "chicken"

    def test_leaves_plain_name_unchanged(self):
        assert _normalize_name("olive oil") == "olive oil"

    def test_multiple_modifiers(self):
        assert _normalize_name("boneless skinless chicken breast") == "chicken breast"


class TestAggregateDedup:
    class FakeRecipe:
        def __init__(self, ingredients_text):
            self.ingredients_text = ingredients_text

    def test_combines_different_volume_units(self):
        r1 = self.FakeRecipe("2 tbsp butter")
        r2 = self.FakeRecipe("1/4 cup butter")
        result = aggregate([r1, r2])
        butter = next(i for i in result if 'butter' in i['ingredient'])
        # 2 tbsp = 6 tsp, 1/4 cup = 12 tsp → 18 tsp = 6 tbsp
        assert butter['unit'] == 'tbsp'
        assert butter['quantity'] == '6'

    def test_combines_different_weight_units(self):
        r1 = self.FakeRecipe("100 g chicken breast")
        r2 = self.FakeRecipe("200 g chicken breast")
        result = aggregate([r1, r2])
        chicken = next(i for i in result if 'chicken' in i['ingredient'])
        assert chicken['unit'] == 'g'
        assert chicken['quantity'] == '300'

    def test_normalises_modifier_words(self):
        r1 = self.FakeRecipe("2 tbsp unsalted butter")
        r2 = self.FakeRecipe("1 tbsp butter")
        result = aggregate([r1, r2])
        butter_items = [i for i in result if 'butter' in i['ingredient']]
        assert len(butter_items) == 1
        assert butter_items[0]['quantity'] == '3'

    def test_comma_modifier_normalised(self):
        r1 = self.FakeRecipe("2 tbsp butter, softened")
        r2 = self.FakeRecipe("1 tbsp butter")
        result = aggregate([r1, r2])
        butter_items = [i for i in result if 'butter' in i['ingredient']]
        assert len(butter_items) == 1

    def test_display_name_uses_shortest_form(self):
        r1 = self.FakeRecipe("2 tbsp unsalted butter")
        r2 = self.FakeRecipe("1 tbsp butter")
        result = aggregate([r1, r2])
        butter = next(i for i in result if 'butter' in i['ingredient'])
        assert butter['ingredient'] == 'butter'

    def test_incompatible_units_kept_separate(self):
        # cloves of garlic vs tbsp garlic powder — different families
        r = self.FakeRecipe("3 cloves garlic\n1 tbsp garlic powder")
        result = aggregate([r])
        garlic_items = [i for i in result if 'garlic' in i['ingredient']]
        assert len(garlic_items) == 2

    def test_no_quantity_ingredient_appears_once(self):
        r1 = self.FakeRecipe("salt to taste")
        r2 = self.FakeRecipe("salt to taste")
        result = aggregate([r1, r2])
        salt_items = [i for i in result if 'salt' in i['ingredient']]
        assert len(salt_items) == 1

    def test_oz_to_lb_conversion(self):
        r1 = self.FakeRecipe("8 oz chicken")
        r2 = self.FakeRecipe("8 oz chicken")
        result = aggregate([r1, r2])
        chicken = next(i for i in result if 'chicken' in i['ingredient'])
        # 16 oz = 1 lb
        assert chicken['unit'] == 'lb'
        assert chicken['quantity'] == '1'

    def test_combines_no_space_weight_format(self):
        r1 = self.FakeRecipe("50g parmesan, finely grated")
        r2 = self.FakeRecipe("60g parmesan, grated")
        result = aggregate([r1, r2])
        parmesan_items = [i for i in result if 'parmesan' in i['ingredient']]
        assert len(parmesan_items) == 1
        assert parmesan_items[0]['quantity'] == '110'
        assert parmesan_items[0]['unit'] == 'g'

    def test_salt_and_pepper_variants_produce_two_items(self):
        r1 = self.FakeRecipe("salt and black pepper to taste")
        r2 = self.FakeRecipe("salt and pepper to taste")
        result = aggregate([r1, r2])
        names = [i['ingredient'] for i in result]
        assert len(result) == 2
        assert any('salt' in n for n in names)
        assert any('pepper' in n for n in names)

    def test_to_taste_stripped_from_display_name(self):
        r = self.FakeRecipe("salt to taste")
        result = aggregate([r])
        assert result[0]['ingredient'] == 'salt'

    def test_metric_volume_stays_metric(self):
        r1 = self.FakeRecipe("200 ml milk")
        r2 = self.FakeRecipe("100 ml milk")
        result = aggregate([r1, r2])
        milk = next(i for i in result if 'milk' in i['ingredient'])
        assert milk['unit'] == 'ml'
        assert milk['quantity'] == '300'
