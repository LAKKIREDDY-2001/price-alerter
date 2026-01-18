# Ad Placement Plan

## Current State Analysis

### Already Implemented:
1. ✅ AdSense script in `<head>` section
2. ✅ AMP auto ads in `<head>` and `<body>`
3. ✅ Banner ad at top (`ad-banner-top`)

### Missing:
1. ❌ Banner ad at the bottom of the page
2. ❌ Proper ad initialization for both top and bottom ads

## Information Gathered

### From User's AdSense Code:
- Publisher ID: `ca-pub-1181608933401999`
- Ad Slot: `7186431191` (used in user's provided code)
- Ad Format: Auto-responsive
- Two ad types provided:
  - AMP ad code for AMP pages
  - Regular JavaScript code for non-AMP pages

### From Current Project:
- Page is non-AMP (regular HTML)
- Ad containers need to be in `<body>` section
- AdSense script is already loaded

## Plan

### Step 1: Add Bottom Ad Container
Add a new ad container at the bottom of `templates/index.html`

### Step 2: Update Ad Initialization
Ensure proper ad initialization for both top and bottom ads

### Step 3: Add CSS Styles
Add appropriate styles for ad containers

### Step 4: Verify Ad Loading
Ensure ads load properly without errors

## Implementation Details

### File: `templates/index.html`
1. Add bottom ad container before closing `</body>` tag
2. Use existing ad unit ID or the one from user's code
3. Ensure proper ad formatting

### File: `static/ads.js`
1. Update `initializeAds()` function to include bottom ad
2. Add `renderBottomAd()` function
3. Ensure proper ad push to AdSense

### File: `static/style.css`
1. Add styles for ad containers
2. Ensure responsive design
3. Add spacing for better UX

## Expected Result
- Ads appear at top and bottom of the page
- Ads are responsive and auto-sized
- AdSense script loads properly
- No JavaScript errors

## Ad Unit IDs to Use
- Top Ad: Use existing or create new
- Bottom Ad: Use user's provided slot `7186431191` or create new one

## Testing Checklist
- [ ] Ads load at top of page
- [ ] Ads load at bottom of page
- [ ] No console errors
- [ ] Ads are responsive
- [ ] Ad labels are displayed

