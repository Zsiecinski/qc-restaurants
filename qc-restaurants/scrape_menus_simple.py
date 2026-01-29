#!/usr/bin/env python3
"""
Menu Scraper for QC Restaurants - Standard Library Only Version
Uses only built-in modules for maximum compatibility.
"""

import json
import re
import time
import urllib.request
from urllib.parse import urljoin, urlparse
import urllib.error
import pandas as pd
import os
import sys
import ssl

# Disable SSL verification for some sites
import urllib.request
ssl._create_default_https_context = ssl._create_unverified_context

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, 'restaurants.xlsx.csv')
MENU_FILE = os.path.join(BASE_DIR, 'data', 'menus.json')

# User-Agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def load_restaurants():
    """Load restaurant data from CSV."""
    print(f"Loading restaurants from {CSV_FILE}...")
    try:
        import pandas as pd
        df = pd.read_csv(CSV_FILE)
        print(f"Loaded {len(df)} restaurants")
        return df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None

def fetch_url(url):
    """Fetch URL content with error handling."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None

def extract_prices(text):
    """Extract price patterns from text."""
    prices = re.findall(r'₱[\d,]+|₱\s*[\d]+|PHP\s*[\d,]+', text)
    return list(set(prices))

def extract_menu_items_foodpanda(html):
    """Extract menu items from Foodpanda page (simple pattern matching)."""
    items = []
    
    # Look for price patterns near item names
    price_patterns = [
        r'([₱₱₱₱₱][^<]{0,50})',
        r'>([^<]{5,50})<[^>]*>[^<]*([₱][\d,]+)',
    ]
    
    # Simple approach: look for price patterns and get surrounding text
    price_matches = re.findall(r'>([^<]{2,30}?)\s*([₱][\d]{2,4})<', html, re.IGNORECASE)
    
    for name, price in price_matches[:15]:
        if len(name) > 2:
            items.append({
                'name': name.strip(),
                'price': price.strip(),
                'description': ''
            })
    
    return {'source': 'foodpanda', 'items': items}

def extract_menu_items_generic(html):
    """Generic menu extraction using common patterns."""
    items = []
    
    # Look for menu item patterns
    patterns = [
        # Pattern: name ... price
        (r'([A-Z][a-zA-Z\s&\'-]{5,40}[a-zA-Z])\s*([₱][\d]{2,4})', 'price_after'),
        # Pattern: price ... name  
        (r'([₱][\d]{2,4})\s*([A-Z][a-zA-Z\s&\'-]{5,40}[a-zA-Z])', 'price_before'),
    ]
    
    for pattern, style in patterns:
        matches = re.findall(pattern, html)
        for match in matches:
            if style == 'price_after':
                name, price = match
            else:
                price, name = match
            
            name = name.strip()
            price = price.strip()
            
            if len(name) > 3 and len(price) > 0:
                # Check for duplicates
                if not any(i['name'] == name for i in items):
                    items.append({
                        'name': name,
                        'price': price,
                        'description': ''
                    })
    
    return {'source': 'website', 'items': items[:20]}

def scrape_restaurant_menu(row):
    """Scrape menu for a single restaurant."""
    name = row.get('name', 'Unknown')
    
    # Get URL (menu_link or site)
    menu_url = row.get('menu_link', '') or row.get('site', '')
    
    if not menu_url or str(menu_url) == 'nan':
        return None
    
    menu_url = str(menu_url)
    if not menu_url.startswith('http'):
        return None
    
    print(f"  Scraping: {name[:40]}...")
    
    # Fetch page
    html = fetch_url(menu_url)
    if not html:
        return None
    
    # Extract menu items based on URL pattern
    url_lower = menu_url.lower()
    
    if 'foodpanda' in url_lower:
        menu_data = extract_menu_items_foodpanda(html)
    else:
        menu_data = extract_menu_items_generic(html)
    
    if menu_data.get('items'):
        return menu_data
    
    return None

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
    print(f"\nSaved to {MENU_FILE}")

def main(limit=20):
    """Main function to scrape menus."""
    print("=" * 60)
    print("QC Restaurants Menu Scraper (Standard Library)")
    print("=" * 60)
    
    # Load existing data
    menus_data = load_existing_menus()
    existing_count = len(menus_data.get('menus', {}))
    print(f"Existing menus: {existing_count}\n")
    
    # Load restaurants
    df = load_restaurants()
    if df is None:
        return
    
    # Scrape menus
    scraped = 0
    total_items = 0
    
    for idx, row in df.head(limit).iterrows():
        name = row.get('name', 'Unknown')
        
        # Skip if already scraped
        if name in menus_data.get('menus', {}):
            print(f"  Skipping (exists): {name[:40]}")
            continue
        
        # Scrape menu
        menu_data = scrape_restaurant_menu(row)
        
        if menu_data and menu_data.get('items'):
            menus_data['menus'][name] = {
                'restaurant_id': str(row.get('place_id', '')),
                'menu_url': str(row.get('menu_link', '') or row.get('site', '')),
                'cuisine': str(row.get('type', '')),
                'area': str(row.get('SEO Area', '')),
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'data': menu_data
            }
            scraped += 1
            total_items += len(menu_data['items'])
            print(f"    ✓ {len(menu_data['items'])} items found")
        
        # Rate limiting
        time.sleep(0.5)
    
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
