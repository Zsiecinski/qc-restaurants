from flask import Flask, render_template, url_for
import pandas as pd
import json
from datetime import datetime, timezone, timedelta
import re
import os
import random
import requests

app = Flask(__name__)

# Add custom Jinja2 filter for random sampling
@app.template_filter('random_sample')
def random_sample(lst, n):
    return random.sample(list(lst), min(n, len(lst)))

# Get the absolute path to the data file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'Outscraper-20250306082041s8b.xlsx')

def parse_working_hours(hours_str):
    if pd.isna(hours_str):
        return {}
    try:
        # Convert string to proper JSON format if needed
        if isinstance(hours_str, str):
            hours_str = hours_str.replace("'", '"')
        hours_dict = json.loads(hours_str)
        
        # Clean up the hours format
        cleaned_hours = {}
        for day, hours in hours_dict.items():
            if hours and isinstance(hours, str):
                # Remove any spaces between time and AM/PM
                hours = re.sub(r'(\d)(?:\s+)(AM|PM)', r'\1\2', hours)
                cleaned_hours[day] = hours
        return cleaned_hours
    except:
        return {}

def extract_service_options(about):
    # Default features for all restaurants
    default_features = ['Takeout', 'Dine-in']
    
    if pd.isna(about):
        return default_features
        
    try:
        # Try parsing as JSON first
        about_dict = json.loads(about) if isinstance(about, str) else about
        service_options = about_dict.get('Service options', {})
        features = []
        
        # Check all delivery-related options
        if service_options.get('Delivery', False) or service_options.get('No-contact delivery', False):
            features.append('Delivery')
        if service_options.get('Takeout', False):
            features.append('Takeout')
        if service_options.get('Dine-in', False) or service_options.get('Onsite services', False):
            features.append('Dine-in')
            
        # For fast food restaurants, ensure they have basic features
        if 'fast food' in str(about_dict.get('category', '')).lower():
            if 'Takeout' not in features:
                features.append('Takeout')
            if 'Dine-in' not in features:
                features.append('Dine-in')
            if 'Delivery' not in features:
                features.append('Delivery')
            
        return features if features else default_features
    except Exception as e:
        print(f"Error extracting features: {str(e)}")
        return default_features

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
    # Use Filipino time (UTC+8)
    ph_time = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))
    return ph_time.strftime('%A')  # Returns the current day name

def format_working_hours(hours_dict):
    if not hours_dict:
        return "Hours not available"
    current_day = get_current_day()
    if current_day in hours_dict:
        return f"Today: {hours_dict[current_day]}"
    return "Hours not available"

def extract_price_range(about):
    if pd.isna(about):
        return '1'  # Default to budget-friendly for fast food
    try:
        # Parse the JSON
        about_dict = json.loads(about) if isinstance(about, str) else about
        
        # Check if it's a fast food restaurant
        category = about_dict.get('category', '').lower()
        if 'fast food' in category or 'fastfood' in category:
            return '1'  # Fast food is typically budget-friendly
            
        # Look for price level in the JSON
        price_info = about_dict.get('Price', {})
        if isinstance(price_info, dict):
            # Count how many price options are true
            price_level = sum(1 for key, value in price_info.items() if value and '₱' in key)
            return str(price_level) if price_level > 0 else '1'
        return '1'
    except:
        # If JSON parsing fails, try the old method
        about_str = str(about).lower()
        if 'fast food' in about_str or 'fastfood' in about_str:
            return '1'
        count = about_str.count('₱')
        return str(count) if count > 0 else '1'

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

def extract_main_cuisine(subtypes):
    if not subtypes or len(subtypes) == 0:
        return None
    # Print debug info
    print(f"Debug - Processing subtypes: {subtypes}")
    
    # Clean up and standardize the cuisine name
    cuisine = subtypes[0].strip()
    cuisine = cuisine.replace(' Restaurant', '').strip()
    cuisine = cuisine.replace('Restaurant', '').strip()
    
    # Skip if it's just "Restaurant"
    if cuisine.lower() == 'restaurant':
        return None
        
    print(f"Debug - Extracted cuisine: {cuisine}")
    return cuisine

