

// Dashboard JavaScript - Main app functionality
let trackers = [];
let selectedTrackers = new Set(); // Track selected products
let currentFilter = 'all';
let currentTracker = null;
let priceFetchTimeout = null;
let autoRefreshInterval = null;
let lastAutoRefreshTime = null;

document.addEventListener('DOMContentLoaded', () => {
    loadTrackers();
    setupNavigation();
    loadUserData();
    // Initialize live prices feature
    initLivePrices();
    // Initialize auto-refresh feature
    initAutoRefresh();
    
    // Auto-add the specified product tracker
    addUSPoloAssnTracker();
});

// ==================== ADD SPECIFIED PRODUCT TRACKER ====================

function addUSPoloAssnTracker() {
    // Check if this product already exists
    const productUrl = 'https://www.flipkart.com/u-s-polo-assn-solid-men-neck-black-t-shirt/p/itmda668d4224541?pid=TSHHYGAWEFZAETB5&lid=LSTTSHHYGAWEFZAETB5FHHXMI&marketplace=FLIPKART&store=clo%2Fash%2Fank%2Fedy&srno=b_1_1&otracker=browse&fm=organic&iid=en_d9NuT7f3Zcr0Dz6hTzHmKItdolUiCoThSYZEF7IVDF90lKr-JKFmRzIt7kFIMbQF-T4A7WRFZUfkZxDsxhY3J_UFjCTyOHoHZs-Z5_PS_w0%3D&ppt=None&ppn=None&ssid=8jka8e7wy80000001768154936964';
    
    const existingTracker = trackers.find(t => t.url === productUrl);
    
    if (existingTracker) {
        console.log('U.S. POLO ASSN. tracker already exists');
        return;
    }
    
    // Create new tracker object
    const newTracker = {
        id: Date.now(),
        url: productUrl,
        productName: 'U.S. POLO ASSN. Solid Men Polo Neck Black T',
        currentPrice: 679,
        targetPrice: 500.6,
        currency: 'INR',
        currencySymbol: '₹',
        site: 'flipkart',
        createdAt: new Date().toISOString()
    };
    
    // Add to trackers array
    trackers.push(newTracker);
    
    // Save to localStorage
    localStorage.setItem('trackers', JSON.stringify(trackers));
    
    console.log('U.S. POLO ASSN. tracker added successfully');
    
    // Update UI
    renderTrackers();
    updateStats();
    updateLiveProductSelector();
}

// Function to manually add product (can be called from console or button)
window.addProductTracker = function() {
    addUSPoloAssnTracker();
    showToast('success', 'U.S. POLO ASSN. tracker added!');
    switchView('my-trackers');
};

// ==================== AUTO-REFRESH FEATURE ====================

function initAutoRefresh() {
    // Get saved interval from settings (default: 15 minutes)
    const settings = JSON.parse(localStorage.getItem('settings') || '{}');
    const intervalMinutes = parseInt(settings.refreshInterval) || 15;
    
    // Start auto-refresh
    startAutoRefresh(intervalMinutes);
    
    // Check if we should refresh immediately (user was away)
    checkAndRefreshIfNeeded();
}

function startAutoRefresh(minutes) {
    // Clear existing interval
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    // Convert minutes to milliseconds
    const intervalMs = minutes * 60 * 1000;
    
    // Save the interval setting
    autoRefreshInterval = setInterval(() => {
        autoRefreshAllTrackers();
    }, intervalMs);
    
    console.log(`Auto-refresh started: every ${minutes} minutes`);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

async function checkAndRefreshIfNeeded() {
    // Check if enough time has passed since last refresh
    const lastRefresh = localStorage.getItem('lastAutoRefresh');
    const settings = JSON.parse(localStorage.getItem('settings') || '{}');
    const intervalMinutes = parseInt(settings.refreshInterval) || 15;
    
    if (lastRefresh) {
        const timeSinceLastRefresh = Date.now() - parseInt(lastRefresh);
        const intervalMs = intervalMinutes * 60 * 1000;
        
        // If more than the interval has passed, refresh immediately
        if (timeSinceLastRefresh >= intervalMs) {
            await autoRefreshAllTrackers();
        }
    }
}

async function autoRefreshAllTrackers() {
    if (trackers.length === 0) return;
    
    console.log('Auto-refreshing all trackers...');
    lastAutoRefreshTime = new Date().toLocaleTimeString();
    localStorage.setItem('lastAutoRefresh', Date.now().toString());
    
    let targetReachedCount = 0;
    const results = [];
    
    // Process trackers in batches to avoid overwhelming the server
    const batchSize = 3;
    for (let i = 0; i < trackers.length; i += batchSize) {
        const batch = trackers.slice(i, i + batchSize);
        const batchResults = await Promise.all(batch.map(tracker => refreshTrackerQuietly(tracker)));
        results.push(...batchResults);
        
        // Small delay between batches
        if (i + batchSize < trackers.length) {
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
    
    // Count how many trackers reached target
    results.forEach(result => {
        if (result && result.justReached) {
            targetReachedCount++;
        }
    });
    
    // Save updated trackers
    localStorage.setItem('trackers', JSON.stringify(trackers));
    
    // Update UI
    renderTrackers();
    updateStats();
    
    // Show notification if targets were reached
    if (targetReachedCount > 0) {
        console.log(`${targetReachedCount} tracker(s) reached target price!`);
        showToast('success', `${targetReachedCount} tracker(s) reached target price! Check "Target Reached" tab.`);
        
        // Also try to show browser notification if permitted
        showBrowserNotification(targetReachedCount);
    }
}

async function refreshTrackerQuietly(tracker) {
    try {
        const response = await fetch('/get-price', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: tracker.url })
        });
        
        if (response.ok) {
            const data = await response.json();
            const oldPrice = tracker.currentPrice;
            const wasActive = oldPrice > tracker.targetPrice;
            
            tracker.currentPrice = data.price;
            tracker.productName = data.productName || tracker.productName;
            
            const isReached = tracker.currentPrice <= tracker.targetPrice;
            
            return {
                trackerId: tracker.id,
                justReached: wasActive && isReached,
                newPrice: data.price
            };
        }
    } catch (error) {
        console.log(`Failed to refresh tracker ${tracker.id}:`, error.message);
    }
    return null;
}

