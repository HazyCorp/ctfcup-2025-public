"""
Large collection of cocktail recipes for randomization in checker
"""
import random

COCKTAIL_RECIPES = [
    {
        "name": "Moscow Mule",
        "ingredients": ["2 oz vodka", "4 oz ginger beer", "0.5 oz lime juice", "Ice cubes"],
        "instructions": [
            "Fill a copper mug with ice",
            "Add vodka and lime juice",
            "Top with ginger beer",
            "Stir gently",
            "Garnish with lime wedge"
        ],
        "secrets": [
            "A dash of vanilla extract",
            "A pinch of cinnamon",
            "Use fresh ginger juice instead of ginger beer",
            "Add a splash of elderflower liqueur",
            "Muddle fresh mint leaves"
        ]
    },
    {
        "name": "Margarita",
        "ingredients": ["2 oz tequila", "1 oz lime juice", "1 oz triple sec", "Salt for rim"],
        "instructions": [
            "Rim glass with salt",
            "Shake ingredients with ice",
            "Strain into glass",
            "Garnish with lime"
        ],
        "secrets": [
            "Add a pinch of cayenne pepper",
            "Use mezcal instead of tequila",
            "Add fresh jalapeño slices",
            "Mix in agave nectar",
            "Use Tajín instead of salt on the rim"
        ]
    },
    {
        "name": "Mojito",
        "ingredients": ["2 oz white rum", "1 oz lime juice", "2 tsp sugar", "Mint leaves", "Soda water"],
        "instructions": [
            "Muddle mint with sugar and lime",
            "Add rum and ice",
            "Top with soda water",
            "Garnish with mint"
        ],
        "secrets": [
            "Use brown sugar instead of white",
            "Add fresh basil along with mint",
            "Use coconut rum",
            "Add a splash of passion fruit puree",
            "Muddle cucumber with mint"
        ]
    },
    {
        "name": "Old Fashioned",
        "ingredients": ["2 oz bourbon", "1 sugar cube", "2 dashes Angostura bitters", "Orange peel"],
        "instructions": [
            "Muddle sugar with bitters",
            "Add bourbon and ice",
            "Stir gently",
            "Express orange peel over drink"
        ],
        "secrets": [
            "Use maple syrup instead of sugar",
            "Add a dash of black walnut bitters",
            "Use smoked bourbon",
            "Add a luxardo cherry",
            "Flame the orange peel"
        ]
    },
    {
        "name": "Piña Colada",
        "ingredients": ["2 oz white rum", "3 oz pineapple juice", "2 oz coconut cream", "Crushed ice"],
        "instructions": [
            "Blend all ingredients with ice",
            "Pour into hurricane glass",
            "Garnish with pineapple wedge",
            "Add cocktail umbrella"
        ],
        "secrets": [
            "Add fresh mango chunks",
            "Use coconut rum",
            "Blend in frozen banana",
            "Add a splash of amaretto",
            "Top with toasted coconut flakes"
        ]
    },
    {
        "name": "Cosmopolitan",
        "ingredients": ["1.5 oz vodka", "1 oz Cointreau", "0.5 oz lime juice", "Splash cranberry juice"],
        "instructions": [
            "Shake all ingredients with ice",
            "Strain into martini glass",
            "Garnish with lime wheel",
            "Flame orange peel over drink"
        ],
        "secrets": [
            "Use citrus vodka",
            "Add fresh cranberries",
            "Use blood orange juice",
            "Add elderflower liqueur",
            "Rim glass with sugar"
        ]
    },
    {
        "name": "Whiskey Sour",
        "ingredients": ["2 oz whiskey", "0.75 oz lemon juice", "0.5 oz simple syrup", "Egg white (optional)"],
        "instructions": [
            "Dry shake with egg white",
            "Add ice and shake again",
            "Strain into rocks glass",
            "Garnish with cherry and orange"
        ],
        "secrets": [
            "Use bourbon barrel-aged maple syrup",
            "Add a dash of bitters on foam",
            "Use rye whiskey",
            "Add fresh thyme",
            "Smoke the glass with applewood"
        ]
    },
    {
        "name": "Daiquiri",
        "ingredients": ["2 oz white rum", "1 oz lime juice", "0.75 oz simple syrup"],
        "instructions": [
            "Shake all ingredients with ice",
            "Strain into coupe glass",
            "Garnish with lime wheel"
        ],
        "secrets": [
            "Use aged rum",
            "Add fresh strawberries",
            "Use demerara syrup",
            "Add fresh mint",
            "Blend with frozen fruit"
        ]
    },
    {
        "name": "Manhattan",
        "ingredients": ["2 oz rye whiskey", "1 oz sweet vermouth", "2 dashes bitters", "Cherry"],
        "instructions": [
            "Stir ingredients with ice",
            "Strain into coupe glass",
            "Garnish with cherry"
        ],
        "secrets": [
            "Use both Angostura and orange bitters",
            "Add a dash of cherry liqueur",
            "Use bourbon instead of rye",
            "Rinse glass with absinthe",
            "Use Luxardo cherry"
        ]
    },
    {
        "name": "Negroni",
        "ingredients": ["1 oz gin", "1 oz Campari", "1 oz sweet vermouth", "Orange peel"],
        "instructions": [
            "Stir ingredients with ice",
            "Strain into rocks glass",
            "Express orange peel",
            "Garnish with orange wheel"
        ],
        "secrets": [
            "Use mezcal instead of gin",
            "Add a splash of sparkling wine",
            "Use barrel-aged Campari",
            "Add fresh rosemary",
            "Use grapefruit peel instead of orange"
        ]
    },
    {
        "name": "Mai Tai",
        "ingredients": ["2 oz aged rum", "0.75 oz lime juice", "0.5 oz orange curaçao", "0.25 oz orgeat"],
        "instructions": [
            "Shake ingredients with ice",
            "Strain into rocks glass",
            "Top with crushed ice",
            "Garnish with mint and lime"
        ],
        "secrets": [
            "Use two types of rum",
            "Add fresh pineapple juice",
            "Float dark rum on top",
            "Use homemade orgeat",
            "Add a dash of Angostura bitters"
        ]
    },
    {
        "name": "Aperol Spritz",
        "ingredients": ["3 oz Aperol", "3 oz prosecco", "Splash soda water", "Orange slice"],
        "instructions": [
            "Fill glass with ice",
            "Add Aperol",
            "Top with prosecco and soda",
            "Garnish with orange"
        ],
        "secrets": [
            "Use Campari for bitter version",
            "Add fresh strawberries",
            "Use blood orange",
            "Add basil leaves",
            "Freeze prosecco into ice cubes"
        ]
    },
    {
        "name": "Espresso Martini",
        "ingredients": ["2 oz vodka", "1 oz coffee liqueur", "1 oz fresh espresso", "0.5 oz simple syrup"],
        "instructions": [
            "Shake vigorously with ice",
            "Strain into martini glass",
            "Garnish with coffee beans"
        ],
        "secrets": [
            "Use vanilla vodka",
            "Add chocolate bitters",
            "Use salted caramel liqueur",
            "Add a pinch of cinnamon",
            "Rim with cocoa powder"
        ]
    },
    {
        "name": "Tom Collins",
        "ingredients": ["2 oz gin", "1 oz lemon juice", "0.5 oz simple syrup", "Club soda"],
        "instructions": [
            "Shake gin, lemon, syrup with ice",
            "Strain into collins glass",
            "Top with club soda",
            "Garnish with lemon and cherry"
        ],
        "secrets": [
            "Use elderflower liqueur",
            "Add fresh cucumber",
            "Use lavender syrup",
            "Add muddled berries",
            "Use tonic water instead of soda"
        ]
    },
    {
        "name": "Bloody Mary",
        "ingredients": ["2 oz vodka", "4 oz tomato juice", "0.5 oz lemon juice", "Worcestershire", "Hot sauce"],
        "instructions": [
            "Mix all ingredients in glass",
            "Add ice",
            "Stir gently",
            "Garnish elaborately"
        ],
        "secrets": [
            "Add horseradish",
            "Use pickle juice",
            "Add smoked paprika",
            "Use aquavit instead of vodka",
            "Rim with Old Bay seasoning"
        ]
    },
    {
        "name": "Caipirinha",
        "ingredients": ["2 oz cachaça", "1 lime quartered", "2 tsp sugar"],
        "instructions": [
            "Muddle lime and sugar",
            "Add cachaça",
            "Fill with crushed ice",
            "Stir well"
        ],
        "secrets": [
            "Use brown sugar",
            "Add passion fruit",
            "Use white rum (Caipirissima)",
            "Add fresh ginger",
            "Muddle with fresh berries"
        ]
    },
    {
        "name": "French 75",
        "ingredients": ["1 oz gin", "0.5 oz lemon juice", "0.5 oz simple syrup", "Champagne"],
        "instructions": [
            "Shake gin, lemon, syrup with ice",
            "Strain into champagne flute",
            "Top with champagne",
            "Garnish with lemon twist"
        ],
        "secrets": [
            "Use cognac instead of gin",
            "Add elderflower liqueur",
            "Use lavender syrup",
            "Add fresh berries",
            "Use rosé champagne"
        ]
    },
    {
        "name": "Paloma",
        "ingredients": ["2 oz tequila", "0.5 oz lime juice", "Grapefruit soda", "Salt rim"],
        "instructions": [
            "Salt the rim",
            "Add tequila and lime to glass",
            "Fill with ice",
            "Top with grapefruit soda"
        ],
        "secrets": [
            "Use fresh grapefruit juice",
            "Add jalapeño slices",
            "Use mezcal",
            "Add fresh rosemary",
            "Use Tajín on the rim"
        ]
    },
    {
        "name": "Singapore Sling",
        "ingredients": ["1.5 oz gin", "0.5 oz cherry liqueur", "0.25 oz Cointreau", "Pineapple juice", "Lime juice"],
        "instructions": [
            "Shake gin, liqueurs, juices with ice",
            "Strain into hurricane glass",
            "Top with soda water",
            "Garnish with pineapple and cherry"
        ],
        "secrets": [
            "Add a float of Benedictine",
            "Use fresh cherry syrup",
            "Add Angostura bitters",
            "Use blood orange juice",
            "Garnish with orchid flower"
        ]
    },
    {
        "name": "Irish Coffee",
        "ingredients": ["1.5 oz Irish whiskey", "6 oz hot coffee", "1 tsp brown sugar", "Heavy cream"],
        "instructions": [
            "Warm glass with hot water",
            "Add whiskey and sugar",
            "Pour in hot coffee",
            "Float cream on top"
        ],
        "secrets": [
            "Add chocolate liqueur",
            "Use maple syrup",
            "Add cinnamon stick",
            "Use cold brew concentrate",
            "Top with whipped cream and cocoa"
        ]
    }
]