def is_currently_open(hours_dict):
    if not hours_dict:
        return False
    
    # Use Filipino time (UTC+8)
    ph_time = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))
    current_day = ph_time.strftime('%A')
    
    if current_day not in hours_dict:
        return False
        
    try:
        hours = hours_dict[current_day]
        
        # Check if it's open 24 hours
        if hours.lower().strip() == 'open 24 hours':
            return True
            
        if '-' not in hours:
            return False
            
        current_time = ph_time.strftime('%I:%M%p')  # Format: 11:00AM
        open_time, close_time = hours.split('-')
        # Remove any spaces and standardize format
        open_time = re.sub(r'\s+', '', open_time).upper()
        close_time = re.sub(r'\s+', '', close_time).upper()
        current_time = current_time.upper()
        
        # Convert times to comparable format (minutes since midnight)
        def time_to_minutes(time_str):
            # Remove any spaces and ensure AM/PM is at the end
            time_str = re.sub(r'\s+', '', time_str).upper()
            # Handle cases where there's no minutes specified (e.g., "11AM" -> "11:00AM")
            if 'AM' in time_str or 'PM' in time_str:
                if ':' not in time_str:
                    time_str = time_str.replace('AM', ':00AM').replace('PM', ':00PM')
            
            try:
                return datetime.strptime(time_str, '%I:%M%p').hour * 60 + datetime.strptime(time_str, '%I:%M%p').minute
            except ValueError:
                try:
                    return datetime.strptime(time_str, '%I%p').hour * 60
                except ValueError:
                    return 0

        open_minutes = time_to_minutes(open_time)
        close_minutes = time_to_minutes(close_time)
        current_minutes = time_to_minutes(current_time)
        
        # Handle cases where closing time is past midnight
        if close_minutes < open_minutes:
            close_minutes += 24 * 60
            if current_minutes < open_minutes:
                current_minutes += 24 * 60
                
        return open_minutes <= current_minutes <= close_minutes
    except Exception as e:
        print(f"Error checking if restaurant is open: {str(e)}")
        return False

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

    # Process photos
    def is_valid_image_url(url):
        if pd.isna(url) or not str(url).strip() or url == 'nan' or url == 'None':
            return False
        url = str(url).strip()
        # Accept Google Photos URLs and other common image hosting services
        valid_domains = ['googleusercontent.com', 'photos.app.goo.gl', 'lh3.googleusercontent.com']
        return (url.startswith('http://') or url.startswith('https://')) and any(domain in url.lower() for domain in valid_domains)

    def process_photo_url(url):
        # Return default SVG for missing/empty URLs
        if pd.isna(url) or not url or url == 'nan' or url == 'None':
            return url_for('static', filename='cuisine-images/default.svg', _external=True)
        
        # Handle Google Photos URLs
        if 'photos.google.com' in url or 'photos.app.goo.gl' in url:
            return url_for('static', filename='cuisine-images/default.svg', _external=True)
        
        # For all other URLs, return as is - the img tag's onerror will handle any invalid images
        return url

    # Clean phone numbers and website URLs
    def clean_field(value):
        if pd.isna(value) or value == 'nan' or value == 'None' or str(value).strip() == '':
            return None
        return str(value).strip()

    # Convert reviews to integer
    df['reviews'] = df['reviews'].fillna(0).astype(int)
    
    df['phone'] = df['phone'].apply(clean_field)
    df['site'] = df['site'].apply(clean_field)
    
    # Process subtypes first
    print("\nDebug - Processing subtypes and cuisines:")
    df['subtypes_list'] = df['subtypes'].apply(parse_subtypes)
    
    # Process working hours
    df['working_hours_dict'] = df['working_hours'].apply(parse_working_hours)
    current_day = get_current_day()
    df['current_day'] = current_day
    df['is_open'] = df['working_hours_dict'].apply(is_currently_open)
    df['hours'] = df['working_hours_dict']
    
    # Process cuisine from subtypes
    df['cuisine'] = df['subtypes_list'].apply(extract_main_cuisine)
    
    # Print unique cuisines after processing
    print("\nDebug - Unique cuisines after processing:")
    print(df['cuisine'].unique())
    
    # Process photos after cuisine is extracted
    df['photo_url'] = df.apply(lambda x: process_photo_url(x.get('photo', None)), axis=1)
    
    # Process about data
    def process_about(about):
        if pd.isna(about):
            return {}
        try:
            # Try parsing as JSON first
            if isinstance(about, str):
                return json.loads(about)
            return about
        except:
            return {}

    # Process about data
    df['about'] = df['about'].apply(process_about)
    
    # Extract service options, highlights, and accessibility from about field
    def extract_about_info(about):
        if not about:
            return False, False, [], False, False
        try:
            # Extract accessibility information
            accessibility = about.get('Accessibility', {})
            wheelchair_accessible = (
                accessibility.get('Wheelchair accessible entrance', False) and 
                accessibility.get('Wheelchair accessible seating', False)
            )
            
            # Extract children information
            children = about.get('Children', {})
            good_for_kids = children.get('Good for kids', False)
            has_high_chairs = children.get('High chairs', False)
            
            # Extract service options
            service_options = about.get('Service options', {})
            features = []
            # Check all delivery-related options
            if service_options.get('Delivery', False) or service_options.get('No-contact delivery', False):
                features.append('Delivery')
            if service_options.get('Takeout', False):
                features.append('Takeout')
            if service_options.get('Dine-in', False) or service_options.get('Onsite services', False):
                features.append('Dine-in')
            
            # Extract amenities
            amenities = about.get('Amenities', {})
            has_wifi = amenities.get('Wi-Fi', False)
            
            return wheelchair_accessible, good_for_kids, features, has_wifi, has_high_chairs
        except:
            return False, False, [], False, False
    
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
    df['price'] = df['about'].apply(extract_price_range)
    
    # Process top pick status from 'top pick' column if it exists
    if 'top pick' in df.columns:
        df['top_pick'] = df['top pick'].fillna(False).astype(bool)
    else:
        df['top_pick'] = False
    
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
        # Read the Excel file
        df = pd.read_excel(DATA_FILE)
        
        # Process the dataframe
        df, all_cuisines = process_dataframe(df)
        
        # Get cuisine counts for all restaurants before filtering
        cuisine_counts = {}
        for cuisine in df['cuisine'].dropna().unique():
            count = len(df[df['cuisine'] == cuisine])
            cuisine_counts[cuisine] = count
        
        # Filter for top pick restaurants for display
        df = df[df['top_pick'] == True]
        
        return render_template('home.html', df=df.to_dict('records'), cuisine_counts=cuisine_counts, all_cuisines=all_cuisines)
    except Exception as e:
        return render_template('home.html', df=[], cuisine_counts={}, all_cuisines=[])

