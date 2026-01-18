# Website Support Update TODO

## Task: Add support for 33 e-commerce websites

### Websites to Add:

#### 🇮🇳 India (15 websites)
- [x] amazon.in (already exists - add amazon.com)
- [x] flipkart.com (exists)
- [x] myntra.com (exists)
- [x] ajio.com (exists)
- [x] meesho.com (exists)
- [x] snapdeal.com (exists)
- [x] tatacliq.com (exists)
- [x] reliancedigital.in (exists)
- [x] croma.com (exists)
- [x] nykaa.com (exists)
- [x] firstcry.com (NEW)
- [x] pepperfry.com (NEW)
- [x] urbanladder.com (NEW)
- [x] bigbasket.com (NEW)
- [x] jiomart.com (NEW)

#### 🌍 Global (14 websites)
- [x] amazon.com (NEW - separate from amazon.in)
- [x] ebay.com (NEW)
- [x] aliexpress.com (NEW)
- [x] walmart.com (NEW)
- [x] bestbuy.com (NEW)
- [x] target.com (NEW)
- [x] etsy.com (NEW)
- [x] newegg.com (NEW)
- [x] shein.com (NEW)
- [x] zara.com (NEW)
- [x] hm.com (NEW)
- [x] adidas.com (NEW)
- [x] nike.com (NEW)

#### 🎯 Electronics-focused (4 websites)
- [x] samsung.com (NEW)
- [x] apple.com (NEW)
- [x] mi.com (NEW)
- [x] oneplus.in (NEW)
- [x] vijaysales.com (NEW)

## Files to Update

### 1. app.py
- [x] Update `get_random_headers()` with new site headers
- [x] Update `get_site_info()` with new site detection
- [x] Update `fetch_page_with_retry()` for new sites
- [x] Update `get_product_name()` with new selectors
- [x] Add new price scraping functions for:
  - firstcry, pepperfry, urbanladder, bigbasket, jiomart
  - amazon.com, ebay, aliexpress, walmart, bestbuy, target, etsy, newegg, shein
  - zara, hm, adidas, nike
  - samsung, apple, mi, oneplus, vijaysales
- [x] Add new scrape functions to main `scrape_price()` function

### 2. test_currency.py
- [x] Update `get_site_info()` with new site detection
- [x] Add test URLs for all new websites

### 3. browser-extension/popup.js
- [x] Update `shoppingPatterns` array with new URL patterns

### 4. browser-extension/content.js
- [x] No changes needed (uses generic price extraction)

## Progress

### Step 1: Update app.py - COMPLETED ✓
- [x] 1.1 Add site headers for new Indian sites
- [x] 1.2 Add site headers for global sites
- [x] 1.3 Add site detection in get_site_info()
- [x] 1.4 Add price selectors for new sites
- [x] 1.5 Add price scraping functions
- [x] 1.6 Update main scrape_price() function

### Step 2: Update test_currency.py - COMPLETED ✓
- [x] 2.1 Add site detection for new sites
- [x] 2.2 Add test URLs

### Step 3: Update browser-extension/popup.js - COMPLETED ✓
- [x] 3.1 Add URL patterns for shopping site detection

## STATUS: COMPLETED ✓
All 33 websites have been added to the price alerter system!

