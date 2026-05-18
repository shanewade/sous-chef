"""
Clears the database and inserts 10 real recipes.
Run with: python seed.py
"""
import app as app_module
from extensions import db
from models import Recipe, Tag, MealPlanEntry, MealPlan

RECIPES = [
    {
        "title": "Spaghetti Carbonara",
        "description": "A Roman classic — silky egg-and-cheese sauce with crispy pancetta. Ready in 25 minutes.",
        "cook_time_minutes": 25,
        "servings": 4,
        "tags": ["italian", "pasta", "quick", "dinner"],
        "ingredients_text": """\
400g spaghetti
200g pancetta or guanciale, diced
4 large eggs
100g Pecorino Romano, finely grated
50g Parmesan, finely grated
2 cloves garlic, lightly crushed
2 tbsp olive oil
salt and black pepper to taste""",
        "steps": """\
1. Bring a large pot of salted water to a boil and cook spaghetti until al dente. Reserve 1 cup pasta water before draining.
2. Meanwhile, cook pancetta and garlic in olive oil over medium heat until crispy. Discard garlic.
3. Whisk eggs with Pecorino and Parmesan in a bowl. Season generously with black pepper.
4. Remove pan from heat. Add drained pasta and toss to coat in the pancetta fat.
5. Pour egg mixture over pasta, tossing quickly and adding pasta water a splash at a time until sauce is creamy and clings to the noodles.
6. Serve immediately with extra cheese and black pepper.""",
    },
    {
        "title": "Black Bean Tacos",
        "description": "Smoky spiced black beans with fresh mango salsa in warm corn tortillas. On the table in 20 minutes.",
        "cook_time_minutes": 20,
        "servings": 4,
        "tags": ["mexican", "vegetarian", "quick", "dinner"],
        "ingredients_text": """\
2 cans (400g each) black beans, drained and rinsed
1 tsp ground cumin
1 tsp smoked paprika
1/2 tsp chili powder
1 clove garlic, minced
2 tbsp olive oil
8 small corn tortillas
1 mango, diced
1/2 red onion, finely diced
1 lime, juiced
1/4 cup fresh cilantro, chopped
1 avocado, sliced
salt to taste""",
        "steps": """\
1. Make the mango salsa: combine mango, red onion, lime juice, and cilantro. Season with salt and set aside.
2. Heat olive oil in a skillet over medium heat. Add garlic and cook 30 seconds.
3. Add black beans, cumin, paprika, and chili powder. Cook 5 minutes, stirring, until heated through and fragrant. Lightly mash some beans with the back of a spoon.
4. Warm tortillas in a dry pan or directly over a gas flame.
5. Fill tortillas with black beans, mango salsa, and avocado slices. Serve immediately.""",
    },
    {
        "title": "Lemon Herb Baked Salmon",
        "description": "Flaky salmon fillets roasted with lemon, garlic, and fresh herbs. Healthy and done in 25 minutes.",
        "cook_time_minutes": 25,
        "servings": 4,
        "tags": ["fish", "healthy", "quick", "dinner"],
        "ingredients_text": """\
4 salmon fillets (about 180g each)
2 lemons (1 sliced, 1 juiced)
3 cloves garlic, minced
2 tbsp olive oil
1 tbsp fresh dill, chopped
1 tbsp fresh parsley, chopped
1 tsp Dijon mustard
salt and pepper to taste""",
        "steps": """\
1. Preheat oven to 200°C (400°F). Line a baking dish with foil.
2. Whisk together olive oil, lemon juice, garlic, mustard, dill, and parsley.
3. Place salmon fillets skin-side down in the dish. Pour herb mixture over top. Lay lemon slices alongside.
4. Season with salt and pepper.
5. Bake 15–18 minutes until salmon flakes easily with a fork.
6. Serve with roasted vegetables or a green salad.""",
    },
    {
        "title": "Mushroom Risotto",
        "description": "Creamy Arborio rice slowly cooked with a mix of mushrooms, white wine, and Parmesan.",
        "cook_time_minutes": 40,
        "servings": 4,
        "tags": ["italian", "vegetarian", "dinner"],
        "ingredients_text": """\
300g Arborio rice
500g mixed mushrooms (cremini, shiitake, oyster), sliced
1 litre warm vegetable stock
1 cup dry white wine
1 onion, finely diced
3 cloves garlic, minced
60g Parmesan, grated
2 tbsp butter
2 tbsp olive oil
1 tbsp fresh thyme leaves
salt and pepper to taste""",
        "steps": """\
1. Heat stock in a saucepan and keep warm over low heat.
2. Sauté onion in olive oil and 1 tbsp butter over medium heat until soft, about 5 minutes. Add garlic and thyme.
3. Add mushrooms and cook until browned, 5–7 minutes.
4. Stir in rice and toast for 1 minute. Pour in wine and stir until absorbed.
5. Add warm stock one ladle at a time, stirring constantly and waiting for each addition to be absorbed before adding the next (about 20 minutes total).
6. Remove from heat. Stir in remaining butter and Parmesan. Season and serve immediately.""",
    },
    {
        "title": "Thai Green Curry",
        "description": "Fragrant coconut curry with vegetables and tofu. Serve over jasmine rice for a satisfying weeknight meal.",
        "cook_time_minutes": 30,
        "servings": 4,
        "tags": ["thai", "vegetarian", "dinner"],
        "ingredients_text": """\
400ml coconut milk
400g firm tofu, cubed
2 tbsp green curry paste
1 zucchini, sliced
1 red bell pepper, sliced
1 cup snap peas
1 can (400ml) coconut milk (second tin)
2 tbsp fish sauce (or soy sauce for vegan)
1 tbsp brown sugar
4 kaffir lime leaves
1 stalk lemongrass, bruised
1 tbsp vegetable oil
fresh Thai basil and lime wedges to serve
2 cups jasmine rice, cooked""",
        "steps": """\
1. Cook jasmine rice per package instructions.
2. Heat oil in a wok over medium-high heat. Fry curry paste 1 minute until fragrant.
3. Add one tin of coconut milk, lemongrass, and kaffir lime leaves. Bring to a simmer.
4. Add tofu, vegetables, fish sauce (or soy), and sugar. Simmer 10 minutes.
5. Pour in the second tin of coconut milk and heat through.
6. Discard lemongrass and lime leaves. Serve over rice with fresh basil and lime.""",
    },
    {
        "title": "Classic Beef Burger",
        "description": "Juicy homemade beef patties with all the trimmings. Better than any fast food.",
        "cook_time_minutes": 20,
        "servings": 4,
        "tags": ["beef", "american", "quick", "dinner"],
        "ingredients_text": """\
700g ground beef (80/20 fat ratio)
1 tsp garlic powder
1 tsp onion powder
1 tsp Worcestershire sauce
salt and black pepper
4 burger buns, toasted
4 slices cheddar cheese
4 leaves lettuce
2 tomatoes, sliced
1 red onion, thinly sliced
pickles to taste
ketchup and mustard to serve""",
        "steps": """\
1. Combine beef with garlic powder, onion powder, Worcestershire sauce, salt, and pepper. Do not overwork the meat.
2. Divide into 4 equal patties about 2cm thick. Press a small indent in the centre of each to prevent puffing.
3. Heat a cast iron skillet or griddle over high heat until very hot.
4. Cook patties 3–4 minutes per side for medium. Add cheese in the last minute and cover to melt.
5. Toast buns in the same pan.
6. Build burgers with lettuce, tomato, onion, and pickles. Sauce and serve.""",
    },
    {
        "title": "Tomato Lentil Soup",
        "description": "A hearty, warming soup packed with red lentils, tomatoes, and spices. Great for meal prep.",
        "cook_time_minutes": 35,
        "servings": 6,
        "tags": ["vegetarian", "healthy", "soup", "lunch"],
        "ingredients_text": """\
300g red lentils, rinsed
2 cans (400g each) crushed tomatoes
1 litre vegetable stock
1 large onion, diced
3 cloves garlic, minced
1 carrot, diced
2 tsp ground cumin
1 tsp ground coriander
1/2 tsp turmeric
1/2 tsp smoked paprika
2 tbsp olive oil
juice of 1 lemon
salt and pepper to taste
fresh parsley to serve""",
        "steps": """\
1. Heat olive oil in a large pot over medium heat. Sauté onion and carrot until softened, 6 minutes. Add garlic and cook 1 minute.
2. Stir in cumin, coriander, turmeric, and paprika; cook 1 minute until fragrant.
3. Add lentils, crushed tomatoes, and stock. Bring to a boil.
4. Reduce heat and simmer 20–25 minutes until lentils are completely soft.
5. Use an immersion blender to partially blend for a chunky texture, or leave as is.
6. Stir in lemon juice, season, and serve topped with fresh parsley.""",
    },
    {
        "title": "Banana Oat Pancakes",
        "description": "Naturally sweetened, gluten-free-friendly pancakes made from oats and banana. A wholesome breakfast.",
        "cook_time_minutes": 15,
        "servings": 2,
        "tags": ["breakfast", "vegetarian", "quick", "healthy"],
        "ingredients_text": """\
2 ripe bananas, mashed
1 cup rolled oats
2 eggs
1/2 cup milk
1 tsp baking powder
1/2 tsp cinnamon
pinch of salt
butter or coconut oil for frying
maple syrup and fresh berries to serve""",
        "steps": """\
1. Blend oats in a blender until a coarse flour forms.
2. Add bananas, eggs, milk, baking powder, cinnamon, and salt. Blend until smooth. Rest 2 minutes.
3. Heat a non-stick pan over medium heat with a little butter or oil.
4. Pour about 3 tbsp batter per pancake. Cook until bubbles form and edges look set, about 2 minutes. Flip and cook 1 minute more.
5. Serve with maple syrup and fresh berries.""",
    },
    {
        "title": "Sheet Pan Chicken Thighs with Vegetables",
        "description": "One-pan roasted chicken thighs with seasonal vegetables. Minimal washing up, maximum flavour.",
        "cook_time_minutes": 50,
        "servings": 4,
        "tags": ["chicken", "dinner", "healthy"],
        "ingredients_text": """\
8 bone-in chicken thighs
2 medium potatoes, cut into chunks
2 carrots, sliced
1 red bell pepper, cut into strips
1 zucchini, sliced
4 cloves garlic, smashed
3 tbsp olive oil
1 tsp dried oregano
1 tsp smoked paprika
1/2 tsp garlic powder
salt and pepper to taste
fresh lemon wedges to serve""",
        "steps": """\
1. Preheat oven to 220°C (425°F).
2. Toss vegetables and garlic with 2 tbsp olive oil, salt, pepper, and half the spices. Spread on a large sheet pan.
3. Rub chicken thighs with remaining oil and spices. Place on top of vegetables skin-side up.
4. Roast 40–45 minutes until chicken skin is golden and crispy and juices run clear.
5. Serve directly from the pan with lemon wedges.""",
    },
    {
        "title": "Greek Salad with Crispy Chickpeas",
        "description": "A vibrant, protein-packed salad with roasted chickpeas, olives, feta, and a simple red wine vinaigrette.",
        "cook_time_minutes": 30,
        "servings": 2,
        "tags": ["vegetarian", "salad", "healthy", "lunch"],
        "ingredients_text": """\
1 can (400g) chickpeas, drained and dried well
1 English cucumber, chopped
2 large tomatoes, chopped
1/2 red onion, thinly sliced
100g Kalamata olives
150g feta cheese, crumbled
3 tbsp olive oil (2 for chickpeas, 1 for dressing)
1 tsp dried oregano
2 tbsp red wine vinegar
salt and pepper to taste""",
        "steps": """\
1. Preheat oven to 210°C (410°F). Toss dried chickpeas with 2 tbsp olive oil, oregano, salt, and pepper. Spread on a baking sheet.
2. Roast chickpeas 25 minutes until golden and crispy. Let cool slightly.
3. Whisk together 1 tbsp olive oil, red wine vinegar, salt, and pepper.
4. Combine cucumber, tomatoes, red onion, and olives in a bowl. Pour dressing over and toss.
5. Top with feta and crispy chickpeas. Serve immediately.""",
    },
]


def seed():
    with app_module.app.app_context():
        print("Clearing existing data...")
        MealPlanEntry.query.delete()
        MealPlan.query.delete()

        # Clear recipe_tags association then recipes and tags
        for recipe in Recipe.query.all():
            recipe.tags = []
        db.session.flush()
        Recipe.query.delete()
        Tag.query.delete()
        db.session.commit()

        print(f"Inserting {len(RECIPES)} recipes...")
        for data in RECIPES:
            tag_names = data.pop("tags")
            recipe = Recipe(**data)

            tags = []
            for name in tag_names:
                tag = Tag.query.filter_by(name=name).first()
                if tag is None:
                    tag = Tag(name=name)
                    db.session.add(tag)
                tags.append(tag)
            recipe.tags = tags
            db.session.add(recipe)

        db.session.commit()
        print(f"Done. {Recipe.query.count()} recipes in the database.")


if __name__ == "__main__":
    seed()
