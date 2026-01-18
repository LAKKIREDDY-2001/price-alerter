
let autoRefreshInterval = null;
let priceHistory = {};
let sensexChart = null;
let selectedLiveTracker = null;
let currentGraphPeriod = '24h';
let liveChartInterval = null;
let lastPrice = null;

// Initialize live prices - called from script.js after DOM is ready
function initLivePrices() {
    try {
        loadPriceHistory();
        // renderLiveProductSelector will be called after trackers are loaded
        // This is now handled by updateLiveProductSelector() in script.js
        updateLiveStats();
        
        // Initialize graph with current prices if no history exists
        initializeGraphData();
        
        // Check for auto-refresh setting
        const autoRefreshEnabled = localStorage.getItem('autoRefreshEnabled') === 'true';
        const autoRefreshCheckbox = document.getElementById('auto-refresh');
        if (autoRefreshEnabled && autoRefreshCheckbox) {
            autoRefreshCheckbox.checked = true;
            startAutoRefresh();
        }
    } catch (error) {
        console.error('Error initializing live prices:', error);
    }
}

// Initialize graph data with current prices as starting point
function initializeGraphData() {
    if (!window.trackers || window.trackers.length === 0) return;
    
    let hasAnyHistory = false;
    window.trackers.forEach(tracker => {
        if (priceHistory[tracker.id] && priceHistory[tracker.id].length > 0) {
            hasAnyHistory = true;
        }
    });
    
    // If no history exists, create initial history points from current prices
    if (!hasAnyHistory) {
        window.trackers.forEach(tracker => {
            priceHistory[tracker.id] = [{
                price: tracker.currentPrice,
                timestamp: new Date().toISOString()
            }];
        });
        savePriceHistory();
    }
}

