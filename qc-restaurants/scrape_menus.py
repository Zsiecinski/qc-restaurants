#!/usr/bin/env python3
"""
Menu Scraper for QC Restaurants - Works on any Python installation!
Uses csv module (built-in) with proper handling of quoted CSV fields.
"""

import json
import re
import time
import urllib.request
import urllib.error
import csv
import os
import sys
import ssl

# Disable SSL verification for some sites
ssl._create_default_https_context = ssl._create_unverified_context

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, 'restaurants.xlsx.csv')
MENU_FILE = os.path.join(BASE_DIR, 'data', 'menus.json')

# User-Agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

def fetch_url(url):
    """Fetch URL content with error handling."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8', errors='ignore')
    except:
        return None

def extract_menu_items(html, source='generic'):
    """Extract menu items from HTML using regex patterns."""
    items = []
    
    # Common price patterns
    price_patterns = [
        r'([A-Z][a-zA-Z0-9\s&\'-]{4,35}[a-zA-Z])\s*([₱][\d]{2,4})',
        r'([₱][\d]{2,4})\s*([A-Z][a-zA-Z0-9\s&\'-]{4,35}[a-zA-Z])',
    ]
    
    for pattern in price_patterns:
        matches = re.findall(pattern, html)
        for match in matches:
            name, price = match
            name = name.strip()
            price = price.strip()
            
            if len(name) > 3 and len(price) > 0:
                # Skip if looks like a header or random text
                if any(skip in name.lower() for skip in ['home', 'menu', 'about', 'contact', 'order', 'delivery', 'login', 'sign']):
                    continue
                if not any(c.isalpha() for c in name):
                    continue
                if not any(c.islower() or c.isupper() for c in name):
                    continue
                    
                if not any(i['name'] == name for i in items):
                    items.append({
                        'name': name,
                        'price': price,
                        'description': ''
                    })
    
    return {'source': source, 'items': items[:15]}

def scrape_restaurant_menu(name, menu_url, site_url):
    """Scrape menu for a restaurant."""
    url = menu_url if menu_url and menu_url.startswith('http') else site_url
    if not url or not url.startswith('http'):
        return None
    
    print(f"  {name[:32]:<32}...", end=' ')
    sys.stdout.flush()
    
    # Fetch page
    html = fetch_url(url)
    if not html:
        print("no response")
        return None
    
    # Detect source and extract
    url_lower = url.lower()
    if 'foodpanda' in url_lower:
        source = 'foodpanda'
    elif 'grabfood' in url_lower:
        source = 'grabfood'
    else:
        source = 'website'
    
    menu_data = extract_menu_items(html, source)
    
    if menu_data.get('items'):
        print(f"✓ {len(menu_data['items'])} items")
        return menu_data
    
    print("no menu data")
    return None

def load_restaurants():
    """Load restaurant data from CSV using csv module."""
    print(f"Loading restaurants from {CSV_FILE}...")
    
    restaurants = []
    try:
        with open(CSV_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                name = row.get('name', '').strip()
                if not name:
                    continue
                
                restaurants.append({
                    'name': name,
                    'menu_url': row.get('menu_link', '').strip(),
                    'site': row.get('site', '').strip(),
                    'cuisine': row.get('type', '').strip(),
                    'area': row.get('SEO Area', '').strip(),
                    'place_id': row.get('place_id', '').strip()
                })
        
        print(f"Loaded {len(restaurants)} restaurants\n")
        return restaurants
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def load_existing_menus():
    """Load existing menu data from JSON file."""
    if os.path.exists(MENU_FILE):
        try:
            with open(MENU_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'metadata': {'last_updated': None, 'total_restaurants_with_menus': 0}, 'menus': {}}

def save_menus(menus_data):
    """Save menu data to JSON file."""
    os.makedirs(os.path.dirname(MENU_FILE), exist_ok=True)
    with open(MENU_FILE, 'w') as f:
        json.dump(menus_data, f, indent=2)
    print(f"\n✓ Saved to {MENU_FILE}")

def main(limit=30):
    """Main scraping function."""
    print("=" * 60)
    print("QC Restaurants Menu Scraper")
    print("=" * 60)
    
    # Load existing data
    menus_data = load_existing_menus()
    existing = len(menus_data.get('menus', {}))
    print(f"Existing entries: {existing}\n")
    
    # Load restaurants
    restaurants = load_restaurants()
    if not restaurants:
        return
    
    # Scrape menus
    scraped = 0
    total_items = 0
    
    for row in restaurants[:limit]:
        name = row['name']
        
        # Skip if already scraped
        if name in menus_data.get('menus', {}):
            continue
        
        # Scrape
        menu_data = scrape_restaurant_menu(name, row['menu_url'], row['site'])
        
        if menu_data and menu_data.get('items'):
            menus_data['menus'][name] = {
                'restaurant_id': row['place_id'],
                'menu_url': row['menu_url'] or row['site'],
                'cuisine': row['cuisine'],
                'area': row['area'],
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'data': menu_data
            }
            scraped += 1
            total_items += len(menu_data['items'])
        
        time.sleep(0.3)
    
    # Save
    menus_data['metadata']['last_updated'] = time.strftime('%Y-%m-%d')
    menus_data['metadata']['total_restaurants_with_menus'] = existing + scraped
    save_menus(menus_data)
    
    print(f"\n{'=' * 60}")
    print(f"RESULTS:")
    print(f"  New restaurants scraped: {scraped}")
    print(f"  Total menu items: {total_items}")
    print(f"  Total with menus: {menus_data['metadata']['total_restaurants_with_menus']}")
    print(f"{'=' * 60}")

if __name__ == '__main__':
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    main(limit)
