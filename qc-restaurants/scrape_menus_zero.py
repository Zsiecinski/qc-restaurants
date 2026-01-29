#!/usr/bin/env python3
"""
Menu Scraper for QC Restaurants - Zero Dependencies Version
Uses only Python standard library - no pip install needed!
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
import io

# Disable SSL verification for some sites
ssl._create_default_https_context = ssl._create_unverified_context

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, 'restaurants.xlsx.csv')
MENU_FILE = os.path.join(BASE_DIR, 'data', 'menus.json')

# User-Agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def fetch_url(url):
    """Fetch URL content with error handling."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None

def extract_menu_items_foodpanda(html):
    """Extract menu items from Foodpanda page."""
    items = []
    
    # Pattern: item name followed by price
    price_matches = re.findall(r'>([^<]{3,35}?)\s*([₱][\d]{2,4})<', html, re.IGNORECASE)
    
    for name, price in price_matches[:15]:
        name = name.strip()
        if len(name) > 3 and len(price) > 0:
            if not any(i['name'] == name for i in items):
                items.append({
                    'name': name,
                    'price': price.strip(),
                    'description': ''
                })
    
    return {'source': 'foodpanda', 'items': items}

def extract_menu_items_generic(html):
    """Generic menu extraction using common patterns."""
    items = []
    
    # Look for price patterns with item names
    patterns = [
        r'([A-Z][a-zA-Z\s&\'-]{5,40}[a-zA-Z])\s*([₱][\d]{2,4})',
        r'([₱][\d]{2,4})\s*([A-Z][a-zA-Z\s&\'-]{5,40}[a-zA-Z])',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html)
        for match in matches:
            name, price = match
            name = name.strip()
            price = price.strip()
            
            if len(name) > 3 and len(price) > 0:
                if not any(i['name'] == name for i in items):
                    items.append({
                        'name': name,
                        'price': price,
                        'description': ''
                    })
    
    return {'source': 'website', 'items': items[:20]}

def scrape_restaurant_menu(name, menu_url):
    """Scrape menu for a restaurant."""
    if not menu_url or not str(menu_url).startswith('http'):
        return None
    
    print(f"  Scraping: {name[:35]}...")
    
    # Fetch page
    html = fetch_url(menu_url)
    if not html:
        return None
    
    # Extract menu items
    url_lower = menu_url.lower()
    
    if 'foodpanda' in url_lower:
        menu_data = extract_menu_items_foodpanda(html)
    else:
        menu_data = extract_menu_items_generic(html)
    
    if menu_data.get('items'):
        return menu_data
    
    return None

def load_csv_restaurants():
    """Load restaurant data from CSV using csv module (no pandas)."""
    print(f"Loading restaurants from {CSV_FILE}...")
    
    restaurants = []
    try:
        with open(CSV_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            # Try to detect dialect
            sample = f.read(8192)
            f.seek(0)
            
            reader = csv.DictReader(io.StringIO(sample))
            fieldnames = reader.fieldnames
            
            # Find column indices
            name_idx = None
            menu_idx = None
            site_idx = None
            type_idx = None
            area_idx = None
            place_idx = None
            
            for i, fname in enumerate(fieldnames):
                fname_lower = fname.lower().strip()
                if 'name' in fname_lower and 'email' not in fname_lower:
                    name_idx = i
                if 'menu' in fname_lower:
                    menu_idx = i
                if fname_lower == 'site':
                    site_idx = i
                if fname_lower == 'type' or 'cuisine' in fname_lower:
                    type_idx = i
                if 'seo area' in fname_lower or 'area' in fname_lower:
                    area_idx = i
                if 'place_id' in fname_lower:
                    place_idx = i
            
            # Read full file
            f.seek(0)
            reader = csv.reader(f)
            header = next(reader)
            
            for row in reader:
                if len(row) <= max(filter(None, [name_idx, menu_idx, site_idx])):
                    continue
                
                name = row[name_idx].strip() if name_idx is not None and name_idx < len(row) else ''
                menu_url = row[menu_idx].strip() if menu_idx is not None and menu_idx < len(row) else ''
                site = row[site_idx].strip() if site_idx is not None and site_idx < len(row) else ''
                cuisine = row[type_idx].strip() if type_idx is not None and type_idx < len(row) else ''
                area = row[area_idx].strip() if area_idx is not None and area_idx < len(row) else ''
                place_id = row[place_idx].strip() if place_idx is not None and place_idx < len(row) else ''
                
                if name:
                    restaurants.append({
                        'name': name,
                        'menu_url': menu_url if menu_url.startswith('http') else site if site.startswith('http') else '',
                        'cuisine': cuisine,
                        'area': area,
                        'place_id': place_id
                    })
        
        print(f"Loaded {len(restaurants)} restaurants\n")
        return restaurants
        
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return []

def load_existing_menus():
    """Load existing menu data from JSON file."""
    if os.path.exists(MENU_FILE):
        try:
            with open(MENU_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'metadata': {
            'last_updated': None,
            'total_restaurants_with_menus': 0
        },
        'menus': {}
    }

def save_menus(menus_data):
    """Save menu data to JSON file."""
    os.makedirs(os.path.dirname(MENU_FILE), exist_ok=True)
    with open(MENU_FILE, 'w') as f:
        json.dump(menus_data, f, indent=2)
    print(f"\n✓ Saved to {MENU_FILE}")

def main(limit=20):
    """Main function to scrape menus."""
    print("=" * 60)
    print("QC Restaurants Menu Scraper (Zero Dependencies)")
    print("=" * 60)
    
    # Load existing data
    menus_data = load_existing_menus()
    existing_count = len(menus_data.get('menus', {}))
    print(f"Existing menus: {existing_count}\n")
    
    # Load restaurants
    restaurants = load_csv_restaurants()
    if not restaurants:
        return
    
    # Scrape menus
    scraped = 0
    total_items = 0
    
    for i, row in enumerate(restaurants[:limit]):
        name = row['name']
        
        # Skip if already scraped
        if name in menus_data.get('menus', {}):
            print(f"  Skipping (exists): {name[:35]}")
            continue
        
        # Scrape menu
        menu_data = scrape_restaurant_menu(name, row['menu_url'])
        
        if menu_data and menu_data.get('items'):
            menus_data['menus'][name] = {
                'restaurant_id': row['place_id'],
                'menu_url': row['menu_url'],
                'cuisine': row['cuisine'],
                'area': row['area'],
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'data': menu_data
            }
            scraped += 1
            total_items += len(menu_data['items'])
            print(f"    ✓ {len(menu_data['items'])} items")
        
        # Rate limiting
        time.sleep(0.3)
    
    # Update metadata
    menus_data['metadata']['last_updated'] = time.strftime('%Y-%m-%d')
    menus_data['metadata']['total_restaurants_with_menus'] = existing_count + scraped
    
    # Save
    save_menus(menus_data)
    
    print(f"\n{'=' * 60}")
    print(f"RESULTS:")
    print(f"  New restaurants scraped: {scraped}")
    print(f"  Total menu items collected: {total_items}")
    print(f"  Total with menus now: {menus_data['metadata']['total_restaurants_with_menus']}")
    print(f"{'=' * 60}")
    
    return menus_data

if __name__ == '__main__':
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    main(limit)