// Render product selector dropdown
function renderLiveProductSelector() {
    try {
        const select = document.getElementById('live-product-select');
        if (!select) return;
        
        // Clear existing options
        select.innerHTML = '';
        
        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = '-- Select a Product --';
        select.appendChild(defaultOption);
        
        // Use global trackers variable from script.js
        if (!window.trackers || window.trackers.length === 0) {
            const emptyOption = document.createElement('option');
            emptyOption.value = '';
            emptyOption.textContent = 'No trackers available';
            emptyOption.disabled = true;
            select.appendChild(emptyOption);
            return;
        }
        
        // Add tracker options with product name
        window.trackers.forEach(tracker => {
            const option = document.createElement('option');
            option.value = tracker.id;
            // Use product name or fall back to URL hostname
            const displayName = tracker.productName && tracker.productName.trim() !== '' 
                ? tracker.productName 
                : (tracker.url ? new URL(tracker.url).hostname : 'Product');
            option.textContent = displayName;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error rendering product selector:', error);
    }
}

// Select a product for live tracking
function selectLiveProduct(trackerId) {
    try {
        if (!trackerId) {
            const singleProduct = document.getElementById('live-single-product');
            const emptyState = document.getElementById('live-empty-state');
            if (singleProduct) singleProduct.style.display = 'none';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }
        
        // Use global trackers from script.js
        const tracker = window.trackers.find(t => t.id == trackerId);
        if (!tracker) return;
        
        selectedLiveTracker = tracker;
        
        // Get product name or URL hostname
        const productName = tracker.productName && tracker.productName.trim() !== '' 
            ? tracker.productName 
            : (tracker.url ? new URL(tracker.url).hostname : 'Product');
        
        // Show product card
        const singleProduct = document.getElementById('live-single-product');
        const emptyState = document.getElementById('live-empty-state');
        if (singleProduct) singleProduct.style.display = 'block';
        if (emptyState) emptyState.style.display = 'none';
        
        // Update product info
        const nameEl = document.getElementById('live-selected-product-name');
        const urlEl = document.getElementById('live-selected-product-url');
        const currencyEl = document.getElementById('live-currency');
        const priceEl = document.getElementById('live-current-price-display');
        const targetEl = document.getElementById('live-target-price');
        const progressCurrentEl = document.getElementById('live-progress-current');
        const progressTargetEl = document.getElementById('live-progress-target');
        
        // Ensure targetPrice exists
        const targetPrice = tracker.targetPrice || tracker.currentPrice * 0.8;
        
        if (nameEl) nameEl.textContent = productName;
        if (urlEl && tracker.url) urlEl.textContent = new URL(tracker.url).hostname;
        if (currencyEl) currencyEl.textContent = tracker.currencySymbol || '₹';
        if (priceEl) priceEl.textContent = tracker.currentPrice.toFixed(2);
        if (targetEl) targetEl.textContent = (tracker.currencySymbol || '₹') + targetPrice.toFixed(2);
        if (progressCurrentEl) progressCurrentEl.textContent = (tracker.currencySymbol || '₹') + tracker.currentPrice.toFixed(0);
        if (progressTargetEl) progressTargetEl.textContent = (tracker.currencySymbol || '₹') + targetPrice.toFixed(0);
        
        // Update progress bar
        updateProgressBar(tracker);
        
        // Update price change badge
        updatePriceChangeBadge(tracker);
        
        // Render the sensex-style graph
        renderSensexGraph(tracker);
    } catch (error) {
        console.error('Error selecting product:', error);
    }
}

// Update progress bar
function updateProgressBar(tracker) {
    const fill = document.getElementById('live-progress-fill');
    if (!fill) return;
    
    // Ensure targetPrice exists
    const targetPrice = tracker.targetPrice || tracker.currentPrice * 0.8;
    
    const maxPrice = Math.max(tracker.currentPrice, targetPrice);
    const minPrice = Math.min(tracker.currentPrice, targetPrice);
    const range = maxPrice - minPrice || 1;
    
    // Calculate progress (how close to target)
    const progress = 100 - ((targetPrice - tracker.currentPrice) / range * 100);
    fill.style.width = Math.max(0, Math.min(100, progress)) + '%';
}

// Update price change badge
function updatePriceChangeBadge(tracker) {
    const badge = document.getElementById('live-price-change');
    if (!badge) return;
    
    const history = priceHistory[tracker.id] || [];
    let priceChange = 0;
    
    if (history.length > 1) {
        priceChange = tracker.currentPrice - history[history.length - 2].price;
    }
    
    badge.className = 'live-price-change-badge';
    
    if (priceChange < 0) {
        badge.classList.add('down');
        badge.innerHTML = '<i class="fa fa-arrow-down"></i> ' + Math.abs(priceChange).toFixed(2);
    } else if (priceChange > 0) {
        badge.classList.add('up');
        badge.innerHTML = '<i class="fa fa-arrow-up"></i> +' + priceChange.toFixed(2);
    } else {
        badge.classList.add('neutral');
        badge.innerHTML = '<i class="fa fa-minus"></i> No change';
    }
}

// Render sensex-style live graph with real-time animation
function renderSensexGraph(tracker) {
    const canvas = document.getElementById('sensexPriceChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart and animation
    if (sensexChart) {
        sensexChart.destroy();
    }
    if (liveChartInterval) {
        clearInterval(liveChartInterval);
    }
    
    // Get price history for selected period
    const prices = getPriceDataForPeriod(tracker.id, currentGraphPeriod);
    lastPrice = prices[prices.length - 1];
    
    // Update graph stats
    const high = Math.max(...prices);
    const low = Math.min(...prices);
    const firstPrice = prices[0];
    const lastPriceValue = prices[prices.length - 1];
    const change = firstPrice > 0 ? ((lastPriceValue - firstPrice) / firstPrice * 100) : 0;
    
    document.getElementById('graph-high').textContent = tracker.currencySymbol + high.toFixed(0);
    document.getElementById('graph-low').textContent = tracker.currencySymbol + low.toFixed(0);
    
    const changeEl = document.getElementById('graph-change');
    changeEl.textContent = (change >= 0 ? '+' : '') + change.toFixed(2) + '%';
    changeEl.className = 'graph-stat-value ' + (change >= 0 ? 'positive' : 'negative');
    
    // Generate time labels
    const labels = generateTimeLabels(prices.length, currentGraphPeriod);
    
    // Create gradient based on price direction
    const gradient = ctx.createLinearGradient(0, 0, 0, 200);
    gradient.addColorStop(0, change >= 0 ? 'rgba(39, 201, 63, 0.3)' : 'rgba(255, 95, 86, 0.3)');
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
    
    // Create line color based on price direction
    const lineColor = change >= 0 ? '#27c93f' : '#ff5f56';
    
    sensexChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Price',
                data: prices,
                borderColor: lineColor,
                backgroundColor: gradient,
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: lineColor,
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 500
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(29, 29, 31, 0.9)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    padding: 12,
                    cornerRadius: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return tracker.currencySymbol + context.parsed.y.toFixed(2);
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    display: false
                }
            }
        }
    });
    
    // Start live animation (simulates real-time price movement)
    startLiveAnimation(tracker, lineColor);
}

