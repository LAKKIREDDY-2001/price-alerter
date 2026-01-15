# AdSense Integration Implementation Plan

## Current Status - ALL TASKS COMPLETED ✅
- ✅ AdSense script added to forgot-password.html
- ✅ AdSense script added to reset-password.html
- ✅ AdSense script added to error.html
- ✅ AdSense script added to index.html
- ✅ AdSense script fixed in signup.html
- ✅ AdSense script added to login.html
- ✅ static/ads.js created with ad loading functions
- ✅ Ad containers added to index.html
- ✅ Ad containers added to login.html
- ✅ Ad containers added to signup.html
- ✅ AdSense removed from browser extension (policy violation)
- ✅ CSS styles added for ad containers in style.css
- ✅ CSS styles added for ad containers in auth.css

## Implementation Steps

### Step 1: Add AdSense Script to Templates
- [x] Add AdSense script to `templates/forgot-password.html`
- [x] Add AdSense script to `templates/reset-password.html`
- [x] Add AdSense script to `templates/error.html`
- [x] Add AdSense script to `templates/index.html`
- [x] Fix AdSense script in `templates/signup.html`
- [x] Add AdSense script to `templates/login.html`

### Step 2: Create Ad Loading Script
- [x] Create `static/ads.js` with publisher ID and ad unit configuration
- [x] Add functions for banner, rectangle, and responsive ads

### Step 3: Add Ad Containers to Templates
- [x] Add ad containers to `templates/index.html`
- [x] Add ad containers to `templates/login.html`
- [x] Add ad containers to `templates/signup.html`

### Step 4: Fix Browser Extension
- [x] Remove AdSense script from `browser-extension/popup.html`

### Step 5: Style Ad Containers
- [x] Add CSS for ad containers in `static/style.css`
- [x] Add CSS for ad containers in `static/auth.css`

## AdSense Publisher ID
- Publisher ID: `ca-pub-1181608933401999`

## Next Steps for Full Integration
1. Create ad units in AdSense dashboard to get actual ad slot IDs
2. Update AD_UNITS in `static/ads.js` with real ad unit IDs
3. Test ads on staging before deploying to production
4. Monitor AdSense performance and compliance

## Important Notes
- AdSense does NOT allow ads in browser extensions - ✅ Fixed
- Replace ad unit IDs with your actual ad unit IDs after creating them in AdSense dashboard
- Test ads on staging before deploying to production

