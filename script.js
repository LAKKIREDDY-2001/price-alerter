// View Management - Initialize after DOM is loaded
let views = {};
let navItems = [];
let currentFilter = 'all';
let selectedTrackers = new Set();
let currentTimePeriod = '7d';

document.addEventListener('DOMContentLoaded', () => {
    // Apply dark mode on load
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
        const darkModeToggle = document.getElementById('dark-mode');
        if (darkModeToggle) {
            darkModeToggle.checked = true;
        }
    }
    
    // Initialize views object after DOM is ready
    views = {
        'new-alert': document.getElementById('view-new-alert'),
        'my-trackers': document.getElementById('view-my-trackers'),
        'price-trends': document.getElementById('view-price-trends'),
        'settings': document.getElementById('view-settings')
    };

    navItems = document.querySelectorAll('.nav-item');

    // Add click handlers to nav items
    navItems.forEach((item) => {
        item.addEventListener('click', () => {
            const viewName = item.dataset.view;
            if (viewName) {
                switchView(viewName);
            }
        });
    });

    // Initialize trackers and currency preference
    initializeTrackers();
    initializeCurrencyPreference();
    updateStats();

    // Auth forms
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }
});

async function handleLogin(e) {
    e.preventDefault();
    const email = e.target.email.value;
    const password = e.target.password.value;

    const response = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });

    if (response.ok) {
        window.location.href = '/dashboard';
    } else {
        alert('Login failed!');
    }
}

async function handleSignup(e) {
    e.preventDefault();
    const username = e.target.username.value;
    const email = e.target.email.value;
    const password = e.target.password.value;

    const response = await fetch('/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
    });

    if (response.ok) {
        window.location.href = '/login';
    } else {
        alert('Signup failed!');
    }
}


// Switch view function
function switchView(viewName) {
    navItems.forEach(nav => nav.classList.remove('active'));
    
    navItems.forEach(item => {
        if (item.dataset.view === viewName) {
            item.classList.add('active');
        }
    });
    
    Object.values(views).forEach(view => view && view.classList.remove('active'));
    if (views[viewName]) {
        views[viewName].classList.add('active');
    }
}

// Tracker storage
let trackers = JSON.parse(localStorage.getItem('trackers')) || [];
let currentProduct = null;
let currentPrice = null;
let currentCurrency = 'INR';
let currentCurrencySymbol = '₹';

// Load settings
let savedCurrency = localStorage.getItem('preferredCurrency');
if (savedCurrency) {
    currentCurrency = savedCurrency.split(' ')[0];
    currentCurrencySymbol = savedCurrency.includes('USD') ? '$' : savedCurrency.includes('GBP') ? '£' : savedCurrency.includes('EUR') ? '€' : '₹';
}

// Settings functions
function saveSettings() {
    const settings = {
        'push-notifications': document.getElementById('push-notifications')?.checked,
        'email-alerts': document.getElementById('email-alerts')?.checked,
        'refresh-interval': document.getElementById('refresh-interval')?.value,
        'auto-delete': document.getElementById('auto-delete')?.value,
        'drop-percentage': document.getElementById('drop-percentage')?.value,
        'site-preference': document.getElementById('site-preference')?.value,
        'compact-view': document.getElementById('compact-view')?.checked
    };
    localStorage.setItem('settings', JSON.stringify(settings));
    showToast('Settings saved successfully!');
}

function connectTelegram() {
    showToast('Telegram integration coming soon!');
}

function connectWhatsApp() {
    showToast('WhatsApp integration coming soon!');
}

function toggleTheme() {
    const isDark = document.getElementById('dark-mode')?.checked;
    document.body.classList.toggle('dark-mode', isDark);
    localStorage.setItem('darkMode', isDark);
}