// Start live price animation with growth trend
function startLiveAnimation(tracker, lineColor) {
    if (liveChartInterval) {
        clearInterval(liveChartInterval);
    }
    
    // Update every 2 seconds to simulate live movement
    liveChartInterval = setInterval(() => {
        if (!selectedLiveTracker || selectedLiveTracker.id !== tracker.id) {
            clearInterval(liveChartInterval);
            return;
        }
        
        // Simulate price growth (positive movement ±0.3%)
        if (lastPrice !== null) {
            // Bias towards positive growth
            const growthFactor = 0.003; // 0.3% growth per update
            const priceChange = lastPrice * growthFactor * (0.5 + Math.random());
            lastPrice = lastPrice + priceChange;
            
            // Update chart with new price point
            if (sensexChart) {
                const newData = sensexChart.data.datasets[0].data;
                newData.shift(); // Remove oldest
                newData.push(lastPrice); // Add new
                sensexChart.data.datasets[0].data = newData;
                sensexChart.update('none'); // Update without animation for smooth effect
            }
            
            // Update price display
            const priceEl = document.getElementById('live-current-price-display');
            if (priceEl) {
                priceEl.textContent = lastPrice.toFixed(2);
            }
            
            // Update stats
            const data = sensexChart.data.datasets[0].data;
            const high = Math.max(...data);
            const low = Math.min(...data);
            const firstPrice = data[0];
            const priceChangePercent = firstPrice > 0 ? ((lastPrice - firstPrice) / firstPrice * 100) : 0;
            
            document.getElementById('graph-high').textContent = tracker.currencySymbol + high.toFixed(0);
            document.getElementById('graph-low').textContent = tracker.currencySymbol + low.toFixed(0);
            
            const changeEl = document.getElementById('graph-change');
            changeEl.textContent = (priceChangePercent >= 0 ? '+' : '') + priceChangePercent.toFixed(2) + '%';
            changeEl.className = 'graph-stat-value ' + (priceChangePercent >= 0 ? 'positive' : 'negative');
        }
    }, 2000); // Update every 2 seconds
}

// Get price data for selected period
function getPriceDataForPeriod(trackerId, period) {
    const history = priceHistory[trackerId] || [];
    // Use global trackers from script.js
    const tracker = window.trackers ? window.trackers.find(t => t.id == trackerId) : null;
    
    if (history.length === 0) {
        // Create demo data
        return generateDemoPrices(tracker?.currentPrice || 100, 20);
    }
    
    const prices = history.map(h => h.price);
    prices.push(tracker?.currentPrice || prices[prices.length - 1]);
    
    // Filter by period
    const periodHours = {
        '1h': 1,
        '24h': 24,
        '7d': 168,
        '30d': 720
    };
    
    const hours = periodHours[period] || 24;
    const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);
    
    // If we have enough data points, filter by time
    if (history.length > hours) {
        const filtered = history.filter(h => new Date(h.timestamp) >= cutoff);
        return filtered.map(h => h.price);
    }
    
    return prices;
}

