"""
Menu Suggestions for Food Tour Builder
Contains curated menu recommendations for popular restaurants in Quezon City.
"""

# Sample menu data for restaurants in the food tour
# This data can be expanded as more restaurants are added
RESTAURANT_MENUS = {
    # Filipino Restaurants
    "Esmeralda Kitchen": {
        "signature_dishes": [
            {"name": "Bicol Express", "price": "₱350", "description": "Spicy pork in coconut milk with chilies"},
            {"name": "Crispy Kare-Kare", "price": "₱450", "description": "Oxtail with peanut sauce, crispy version"},
            {"name": "Sizzling Sisig", "price": "₱280", "description": "Chopped pork ears and belly, sizzling plate"}
        ]
    },
    "LOLA Cafe": {
        "signature_dishes": [
            {"name": "Crispy Kare-Kare", "price": "₱420", "description": "Traditional oxtail with bagoong"},
            {"name": "Bagnet", "price": "₱380", "description": "Deep-fried pork belly with dipping sauce"},
            {"name": "Pinakbet", "price": "₱250", "description": "Mixed vegetables with shrimp paste"}
        ]
    },
    "Patio de Conchita Restaurant": {
        "signature_dishes": [
            {"name": "Conchita's Special", "price": "₱450", "description": "House specialty dish"},
            {"name": "Lechon Kawali", "price": "₱320", "description": "Crispy pork belly"},
            {"name": "Sinigang na Baboy", "price": "₱350", "description": "Sour pork soup"}
        ]
    },
    "Elar's Lechon the Original": {
        "signature_dishes": [
            {"name": "Lechon Kawali", "price": "₱280", "description": "Crispy pork belly"},
            {"name": "Lechon", "price": "₱800", "description": "Whole roasted pig (order ahead)"},
            {"name": "Sisig", "price": "₱250", "description": "Sizzling pork variant"}
        ]
    },
    
    # Asian/Fusion Restaurants
    "Some Thai": {
        "signature_dishes": [
            {"name": "Pad Thai", "price": "₱350", "description": "Stir-fried rice noodles with shrimp"},
            {"name": "Green Curry", "price": "₱380", "description": "Thai green curry with jasmine rice"},
            {"name": "Tom Yum Soup", "price": "₱280", "description": "Hot and sour soup"}
        ]
    },
    "Bugis Singapore Street Food": {
        "signature_dishes": [
            {"name": "Chili Crab", "price": "₱680", "description": "Singapore-style crab in spicy sauce"},
            {"name": "Satay Skewers", "price": "₱250", "description": "Grilled meat skewers with peanut sauce"},
            {"name": "Hainanese Chicken Rice", "price": "₱320", "description": "Poached chicken with ginger rice"}
        ]
    },
    "Shiok Shiok Singaporean Restaurant": {
        "signature_dishes": [
            {"name": "Laksa", "price": "₱380", "description": "Spicy noodle soup with coconut milk"},
            {"name": "Singapore Fried Rice", "price": "₱280", "description": "Wok-fried rice with eggs and shrimp"},
            {"name": "Chicken Curry", "price": "₱350", "description": "Rich coconut curry"}
        ]
    },
    
    # Breakfast/Cafe Options
    "Café Inggo 1587": {
        "signature_dishes": [
            {"name": "Filipino Breakfast", "price": "₱280", "description": "Tapa, sinangag, itlog"},
            {"name": "Coffee", "price": "₱120", "description": "Barako or kapeng barako"},
            {"name": "Tapsilog", "price": "₱320", "description": "Beef tapa with garlic rice"}
        ]
    },
    
    # Casual/Fast Food Chains
    "Greenwich": {
        "signature_dishes": [
            {"name": "Overload Pizza", "price": "₱699", "description": "Pizza with all toppings"},
            {"name": "Pasta overload", "price": "₱399", "description": "Creamy pasta with toppings"},
            {"name": "Chicken Wings", "price": "₱249", "description": "Barbeque or spicy"}
        ]
    },
    "Jollibee Banawe Cardiz": {
        "signature_dishes": [
            {"name": "Chickenjoy", "price": "₱249", "description": "Crispy fried chicken"},
            {"name": "Jolly Spaghetti", "price": "₱199", "description": "Sweet-style Filipino spaghetti"},
            {"name": "Yum Burger", "price": "₱99", "description": "Classic burger"}
        ]
    },
    "McDonald's Mayon Dapitan": {
        "signature_dishes": [
            {"name": "Big Mac", "price": "₱285", "description": "Signature burger"},
            {"name": "McChicken", "price": "₱205", "description": "Chicken sandwich"},
            {"name": "McFloat", "price": "₱75", "description": "Soft serve float"}
        ]
    },
    "Burger King - Welcome Rotonda": {
        "signature_dishes": [
            {"name": "Whopper", "price": "₱299", "description": "Flame-grilled beef burger"},
            {"name": "Chicken Royale", "price": "₱279", "description": "Crispy chicken sandwich"},
            {"name": "Onion Rings", "price": "₱99", "description": "Crispy fried onion rings"}
        ]
    },
    
    # Hotpot/Specialty
    "Hotpot Kid": {
        "signature_dishes": [
            {"name": "Shabu-Shabu Set", "price": "₱499", "description": "All-you-can hotpot"},
            {"name": "Beef Slices", "price": "₱350", "description": "Premium beef for hotpot"},
            {"name": "Seafood Platter", "price": "₱450", "description": "Mixed seafood selection"}
        ]
    },
    
    # More Filipino Favorites
    "Bulalohan sa Ramirez": {
        "signature_dishes": [
            {"name": "Bulalo", "price": "₱350", "description": "Beef marrow soup"},
            {"name": "Sinigang na Hipon", "price": "₱380", "description": "Shrimp in sour soup"},
            {"name": "Nilaga", "price": "₱320", "description": "Boiled beef with vegetables"}
        ]
    },
    "The Original Pares Mami House Restaurant": {
        "signature_dishes": [
            {"name": "Pares", "price": "₱180", "description": "Beef pares with soup"},
            {"name": "Mami", "price": "₱120", "description": "Filipino noodle soup"},
            {"name": "Lumpia", "price": "₱80", "description": "Fried spring rolls"}
        ]
    },
    "Sincerity Restaurant": {
        "signature_dishes": [
            {"name": "Beijing Boneless Chicken", "price": "₱450", "description": "House specialty"},
            {"name": "Yang Chow Fried Rice", "price": "₱280", "description": "Chinese-style fried rice"},
            {"name": "Hototay Soup", "price": "₱320", "description": "Mixed meat soup"}
        ]
    },
    "24 Chicken Petron Apo -Q. Ave, Quezon City": {
        "signature_dishes": [
            {"name": "24 Chicken", "price": "₱299", "description": "Fried chicken specialty"},
            {"name": "Garlic Rice", "price": "₱80", "description": "Aromatic garlic fried rice"},
            {"name": "Side Salad", "price": "₱99", "description": "Fresh garden salad"}
        ]
    },
    "ANGKOL buttered chicken house": {
        "signature_dishes": [
            {"name": "Buttered Chicken", "price": "₱350", "description": "Butter chicken curry"},
            {"name": "Naan Bread", "price": "₱80", "description": "Fresh baked naan"},
            {"name": "Biryani", "price": "₱380", "description": "Aromatic rice dish"}
        ]
    },
    "Comida": {
        "signature_dishes": [
            {"name": "Fusion Pizza", "price": "₱450", "description": "Filipino-Italian fusion"},
            {"name": "Pasta", "price": "₱320", "description": "House-made pasta"},
            {"name": "Salad", "price": "₱180", "description": "Fresh garden options"}
        ]
    },
    "The Purity Kitchen": {
        "signature_dishes": [
            {"name": "Healthy Bowl", "price": "₱350", "description": "Balanced meal bowl"},
            {"name": "Grilled Fish", "price": "₱420", "description": "Fresh grilled seafood"},
            {"name": "Fresh Juices", "price": "₱150", "description": "Detox and wellness drinks"}
        ]
    },
    "Le Village Lifestyle Park": {
        "signature_dishes": [
            {"name": "Food Park Favorites", "price": "Varies", "description": "Various vendor options"},
            {"name": "BBQ Skewers", "price": "₱150", "description": "Grilled meat on sticks"},
            {"name": "Drinks", "price": "₱80", "description": "Refreshments"}
        ]
    },
    "South Eats Asia": {
        "signature_dishes": [
            {"name": "Asian Platter", "price": "₱450", "description": "Mixed Asian dishes"},
            {"name": "Thai Iced Tea", "price": "₱120", "description": "Sweet Thai tea"},
            {"name": "Spring Rolls", "price": "₱150", "description": "Crispy appetizer"}
        ]
    }
}

