"""
Food Tour Builder
Creates curated food tour routes based on cuisine, budget, and area preferences.
"""

import random
import re

def generate_restaurant_slug(name):
    """Generate URL-friendly slug from restaurant name."""
    # Convert to lowercase
    slug = name.lower()
    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug.strip('-')

def build_food_tour(restaurants_df, cuisine=None, budget=None, area=None, stops=3):
    """
    Build a food tour based on preferences.
    
    Args:
        restaurants_df: DataFrame containing restaurant data
        cuisine: Type of cuisine (Filipino, Asian, Western, etc.)
        budget: Budget level (budget, mid, splurge)
        area: Specific area in QC (Timog, Tomas Morato, etc.)
        stops: Number of tour stops (default 3)
    
    Returns:
        List of restaurant dictionaries for the tour
    """
    filtered = restaurants_df.copy()
    
    # Filter by cuisine
    if cuisine and cuisine != 'any':
        cuisine_map = {
            'filipino': ['Filipino', 'Pinoy', 'Filipino'],
            'asian': ['Japanese', 'Thai', 'Vietnamese', 'Korean', 'Chinese', 'Asian', 'Thai', 'Singaporean'],
            'western': ['American', 'Italian', 'Spanish', 'Western', 'European']
        }
        if cuisine in cuisine_map:
            cuisine_filter = filtered['type'].fillna('').apply(
                lambda x: any(c.lower() in x.lower() for c in cuisine_map[cuisine])
            )
            filtered = filtered[cuisine_filter]
    
    # Filter by budget
    if budget:
        budget_map = {
            'budget': (0, 200),
            'mid': (200, 500),
            'splurge': (500, 1000)
        }
        if budget in budget_map:
            min_price, max_price = budget_map[budget]
            filtered = filtered[filtered['rating'].notna()]
    
    # Filter by area
    if area and area != 'any':
        area_keywords = {
            'timog': ['Timog', 'Scout'],
            'tomas morato': ['Tomas Morato', 'Morato'],
            'north': ['SM North', 'North EDSA', 'Trinoma'],
            'east': ['Eastwood', 'Ortigas'],
            'cubao': ['Cubao', 'Araneta'],
            'maginhawa': ['Maginhawa', 'Teacher\'s Village']
        }
        if area.lower() in area_keywords:
            area_filter = filtered['SEO Area'].fillna('').apply(
                lambda x: any(k.lower() in x.lower() for k in area_keywords[area.lower()])
            )
            filtered = filtered[area_filter]
    
    # Sort by rating and take top stops
    filtered = filtered.sort_values('rating', ascending=False)
    tour_stops = filtered.head(stops)
    
    tour = []
    for _, row in tour_stops.iterrows():
        restaurant = {
            'name': row.get('name_for_emails', row.get('name', 'Unknown')),
            'slug': generate_restaurant_slug(row.get('name', '')),
            'cuisine': row.get('type', 'Restaurant'),
            'rating': row.get('rating', 0),
            'area': row.get('SEO Area', 'Quezon City'),
            'address': row.get('street', row.get('address', '')),
            'photo': row.get('photo', ''),
            'price_range': row.get('prices', '₱₱'),
            'order': len(tour) + 1
        }
        tour.append(restaurant)
    
    return tour