function showBrowserNotification(count) {
    // Check if browser notifications are supported and permitted
    if (!('Notification' in window)) return;
    
    if (Notification.permission === 'granted') {
        new Notification('🎉 Target Price Reached!', {
            body: `${count} of your tracked products have reached the target price!`,
            icon: '/static/Logos/amazon.svg',
            tag: 'target-reached'
        });
    } else if (Notification.permission !== 'denied') {
        // Request permission
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                new Notification('🎉 Target Price Reached!', {
                    body: `${count} of your tracked products have reached the target price!`,
                    icon: '/static/Logos/amazon.svg',
                    tag: 'target-reached'
                });
            }
        });
    }
}

function updateAutoRefreshInterval(minutes) {
    startAutoRefresh(minutes);
    localStorage.setItem('autoRefreshInterval', minutes.toString());
}

// Update settings to include auto-refresh interval
const originalSaveSettings = saveSettings;
saveSettings = function() {
    originalSaveSettings();
    
    // Also update auto-refresh interval
    const settings = JSON.parse(localStorage.getItem('settings') || '{}');
    if (settings.refreshInterval) {
        updateAutoRefreshInterval(parseInt(settings.refreshInterval));
    }
};

// ==================== END AUTO-REFRESH FEATURE ====================

async function loadUserData() {
    try {
        const response = await fetch('/api/user');
        if (response.ok) {
            const user = await response.json();
            if (user.username) {
                document.getElementById('user-greeting').textContent = 'Welcome, ' + user.username;
            }
        }
    } catch (error) {
        console.log('User not logged in');
    }
}

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const view = item.dataset.view;
            switchView(view);
        });
    });
}

function switchView(viewName) {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.view === viewName) {
            item.classList.add('active');
        }
    });
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    document.getElementById('view-' + viewName).classList.add('active');
    
    // Populate live prices dropdown when switching to that view
    if (viewName === 'live-prices') {
        updateLiveProductSelector();
    }
}

function setLoadingState(loading, message) {
    const mainBtn = document.getElementById('mainBtn');
    if (!mainBtn) return;
    
    if (loading) {
        mainBtn.disabled = true;
        mainBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> ' + (message || 'Loading...');
    } else {
        mainBtn.disabled = false;
        mainBtn.innerHTML = 'Start AI Tracking';
    }
}

function clearPriceFetchTimeout() {
    if (priceFetchTimeout) {
        clearTimeout(priceFetchTimeout);
        priceFetchTimeout = null;
    }
}

async function handleFlow() {
    const urlInput = document.getElementById('urlInput');
    const priceStep = document.getElementById('priceStep');
    const mainBtn = document.getElementById('mainBtn');
    
    if (!urlInput) {
        showToast('error', 'URL input element not found');
        return;
    }
    
    const url = urlInput.value.trim();
    
    if (!url) {
        showToast('error', 'Please enter a URL');
        return;
    }
    
    if (priceStep.style.display === 'none') {
        // First step: fetch price
        setLoadingState(true, 'Fetching price...');
        
        // Set a timeout to fail after 10 seconds
        clearPriceFetchTimeout();
        priceFetchTimeout = setTimeout(() => {
            setLoadingState(false);
            showToast('error', 'Request timed out. The site may be slow or blocking requests.');
        }, 10000);
        
        try {
            const response = await fetch('/get-price', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            });
            
            clearPriceFetchTimeout();
            const data = await response.json();
            
            if (response.ok) {
                priceStep.style.display = 'block';
                priceStep.innerHTML = '<p><strong>Current Price: ' + data.currency_symbol + data.price + '</strong></p>' +
                    '<input type="number" id="targetPrice" class="product-input" style="width: 150px;" placeholder="Set target price" value="' + (data.price * 0.9).toFixed(2) + '">';
                mainBtn.innerHTML = 'Create Tracker';
                setLoadingState(false);
                
                // Store the product name and price data for later use
                priceStep.dataset.productName = data.productName || 'Product';
                priceStep.dataset.currentPrice = data.price;
                priceStep.dataset.currency = data.currency;
                priceStep.dataset.currencySymbol = data.currency_symbol;
            } else {
                setLoadingState(false);
                showToast('error', data.error || 'Failed to fetch price');
                if (data.suggestion) {
                    showToast('info', data.suggestion);
                }
            }
        } catch (error) {
            clearPriceFetchTimeout();
            setLoadingState(false);
            showToast('error', 'Failed to connect to server: ' + error.message);
        }
    } else {
        // Second step: create tracker
        const targetPrice = document.getElementById('targetPrice').value;
        if (!targetPrice) {
            showToast('error', 'Please set a target price');
            return;
        }
        
        const currentPrice = parseFloat(priceStep.dataset.currentPrice || priceStep.querySelector('strong')?.textContent?.replace(/[^0-9.]/g, '') || 0);
        const productName = priceStep.dataset.productName || 'Product';
        const currency = priceStep.dataset.currency || 'USD';
        const currencySymbol = priceStep.dataset.currencySymbol || '$';
        
        await createTracker(url, targetPrice, currentPrice, productName, currency, currencySymbol);
    }
}