// Generate demo prices for testing
function generateDemoPrices(basePrice, count) {
    const prices = [];
    let price = basePrice;
    for (let i = 0; i < count; i++) {
        prices.push(price);
        price = price + (Math.random() - 0.5) * basePrice * 0.05;
    }
    return prices;
}

// Generate time labels for graph
function generateTimeLabels(count, period) {
    const labels = [];
    const now = new Date();
    
    for (let i = count - 1; i >= 0; i--) {
        const date = new Date(now);
        
        if (period === '1h') {
            date.setMinutes(date.getMinutes() - i * 3);
            labels.push(date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));
        } else if (period === '24h') {
            date.setHours(date.getHours() - i);
            labels.push(date.toLocaleTimeString('en-US', { hour: '2-digit' }));
        } else if (period === '7d') {
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('en-US', { weekday: 'short' }));
        } else {
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        }
    }
    
    return labels;
}

// Set graph time period
function setGraphPeriod(period) {
    currentGraphPeriod = period;
    
    // Update buttons
    document.querySelectorAll('.live-graph-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent === period) {
            btn.classList.add('active');
        }
    });
    
    // Re-render chart
    if (selectedLiveTracker) {
        renderSensexGraph(selectedLiveTracker);
    }
}

// Refresh selected product
function refreshSelectedProduct() {
    if (!selectedLiveTracker) return;
    
    // Show updating state
    const nameEl = document.getElementById('live-selected-product-name');
    if (nameEl) {
        nameEl.textContent = 'Updating...';
    }
    
    refreshLivePrice(selectedLiveTracker.id)
        .then(() => {
            // Update graph and UI after refresh
            setTimeout(() => {
                if (selectedLiveTracker) {
                    renderSensexGraph(selectedLiveTracker);
                    updatePriceChangeBadge(selectedLiveTracker);
                    updateProgressBar(selectedLiveTracker);
                    
                    // Update price display
                    const priceEl = document.getElementById('live-current-price-display');
                    if (priceEl) {
                        priceEl.textContent = selectedLiveTracker.currentPrice.toFixed(2);
                    }
                    
                    // Get product name or URL hostname
                    const productName = selectedLiveTracker.productName && selectedLiveTracker.productName.trim() !== '' 
                        ? selectedLiveTracker.productName 
                        : (selectedLiveTracker.url ? new URL(selectedLiveTracker.url).hostname : 'Product');
                    
                    if (nameEl) nameEl.textContent = productName;
                }
            }, 1500);
        })
        .catch(error => {
            console.log('Refresh failed:', error);
            // Even on failure, update the graph with current data
            if (selectedLiveTracker) {
                renderSensexGraph(selectedLiveTracker);
                const productName = selectedLiveTracker.productName && selectedLiveTracker.productName.trim() !== '' 
                    ? selectedLiveTracker.productName 
                    : (selectedLiveTracker.url ? new URL(selectedLiveTracker.url).hostname : 'Product');
                if (nameEl) nameEl.textContent = productName;
            }
        });
}

// Load price history from localStorage
function loadPriceHistory() {
    const saved = localStorage.getItem('priceHistory');
    if (saved) {
        priceHistory = JSON.parse(saved);
    }
}

// Save price history to localStorage
function savePriceHistory() {
    localStorage.setItem('priceHistory', JSON.stringify(priceHistory));
}

// Toggle auto-refresh
function toggleAutoRefresh() {
    const enabled = document.getElementById('auto-refresh').checked;
    localStorage.setItem('autoRefreshEnabled', enabled);
    
    if (enabled) {
        startAutoRefresh();
        showToast('success', 'Auto-refresh enabled (every 5 minutes)');
    } else {
        stopAutoRefresh();
        showToast('info', 'Auto-refresh disabled');
    }
}

