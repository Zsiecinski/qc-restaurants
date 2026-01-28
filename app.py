from flask import Flask, render_template, url_for, send_from_directory, abort, request, redirect
import pandas as pd
import json
from datetime import datetime, timezone, timedelta
import re
import os
import random
import requests
import time
from blog_data import blog_posts
from services.tour_builder import build_food_tour, generate_restaurant_slug
from services.menu_suggestions import get_tour_menu_suggestions
from services.premium_tour_builder import build_premium_tour
# Load restaurant data from New Master List
OUTSCRAPER_FILE = 'New Master List - Sheet1.csv'

# Format phone numbers to local Philippine format
def format_phone_number(phone):
    if not phone or pd.isna(phone):
        return None
    
    # Convert to string and remove any non-digit characters
    phone_str = str(phone).strip()
    digits = ''.join(filter(str.isdigit, phone_str))
    
    # Case 1: 12 digits (mobile numbers with country code 63)
    if len(digits) == 12:
        # +63 966 627 1522 → 0966 627 1522
        local_digits = digits[2:]  # Remove 63, get 9666271522
        return f"0{local_digits[:3]} {local_digits[3:6]} {local_digits[6:]}"
    
    # Case 2: 11 digits (Metro Manila landlines with country code 63)
    elif len(digits) == 11:
        # +63283746879 → (02) 8374 6879
        local_digits = digits[2:]  # Remove 63, get 283746879
        return f"(02) {local_digits[1:5]} {local_digits[5:]}"
    
    # For any other format, return as is
    else:
        return phone_str

restaurants_df = pd.read_csv(OUTSCRAPER_FILE)

# Load the restaurant photo mapping
def load_restaurant_image_mapping():
    """Load the mapping of restaurant names to local image files"""
    try:
        photo_results = pd.read_csv('restaurant_photo_results.csv')
        # Create a mapping of restaurant name to local filename
        mapping = {}
        for _, row in photo_results.iterrows():
            if row['download_status'] == 'downloaded':
                mapping[row['restaurant_name']] = row['filename']
        return mapping
    except (FileNotFoundError, Exception) as e:
        print(f"Warning: Could not load restaurant image mapping: {e}")
        return {}

# Load the image mapping once when app starts
RESTAURANT_IMAGE_MAPPING = load_restaurant_image_mapping()

def get_restaurant_image_url(restaurant_name, fallback_photo_url, alt_tag=None, street=None):
    """
    Get the best available image URL for a restaurant.
    Priority:
    1. Check local downloaded image by restaurant name in restaurant_cards (most specific)
    2. Check for webp image using sanitized street address in restaurant_cards_webp (fallback)
    3. Fall back to original photo URL
    
    Args:
        restaurant_name: Name of the restaurant
        fallback_photo_url: Original photo URL from CSV
        alt_tag: Optional alt tag override
        street: Street address for webp image lookup
    
    Returns:
        tuple: (image_url, alt_tag)
    """
    try:
        # Priority 1: Check if we have a local downloaded image by restaurant name (most specific)
        if restaurant_name:
            # Try exact match first
            if restaurant_name in RESTAURANT_IMAGE_MAPPING:
                local_filename = RESTAURANT_IMAGE_MAPPING[restaurant_name]
                local_url = url_for('static', filename=f'images/restaurant_cards/{local_filename}')
                
                # Generate alt tag if not provided
                if not alt_tag:
                    alt_tag = f"{restaurant_name} restaurant in Quezon City - exterior view and dining atmosphere"
                
                return local_url, alt_tag
            
            # Try case-insensitive match
            restaurant_name_lower = restaurant_name.lower().strip()
            for mapped_name, local_filename in RESTAURANT_IMAGE_MAPPING.items():
                if mapped_name.lower().strip() == restaurant_name_lower:
                    local_url = url_for('static', filename=f'images/restaurant_cards/{local_filename}')
                    
                    # Generate alt tag if not provided
                    if not alt_tag:
                        alt_tag = f"{restaurant_name} restaurant in Quezon City - exterior view and dining atmosphere"
                    
                    return local_url, alt_tag
        
        # Priority 2: Check restaurant_cards folder directly by sanitized restaurant name
        if restaurant_name:
            sanitized_name = sanitize_filename_for_lookup(restaurant_name)
            # Try common extensions
            for ext in ['.webp', '.jpg', '.png', '.jpeg']:
                potential_filename = sanitized_name + ext
                potential_path = os.path.join('static', 'images', 'restaurant_cards', potential_filename)
                if os.path.exists(potential_path):
                    local_url = url_for('static', filename=f'images/restaurant_cards/{potential_filename}')
                    if not alt_tag:
                        alt_tag = f"{restaurant_name} restaurant in Quezon City - exterior view and dining atmosphere"
                    return local_url, alt_tag
            
            # Also try checking if any file contains the restaurant name (for variations)
            try:
                restaurant_cards_dir = os.path.join('static', 'images', 'restaurant_cards')
                if os.path.exists(restaurant_cards_dir):
                    restaurant_name_lower = restaurant_name.lower().replace(' ', '_').replace('-', '_')
                    for filename in os.listdir(restaurant_cards_dir):
                        filename_lower = filename.lower()
                        # Check if filename contains key parts of restaurant name
                        name_parts = [part for part in restaurant_name_lower.split() if len(part) > 3]
                        if any(part in filename_lower for part in name_parts):
                            # Additional check: make sure it's a reasonable match
                            if filename_lower.endswith(('.webp', '.jpg', '.png', '.jpeg')):
                                local_url = url_for('static', filename=f'images/restaurant_cards/{filename}')
                                if not alt_tag:
                                    alt_tag = f"{restaurant_name} restaurant in Quezon City - exterior view and dining atmosphere"
                                return local_url, alt_tag
            except Exception as e:
                pass  # Continue to next priority
        
        # Priority 3: Check for street-based webp in restaurant_cards_webp (fallback if no name match)
        if street:
            street_filename = sanitize_filename_for_lookup(street) + '.webp'
            street_path = os.path.join('static', 'images', 'restaurant_cards_webp', street_filename)
            
            if os.path.exists(street_path):
                local_url = url_for('static', filename=f'images/restaurant_cards_webp/{street_filename}')
                if not alt_tag:
                    alt_tag = f"{restaurant_name} restaurant in Quezon City"
                print(f"✓ Found webp for {restaurant_name}: {street_filename}")
                return local_url, alt_tag
    except Exception as e:
        print(f"Warning: Error in get_restaurant_image_url for {restaurant_name}: {e}")
    
    # Priority 3: Fallback to original photo URL
    if not alt_tag:
        alt_tag = f"{restaurant_name or 'Restaurant'} restaurant in Quezon City"
    
    return fallback_photo_url or '', alt_tag

def sanitize_filename_for_lookup(name):
    """Convert restaurant name to the same format used in image filenames"""
    import re
    # Remove special characters and spaces
    name = re.sub(r'[^\w\s-]', '', name)
    # Replace spaces with underscores
    name = re.sub(r'\s+', '_', name)
    # Convert to lowercase
    name = name.lower()
    # Remove multiple underscores
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    return name

def generate_restaurant_slug(name):
    """Generate a clean slug from restaurant name"""
    slug = name.lower().replace(' ', '-').replace('&', 'and').replace("'", '').replace('"', '').replace(',', '').replace('.', '')
    # Remove multiple hyphens
    slug = '-'.join(filter(None, slug.split('-')))
    return slug

def parse_about_data(about_str):
    """Parse the about column JSON data into structured information"""
    if pd.isna(about_str) or not about_str:
        return {}
    
    try:
        # Handle both string and dict formats
        if isinstance(about_str, str):
            # Clean up the JSON string
            about_str = about_str.replace("'", '"')
            about_data = json.loads(about_str)
        else:
            about_data = about_str
            
        return about_data
    except:
        return {}

def extract_price_range_from_about(about_str):
    """Extract price range from about data"""
    about_data = parse_about_data(about_str)
    
    # Look for price range indicators
    if 'price_range' in about_data:
        return about_data['price_range']
    
    # Check for price indicators in other fields
    price_indicators = {
        'Budget-friendly': '₱',
        'Moderate': '₱₱', 
        'Expensive': '₱₱₱',
        'Luxury': '₱₱₱₱'
    }
    
    for indicator, price in price_indicators.items():
        if indicator.lower() in str(about_data).lower():
            return price
    
    return '₱₱'  # Default to moderate