async function createTracker(url, targetPrice, currentPrice, productName, currency, currencySymbol) {
    const urlInput = document.getElementById('urlInput');
    const mainBtn = document.getElementById('mainBtn');
    const priceStep = document.getElementById('priceStep');
    
    if (!mainBtn || !priceStep) {
        showToast('error', 'Required elements not found');
        return;
    }
    
    setLoadingState(true, 'Creating tracker...');
    
    try {
        // Fetch fresh price to ensure accuracy
        const response = await fetch('/get-price', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        const priceData = await response.json();
        if (!response.ok) throw new Error(priceData.error || 'Failed to fetch price');
        
        const finalProductName = priceData.productName || productName;
        
        // Create tracker via API (only if logged in)
        let newTracker = null;
        
        if (sessionStorage.getItem('isLoggedIn') || document.cookie.includes('session')) {
            // User is logged in, try to create via API
            try {
                const createResponse = await fetch('/api/trackers', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        url: url,
                        currentPrice: priceData.price,
                        targetPrice: parseFloat(targetPrice),
                        currency: priceData.currency,
                        currencySymbol: priceData.currency_symbol,
                        productName: finalProductName,
                        site: priceData.site || 'unknown'
                    })
                });
                
                if (createResponse.ok) {
                    const serverTracker = await createResponse.json();
                    newTracker = {
                        id: serverTracker.id || Date.now(),
                        url: url,
                        productName: finalProductName,
                        currentPrice: priceData.price,
                        targetPrice: parseFloat(targetPrice),
                        currency: priceData.currency,
                        currencySymbol: priceData.currency_symbol,
                        site: priceData.site,
                        createdAt: new Date().toISOString()
                    };
                } else {
                    // API failed, fall through to local storage
                    console.log('API tracker creation failed, using local storage');
                }
            } catch (apiError) {
                console.log('API not available, using local storage:', apiError.message);
            }
        }
        
        // If no server tracker, create local tracker
        if (!newTracker) {
            newTracker = {
                id: Date.now(),
                url: url,
                productName: finalProductName,
                currentPrice: priceData.price,
                targetPrice: parseFloat(targetPrice),
                currency: priceData.currency,
                currencySymbol: priceData.currency_symbol,
                site: priceData.site || 'unknown',
                createdAt: new Date().toISOString()
            };
        }
        
        trackers.push(newTracker);
        localStorage.setItem('trackers', JSON.stringify(trackers));
        
        setLoadingState(false);
        showToast('success', 'Tracker created successfully!');
        
        urlInput.value = '';
        priceStep.style.display = 'none';
        mainBtn.innerHTML = 'Start AI Tracking';
        
        renderTrackers();
        updateStats();
        updateLiveProductSelector(); // Refresh live prices dropdown
        switchView('my-trackers');
    } catch (error) {
        setLoadingState(false);
        showToast('error', error.message);
    }
}

function loadTrackers() {
    trackers = JSON.parse(localStorage.getItem('trackers') || '[]');
    renderTrackers();
    updateStats();
    // Update live prices dropdown
    updateLiveProductSelector();
}

function renderTrackers() {
    const container = document.getElementById('trackers-list');
    if (trackers.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="fa fa-rocket"></i><h3>No trackers yet!</h3><p>Create your first price alert to start saving money</p><button class="action-btn" onclick="switchView(\'new-alert\')">Create Tracker</button></div>';
        // Hide bulk actions when no trackers
        document.getElementById('bulk-actions').style.display = 'none';
        return;
    }
    
    let filteredTrackers = trackers;
    if (currentFilter !== 'all') {
        filteredTrackers = trackers.filter(t => {
            if (currentFilter === 'active') return t.currentPrice > t.targetPrice;
            if (currentFilter === 'reached') return t.currentPrice <= t.targetPrice;
            return true;
        });
    }
    
    container.innerHTML = filteredTrackers.map(tracker => {
        const status = tracker.currentPrice <= tracker.targetPrice ? 'reached' : 'active';
        const statusClass = status === 'reached' ? 'status-reached' : 'status-active';
        const statusText = status === 'reached' ? 'Target Reached!' : 'Active';
        const isSelected = selectedTrackers.has(tracker.id);
        const selectedClass = isSelected ? 'selected' : '';
        
        return '<div class="tracker-card ' + selectedClass + '" data-id="' + tracker.id + '" onclick="handleCardClick(event, ' + tracker.id + ')"><div class="tracker-header"><div class="tracker-checkbox ' + (isSelected ? 'checked' : '') + '" onclick="event.stopPropagation(); toggleSelect(' + tracker.id + ')" id="checkbox-' + tracker.id + '"><i class="fa fa-check" style="display: ' + (isSelected ? 'block' : 'none') + ';"></i></div><div class="tracker-info"><img src="/static/Logos/' + tracker.site + '.svg" alt="' + tracker.site + '" class="site-logo-small" onerror="this.style.display=\'none\'"><a href="' + tracker.url + '" target="_blank" class="tracker-product-link" title="Click to open product page"><h4>' + (tracker.productName || 'Product') + '</h4></a><div class="tracker-url">' + tracker.url + '</div></div></div><div class="tracker-prices"><div class="price-info current"><span class="price-label">Current</span><span class="price-amount">' + tracker.currencySymbol + tracker.currentPrice + '</span></div><div class="price-info target"><span class="price-label">Target</span><span class="price-amount">' + tracker.currencySymbol + tracker.targetPrice + '</span></div><div class="price-status ' + statusClass + '">' + statusText + '</div></div><div class="tracker-actions"><button class="tracker-action" onclick="viewTrends(' + tracker.id + ')"><i class="fa fa-chart-line"></i> Trends</button><button class="tracker-action" onclick="refreshPrice(' + tracker.id + ')"><i class="fa fa-refresh"></i> Refresh</button><button class="tracker-action delete" onclick="deleteTracker(' + tracker.id + ')"><i class="fa fa-trash"></i></button></div></div>';
    }).join('');
    
    updateCounts();
    updateBulkActions();
}

function updateStats() {
    document.getElementById('sidebar-active-trackers').textContent = trackers.length;
    document.getElementById('sidebar-deals').textContent = trackers.filter(t => t.currentPrice <= t.targetPrice).length;
    document.getElementById('total-trackers').textContent = trackers.length;
    document.getElementById('active-deals').textContent = trackers.filter(t => t.currentPrice <= t.targetPrice).length;
    if (trackers.length > 0) document.getElementById('avg-savings').textContent = '10%';
}

// Update live prices product selector when new tracker is created
function updateLiveProductSelector() {
    if (typeof renderLiveProductSelector === 'function') {
        renderLiveProductSelector();
    }
}