def get_restaurant_menu(restaurant_name):
    """
    Get menu suggestions for a specific restaurant.
    Returns list of signature dishes.
    """
    # Try exact match first
    if restaurant_name in RESTAURANT_MENUS:
        return RESTAURANT_MENUS[restaurant_name].get("signature_dishes", [])
    
    # Try case-insensitive match
    for name, menu in RESTAURANT_MENUS.items():
        if restaurant_name.lower() in name.lower() or name.lower() in restaurant_name.lower():
            return menu.get("signature_dishes", [])
    
    return []

def get_all_restaurants_with_menus():
    """Get list of all restaurants that have menu data."""
    return list(RESTAURANT_MENUS.keys())

def get_tour_menu_suggestions(tour_stops):
    """
    Get menu suggestions for all stops in a food tour.
    
    Args:
        tour_stops: List of restaurant dictionaries from the tour
    
    Returns:
        Dictionary mapping restaurant names to their menu suggestions
    """
    suggestions = {}
    
    for stop in tour_stops:
        restaurant_name = stop.get('name', '')
        if restaurant_name:
            menu = get_restaurant_menu(restaurant_name)
            if menu:
                suggestions[restaurant_name] = menu
    
    return suggestions

def add_menu_data(restaurant_name, dishes):
    """
    Add new menu data for a restaurant.
    
    Args:
        restaurant_name: Name of the restaurant
        dishes: List of dish dictionaries with 'name', 'price', 'description'
    """
    if restaurant_name not in RESTAURANT_MENUS:
        RESTAURANT_MENUS[restaurant_name] = {}
    
    RESTAURANT_MENUS[restaurant_name]["signature_dishes"] = dishes
    return True