# Create restaurant slugs and data dictionary
restaurants_data = {}
for idx, row in restaurants_df.iterrows():
    # Generate slug from restaurant name (using name_for_emails for display, name for slug generation)
    display_name = row.get('name_for_emails', row['name'])
    slug = generate_restaurant_slug(row['name'])
    
    # Store restaurant data
    restaurants_data[slug] = {
        'name': display_name,  # Use name_for_emails for display
        'slug': slug,
        'address': row.get('street', ''),
        'phone': format_phone_number(row.get('+63', '')) if pd.notna(row.get('+63', '')) and row.get('+63', '') else '',
        'website': row.get('site', ''),
        'rating': row.get('rating', 0),
        'reviews': row.get('reviews', 0),
        'latitude': row.get('latitude', ''),
        'longitude': row.get('longitude', ''),
        'category': row.get('category', ''),
        'subtypes': row.get('subtypes', ''),
        'cuisine_type': row.get('subtypes', '').split(',')[0].strip() if pd.notna(row.get('subtypes', '')) else '',
        'photos_count': row.get('photos_count', 0),
        'photo': row.get('photo', ''),
        'reviews_link': row.get('reviews_link', ''),
        'area_service': row.get('area_service', ''),
        'city': row.get('city', 'Quezon City'),
        'state': row.get('state', 'Metro Manila'),
        'country': row.get('country', 'Philippines'),
        'about_data': parse_about_data(row.get('about', '')),
        'price_range': extract_price_range_from_about(row.get('about', ''))
    }

app = Flask(__name__)

# Initialize empty defaults
PROCESSED_DF = pd.DataFrame()
ALL_CUISINES = []
AREA_COUNTS = {}
CUISINE_COUNTS = {}

# Add int function to Jinja2 environment
app.jinja_env.globals['int'] = int

def rating_to_stars(rating):
    """Convert numerical rating to star display"""
    if pd.isna(rating) or rating == 0:
        return {'full': 0, 'half': 0, 'empty': 5}
    
    rating = float(rating)
    full_stars = int(rating)
    decimal = rating - full_stars
    
    if decimal >= 0.8:
        full_stars += 1
        half_stars = 0
    elif decimal >= 0.3:
        half_stars = 1
    else:
        half_stars = 0
    
    empty_stars = 5 - full_stars - half_stars
    
    return {
        'full': full_stars,
        'half': half_stars,
        'empty': empty_stars
    }

# Add rating_to_stars function to Jinja2 environment
app.jinja_env.globals['rating_to_stars'] = rating_to_stars

# Add restaurant image helper function to Jinja2 environment
app.jinja_env.globals['get_restaurant_image_url'] = get_restaurant_image_url

# Add custom Jinja2 filter for random sampling
@app.template_filter('random_sample')
def random_sample(lst, n):
    return random.sample(list(lst), min(n, len(lst)))

@app.template_filter('restaurant_slug')
def restaurant_slug(name):
    """Template filter to generate restaurant slug"""
    return generate_restaurant_slug(name)

# Get the absolute path to the data file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'New Master List - Sheet1.csv')

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

def extract_service_options_from_about(about_str):
    """Extract service options from about data"""
    about_data = parse_about_data(about_str)
    service_options = about_data.get('Service options', {})
    
    options = []
    if service_options.get('Delivery', False):
        options.append('Delivery')
    if service_options.get('Takeout', False):
        options.append('Takeout')
    if service_options.get('Dine-in', False):
        options.append('Dine-in')
    if service_options.get('No-contact delivery', False):
        options.append('No-contact delivery')
    
    return options

def extract_amenities_from_about(about_str):
    """Extract amenities from about data"""
    about_data = parse_about_data(about_str)
    
    amenities = []
    
    # Check various amenity categories
    amenity_categories = ['Amenities', 'Accessibility', 'Children', 'Parking', 'Other']
    
    for category in amenity_categories:
        if category in about_data:
            category_data = about_data[category]
            if isinstance(category_data, dict):
                for amenity, available in category_data.items():
                    if available:
                        amenities.append(amenity)
    
    return amenities

def extract_atmosphere_from_about(about_str):
    """Extract atmosphere and crowd information"""
    about_data = parse_about_data(about_str)
    
    atmosphere = []
    
    # Check atmosphere
    if 'Atmosphere' in about_data:
        atmosphere_data = about_data['Atmosphere']
        if isinstance(atmosphere_data, dict):
            for trait, available in atmosphere_data.items():
                if available:
                    atmosphere.append(trait)
    
    # Check crowd
    if 'Crowd' in about_data:
        crowd_data = about_data['Crowd']
        if isinstance(crowd_data, dict):
            for trait, available in crowd_data.items():
                if available:
                    atmosphere.append(trait)
    
    return atmosphere

def extract_dining_options_from_about(about_str):
    """Extract dining options from about data"""
    about_data = parse_about_data(about_str)
    
    dining_options = []
    
    # Check dining options
    if 'Dining options' in about_data:
        dining_data = about_data['Dining options']
        if isinstance(dining_data, dict):
            for option, available in dining_data.items():
                if available:
                    dining_options.append(option)
    
    # Check popular for
    if 'Popular for' in about_data:
        popular_data = about_data['Popular for']
        if isinstance(popular_data, dict):
            for option, available in popular_data.items():
                if available and option not in dining_options:
                    dining_options.append(option)
    
    return dining_options

def extract_offerings_from_about(about_str):
    """Extract offerings from about data"""
    about_data = parse_about_data(about_str)
    
    offerings = []
    
    if 'Offerings' in about_data:
        offerings_data = about_data['Offerings']
        if isinstance(offerings_data, dict):
            for offering, available in offerings_data.items():
                if available:
                    offerings.append(offering)
    
    return offerings

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

def extract_main_cuisine(type_value):
    if pd.isna(type_value) or not type_value or str(type_value).strip() == '':
        return None
    # Print debug info
    print(f"Debug - Processing type: {type_value}")
    
    # Clean up and standardize the cuisine name
    cuisine = str(type_value).strip()
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
            
        # Handle multiple time ranges (e.g., "11AM-3PM,5-9PM")
        time_ranges = [range_str.strip() for range_str in hours.split(',')]
        
        current_time = ph_time.strftime('%I:%M%p')  # Format: 11:00AM
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

        current_minutes = time_to_minutes(current_time)
        
        # Check each time range
        for time_range in time_ranges:
            if '-' not in time_range:
                continue
                
            open_time, close_time = time_range.split('-')
            open_time = re.sub(r'\s+', '', open_time).upper()
            close_time = re.sub(r'\s+', '', close_time).upper()
            
            open_minutes = time_to_minutes(open_time)
            close_minutes = time_to_minutes(close_time)
            
            # Handle cases where closing time is past midnight
            if close_minutes < open_minutes:
                close_minutes += 24 * 60
                if current_minutes < open_minutes:
                    current_minutes += 24 * 60
                    
            # If current time falls within this range, restaurant is open
            if open_minutes <= current_minutes <= close_minutes:
                return True
        
        # If we get here, restaurant is not open in any time range
        return False
    except Exception as e:
        print(f"Error checking if restaurant is open: {str(e)}")
        return False