function updateCounts() {
    document.getElementById('count-all').textContent = trackers.length;
    document.getElementById('count-active').textContent = trackers.filter(t => t.currentPrice > t.targetPrice).length;
    document.getElementById('count-reached').textContent = trackers.filter(t => t.currentPrice <= t.targetPrice).length;
}

function setFilter(filter) {
    currentFilter = filter;
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.filter === filter) tab.classList.add('active');
    });
    renderTrackers();
}

function filterTrackers() {
    const search = document.getElementById('tracker-search').value.toLowerCase();
    const cards = document.querySelectorAll('.tracker-card');
    cards.forEach(card => {
        card.style.display = card.textContent.toLowerCase().includes(search) ? 'block' : 'none';
    });
}

function sortTrackers() {
    const sortBy = document.getElementById('sort-trackers').value;
    trackers.sort((a, b) => {
        if (sortBy === 'date') return new Date(b.createdAt) - new Date(a.createdAt);
        if (sortBy === 'name') return (a.productName || '').localeCompare(b.productName || '');
        if (sortBy === 'price') return a.currentPrice - b.currentPrice;
        return 0;
    });
    renderTrackers();
}

function viewTrends(trackerId) {
    const tracker = trackers.find(t => t.id === trackerId);
    if (!tracker) return;
    currentTracker = tracker;
    switchView('price-trends');
    document.querySelector('.product-details h3').textContent = tracker.productName || 'Product';
    document.querySelector('.product-details p').textContent = tracker.url;
    document.getElementById('original-price').textContent = tracker.currencySymbol + tracker.currentPrice;
    document.getElementById('current-price').textContent = tracker.currencySymbol + tracker.currentPrice;
    const savings = tracker.currentPrice - tracker.targetPrice;
    document.getElementById('savings-amount').textContent = tracker.currencySymbol + savings.toFixed(2);
    generateChart(tracker);
    generateGlobalAlertsChart();
    const prediction = tracker.currentPrice <= tracker.targetPrice ? 'Price is at or below your target!' : 'Price may drop further';
    document.getElementById('prediction-text').textContent = prediction;
    document.getElementById('confidence').textContent = '85%';
}

function generateChart(tracker) {
    const chartContainer = document.querySelector('.chart-main');
    const days = 7;
    const data = [];
    let basePrice = tracker.currentPrice;
    for (let i = 0; i < days; i++) {
        const variation = (Math.random() - 0.5) * basePrice * 0.1;
        data.push(basePrice + variation);
    }
    data[days - 1] = tracker.currentPrice;
    const maxPrice = Math.max(...data);
    chartContainer.innerHTML = '<div class="chart-placeholder"><div class="chart-line">' + data.map(price => '<div class="chart-bar" style="height: ' + ((price / maxPrice) * 150) + 'px;" title="' + price.toFixed(2) + '"></div>').join('') + '</div><div class="chart-labels">' + Array.from({length: days}, (_, i) => { const date = new Date(); date.setDate(date.getDate() - (days - 1 - i)); return '<span>' + date.toLocaleDateString('en-US', {month: 'short', day: 'numeric'}) + '</span>'; }).join('') + '</div></div>';
    document.getElementById('trend-lowest').textContent = tracker.currencySymbol + Math.min(...data).toFixed(2);
    document.getElementById('trend-highest').textContent = tracker.currencySymbol + Math.max(...data).toFixed(2);
    document.getElementById('trend-since').textContent = new Date(tracker.createdAt).toLocaleDateString();
    document.getElementById('buy-now-btn').style.display = tracker.currentPrice <= tracker.targetPrice ? 'flex' : 'none';
    document.getElementById('buy-now-btn').onclick = () => window.open(tracker.url, '_blank');
}

function generateGlobalAlertsChart() {
    // Generate sample global alert data across all trackers - in real app, this would come from backend
    const days = 30;
    const alertsData = [];
    let totalAlerts = 0;
    let alertsThisWeek = 0;
    let alertsThisMonth = 0;
    
    const now = new Date();
    const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const oneMonthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    
    for (let i = 0; i < days; i++) {
        // Simulate random alerts (0-15 per day across all trackers)
        const alerts = Math.floor(Math.random() * 16);
        alertsData.push(alerts);
        totalAlerts += alerts;
        
        const date = new Date(now.getTime() - (days - 1 - i) * 24 * 60 * 60 * 1000);
        if (date >= oneWeekAgo) alertsThisWeek += alerts;
        if (date >= oneMonthAgo) alertsThisMonth += alerts;
    }
    
    // Update stats
    document.getElementById('total-alerts').textContent = totalAlerts;
    document.getElementById('alerts-this-week').textContent = alertsThisWeek;
    document.getElementById('alerts-this-month').textContent = alertsThisMonth;
    
    // Create bar chart
    const maxAlerts = Math.max(...alertsData) || 1;
    const barsHtml = alertsData.map((alerts, index) => {
        const height = (alerts / maxAlerts) * 150;
        const date = new Date(now.getTime() - (days - 1 - index) * 24 * 60 * 60 * 1000);
        return `<div class="chart-bar" style="height: ${height}px;" title="${alerts} alerts on ${date.toLocaleDateString()}"></div>`;
    }).join('');
    
    const labelsHtml = Array.from({length: days}, (_, i) => {
        if (i % 5 === 0) {
            const date = new Date(now.getTime() - (days - 1 - i) * 24 * 60 * 60 * 1000);
            return `<span>${date.getDate()}</span>`;
        }
        return '<span></span>';
    }).join('');
    
    document.getElementById('alerts-chart-bars').innerHTML = barsHtml;
    document.getElementById('alerts-chart-labels').innerHTML = labelsHtml;
}


