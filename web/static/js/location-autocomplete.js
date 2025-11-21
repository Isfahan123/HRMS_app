/**
 * Location Autocomplete Component
 * Provides Geoapify-powered location suggestions for input fields
 */

class LocationAutocomplete {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.options = {
            country: options.country || null,  // e.g., 'MY' for Malaysia
            minChars: options.minChars || 3,
            debounceMs: options.debounceMs || 300,
            onSelect: options.onSelect || null,
            ...options
        };
        
        this.debounceTimer = null;
        this.selectedPlaceId = null;
        this.dropdownElement = null;
        
        this.init();
    }
    
    init() {
        // Create dropdown element
        this.createDropdown();
        
        // Add event listeners
        this.input.addEventListener('input', (e) => this.handleInput(e));
        this.input.addEventListener('blur', () => this.hideDropdown(200));
        this.input.addEventListener('focus', () => {
            if (this.input.value.length >= this.options.minChars) {
                this.performSearch(this.input.value);
            }
        });
        
        // Prevent dropdown from closing when clicking on it
        this.dropdownElement.addEventListener('mousedown', (e) => {
            e.preventDefault();
        });
    }
    
    createDropdown() {
        this.dropdownElement = document.createElement('div');
        this.dropdownElement.className = 'location-autocomplete-dropdown';
        this.dropdownElement.style.cssText = `
            position: absolute;
            background: white;
            border: 1px solid #ccc;
            border-top: none;
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        `;
        
        // Insert dropdown after input
        this.input.parentElement.style.position = 'relative';
        this.input.parentElement.appendChild(this.dropdownElement);
    }
    
    handleInput(e) {
        const value = e.target.value.trim();
        
        // Clear selected place when user types
        this.selectedPlaceId = null;
        
        // Clear previous timer
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        
        // Hide dropdown if input too short
        if (value.length < this.options.minChars) {
            this.hideDropdown();
            return;
        }
        
        // Debounce search
        this.debounceTimer = setTimeout(() => {
            this.performSearch(value);
        }, this.options.debounceMs);
    }
    
    async performSearch(query) {
        try {
            // Build query params
            let url = `/api/location/autocomplete?query=${encodeURIComponent(query)}`;
            if (this.options.country) {
                url += `&country=${encodeURIComponent(this.options.country)}`;
            }
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success && data.data && data.data.length > 0) {
                this.showResults(data.data);
            } else {
                this.hideDropdown();
            }
        } catch (error) {
            console.error('Location autocomplete error:', error);
            this.hideDropdown();
        }
    }
    
    showResults(results) {
        // Clear existing results
        this.dropdownElement.innerHTML = '';
        
        // Add results
        results.forEach(result => {
            const item = document.createElement('div');
            item.className = 'location-autocomplete-item';
            item.textContent = result.description;
            item.style.cssText = `
                padding: 8px 12px;
                cursor: pointer;
                border-bottom: 1px solid #eee;
            `;
            
            // Hover effect
            item.addEventListener('mouseenter', () => {
                item.style.backgroundColor = '#f0f0f0';
            });
            item.addEventListener('mouseleave', () => {
                item.style.backgroundColor = 'white';
            });
            
            // Click handler
            item.addEventListener('click', () => {
                this.selectResult(result);
            });
            
            this.dropdownElement.appendChild(item);
        });
        
        // Position and show dropdown
        const rect = this.input.getBoundingClientRect();
        this.dropdownElement.style.width = `${rect.width}px`;
        this.dropdownElement.style.display = 'block';
    }
    
    selectResult(result) {
        // Update input value
        this.input.value = result.description;
        this.selectedPlaceId = result.place_id;
        
        // Call onSelect callback if provided
        if (this.options.onSelect) {
            this.options.onSelect(result);
        }
        
        // Hide dropdown
        this.hideDropdown();
    }
    
    hideDropdown(delay = 0) {
        if (delay > 0) {
            setTimeout(() => {
                this.dropdownElement.style.display = 'none';
            }, delay);
        } else {
            this.dropdownElement.style.display = 'none';
        }
    }
    
    getSelectedPlaceId() {
        return this.selectedPlaceId;
    }
    
    destroy() {
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        if (this.dropdownElement && this.dropdownElement.parentElement) {
            this.dropdownElement.parentElement.removeChild(this.dropdownElement);
        }
    }
}

// Helper function to initialize autocomplete on multiple elements
function initLocationAutocomplete(selector, options = {}) {
    const elements = document.querySelectorAll(selector);
    const instances = [];
    
    elements.forEach(element => {
        instances.push(new LocationAutocomplete(element, options));
    });
    
    return instances.length === 1 ? instances[0] : instances;
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { LocationAutocomplete, initLocationAutocomplete };
}
