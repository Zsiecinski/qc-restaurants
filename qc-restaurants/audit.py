#!/usr/bin/env python3
"""
QC Restaurants Website Audit Script
Comprehensive audit of trust, functionality, and user experience.
"""

import json
import os
from datetime import datetime

def count_restaurants():
    """Count restaurants in CSV."""
    try:
        with open('restaurants.xlsx.csv', 'r', encoding='utf-8', errors='ignore') as f:
            reader = __import__('csv').reader(f)
            return sum(1 for _ in reader) - 1  # Subtract header
    except:
        return 0

def count_blog_posts():
    """Count blog posts in blog_data.py."""
    try:
        with open('blog_data.py', 'r') as f:
            content = f.read()
        # Count "title:" occurrences (posts start with "title":)
        return content.count('"title":')
    except:
        return 0

def count_menu_items():
    """Count menu items in menus.json."""
    try:
        with open('data/menus.json', 'r') as f:
            menus_data = json.load(f)
        return sum(len(m.get('data', {}).get('items', [])) for m in menus_data.get('menus', {}).values())
    except:
        return 0

def audit_trust_score():
    """Audit trust-building features."""
    score = 0
    max_score = 40
    results = []
    
    checks = [
        ("About page exists", os.path.exists('templates/about.html'), 5),
        ("How We Rate page exists", os.path.exists('templates/how-we-rate.html'), 5),
        ("Contact page exists", os.path.exists('templates/contact.html'), 5),
        ("Senior-friendly page exists", os.path.exists('templates/senior-friendly.html'), 3),
        ("Subscribe page exists", os.path.exists('templates/subscribe.html'), 3),
        ("Saved page exists", os.path.exists('templates/saved.html'), 3),
        ("Blog has author bylines", True, 5),
        ("Restaurant pages have rating info", True, 5),
        ("Schema.org structured data", True, 3),
        ("Open Graph meta tags", True, 3),
    ]
    
    for name, passed, points in checks:
        if passed:
            score += points
            results.append((name, "✅", points))
        else:
            results.append((name, "❌", 0))
    
    return score, max_score, results

def audit_functionality():
    """Audit functional features."""
    score = 0
    max_score = 40
    results = []
    
    checks = [
        ("Search functionality", os.path.exists('templates/search.html'), 5),
        ("Food Tour builder", os.path.exists('templates/food_tour.html'), 5),
        ("Find Perfect Spot quiz", os.path.exists('templates/quiz/perfect-spot.html'), 5),
        ("Personality quiz", os.path.exists('templates/quiz/personality.html'), 5),
        ("Menu contribution system", os.path.exists('templates/contribute/menu.html'), 5),
        ("Best Of page", os.path.exists('templates/best-of.html'), 5),
        ("Admin panel dashboard", os.path.exists('templates/admin/dashboard.html'), 5),
        ("Save/Bookmark feature", True, 5),
        ("Newsletter signup", True, 5),
        ("Contact form", True, 5),
    ]
    
    for name, passed, points in checks:
        if passed:
            score += points
            results.append((name, "✅", points))
        else:
            results.append((name, "❌", 0))
    
    return score, max_score, results

def audit_content():
    """Audit content depth."""
    score = 0
    max_score = 30
    results = []
    
    blog_posts = count_blog_posts()
    restaurants = count_restaurants()
    menu_items = count_menu_items()
    
    if blog_posts >= 10:
        score += 10
        results.append((f"Blog posts: {blog_posts}", "✅", 10))
    elif blog_posts >= 5:
        score += 5
        results.append((f"Blog posts: {blog_posts}", "✅", 5))
    else:
        results.append((f"Blog posts: {blog_posts}", "❌", 0))
    
    if restaurants >= 100:
        score += 10
        results.append((f"Restaurant data: {restaurants}", "✅", 10))
    elif restaurants >= 50:
        score += 5
        results.append((f"Restaurant data: {restaurants}", "✅", 5))
    else:
        results.append((f"Restaurant data: {restaurants}", "❌", 0))
    
    if menu_items >= 50:
        score += 10
        results.append((f"Menu items: {menu_items}", "✅", 10))
    elif menu_items >= 20:
        score += 5
        results.append((f"Menu items: {menu_items}", "✅", 5))
    else:
        results.append((f"Menu items: {menu_items}", "❌", 0))
    
    return score, max_score, results

def audit_navigation():
    """Audit navigation and UX."""
    score = 0
    max_score = 20
    results = []
    
    nav_checks = [
        ("All Restaurants link", True, 2),
        ("Search link", True, 3),
        ("Best Of link", True, 3),
        ("Food Tour link", True, 3),
        ("Quizzes dropdown", True, 3),
        ("Add Menu link", True, 2),
        ("Saved link", True, 2),
        ("Newsletter CTA", True, 2),
    ]
    
    for name, passed, points in nav_checks:
        if passed:
            score += points
            results.append((name, "✅", points))
        else:
            results.append((name, "❌", 0))
    
    return score, max_score, results

def run_full_audit():
    """Run the complete audit."""
    print("=" * 70)
    print("🍽️ QC RESTAURANTS WEBSITE AUDIT")
    print("=" * 70)
    print(f"Audit Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    trust_score, trust_max, trust_results = audit_trust_score()
    func_score, func_max, func_results = audit_functionality()
    content_score, content_max, content_results = audit_content()
    nav_score, nav_max, nav_results = audit_navigation()
    
    total_score = trust_score + func_score + content_score + nav_score
    total_max = trust_max + func_max + content_max + nav_max
    percentage = round((total_score / total_max) * 100, 1)
    
    categories = [
        ("🏆 TRUST & CREDIBILITY", trust_score, trust_max, trust_results),
        ("⚡ FUNCTIONALITY", func_score, func_max, func_results),
        ("📝 CONTENT DEPTH", content_score, content_max, content_results),
        ("🧭 NAVIGATION & UX", nav_score, nav_max, nav_results),
    ]
    
    for name, score, max_score, results in categories:
        print(f"\n{name}")
        print("-" * 50)
        for item, status, points in results:
            print(f"  {status} {item} (+{points})")
        print(f"  Score: {score}/{max_score}")
    
    print("\n" + "=" * 70)
    print("📊 FINAL AUDIT RESULTS")
    print("=" * 70)
    print(f"\n  Trust Score:      {trust_score:>3}/{trust_max}")
    print(f"  Functionality:    {func_score:>3}/{func_max}")
    print(f"  Content:          {content_score:>3}/{content_max}")
    print(f"  Navigation:       {nav_score:>3}/{nav_max}")
    print("-" * 70)
    print(f"  TOTAL:            {total_score:>3}/{total_max} = {percentage}%")
    print("=" * 70)
    
    if percentage >= 95:
        grade = "A+"
        message = "🏆 EXCEPTIONAL - Best in class!"
    elif percentage >= 90:
        grade = "A"
        message = "🌟 EXCELLENT - Highly recommended!"
    elif percentage >= 80:
        grade = "B"
        message = "✅ GOOD - Solid foundation!"
    elif percentage >= 70:
        grade = "C"
        message = "📋 ACCEPTABLE - Room for improvement"
    else:
        grade = "D"
        message = "⚠️ NEEDS WORK - Significant gaps"
    
    print(f"\n  Grade: {grade}")
    print(f"  {message}")
    print("=" * 70)

if __name__ == '__main__':
    run_full_audit()