async function refreshPrice(trackerId) {
    const tracker = trackers.find(t => t.id === trackerId);
    if (!tracker) return;
    
    // Find the refresh button and show loading
    const card = document.querySelector('.tracker-card[data-id="' + trackerId + '"]');
    const refreshBtn = card?.querySelector('.tracker-action[onclick*="refreshPrice"]');
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
    }
    
    // Set timeout for refresh
    const refreshTimeout = setTimeout(() => {
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fa fa-refresh"></i> Refresh';
        }
        showToast('error', 'Refresh timed out. Try again later.');
    }, 8000);
    
    try {
        const response = await fetch('/get-price', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: tracker.url })
        });
        clearTimeout(refreshTimeout);
        
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fa fa-refresh"></i> Refresh';
        }
        
        const data = await response.json();
        if (response.ok) {
            tracker.currentPrice = data.price;
            tracker.productName = data.productName || tracker.productName;
            localStorage.setItem('trackers', JSON.stringify(trackers));
            showToast('success', 'Price updated: ' + data.currency_symbol + data.price);
            renderTrackers();
            updateStats();
        } else {
            showToast('error', data.error || 'Failed to refresh price');
        }
    } catch (error) {
        clearTimeout(refreshTimeout);
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fa fa-refresh"></i> Refresh';
        }
        showToast('error', 'Failed to connect to server');
    }
}

function deleteTracker(trackerId) {
    if (!confirm('Are you sure you want to delete this tracker?')) return;
    trackers = trackers.filter(t => t.id !== trackerId);
    localStorage.setItem('trackers', JSON.stringify(trackers));
    renderTrackers();
    updateStats();
    showToast('success', 'Tracker deleted');
}

function toggleSelect(trackerId) {
    const card = document.querySelector('.tracker-card[data-id="' + trackerId + '"]');
    const checkbox = card?.querySelector('.tracker-checkbox');
    
    if (!checkbox) return;
    
    checkbox.classList.toggle('checked');
    const icon = checkbox.querySelector('i');
    icon.style.display = checkbox.classList.contains('checked') ? 'block' : 'none';
    
    // Update card selection state
    if (checkbox.classList.contains('checked')) {
        selectedTrackers.add(trackerId);
        card.classList.add('selected');
    } else {
        selectedTrackers.delete(trackerId);
        card.classList.remove('selected');
    }
    
    // Update bulk actions UI
    updateBulkActions();
}

function handleCardClick(event, trackerId) {
    // Only toggle selection if clicking on the card (not buttons)
    if (event.target.tagName === 'BUTTON' || event.target.closest('button')) {
        return; // Let button click handlers work
    }
    // Toggle selection on card click
    toggleSelect(trackerId);
}

function selectAll() {
    // Get currently visible trackers based on filter
    let visibleTrackers = trackers;
    if (currentFilter !== 'all') {
        visibleTrackers = trackers.filter(t => {
            if (currentFilter === 'active') return t.currentPrice > t.targetPrice;
            if (currentFilter === 'reached') return t.currentPrice <= t.targetPrice;
            return true;
        });
    }
    
    visibleTrackers.forEach(tracker => {
        selectedTrackers.add(tracker.id);
        const card = document.querySelector('.tracker-card[data-id="' + tracker.id + '"]');
        if (card) {
            card.classList.add('selected');
            const checkbox = card.querySelector('.tracker-checkbox');
            if (checkbox) {
                checkbox.classList.add('checked');
                const icon = checkbox.querySelector('i');
                if (icon) icon.style.display = 'block';
            }
        }
    });
    
    updateBulkActions();
    showToast('success', selectedTrackers.size + ' trackers selected');
}

function deselectAll() {
    selectedTrackers.forEach(id => {
        const card = document.querySelector('.tracker-card[data-id="' + id + '"]');
        if (card) {
            card.classList.remove('selected');
            const checkbox = card.querySelector('.tracker-checkbox');
            if (checkbox) {
                checkbox.classList.remove('checked');
                const icon = checkbox.querySelector('i');
                if (icon) icon.style.display = 'none';
            }
        }
    });
    selectedTrackers.clear();
    updateBulkActions();
    showToast('info', 'Selection cleared');
}

function updateBulkActions() {
    const bulkActions = document.getElementById('bulk-actions');
    const selectedCount = selectedTrackers.size;
    
    if (selectedCount > 0) {
        bulkActions.style.display = 'flex';
        document.getElementById('selected-count').textContent = selectedCount + ' selected';
        
        // Update select all button text
        const selectAllBtn = document.getElementById('select-all-btn');
        if (selectAllBtn) {
            selectAllBtn.innerHTML = '<i class="fa fa-check-square"></i> Deselect All';
            selectAllBtn.onclick = deselectAll;
        }
    } else {
        bulkActions.style.display = 'none';
        
        // Reset select all button
        const selectAllBtn = document.getElementById('select-all-btn');
        if (selectAllBtn) {
            selectAllBtn.innerHTML = '<i class="fa fa-check-square-o"></i> Select All';
            selectAllBtn.onclick = selectAll;
        }
    }
}

// ==================== SHARE FUNCTIONALITY ====================

async function shareSelected() {
    const selected = Array.from(selectedTrackers);
    
    if (selected.length === 0) {
        showToast('error', 'No trackers selected');
        return;
    }
    
    // Get tracker data for selected items
    const selectedTrackersData = trackers.filter(t => selectedTrackers.has(t.id));
    
    try {
        const response = await fetch('/api/share', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ trackers: selectedTrackersData })
        });
        
        const data = await response.json();
        
        if (response.ok && data.share_url) {
            // Show share modal with the link
            showShareModal(data.share_url, selectedTrackersData);
        } else {
            showToast('error', data.error || 'Failed to generate share link');
        }
    } catch (error) {
        showToast('error', 'Failed to connect to server: ' + error.message);
    }
}

