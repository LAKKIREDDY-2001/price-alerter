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
    if 'moglix' in url_lower:
        return 'moglix', 'INR', '₹'
    if '.in' in url_lower or url_lower.endswith('.in'):
        return 'unknown', 'INR', '₹'
    if 'ebay' in url_lower:
        return 'ebay', 'USD', '$'
    return 'unknown', 'USD', '$'

# Test URLs
test_urls = [
    'https://www.amazon.in/dp/B09G9HD6GF',
    'https://www.flipkart.com/product/p',
    'https://www.myntra.com/shirt',
    'https://www.ajio.com/shirt',
    'https://meesho.com/product',
    'https://www.snapdeal.com/product',
    'https://www.tatacliq.com/product',
    'https://www.reliancedigital.in/product',
    'https://www.croma.com/product',
    'https://www.amazon.com/product',
    'https://www.ebay.com/product',
]

print('Currency Detection Test Results:')
print('=' * 60)
for url in test_urls:
    site, currency, symbol = get_site_info(url)
    print(f'{url:45} -> {symbol} {currency}')
print('=' * 60)