// Start auto-refresh
function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    // Show live status
    const liveStatus = document.getElementById('live-status');
    if (liveStatus) {
        liveStatus.style.display = 'flex';
    }
    
    // Refresh all prices immediately
    refreshAllPrices();
    
    // Set interval for 5 minutes
    autoRefreshInterval = setInterval(() => {
        refreshAllPrices();
    }, 5 * 60 * 1000); // 5 minutes
}

// Stop auto-refresh
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
    
    // Hide live status
    const liveStatus = document.getElementById('live-status');
    if (liveStatus) {
        liveStatus.style.display = 'none';
    }
}

// Refresh all prices
async function refreshAllPrices() {
    // Use global trackers from script.js
    if (!window.trackers || window.trackers.length === 0) return;
    
    let updated = 0;
    let priceDrops = 0;
    let pending = 0;
    
    for (const tracker of window.trackers) {
        try {
            const response = await fetch('/get-price', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: tracker.url })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                const oldPrice = tracker.currentPrice;
                tracker.currentPrice = data.price;
                tracker.productName = data.productName || tracker.productName;
                
                // Track price history
                if (!priceHistory[tracker.id]) {
                    priceHistory[tracker.id] = [];
                }
                priceHistory[tracker.id].push({
                    price: data.price,
                    timestamp: new Date().toISOString()
                });
                
                // Keep only last 30 price points
                if (priceHistory[tracker.id].length > 30) {
                    priceHistory[tracker.id].shift();
                }
                
                // Check for price drop
                if (data.price < oldPrice) {
                    priceDrops++;
                    // Play notification sound
                    playPriceDropSound();
                }
                
                updated++;
            } else {
                pending++;
            }
        } catch (error) {
            pending++;
        }
    }
    
    // Save trackers and history
    localStorage.setItem('trackers', JSON.stringify(window.trackers));
    savePriceHistory();
    
    // Update UI
    renderLiveProducts();
    updateLiveStats(updated, priceDrops, pending);
    drawLivePriceGraph();
    
    if (updated > 0) {
        showToast('success', `${updated} prices updated${priceDrops > 0 ? ', ' + priceDrops + ' dropped!' : ''}`);
    }
}

// Update live stats
function updateLiveStats(updated = 0, drops = 0, pending = 0) {
    const updatedEl = document.getElementById('live-updated');
    const dropsEl = document.getElementById('live-drops');
    const pendingEl = document.getElementById('live-pending');
    
    if (updatedEl) updatedEl.textContent = updated;
    if (dropsEl) dropsEl.textContent = drops;
    if (pendingEl) pendingEl.textContent = pending;
}

// Render live products list
function renderLiveProducts() {
    const container = document.getElementById('live-products');
    if (!container) return;
    
    // Use global trackers from script.js
    if (!window.trackers || window.trackers.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="fa fa-line-chart"></i><h3>No live data yet!</h3><p>Create trackers to see live prices here</p><button class="action-btn" onclick="switchView(\'new-alert\')">Create Tracker</button></div>';
        return;
    }
    
    container.innerHTML = window.trackers.map(tracker => {
        const history = priceHistory[tracker.id] || [];
        const prevPrice = history.length > 1 ? history[history.length - 2]?.price : tracker.currentPrice;
        const priceChange = prevPrice ? tracker.currentPrice - prevPrice : 0;
        const changeClass = priceChange < 0 ? 'down' : priceChange > 0 ? 'up' : 'neutral';
        const changeText = priceChange < 0 ? `-${Math.abs(priceChange).toFixed(2)}` : priceChange > 0 ? `+${priceChange.toFixed(2)}` : 'No change';
        
        return `
            <div class="live-product-card" id="live-card-${tracker.id}">
                <div class="live-product-header">
                    <div class="live-product-info">
                        <h4>${tracker.productName || 'Product'}</h4>
                        <div class="product-url">${new URL(tracker.url).hostname}</div>
                    <div class="live-price-badge">
                        <div class="live-current-price">
                            ${tracker.currencySymbol}${tracker.currentPrice.toFixed(2)}
                            ${priceChange < 0 ? '<i class="fa fa-arrow-down"></i>' : priceChange > 0 ? '<i class="fa fa-arrow-up"></i>' : ''}
                        </div>
                        <span class="live-price-change ${changeClass}">${changeText}</span>
                    </div>
                <div class="live-product-footer">
                    <div class="live-target-info">
                        Target: ${tracker.currencySymbol}${tracker.targetPrice}
                        <span class="live-status-indicator">
                            <span class="status-dot live"></span>
                            Live
                        </span>
                    </div>
                    <button class="live-refresh-btn" onclick="refreshLivePrice(${tracker.id})">
                        <i class="fa fa-refresh"></i> Refresh
                    </button>
                </div>
        `;
    }).join('');
}