function showShareModal(shareUrl, selectedData) {
    // Create share modal if it doesn't exist
    let modal = document.getElementById('share-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.id = 'share-modal';
        modal.innerHTML = `
            <div class="modal" style="max-width: 500px;">
                <div class="modal-header">
                    <h3><i class="fa fa-share-alt"></i> Share Trackers</h3>
                    <button class="modal-close" onclick="closeModal('share-modal')">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="share-products-preview" id="share-products-preview">
                        <p style="margin-bottom: 10px;"><strong>Sharing ${selectedData.length} tracker(s):</strong></p>
                        <div class="share-items-list"></div>
                    </div>
                    <div class="share-link-section">
                        <p style="margin-bottom: 10px;"><strong>Share this link:</strong></p>
                        <div class="share-link-input-group">
                            <input type="text" id="share-link-input" class="product-input" readonly>
                            <button class="action-btn" onclick="copyShareLink()">
                                <i class="fa fa-copy"></i> Copy
                            </button>
                        </div>
                        <p class="share-note" style="font-size: 12px; color: #86868b; margin-top: 10px;">
                            <i class="fa fa-info-circle"></i> Anyone with this link can view these trackers without logging in.
                        </p>
                    </div>
                    <div class="share-actions" style="margin-top: 20px; display: flex; gap: 10px; justify-content: center;">
                        <button class="btn-secondary" onclick="shareViaWhatsApp()">
                            <img src="/static/Logos/whatsapp.svg" alt="WhatsApp" style="width: 20px; vertical-align: middle;"> WhatsApp
                        </button>
                        <button class="btn-secondary" onclick="shareViaTelegram()">
                            <img src="/static/Logos/telegram.svg" alt="Telegram" style="width: 20px; vertical-align: middle;"> Telegram
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Update modal content
    const shareLinkInput = document.getElementById('share-link-input');
    if (shareLinkInput) {
        shareLinkInput.value = shareUrl;
    }
    
    // Show products being shared
    const previewList = modal.querySelector('.share-items-list');
    if (previewList) {
        previewList.innerHTML = selectedData.slice(0, 5).map(t => 
            `<div class="share-item-preview"><strong>${t.productName || 'Product'}</strong> - ${t.currencySymbol}${t.currentPrice}</div>`
        ).join('') + (selectedData.length > 5 ? `<div>+${selectedData.length - 5} more...</div>` : '');
    }
    
    // Store the share URL for social sharing
    modal.dataset.shareUrl = shareUrl;
    
    setTimeout(() => modal.classList.add('active'), 10);
}

function copyShareLink() {
    const shareLinkInput = document.getElementById('share-link-input');
    if (!shareLinkInput) return;
    
    shareLinkInput.select();
    document.execCommand('copy');
    
    showToast('success', 'Link copied to clipboard!');
}

function shareViaWhatsApp() {
    const modal = document.getElementById('share-modal');
    const shareUrl = modal ? modal.dataset.shareUrl : '';
    
    if (shareUrl) {
        const text = encodeURIComponent(`Check out these price trackers! ${shareUrl}`);
        window.open(`https://wa.me/?text=${text}`, '_blank');
    }
}

function shareViaTelegram() {
    const modal = document.getElementById('share-modal');
    const shareUrl = modal ? modal.dataset.shareUrl : '';
    
    if (shareUrl) {
        const text = encodeURIComponent(`Check out these price trackers! ${shareUrl}`);
        window.open(`https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${text}`, '_blank');
    }
}

function deleteSelected() {
    const selected = Array.from(selectedTrackers);
    if (selected.length === 0) {
        showToast('error', 'No trackers selected');
        return;
    }
    if (!confirm('Delete ' + selected.length + ' tracker(s)?')) return;
    
    trackers = trackers.filter(t => !selectedTrackers.has(t.id));
    localStorage.setItem('trackers', JSON.stringify(trackers));
    selectedTrackers.clear();
    renderTrackers();
    updateStats();
    showToast('success', 'Selected trackers deleted');
}

function exportSelected() {
    const selected = trackers.filter(t => selectedTrackers.has(t.id));
    if (selected.length === 0) {
        showToast('error', 'No trackers selected');
        return;
    }
    
    const data = JSON.stringify(selected, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'selected-tracker-backup.json';
    a.click();
    URL.revokeObjectURL(url);
    showToast('success', selected.length + ' trackers exported');
}

function refreshSelected() {
    const selected = Array.from(selectedTrackers);
    if (selected.length === 0) {
        showToast('error', 'No trackers selected');
        return;
    }
    
    let refreshed = 0;
    selected.forEach(async (trackerId) => {
        await refreshPrice(trackerId);
        refreshed++;
    });
    
    showToast('success', 'Refreshing ' + refreshed + ' trackers...');
}

function setTimePeriod(period) {
    document.querySelectorAll('.time-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.toLowerCase().includes(period)) btn.classList.add('active');
    });
    if (currentTracker) generateChart(currentTracker);
}

function showToast(type, message) {
    // Handle backward compatibility: if only one argument is passed, treat it as message with type 'success'
    if (typeof type === 'string' && typeof message === 'undefined') {
        message = type;
        type = 'success';
    }
    
    // Remove any existing toast-notification from auth.js
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) {
        existingToast.remove();
    }
    
    const toast = document.getElementById('toast');
    if (!toast) {
        console.error('Toast element not found');
        return;
    }
    
    const toastMsg = document.getElementById('toastMsg');
    const toastTitle = document.getElementById('toast-title');
    const toastIcon = toast.querySelector('.toast-icon');
    
    if (toastTitle) {
        toastTitle.textContent = type === 'success' ? 'Success!' : 'Error!';
    }
    if (toastMsg) {
        toastMsg.textContent = message;
    }
    if (toastIcon) {
        toastIcon.className = 'toast-icon ' + type;
    }
    
    toast.classList.add('active');
    
    // Clear any existing timeout
    if (toast.timeoutId) {
        clearTimeout(toast.timeoutId);
    }
    
    toast.timeoutId = setTimeout(() => {
        toast.classList.remove('active');
    }, 4000);
}

function saveSettings() {
    localStorage.setItem('settings', JSON.stringify({
        pushNotifications: document.getElementById('push-notifications').checked,
        emailAlerts: document.getElementById('email-alerts').checked,
        darkMode: document.getElementById('dark-mode').checked,
        compactView: document.getElementById('compact-view').checked,
        refreshInterval: document.getElementById('refresh-interval').value,
        autoDelete: document.getElementById('auto-delete').value,
        dropPercentage: document.getElementById('drop-percentage').value
    }));
    showToast('success', 'Settings saved');
}

