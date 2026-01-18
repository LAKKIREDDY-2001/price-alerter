# AdSense Policy Fix - TODO

## Goal: Fix "Google-served ads on screens without publisher-content" violation

### ✅ Tasks Completed:
- [x] Fix login.html - Remove AdSense (AMP Auto Ads, scripts, ad containers)
- [x] Fix signup.html - Remove AdSense (AMP Auto Ads, scripts, ad containers)
- [x] Fix forgot-password.html - Remove AdSense (AMP Auto Ads, scripts, ad containers)
- [x] Fix reset-password.html - Remove AdSense (AMP Auto Ads, scripts, ad containers)
- [x] Fix error.html - Remove AdSense (AMP Auto Ads, scripts, ad containers)
- [x] Fix index.html - Remove AMP Auto Ads only (keep main ads)
- [x] Fix static/ads.js - Remove AMP Auto Ads related code

### Summary of Changes:
1. **Removed from all auth/utility pages** (login.html, signup.html, forgot-password.html, reset-password.html, error.html):
   - `<meta name="google-adsense-account">` tag
   - AdSense script tag (`pagead2.googlesyndication.com`)
   - AMP Auto Ads script and `<amp-auto-ads>` tag
   - Ad containers (`<ins class="adsbygoogle">`)

2. **Removed from index.html**:
   - `<meta name="google-adsense-account">` tag
   - AMP Auto Ads script and `<amp-auto-ads>` tag
   - **Kept** main AdSense ads (banner at top, banner at bottom) on the content-rich dashboard

### Verification Results:
✅ AdSense script ONLY remains in index.html (main dashboard)
✅ All other template files have NO AdSense code
✅ Only the dashboard with substantial user content displays ads

### Next Steps:
1. Deploy the changes to production
2. Request AdSense review through your AdSense dashboard