def get_time_until_open(hours_dict):
    """Calculate time until restaurant opens next"""
    if not hours_dict:
        return None
    
    # Use Filipino time (UTC+8)
    ph_time = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))
    current_day = ph_time.strftime('%A')
    current_time = ph_time
    
    # First check if currently open
    if is_currently_open(hours_dict):
        return "Open Now"
    
    # Get list of days in order
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Start from current day and check next 7 days
    for i in range(7):
        check_day = days[(days.index(current_day) + i) % 7]
        
        if check_day in hours_dict:
            hours = hours_dict[check_day]
            if hours and '-' in hours:
                try:
                    # Handle multiple time ranges (e.g., "11AM-3PM,5-9PM")
                    time_ranges = [range_str.strip() for range_str in hours.split(',')]
                    
                    # Find the next opening time from any range
                    next_open_time = None
                    for time_range in time_ranges:
                        if '-' not in time_range:
                            continue
                            
                        open_time_str = time_range.split('-')[0].strip()
                        
                        # Convert opening time to datetime
                        if ':' in open_time_str:
                            time_format = '%I:%M%p'
                        else:
                            time_format = '%I%p'
                            open_time_str = open_time_str.replace('AM', ':00AM').replace('PM', ':00PM')
                        
                        # Parse the opening time
                        open_time = datetime.strptime(open_time_str, time_format)
                        
                        # Create datetime for the check day
                        if i == 0:  # Same day
                            check_datetime = current_time.replace(hour=open_time.hour, minute=open_time.minute, second=0, microsecond=0)
                            if check_datetime > current_time:
                                # This opening time is still today and in the future
                                if next_open_time is None or check_datetime < next_open_time:
                                    next_open_time = check_datetime
                        else:  # Future day
                            # Find the next occurrence of this day
                            days_ahead = i
                            check_datetime = current_time + timedelta(days=days_ahead)
                            check_datetime = check_datetime.replace(hour=open_time.hour, minute=open_time.minute, second=0, microsecond=0)
                            
                            if next_open_time is None or check_datetime < next_open_time:
                                next_open_time = check_datetime
                    
                    # If we found a next opening time, calculate the difference
                    if next_open_time:
                        time_diff = next_open_time - current_time
                        hours_until = int(time_diff.total_seconds() // 3600)
                        minutes_until = int((time_diff.total_seconds() % 3600) // 60)
                        
                        if hours_until > 0:
                            if minutes_until > 0:
                                return f"Opens in {hours_until}h {minutes_until}m"
                            else:
                                return f"Opens in {hours_until}h"
                        else:
                            return f"Opens in {minutes_until}m"
                        
                except Exception as e:
                    print(f"Error calculating time until open: {str(e)}")
                    continue
    
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
            return '/static/cuisine-images/default.svg'
        
        # If it's already a local path, return as is
        if url.startswith('/static/images/'):
            return url
        
        # Handle Google Photos URLs
        if 'photos.google.com' in url or 'photos.app.goo.gl' in url:
            return '/static/cuisine-images/default.svg'
        
        # Check for problematic Google image URLs and test accessibility
        if 'lh3.googleusercontent.com' in url and 'gps-cs-s' in url:
            # Use the Google Photos URL directly - it should work in browsers
            return url
        
        # For all other URLs, add cache-busting parameter to force refresh
        if url and isinstance(url, str) and url.startswith('http'):
            # Add CSV file modification time as version to force browser to reload image
            try:
                csv_mtime = os.path.getmtime(OUTSCRAPER_FILE)
                timestamp = int(csv_mtime)
                separator = '&' if '?' in url else '?'
                return f"{url}{separator}v={timestamp}"
            except:
                # Fallback to current timestamp if file access fails
                timestamp = int(datetime.now().timestamp())
                separator = '&' if '?' in url else '?'
                return f"{url}{separator}v={timestamp}"
        
        # For all other URLs, return as is - the img tag's onerror will handle any invalid images
        return url

    # Clean phone numbers and website URLs
    def clean_field(value):
        if pd.isna(value) or value == 'nan' or value == 'None' or str(value).strip() == '':
            return None
        return str(value).strip()
    
    # Format phone numbers to local Philippine format


    # Convert reviews to integer - handle missing reviews column gracefully
    if 'reviews' in df.columns:
        df['reviews'] = df['reviews'].fillna(0).astype(int)
    else:
        df['reviews'] = [0 for _ in range(len(df))]
    
    # Handle phone and site columns gracefully
    if '+63' in df.columns:
        df['phone'] = df['+63'].apply(format_phone_number)
    elif 'phone' in df.columns:
        df['phone'] = df['phone'].apply(format_phone_number)
    else:
        df['phone'] = [None for _ in range(len(df))]
        
    if 'site' in df.columns:
        df['site'] = df['site'].apply(clean_field)
    else:
        df['site'] = [None for _ in range(len(df))]
    
    # Process type column for cuisines - handle missing type column gracefully
    print("\nDebug - Processing type column for cuisines:")
    if 'type' in df.columns:
        df['cuisine'] = df['type'].apply(extract_main_cuisine)
    else:
        # Create default cuisine if type column doesn't exist
        df['cuisine'] = ['Restaurant' for _ in range(len(df))]
    
    # Process working hours - handle missing working_hours column gracefully
    if 'working_hours' in df.columns:
        df['working_hours_dict'] = df['working_hours'].apply(parse_working_hours)
        current_day = get_current_day()
        df['current_day'] = current_day
        df['is_open'] = df['working_hours_dict'].apply(is_currently_open)
        df['hours'] = df['working_hours_dict']
    else:
        # Create empty working hours data if column doesn't exist
        df['working_hours_dict'] = [{} for _ in range(len(df))]
        df['current_day'] = current_day
        df['is_open'] = [False for _ in range(len(df))]
        df['hours'] = [{} for _ in range(len(df))]
    
    # Print unique cuisines after processing
    print("\nDebug - Unique cuisines after processing:")
    print(df['cuisine'].unique())
    
    # Process photos after cuisine is extracted - handle missing photo column gracefully
    if 'photo' in df.columns:
        df['photo_url'] = df.apply(lambda x: process_photo_url(x.get('photo', None)), axis=1)
    else:
        df['photo_url'] = ['/static/cuisine-images/default.svg' for _ in range(len(df))]
    
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

    # Process about data - handle missing about column gracefully
    if 'about' in df.columns:
        df['about'] = df['about'].apply(process_about)
    else:
        # Create empty about data if column doesn't exist
        df['about'] = [{} for _ in range(len(df))]
    
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
    
    # Convert latitude and longitude to float - handle missing columns gracefully
    if 'latitude' in df.columns:
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    else:
        df['latitude'] = [None for _ in range(len(df))]
        
    if 'longitude' in df.columns:
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    else:
        df['longitude'] = [None for _ in range(len(df))]
    
    # Process price range - prioritize 'range' column if available, fallback to 'about'
    if 'range' in df.columns:
        df['price'] = df['range'].apply(lambda x: str(x).count('₱') if pd.notna(x) else '1')
    else:
        df['price'] = df['about'].apply(extract_price_range)
    
    # Process top pick status from 'top pick' column if it exists
    if 'top pick' in df.columns:
        df['top_pick'] = df['top pick'].fillna(False).astype(bool)
    elif 'top_pick' in df.columns:
        df['top_pick'] = df['top_pick'].fillna(False).astype(bool)
    else:
        df['top_pick'] = False
    
    # Calculate score and sort - handle missing rating column gracefully
    if 'rating' in df.columns:
        df['score'] = df['rating'] * df['reviews']
    else:
        df['score'] = [0 for _ in range(len(df))]
    df = df.sort_values('score', ascending=False).reset_index(drop=True)
    
    # Get unique cuisine types for filter and only include those that have at least one restaurant
    cuisine_counts = {}
    if 'type' in df.columns:
        for cuisine_type in df['type']:
            if pd.notna(cuisine_type):  # Only count non-null cuisine types
                cuisine_type = cuisine_type.strip()
                if cuisine_type.lower() != 'restaurant':
                    cuisine_counts[cuisine_type] = cuisine_counts.get(cuisine_type, 0) + 1
    else:
        # Fallback to old cuisine column if type column doesn't exist
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
    
    # Get area counts from SEO Area column
    area_counts = {}
    if 'SEO Area' in df.columns:
        for area in df['SEO Area'].dropna().unique():
            if pd.notna(area) and area:
                count = len(df[df['SEO Area'] == area])
                area_counts[area] = count
        # Sort areas by restaurant count (highest first)
        area_counts = dict(sorted(area_counts.items(), key=lambda x: x[1], reverse=True))
    else:
        # Fallback: create default area counts if SEO Area column doesn't exist
        area_counts = {'Quezon City': len(df)}
    
    return df, all_cuisines, area_counts

## Cache processed restaurant data at startup (after function definitions)
#try:
#    print("Loading and processing restaurant data at startup...")
#    start_time = time.time()
#    restaurants_df = pd.read_csv(OUTSCRAPER_FILE)
#    PROCESSED_DF, ALL_CUISINES, AREA_COUNTS = process_dataframe(restaurants_df)
#    print(f"Restaurant data processed in {time.time() - start_time:.2f} seconds")
#    
#    # Pre-calculate cuisine counts
#    CUISINE_COUNTS = {}
#    if 'type' in PROCESSED_DF.columns:
#        for cuisine_type in PROCESSED_DF['type'].dropna().unique():
#            count = len(PROCESSED_DF[PROCESSED_DF['type'] == cuisine_type])
#            CUISINE_COUNTS[cuisine_type] = count
#    else:
#        for cuisine in PROCESSED_DF['cuisine'].dropna().unique():
#            count = len(PROCESSED_DF[PROCESSED_DF['cuisine'] == cuisine])
#            CUISINE_COUNTS[cuisine] = count
#    
#    print("Startup caching completed successfully!")
#except Exception as e:
###    print(f"ERROR: Failed to load restaurant data at startup: {e}")
#    # Create empty defaults so app can still start
#    PROCESSED_DF = pd.DataFrame()
#    ALL_CUISINES = []
#    AREA_COUNTS = {}
#    CUISINE_COUNTS = {}

@app.route('/')
def home():
    try:
        # Read and process restaurant data
        restaurants_df = pd.read_csv(OUTSCRAPER_FILE)
        df, all_cuisines, area_counts = process_dataframe(restaurants_df)
        
        # Filter out permanently closed restaurants
        if 'business_status' in df.columns:
            closed_mask = df['business_status'].str.contains('CLOSED_PERMANENTLY', case=False, na=False)
            df = df[~closed_mask]
        
        # Pre-calculate cuisine counts
        cuisine_counts = {}
        if 'type' in df.columns:
            for cuisine_type in df['type'].dropna().unique():
                count = len(df[df['type'] == cuisine_type])
                cuisine_counts[cuisine_type] = count
        else:
            for cuisine in df['cuisine'].dropna().unique():
                count = len(df[df['cuisine'] == cuisine])
                cuisine_counts[cuisine] = count
        
        # Filter for top pick restaurants for display
        df = df[df['top_pick'] == True]
        
        return render_template('home.html', df=df.to_dict('records'), cuisine_counts=cuisine_counts, area_counts=area_counts, all_cuisines=all_cuisines)
    except Exception as e:
        print(f"Error in home route: {e}")
        return render_template('home.html', df=[], cuisine_counts={}, area_counts={}, all_cuisines=[])

@app.route('/all-restaurants')
def all_restaurants_page():
    # Get page number from query parameter, default to 1
    page = request.args.get('page', 1, type=int)
    per_page = 12

    try:
        # Read and process restaurant data
        restaurants_df = pd.read_csv(OUTSCRAPER_FILE)
        df, all_cuisines, area_counts = process_dataframe(restaurants_df)
        
        # Filter out permanently closed restaurants
        if 'business_status' in df.columns:
            closed_mask = df['business_status'].str.contains('CLOSED_PERMANENTLY', case=False, na=False)
            df = df[~closed_mask]
        
        # Pre-calculate cuisine counts
        cuisine_counts = {}
        if 'type' in df.columns:
            for cuisine_type in df['type'].dropna().unique():
                count = len(df[df['type'] == cuisine_type])
                cuisine_counts[cuisine_type] = count
        else:
            for cuisine in df['cuisine'].dropna().unique():
                count = len(df[df['cuisine'] == cuisine])
                cuisine_counts[cuisine] = count

        # Sort by rating and reviews (high to low)
        if 'rating' in df.columns and 'reviews' in df.columns:
            df = df.sort_values(by=['rating', 'reviews'], ascending=[False, False]).reset_index(drop=True)

        total_count = len(df)

        # Ensure page bounds
        total_pages = (total_count + per_page - 1) // per_page if total_count else 1
        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages

        # Slice current page
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_count)
        paginated = df.iloc[start_idx:end_idx].to_dict('records')

        # Simple pagination helper (same structure as cuisine pages)
        class Pagination:
            def __init__(self, page, per_page, total_count):
                self.page = page
                self.per_page = per_page
                self.total = total_count
                self.pages = total_pages
                self.has_prev = page > 1
                self.has_next = page < total_pages
                self.prev_num = page - 1
                self.next_num = page + 1
                self.first = start_idx + 1 if total_count else 0
                self.last = end_idx

            def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
                last = 0
                for num in range(1, self.pages + 1):
                    if num <= left_edge or \
                       (num > self.page - left_current - 1 and num < self.page + right_current) or \
                       num > self.pages - right_edge:
                        if last + 1 != num:
                            yield None
                        yield num
                        last = num

        pagination = Pagination(page, per_page, total_count)

        return render_template(
            'all_restaurants_new.html',
            df=paginated,
            cuisine_counts=cuisine_counts,
            area_counts=area_counts,
            all_cuisines=all_cuisines,
            pagination=pagination,
        )
    except Exception as e:
        print(f"Error in all_restaurants route: {e}")
        return render_template('all_restaurants_new.html', df=[], pagination={}, cuisine_counts={}, area_counts={}, all_cuisines=[])

# Accept trailing-slash URL and redirect to canonical without slash
@app.route('/all-restaurants/')
def all_restaurants_page_slash():
    return redirect(url_for('all_restaurants_page'), code=301)

@app.route('/cuisine/<cuisine>')
def cuisine_page(cuisine):
    # Get page number from query parameter, default to 1
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Show 12 restaurants per page (3 rows of 4 cards)
    # Get area filter from query parameter
    area_filter = request.args.get('area', None)
    

    
    # Read and process the data
    df = pd.read_csv(DATA_FILE)
    df, all_cuisines, area_counts = process_dataframe(df)
    
    # Convert URL-friendly name back to display name
    cuisine_name = cuisine.replace('-', ' ').title()
    print(f"\nDebug - Requested cuisine: {cuisine_name}")
    
    # Filter restaurants by cuisine type
    if 'type' in df.columns:
        mask = df['type'].str.lower() == cuisine_name.lower()
        cuisine_restaurants = df[mask].copy() if pd.notna(df['type']).any() else pd.DataFrame()
    else:
        # Fallback to old cuisine column if type column doesn't exist
        mask = df['cuisine'].str.lower() == cuisine_name.lower()
        cuisine_restaurants = df[mask].copy() if pd.notna(df['cuisine']).any() else pd.DataFrame()
    
    # Filter out permanently closed restaurants
    if 'business_status' in cuisine_restaurants.columns:
        closed_mask = cuisine_restaurants['business_status'].str.contains('CLOSED_PERMANENTLY', case=False, na=False)
        cuisine_restaurants = cuisine_restaurants[~closed_mask]
        print(f"Debug - Filtered out permanently closed restaurants, remaining: {len(cuisine_restaurants)} restaurants")
    
    # Apply area filter if specified
    if area_filter:
        # Find the area name from the slug
        area_name = None
        for area in df['SEO Area'].dropna().unique():
            if pd.notna(area) and area:
                area_slug = area.lower().replace(' ', '-').replace('/', '-').replace('.', '').replace('(', '').replace(')', '')
                if area_slug == area_filter:
                    area_name = area
                    break
        
        if area_name:
            # Filter by both cuisine and area
            area_mask = df['SEO Area'] == area_name
            cuisine_restaurants = cuisine_restaurants[area_mask]
            print(f"Debug - Filtered by area: {area_name}, found {len(cuisine_restaurants)} restaurants")
    
    # Ensure price and features are properly formatted first
    if 'range' in cuisine_restaurants.columns:
        cuisine_restaurants['price'] = cuisine_restaurants['range'].apply(
            lambda x: str(x).count('₱') if pd.notna(x) else '1'
        )
    else:
        cuisine_restaurants['price'] = cuisine_restaurants.apply(
            lambda row: '1' if cuisine_name.lower() == 'fast food' else extract_price_range(row['about']),
            axis=1
        )
    
    # Extract and format features
    cuisine_restaurants['features'] = cuisine_restaurants['about'].apply(extract_service_options_from_about)
    

    

    

    
    if cuisine_restaurants.empty:
        print(f"Debug - No restaurants found for cuisine: {cuisine_name}")
        # Get basic data for 404 template
        df = pd.read_csv(DATA_FILE)
        df, all_cuisines, area_counts = process_dataframe(df)
        return render_template('404.html', 
                             all_cuisines=all_cuisines,
                             area_counts=area_counts), 404
    

    
    # Get cuisine counts for display
    if 'type' in df.columns:
        cuisine_counts = df['type'].value_counts().to_dict()
    else:
        cuisine_counts = df['cuisine'].value_counts().to_dict()
    
    # Price range labels
    price_labels = ['Budget-friendly', 'Mid-range', 'High-end', 'Fine dining']
    
    # Get all possible features
    all_features = set()
    for features in cuisine_restaurants['features']:
        if isinstance(features, list):
            all_features.update(features)
    features = sorted(list(all_features))
    

    
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
                restaurant['about'] = json.dumps(restaurant['about'])
            else:
                restaurant['about'] = '{}'
        except:
            restaurant['about'] = '{}'
        
        # Map display name correctly (use name_for_emails if available)
        if 'name_for_emails' in restaurant:
            restaurant['display_name'] = restaurant['name_for_emails']
            restaurant['name'] = restaurant['name_for_emails']  # Also update the name field for compatibility
        else:
            restaurant['display_name'] = restaurant.get('name', 'Unknown Restaurant')
            restaurant['name'] = restaurant.get('name', 'Unknown Restaurant')  # Keep name field consistent
        
        # Map photo field correctly
        if 'photo_url' in restaurant and restaurant['photo_url']:
            restaurant['photo_url'] = restaurant['photo_url'].strip()
        elif 'photo' in restaurant and restaurant['photo']:
            restaurant['photo_url'] = restaurant['photo'].strip()

        else:
            restaurant['photo_url'] = url_for('static', filename='cuisine-images/default.svg', _external=True)
            print(f"DEBUG: No photo for {restaurant.get('name', 'Unknown')}, using default")
        
        # Map address field correctly
        if 'street' in restaurant:
            restaurant['street'] = restaurant['street']
        elif 'address' in restaurant:
            restaurant['street'] = restaurant['address']
        else:
            restaurant['street'] = 'Address not available'
        
        # Map hours field correctly
        if 'working_hours_dict' in restaurant:
            restaurant['hours'] = restaurant['working_hours_dict']
        elif 'hours' in restaurant:
            restaurant['hours'] = restaurant['hours']
        else:
            restaurant['hours'] = {}
        
        # Map phone field correctly
        if 'phone' in restaurant:
            restaurant['phone'] = restaurant['phone']
        elif '+63' in restaurant:
            restaurant['phone'] = restaurant['+63']
        else:
            restaurant['phone'] = None
        
        # Map website field correctly
        if 'site' in restaurant:
            restaurant['site'] = restaurant['site']
        else:
            restaurant['site'] = None
        
        # Map accessibility features
        if 'wheelchair_accessible' in restaurant:
            restaurant['wheelchair_accessible'] = restaurant['wheelchair_accessible']
        else:
            restaurant['wheelchair_accessible'] = False
            
        if 'good_for_kids' in restaurant:
            restaurant['good_for_kids'] = restaurant['good_for_kids']
        else:
            restaurant['good_for_kids'] = False
            
        if 'has_wifi' in restaurant:
            restaurant['has_wifi'] = restaurant['has_wifi']
        else:
            restaurant['has_wifi'] = False
            
        if 'has_high_chairs' in restaurant:
            restaurant['has_high_chairs'] = restaurant['has_high_chairs']
        else:
            restaurant['has_high_chairs'] = False
        
        # Map open/closed status
        if 'is_open' in restaurant:
            restaurant['is_open'] = restaurant['is_open']
        else:
            restaurant['is_open'] = False
        
        # Map current day
        if 'current_day' in restaurant:
            restaurant['current_day'] = restaurant['current_day']
        else:
            restaurant['current_day'] = 'Monday'  # Default fallback
        
        # Map jacky_pick field
        if 'jacky_pick' in restaurant:
            restaurant['jacky_pick'] = restaurant['jacky_pick']
        else:
            restaurant['jacky_pick'] = False
        
        # Map top_pick field
        if 'top_pick' in restaurant:
            restaurant['top_pick'] = restaurant['top_pick']
        else:
            restaurant['top_pick'] = False
        
        restaurant_data.append(restaurant)
    
    # Implement pagination
    filtered_count = len(cuisine_restaurants)
    total_pages = (filtered_count + per_page - 1) // per_page
    
    # Ensure page is within valid range
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages
    
    # Calculate start and end indices for current page
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, filtered_count)
    
    # Get restaurants for current page
    paginated_restaurants = restaurant_data[start_idx:end_idx]
    

    
    # Create pagination object
    class Pagination:
        def __init__(self, page, per_page, total_count):
            self.page = page
            self.per_page = per_page
            self.total = total_count
            self.pages = total_pages
            self.has_prev = page > 1
            self.has_next = page < total_pages
            self.prev_num = page - 1
            self.next_num = page + 1
            self.first = start_idx + 1
            self.last = end_idx
            
        def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
            """Generate page numbers for pagination display"""
            last = 0
            for num in range(1, self.pages + 1):
                if num <= left_edge or \
                   (num > self.page - left_current - 1 and num < self.page + right_current) or \
                   num > self.pages - right_edge:
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num
    
    pagination = Pagination(page, per_page, filtered_count)
    
    # Get popular areas for this cuisine using actual SEO Area values
    popular_areas = []
    popular_area_counts = {}
    
    # Count restaurants by their actual SEO Area
    for _, row in cuisine_restaurants.iterrows():
        seo_area = row.get('SEO Area', '')
        if pd.notna(seo_area) and seo_area:
            popular_area_counts[seo_area] = popular_area_counts.get(seo_area, 0) + 1
    
    # Sort areas by restaurant count and take top 4
    popular_areas = sorted(popular_area_counts.items(), key=lambda x: x[1], reverse=True)[:4]
    
    # Get similar cuisines (cuisines with similar names or categories)
    similar_cuisines = []
    for other_cuisine in all_cuisines:
        if other_cuisine != cuisine_name and pd.notna(other_cuisine):
            # Simple similarity logic - can be enhanced later
            if any(word in other_cuisine.lower() for word in cuisine_name.lower().split()):
                similar_cuisines.append(other_cuisine)
            elif any(word in cuisine_name.lower() for word in other_cuisine.lower().split()):
                similar_cuisines.append(other_cuisine)
    
    # Limit to 3 similar cuisines
    similar_cuisines = similar_cuisines[:3]
    
    # Get current date for "Last Updated"
    current_date = datetime.now().strftime("%B %Y")
    
    return render_template('cuisine.html',
                         cuisine_name=cuisine_name,
                         restaurants=paginated_restaurants,  # Send only paginated restaurants
                         restaurant_count=filtered_count,  # Total count of all filtered restaurants
                         total_restaurants=filtered_count,  # Total count of all filtered restaurants
                         all_cuisines=all_cuisines,
                         cuisine_counts=cuisine_counts,
                         area_counts=area_counts,  # Add missing area_counts
                         price_labels=price_labels,
                         features=features,
                         popular_areas=popular_areas,
                         similar_cuisines=similar_cuisines,
                         current_date=current_date,
                         pagination=pagination)

