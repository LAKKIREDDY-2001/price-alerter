from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import json
import time
import random
from urllib.parse import urlparse
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
CORS(app)

http_session = requests.Session()

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
}

SITE_HEADERS = {
    'myntra': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.myntra.com/',
        'Origin': 'https://www.myntra.com'
    },
    'ajio': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.ajio.com/',
        'Origin': 'https://www.ajio.com'
    },
    'flipkart': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.flipkart.com/',
        'Origin': 'https://www.flipkart.com'
    },
    'amazon': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.amazon.in/',
        'Connection': 'keep-alive'
    },
    'meesho': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.meesho.com/',
        'Origin': 'https://www.meesho.com'
    },
    'snapdeal': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.snapdeal.com/',
        'Origin': 'https://www.snapdeal.com'
    },
    'tatacliq': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.tatacliq.com/',
        'Origin': 'https://www.tatacliq.com'
    },
    'reliancedigital': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.reliancedigital.in/',
        'Origin': 'https://www.reliancedigital.in'
    },
    'croma': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.croma.com/',
        'Origin': 'https://www.croma.com'
    },
    'nykaa': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.nykaa.com/',
        'Origin': 'https://www.nykaa.com'
    },
    'shopsy': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.shopsy.in/',
        'Origin': 'https://www.shopsy.in'
    }
}

def get_site_info(url):
    """Detect the e-commerce site from URL and return currency info"""
    url_lower = url.lower()
    
    if 'amazon' in url_lower:
        if '.in' in url_lower or 'amazon.in/' in url_lower:
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
    
    if 'reliancedigital' in url_lower or 'reliance' in url_lower:
        return 'reliancedigital', 'INR', '₹'
    
    if 'croma' in url_lower:
        return 'croma', 'INR', '₹'
    
    if 'shopsy' in url_lower:
        return 'shopsy', 'INR', '₹'
    
    if 'nykaa' in url_lower:
        return 'nykaa', 'INR', '₹'
    
    if '.in' in url_lower:
        return 'unknown', 'INR', '₹'
    
    if 'ebay' in url_lower:
        return 'ebay', 'USD', '$'
    
    return 'unknown', 'USD', '$'

def fetch_page_with_retry(url, site, max_retries=3):
    """Fetch a page with retry logic for rate limiting and blocking"""
    headers = SITE_HEADERS.get(site, DEFAULT_HEADERS).copy()
    
    for attempt in range(max_retries):
        try:
            # Add some randomness to User-Agent on retries
            if attempt > 0:
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Firefox/121.0'
                ]
                headers['User-Agent'] = random.choice(user_agents)
            
            response = http_session.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return response
            elif response.status_code == 403:
                print(f"Attempt {attempt + 1}: Got 403 for {site}, retrying...")
                time.sleep(2 * (attempt + 1))
            elif response.status_code == 429:
                print(f"Attempt {attempt + 1}: Rate limited for {site}, waiting...")
                time.sleep(5 * (attempt + 1))
            else:
                print(f"Attempt {attempt + 1}: Got status {response.status_code} for {site}")
                
        except requests.exceptions.Timeout:
            print(f"Attempt {attempt + 1}: Timeout for {site}")
            time.sleep(2 * (attempt + 1))
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}: Request failed for {site}: {str(e)}")
            time.sleep(1)
    
    return None

def parse_price(price_str):
    """Parse price string to float, handling various formats"""
    if not price_str:
        return None
    try:
        price_str = str(price_str)
        # Remove all non-numeric characters except decimal point
        price_str = re.sub(r'[^\d.]', '', price_str)
        price = float(price_str)
        if price > 0 and price < 1000000:
            return price
    except (ValueError, TypeError):
        pass
    return None

def get_product_name(soup, site):
    """Extract product name from page"""
    selectors = {
        'amazon': ['#productTitle', '.a-size-extra-large', 'h1#title'],
        'flipkart': ['h1._30jeq3', 'span.B_NuCI', '[data-testid="product-title"]'],
        'myntra': ['h1.pdp-title', '.pdp-name', '[class*="pdp-title"]'],
        'ajio': ['.prod-name', 'h1[itemprop="name"]', '.product-title'],
        'meesho': ['h2.sc-fznxsB', '[class*="product-name"]', 'h1'],
        'snapdeal': ['.pdp-e-i-name', 'h1[itemprop="name"]'],
        'tatacliq': ['.pdp-title', 'h1[class*="title"]'],
        'reliancedigital': ['.pdp__productName', 'h1[itemprop="name"]'],
        'croma': ['.pdp__productName', 'h1[itemprop="name"]'],
        'nykaa': ['.pdp-name', 'h1[itemprop="name"]'],
        'shopsy': ['.product-name', 'h2[class*="name"]']
    }
    
    site_selectors = selectors.get(site, selectors['amazon'])
    
    for selector in site_selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text().strip()
            if text and len(text) > 5:
                text = re.sub(r'\s+', ' ', text)
                return text[:100]
    
    # Fallback to any h1
    h1 = soup.find('h1')
    if h1:
        text = h1.get_text().strip()
        if text and len(text) > 5:
            return text[:100]
    
    return "Unknown Product"