@app.route('/all-restaurants')
def all_restaurants():
    try:
        # Read the Excel file using the DATA_FILE constant
        df = pd.read_excel(DATA_FILE)
        
        # Process the dataframe
        df, all_cuisines = process_dataframe(df)
        
        # Get cuisine counts for the filters
        cuisine_counts = {}
        for cuisine in df['cuisine'].dropna().unique():
            count = len(df[df['cuisine'] == cuisine])
            cuisine_counts[cuisine] = count
        
        # Debug restaurant data
        print("\nDebug - Restaurant data for all-restaurants:")
        for idx, row in df.iterrows():
            print(f"\nRestaurant: {row['name']}")
            print(f"Price value: {row['price']}")
            print(f"About data type: {type(row['about'])}")
            print(f"About data: {row['about']}")
            print(f"Features: {row['features']}")
        
        # Convert restaurant data to dict and ensure proper formatting
        restaurant_data = []
        for _, row in df.iterrows():
            restaurant = row.to_dict()
            # Ensure price is a string
            restaurant['price'] = str(restaurant['price']) if restaurant['price'] is not None else '1'
            # Ensure features is a list
            restaurant['features'] = list(restaurant['features']) if isinstance(restaurant['features'], list) else ['Takeout', 'Dine-in']
            # Ensure about data is properly formatted as a JSON string
            try:
                if isinstance(restaurant['about'], dict):
                    restaurant['about'] = json.dumps(restaurant['about'])
                    print(f"\nConverted dict to JSON for {restaurant['name']}:")
                    print(f"About data: {restaurant['about']}")
                elif isinstance(restaurant['about'], str):
                    # If it's already a string, try to parse and re-stringify to ensure it's valid JSON
                    parsed = json.loads(restaurant['about'])
                    restaurant['about'] = json.dumps(parsed)
                    print(f"\nRe-stringified JSON for {restaurant['name']}:")
                    print(f"About data: {restaurant['about']}")
                else:
                    restaurant['about'] = '{}'
                    print(f"\nSet empty JSON for {restaurant['name']} (invalid type: {type(restaurant['about'])})")
            except Exception as e:
                restaurant['about'] = '{}'
                print(f"\nError processing about data for {restaurant['name']}: {str(e)}")
            restaurant_data.append(restaurant)
        
        print(f"\nSuccessfully loaded {len(df)} restaurants for all-restaurants page")
        print("Cuisine counts:")
        for cuisine, count in cuisine_counts.items():
            print(f"{cuisine}: {count} restaurants")
        
        # Debug final restaurant data
        print("\nDebug - Final restaurant data sample:")
        for restaurant in restaurant_data[:3]:  # Show first 3 restaurants
            print(f"\nRestaurant: {restaurant['name']}")
            print(f"Price: {restaurant['price']}")
            print(f"Features: {restaurant['features']}")
            print(f"About data: {restaurant['about']}")
        
        return render_template('all_restaurants.html', 
                             restaurants=restaurant_data,
                             all_cuisines=all_cuisines,
                             cuisines=all_cuisines,
                             cuisine_counts=cuisine_counts,
                             price_labels=['Budget-friendly', 'Mid-range', 'High-end', 'Fine dining'])
    except Exception as e:
        print(f"Error in all_restaurants route: {str(e)}")
        return render_template('all_restaurants.html', 
                             restaurants=[],
                             all_cuisines=[],
                             cuisines=[],
                             cuisine_counts={},
                             price_labels=['Budget-friendly', 'Mid-range', 'High-end', 'Fine dining'],
                             error="Unable to load restaurant data. Please try again later.")