@app.route('/<neighbourhood_slug>/')
def neighbourhood_page(neighbourhood_slug):
    try:
        # Read the CSV file
        df = pd.read_csv(DATA_FILE)
        
        # Process the dataframe
        df, all_cuisines, area_counts = process_dataframe(df)
        
        # Find the neighbourhood by slug
        neighbourhood_name = None
        
        # Check if SEO Area column exists
        if 'SEO Area' not in df.columns:
            return render_template('404.html', 
                                 all_cuisines=all_cuisines,
                                 area_counts=area_counts), 404
        
        # Find the neighbourhood by slug
        for area in df['SEO Area'].dropna().unique():
            if pd.notna(area) and area:
                # Use the exact same slug generation as the home template
                area_slug = area.lower().replace(' ', '-').replace('/', '-').replace('.', '').replace('(', '').replace(')', '')
                if area_slug == neighbourhood_slug:
                    neighbourhood_name = area
                    break
        
        if not neighbourhood_name:
            return render_template('404.html', 
                                 all_cuisines=all_cuisines,
                                 area_counts=area_counts), 404
        
        # Filter restaurants for this neighbourhood
        neighbourhood_restaurants = df[df['SEO Area'] == neighbourhood_name]
        
        # Filter out permanently closed restaurants
        if 'business_status' in neighbourhood_restaurants.columns:
            closed_mask = neighbourhood_restaurants['business_status'].str.contains('CLOSED_PERMANENTLY', case=False, na=False)
            neighbourhood_restaurants = neighbourhood_restaurants[~closed_mask]
        
        # Get cuisine counts for this neighbourhood
        neighbourhood_cuisine_counts = {}
        if 'type' in neighbourhood_restaurants.columns:
            for cuisine in neighbourhood_restaurants['type'].dropna().unique():
                count = len(neighbourhood_restaurants[neighbourhood_restaurants['type'] == cuisine])
                neighbourhood_cuisine_counts[cuisine] = count
        
        # Sort cuisines by count (highest first)
        neighbourhood_cuisine_counts = dict(sorted(neighbourhood_cuisine_counts.items(), key=lambda x: x[1], reverse=True))
        
        # Get all areas for nearby neighbourhoods
        all_areas = df['SEO Area'].dropna().value_counts().to_dict()
        
        # Find nearby neighbourhoods (exclude current one)
        nearby_areas = []
        for area, count in all_areas.items():
            if area != neighbourhood_name and pd.notna(area) and area:
                nearby_areas.append({'name': area, 'count': count, 'slug': area.lower().replace(' ', '-').replace('/', '-').replace('.', '').replace('(', '').replace(')', '')})
        
        # Sort by restaurant count and take top 3
        nearby_areas.sort(key=lambda x: x['count'], reverse=True)
        nearby_areas = nearby_areas[:3]
        
        # Process restaurant data for display
        restaurants_data = []
        for _, row in neighbourhood_restaurants.iterrows():
            try:
                restaurant = {}
                
                # Map display name
                if pd.notna(row.get('name_for_emails')) and row.get('name_for_emails'):
                    restaurant['display_name'] = row['name_for_emails']
                else:
                    restaurant['display_name'] = row.get('name', 'Unknown Restaurant')
                
                # Map other fields
                restaurant['name'] = restaurant['display_name']
                restaurant['name_for_emails'] = row.get('name_for_emails', restaurant['display_name'])
                restaurant['cuisine'] = row.get('type', 'Unknown Cuisine')
                # Handle price field - get from 'range' column and convert to numeric
                price_value = row.get('range')
                if price_value is not None and str(price_value).lower() != 'nan' and str(price_value).strip() != '':
                    # Count the peso symbols (₱) to get the price level
                    price_str = str(price_value)
                    if '₱' in price_str or 'â‚±' in price_str:
                        # Count the symbols to determine price level
                        price_level = price_str.count('₱') + price_str.count('â‚±')
                        restaurant['price'] = price_level if price_level > 0 else 1
                    else:
                        # Try to convert to int if it's a number
                        try:
                            restaurant['price'] = int(price_value)
                        except (ValueError, TypeError):
                            restaurant['price'] = 1
                else:
                    restaurant['price'] = 1
                restaurant['rating'] = row.get('rating', 0)
                restaurant['reviews'] = row.get('reviews', 0)
                restaurant['photo_url'] = row.get('photo_url') if pd.notna(row.get('photo_url')) and row.get('photo_url') else row.get('photo', '')
                restaurant['street'] = row.get('street') if pd.notna(row.get('street')) and row.get('street') else row.get('address', '')
                
                # Handle hours field properly - ensure it's a dictionary or None
                hours_data = row.get('hours') if pd.notna(row.get('hours')) and row.get('hours') else row.get('working_hours', '')
                if pd.isna(hours_data) or not hours_data:
                    restaurant['hours'] = None
                elif isinstance(hours_data, str):
                    try:
                        # Try to parse as JSON if it's a string
                        import json
                        restaurant['hours'] = json.loads(hours_data)
                    except:
                        restaurant['hours'] = None
                elif isinstance(hours_data, dict):
                    restaurant['hours'] = hours_data
                else:
                    restaurant['hours'] = None
                
                restaurant['phone'] = format_phone_number(row.get('+63')) if pd.notna(row.get('+63')) and row.get('+63') else None
                restaurant['site'] = row.get('site') if pd.notna(row.get('site')) and row.get('site') else None
                restaurant['features'] = row.get('features', [])
                restaurant['is_open'] = row.get('is_open', False)
                restaurant['current_day'] = row.get('current_day', '')
                restaurant['jacky_pick'] = row.get('jacky_pick', False)
                restaurant['top_pick'] = row.get('top_pick', False)
                
                # Add accessibility and amenity fields
                restaurant['wheelchair_accessible'] = row.get('wheelchair_accessible', False)
                restaurant['good_for_kids'] = row.get('good_for_kids', False)
                restaurant['free_wifi'] = row.get('free_wifi', False)
                restaurant['high_chairs'] = row.get('high_chairs', False)
                
                # Add location fields for clickable addresses
                restaurant['latitude'] = row.get('latitude')
                restaurant['longitude'] = row.get('longitude')
                
                restaurants_data.append(restaurant)
            except Exception as e:
                continue
        
        # Sort restaurants by rating (highest first)
        restaurants_data.sort(key=lambda x: float(x['rating']) if x['rating'] else 0, reverse=True)
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = 12
        total_pages = (len(restaurants_data) + per_page - 1) // per_page
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_restaurants = restaurants_data[start_idx:end_idx]
        
        return render_template('neighbourhood.html',
                             neighbourhood_name=neighbourhood_name,
                             neighbourhood_slug=neighbourhood_slug,
                             restaurants=paginated_restaurants,
                             cuisine_counts=neighbourhood_cuisine_counts,
                             nearby_areas=nearby_areas,
                             total_restaurants=len(restaurants_data),
                             current_page=page,
                             total_pages=total_pages,
                             has_prev=page > 1,
                             has_next=page < total_pages,
                             all_cuisines=all_cuisines,
                             area_counts=area_counts)
    except Exception as e:
        return render_template('404.html', 
                             all_cuisines=all_cuisines,
                             area_counts=area_counts), 404