function saveCurrencyPreference() {
    localStorage.setItem('currency', document.getElementById('currency-select').value);
    showToast('success', 'Currency preference saved');
}

function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    saveSettings();
}

function connectTelegram() {
    // Create Telegram connection modal
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'telegram-modal';
    modal.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3><i class="fa fa-telegram"></i> Connect Telegram</h3>
                <button class="modal-close" onclick="closeModal('telegram-modal')">&times;</button>
            </div>
            <div class="modal-body">
                <div class="modal-icon telegram-icon">
                    <i class="fa fa-telegram"></i>
                </div>
                <p>Get instant price drop alerts on Telegram!</p>
                <div class="modal-steps">
                    <ol>
                        <li>Open Telegram and search for <strong id="bot-username">@AI_Price_Alert_Bot</strong></li>
                        <li>Start a chat with the bot</li>
                        <li>Click "Start" or send /start</li>
                        <li>Your chat ID will be sent automatically</li>
                    </ol>
                </div>
                <button class="action-btn" onclick="openTelegramBot()">
                    <i class="fa fa-external-link"></i> Open Telegram Bot
                </button>
                <div class="connection-status" id="telegram-status">
                    <span class="status-badge disconnected">Not Connected</span>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    setTimeout(() => modal.classList.add('active'), 10);
}

function connectWhatsApp() {
    // Create WhatsApp connection modal
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'whatsapp-modal';
    modal.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3><i class="fa fa-whatsapp"></i> Connect WhatsApp</h3>
                <button class="modal-close" onclick="closeModal('whatsapp-modal')">&times;</button>
            </div>
            <div class="modal-body">
                <div class="modal-icon whatsapp-icon">
                    <i class="fa fa-whatsapp"></i>
                </div>
                <p>Get price drop alerts on WhatsApp!</p>
                <div class="form-group">
                    <label>Enter your WhatsApp number:</label>
                    <input type="tel" id="whatsapp-number" class="product-input" placeholder="+1234567890">
                </div>
                <div class="form-group">
                    <label style="font-size: 12px; color: #666;">Include country code (e.g., +91 for India)</label>
                </div>
                <button class="action-btn" onclick="saveWhatsAppNumber()">
                    <i class="fa fa-check"></i> Connect WhatsApp
                </button>
                <div class="connection-status" id="whatsapp-status">
                    <span class="status-badge disconnected">Not Connected</span>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    setTimeout(() => modal.classList.add('active'), 10);
}

function openTelegramBot() {
    const botUsername = TELEGRAM_BOT_USERNAME || 'AI_Price_Alert_Bot';
    window.open('https://t.me/' + botUsername, '_blank');
    showToast('info', 'After starting the bot, return here and click "Check Connection"');
}

async function saveWhatsAppNumber() {
    const phone = document.getElementById('whatsapp-number').value.trim();
    if (!phone) {
        showToast('error', 'Please enter your WhatsApp number');
        return;
    }
    
    // Validate phone format
    const phoneClean = phone.replace(/[^\d+]/g, '');
    if (phoneClean.length < 10) {
        showToast('error', 'Invalid phone number format');
        return;
    }
    
    try {
        const response = await fetch('/api/notifications/whatsapp/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone: phone })
        });
        const data = await response.json();
        
        if (response.ok) {
            showToast('success', data.message || 'WhatsApp connected!');
            updateConnectionStatus('whatsapp', true);
            closeModal('whatsapp-modal');
        } else {
            showToast('error', data.error || 'Failed to connect WhatsApp');
        }
    } catch (error) {
        showToast('error', 'Connection failed: ' + error.message);
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        setTimeout(() => modal.remove(), 300);
    }
}

function updateConnectionStatus(service, connected) {
    const statusEl = document.getElementById(service + '-status');
    if (statusEl) {
        const badge = statusEl.querySelector('.status-badge');
        if (badge) {
            badge.className = 'status-badge ' + (connected ? 'connected' : 'disconnected');
            badge.textContent = connected ? 'Connected ✓' : 'Not Connected';
        }
    }
}

// Close modal on outside click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
        setTimeout(() => e.target.remove(), 300);
    }
});

function exportData() {
    const data = JSON.stringify(trackers, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'price-tracker-backup.json';
    a.click();
    URL.revokeObjectURL(url);
    showToast('success', 'Data exported');
}

function importData(input) {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const imported = JSON.parse(e.target.result);
            if (Array.isArray(imported)) {
                trackers = imported;
                localStorage.setItem('trackers', JSON.stringify(trackers));
                renderTrackers();
                updateStats();
                showToast('success', 'Data imported successfully');
            }
        } catch (error) {
            showToast('error', 'Invalid file format');
        }
    };
    reader.readAsText(file);
}

function clearAllData() {
    if (!confirm('Are you sure you want to delete all trackers? This cannot be undone.')) return;
    trackers = [];
    localStorage.setItem('trackers', JSON.stringify(trackers));
    renderTrackers();
    updateStats();
    showToast('success', 'All data cleared');
}

function exportTrackers() { exportData(); }

function deleteSelected() {
    const selected = document.querySelectorAll('.tracker-checkbox.checked');
    if (selected.length === 0) {
        showToast('error', 'No trackers selected');
        return;
    }
    if (!confirm('Delete ' + selected.length + ' tracker(s)?')) return;
    selected.forEach(checkbox => {
        const card = checkbox.closest('.tracker-card');
        const id = parseInt(card.dataset.id);
        trackers = trackers.filter(t => t.id !== id);
    });
    localStorage.setItem('trackers', JSON.stringify(trackers));
    renderTrackers();
    updateStats();
    document.getElementById('bulk-actions').style.display = 'none';
    showToast('success', 'Selected trackers deleted');
}