@app.route('/quezoncity/<category>')
def category_restaurants(category):
    try:
        df = pd.read_excel(DATA_FILE)
        df, cuisines = process_dataframe(df)
        
        # Convert category name for matching
        category_name = category.lower().replace('-', ' ')
        category_df = df[df['category'].str.lower() == category_name]
        
        if category_df.empty:
            return render_template('404.html'), 404
            
        return render_template('category.html', 
                             category=category.replace('-', ' ').title(),
                             restaurants=category_df.to_dict('records'),
                             cuisines=cuisines)
    except Exception as e:
        print(f"Error in category route: {str(e)}")
        return render_template('category.html',
                             category=category.replace('-', ' ').title(),
                             restaurants=[],
                             cuisines=[],
                             error="Unable to load restaurant data. Please try again later.")

@app.route('/cuisine/<cuisine>')
def cuisine_page(cuisine):
    # Read and process the data
    df = pd.read_excel(DATA_FILE)
    df, all_cuisines = process_dataframe(df)
    
    # Convert URL-friendly name back to display name
    cuisine_name = cuisine.replace('-', ' ').title()
    print(f"\nDebug - Requested cuisine: {cuisine_name}")
    
    # Filter restaurants by cuisine
    mask = df['cuisine'].str.lower() == cuisine_name.lower()
    cuisine_restaurants = df[mask].copy() if pd.notna(df['cuisine']).any() else pd.DataFrame()
    
    if cuisine_restaurants.empty:
        print(f"Debug - No restaurants found for cuisine: {cuisine_name}")
        return render_template('404.html'), 404
    
    # Ensure price and features are properly formatted
    cuisine_restaurants['price'] = cuisine_restaurants.apply(
        lambda row: '1' if cuisine_name.lower() == 'fast food' else extract_price_range(row['about']),
        axis=1
    )
    
    # Extract and format features
    cuisine_restaurants['features'] = cuisine_restaurants['about'].apply(extract_service_options)
    
    # Debug restaurant data
    print("\nDebug - Restaurant data:")
    for idx, row in cuisine_restaurants.iterrows():
        print(f"Restaurant: {row['name']}")
        print(f"Price value: {row['price']}")
        print(f"About data: {row['about']}")
    
    # Get cuisine counts for display
    cuisine_counts = df['cuisine'].value_counts().to_dict()
    
    # Price range labels
    price_labels = ['Budget-friendly', 'Mid-range', 'High-end', 'Fine dining']
    
    # Get all possible features
    all_features = set()
    for features in cuisine_restaurants['features']:
        if isinstance(features, list):
            all_features.update(features)
    features = sorted(list(all_features))
    
    print("\nDebug - Available features:", features)
    
    # Convert restaurant data to dict and ensure proper formatting
    restaurant_data = []
    for _, row in cuisine_restaurants.iterrows():
        restaurant = row.to_dict()
        # Ensure price is a string
        restaurant['price'] = str(restaurant['price']) if restaurant['price'] is not None else '1'
        # Ensure features is a list
        restaurant['features'] = list(restaurant['features']) if isinstance(restaurant['features'], list) else ['Takeout', 'Dine-in']
        # Ensure about data is properly formatted as a JSON string
        try:
            if isinstance(restaurant['about'], dict):
                restaurant['about'] = json.dumps(restaurant['about'])
            elif isinstance(restaurant['about'], str):
                # If it's already a string, try to parse and re-stringify to ensure it's valid JSON
                parsed = json.loads(restaurant['about'])
                restaurant['about'] = json.dumps(parsed)
            else:
                restaurant['about'] = '{}'
        except:
            restaurant['about'] = '{}'
        restaurant_data.append(restaurant)
    
    return render_template('cuisine.html',
                         cuisine_name=cuisine_name,
                         restaurants=restaurant_data,
                         restaurant_count=len(cuisine_restaurants),
                         all_cuisines=all_cuisines,
                         cuisine_counts=cuisine_counts,
                         price_labels=price_labels,
                         features=features)

@app.route('/about')
def about():
    # Get all unique cuisines for the navigation
    df = pd.read_excel(DATA_FILE)
    df, all_cuisines = process_dataframe(df)
    return render_template('about.html', all_cuisines=all_cuisines)

@app.route('/blog/best-coffee-shops-quezon-city')
def coffee_shops_blog():
    return render_template('blog/best-coffee-shops-quezon-city.html')

if __name__ == '__main__':
    app.run(debug=True) 