// Refresh single price in live view
async function refreshLivePrice(trackerId) {
    // Use global trackers from script.js
    const tracker = window.trackers.find(t => t.id === trackerId);
    if (!tracker) return;
    
    const card = document.getElementById(`live-card-${trackerId}`);
    if (card) {
        card.classList.add('updating');
    }
    
    try {
        const response = await fetch('/get-price', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: tracker.url })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const oldPrice = tracker.currentPrice;
            tracker.currentPrice = data.price;
            tracker.productName = data.productName || tracker.productName;
            
            // Track history
            if (!priceHistory[tracker.id]) {
                priceHistory[tracker.id] = [];
            }
            priceHistory[tracker.id].push({
                price: data.price,
                timestamp: new Date().toISOString()
            });
            
            if (priceHistory[tracker.id].length > 30) {
                priceHistory[tracker.id].shift();
            }
            
            localStorage.setItem('trackers', JSON.stringify(window.trackers));
            savePriceHistory();
            
            // Update card
            if (card) {
                card.classList.remove('updating');
                card.classList.add('updated');
                
                if (data.price < oldPrice) {
                    card.classList.add('price-drop');
                    playPriceDropSound();
                }
                
                setTimeout(() => {
                    card.classList.remove('updated', 'price-drop');
                }, 2000);
            }
            
            renderLiveProducts();
            drawLivePriceGraph();
            showToast('success', `Updated: ${tracker.currencySymbol}${data.price}`);
        } else {
            if (card) card.classList.remove('updating');
            showToast('error', data.error || 'Failed to refresh price');
        }
    } catch (error) {
        if (card) card.classList.remove('updating');
        showToast('error', 'Connection failed');
    }
}