def get_random_recipe() -> dict:
    """
    Get a random cocktail recipe with random secret ingredient.
    
    Returns:
        dict with 'recipe_text' and 'secret_ingredient'
    """
    recipe = random.choice(COCKTAIL_RECIPES)
    
    # Format recipe text
    recipe_text = f"""{recipe['name']}

Ingredients:
{chr(10).join('- ' + ing for ing in recipe['ingredients'])}

Instructions:
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(recipe['instructions']))}"""
    
    # Pick random secret
    secret_ingredient = random.choice(recipe['secrets'])
    
    return {
        'recipe_text': recipe_text,
        'secret_ingredient': secret_ingredient
    }


def get_multiple_random_recipes(count: int) -> list:
    """
    Get multiple unique random recipes.
    
    Args:
        count: Number of recipes to generate
        
    Returns:
        List of recipe dicts
    """
    if count > len(COCKTAIL_RECIPES):
        # If requesting more than available, allow repeats but with different secrets
        return [get_random_recipe() for _ in range(count)]
    
    # Get unique recipes
    selected = random.sample(COCKTAIL_RECIPES, count)
    return [
        {
            'recipe_text': f"""{r['name']}

Ingredients:
{chr(10).join('- ' + ing for ing in r['ingredients'])}

Instructions:
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(r['instructions']))}""",
            'secret_ingredient': random.choice(r['secrets'])
        }
        for r in selected
    ]