def scrape_amazon_price(soup, url):
    """Scrape price from Amazon pages"""
    # Try inline price first
    inline_price = soup.select_one('.a-price .a-offscreen')
    if inline_price:
        price = parse_price(inline_price.get_text())
        if price:
            return price
    
    # Try main price elements
    price_elements = soup.select_one('#priceblock_ourprice') or soup.select_one('#priceblock_dealprice') or soup.select_one('.a-price .a-text-price')
    if price_elements:
        price = parse_price(price_elements.get_text())
        if price:
            return price
    
    # Fallback: regex search in page text
    all_text = soup.get_text()
    prices = re.findall(r'[\₹$£€]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and 100 < price < 100000:
            return price
    
    return None

def scrape_flipkart_price(soup, url):
    """Scrape price from Flipkart pages"""
    # Try the main price element
    price_elem = soup.select_one('div._30jeq3')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Try alternative selectors
    price_elem = soup.select_one('[data-testid="price"]') or soup.select_one('span._30jeq3')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\₹$£€]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and 100 < price < 100000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_myntra_price(soup, url):
    """Scrape price from Myntra pages - prioritize the main selling price (not original price)"""
    
    # Method 1: Try to find the selling price in script tags with product data
    # Myntra often embeds product data in scripts with "sellingPrice" or "finalPrice"
    all_scripts = soup.find_all("script")
    for script in all_scripts:
        script_text = script.get_text() if script else ""
        if script_text:
            # Look for sellingPrice or discounted price patterns
            selling_matches = re.findall(r'sellingPrice["\']?\s*:\s*([\d.]+)', script_text)
            for match in selling_matches:
                try:
                    val = float(match)
                    if 200 < val < 100000:
                        return val
                except ValueError:
                    continue
            
            # Look for "sp" (common abbreviation for selling price in Myntra)
            sp_matches = re.findall(r'"sp"\s*:\s*([\d.]+)', script_text)
            for match in sp_matches:
                try:
                    val = float(match)
                    if 200 < val < 100000:
                        return val
                except ValueError:
                    continue
            
            # Look for "discountedPrice" or "offerPrice" or "fp" (final price)
            discount_matches = re.findall(r'(?:discountedPrice|offerPrice|finalPrice|fp)["\']?\s*:\s*([\d.]+)', script_text, re.IGNORECASE)
            for match in discount_matches:
                try:
                    val = float(match)
                    if 200 < val < 100000:
                        return val
                except ValueError:
                    continue
    
    # Method 2: Look for price-info containers (modern Myntra layout)
    price_info = soup.find_all(class_=lambda x: x and 'pdp-pricing-container' in str(x).lower() if x else False)
    for container in price_info:
        text = container.get_text()
        nums = re.findall(r'₹\s*([\d,]+\.?\d*)', text)
        for match in nums:
            try:
                val = float(match.replace(",", ""))
                if 100 < val < 100000:
                    return val
            except ValueError:
                continue
    
    # Method 3: Try specific Myntra selectors - prioritize selling price selectors
    selling_price_selectors = [
        "[class*='selling-price']",
        "[class*='sellingPrice']",
        "[class*='final-price']",
        "[class*='current-price']",
        ".pdp__selling-price",
        ".pdp-selling-price",
        "span.discounted-price",
        ".pdp-price-info",
        ".pdp-pricing",
        ".PriceCard",
        "[data-testid='pdp-price']"
    ]
    
    for selector in selling_price_selectors:
        price_element = soup.select_one(selector)
        if price_element:
            text = price_element.get_text().strip()
            nums = re.findall(r'[\d,]+\.?\d*', text.replace(",", ""))
            for num_str in nums:
                try:
                    val = float(num_str.replace(",", ""))
                    if 100 < val < 100000:
                        return val
                except ValueError:
                    continue
    
    # Method 4: Look for the most common reasonable price
    all_prices = []
    all_elements = soup.find_all(string=lambda t: t and '₹' in t if t else False)
    
    for elem_text in all_elements:
        upper_text = elem_text.upper()
        skip_words = ['FREE', 'DELIVERY', 'SHIPPING', 'DELIVERY FEE', 'SHIPPING FEE',
                     '₹0', '₹10', '₹20', '₹30', '₹40', '₹49', '₹50',
                     '₹60', '₹70', '₹80', '₹90', '₹99', '₹100',
                     '₹150', '₹199', '₹250']
        
        if any(word in upper_text for word in skip_words):
            continue
        
        nums = re.findall(r'₹\s*([\d,]+\.?\d*)', elem_text)
        for match in nums:
            try:
                val = float(match.replace(",", ""))
                if 100 < val < 100000:
                    all_prices.append(val)
            except ValueError:
                continue
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_ajio_price(soup, url):
    """Scrape price from AJIO pages"""
    price_elem = soup.select_one('.prod-sp') or soup.select_one('.price') or soup.select_one('[class*="current-price"]')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\₹$£€]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and 50 < price < 100000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_meesho_price(soup, url):
    """Scrape price from Meesho pages"""
    price_elem = soup.select_one('[class*="Price"]') or soup.select_one('[class*="price"]')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\₹$£€]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and 50 < price < 50000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_snapdeal_price(soup, url):
    """Scrape price from Snapdeal pages"""
    price_elem = soup.select_one('.pdp-final-price') or soup.select_one('[class*="price"]') or soup.select_one('.sp-info')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\₹$£€]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and 50 < price < 100000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_tatacliq_price(soup, url):
    """Scrape price from Tata CLiQ pages"""
    price_elem = soup.select_one('[class*="pdp-price"]') or soup.select_one('[class*="price"]') or soup.select_one('.final-price')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\₹$£€]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and 100 < price < 100000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_reliancedigital_price(soup, url):
    """Scrape price from Reliance Digital pages"""
    price_elem = soup.select_one('[class*="pdp__price"]') or soup.select_one('[class*="price"]') or soup.select_one('.final-price')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\₹$£€]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and 100 < price < 100000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_croma_price(soup, url):
    """Scrape price from Croma pages"""
    price_elem = soup.select_one('[class*="pdp-price"]') or soup.select_one('[class*="price"]') or soup.select_one('.final-price')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\₹$£€]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and 100 < price < 100000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_nykaa_price(soup, url):
    """Scrape price from Nykaa pages"""
    price_elem = soup.select_one('[class*="pdp-price"]') or soup.select_one('[class*="price"]') or soup.select_one('.final-price')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\₹$£€]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and 50 < price < 100000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_shopsy_price(soup, url):
    """Scrape price from Shopsy pages"""
    price_elem = soup.select_one('[class*="price"]') or soup.select_one('.final-price') or soup.select_one('[class*="Price"]')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\₹$£€]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and 50 < price < 50000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_price(url):
    """Main function to scrape price from a URL"""
    site, currency, symbol = get_site_info(url)
    
    response = fetch_page_with_retry(url, site)
    
    if not response:
        return None, site, currency, symbol, "Failed to fetch page after multiple attempts"
    
    try:
        soup = BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        return None, site, currency, symbol, f"Failed to parse page: {str(e)}"
    
    # Get product name
    product_name = get_product_name(soup, site)
    
    # Scrape price based on site
    price = None
    
    if site == 'amazon':
        price = scrape_amazon_price(soup, url)
    elif site == 'flipkart':
        price = scrape_flipkart_price(soup, url)
    elif site == 'myntra':
        price = scrape_myntra_price(soup, url)
    elif site == 'ajio':
        price = scrape_ajio_price(soup, url)
    elif site == 'meesho':
        price = scrape_meesho_price(soup, url)
    elif site == 'snapdeal':
        price = scrape_snapdeal_price(soup, url)
    elif site == 'tatacliq':
        price = scrape_tatacliq_price(soup, url)
    elif site == 'reliancedigital':
        price = scrape_reliancedigital_price(soup, url)
    elif site == 'croma':
        price = scrape_croma_price(soup, url)
    elif site == 'nykaa':
        price = scrape_nykaa_price(soup, url)
    elif site == 'shopsy':
        price = scrape_shopsy_price(soup, url)
    else:
        # Generic scraping for unknown sites
        all_text = soup.get_text()
        prices = re.findall(r'[\₹$£€]\s*([\d,]+\.?\d*)', all_text)
        for price_str in prices:
            price = parse_price(price_str)
            if price and 50 < price < 100000:
                break
    
    if price:
        return price, site, currency, symbol, None
    
    return None, site, currency, symbol, f"Could not extract price from {site}. The site may have changed its structure."

# Flask Routes

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Login page"""
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    """Signup page"""
    return render_template('signup.html')

@app.route('/forgot-password')
def forgot_password_page():
    """Forgot password page"""
    return render_template('forgot-password.html')

@app.route('/reset-password')
def reset_password_page():
    """Reset password page"""
    return render_template('reset-password.html')

@app.route('/error')
def error_page():
    """Error page"""
    return render_template('error.html')

@app.route('/get-price', methods=['POST'])
def get_price():
    """API endpoint to get price from URL"""
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    url = data['url']
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    price, site, currency, currency_symbol, error = scrape_price(url)
    
    if error:
        return jsonify({
            'error': error,
            'suggestion': f'Try checking the URL directly in your browser. If the product exists, the site may be blocking automated access.'
        }), 400
    
    return jsonify({
        'price': price,
        'currency': currency,
        'currency_symbol': currency_symbol,
        'productName': None,
        'site': site
    })

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