// Draw live price graph
function drawLivePriceGraph() {
    const canvas = document.getElementById('livePriceChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const container = canvas.parentElement;
    
    // Set canvas size
    canvas.width = container.offsetWidth - 40;
    canvas.height = container.offsetHeight - 40;
    
    const width = canvas.width;
    const height = canvas.height;
    const padding = 40;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Use global trackers from script.js
    if (!window.trackers || window.trackers.length === 0) return;
    
    // Find min/max prices across all trackers
    let minPrice = Infinity;
    let maxPrice = -Infinity;
    
    window.trackers.forEach(tracker => {
        const history = priceHistory[tracker.id] || [];
        history.forEach(h => {
            minPrice = Math.min(minPrice, h.price);
            maxPrice = Math.max(maxPrice, h.price);
        });
        // Include current price
        minPrice = Math.min(minPrice, tracker.currentPrice);
        maxPrice = Math.max(maxPrice, tracker.currentPrice);
    });
    
    if (minPrice === Infinity) minPrice = 0;
    if (maxPrice === -Infinity) maxPrice = 100;
    
    // Add padding to price range
    const priceRange = maxPrice - minPrice;
    minPrice = Math.max(0, minPrice - priceRange * 0.1);
    maxPrice = maxPrice + priceRange * 0.1;
    
    // Colors for different trackers
    const colors = ['#11998e', '#ff6b6b', '#f093fb', '#54a0ff', '#feca57', '#00d2d3'];
    
    // Draw grid
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;
    
    // Horizontal lines
    for (let i = 0; i <= 5; i++) {
        const y = padding + (height - padding * 2) * (i / 5);
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
        
        // Price label
        const price = maxPrice - (maxPrice - minPrice) * (i / 5);
        ctx.fillStyle = '#666';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(price.toFixed(0), padding - 8, y + 4);
    }
    
    // Draw each tracker's price line
    window.trackers.forEach((tracker, index) => {
        const history = priceHistory[tracker.id] || [];
        const color = colors[index % colors.length];
        
        if (history.length === 0) return;
        
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        const points = [...history, { price: tracker.currentPrice, timestamp: new Date().toISOString() }];
        
        points.forEach((point, i) => {
            const x = padding + (width - padding * 2) * (i / Math.max(points.length - 1, 1));
            const y = padding + (height - padding * 2) * (1 - (point.price - minPrice) / (maxPrice - minPrice));
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        
        ctx.stroke();
        
        // Draw green dots for current prices
        const lastX = padding + (width - padding * 2);
        const lastY = padding + (height - padding * 2) * (1 - (tracker.currentPrice - minPrice) / (maxPrice - minPrice));
        
        // Green dot for current price
        ctx.beginPath();
        ctx.arc(lastX, lastY, 8, 0, Math.PI * 2);
        ctx.fillStyle = '#11998e';
        ctx.fill();
        ctx.strokeStyle = '#38ef7d';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // Glow effect
        ctx.beginPath();
        ctx.arc(lastX, lastY, 12, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(17, 153, 142, 0.3)';
        ctx.fill();
        
        // Draw historical points (orange dots)
        history.forEach((point, i) => {
            if (i === history.length - 1) return; // Skip last point (it's the current price)
            
            const x = padding + (width - padding * 2) * (i / Math.max(history.length - 1, 1));
            const y = padding + (height - padding * 2) * (1 - (point.price - minPrice) / (maxPrice - minPrice));
            
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fillStyle = '#f093fb';
            ctx.fill();
        });
    });
}

// Generate host link for sharing
function generateHostLink() {
    // Use global trackers from script.js
    if (!window.trackers || window.trackers.length === 0) {
        showToast('error', 'No trackers to share');
        return;
    }
    
    // Create shareable data
    const shareData = {
        trackers: window.trackers.map(t => ({
            n: t.productName,
            p: t.currentPrice,
            t: t.targetPrice,
            c: t.currencySymbol,
            u: t.url,
            s: t.site
        })),
        h: priceHistory
    };
    
    // Encode as base64
    const encoded = btoa(JSON.stringify(shareData));
    const hostLink = `${window.location.origin}/host.html?data=${encoded}`;
    
    document.getElementById('host-link-input').value = hostLink;
    
    // Generate QR code (using a simple API)
    const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(hostLink)}`;
    document.getElementById('qr-code-img').src = qrCodeUrl;
    document.getElementById('host-qr-code').style.display = 'block';
    
    showToast('success', 'Host link generated!');
}

// Copy host link
function copyHostLink() {
    const input = document.getElementById('host-link-input');
    if (!input.value) {
        showToast('error', 'Generate a link first');
        return;
    }
    
    input.select();
    document.execCommand('copy');
    showToast('success', 'Link copied to clipboard!');
}

// Play price drop sound
function playPriceDropSound() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(880, audioContext.currentTime); // A5
        oscillator.frequency.setValueAtTime(659, audioContext.currentTime + 0.1); // E5
        
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.3);
    } catch (e) {
        console.log('Sound not available');
    }
}

// Make functions globally available
window.initLivePrices = initLivePrices;
window.toggleAutoRefresh = toggleAutoRefresh;
window.refreshAllPrices = refreshAllPrices;
window.refreshLivePrice = refreshLivePrice;
window.generateHostLink = generateHostLink;
window.copyHostLink = copyHostLink;
window.selectLiveProduct = selectLiveProduct;
window.setGraphPeriod = setGraphPeriod;
window.refreshSelectedProduct = refreshSelectedProduct;
