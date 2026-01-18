/**
 * AdSense Integration for Price Alert Web App
 * Publisher ID: ca-pub-1181608933401999
 * 
 * Note: AdSense does NOT allow ads in browser extensions.
 * This file is for web app only.
 * 
 * IMPORTANT: AMP Auto Ads are only valid for AMP pages.
 * Regular web pages should NOT use AMP Auto Ads.
 */

// AdSense Publisher ID
const ADSENSE_PUBLISHER_ID = 'ca-pub-1181608933401999';

// Ad Unit IDs (replace with your actual ad unit IDs after creating them in AdSense dashboard)
// Example format: '/2293293293/your_ad_unit_name'
const AD_UNITS = {
    banner_top: '2293293293/banner_top',
    banner_bottom: '2293293293/banner_bottom',
    rectangle: '2293293293/rectangle',
    responsive: '2293293293/responsive'
};

/**
 * Load AdSense script dynamically
 */
function loadAdSenseScript() {
    // Check if already loaded
    if (document.querySelector('script[src*="googlesyndication.com/pagead/js/adsbygoogle.js"]')) {
        return;
    }

    const script = document.createElement('script');
    script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${ADSENSE_PUBLISHER_ID}`;
    script.async = true;
    script.crossOrigin = 'anonymous';
    script.setAttribute('data-ad-channel', 'auto');
    document.head.appendChild(script);

    // Handle script load
    script.onload = function() {
        console.log('AdSense script loaded successfully');
        // Initialize any pending ads
        if (window.adsbygoogle && window.adsbygoogle.pending) {
            window.adsbygoogle.forEach(ad => adsbygoogle.push(ad));
        }
    };

    script.onerror = function() {
        console.error('Failed to load AdSense script');
    };
}

/**
 * Render a banner ad (728x90 or responsive)
 * @param {string} containerId - ID of the container element
 * @param {string} adUnitId - Ad unit ID from AD_UNITS
 */
function renderBannerAd(containerId, adUnitId = AD_UNITS.banner_top) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn(`Ad container not found: ${containerId}`);
        return;
    }

    // Create ad slot
    const adSlot = document.createElement('ins');
    adSlot.className = 'adsbygoogle';
    adSlot.style.display = 'block';
    adSlot.style.width = '100%';
    adSlot.style.height = '90px';
    adSlot.style.maxWidth = '100%';
    adSlot.dataset.adClient = ADSENSE_PUBLISHER_ID;
    adSlot.dataset.adSlot = adUnitId;
    adSlot.dataset.adFormat = 'auto';
    adSlot.dataset.fullWidthResponsive = 'true';

    // Clear container and add ad
    container.innerHTML = '';
    container.appendChild(adSlot);

    // Push to AdSense
    if (window.adsbygoogle) {
        adsbygoogle.push(adSlot);
    }
}

/**
 * Render a rectangle ad (300x250)
 * @param {string} containerId - ID of the container element
 * @param {string} adUnitId - Ad unit ID from AD_UNITS
 */
function renderRectangleAd(containerId, adUnitId = AD_UNITS.rectangle) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn(`Ad container not found: ${containerId}`);
        return;
    }

    // Create ad slot
    const adSlot = document.createElement('ins');
    adSlot.className = 'adsbygoogle';
    adSlot.style.display = 'inline-block';
    adSlot.style.width = '300px';
    adSlot.style.height = '250px';
    adSlot.dataset.adClient = ADSENSE_PUBLISHER_ID;
    adSlot.dataset.adSlot = adUnitId;
    adSlot.dataset.adFormat = 'auto';

    // Clear container and add ad
    container.innerHTML = '';
    container.appendChild(adSlot);

    // Push to AdSense
    if (window.adsbygoogle) {
        adsbygoogle.push(adSlot);
    }
}

/**
 * Render a responsive ad
 * @param {string} containerId - ID of the container element
 */
function renderResponsiveAd(containerId) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn(`Ad container not found: ${containerId}`);
        return;
    }

    // Create ad slot
    const adSlot = document.createElement('ins');
    adSlot.className = 'adsbygoogle';
    adSlot.style.display = 'block';
    adSlot.style.width = '100%';
    adSlot.style.height = 'auto';
    adSlot.style.minHeight = '250px';
    adSlot.dataset.adClient = ADSENSE_PUBLISHER_ID;
    adSlot.dataset.adSlot = AD_UNITS.responsive;
    adSlot.dataset.adFormat = 'auto';
    adSlot.dataset.fullWidthResponsive = 'true';

    // Clear container and add ad
    container.innerHTML = '';
    container.appendChild(adSlot);

    // Push to AdSense
    if (window.adsbygoogle) {
        adsbygoogle.push(adSlot);
    }
}

/**
 * Render an in-feed ad (between content items)
 * @param {string} containerId - ID of the container element
 */
function renderInFeedAd(containerId) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn(`Ad container not found: ${containerId}`);
        return;
    }

    // Create ad slot
    const adSlot = document.createElement('ins');
    adSlot.className = 'adsbygoogle';
    adSlot.style.display = 'block';
    adSlot.style.width = '100%';
    adSlot.style.height = '200px';
    adSlot.dataset.adClient = ADSENSE_PUBLISHER_ID;
    adSlot.dataset.adSlot = AD_UNITS.responsive;
    adSlot.dataset.adFormat = 'fluid';
    adSlot.dataset.layout = 'in-article';

    // Clear container and add ad
    container.innerHTML = '';
    container.appendChild(adSlot);

    // Push to AdSense
    if (window.adsbygoogle) {
        adsbygoogle.push(adSlot);
    }
}

/**
 * Create and append an ad label
 * @param {HTMLElement} container - Parent container
 */
function createAdLabel(container) {
    const label = document.createElement('div');
    label.className = 'ad-label';
    label.textContent = 'Advertisement';
    label.style.cssText = `
        font-size: 10px;
        color: #666;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 2px;
        padding: 2px 0;
    `;
    container.insertBefore(label, container.firstChild);
}

/**
 * Initialize ads on page load
 */
function initializeAds() {
    // Load AdSense script
    loadAdSenseScript();

    // Common ad containers to initialize
    const adContainers = [
        'ad-banner-top',
        'ad-banner-bottom',
        'ad-rectangle',
        'ad-responsive',
        'ad-in-feed'
    ];

    // Check for containers and render ads
    adContainers.forEach(containerId => {
        const container = document.getElementById(containerId);
        if (container) {
            // Add label
            createAdLabel(container);

            // Render appropriate ad based on container
            if (containerId.includes('banner')) {
                renderBannerAd(containerId);
            } else if (containerId.includes('rectangle')) {
                renderRectangleAd(containerId);
            } else if (containerId.includes('responsive') || containerId.includes('in-feed')) {
                renderResponsiveAd(containerId);
            }
        }
    });

    // Initialize bottom ad container
    initializeBottomAd();
}

/**
 * Initialize bottom ad
 * Uses the ad slot provided by the user: 7186431191
 */
function initializeBottomAd() {
    const bottomAdContainer = document.querySelector('.ad-bottom-container');
    if (bottomAdContainer) {
        // Create ad slot if not exists
        let adSlot = bottomAdContainer.querySelector('.adsbygoogle');
        if (!adSlot) {
            adSlot = document.createElement('ins');
            adSlot.className = 'adsbygoogle';
            adSlot.style.display = 'block';
            adSlot.dataset.adClient = ADSENSE_PUBLISHER_ID;
            adSlot.dataset.adSlot = '7186431191';
            adSlot.dataset.adFormat = 'auto';
            adSlot.dataset.fullWidthResponsive = 'true';
            bottomAdContainer.appendChild(adSlot);
        }

        // Push to AdSense
        if (window.adsbygoogle) {
            try {
                adsbygoogle.push(adSlot);
                console.log('Bottom ad initialized successfully');
            } catch (e) {
                console.warn('Bottom ad push failed (might be normal):', e.message);
            }
        }
    }
}

/**
 * Track ad impressions for analytics
 * @param {string} adType - Type of ad
 */
function trackAdImpression(adType) {
    if (typeof gtag !== 'undefined') {
        gtag('event', 'ad_impression', {
            'event_category': 'ads',
            'event_label': adType
        });
    }
}

/**
 * Track ad clicks for analytics
 * @param {string} adSlot - Ad slot ID
 */
function trackAdClick(adSlot) {
    if (typeof gtag !== 'undefined') {
        gtag('event', 'ad_click', {
            'event_category': 'ads',
            'event_label': adSlot
        });
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', initializeAds);

// Export functions for manual calls if needed
window.AdsManager = {
    renderBannerAd,
    renderRectangleAd,
    renderResponsiveAd,
    renderInFeedAd,
    loadAdSenseScript
};

