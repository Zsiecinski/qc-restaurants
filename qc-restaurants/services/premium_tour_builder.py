"""
Premium Tour Builder
Enhanced food tour with curated stops, dishes, and expert recommendations.
"""

from services.tour_builder import generate_restaurant_slug

# Premium tour configurations
PREMIUM_TOURS = {
    'filipino': {
        'theme': 'Filipino Food Journey',
        'description': 'Experience the best of Filipino cuisine from traditional to modern interpretations',
        'stops': [
            {
                'name': 'Esmeralda Kitchen',
                'type': 'Filipino',
                'order': 1,
                'dishes': ['Bicol Express', 'Crispy Kare-Kare', 'Sizzling Sisig'],
                'highlights': ['Authentic Filipino flavors', 'Cozy atmosphere', 'Great for groups'],
                'duration': '45 min - 1 hour'
            },
            {
                'name': 'LOLA Cafe',
                'type': 'Filipino',
                'order': 2,
                'dishes': ['Bagnet', 'Pinakbet', 'Crispy Kare-Kare'],
                'highlights': ['Nostalgic Filipino comfort food', 'Family recipes', 'Affordable'],
                'duration': '45 min - 1 hour'
            },
            {
                'name': 'Patio de Conchita Restaurant',
                'type': 'Filipino',
                'order': 3,
                'dishes': ['Conchita\'s Special', 'Lechon Kawali', 'Sinigang na Baboy'],
                'highlights': ['Traditional recipes', 'Spacious venue', 'Family-friendly'],
                'duration': '45 min - 1 hour'
            }
        ]
    },
    'asian': {
        'theme': 'Asian Flavor Expedition',
        'description': 'Explore diverse Asian cuisines in one tour',
        'stops': [
            {
                'name': 'Some Thai',
                'type': 'Thai',
                'order': 1,
                'dishes': ['Pad Thai', 'Green Curry', 'Tom Yum Soup'],
                'highlights': ['Authentic Thai', 'Cozy ambiance', 'Great for dates'],
                'duration': '45 min - 1 hour'
            },
            {
                'name': 'Bugis Singapore Street Food',
                'type': 'Singaporean',
                'order': 2,
                'dishes': ['Satay Skewers', 'Chili Crab', 'Hainanese Chicken Rice'],
                'highlights': ['Singapore authenticity', 'Street food vibes', 'Friendly staff'],
                'duration': '45 min - 1 hour'
            },
            {
                'name': 'Shiok Shiok Singaporean Restaurant',
                'type': 'Singaporean',
                'order': 3,
                'dishes': ['Laksa', 'Singapore Fried Rice', 'Chicken Curry'],
                'highlights': ['Rich flavors', 'Comforting soups', 'Generous portions'],
                'duration': '45 min - 1 hour'
            }
        ]
    },
    'mixed': {
        'theme': 'QC Foodie Discovery',
        'description': 'A mix of the best restaurants Quezon City has to offer',
        'stops': [
            {
                'name': 'Café Inggo 1587',
                'type': 'Filipino Cafe',
                'order': 1,
                'dishes': ['Filipino Breakfast', 'Tapsilog', 'Coffee'],
                'highlights': ['All-day breakfast', 'Coffee specialty', 'Budget-friendly'],
                'duration': '30-45 min'
            },
            {
                'name': 'Hotpot Kid',
                'type': 'Hotpot',
                'order': 2,
                'dishes': ['Shabu-Shabu Set', 'Beef Slices', 'Seafood Platter'],
                'highlights': ['Interactive dining', 'Fresh ingredients', 'Fun experience'],
                'duration': '1-1.5 hours'
            },
            {
                'name': 'ANGKOL buttered chicken house',
                'type': 'Asian Fusion',
                'order': 3,
                'dishes': ['Buttered Chicken', 'Naan Bread', 'Biryani'],
                'highlights': ['Unique flavors', 'Great for groups', 'Comfort food'],
                'duration': '45 min - 1 hour'
            }
        ]
    }
}

def build_premium_tour(restaurants_df=None, cuisine=None, budget=None, area=None, 
                       num_stops=3, vibes=None, dietary_restrictions=None, starting_point=None):
    """
    Build a premium food tour with curated stops and dish recommendations.
    
    Args:
        restaurants_df: Optional DataFrame for additional filtering
        cuisine: Type of cuisine
        budget: Budget level
        area: Specific area
        num_stops: Number of tour stops (default 3)
        vibes: List of preferred vibes
        dietary_restrictions: Dietary needs
        starting_point: Starting location
    
    Returns:
        Dictionary with tour details
    """
    # Determine tour type
    tour_key = cuisine.lower() if cuisine else 'mixed'
    if tour_key not in PREMIUM_TOURS:
        tour_key = 'mixed'
    
    tour_config = PREMIUM_TOURS[tour_key]
    
    # Build tour response
    tour_data = {
        'theme': tour_config['theme'],
        'description': tour_config['description'],
        'cuisine': cuisine,
        'budget': budget,
        'area': area,
        'total_stops': len(tour_config['stops']),
        'estimated_duration': '2-3 hours',
        'total_estimate': '₱1,500 - ₱3,000 for 3 people',
        'stops': []
    }
    
    # Add stops with slug for URL
    for idx, stop in enumerate(tour_config['stops'][:num_stops], 1):
        stop_data = {
            'name': stop['name'],
            'slug': generate_restaurant_slug(stop['name']),
            'category': stop['type'],
            'order': idx,
            'area_label': stop['type'],  # For compatibility
            'estimated_cost': budget * 350 if budget else 400,  # Estimate based on budget
            'latitude': 14.6300,  # Default coordinates for QC
            'longitude': 121.0000,
            'address': 'Quezon City',  # Default address
            'why_visit': stop['highlights'][0] if stop['highlights'] else 'Great food!',
            'vibe_tags': stop['highlights'] if stop['highlights'] else [],
            'travel_time_minutes': 15,  # Default travel time
            'dishes': [{'name': dish, 'recommended': True} for dish in stop['dishes']]
        }
        tour_data['stops'].append(stop_data)
        stop_data = {
            'name': stop['name'],
            'slug': generate_restaurant_slug(stop['name']),
            'type': stop['type'],
            'order': stop['order'],
            'dishes': [
                {'name': dish, 'recommended': True} 
                for dish in stop['dishes']
            ],
            'highlights': stop['highlights'],
            'duration': stop['duration']
        }
        tour_data['stops'].append(stop_data)
    
    return tour_data

def get_available_tours():
    """Get list of available premium tour types."""
    return [
        {
            'key': key,
            'theme': config['theme'],
            'description': config['description'],
            'stops': len(config['stops'])
        }
        for key, config in PREMIUM_TOURS.items()
    ]