function exportData() {
    const data = {
        trackers: trackers,
        settings: JSON.parse(localStorage.getItem('settings') || '{}'),
        exportedAt: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `price-tracker-backup-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Data exported successfully!');
}

function importData(input) {
    const file = input.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                if (data.trackers) {
                    trackers = data.trackers;
                    localStorage.setItem('trackers', JSON.stringify(trackers));
                    initializeTrackers();
                    updateStats();
                    showToast('Data imported successfully!');
                }
            } catch (err) {
                showToast('Invalid backup file!');
            }
        };
        reader.readAsText(file);
    }
}

function clearAllData() {
    if (confirm('Are you sure you want to delete all trackers? This cannot be undone!')) {
        trackers = [];
        localStorage.setItem('trackers', JSON.stringify(trackers));
        initializeTrackers();
        updateStats();
        showToast('All data cleared!');
    }
}

// Filter functions
function setFilter(filter) {
    currentFilter = filter;
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.filter === filter);
    });
    renderTrackers();
}

function filterTrackers() {
    renderTrackers();
}

function sortTrackers() {
    renderTrackers();
}

// Update tracker stats
function updateStats() {
    const total = trackers.length;
    const active = trackers.filter(t => t.currentPrice > t.targetPrice).length;
    const reached = trackers.filter(t => t.currentPrice <= t.targetPrice).length;
    
    // Update sidebar stats
    const sidebarActive = document.getElementById('sidebar-active-trackers');
    const sidebarDeals = document.getElementById('sidebar-deals');
    if (sidebarActive) sidebarActive.textContent = total;
    if (sidebarDeals) sidebarDeals.textContent = reached;
    
    // Update filter counts
    const countAll = document.getElementById('count-all');
    if(countAll) countAll.textContent = total;
    const countActive = document.getElementById('count-active');
    if(countActive) countActive.textContent = active;
    const countReached = document.getElementById('count-reached');
    if(countReached) countReached.textContent = reached;
    
    // Update stats cards
    const totalTrackers = document.getElementById('total-trackers');
    if(totalTrackers) totalTrackers.textContent = total;
    const activeDeals = document.getElementById('active-deals');
    if(activeDeals) activeDeals.textContent = reached;
    
    // Calculate average savings
    const avgSavings = document.getElementById('avg-savings');
    if (trackers.length > 0) {
        let totalSavings = 0;
        trackers.forEach(t => {
            const savings = ((t.currentPrice - t.targetPrice) / t.currentPrice) * 100;
            if (savings > 0) totalSavings += savings;
        });
        if(avgSavings) avgSavings.textContent = Math.round(totalSavings / trackers.length) + '%';
    } else {
        if(avgSavings) avgSavings.textContent = '0%';
    }
}

// Render trackers
function renderTrackers() {
    const container = document.getElementById('trackers-list');
    if (!container) return;
    const searchTerm = document.getElementById('tracker-search')?.value.toLowerCase() || '';
    const sortBy = document.getElementById('sort-trackers')?.value || 'date';
    
    let filtered = trackers;
    
    // Apply filter
    if (currentFilter === 'active') {
        filtered = trackers.filter(t => t.currentPrice > t.targetPrice);
    } else if (currentFilter === 'reached') {
        filtered = trackers.filter(t => t.currentPrice <= t.targetPrice);
    }
    
    // Apply search
    if (searchTerm) {
        filtered = filtered.filter(t => 
            t.name.toLowerCase().includes(searchTerm) || 
            t.url.toLowerCase().includes(searchTerm)
        );
    }
    
    // Apply sort
    filtered = [...filtered].sort((a, b) => {
        if (sortBy === 'name') return a.name.localeCompare(b.name);
        if (sortBy === 'price') return a.currentPrice - b.currentPrice;
        return parseInt(b.id) - parseInt(a.id);
    });
    
    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fa fa-rocket"></i>
                <h3>No trackers found!</h3>
                <p>${searchTerm ? 'Try a different search term' : 'Create your first price alert to start saving money'}</p>
                ${!searchTerm ? '<button class="action-btn" onclick="switchView(\'new-alert\')">Create Tracker</button>' : ''}
            </div>
        `;
        return;
    }
    
    container.innerHTML = filtered.map(tracker => {
        const isReached = tracker.currentPrice <= tracker.targetPrice;
        const statusClass = isReached ? 'status-reached' : (tracker.currentPrice <= tracker.targetPrice * 1.1 ? 'status-active' : 'status-waiting');
        const statusText = isReached ? 'Target Reached!' : 'Active';
        const isSelected = selectedTrackers.has(tracker.id);
        
        return `
            <div class="tracker-card" data-id="${tracker.id}">
                <div class="tracker-header">
                    <div class="tracker-info">
                        <h4>${tracker.name}</h4>
                        <p class="tracker-url">${tracker.url.substring(0, 50)}...</p>
                    </div>
                    <div class="tracker-checkbox ${isSelected ? 'checked' : ''}" onclick="toggleSelectTracker('${tracker.id}', this)">
                        ${isSelected ? '<i class="fa fa-check" style="font-size: 12px;"></i>' : ''}
                    </div>
                </div>
                <div class="tracker-prices">
                    <div class="price-info current">
                        <span class="price-label">Current</span>
                        <span class="price-amount">${tracker.currencySymbol}${tracker.currentPrice}</span>
                    </div>
                    <div class="price-status ${statusClass}">${statusText}</div>
                    <div class="price-info target">
                        <span class="price-label">Target</span>
                        <span class="price-amount">${tracker.currencySymbol}${tracker.targetPrice}</span>
                    </div>
                </div>
                <div class="tracker-actions">
                    <button class="tracker-action" onclick="viewPriceTrend('${tracker.id}')">
                        <i class="fa fa-line-chart"></i> Trends
                    </button>
                    <button class="tracker-action" onclick="removeTrackerById('${tracker.id}')">
                        <i class="fa fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    updateBulkActions();
}

function toggleSelectTracker(id, element) {
    if (selectedTrackers.has(id)) {
        selectedTrackers.delete(id);
        element.classList.remove('checked');
        element.innerHTML = '';
    } else {
        selectedTrackers.add(id);
        element.classList.add('checked');
        element.innerHTML = '<i class="fa fa-check" style="font-size: 12px;"></i>';
    }
    updateBulkActions();
}

function updateBulkActions() {
    const bulkActions = document.getElementById('bulk-actions');
    const count = selectedTrackers.size;
    if (bulkActions) {
        bulkActions.style.display = count > 0 ? 'flex' : 'none';
        document.getElementById('selected-count').textContent = `${count} selected`;
    }
}

function deleteSelected() {
    if (selectedTrackers.size === 0) return;
    if (confirm(`Delete ${selectedTrackers.size} selected trackers?`)) {
        trackers = trackers.filter(t => !selectedTrackers.has(t.id));
        localStorage.setItem('trackers', JSON.stringify(trackers));
        selectedTrackers.clear();
        renderTrackers();
        updateStats();
        showToast('Trackers deleted!');
    }
}

function exportTrackers() {
    exportData();
}

// Remove tracker function
function removeTracker(button) {
    const card = button.closest('.tracker-card');
    const trackerId = card.dataset.id;
    
    card.style.animation = 'fadeOut 0.3s ease forwards';
    setTimeout(() => {
        trackers = trackers.filter(t => t.id !== trackerId);
        localStorage.setItem('trackers', JSON.stringify(trackers));
        card.remove();
        renderTrackers();
        updateStats();
    }, 300);
}

function removeTrackerById(id) {
    if (confirm('Delete this tracker?')) {
        trackers = trackers.filter(t => t.id !== id);
        localStorage.setItem('trackers', JSON.stringify(trackers));
        renderTrackers();
        updateStats();
        showToast('Tracker deleted!');
    }
}

// Add tracker to list
function addTrackerToList(tracker) {
    renderTrackers();
}

// View price trend for a tracker
function viewPriceTrend(trackerId) {
    const tracker = trackers.find(t => t.id === trackerId);
    if (!tracker) return;
    
    // Switch to price trends view
    switchView('price-trends');
    
    // Update product preview
    const productPreview = document.getElementById('product-preview');
    productPreview.innerHTML = `
        <div class="product-image"><i class="fa fa-shopping-bag"></i></div>
        <div class="product-details">
            <h3>${tracker.name}</h3>
            <p>${tracker.url.substring(0, 60)}...</p>
        </div>
    `;
    
    // Update price comparison
    document.getElementById('original-price').textContent = `${tracker.currencySymbol}${tracker.currentPrice}`;
    document.getElementById('current-price').textContent = `${tracker.currencySymbol}${tracker.currentPrice}`;
    
    const savings = tracker.currentPrice - tracker.targetPrice;
    const savingsPercent = ((savings / tracker.currentPrice) * 100).toFixed(1);
    document.getElementById('savings-amount').textContent = `${tracker.currencySymbol}${savings.toFixed(0)} (${savingsPercent}%)`;
    
    // Update trend details
    document.getElementById('trend-lowest').textContent = `${tracker.currencySymbol}${tracker.targetPrice}`;
    document.getElementById('trend-highest').textContent = `${tracker.currencySymbol}${tracker.currentPrice}`;
    document.getElementById('trend-since').textContent = new Date(tracker.createdAt).toLocaleDateString();
    
    // Generate chart
    generateChart(tracker);
    
    // Update prediction
    updatePrediction(tracker);
    
    // Show buy now button if target reached
    document.getElementById('buy-now-btn').style.display = tracker.currentPrice <= tracker.targetPrice ? 'flex' : 'none';
}

// Time period filter
function setTimePeriod(period) {
    currentTimePeriod = period;
    document.querySelectorAll('.time-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.toLowerCase().includes(period));
    });
    
    // Re-render chart with new time period
    const preview = document.getElementById('product-preview');
    if (preview.querySelector('.product-details h3')?.textContent !== 'Select a tracker to view trends') {
        const trackerName = preview.querySelector('.product-details h3')?.textContent;
        const tracker = trackers.find(t => t.name === trackerName);
        if (tracker) {
            generateChart(tracker);
        }
    }
}

// Generate chart
function generateChart(tracker) {
    const chartContainer = document.querySelector('.chart-main');
    const prices = generatePriceHistory(tracker.currentPrice, tracker.targetPrice, currentTimePeriod);
    
    const maxPrice = Math.max(...prices);
    const minPrice = Math.min(...prices);
    
    chartContainer.innerHTML = `
        <div class="chart-placeholder">
            <div class="chart-line">
                ${prices.map(price => {
                    const height = ((price - minPrice) / (maxPrice - minPrice)) * 100;
                    return `<div class="chart-bar" style="height: ${Math.max(20, height)}%;" title="${tracker.currencySymbol}${price}"></div>`;
                }).join('')}
            </div>
            <div class="chart-labels">
                ${prices.map((_, i) => {
                    const labels = currentTimePeriod === '7d' 
                        ? ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                        : currentTimePeriod === '30d'
                        ? ['W1', 'W2', 'W3', 'W4']
                        : ['M1', 'M2', 'M3'];
                    return `<span>${labels[i % labels.length]}</span>`;
                }).join('')}
            </div>
        </div>
    `;
}

// Update prediction
function updatePrediction(tracker) {
    const prices = generatePriceHistory(tracker.currentPrice, tracker.targetPrice, currentTimePeriod);
    const trend = prices[prices.length - 1] - prices[0];
    const predictionCard = document.getElementById('prediction-card');
    const predictionText = document.getElementById('prediction-text');
    const confidence = document.getElementById('confidence');
    
    if (trend < 0) {
        predictionCard.style.background = 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)';
        predictionText.textContent = 'Price is likely to drop further!';
        confidence.textContent = '85%';
    } else if (trend > 0) {
        predictionCard.style.background = 'linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%)';
        predictionText.textContent = 'Price may rise soon. Consider buying!';
        confidence.textContent = '72%';
    } else {
        predictionCard.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        predictionText.textContent = 'Price is stable';
        confidence.textContent = '90%';
    }
}

// Generate simulated price history
function generatePriceHistory(currentPrice, targetPrice, period = '7d') {
    const prices = [];
    const steps = period === '7d' ? 7 : period === '30d' ? 4 : 7;
    
    let price = currentPrice * 1.3;
    
    for (let i = 0; i < steps; i++) {
        const progress = i / (steps - 1);
        const targetAtStep = currentPrice + (price - currentPrice) * (1 - progress);
        const variation = (Math.random() - 0.5) * currentPrice * 0.15;
        prices.push(Math.round(targetAtStep + variation));
    }
    prices[prices.length - 1] = currentPrice;
    return prices;
}

// Save tracker
function saveTracker(name, url, currentPrice, targetPrice, currency, currencySymbol) {
    const tracker = {
        id: Date.now().toString(),
        name,
        url,
        currentPrice,
        targetPrice,
        currency,
        currencySymbol,
        createdAt: new Date().toISOString()
    };
    
    trackers.push(tracker);
    localStorage.setItem('trackers', JSON.stringify(trackers));
    addTrackerToList(tracker);
    updateStats();
}

// Initialize trackers on load
function initializeTrackers() {
    renderTrackers();
}

// Initialize currency preference on load
function initializeCurrencyPreference() {
    const currencySelect = document.getElementById('currency-select');
    if (currencySelect && savedCurrency) {
        currencySelect.value = savedCurrency;
    }
}

// Settings: Currency preference
function saveCurrencyPreference() {
    const select = document.getElementById('currency-select');
    if (select) {
        const value = select.value;
        localStorage.setItem('preferredCurrency', value);
        
        const [currency, symbol] = value.split(' ');
        currentCurrency = currency;
        currentCurrencySymbol = symbol.replace(/[()]/g, '');
        
        showToast(`Currency preference saved: ${value}`);
    }
}

// Toast notification
function showToast(message) {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toastMsg');
    const toastTitle = document.getElementById('toast-title');
    
    if (toast) {
        toastMsg.textContent = message;
        toastTitle.textContent = message.includes('error') || message.includes('Error') || message.includes('failed') ? 'Error!' : 'Success!';
        
        toast.classList.add('active');
        
        setTimeout(() => {
            toast.classList.remove('active');
        }, 4000);
    }
}

// Add fadeOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; transform: translateX(0); }
        to { opacity: 0; transform: translateX(-20px); }
    }
`;
document.head.appendChild(style);

let step = 1;

async function handleFlow() {
    const btn = document.getElementById('mainBtn');
    const urlInput = document.getElementById('urlInput');
    const priceStep = document.getElementById('priceStep');
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toastMsg');

    if (step === 1) {
        const url = urlInput.value;
        if (url === "") {
            alert("Please paste a link first!");
            return;
        }

        btn.disabled = true;
        btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Analyzing...';

        try {
            const response = await fetch('/get-price', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.price) {
                currentProduct = url;
                currentPrice = result.price;
                currentCurrency = result.currency;
                currentCurrencySymbol = result.currency_symbol;
                
                const currencySymbol = result.currency_symbol || '$';
                alert(`AI Found Price: ${currencySymbol}${result.price} (${result.currency})`);
                urlInput.style.display = "none";
                priceStep.style.display = "block";
                priceStep.innerHTML = `
                    <p><strong>Set Target Price (${currencySymbol}):</strong></p>
                    <input type="number" id="targetPrice" class="product-input" style="width: 150px;" placeholder="0.00" value="${Math.round(result.price * 0.8)}">
                `;
                btn.innerText = "Confirm Alert";
                step = 2;
            } else {
                alert("AI could not find the price. Check the link or selector in app.py!");
            }
        } catch (error) {
            console.error("Fetch error:", error);
            alert("Failed to connect to the backend. Make sure the Python server is running.");
            return;
        } finally {
            btn.disabled = false;
            if(step !== 2) {
                btn.innerText = "Start AI Tracking";
            }
        }
    } 
    else if (step === 2) {
        const targetPrice = document.getElementById('targetPrice').value;
        if (!targetPrice) {
            alert("Please set a target price.");
            return;
        }
        
        let productName = currentProduct.split('/')[3] || 'Product';
        productName = productName.replace(/-/g, ' ').replace(/\+/g, ' ').substring(0, 30);
        
        saveTracker(productName, currentProduct, currentPrice, targetPrice, currentCurrency, currentCurrencySymbol);
        
        priceStep.innerHTML = `
            <div style="padding: 20px; border: 2px solid #27c93f; border-radius: 12px; background: #f0fff4;">
                <i class="fa fa-robot fa-spin" style="font-size: 2rem; color: #27c93f;"></i>
                <p><strong>AI Tracking Active!</strong></p>
                <p style="font-size: 0.8rem;">Monitoring live prices... We will notify you when the target is reached.</p>
            </div>
        `;
        btn.style.display = "none";
        
        toastMsg.innerText = `Alert set! Will notify when price drops to ${currentCurrencySymbol}${targetPrice}`;
        toast.classList.add('active');

        setTimeout(() => {
            toast.classList.remove('active');
        }, 8000);
        
        setTimeout(() => {
            step = 1;
            urlInput.style.display = "block";
            urlInput.value = "";
            btn.style.display = "block";
            btn.innerText = "Start AI Tracking";
            priceStep.style.display = "none";
            priceStep.innerHTML = `<p><strong>Set Target Price:</strong></p><input type="number" id="targetPrice" class="product-input" style="width: 150px;" placeholder="$0.00">`;
        }, 3000);
    }
}