function loadSettings() {
    const settings = JSON.parse(localStorage.getItem('settings') || '{}');
    if (settings.pushNotifications !== undefined) document.getElementById('push-notifications').checked = settings.pushNotifications;
    if (settings.emailAlerts !== undefined) document.getElementById('email-alerts').checked = settings.emailAlerts;
    if (settings.darkMode !== undefined) document.getElementById('dark-mode').checked = settings.darkMode;
    if (settings.compactView !== undefined) document.getElementById('compact-view').checked = settings.compactView;
    if (settings.refreshInterval !== undefined) document.getElementById('refresh-interval').value = settings.refreshInterval;
    if (settings.autoDelete !== undefined) document.getElementById('auto-delete').value = settings.autoDelete;
    if (settings.dropPercentage !== undefined) document.getElementById('drop-percentage').value = settings.dropPercentage;
    const currency = localStorage.getItem('currency');
    if (currency) document.getElementById('currency-select').value = currency;
}

loadSettings();

// ==================== TARGET REACHED ANIMATION ====================

function showTargetReachedAnimation(productName, currentPrice, targetPrice, currencySymbol) {
    // Create overlay if it doesn't exist
    let overlay = document.getElementById('target-reached-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'target-reached-overlay';
        overlay.innerHTML = `
            <div class="fullscreen-waves">
                <div class="fullscreen-wave"></div>
                <div class="fullscreen-wave"></div>
                <div class="fullscreen-wave"></div>
                <div class="fullscreen-wave"></div>
                <div class="fullscreen-wave"></div>
                <div class="fullscreen-wave"></div>
            </div>
            <div class="confetti-container" id="confetti-container"></div>
            <div class="sparkle-container" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 9999;">
                <div class="sparkle"></div>
                <div class="sparkle"></div>
                <div class="sparkle"></div>
                <div class="sparkle"></div>
                <div class="sparkle"></div>
                <div class="sparkle"></div>
                <div class="sparkle"></div>
                <div class="sparkle"></div>
            </div>
            <div class="wave-container">
                <div class="wave"></div>
                <div class="wave"></div>
                <div class="wave"></div>
                <div class="wave"></div>
                <div class="wave"></div>
                <div class="wave"></div>
                <div class="wave-circle"></div>
                <div class="target-text">
                    <h1>TARGET REACHED!</h1>
                    <p>${productName || 'Your Product'}</p>
                    <div class="price-display">${currencySymbol}${currentPrice}</div>
                </div>
            </div>
            <div class="close-animation">
                <button onclick="closeTargetReachedAnimation()">
                    <i class="fa fa-check"></i> Awesome!
                </button>
            </div>
        `;
        document.body.appendChild(overlay);
    }
    
    // Update product info
    const priceDisplay = overlay.querySelector('.price-display');
    const productText = overlay.querySelector('.target-text p');
    if (priceDisplay) priceDisplay.textContent = currencySymbol + currentPrice;
    if (productText) productText.textContent = productName || 'Your Product';
    
    // Create confetti
    createConfetti();
    
    // Show overlay
    overlay.classList.add('active');
    
    // Play celebration sound (optional - browser may block this)
    try {
        playCelebrationSound();
    } catch (e) {
        console.log('Sound blocked by browser');
    }
}

function createConfetti() {
    const container = document.getElementById('confetti-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    const colors = ['#ff6b6b', '#feca57', '#48dbfb', '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#1dd1a1'];
    const shapes = ['square', 'circle'];
    
    for (let i = 0; i < 100; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti';
        confetti.style.left = Math.random() * 100 + '%';
        confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.animationDelay = Math.random() * 2 + 's';
        confetti.style.animationDuration = (3 + Math.random() * 2) + 's';
        
        if (shapes[Math.floor(Math.random() * shapes.length)] === 'circle') {
            confetti.style.borderRadius = '50%';
        }
        
        container.appendChild(confetti);
    }
}

function playCelebrationSound() {
    // Create a simple beep celebration
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    // Play a cheerful ascending arpeggio
    const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
    notes.forEach((freq, i) => {
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.type = 'sine';
        oscillator.frequency.value = freq;
        
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime + i * 0.15);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + i * 0.15 + 0.3);
        
        oscillator.start(audioContext.currentTime + i * 0.15);
        oscillator.stop(audioContext.currentTime + i * 0.15 + 0.3);
    });
}

function closeTargetReachedAnimation() {
    const overlay = document.getElementById('target-reached-overlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

// Modified refreshPrice function to show animation when target is reached
const originalRefreshPrice = refreshPrice;
refreshPrice = async function(trackerId) {
    const tracker = trackers.find(t => t.id === trackerId);
    if (!tracker) return;
    
    // Find the refresh button and show loading
    const card = document.querySelector('.tracker-card[data-id="' + trackerId + '"]');
    const refreshBtn = card?.querySelector('.tracker-action[onclick*="refreshPrice"]');
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
    }
    
    // Set timeout for refresh
    const refreshTimeout = setTimeout(() => {
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fa fa-refresh"></i> Refresh';
        }
        showToast('error', 'Refresh timed out. Try again later.');
    }, 8000);
    
    try {
        const response = await fetch('/get-price', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: tracker.url })
        });
        clearTimeout(refreshTimeout);
        
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fa fa-refresh"></i> Refresh';
        }
        
        const data = await response.json();
        if (response.ok) {
            const oldPrice = tracker.currentPrice;
            tracker.currentPrice = data.price;
            tracker.productName = data.productName || tracker.productName;
            localStorage.setItem('trackers', JSON.stringify(trackers));
            
            // Check if target was just reached
            const wasActive = oldPrice > tracker.targetPrice;
            const isReached = tracker.currentPrice <= tracker.targetPrice;
            
            showToast('success', 'Price updated: ' + data.currency_symbol + data.price);
            renderTrackers();
            updateStats();
            
            // Show celebration if target was just reached
            if (wasActive && isReached) {
                setTimeout(() => {
                    showTargetReachedAnimation(
                        tracker.productName,
                        tracker.currentPrice,
                        tracker.targetPrice,
                        tracker.currencySymbol
                    );
                }, 500);
            }
        } else {
            showToast('error', data.error || 'Failed to refresh price');
        }
    } catch (error) {
        clearTimeout(refreshTimeout);
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fa fa-refresh"></i> Refresh';
        }
        showToast('error', 'Failed to connect to server');
    }
};
