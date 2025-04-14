from flask import Flask, render_template
import pandas as pd
import json
from datetime import datetime
import re
import os

app = Flask(__name__)

# Get the absolute path to the data file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'restaurants.xlsx.csv')

def parse_working_hours(hours_str):
    if pd.isna(hours_str):
        return {}
    try:
        return json.loads(hours_str)
    except:
        return {}

def extract_service_options(about):
    if pd.isna(about):
        return []
    try:
        # Try parsing as JSON first
        about_dict = json.loads(about)
        service_options = about_dict.get('service_options', {})
        return [key for key, value in service_options.items() if value]
    except:
        # If not JSON, look for keywords in the text
        about_lower = str(about).lower()
        options = []
        if 'delivery' in about_lower:
            options.append('Delivery')
        if 'takeout' in about_lower or 'take out' in about_lower or 'take-out' in about_lower:
            options.append('Takeout')
        if 'dine in' in about_lower or 'dine-in' in about_lower or 'dining' in about_lower:
            options.append('Dine-in')
        return options

def extract_highlights(about):
    if pd.isna(about):
        return []
    try:
        # Try parsing as JSON first
        about_dict = json.loads(about)
        popular_for = about_dict.get('popular_for', {})
        return [key for key, value in popular_for.items() if value][:3]
    except:
        # If not JSON, look for keywords in the text
        about_lower = str(about).lower()
        highlights = []
        keywords = {
            'breakfast': ['breakfast', 'brunch'],
            'lunch': ['lunch'],
            'dinner': ['dinner'],
            'groups': ['groups', 'group dining'],
            'family': ['family', 'families'],
            'kids': ['kids', 'children'],
            'solo dining': ['solo dining', 'alone']
        }
        for highlight, terms in keywords.items():
            if any(term in about_lower for term in terms):
                highlights.append(highlight.title())
        return highlights[:3]

def get_current_day():
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return days[datetime.now().weekday()]

def format_working_hours(hours_dict):
    if not hours_dict:
        return "Hours not available"
    current_day = get_current_day()
    if current_day in hours_dict:
        return f"Today: {hours_dict[current_day]}"
    return "Hours not available"

def extract_price_level(about):
    if pd.isna(about):
        return None
    price_pattern = r'"price_level":\s*"([₱]+)"'
    match = re.search(price_pattern, about)
    if match:
        return str(len(match.group(1)))
    return None

def extract_cuisine(subtypes):
    if pd.isna(subtypes):
        return None
    try:
        cuisines = json.loads(subtypes)
        if cuisines and len(cuisines) > 0:
            main_cuisine = cuisines[0].lower()
            cuisine_map = {
                'filipino': ['filipino', 'pinoy'],
                'chinese': ['chinese', 'cantonese', 'szechuan'],
                'japanese': ['japanese', 'sushi'],
                'korean': ['korean'],
                'american': ['american', 'burger', 'steak']
            }
            for category, keywords in cuisine_map.items():
                if any(keyword in main_cuisine for keyword in keywords):
                    return category
        return None
    except:
        return None