@app.route('/about')
def about():
    # Get all unique cuisines for the navigation
    df = pd.read_csv(DATA_FILE)
    df, all_cuisines, area_counts = process_dataframe(df)
    return render_template('about.html', all_cuisines=all_cuisines, area_counts=area_counts)

@app.route('/robots.txt')
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/blog')
def blog_index():
    # Get all unique cuisines for the navigation
    df = pd.read_csv(DATA_FILE)
    df, all_cuisines, area_counts = process_dataframe(df)
    return render_template('blog/index.html', posts=blog_posts, all_cuisines=all_cuisines, area_counts=area_counts)

@app.route('/blog/<slug>')
def blog_post(slug):
    # Get all unique cuisines for the navigation
    df = pd.read_csv(DATA_FILE)
    df, all_cuisines, area_counts = process_dataframe(df)
    
    # Special route for Tomas Morato article - use simple template
    if slug == 'tomas-morato-restaurants-2025':
        # Get Tomas Morato restaurants from the new CSV data
        tomas_morato_restaurants = []
        tomas_morato_mask = df['SEO Area'].str.contains('Tomas Morato', case=False, na=False)
        tomas_morato_df = df[tomas_morato_mask]
        
        for _, row in tomas_morato_df.iterrows():
            restaurant = {
                'name': row.get('name_for_emails', row.get('name', 'Unknown Restaurant')),
                'cuisine': row.get('type', 'Unknown Cuisine'),
                'rating': row.get('rating', 0),
                'reviews': row.get('reviews', 0),
                'address': row.get('street', row.get('address', '')),
                'photo': row.get('photo', ''),
                'phone': format_phone_number(row.get('+63', '')) if pd.notna(row.get('+63', '')) and row.get('+63', '') else '',
                'site': row.get('site', ''),
                'price_range': row.get('prices', '₱₱'),
                'hours': row.get('working_hours', ''),
                'subtypes': row.get('subtypes', ''),
                'top_pick': row.get('top pick', False),
                'verified': row.get('verified', 0),
                'business_status': row.get('business_status', ''),
                'category': row.get('category', ''),
                'features': []
            }
            tomas_morato_restaurants.append(restaurant)
        
        # Sort by rating (highest first) and take top 10
        tomas_morato_restaurants.sort(key=lambda x: float(x.get('rating', 0) or 0), reverse=True)
        tomas_morato_restaurants = tomas_morato_restaurants[:10]
        
        return render_template('blog/tomas-morato-simple.html', 
                             all_cuisines=all_cuisines, 
                             area_counts=area_counts,
                             tomas_morato_restaurants=tomas_morato_restaurants)
    
    # Special route for Vikings Restaurant article - MOVED TO TOP
    if slug == 'vikings-restaurant-sm-north':
        return render_template('blog/vikings-restaurant-sm-north.html', 
                             all_cuisines=all_cuisines, 
                             area_counts=area_counts)
    
    # Special route for Belcap's Big Tree Diner article
    if slug == 'belcaps-big-tree-diner':
        return render_template('blog/belcaps-big-tree-diner.html', 
                             all_cuisines=all_cuisines, 
                             area_counts=area_counts)
    
    # Special route for H&T Wine Gallery article
    if slug == 'ht-wine-gallery-quezon-city':
        return render_template('blog/ht-wine-gallery-quezon-city.html', 
                             all_cuisines=all_cuisines, 
                             area_counts=area_counts)
    
    # Special route for Wiltlover Cafe article
    if slug == 'wiltlover-cafe':
        return render_template('blog/wiltlover-cafe.html', 
                             all_cuisines=all_cuisines, 
                             area_counts=area_counts)
    
    # Special route for Banapple Pies & Cheesecakes article
    if slug == 'banapple-pies-cheesecakes':
        return render_template('blog/banapple-pies-cheesecakes.html', 
                             all_cuisines=all_cuisines, 
                             area_counts=area_counts)
    
    # Special route for SM Fairview restaurants article
    if slug == 'sm-fairview-restaurants-2025':
        # Get Fairview restaurants from the new CSV data
        fairview_restaurants = []
        fairview_mask = df['SEO Area'].str.contains('Fairview', case=False, na=False)
        fairview_df = df[fairview_mask]
        
        for _, row in fairview_df.iterrows():
            restaurant = {
                'name': row.get('name_for_emails', row.get('name', 'Unknown Restaurant')),
                'cuisine': row.get('type', 'Unknown Cuisine'),
                'rating': row.get('rating', 0),
                'reviews': row.get('reviews', 0),
                'address': row.get('street', row.get('address', '')),
                'photo_url': row.get('photo', ''),
                'phone': format_phone_number(row.get('+63', '')) if pd.notna(row.get('+63', '')) and row.get('+63', '') else '',
                'site': row.get('site', ''),
                'price_range': row.get('prices', '₱₱'),
                'hours': row.get('working_hours', ''),
                'subtypes': row.get('subtypes', ''),
                'top_pick': row.get('top pick', False),
                'verified': row.get('verified', 0),
                'business_status': row.get('business_status', ''),
                'category': row.get('category', ''),
                'features': []
            }
            fairview_restaurants.append(restaurant)
        
        # Sort by rating (highest first) and take top 20
        fairview_restaurants.sort(key=lambda x: float(x.get('rating', 0) or 0), reverse=True)
        fairview_restaurants = fairview_restaurants[:20]
        
        return render_template('blog/sm-fairview-restaurants-2025.html', 
                             all_cuisines=all_cuisines, 
                             area_counts=area_counts,
                             fairview_restaurants=fairview_restaurants)
    
    # Special route for SM North EDSA article
    if slug == 'sm-north-edsa-restaurants-2025':
        # Get SM North EDSA restaurants from the new CSV data
        sm_north_restaurants = []
        sm_north_mask = df['SEO Area'].str.contains('SM North', case=False, na=False)
        sm_north_df = df[sm_north_mask]
        
        for _, row in sm_north_df.iterrows():
            # Handle address - ensure it's a string, not NaN
            address = row.get('street', row.get('address', ''))
            if pd.isna(address) or address == 'nan' or str(address).strip() == '':
                address = ''
            else:
                address = str(address).strip()
            
            # Handle hours - parse JSON string to dict
            hours_raw = row.get('working_hours', '')
            hours_dict = {}
            if hours_raw and not pd.isna(hours_raw) and str(hours_raw).strip() != '':
                if isinstance(hours_raw, dict):
                    hours_dict = hours_raw
                elif isinstance(hours_raw, str) and hours_raw.startswith('{'):
                    try:
                        # Parse JSON string
                        hours_raw = hours_raw.replace("'", '"')
                        hours_dict = json.loads(hours_raw)
                    except:
                        hours_dict = {}
                else:
                    # Try using parse_working_hours function
                    hours_dict = parse_working_hours(hours_raw)
            hours = hours_dict if hours_dict else None
            
            restaurant = {
                'name': row.get('name_for_emails', row.get('name', 'Unknown Restaurant')),
                'cuisine': row.get('type', 'Unknown Cuisine'),
                'rating': row.get('rating', 0),
                'reviews': row.get('reviews', 0),
                'address': address,
                'photo_url': row.get('photo', ''),
                'phone': format_phone_number(row.get('+63', '')) if pd.notna(row.get('+63', '')) and row.get('+63', '') else '',
                'site': row.get('site', ''),
                'price_range': row.get('prices', '₱₱'),
                'hours': hours,
                'subtypes': row.get('subtypes', ''),
                'top_pick': row.get('top pick', False),
                'verified': row.get('verified', 0),
                'business_status': row.get('business_status', ''),
                'category': row.get('category', ''),
                'features': []
            }
            sm_north_restaurants.append(restaurant)
        
        # Sort by rating (highest first) and take top 20
        sm_north_restaurants.sort(key=lambda x: float(x.get('rating', 0) or 0), reverse=True)
        sm_north_restaurants = sm_north_restaurants[:20]
        
        # Get current day for hours display
        ph_time = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))
        current_day = ph_time.strftime('%A')
        
        return render_template('blog/sm-north-edsa-restaurants-2025.html',
                             current_day=current_day, 
                             all_cuisines=all_cuisines, 
                             area_counts=area_counts,
                             sm_north_restaurants=sm_north_restaurants)
    
    # Special route for Banawe article
    if slug == 'banawe-restaurants-2025':
        # Get Banawe restaurants from the new CSV data
        banawe_restaurants = []
        banawe_mask = df['SEO Area'].str.contains('Banawe', case=False, na=False)
        banawe_df = df[banawe_mask]
        
        for _, row in banawe_df.iterrows():
            restaurant = {
                'name': row.get('name_for_emails', row.get('name', 'Unknown Restaurant')),
                'cuisine': row.get('type', 'Unknown Cuisine'),
                'rating': row.get('rating', 0),
                'reviews': row.get('reviews', 0),
                'address': row.get('street', row.get('address', '')),
                'photo': row.get('photo', ''),
                'phone': format_phone_number(row.get('+63', '')) if pd.notna(row.get('+63', '')) and row.get('+63', '') else '',
                'site': row.get('site', ''),
                'price_range': row.get('prices', '₱₱'),
                'hours': row.get('working_hours', ''),
                'subtypes': row.get('subtypes', ''),
                'top_pick': row.get('top pick', False),
                'verified': row.get('verified', 0),
                'business_status': row.get('business_status', ''),
                'category': row.get('category', ''),
                'features': []
            }
            banawe_restaurants.append(restaurant)
        
        # Sort by rating (highest first) and take top 10
        banawe_restaurants.sort(key=lambda x: float(x.get('rating', 0) or 0), reverse=True)
        banawe_restaurants = banawe_restaurants[:10]
        
        return render_template('blog/banawe-restaurants-2025.html', 
                             all_cuisines=all_cuisines,
                             banawe_restaurants=banawe_restaurants,
                             area_counts=area_counts)
    
    # Special route for Maginhawa article
    if slug == 'maginhawa-restaurants-2025':
        # Get Maginhawa restaurants from the new CSV data
        maginhawa_restaurants = []
        maginhawa_mask = df['SEO Area'].str.contains('Maginhawa', case=False, na=False)
        maginhawa_df = df[maginhawa_mask]
        
        for _, row in maginhawa_df.iterrows():
            restaurant = {
                'name': row.get('name_for_emails', row.get('name', 'Unknown Restaurant')),
                'cuisine': row.get('type', 'Unknown Cuisine'),
                'rating': row.get('rating', 0),
                'reviews': row.get('reviews', 0),
                'address': row.get('street', row.get('address', '')),
                'photo': row.get('photo', ''),
                'phone': format_phone_number(row.get('+63', '')) if pd.notna(row.get('+63', '')) and row.get('+63', '') else '',
                'site': row.get('site', ''),
                'price_range': row.get('prices', '₱₱'),
                'hours': row.get('working_hours', ''),
                'subtypes': row.get('subtypes', ''),
                'top_pick': row.get('top pick', False),
                'verified': row.get('verified', 0),
                'business_status': row.get('business_status', ''),
                'category': row.get('category', ''),
                'features': []
            }
            maginhawa_restaurants.append(restaurant)
        
        # Sort by rating (highest first) and take top 10
        maginhawa_restaurants.sort(key=lambda x: float(x.get('rating', 0) or 0), reverse=True)
        maginhawa_restaurants = maginhawa_restaurants[:10]
        
        return render_template('blog/maginhawa-restaurants-2025.html', 
                             all_cuisines=all_cuisines, 
                             area_counts=area_counts,
                             maginhawa_restaurants=maginhawa_restaurants)
    
    # Special route for Eastwood Restaurants article
    if slug == 'eastwood-restaurants-2025':
        # Get Eastwood restaurants from the new CSV data
        eastwood_restaurants = []
        eastwood_mask = df['SEO Area'].str.contains('Eastwood', case=False, na=False)
        eastwood_df = df[eastwood_mask]
        
        # Get current day for highlighting
        ph_time = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))
        current_day = ph_time.strftime('%A')
        
        for _, row in eastwood_df.iterrows():
            # Parse hours from JSON string
            hours_raw = row.get('working_hours', '')
            hours_dict = {}
            if hours_raw and isinstance(hours_raw, str) and hours_raw.startswith('{'):
                try:
                    hours_dict = json.loads(hours_raw)
                except:
                    hours_dict = {}
            
            restaurant = {
                'name': row.get('name_for_emails', row.get('name', 'Unknown Restaurant')),
                'cuisine': row.get('type', 'Unknown Cuisine'),
                'rating': row.get('rating', 0),
                'reviews': row.get('reviews', 0),
                'address': row.get('street', row.get('address', '')),
                'photo': row.get('photo', ''),
                'phone': format_phone_number(row.get('+63', '')) if pd.notna(row.get('+63', '')) and row.get('+63', '') else '',
                'site': row.get('site', ''),
                'price_range': row.get('prices', '₱₱'),
                'hours': hours_dict,
                'hours_raw': hours_raw,  # Keep the raw string for backward compatibility
                'subtypes': row.get('subtypes', ''),
                'top_pick': row.get('top pick', False),
                'verified': row.get('verified', 0),
                'business_status': row.get('business_status', ''),
                'category': row.get('category', ''),
                'features': [],
                'is_open': is_currently_open(hours_dict),
                'current_day': current_day
            }
            eastwood_restaurants.append(restaurant)
        
        # Sort by rating (highest first) and take top 10
        eastwood_restaurants.sort(key=lambda x: float(x.get('rating', 0) or 0), reverse=True)
        eastwood_restaurants = eastwood_restaurants[:10]
        
        return render_template('blog/eastwood-restaurants-2025.html', 
                             all_cuisines=all_cuisines, 
                             area_counts=area_counts,
                             eastwood_restaurants=eastwood_restaurants,
                             current_day=current_day)
    
    # Special route for UPTC article
    if slug == 'up-town-center-restaurants-2025':
        return render_template('blog/up-town-center-restaurants-2025.html', 
                             all_cuisines=all_cuisines, 
                             area_counts=area_counts)
    
    # Special route for Filipino Restaurants article
    if slug == 'filipino-restaurants-quezon-city':
        # Read and process the data exactly like the main page
        df = pd.read_csv(DATA_FILE)
        df, all_cuisines, area_counts = process_dataframe(df)
        
        # Use the specific 10 Filipino restaurants from the article
        specific_restaurant_names = [
            'Romulo Café',
            'The Frazzled Cook',
            'Pino Restaurant',
            'Gubat QC',
            'Lola Ote Restaurant',
            'Mesa Tomas Morato',
            'Old Baguio Heritage Cafe and Restaurant',
            'Little Quiapo',
            'Provenciano',
            'Max\'s Restaurant Scout Tuason'
        ]
        
        # Find these specific restaurants in the database
        filipino_restaurants = []
        for restaurant_name in specific_restaurant_names:
            # Search for exact name match first
            mask = df['name'].str.contains(restaurant_name, case=False, na=False)
            
            # If no exact match, try to find the closest match
            if not mask.any():
                # Try to find restaurants that contain key words from the name
                key_words = [word for word in restaurant_name.split() if len(word) > 2]
                for word in key_words:
                    mask = df['name'].str.contains(word, case=False, na=False)
                    if mask.any():
                        break
            
            if mask.any():
                # Get all matches and find the best one
                matches = df[mask]
                # Sort by rating to get the best match
                matches = matches.sort_values('rating', ascending=False)
                row = matches.iloc[0]  # Take the highest rated match
                
                # Debug: Print what we found
                print(f"Found restaurant: {row.get('name')} for search: {restaurant_name}")
                restaurant = {
                    'name': restaurant_name,  # Use our exact name, not the CSV name
                    'cuisine': row.get('type', 'Filipino'),
                    'rating': row.get('rating', 4.0),
                    'reviews': row.get('reviews', 500),
                    'address': row.get('street', row.get('address', 'Quezon City')),
                    'photo': row.get('photo', row.get('photo_url', 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?q=80&w=800&auto=format&fit=crop')),
                    'phone': format_phone_number(row.get('+63', '')),
                    'site': row.get('site', ''),
                    'price_range': row.get('range', '₱₱'),
                    'hours': row.get('hours', {}),
                    'subtypes': '',
                    'top_pick': row.get('top_pick', True),
                    'verified': row.get('verified', 1),
                    'business_status': row.get('business_status', 'OPERATIONAL'),
                    'category': row.get('category', 'Restaurant'),
                    'features': row.get('features', []),
                    'wheelchair_accessible': row.get('wheelchair_accessible', False),
                    'good_for_kids': row.get('good_for_kids', False),
                    'has_wifi': row.get('has_wifi', False),
                    'has_high_chairs': row.get('has_high_chairs', False)
                }
                
                # Calculate open status and time until open
                restaurant['is_open'] = is_currently_open(restaurant['hours'])
                restaurant['time_until_open'] = get_time_until_open(restaurant['hours'])
                
                filipino_restaurants.append(restaurant)
            else:
                # If restaurant not found in database, create a default entry
                print(f"No match found for: {restaurant_name}, using default")
                restaurant = {
                    'name': restaurant_name,
                    'cuisine': 'Filipino',
                    'rating': 4.0,
                    'reviews': 500,
                    'address': 'Quezon City',
                    'photo': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?q=80&w=800&auto=format&fit=crop',
                    'phone': '',
                    'site': '',
                    'price_range': '₱₱',
                    'hours': {'Monday': '11:00 AM - 9:00 PM', 'Tuesday': '11:00 AM - 9:00 PM', 'Wednesday': '11:00 AM - 9:00 PM', 'Thursday': '11:00 AM - 9:00 PM', 'Friday': '11:00 AM - 10:00 PM', 'Saturday': '11:00 AM - 10:00 PM', 'Sunday': '11:00 AM - 9:00 PM'},
                    'subtypes': '',
                    'top_pick': True,
                    'verified': 1,
                    'business_status': 'OPERATIONAL',
                    'category': 'Restaurant',
                    'features': ['Dine-in', 'Takeout'],
                    'wheelchair_accessible': False,
                    'good_for_kids': False,
                    'has_wifi': False,
                    'has_high_chairs': False,
                    'is_open': False,
                    'time_until_open': 'Opens tomorrow'
                }
                filipino_restaurants.append(restaurant)
        
        return render_template('blog/filipino-restaurants-quezon-city.html', 
                             all_cuisines=all_cuisines, 
                             area_counts=area_counts,
                             filipino_restaurants=filipino_restaurants)
    
    post = next((p for p in blog_posts if p['slug'] == slug), None)
    if not post:
        abort(404)
    # Find related posts (sharing at least one keyword, not itself)
    related_posts = [
        p for p in blog_posts
        if p['slug'] != slug and set(p['keywords']) & set(post['keywords'])
    ]
    return render_template('blog/post.html', post=post, related_posts=related_posts, request=request, all_cuisines=all_cuisines, area_counts=area_counts)

@app.route('/restaurant/<slug>')
def restaurant_details(slug):
    # Get all unique cuisines for the navigation
    df = pd.read_csv(DATA_FILE)
    df, all_cuisines, area_counts = process_dataframe(df)
    
    # Get restaurant data
    restaurant = restaurants_data.get(slug)
    if not restaurant:
        abort(404)
    
    # Generate SEO-friendly title and description
    title = f"{restaurant['name']} – {restaurant['city']} Restaurant"
    description = f"Visit {restaurant['name']} in {restaurant['city']}. "
    if restaurant['rating']:
        description += f"Rated {restaurant['rating']}/5 stars with {int(restaurant['reviews'])} reviews. "
    description += f"Located at {restaurant['address']}."
    
    # Generate Google Maps URL
    maps_url = ""
    if restaurant['latitude'] and restaurant['longitude']:
        maps_url = f"https://www.google.com/maps?q={restaurant['latitude']},{restaurant['longitude']}"
    elif restaurant['address']:
        maps_url = f"https://www.google.com/maps/search/{restaurant['address'].replace(' ', '+')}"
    
    return render_template('restaurant.html', 
                         restaurant=restaurant,
                         all_cuisines=all_cuisines,
                         area_counts=area_counts,
                         title=title,
                         description=description,
                         maps_url=maps_url)

@app.route('/food-tour', methods=['GET', 'POST'])
def food_tour():
    """Food Tour Builder - Generate a mini food tour based on cuisine, budget, and area"""
    # Get all unique cuisines for the navigation
    df = pd.read_csv(DATA_FILE)
    df, all_cuisines, area_counts = process_dataframe(df)
    
    tour = []
    premium_tour_data = None
    form_data = {
        'cuisine': '',
        'budget': '',
        'area': ''
    }
    
    if request.method == 'POST':
        # Get form inputs
        cuisine = request.form.get('cuisine', '').strip()
        budget_str = request.form.get('budget', '').strip()
        area = request.form.get('area', '').strip()
        
        # Store form data for re-display
        form_data = {
            'cuisine': cuisine,
            'budget': budget_str,
            'area': area
        }
        
        # Convert budget to int safely
        try:
            budget = int(budget_str) if budget_str else 0
        except ValueError:
            budget = 0
        
        # Build tour if we have valid inputs
        if cuisine and budget > 0:
            try:
                # Load fresh restaurant data
                restaurants_df = pd.read_csv(DATA_FILE)
                
                # Use premium tour builder for enhanced experience
                try:
                    premium_tour_data = build_premium_tour(
                        restaurants_df=restaurants_df,
                        cuisine=cuisine,
                        budget=budget,
                        area=area if area else None,
                        num_stops=3,  # Default to 3 stops
                        vibes=None,
                        dietary_restrictions=None,
                        starting_point=None
                    )
                    
                    # Convert premium tour format to legacy format for backward compatibility
                    if premium_tour_data and 'stops' in premium_tour_data and premium_tour_data['stops']:
                        tour = []
                        for idx, stop in enumerate(premium_tour_data['stops'], 1):
                            tour.append({
                                'label': f"Stop {idx}: {stop['category'].title()}",
                                'name': stop['name'],
                                'lat': stop['latitude'],
                                'lng': stop['longitude'],
                                'area': stop['area_label'],
                                'avg_price': stop['estimated_cost'],
                                'slug': generate_restaurant_slug(stop['name']),
                                'address': stop['address'],
                                'price_range': '₱₱' if stop['estimated_cost'] < 800 else '₱₱₱',
                                'travel_time': stop.get('travel_time_minutes', 0),
                                'why_visit': stop.get('why_visit', ''),
                                'vibe_tags': stop.get('vibe_tags', []),
                                'dishes': stop.get('dishes', [])  # Include dishes from premium tour
                            })
                        # premium_tour_data is kept for template - don't set to None
                    else:
                        # Fallback to basic tour builder if premium fails
                        tour = build_food_tour(restaurants_df, cuisine, budget, area if area else None)
                        premium_tour_data = None
                except Exception as e:
                    print(f"Error in premium tour builder: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback to basic tour builder
                    tour = build_food_tour(restaurants_df, cuisine, budget, area if area else None)
                    premium_tour_data = None
                
                # Log the tour request (fail silently if logging fails)
                try:
                    log_file = 'food_tour_logs.csv'
                    log_exists = os.path.exists(log_file)
                    
                    import csv
                    with open(log_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        if not log_exists:
                            # Write header if file doesn't exist
                            writer.writerow(['timestamp', 'cuisine', 'budget', 'area', 'main_stop_name', 'dessert_stop_name'])
                        
                        main_name = tour[0]['name'] if len(tour) > 0 else ''
                        dessert_name = tour[1]['name'] if len(tour) > 1 else ''
                        
                        writer.writerow([
                            datetime.now().isoformat(),
                            cuisine,
                            budget,
                            area if area else '',
                            main_name,
                            dessert_name
                        ])
                except Exception as e:
                    # Silently fail logging - don't break the user experience
                    pass
                    
            except Exception as e:
                # If tour building fails, tour will be empty list
                print(f"Error building tour: {e}")
                import traceback
                traceback.print_exc()
                pass
    
    # Get menu suggestions if tour exists
    menu_suggestions = get_tour_menu_suggestions(tour) if tour else {}
    
    return render_template('food_tour.html',
                         tour=tour,
                         premium_tour=premium_tour_data,
                         form_data=form_data,
                         menu_suggestions=menu_suggestions,
                         all_cuisines=all_cuisines,
                         area_counts=area_counts)

@app.route('/blog/best-coffee-shops-quezon-city')
def coffee_shops_blog():
    # Get all unique cuisines for the navigation
    df = pd.read_csv(DATA_FILE)
    df, all_cuisines, area_counts = process_dataframe(df)
    return render_template('blog/best-coffee-shops-quezon-city.html', 
                         all_cuisines=all_cuisines, 
                         area_counts=area_counts)

if __name__ == '__main__':
    app.run(debug=True) 
