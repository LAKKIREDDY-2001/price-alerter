#!/usr/bin/env python3
"""Test script to debug price scraping"""

import sys
sys.path.insert(0, '/Users/lakkireddyvenkatamadhavareddy/Downloads/price-alerter-main')

import requests
from bs4 import BeautifulSoup
import re
from app import parse_price, get_site_info, get_random_headers, fetch_page_with_retry

# Test URLs - replace with actual URLs to test
TEST_URLS = [
    "https://www.amazon.in/dp/B09G9VP2TC",
    "https://www.flipkart.com/product/p/abc123",
    "https://www.myntra.com/shirt",
]

def debug_price_scrape(url, site):
    """Debug price scraping for a given URL"""
    print(f"\n{'='*60}")
    print(f"Testing URL: {url}")
    print(f"Detected site: {site}")
    print('='*60)
    
    # Fetch the page
    response = fetch_page_with_retry(url, site, max_retries=2)
    
    if not response:
        print("❌ Failed to fetch page")
        return
    
    print(f"✅ Page fetched successfully")
    print(f"Content length: {len(response.content)} bytes")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Get all price-related elements
    all_prices = []
    all_text = soup.get_text()
    
    # Find all prices using regex
    prices = re.findall(r'₹\s*([\d,]+\.?\d*)', all_text)
    print(f"\n📊 Found {len(prices)} price occurrences:")
    
    price_counts = {}
    for p in prices:
        price = parse_price(p)
        if price:
            if price not in price_counts:
                price_counts[price] = 0
            price_counts[price] += 1
    
    # Sort by frequency
    sorted_prices = sorted(price_counts.items(), key=lambda x: x[1], reverse=True)
    for price, count in sorted_prices[:10]:  # Show top 10
        print(f"  ₹{price:.2f} - appears {count} times")
    
    # Try different selectors based on site
    print(f"\n🔍 Trying site-specific selectors for {site}:")
    
    if site == 'amazon':
        selectors = [
            ('#priceblock_ourprice', 'Main price block'),
            ('#priceblock_dealprice', 'Deal price'),
            ('.a-price .a-offscreen', 'Inline price'),
            ('#priceblock_saleprice', 'Sale price'),
            ('.a-size-medium.a-color-price', 'Color price'),
        ]
    elif site == 'flipkart':
        selectors = [
            ('div._30jeq3', 'Main price'),
            ('[data-testid="price"]', 'Testid price'),
            ('span._30jeq3', 'Span price'),
            ('div._16P6d', 'Discount price'),
            ('.\_2B_pmu', 'Another price class'),
        ]
    elif site == 'myntra':
        selectors = [
            ('.pdp-price-info', 'Price info'),
            ('[class*="selling"]', 'Selling price'),
            ('.pdp__selling-price', 'PDP selling price'),
            ('.PriceCard', 'Price card'),
        ]
    else:
        selectors = []
    
    for selector, desc in selectors:
        elem = soup.select_one(selector)
        if elem:
            text = elem.get_text().strip()
            price = parse_price(text)
            print(f"  {desc} ({selector}): {text} → ₹{price}" if price else f"  {desc}: {text}")
        else:
            print(f"  {desc} ({selector}): Not found")

def test_amazon_selectors():
    """Test Amazon-specific price extraction"""
    print("\n" + "="*60)
    print("AMAZON PRICE EXTRACTION DEBUG")
    print("="*60)
    
    # Look for various Amazon price elements
    selectors = [
        ('#priceblock_ourprice', 'Main Price Block'),
        ('#priceblock_dealprice', 'Deal Price'),
        ('#priceblock_saleprice', 'Sale Price'),
        ('#priceblock_ourprice_lbl', 'Price Label'),
        ('.a-price .a-offscreen', 'Inline Price (a-offscreen)'),
        ('.a-price .a-text-price', 'Text Price'),
        ('.a-size-medium.a-color-price', 'Color Price'),
        ('.a-section #ppd .a-price', 'PPD Price'),
        ('#corePrice_feature_div', 'Core Price Div'),
        ('[data-asin-price]', 'Data Asin Price'),
    ]
    
    print("\nSelector tests:")
    for selector, name in selectors:
        print(f"  {name}: {selector}")

def test_flipkart_selectors():
    """Test Flipkart-specific price extraction"""
    print("\n" + "="*60)
    print("FLIPKART PRICE EXTRACTION DEBUG")
    print("="*60)
    
    selectors = [
        ('div._30jeq3', 'Main Price (._30jeq3)'),
        ('[data-testid="price"]', 'Data Test ID Price'),
        ('span._30jeq3', 'Span Price'),
        ('div._16P6d', 'Discount Price'),
        ('.\_2B_pmu', 'Price Class'),
        ('.\_3qQ0my', 'Another Price'),
        ('div.VGFzh', 'VGFzh Price'),
    ]
    
    print("\nSelector tests:")
    for selector, name in selectors:
        print(f"  {name}: {selector}")

if __name__ == '__main__':
    # Test the selectors
    test_amazon_selectors()
    test_flipkart_selectors()
    
    print("\n" + "="*60)
    print("INSTRUCTIONS")
    print("="*60)
    print("""
To test with a real URL, update TEST_URLS at the top of this script
and run: python3 test_price_scrape.py

The script will:
1. Fetch the page
2. Show all prices found and their frequencies
3. Test site-specific selectors
4. Help identify the correct price
""")

