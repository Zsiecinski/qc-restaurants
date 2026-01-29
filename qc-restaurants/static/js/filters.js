/**
 * Restaurant Filters JavaScript
 * Handles filtering, sorting, and search for All Restaurants page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get all filter checkboxes
    const priceFilters = document.querySelectorAll('input[name="price"]');
    const featureFilters = document.querySelectorAll('input[name="features"]');
    const seniorFilters = document.querySelectorAll('input[name="senior"]');
    const searchInput = document.getElementById('restaurantSearch');
    const sortSelect = document.getElementById('sortBy');
    const restaurantCards = document.querySelectorAll('.restaurant-card');
    
    // Add event listeners
    priceFilters.forEach(checkbox => checkbox.addEventListener('change', applyFilters));
    featureFilters.forEach(checkbox => checkbox.addEventListener('change', applyFilters));
    seniorFilters.forEach(checkbox => checkbox.addEventListener('change', applyFilters));
    
    if (searchInput) {
        searchInput.addEventListener('input', debounce(applyFilters, 300));
    }
    
    if (sortSelect) {
        sortSelect.addEventListener('change', applyFilters);
    }
    
    /**
     * Main filter function - applies all active filters
     */
    function applyFilters() {
        const selectedPrices = getCheckedValues(priceFilters);
        const selectedFeatures = getCheckedValues(featureFilters);
        const selectedSenior = getCheckedValues(seniorFilters);
        const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
        const sortBy = sortSelect ? sortSelect.value : 'rating';
        
        restaurantCards.forEach(card => {
            let show = true;
            
            // Price filter
            if (selectedPrices.length > 0) {
                const cardPrice = parseInt(card.dataset.price || '0');
                if (!selectedPrices.includes(cardPrice)) {
                    show = false;
                }
            }
            
            // Feature filter
            if (show && selectedFeatures.length > 0) {
                const cardFeatures = JSON.parse(card.dataset.features || '[]');
                const hasAllFeatures = selectedFeatures.every(f => cardFeatures.includes(f));
                if (!hasAllFeatures) {
                    show = false;
                }
            }
            
            // Senior filter
            if (show && selectedSenior.length > 0) {
                // Check for wheelchair
                if (selectedSenior.includes('wheelchair')) {
                    const wheelchairBadge = card.querySelector('.feature-badge.wheelchair');
                    if (!wheelchairBadge) show = false;
                }
                
                // Check for parking (look for parking-related features)
                if (show && selectedSenior.includes('parking')) {
                    const features = JSON.parse(card.dataset.features || '[]');
                    const hasParking = features.some(f => 
                        f.toLowerCase().includes('parking') || 
                        f.toLowerCase().includes('park')
                    );
                    // This is a placeholder - actual implementation depends on data
                    if (!hasParking && !card.dataset.features?.includes('Parking')) {
                        // Don't filter out if we can't determine - show it
                    }
                }
                
                // Check for quiet (not currently in data - placeholder)
                if (show && selectedSenior.includes('quiet')) {
                    // This would require noise level data - show all for now
                }
                
                // Check for comfortable seating (not currently in data - placeholder)
                if (show && selectedSenior.includes('seating')) {
                    // This would require seating comfort data - show all for now
                }
            }
            
            // Search filter
            if (show && searchTerm) {
                const name = card.querySelector('.restaurant-name')?.textContent?.toLowerCase() || '';
                const address = card.querySelector('.address')?.textContent?.toLowerCase() || '';
                const cuisine = card.querySelector('.cuisine-badge')?.textContent?.toLowerCase() || '';
                
                if (!name.includes(searchTerm) && 
                    !address.includes(searchTerm) && 
                    !cuisine.includes(searchTerm)) {
                    show = false;
                }
            }
            
            // Show/hide card
            card.style.display = show ? '' : 'none';
        });
        
        // Apply sorting
        applySorting(sortBy);
        
        // Update results count
        updateResultsCount();
    }
    
    /**
     * Sort visible cards
     */
    function applySorting(sortBy) {
        const container = document.querySelector('.restaurant-list');
        if (!container) return;
        
        const cards = Array.from(container.querySelectorAll('.restaurant-card:visible'));
        
        cards.sort((a, b) => {
            switch (sortBy) {
                case 'rating':
                    return parseFloat(b.dataset.rating || 0) - parseFloat(a.dataset.rating || 0);
                case 'reviews':
                    return parseInt(b.dataset.reviews || 0) - parseInt(a.dataset.reviews || 0);
                case 'price-low':
                    return parseInt(a.dataset.price || 0) - parseInt(b.dataset.price || 0);
                case 'price-high':
                    return parseInt(b.dataset.price || 0) - parseInt(a.dataset.price || 0);
                default:
                    return 0;
            }
        });
        
        cards.forEach(card => container.appendChild(card));
    }
    
    /**
     * Update the visible results count
     */
    function updateResultsCount() {
        const visibleCount = document.querySelectorAll('.restaurant-card:visible').length;
        const countElement = document.getElementById('resultsCount');
        if (countElement) {
            countElement.textContent = `${visibleCount} restaurants`;
        }
    }
    
    /**
     * Get checked checkbox values
     */
    function getCheckedValues(checkboxes) {
        return Array.from(checkboxes)
            .filter(cb => cb.checked)
            .map(cb => {
                const val = cb.value;
                return isNaN(val) ? val : parseInt(val);
            });
    }
    
    /**
     * Debounce function for search input
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Initialize
    applyFilters();
});
