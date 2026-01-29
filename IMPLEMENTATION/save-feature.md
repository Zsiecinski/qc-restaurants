# Save/Bookmark Feature - Implementation Plan

## Feature Scope
Allow users to save restaurants to a favorites list using browser localStorage (no login required).

## Success Criteria
1. "Save" button appears on each restaurant card
2. Clicking saves to localStorage
3. "Saved" indicator shows on saved restaurants
4. "My Saved Restaurants" page displays saved items
5. Works across sessions (persists in localStorage)

## Implementation

### JavaScript (add to base.html or custom.js)
```javascript
// Save a restaurant
function saveRestaurant(id, name, area, cuisine) {
    const saved = JSON.parse(localStorage.getItem('savedRestaurants') || '[]');
    if (!saved.find(r => r.id === id)) {
        saved.push({ id, name, area, cuisine, savedAt: new Date().toISOString() });
        localStorage.setItem('savedRestaurants', JSON.stringify(saved));
        return true;
    }
    return false;
}

// Remove a restaurant
function removeRestaurant(id) {
    let saved = JSON.parse(localStorage.getItem('savedRestaurants') || '[]');
    saved = saved.filter(r => r.id !== id);
    localStorage.setItem('savedRestaurants', JSON.stringify(saved));
    return true;
}

// Get all saved
function getSavedRestaurants() {
    return JSON.parse(localStorage.getItem('savedRestaurants') || '[]');
}

// Check if saved
function isSaved(id) {
    const saved = JSON.parse(localStorage.getItem('savedRestaurants') || '[]');
    return saved.some(r => r.id === id);
}
```

### HTML Changes
Add to each restaurant card:
```html
<button class="btn btn-sm btn-outline-danger save-btn" data-id="123" data-name="Restaurant Name" data-area="Tomas Morato" data-cuisine="Filipino">
    <i class="far fa-heart"></i> Save
</button>
```

### My Saved Page
Create `/saved` route showing all saved restaurants with remove functionality.
