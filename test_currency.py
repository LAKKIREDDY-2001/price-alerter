def get_site_info(url):
    url_lower = url.lower()
    if 'amazon' in url_lower:
        if '.in' in url_lower or 'amazon.in/' in url_lower or 'amazon.co.in' in url_lower:
            return 'amazon', 'INR', '₹'
        elif 'amazon.co.uk' in url_lower:
            return 'amazon', 'GBP', '£'
        else:
            return 'amazon', 'USD', '$'
    if 'flipkart' in url_lower or 'fk' in url_lower:
        return 'flipkart', 'INR', '₹'
    if 'myntra' in url_lower:
        return 'myntra', 'INR', '₹'
    if 'ajio' in url_lower:
        return 'ajio', 'INR', '₹'
    if 'meesho' in url_lower:
        return 'meesho', 'INR', '₹'
    if 'snapdeal' in url_lower:
        return 'snapdeal', 'INR', '₹'
    if 'tatacliq' in url_lower or 'tata' in url_lower:
        return 'tatacliq', 'INR', '₹'
    if 'reliancedigital' in url_lower or 'reliance' in url_lower or 'rd' in url_lower:
        return 'reliancedigital', 'INR', '₹'
    if 'croma' in url_lower:
        return 'croma', 'INR', '₹'
    if 'shopsy' in url_lower:
        return 'shopsy', 'INR', '₹'
    if 'nykaa' in url_lower:
        return 'nykaa', 'INR', '₹'
    if 'firstcry' in url_lower:
        return 'firstcry', 'INR', '₹'
    if 'pepperfry' in url_lower:
        return 'pepperfry', 'INR', '₹'
    if 'urbanladder' in url_lower:
        return 'urbanladder', 'INR', '₹'
    if 'bigbasket' in url_lower:
        return 'bigbasket', 'INR', '₹'
    if 'jiomart' in url_lower or 'jm' in url_lower:
        return 'jiomart', 'INR', '₹'
    if 'oneplus' in url_lower:
        return 'oneplus', 'INR', '₹'
    if 'vijaysales' in url_lower:
        return 'vijaysales', 'INR', '₹'
    if '.in' in url_lower or url_lower.endswith('.in'):
        return 'unknown', 'INR', '₹'
    # Global sites
    if 'ebay' in url_lower:
        return 'ebay', 'USD', '$'
    if 'aliexpress' in url_lower:
        return 'aliexpress', 'USD', '$'
    if 'walmart' in url_lower:
        return 'walmart', 'USD', '$'
    if 'bestbuy' in url_lower:
        return 'bestbuy', 'USD', '$'
    if 'target' in url_lower:
        return 'target', 'USD', '$'
    if 'etsy' in url_lower:
        return 'etsy', 'USD', '$'
    if 'newegg' in url_lower:
        return 'newegg', 'USD', '$'
    if 'shein' in url_lower:
        return 'shein', 'USD', '$'
    if 'zara' in url_lower:
        return 'zara', 'USD', '$'
    if 'hm.com' in url_lower:
        return 'hm', 'USD', '$'
    if 'adidas' in url_lower:
        return 'adidas', 'USD', '$'
    if 'nike' in url_lower:
        return 'nike', 'USD', '$'
    if 'samsung' in url_lower:
        return 'samsung', 'USD', '$'
    if 'apple' in url_lower:
        return 'apple', 'USD', '$'
    if 'mi.com' in url_lower or 'xiaomi' in url_lower or 'mi.in' in url_lower:
        return 'mi', 'USD', '$'
    
    if '.in' in url_lower:
        # Check for global sites with .in presence
        if 'ebay.in' in url_lower:
            return 'ebay', 'INR', '₹'
        if 'walmart.in' in url_lower:
            return 'walmart', 'INR', '₹'
        if 'bestbuy.in' in url_lower:
            return 'bestbuy', 'INR', '₹'
        if 'target.in' in url_lower:
            return 'target', 'INR', '₹'
        if 'etsy.in' in url_lower:
            return 'etsy', 'INR', '₹'
        if 'newegg.in' in url_lower:
            return 'newegg', 'INR', '₹'
        if 'shein.in' in url_lower:
            return 'shein', 'INR', '₹'
        if 'zara.in' in url_lower:
            return 'zara', 'INR', '₹'
        if 'hm.in' in url_lower:
            return 'hm', 'INR', '₹'
        if 'adidas.in' in url_lower:
            return 'adidas', 'INR', '₹'
        if 'nike.in' in url_lower:
            return 'nike', 'INR', '₹'
        if 'samsung.in' in url_lower:
            return 'samsung', 'INR', '₹'
        if 'apple.in' in url_lower:
            return 'apple', 'INR', '₹'
        
        return 'unknown', 'INR', '₹'
    return 'unknown', 'USD', '$'

# Test URLs
test_urls = [
    # India
    'https://www.amazon.in/dp/B09G9HD6GF',
    'https://www.flipkart.com/product/p',
    'https://www.myntra.com/shirt',
    'https://www.ajio.com/shirt',
    'https://meesho.com/product',
    'https://www.snapdeal.com/product',
    'https://www.tatacliq.com/product',
    'https://www.reliancedigital.in/product',
    'https://www.croma.com/product',
    'https://www.nykaa.com/product',
    'https://www.firstcry.com/product',
    'https://www.pepperfry.com/product',
    'https://www.urbanladder.com/product',
    'https://www.bigbasket.com/product',
    'https://www.jiomart.com/product',
    'https://www.oneplus.in/product',
    'https://www.vijaysales.com/product',
    # Global
    'https://www.amazon.com/product',
    'https://www.ebay.com/product',
    'https://www.aliexpress.com/product',
    'https://www.walmart.com/product',
    'https://www.bestbuy.com/product',
    'https://www.target.com/product',
    'https://www.etsy.com/product',
    'https://www.newegg.com/product',
    'https://www.shein.com/product',
    'https://www.zara.com/product',
    'https://www.hm.com/product',
    'https://www.adidas.com/product',
    'https://www.nike.com/product',
    'https://www.samsung.com/product',
    'https://www.apple.com/product',
    'https://www.mi.com/product',
]

print('Currency Detection Test Results:')
print('=' * 60)
for url in test_urls:
    site, currency, symbol = get_site_info(url)
    print(f'{url:45} -> {symbol} {currency}')
print('=' * 60)