def process_dataframe(df):
    # Process subtypes - handle as comma-separated string if not JSON
    def parse_subtypes(x):
        if pd.isna(x):
            return []
        try:
            # Try parsing as JSON first
            subtypes = json.loads(x)
            if isinstance(subtypes, list):
                return [s.strip() for s in subtypes if s.strip().lower() != 'restaurant']
            return []
        except:
            # If not JSON, try splitting by comma
            return [s.strip() for s in str(x).split(',') if s.strip() and s.strip().lower() != 'restaurant']

    # Process subtypes first
    df['subtypes_list'] = df['subtypes'].apply(parse_subtypes)
    
    # Process working hours
    df['working_hours_dict'] = df['working_hours'].apply(parse_working_hours)
    df['formatted_hours'] = df['working_hours_dict'].apply(format_working_hours)
    
    # Process cuisine from subtypes
    def extract_main_cuisine(subtypes):
        if not subtypes or len(subtypes) == 0:
            return None
        # Clean up the cuisine name
        cuisine = subtypes[0].replace(' Restaurant', '').strip()
        return cuisine if cuisine.lower() != 'restaurant' else None
    
    df['cuisine'] = df['subtypes_list'].apply(extract_main_cuisine)
    
    # Extract service options, highlights, and accessibility from about field
    def extract_about_info(about):
        about_dict = json.loads(about) if isinstance(about, str) else about
        
        # Extract accessibility information
        accessibility = about_dict.get('Accessibility', {})
        wheelchair_accessible = (
            accessibility.get('Wheelchair accessible entrance', False) and 
            accessibility.get('Wheelchair accessible seating', False)
        )
        
        # Extract children information
        children = about_dict.get('Children', {})
        good_for_kids = children.get('Good for kids', False)
        has_high_chairs = children.get('High chairs', False)
        
        # Extract service options - now checking "Service options" instead of "service_options"
        service_options = about_dict.get('Service options', {})
        features = []
        if service_options.get('Delivery', False):
            features.append('Delivery')
        if service_options.get('Takeout', False):
            features.append('Takeout')
        if service_options.get('Dine-in', False):
            features.append('Dine-in')
        
        # Extract amenities
        amenities = about_dict.get('Amenities', {})
        has_wifi = amenities.get('Wi-Fi', False)
        
        return wheelchair_accessible, good_for_kids, features, has_wifi, has_high_chairs
    
    # Apply the about info extraction
    print("Processing row 27:")
    print(df.iloc[26]['about'])  # 26 because 0-based indexing
    about_info = df['about'].apply(extract_about_info)
    df['wheelchair_accessible'] = about_info.apply(lambda x: x[0])
    df['good_for_kids'] = about_info.apply(lambda x: x[1])
    df['features'] = about_info.apply(lambda x: x[2])  # Add features from about info
    df['has_wifi'] = about_info.apply(lambda x: x[3])  # Add Wi-Fi status
    df['has_high_chairs'] = about_info.apply(lambda x: x[4])  # Add High chairs status
    
    # Add empty lists for features and highlights since they're still referenced in the template
    df['highlights'] = [[] for _ in range(len(df))]
    
    # Convert latitude and longitude to float
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    
    # Process price range
    def extract_price_range(range_str):
        if pd.isna(range_str):
            return None
        # Count the number of ₱ symbols
        range_str = str(range_str)
        count = range_str.count('₱')
        # Convert to string to match data-price values in the template
        return str(count) if count > 0 else None

    df['price'] = df['range'].apply(extract_price_range)
    
    # Calculate score and sort
    df['score'] = df['rating'] * df['reviews']
    df = df.sort_values('score', ascending=False).reset_index(drop=True)
    
    # Get unique cuisines for filter and only include those that have at least one restaurant
    cuisine_counts = {}
    for cuisine in df['cuisine']:
        if pd.notna(cuisine):  # Only count non-null cuisines
            cuisine = cuisine.strip()
            if cuisine.lower() != 'restaurant':
                cuisine_counts[cuisine] = cuisine_counts.get(cuisine, 0) + 1
    
    # Print cuisine counts for debugging
    print("\nCuisine counts:")
    for cuisine, count in sorted(cuisine_counts.items()):
        print(f"{cuisine}: {count} restaurants")
    
    # Only include cuisines that have at least one restaurant
    all_cuisines = sorted([cuisine for cuisine, count in cuisine_counts.items() if count > 0])
    
    return df, all_cuisines

@app.route('/')
def home():
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin1', 'cp1252']
        df = None
        last_error = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(DATA_FILE, encoding=encoding)
                break
            except UnicodeDecodeError as e:
                last_error = e
                continue
        
        if df is None:
            print(f"Failed to read CSV with any encoding. Last error: {last_error}")
            return render_template('home.html', df=[], cuisine_counts={}, 
                                error="Unable to load restaurant data. Please try again later.")
        
        # Process the dataframe
        process_dataframe(df)
        
        # Get cuisine counts for the filters
        cuisine_counts = {}
        for cuisine in df['cuisine'].dropna().unique():
            count = len(df[df['cuisine'] == cuisine])
            cuisine_counts[cuisine] = count
        
        print("Successfully loaded data!")
        print("Cuisine counts:")
        for cuisine, count in cuisine_counts.items():
            print(f"{cuisine}: {count} restaurants")
        
        return render_template('home.html', df=df.to_dict('records'), cuisine_counts=cuisine_counts)
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return render_template('home.html', df=[], cuisine_counts={}, 
                            error="Unable to load restaurant data. Please try again later.")

@app.route('/quezoncity/')
def all_restaurants():
    df = pd.read_excel('Outscraper-20250306082041s8b.xlsx')
    df, cuisines = process_dataframe(df)
    return render_template('all_restaurants.html', 
                         restaurants=df,
                         get_current_day=get_current_day,
                         cuisines=cuisines)

@app.route('/quezoncity/<category>')
def category_restaurants(category):
    df = pd.read_excel('Outscraper-20250306082041s8b.xlsx')
    df, cuisines = process_dataframe(df)
    category_df = df[df['category'].str.lower() == category.lower().replace('-', ' ')]
    return render_template('category.html', 
                         category=category.replace('-', ' ').title(),
                         restaurants=category_df,
                         get_current_day=get_current_day,
                         cuisines=cuisines)

if __name__ == '__main__':
    app.run(debug=True) 