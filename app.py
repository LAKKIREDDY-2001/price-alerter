from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import json
import time
import random
import hashlib
from urllib.parse import urlparse
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
CORS(app)

# Global error handler for JSON API responses
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'success': False, 'error': 'Bad request'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Server error. Please try again later.'}), 500

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            target_price REAL NOT NULL,
            site_name TEXT,
            product_name TEXT,
            current_price REAL,
            currency TEXT DEFAULT 'INR',
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create price_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id INTEGER NOT NULL,
            price REAL NOT NULL,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (alert_id) REFERENCES alerts (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

http_session = requests.Session()

# Comprehensive list of realistic browser user agents
USER_AGENTS = [
    # Chrome on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    # Chrome on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    # Firefox on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    # Firefox on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    # Safari on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    # Edge on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
]

def get_random_headers(site=None, referer=None):
    """Generate realistic browser headers to bypass anti-bot protection"""
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9,en-GB;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"macOS"',
    }
    
    # Add site-specific headers with better mimicry
    if site:
        site_headers = {
            'myntra': {
                'Referer': 'https://www.myntra.com/',
                'Origin': 'https://www.myntra.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'ajio': {
                'Referer': 'https://www.ajio.com/',
                'Origin': 'https://www.ajio.com',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept-Language': 'en-US,en;q=0.9',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
            },
            'flipkart': {
                'Referer': 'https://www.flipkart.com/',
                'Origin': 'https://www.flipkart.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'amazon': {
                'Referer': 'https://www.amazon.in/',
                'Origin': 'https://www.amazon.in',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'meesho': {
                'Referer': 'https://www.meesho.com/',
                'Origin': 'https://www.meesho.com',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
            },
            'snapdeal': {
                'Referer': 'https://www.snapdeal.com/',
                'Origin': 'https://www.snapdeal.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'tatacliq': {
                'Referer': 'https://www.tatacliq.com/',
                'Origin': 'https://www.tatacliq.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'reliancedigital': {
                'Referer': 'https://www.reliancedigital.in/',
                'Origin': 'https://www.reliancedigital.in',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'croma': {
                'Referer': 'https://www.croma.com/',
                'Origin': 'https://www.croma.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'nykaa': {
                'Referer': 'https://www.nykaa.com/',
                'Origin': 'https://www.nykaa.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'shopsy': {
                'Referer': 'https://www.shopsy.in/',
                'Origin': 'https://www.shopsy.in',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'jio': {
                'Referer': 'https://www.jiomart.com/',
                'Origin': 'https://www.jiomart.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'b落后': {
                'Referer': 'https://www.bigbasket.com/',
                'Origin': 'https://www.bigbasket.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'pharmasy': {
                'Referer': 'https://www.1mg.com/',
                'Origin': 'https://www.1mg.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            # India - New Sites
            'firstcry': {
                'Referer': 'https://www.firstcry.com/',
                'Origin': 'https://www.firstcry.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'pepperfry': {
                'Referer': 'https://www.pepperfry.com/',
                'Origin': 'https://www.pepperfry.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'urbanladder': {
                'Referer': 'https://www.urbanladder.com/',
                'Origin': 'https://www.urbanladder.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'jiomart': {
                'Referer': 'https://www.jiomart.com/',
                'Origin': 'https://www.jiomart.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'oneplus': {
                'Referer': 'https://www.oneplus.in/',
                'Origin': 'https://www.oneplus.in',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'vijaysales': {
                'Referer': 'https://www.vijaysales.com/',
                'Origin': 'https://www.vijaysales.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            # Global Sites
            'ebay': {
                'Referer': 'https://www.ebay.com/',
                'Origin': 'https://www.ebay.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'aliexpress': {
                'Referer': 'https://www.aliexpress.com/',
                'Origin': 'https://www.aliexpress.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'walmart': {
                'Referer': 'https://www.walmart.com/',
                'Origin': 'https://www.walmart.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'bestbuy': {
                'Referer': 'https://www.bestbuy.com/',
                'Origin': 'https://www.bestbuy.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'target': {
                'Referer': 'https://www.target.com/',
                'Origin': 'https://www.target.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'etsy': {
                'Referer': 'https://www.etsy.com/',
                'Origin': 'https://www.etsy.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'newegg': {
                'Referer': 'https://www.newegg.com/',
                'Origin': 'https://www.newegg.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'shein': {
                'Referer': 'https://www.shein.com/',
                'Origin': 'https://www.shein.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'zara': {
                'Referer': 'https://www.zara.com/',
                'Origin': 'https://www.zara.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'hm': {
                'Referer': 'https://www.hm.com/',
                'Origin': 'https://www.hm.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'adidas': {
                'Referer': 'https://www.adidas.com/',
                'Origin': 'https://www.adidas.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'nike': {
                'Referer': 'https://www.nike.com/',
                'Origin': 'https://www.nike.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'samsung': {
                'Referer': 'https://www.samsung.com/',
                'Origin': 'https://www.samsung.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'apple': {
                'Referer': 'https://www.apple.com/',
                'Origin': 'https://www.apple.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
            'mi': {
                'Referer': 'https://www.mi.com/',
                'Origin': 'https://www.mi.com',
                'X-Requested-With': 'XMLHttpRequest',
            },
        }
        if site in site_headers:
            headers.update(site_headers[site])
    
    # Override with custom referer if provided
    if referer:
        headers['Referer'] = referer
    
    return headers

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
    
    if '.in' in url_lower:
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

def fetch_page_with_retry(url, site, max_retries=5):
    """Fetch a page with advanced retry logic for rate limiting and blocking"""
    
    # For sites with strong anti-bot protection, try alternative methods
    if site in ['ajio', 'meesho', 'snapdeal', 'tatacliq', 'reliancedigital', 'croma', 'nykaa', 'shopsy', 'jio', 'firstcry', 'pepperfry', 'urbanladder', 'bigbasket', 'jiomart', 'oneplus', 'vijaysales', 'ebay', 'aliexpress', 'walmart', 'bestbuy', 'target', 'etsy', 'newegg', 'shein', 'zara', 'hm', 'adidas', 'nike', 'samsung', 'apple', 'mi']:
        # First try with a fresh session and cookies
        try:
            fresh_session = requests.Session()
            fresh_headers = get_random_headers(site)
            fresh_headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,application/xhtml+xml,application/xml;q=0.8,*/*;q=0.7',
                'Pragma': 'no-cache',
            })
            # First visit the homepage to get cookies
            site_homepages = {
                'ajio': 'https://www.ajio.com/',
                'meesho': 'https://www.meesho.com/',
                'snapdeal': 'https://www.snapdeal.com/',
                'firstcry': 'https://www.firstcry.com/',
                'pepperfry': 'https://www.pepperfry.com/',
                'urbanladder': 'https://www.urbanladder.com/',
                'bigbasket': 'https://www.bigbasket.com/',
                'jiomart': 'https://www.jiomart.com/',
                'oneplus': 'https://www.oneplus.in/',
                'vijaysales': 'https://www.vijaysales.com/',
                'ebay': 'https://www.ebay.com/',
                'aliexpress': 'https://www.aliexpress.com/',
                'walmart': 'https://www.walmart.com/',
                'bestbuy': 'https://www.bestbuy.com/',
                'target': 'https://www.target.com/',
                'etsy': 'https://www.etsy.com/',
                'newegg': 'https://www.newegg.com/',
                'shein': 'https://www.shein.com/',
                'zara': 'https://www.zara.com/',
                'hm': 'https://www.hm.com/',
                'adidas': 'https://www.adidas.com/',
                'nike': 'https://www.nike.com/',
                'samsung': 'https://www.samsung.com/',
                'apple': 'https://www.apple.com/',
                'mi': 'https://www.mi.com/',
            }
            if site in site_homepages:
                fresh_session.get(site_homepages[site], headers=fresh_headers, timeout=15)
        except:
            pass
    
    for attempt in range(max_retries):
        try:
            # Generate fresh headers for each request
            headers = get_random_headers(site)
            
            # Add random delay to mimic human behavior
            if attempt > 0:
                delay = random.uniform(3, 8) * (attempt + 1)
                time.sleep(delay)
            
            # Use a session with cookies for better mimicry
            response = http_session.get(url, headers=headers, timeout=25)
            
            if response.status_code == 200:
                # Verify we got actual product page content
                if len(response.content) < 500:
                    print(f"Warning: Response too small for {site}, might be blocking page")
                    continue
                return response
            elif response.status_code == 403:
                print(f"Attempt {attempt + 1}/{max_retries}: Got 403 Forbidden for {site}")
                # Try clearing and getting new cookies
                http_session.cookies.clear()
            elif response.status_code == 429:
                print(f"Attempt {attempt + 1}/{max_retries}: Rate limited (429) for {site}, waiting longer...")
                time.sleep(15 * (attempt + 1))
            elif response.status_code == 503:
                print(f"Attempt {attempt + 1}/{max_retries}: Service unavailable for {site}")
                time.sleep(10 * (attempt + 1))
            else:
                print(f"Attempt {attempt + 1}/{max_retries}: Got status {response.status_code} for {site}")
                
        except requests.exceptions.Timeout:
            print(f"Attempt {attempt + 1}/{max_retries}: Timeout for {site}")
            time.sleep(5 * (attempt + 1))
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/{max_retries}: Request failed for {site}: {str(e)}")
            time.sleep(2)
    
    print(f"All {max_retries} attempts failed for {site}")
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
        'shopsy': ['.product-name', 'h2[class*="name"]'],
        # New sites
        'firstcry': ['.pdp_product_name', 'h1[class*="product-name"]', '.product-title'],
        'pepperfry': ['.prod-title', 'h1[class*="title"]', '.product-name'],
        'urbanladder': ['.product-title', 'h1[class*="product"]', '.product-name'],
        'bigbasket': ['.product-title', 'h1[class*="product"]', '.product-name'],
        'jiomart': ['.prod-name', 'h1[class*="product"]', '.product-title'],
        'oneplus': ['.product-name', 'h1[class*="product"]', '.name'],
        'vijaysales': ['.product-name', 'h1[class*="product"]', '.prod-name'],
        'ebay': ['.x-item-title', 'h1[itemprop="name"]', '.product-title'],
        'aliexpress': ['.product-name', 'h1[class*="product"]', '.title'],
        'walmart': ['.product-title', 'h1[class*="product"]', '.prod-title'],
        'bestbuy': ['.sku-title', 'h1[itemprop="name"]', '.product-name'],
        'target': ['.product-title', 'h1[class*="product"]', '.prod-name'],
        'etsy': ['.product-title', 'h1[itemprop="name"]', '.title'],
        'newegg': ['.product-title', 'h1[itemprop="name"]', '.title'],
        'shein': ['.goods-title', 'h1[class*="product"]', '.product-name'],
        'zara': ['.product-name', 'h1[class*="product"]', '.name'],
        'hm': ['.product-name', 'h1[itemprop="name"]', '.title'],
        'adidas': ['.product-name', 'h1[itemprop="name"]', '.title'],
        'nike': ['.product-name', 'h1[itemprop="name"]', '.title'],
        'samsung': ['.product-name', 'h1[itemprop="name"]', '.title'],
        'apple': ['.product-name', 'h1[itemprop="name"]', '.section__title'],
        'mi': ['.product-name', 'h1[itemprop="name"]', '.title'],
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
    """Scrape price from Amazon pages - get actual product price"""
    
    # Strategy: Look for the ACTUAL product price, not delivery
    
    # 1. Try the main product price block - this is the most reliable
    price_elem = soup.select_one('#priceblock_ourprice')
    if price_elem:
        text = price_elem.get_text().strip()
        price = parse_price(text)
        if price and price >= 200:  # Real product prices
            print(f"  → Found price from #priceblock_ourprice: ₹{price}")
            return price
    
    # 2. Try deal price
    price_elem = soup.select_one('#priceblock_dealprice')
    if price_elem:
        text = price_elem.get_text().strip()
        price = parse_price(text)
        if price and price >= 200:
            print(f"  → Found price from #priceblock_dealprice: ₹{price}")
            return price
    
    # 3. Try sale price
    price_elem = soup.select_one('#priceblock_saleprice')
    if price_elem:
        text = price_elem.get_text().strip()
        price = parse_price(text)
        if price and price >= 200:
            print(f"  → Found price from #priceblock_saleprice: ₹{price}")
            return price
    
    # 4. Try the inline price element
    inline_price = soup.select_one('.a-price .a-offscreen')
    if inline_price:
        text = inline_price.get_text().strip()
        price = parse_price(text)
        if price and price >= 200:
            print(f"  → Found price from .a-offscreen: ₹{price}")
            return price
    
    # 5. Look for price in the product buying section
    price_section = soup.select_one('#ppd') or soup.select_one('#centerCol') or soup.select_one('#twotabsearchtextgrid')
    if price_section:
        section_text = price_section.get_text()
        # Look for main product price pattern
        prices = re.findall(r'₹[\s,]*([\d,]+\.?\d*)', section_text)
        for p in prices:
            price = parse_price(p)
            # Skip small delivery-like prices
            if price and 200 <= price <= 100000:
                # Make sure it's not a common delivery price
                if price not in [250, 350, 450, 500, 550, 650, 750]:
                    print(f"  → Found price from product section: ₹{price}")
                    return price
    
    # 6. Fallback - search entire page but be smarter
    all_text = soup.get_text()
    prices = re.findall(r'₹[\s,]*([\d,]+\.?\d*)', all_text)
    
    # Count frequency and filter
    price_counts = {}
    for p in prices:
        price = parse_price(p)
        if price and 200 <= price <= 100000:
            # Skip common non-product prices
            skip_prices = [49, 50, 99, 100, 150, 199, 250, 299, 350, 399, 450, 499, 500, 550, 599, 650, 699, 750, 799, 850, 899, 950, 999]
            if price not in skip_prices:
                if price not in price_counts:
                    price_counts[price] = 0
                price_counts[price] += 1
    
    if price_counts:
        # Return the most frequently occurring reasonable price
        sorted_prices = sorted(price_counts.items(), key=lambda x: x[1], reverse=True)
        print(f"  → Top prices found: {sorted_prices[:3]}")
        # Return the most common price
        return sorted_prices[0][0]
    
    print("  → No valid price found")
    return None

def scrape_flipkart_price(soup, url):
    """Scrape price from Flipkart pages - get actual product price"""
    
    # 1. Try the main price element first (most reliable)
    price_elem = soup.select_one('div._30jeq3')
    if price_elem:
        text = price_elem.get_text().strip()
        price = parse_price(text)
        if price and price >= 200:
            print(f"  → Found price from div._30jeq3: ₹{price}")
            return price
    
    # 2. Try data-testid price
    price_elem = soup.select_one('[data-testid="price"]')
    if price_elem:
        text = price_elem.get_text().strip()
        price = parse_price(text)
        if price and price >= 200:
            print(f"  → Found price from [data-testid='price']: ₹{price}")
            return price
    
    # 3. Try the discount price block
    price_elem = soup.select_one('div._16P6d')
    if price_elem:
        text = price_elem.get_text().strip()
        price = parse_price(text)
        if price and price >= 200:
            print(f"  → Found price from div._16P6d: ₹{price}")
            return price
    
    # 4. Try original price (MRP)
    price_elem = soup.select_one('div._3I9_wc') or soup.select_one('._3OtPd')
    if price_elem:
        text = price_elem.get_text().strip()
        price = parse_price(text)
        if price and price >= 200:
            print(f"  → Found price from MRP block: ₹{price}")
            return price
    
    # 5. Look for prices in the product container
    product_elem = soup.select_one('div._1Yok6V') or soup.select_one('div._2B099h')
    if product_elem:
        elem_text = product_elem.get_text()
        prices = re.findall(r'₹[\s,]*([\d,]+\.?\d*)', elem_text)
        for p in prices:
            price = parse_price(p)
            if price and 200 <= price <= 100000:
                if price not in [250, 350, 450, 500, 550, 650, 750]:
                    print(f"  → Found price from product container: ₹{price}")
                    return price
    
    # 6. Fallback - search all text
    all_text = soup.get_text()
    prices = re.findall(r'₹[\s,]*([\d,]+\.?\d*)', all_text)
    
    price_counts = {}
    for p in prices:
        price = parse_price(p)
        if price and 200 <= price <= 100000:
            skip_prices = [49, 50, 99, 100, 150, 199, 250, 299, 350, 399, 450, 499, 500, 550, 599, 650, 699, 750, 799, 850, 899, 950, 999]
            if price not in skip_prices:
                if price not in price_counts:
                    price_counts[price] = 0
                price_counts[price] += 1
    
    if price_counts:
        sorted_prices = sorted(price_counts.items(), key=lambda x: x[1], reverse=True)
        print(f"  → Top prices found: {sorted_prices[:3]}")
        return sorted_prices[0][0]
    
    print("  → No valid price found")
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

def scrape_firstcry_price(soup, url):
    """Scrape price from FirstCry pages"""
    price_elem = soup.select_one('[class*="selling-price"]') or soup.select_one('[class*="price"]') or soup.select_one('.final-price')
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

def scrape_pepperfry_price(soup, url):
    """Scrape price from Pepperfry pages"""
    price_elem = soup.select_one('[class*="selling-price"]') or soup.select_one('[class*="price"]') or soup.select_one('.final-price')
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

def scrape_urbanladder_price(soup, url):
    """Scrape price from Urban Ladder pages"""
    price_elem = soup.select_one('[class*="selling-price"]') or soup.select_one('[class*="price"]') or soup.select_one('.final-price')
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

def scrape_bigbasket_price(soup, url):
    """Scrape price from BigBasket pages"""
    price_elem = soup.select_one('[class*="sp"]') or soup.select_one('[class*="price"]') or soup.select_one('.final-price')
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
        if price and 10 < price < 10000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_jiomart_price(soup, url):
    """Scrape price from JioMart pages"""
    price_elem = soup.select_one('[class*="selling-price"]') or soup.select_one('[class*="price"]') or soup.select_one('.final-price')
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

def scrape_oneplus_price(soup, url):
    """Scrape price from OnePlus pages"""
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
        if price and 500 < price < 100000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_vijaysales_price(soup, url):
    """Scrape price from Vijay Sales pages"""
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
        if price and 100 < price < 100000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_ebay_price(soup, url):
    """Scrape price from eBay pages"""
    price_elem = soup.select_one('[class*="price"]') or soup.select_one('.vi-price') or soup.select_one('[itemprop="price"]')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\$£€₹]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and price < 10000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_aliexpress_price(soup, url):
    """Scrape price from AliExpress pages"""
    price_elem = soup.select_one('[class*="price"]') or soup.select_one('.product-price') or soup.select_one('[class*="current-price"]')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\$€£]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and price < 1000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_walmart_price(soup, url):
    """Scrape price from Walmart pages"""
    price_elem = soup.select_one('[class*="price"]') or soup.select_one('[data-automation="product-price"]') or soup.select_one('.price-characteristic')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'\$\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and price < 10000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_bestbuy_price(soup, url):
    """Scrape price from BestBuy pages"""
    # Try multiple specific selectors for BestBuy
    price_elem = soup.select_one('[data-automation="buybox-price"]') or \
                 soup.select_one('.priceView-customer-price span') or \
                 soup.select_one('.priceView-price') or \
                 soup.select_one('[itemprop="price"]') or \
                 soup.select_one('.price')
    
    if price_elem:
        price_text = price_elem.get_text().strip()
        price = parse_price(price_text)
        if price and price > 10 and price < 10000:  # Reasonable range for electronics
            print(f"  → Found price from BestBuy: ${price}")
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'\$[\s,]*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and 50 < price < 10000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        price_counts = Counter(all_prices)
        # Return most common price that's reasonable
        for p, count in price_counts.most_common(5):
            if 50 < p < 10000:
                print(f"  → BestBuy fallback price: ${p}")
                return p
    
    print("  → No valid price found for BestBuy")
    return None

def scrape_target_price(soup, url):
    """Scrape price from Target pages"""
    price_elem = soup.select_one('[class*="price"]') or soup.select_one('[data-test="product-price"]') or soup.select_one('.price')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'\$\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and price < 10000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_etsy_price(soup, url):
    """Scrape price from Etsy pages"""
    price_elem = soup.select_one('[class*="price"]') or soup.select_one('[itemprop="price"]') or soup.select_one('.currency-value')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\$£€]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and price < 5000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_newegg_price(soup, url):
    """Scrape price from Newegg pages"""
    price_elem = soup.select_one('[class*="price"]') or soup.select_one('.price') or soup.select_one('[itemprop="price"]')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'\$\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and price < 10000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_shein_price(soup, url):
    """Scrape price from Shein pages"""
    price_elem = soup.select_one('[class*="price"]') or soup.select_one('.salePrice') or soup.select_one('[class*="current-price"]')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\$€£]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and price < 500:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_zara_price(soup, url):
    """Scrape price from Zara pages"""
    price_elem = soup.select_one('[class*="price"]') or soup.select_one('.price') or soup.select_one('[data-testid="price"]')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\$£€]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and price < 1000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_hm_price(soup, url):
    """Scrape price from H&M pages"""
    price_elem = soup.select_one('[class*="price"]') or soup.select_one('.price') or soup.select_one('[data-testid="price"]')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\$£€]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and price < 1000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_adidas_price(soup, url):
    """Scrape price from Adidas pages"""
    price_elem = soup.select_one('[class*="price"]') or soup.select_one('.price') or soup.select_one('[itemprop="price"]')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\$£€]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and price < 1000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_nike_price(soup, url):
    """Scrape price from Nike pages"""
    price_elem = soup.select_one('[class*="price"]') or soup.select_one('.price') or soup.select_one('[itemprop="price"]')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\$£€]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and price < 1000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_samsung_price(soup, url):
    """Scrape price from Samsung pages"""
    price_elem = soup.select_one('[class*="price"]') or soup.select_one('.price') or soup.select_one('[itemprop="price"]')
    if price_elem:
        price = parse_price(price_elem.get_text())
        if price:
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\$£€]\s*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and price < 10000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        return Counter(all_prices).most_common(1)[0][0]
    
    return None

def scrape_apple_price(soup, url):
    """Scrape price from Apple pages"""
    # Try multiple specific selectors for Apple
    price_elem = soup.select_one('[data-component="price"]') or \
                 soup.select_one('.as-priceprice') or \
                 soup.select_one('.price-value') or \
                 soup.select_one('[itemprop="price"]') or \
                 soup.select_one('[class*="price"]')
    
    if price_elem:
        price_text = price_elem.get_text().strip()
        price = parse_price(price_text)
        if price and price > 50 and price < 10000:  # Reasonable range for Apple products
            print(f"  → Found price from Apple: ${price}")
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'\$[\s,]*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and 100 < price < 10000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        price_counts = Counter(all_prices)
        for p, count in price_counts.most_common(5):
            if 100 < p < 10000:
                print(f"  → Apple fallback price: ${p}")
                return p
    
    print("  → No valid price found for Apple")
    return None

def scrape_mi_price(soup, url):
    """Scrape price from Mi/Xiaomi pages"""
    # Try multiple specific selectors for Mi/Xiaomi
    price_elem = soup.select_one('[data-price]') or \
                 soup.select_one('.price') or \
                 soup.select_one('.product-price') or \
                 soup.select_one('[itemprop="price"]') or \
                 soup.select_one('[class*="price"]')
    
    if price_elem:
        price_text = price_elem.get_text().strip()
        price = parse_price(price_text)
        if price and price > 20 and price < 5000:  # Reasonable range for Mi products
            print(f"  → Found price from Mi: ${price}")
            return price
    
    # Fallback: find most common reasonable price
    all_prices = []
    all_text = soup.get_text()
    prices = re.findall(r'[\$€£₹][\s,]*([\d,]+\.?\d*)', all_text)
    for price_str in prices:
        price = parse_price(price_str)
        if price and 30 < price < 5000:
            all_prices.append(price)
    
    if all_prices:
        from collections import Counter
        price_counts = Counter(all_prices)
        for p, count in price_counts.most_common(5):
            if 30 < p < 5000:
                print(f"  → Mi fallback price: ${p}")
                return p
    
    print("  → No valid price found for Mi")
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
    elif site == 'firstcry':
        price = scrape_firstcry_price(soup, url)
    elif site == 'pepperfry':
        price = scrape_pepperfry_price(soup, url)
    elif site == 'urbanladder':
        price = scrape_urbanladder_price(soup, url)
    elif site == 'bigbasket':
        price = scrape_bigbasket_price(soup, url)
    elif site == 'jiomart':
        price = scrape_jiomart_price(soup, url)
    elif site == 'oneplus':
        price = scrape_oneplus_price(soup, url)
    elif site == 'vijaysales':
        price = scrape_vijaysales_price(soup, url)
    elif site == 'ebay':
        price = scrape_ebay_price(soup, url)
    elif site == 'aliexpress':
        price = scrape_aliexpress_price(soup, url)
    elif site == 'walmart':
        price = scrape_walmart_price(soup, url)
    elif site == 'bestbuy':
        price = scrape_bestbuy_price(soup, url)
    elif site == 'target':
        price = scrape_target_price(soup, url)
    elif site == 'etsy':
        price = scrape_etsy_price(soup, url)
    elif site == 'newegg':
        price = scrape_newegg_price(soup, url)
    elif site == 'shein':
        price = scrape_shein_price(soup, url)
    elif site == 'zara':
        price = scrape_zara_price(soup, url)
    elif site == 'hm':
        price = scrape_hm_price(soup, url)
    elif site == 'adidas':
        price = scrape_adidas_price(soup, url)
    elif site == 'nike':
        price = scrape_nike_price(soup, url)
    elif site == 'samsung':
        price = scrape_samsung_price(soup, url)
    elif site == 'apple':
        price = scrape_apple_price(soup, url)
    elif site == 'mi':
        price = scrape_mi_price(soup, url)
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
    """Main page - shows home page or redirects to signup if not logged in"""
    if 'user_id' not in session:
        # Not logged in, redirect to signup page
        return render_template('signup.html')
    
    # Logged in user - show the dashboard
    return render_template('index.html')

@app.route('/host')
def host_page():
    """Host page - displays shared price trackers without login"""
    return render_template('host.html')

@app.route('/api/share', methods=['POST'])
def generate_share_link():
    """API endpoint to generate a shareable link for selected trackers"""
    try:
        data = request.get_json()
        
        if not data or 'trackers' not in data:
            return jsonify({'success': False, 'error': 'No trackers provided'}), 400
        
        trackers = data['trackers']
        
        if not trackers or len(trackers) == 0:
            return jsonify({'success': False, 'error': 'No trackers selected'}), 400
        
        # Prepare share data with minimal required fields
        share_data = {
            'trackers': [],
            'h': {}  # History data
        }
        
        for i, tracker in enumerate(trackers):
            # Extract minimal data needed for display
            share_data['trackers'].append({
                'n': tracker.get('productName', 'Product'),
                'u': tracker.get('url', ''),
                's': tracker.get('site', 'unknown'),
                'p': float(tracker.get('currentPrice', 0)),
                't': float(tracker.get('targetPrice', 0)),
                'c': tracker.get('currencySymbol', '$')
            })
        
        # Encode to base64 for URL
        import base64
        encoded_data = base64.b64encode(json.dumps(share_data).encode()).decode()
        
        # Generate share URL
        base_url = request.host_url.rstrip('/')
        share_url = f"{base_url}/host?data={encoded_data}"
        
        return jsonify({
            'success': True,
            'share_url': share_url
        })
        
    except Exception as e:
        print(f"Generate share link error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to generate share link'}), 500

@app.route('/dashboard')
def dashboard():
    """Redirect dashboard to home page"""
    return redirect(url_for('index'))

@app.route('/api/user')
def get_user():
    """API endpoint to get current user info"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    return jsonify({
        'success': True,
        'user': {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'email': session.get('email')
        }
    })

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Login page - handles both GET (show form) and POST (process login)"""
    if request.method == 'GET':
        return render_template('login.html')
    
    # Handle POST request for login
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validate required fields
        if not email or not password:
            return jsonify({'success': False, 'error': 'Please enter email and password'}), 400
        
        # Validate email format
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email):
            return jsonify({'success': False, 'error': 'Please enter a valid email address'}), 400
        
        # Hash the password and query database
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email FROM users
            WHERE email = ? AND password_hash = ?
        ''', (email, password_hash))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            # Create session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            
            return jsonify({
                'success': True,
                'message': 'Login successful!',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email']
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred during login'}), 500

@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    """Signup page - handles both GET (show form) and POST (process signup)"""
    if request.method == 'GET':
        return render_template('signup.html')
    
    # Handle POST request for signup
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Validate required fields
        if not username or not email or not password:
            return jsonify({'success': False, 'error': 'Please fill in all required fields'}), 400
        
        if password != confirm_password:
            return jsonify({'success': False, 'error': 'Passwords do not match'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        # Validate email format
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email):
            return jsonify({'success': False, 'error': 'Please enter a valid email address'}), 400
        
        # Hash the password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Insert user into database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, phone, password_hash)
                VALUES (?, ?, ?, ?)
            ''', (username, email, phone, password_hash))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            # Create session
            session['user_id'] = user_id
            session['username'] = username
            session['email'] = email
            
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Account created successfully!',
                'user': {
                    'id': user_id,
                    'username': username,
                    'email': email
                }
            })
            
        except sqlite3.IntegrityError as e:
            conn.close()
            error_msg = str(e)
            if 'username' in error_msg.lower():
                return jsonify({'success': False, 'error': 'Username already exists'}), 400
            elif 'email' in error_msg.lower():
                return jsonify({'success': False, 'error': 'Email already registered'}), 400
            else:
                return jsonify({'success': False, 'error': 'Username or email already exists'}), 400
                
    except Exception as e:
        print(f"Signup error: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred during signup'}), 500

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

@app.route('/api/alerts', methods=['POST'])
def create_alert():
    """API endpoint to create a price alert"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        url = data.get('url', '').strip()
        target_price = data.get('target_price', 0)
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        if not target_price or target_price <= 0:
            return jsonify({'success': False, 'error': 'Valid target price is required'}), 400
        
        # Get product info
        site_name, currency, currency_symbol = get_site_info(url)
        
        # Get current price
        current_price, _, _, _, error = scrape_price(url)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (user_id, url, target_price, site_name, current_price, currency, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
        ''', (session['user_id'], url, target_price, site_name, current_price, currency))
        
        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Alert created successfully!',
            'alert_id': alert_id
        })
        
    except Exception as e:
        print(f"Create alert error: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred'}), 500

@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """API endpoint to delete a price alert"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify the alert belongs to the current user
        cursor.execute('SELECT id FROM alerts WHERE id = ? AND user_id = ?', (alert_id, session['user_id']))
        alert = cursor.fetchone()
        
        if not alert:
            conn.close()
            return jsonify({'success': False, 'error': 'Alert not found'}), 404
        
        cursor.execute('DELETE FROM alerts WHERE id = ?', (alert_id,))
        cursor.execute('DELETE FROM price_history WHERE alert_id = ?', (alert_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Alert deleted successfully'})
        
    except Exception as e:
        print(f"Delete alert error: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred'}), 500

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)

