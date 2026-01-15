# SEO & AdSense Fix Plan

## Issues to Fix:
1. **Duplicate without user-selected canonical** - Add canonical tags to all pages
2. **Page with redirect** - Root `/` redirects to `/signup` causing indexing issues
3. **Missing AdSense meta tags** - Only signup.html has the AdSense meta tag

## Tasks Completed ✅

### Step 1: Fix Canonical Tags & Meta Tags in Templates
- [x] templates/index.html - Add canonical, meta description, AdSense tag
- [x] templates/login.html - Add canonical, meta description, AdSense tag
- [x] templates/signup.html - Add canonical, meta description (AdSense already present)
- [x] templates/forgot-password.html - Add canonical, meta description, AdSense tag
- [x] templates/reset-password.html - Add canonical, meta description, AdSense tag
- [x] templates/error.html - Add canonical, meta description, AdSense tag

### Step 2: Fix Redirect Issue in app.py
- [x] Update root route to serve index.html directly (removed redirect)

## Summary of Changes:

### 1. templates/index.html:
```html
<meta name="description" content="AI Price Alert - Smart price tracking assistant. Get instant notifications when prices drop on Amazon, Flipkart, Myntra & more.">
<link rel="canonical" href="https://pricealerter.in/">
<meta name="google-adsense-account" content="ca-pub-1181608933401999">
```

### 2. templates/login.html:
```html
<meta name="description" content="Sign in to AI Price Alert - Access your price trackers and never miss a deal.">
<link rel="canonical" href="https://pricealerter.in/login">
<meta name="google-adsense-account" content="ca-pub-1181608933401999">
```

### 3. templates/signup.html:
```html
<meta name="description" content="Create your free AI Price Alert account - Start tracking prices and save money on Amazon, Flipkart, Myntra & more.">
<link rel="canonical" href="https://pricealerter.in/signup">
```

### 4. templates/forgot-password.html:
```html
<meta name="description" content="Reset your AI Price Alert password - Get back to tracking prices in minutes.">
<link rel="canonical" href="https://pricealerter.in/forgot-password">
<meta name="google-adsense-account" content="ca-pub-1181608933401999">
```

### 5. templates/reset-password.html:
```html
<meta name="description" content="Set a new password for your AI Price Alert account.">
<link rel="canonical" href="https://pricealerter.in/reset-password">
<meta name="google-adsense-account" content="ca-pub-1181608933401999">
```

### 6. templates/error.html:
```html
<meta name="description" content="AI Price Alert - Something went wrong page.">
<link rel="canonical" href="https://pricealerter.in/error">
<meta name="google-adsense-account" content="ca-pub-1181608933401999">
```

### 7. app.py - Fixed redirect:
```python
# Before:
@app.route('/')
def root():
    return redirect(url_for('signup'))

# After:
@app.route('/')
def root():
    return render_template('index.html')
```

## Notes:
- ✅ ads.txt is already correctly configured
- ✅ AdSense code snippet (googlesyndication) is already in signup.html
- All pages now have canonical tags to fix "Duplicate without user-selected canonical"
- Root URL now serves index.html directly to fix "Page with redirect"
- All pages have unique meta descriptions for better SEO
- All pages have AdSense meta tag for verification

