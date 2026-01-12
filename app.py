import os
import re
import sqlite3
import random
import string
import json
import secrets
from flask import Flask, request, jsonify, session, redirect, url_for, render_template, send_from_directory
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from werkzeug.security import generate_password_hash, check_password_hash
from collections import Counter
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
# Allow all origins for development (more flexible CORS)
CORS(app, supports_credentials=True, origins="*")

DATABASE = 'database.db'

# Email Configuration - Load from environment or file
def load_email_config():
    config = {
        'enabled': False,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'smtp_email': '',
        'smtp_password': '',
        'from_name': 'AI Price Alert',
        'provider': 'gmail'
    }
    
    # Try to load from config file
    config_file = 'email_config.json'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"Error loading email config: {e}")
    
    # Override with environment variables if present
    if os.environ.get('SMTP_ENABLED'):
        config['enabled'] = os.environ.get('SMTP_ENABLED').lower() == 'true'
    if os.environ.get('SMTP_SERVER'):
        config['smtp_server'] = os.environ.get('SMTP_SERVER')
    if os.environ.get('SMTP_PORT'):
        config['smtp_port'] = int(os.environ.get('SMTP_PORT'))
    if os.environ.get('SMTP_EMAIL'):
        config['smtp_email'] = os.environ.get('SMTP_EMAIL')
    if os.environ.get('SMTP_PASSWORD'):
        config['smtp_password'] = os.environ.get('SMTP_PASSWORD')
    if os.environ.get('SMTP_FROM_NAME'):
        config['from_name'] = os.environ.get('SMTP_FROM_NAME')
    
    return config

EMAIL_CONFIG = load_email_config()

# Twilio Configuration - Load from environment or file
def load_twilio_config():
    config = {
        'enabled': False,
        'account_sid': '',
        'auth_token': '',
        'phone_number': ''
    }
    
    # Try to load from config file
    config_file = 'twilio_config.json'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"Error loading Twilio config: {e}")
    
    # Override with environment variables if present
    if os.environ.get('TWILIO_ENABLED'):
        config['enabled'] = os.environ.get('TWILIO_ENABLED').lower() == 'true'
    if os.environ.get('TWILIO_ACCOUNT_SID'):
        config['account_sid'] = os.environ.get('TWILIO_ACCOUNT_SID')
    if os.environ.get('TWILIO_AUTH_TOKEN'):
        config['auth_token'] = os.environ.get('TWILIO_AUTH_TOKEN')
    if os.environ.get('TWILIO_PHONE_NUMBER'):
        config['phone_number'] = os.environ.get('TWILIO_PHONE_NUMBER')
    
    return config

TWILIO_CONFIG = load_twilio_config()

# Telegram Configuration - Load from environment or file
def load_telegram_config():
    config = {
        'enabled': False,
        'bot_token': '',
        'webhook_url': '',
        'bot_username': ''
    }
    
    # Try to load from config file
    config_file = 'telegram_config.json'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"Error loading Telegram config: {e}")
    
    # Override with environment variables if present
    if os.environ.get('TELEGRAM_ENABLED'):
        config['enabled'] = os.environ.get('TELEGRAM_ENABLED').lower() == 'true'
    if os.environ.get('TELEGRAM_BOT_TOKEN'):
        config['bot_token'] = os.environ.get('TELEGRAM_BOT_TOKEN')
    if os.environ.get('TELEGRAM_WEBHOOK_URL'):
        config['webhook_url'] = os.environ.get('TELEGRAM_WEBHOOK_URL')
    if os.environ.get('TELEGRAM_BOT_USERNAME'):
        config['bot_username'] = os.environ.get('TELEGRAM_BOT_USERNAME')
    
    return config

TELEGRAM_CONFIG = load_telegram_config()

# WhatsApp Configuration - Load from environment or file
def load_whatsapp_config():
    config = {
        'enabled': False,
        'twilio_account_sid': '',
        'twilio_auth_token': '',
        'twilio_whatsapp_number': '+14155238886',
        'from_name': 'AI Price Alert'
    }
    
    # Try to load from config file
    config_file = 'whatsapp_config.json'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"Error loading WhatsApp config: {e}")
    
    # Override with environment variables if present
    if os.environ.get('WHATSAPP_ENABLED'):
        config['enabled'] = os.environ.get('WHATSAPP_ENABLED').lower() == 'true'
    if os.environ.get('TWILIO_ACCOUNT_SID'):
        config['twilio_account_sid'] = os.environ.get('TWILIO_ACCOUNT_SID')
    if os.environ.get('TWILIO_AUTH_TOKEN'):
        config['twilio_auth_token'] = os.environ.get('TWILIO_AUTH_TOKEN')
    if os.environ.get('TWILIO_WHATSAPP_NUMBER'):
        config['twilio_whatsapp_number'] = os.environ.get('TWILIO_WHATSAPP_NUMBER')
    
    return config

WHATSAPP_CONFIG = load_whatsapp_config()

# Email provider presets
EMAIL_PRESETS = {
    'gmail': {
        'server': 'smtp.gmail.com',
        'port': 587,
        'secure': False
    },
    'outlook': {
        'server': 'smtp.office365.com',
        'port': 587,
        'secure': False
    },
    'yahoo': {
        'server': 'smtp.mail.yahoo.com',
        'port': 587,
        'secure': False
    },
    'yahoo_plus': {
        'server': 'smtp.mail.yahoo.com',
        'port': 465,
        'secure': True
    },
    'custom': {
        'server': '',
        'port': 587,
        'secure': False
    }
}

# Generate a 6-digit OTP
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

# Send email OTP (mock mode prints to console by default)
def send_email_otp(email, otp, purpose="verification"):
    if EMAIL_CONFIG['enabled']:
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            msg = MIMEText(f'''Your AI Price Alert {purpose} code is: {otp}

This code expires in 10 minutes.

If you didn't request this, please ignore this email.
''')
            msg['Subject'] = f'AI Price Alert - {purpose.title()} Code'
            msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['smtp_email']}>"
            msg['To'] = email
            
            with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
                server.starttls()
                server.login(EMAIL_CONFIG['smtp_email'], EMAIL_CONFIG['smtp_password'])
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Email send error: {e}")
            return False
    else:
        # Demo mode - print OTP to console
        print(f"\n{'='*50}")
        print(f"📧 EMAIL OTP ({purpose.upper()}) - DEMO MODE")
        print(f"{'='*50}")
        print(f"To: {email}")
        print(f"OTP: {otp}")
        print(f"Expires in: 10 minutes")
        print(f"{'='*50}\n")
        return True

# Send phone OTP (mock mode prints to console by default)
def send_phone_otp(phone, otp, purpose="verification"):
    if TWILIO_CONFIG['enabled']:
        try:
            from twilio.rest import Client
            
            client = Client(TWILIO_CONFIG['account_sid'], TWILIO_CONFIG['auth_token'])
            message = client.messages.create(
                body=f'AI Price Alert {purpose} code: {otp}\n\nThis code expires in 10 minutes.',
                from_=TWILIO_CONFIG['phone_number'],
                to=phone
            )
            return True
        except Exception as e:
            print(f"SMS send error: {e}")
            return False
    else:
        # Demo mode - print OTP to console
        print(f"\n{'='*50}")
        print(f"📱 PHONE OTP ({purpose.upper()}) - DEMO MODE")
        print(f"{'='*50}")
        print(f"To: {phone}")
        print(f"OTP: {otp}")
        print(f"Expires in: 10 minutes")
        print(f"{'='*50}\n")
        return True

# Send password reset email
def send_password_reset_email(email, reset_token):
    if EMAIL_CONFIG['enabled']:
        try:
            reset_link = f"{request.host_url}reset-password?token={reset_token}"
            
            msg = MIMEText(f'''Password Reset Request

You requested to reset your password for AI Price Alert.

Click the link below to reset your password:
{reset_link}

This link expires in 30 minutes.

If you didn't request this, please ignore this email.
''')
            msg['Subject'] = 'AI Price Alert - Password Reset'
            msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['smtp_email']}>"
            msg['To'] = email
            
            with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
                server.starttls()
                server.login(EMAIL_CONFIG['smtp_email'], EMAIL_CONFIG['smtp_password'])
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Password reset email send error: {e}")
            return False
    else:
        # Demo mode - print to console
        print(f"\n{'='*50}")
        print(f"📧 PASSWORD RESET EMAIL - DEMO MODE")
        print(f"{'='*50}")
        print(f"To: {email}")
        print(f"Reset Link: {request.host_url}reset-password?token={reset_token}")
        print(f"Expires in: 30 minutes")
        print(f"{'='*50}\n")
        return True

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create users table with 2FA fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            phone TEXT,
            email_verified INTEGER DEFAULT 0,
            phone_verified INTEGER DEFAULT 0,
            two_factor_enabled INTEGER DEFAULT 0,
            two_factor_method TEXT DEFAULT 'none',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create OTP verification table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS otp_verification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email TEXT,
            phone TEXT,
            email_otp TEXT,
            phone_otp TEXT,
            email_otp_expiry TIMESTAMP,
            phone_otp_expiry TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create password reset tokens table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reset_token TEXT NOT NULL UNIQUE,
            reset_token_expiry TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create trackers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trackers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            product_name TEXT,
            current_price REAL NOT NULL,
            target_price REAL NOT NULL,
            currency TEXT,
            currency_symbol TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Add site column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE trackers ADD COLUMN site TEXT DEFAULT 'unknown'")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Create pending_signups table for email/phone verification during signup
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_signups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signup_token TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            email_otp TEXT,
            email_otp_expiry TIMESTAMP,
            phone_otp TEXT,
            phone_otp_expiry TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# ==================== OTP ROUTES ====================

@app.route('/api/send-email-otp', methods=['POST'])
def send_email_otp_route():
    """Send OTP to email for verification"""
    data = request.json
    email = data.get('email')
    purpose = data.get('purpose', 'verification')  # verification, login, reset
    signup_token = data.get('signupToken')  # Optional: for linking to pending signup
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    otp = generate_otp()
    expiry = datetime.now() + timedelta(minutes=10)
    
    # Store OTP in database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # If we have a signup token, update pending_signups with email OTP info
    if signup_token:
        cursor.execute("""
            UPDATE pending_signups 
            SET email_otp = ?, email_otp_expiry = ?
            WHERE signup_token = ? AND email = ?
        """, (otp, expiry.isoformat(), signup_token, email))
        
        if cursor.rowcount == 0:
            # Signup token not found, check if it's for an existing user
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if user:
                cursor.execute("""
                    UPDATE otp_verification 
                    SET email_otp = ?, email_otp_expiry = ?
                    WHERE user_id = ?
                """, (otp, expiry.isoformat(), user[0]))
                
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO otp_verification (user_id, email, email_otp, email_otp_expiry)
                        VALUES (?, ?, ?, ?)
                    """, (user[0], email, otp, expiry.isoformat()))
    else:
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if user:
            # Update existing user's OTP
            cursor.execute("""
                UPDATE otp_verification 
                SET email_otp = ?, email_otp_expiry = ?, email = ?
                WHERE user_id = ?
            """, (otp, expiry.isoformat(), email, user[0]))
            
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO otp_verification (user_id, email, email_otp, email_otp_expiry)
                    VALUES (?, ?, ?, ?)
                """, (user[0], email, otp, expiry.isoformat()))
        else:
            # Create temporary OTP record for signup
            cursor.execute("""
                INSERT INTO otp_verification (email, email_otp, email_otp_expiry)
                VALUES (?, ?, ?)
            """, (email, otp, expiry.isoformat()))
    
    conn.commit()
    conn.close()
    
    # Send OTP
    if send_email_otp(email, otp, purpose):
        return jsonify({
            "success": "OTP sent to email",
            "message": "Check your email for the OTP",
            "demo_mode": not EMAIL_CONFIG['enabled']
        }), 200
    else:
        return jsonify({"error": "Failed to send OTP"}), 500

@app.route('/api/send-phone-otp', methods=['POST'])
def send_phone_otp_route():
    """Send OTP to phone for verification"""
    data = request.json
    phone = data.get('phone')
    purpose = data.get('purpose', 'verification')
    signup_token = data.get('signupToken')  # Optional: for linking to pending signup
    
    if not phone:
        return jsonify({"error": "Phone number is required"}), 400
    
    # Validate phone format (basic validation)
    phone_clean = re.sub(r'[^\d+]', '', phone)
    if len(phone_clean) < 10:
        return jsonify({"error": "Invalid phone number format"}), 400
    
    otp = generate_otp()
    expiry = datetime.now() + timedelta(minutes=10)
    
    # Store OTP in database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # If we have a signup token, update pending_signups with phone OTP info
    if signup_token:
        cursor.execute("""
            UPDATE pending_signups 
            SET phone_otp = ?, phone_otp_expiry = ?
            WHERE signup_token = ? AND phone = ?
        """, (otp, expiry.isoformat(), signup_token, phone))
        
        if cursor.rowcount == 0:
            # Signup token not found, check if it's for an existing user
            cursor.execute("SELECT id FROM users WHERE phone = ?", (phone,))
            user = cursor.fetchone()
            
            if user:
                cursor.execute("""
                    UPDATE otp_verification 
                    SET phone_otp = ?, phone_otp_expiry = ?
                    WHERE user_id = ?
                """, (otp, expiry.isoformat(), user[0]))
                
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO otp_verification (user_id, phone, phone_otp, phone_otp_expiry)
                        VALUES (?, ?, ?, ?)
                    """, (user[0], phone, otp, expiry.isoformat()))
    else:
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE phone = ?", (phone,))
        user = cursor.fetchone()
        
        if user:
            cursor.execute("""
                UPDATE otp_verification 
                SET phone_otp = ?, phone_otp_expiry = ?, phone = ?
                WHERE user_id = ?
            """, (otp, expiry.isoformat(), phone, user[0]))
            
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO otp_verification (user_id, phone, phone_otp, phone_otp_expiry)
                    VALUES (?, ?, ?, ?)
                """, (user[0], phone, otp, expiry.isoformat()))
        else:
            cursor.execute("""
                INSERT INTO otp_verification (phone, phone_otp, phone_otp_expiry)
                VALUES (?, ?, ?)
            """, (phone, otp, expiry.isoformat()))
    
    conn.commit()
    conn.close()
    
    # Send OTP
    if send_phone_otp(phone, otp, purpose):
        return jsonify({
            "success": "OTP sent to phone",
            "message": "Check your phone for the OTP",
            "demo_mode": not TWILIO_CONFIG['enabled']
        }), 200
    else:
        return jsonify({"error": "Failed to send OTP"}), 500

@app.route('/api/verify-email-otp', methods=['POST'])
def verify_email_otp():
    """Verify email OTP"""
    data = request.json
    email = data.get('email')
    otp = data.get('otp')
    
    if not email or not otp:
        return jsonify({"error": "Email and OTP are required"}), 400
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Find OTP record
    cursor.execute("""
        SELECT email_otp, email_otp_expiry, user_id FROM otp_verification 
        WHERE email = ?
    """, (email,))
    record = cursor.fetchone()
    
    if not record:
        conn.close()
        return jsonify({"error": "OTP not found. Please request a new OTP."}), 404
    
    stored_otp, expiry_str, user_id = record
    
    # Check expiry
    expiry = datetime.fromisoformat(expiry_str) if expiry_str else None
    if expiry and datetime.now() > expiry:
        conn.close()
        return jsonify({"error": "OTP has expired. Please request a new one."}), 400
    
    # Verify OTP
    if stored_otp == otp:
        # Mark email as verified
        if user_id:
            cursor.execute("UPDATE users SET email_verified = 1 WHERE id = ?", (user_id,))
        
        # Clear the OTP
        cursor.execute("""
            UPDATE otp_verification SET email_otp = NULL, email_otp_expiry = NULL 
            WHERE email = ?
        """, (email,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": "Email verified successfully"}), 200
    else:
        conn.close()
        return jsonify({"error": "Invalid OTP. Please try again."}), 400

@app.route('/api/verify-phone-otp', methods=['POST'])
def verify_phone_otp():
    """Verify phone OTP"""
    data = request.json
    phone = data.get('phone')
    otp = data.get('otp')
    
    if not phone or not otp:
        return jsonify({"error": "Phone and OTP are required"}), 400
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Find OTP record
    cursor.execute("""
        SELECT phone_otp, phone_otp_expiry, user_id FROM otp_verification 
        WHERE phone = ?
    """, (phone,))
    record = cursor.fetchone()
    
    if not record:
        conn.close()
        return jsonify({"error": "OTP not found. Please request a new OTP."}), 404
    
    stored_otp, expiry_str, user_id = record
    
    # Check expiry
    expiry = datetime.fromisoformat(expiry_str) if expiry_str else None
    if expiry and datetime.now() > expiry:
        conn.close()
        return jsonify({"error": "OTP has expired. Please request a new one."}), 400
    
    # Verify OTP
    if stored_otp == otp:
        # Mark phone as verified
        if user_id:
            cursor.execute("UPDATE users SET phone_verified = 1 WHERE id = ?", (user_id,))
        
        # Clear the OTP
        cursor.execute("""
            UPDATE otp_verification SET phone_otp = NULL, phone_otp_expiry = NULL 
            WHERE phone = ?
        """, (phone,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": "Phone verified successfully"}), 200
    else:
        conn.close()
        return jsonify({"error": "Invalid OTP. Please try again."}), 400

@app.route('/api/setup-2fa', methods=['POST'])
def setup_2fa():
    """Enable 2FA for a user"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.json
    method = data.get('method')  # 'email', 'phone', 'both'
    
    if not method or method not in ['email', 'phone', 'both']:
        return jsonify({"error": "Invalid 2FA method"}), 400
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Get user's current verification status
    cursor.execute("""
        SELECT email_verified, phone_verified FROM users WHERE id = ?
    """, (session['user_id'],))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404
    
    email_verified, phone_verified = user
    
    # Check if user has verified the required method
    if method == 'email' and not email_verified:
        conn.close()
        return jsonify({"error": "Please verify your email first"}), 400
    
    if method == 'phone' and not phone_verified:
        conn.close()
        return jsonify({"error": "Please verify your phone first"}), 400
    
    if method == 'both' and not (email_verified and phone_verified):
        conn.close()
        return jsonify({"error": "Please verify both email and phone first"}), 400
    
    # Enable 2FA
    cursor.execute("""
        UPDATE users SET two_factor_enabled = 1, two_factor_method = ? WHERE id = ?
    """, (method, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": "2FA enabled successfully",
        "method": method
    }), 200

@app.route('/api/disable-2fa', methods=['POST'])
def disable_2fa():
    """Disable 2FA for a user"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET two_factor_enabled = 0, two_factor_method = 'none' 
        WHERE id = ?
    """, (session['user_id'],))
    conn.commit()
    conn.close()
    
    return jsonify({"success": "2FA disabled successfully"}), 200

@app.route('/api/2fa-status', methods=['GET'])
def get_2fa_status():
    """Get user's 2FA status"""
    if 'user_id' not in session:
        return jsonify({"enabled": False, "method": "none"}), 401
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT two_factor_enabled, two_factor_method, email_verified, phone_verified 
        FROM users WHERE id = ?
    """, (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({
            "enabled": bool(user[0]),
            "method": user[1],
            "emailVerified": bool(user[2]),
            "phoneVerified": bool(user[3])
        }), 200
    
    return jsonify({"enabled": False, "method": "none"}), 404

# ==================== AUTH ROUTES ====================

@app.route('/')
def root():
    return redirect(url_for('signup'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        phone = data.get('phone')

        if not all([username, email, password]):
            return jsonify({"error": "Missing data"}), 400

        # Check if email already exists
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"error": "Email already exists"}), 409
        
        # Check if there's already a pending signup for this email
        cursor.execute("SELECT id FROM pending_signups WHERE email = ?", (email,))
        if cursor.fetchone():
            # Delete old pending signup
            cursor.execute("DELETE FROM pending_signups WHERE email = ?", (email,))
        
        conn.close()

        # Create user account directly
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (username, email, password, phone, email_verified, phone_verified)
            VALUES (?, ?, ?, ?, 1, 1)
        """, (username, email, generate_password_hash(password), phone))
        
        conn.commit()
        conn.close()

        return jsonify({
            "success": "Account created successfully"
        }), 200

    return render_template('signup.html')

@app.route('/api/signup-complete', methods=['POST'])
def signup_complete():
    """Complete signup after email/phone verification - creates account only after OTP verification"""
    data = request.get_json()
    signup_token = data.get('signupToken')
    email_otp = data.get('emailOTP', '')
    phone_otp = data.get('phoneOTP', '')
    email_verified = False
    phone_verified = False
    
    if not signup_token:
        return jsonify({"error": "Signup token is required"}), 400
    
    # Get pending signup data
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pending_signups WHERE signup_token = ?", (signup_token,))
    pending = cursor.fetchone()
    
    if not pending:
        conn.close()
        return jsonify({"error": "Invalid or expired signup session. Please start over."}), 400
    
    signup_id, stored_token, username, email, password, phone, stored_email_otp, stored_email_otp_expiry, stored_phone_otp, stored_phone_otp_expiry, created_at = pending
    
    # Check if pending signup expired (30 minutes)
    expiry = datetime.fromisoformat(created_at) + timedelta(minutes=30)
    if datetime.now() > expiry:
        cursor.execute("DELETE FROM pending_signups WHERE id = ?", (signup_id,))
        conn.commit()
        conn.close()
        return jsonify({"error": "Signup session expired. Please start over."}), 400
    
    # Verify email OTP if provided
    if email_otp:
        if stored_email_otp and stored_email_otp == email_otp:
            if stored_email_otp_expiry:
                otp_expiry = datetime.fromisoformat(stored_email_otp_expiry)
                if datetime.now() > otp_expiry:
                    conn.close()
                    return jsonify({"error": "Email OTP has expired"}), 400
            # OTP is valid
            email_verified = True
        else:
            conn.close()
            return jsonify({"error": "Invalid email OTP"}), 400
    
    # Verify phone OTP if provided
    if phone_otp:
        if stored_phone_otp and stored_phone_otp == phone_otp:
            if stored_phone_otp_expiry:
                otp_expiry = datetime.fromisoformat(stored_phone_otp_expiry)
                if datetime.now() > otp_expiry:
                    conn.close()
                    return jsonify({"error": "Phone OTP has expired"}), 400
            phone_verified = True
        else:
            conn.close()
            return jsonify({"error": "Invalid phone OTP"}), 400
    
    # Require email verification at minimum
    if not email_verified:
        conn.close()
        return jsonify({
            "error": "Email verification is required",
            "requiresEmailVerification": True
        }), 400
    
    # Check if phone is provided but not verified
    if phone and not phone_verified:
        conn.close()
        return jsonify({
            "error": "Phone verification is required",
            "requiresPhoneVerification": True
        }), 400
    
    # All verifications passed - create the actual account
    try:
        cursor.execute("""
            INSERT INTO users (username, email, password, phone, email_verified, phone_verified)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, email, password, phone, 1 if email_verified else 0, 1 if phone_verified else 0))
        user_id = cursor.lastrowid
        
        # Create OTP verification record for future 2FA
        cursor.execute("""
            INSERT INTO otp_verification (user_id, email, phone)
            VALUES (?, ?, ?)
        """, (user_id, email, phone))
        
        # Delete pending signup
        cursor.execute("DELETE FROM pending_signups WHERE id = ?", (signup_id,))
        
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Email already exists"}), 409
    finally:
        conn.close()
    
    return jsonify({
        "success": "Account created successfully!",
        "userId": user_id,
        "message": "You can now login with your credentials"
    }), 201

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        otp = data.get('otp')  # For 2FA login

        if not email or not password:
            return jsonify({"error": "Missing data"}), 400

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            # Check if 2FA is enabled
            two_factor_enabled = bool(user[7]) if len(user) > 7 else False
            two_factor_method = user[8] if len(user) > 8 else 'none'
            
            if two_factor_enabled:
                # 2FA is enabled, verify OTP
                if not otp:
                    return jsonify({
                        "error": "2FA required",
                        "requires_2fa": True,
                        "method": two_factor_method
                    }), 200  # Return 200 with 2FA requirement
                
                # Verify OTP based on method
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                
                if two_factor_method in ['email', 'both']:
                    cursor.execute("""
                        SELECT email_otp, email_otp_expiry FROM otp_verification WHERE user_id = ?
                    """, (user[0],))
                    otp_record = cursor.fetchone()
                    if otp_record and otp_record[0] == otp:
                        expiry = datetime.fromisoformat(otp_record[1]) if otp_record[1] else None
                        if expiry and datetime.now() > expiry:
                            conn.close()
                            return jsonify({"error": "OTP has expired"}), 400
                        # Clear OTP after successful verification
                        cursor.execute("""
                            UPDATE otp_verification SET email_otp = NULL, email_otp_expiry = NULL 
                            WHERE user_id = ?
                        """, (user[0],))
                    elif otp_record and otp_record[0] != otp:
                        conn.close()
                        return jsonify({"error": "Invalid OTP"}), 400
                
                if two_factor_method in ['phone', 'both']:
                    cursor.execute("""
                        SELECT phone_otp, phone_otp_expiry FROM otp_verification WHERE user_id = ?
                    """, (user[0],))
                    otp_record = cursor.fetchone()
                    if otp_record and otp_record[0] == otp:
                        expiry = datetime.fromisoformat(otp_record[1]) if otp_record[1] else None
                        if expiry and datetime.now() > expiry:
                            conn.close()
                            return jsonify({"error": "OTP has expired"}), 400
                        cursor.execute("""
                            UPDATE otp_verification SET phone_otp = NULL, phone_otp_expiry = NULL 
                            WHERE user_id = ?
                        """, (user[0],))
                    elif otp_record and otp_record[0] != otp:
                        conn.close()
                        return jsonify({"error": "Invalid OTP"}), 400
                
                conn.commit()
                conn.close()
            
            # Create session
            session['user_id'] = user[0]
            return jsonify({
                "success": "Logged in",
                "requires_2fa": False
            }), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password requests"""
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            expiry = datetime.now() + timedelta(minutes=30)
            
            # Store reset token
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO password_resets (user_id, reset_token, reset_token_expiry)
                VALUES (?, ?, ?)
            """, (user[0], reset_token, expiry.isoformat()))
            conn.commit()
            conn.close()
            
            # Send reset email
            send_password_reset_email(email, reset_token)
            
            return jsonify({
                "success": "Password reset email sent",
                "demo_token": reset_token  # For demo mode
            }), 200
        else:
            # Don't reveal if email exists or not
            return jsonify({
                "success": "If an account exists, a reset link has been sent"
            }), 200
    
    return render_template('forgot-password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Handle password reset with token"""
    token = request.args.get('token')
    
    if not token:
        return render_template('error.html', error="Invalid reset link")
    
    # Verify token
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, reset_token_expiry FROM password_resets WHERE reset_token = ?
    """, (token,))
    reset_record = cursor.fetchone()
    
    if not reset_record:
        conn.close()
        return render_template('error.html', error="Invalid or expired reset link")
    
    expiry = datetime.fromisoformat(reset_record[1]) if reset_record[1] else None
    if expiry and datetime.now() > expiry:
        conn.close()
        return render_template('error.html', error="Reset link has expired")
    
    user_id = reset_record[0]
    
    if request.method == 'POST':
        data = request.get_json()
        new_password = data.get('password')
        
        if not new_password or len(new_password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        # Update password
        hashed = generate_password_hash(new_password)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed, user_id))
        
        # Clear reset token
        cursor.execute("DELETE FROM password_resets WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": "Password reset successful"}), 200
    
    conn.close()
    return render_template('reset-password.html', token=token)

@app.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    """API endpoint for forgot password"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        reset_token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(minutes=30)
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO password_resets (user_id, reset_token, reset_token_expiry)
            VALUES (?, ?, ?)
        """, (user[0], reset_token, expiry.isoformat()))
        conn.commit()
        conn.close()
        
        send_password_reset_email(email, reset_token)
        
        return jsonify({
            "success": True,
            "message": "Password reset email sent"
        }), 200
    
    return jsonify({
        "success": True,
        "message": "If an account exists, a reset link has been sent"
    }), 200

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

def parse_price(price_str):
    """Parse price string to float, handling various formats"""
    if not price_str:
        return None
    
    # Remove currency symbols, whitespace, and commas
    price_str = re.sub(r'[^\d.]', '', price_str)
    
    try:
        return float(price_str)
    except ValueError:
        return None

def get_site_info(url):
    """Determine the site and currency based on URL"""
    url_lower = url.lower()
    if 'amazon' in url_lower:
        if 'amazon.in' in url_lower:
            return 'amazon', 'INR', '₹'
        elif 'amazon.co.uk' in url_lower:
            return 'amazon', 'GBP', '£'
        else:
            return 'amazon', 'USD', '$'
    elif 'flipkart' in url_lower:
        return 'flipkart', 'INR', '₹'
    elif 'ebay' in url_lower:
        return 'ebay', 'USD', '$'
    elif 'myntra' in url_lower:
        return 'myntra', 'INR', '₹'
    elif 'ajio' in url_lower:
        return 'ajio', 'INR', '₹'
    elif 'meesho' in url_lower:
        return 'meesho', 'INR', '₹'
    elif 'snapdeal' in url_lower:
        return 'snapdeal', 'INR', '₹'
    elif 'tatacliq' in url_lower:
        return 'tatacliq', 'INR', '₹'
    elif 'reliancedigital' in url_lower or 'reliance digital' in url_lower:
        return 'reliancedigital', 'INR', '₹'
    else:
        return 'unknown', 'USD', '$'

def extract_product_name(soup, site, url):
    """Extract product name from page"""
    # Try to get from page title
    if soup.title:
        title = soup.title.get_text().strip()
        # Clean up title by removing site names
        title = re.sub(r'\s*[-|]\s*(Amazon|Flipkart|Myntra|Ajio|Meesho|Snapdeal|Tata CLiQ|Reliance Digital|eBay)\s*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*[-|]\s*Official Store\s*$', '', title)
        if title and len(title) > 3 and len(title) < 200:
            return title.split('|')[0].split('-')[0].strip()
    
    # Site-specific selectors
    selectors = {
        'amazon': [
            "#productTitle", ".a-size-extra-large", "h1#title",
            "span[data-testid='product-title']"
        ],
        'flipkart': [
            "h1[itemprop='name']", ".yhB1nd", ".G6XhRU", "span.B_NuCI"
        ],
        'myntra': [
            "h1.pdp-title", "h1[itemprop='name']", ".pdp-name"
        ],
        'ajio': [
            ".prod-name", "h1[itemprop='name']", ".name-wrap"
        ],
        'meesho': [
            "[class*='ProductCard__ProductName']", "h2", ".sc-product-title"
        ],
        'snapdeal': [
            ".pdp-e-i-header-title", "h1[itemprop='name']"
        ],
        'tatacliq': [
            "_1nE6t", ".pdp-description h1", "h1.ProductName__Styled"
        ],
        'reliancedigital': [
            ".pdp__title", "h1[itemprop='name']", ".pdp-product-title"
        ]
    }
    
    if site in selectors:
        for selector in selectors[site]:
            elem = soup.select_one(selector)
            if elem:
                name = elem.get_text().strip()
                if name and len(name) > 3:
                    return name.split('|')[0].split('-')[0].strip()
    
    # Fallback: extract from URL
    try:
        from urllib.parse import urlparse
        path = urlparse(url).path
        parts = [p for p in path.split('/') if p and not p.isdigit() and len(p) > 2]
        if parts:
            return ' '.join(parts[-3:]).replace('-', ' ').replace('_', ' ').title()
    except:
        pass
    
    return "Product"

def scrape_amazon_price(soup, currency_symbol):
    """Scrape price from Amazon pages - tries multiple selectors for modern Amazon layouts"""
    
    # Try modern Amazon price structure with a-price
    price_elem = soup.find("span", {"class": "a-price"})
    if price_elem:
        # Get the whole part (main price)
        whole = price_elem.find("span", {"class": "a-price-whole"})
        if whole:
            price_str = whole.get_text()
            price = parse_price(price_str)
            if price:
                return price
        
        # Try the entire price text
        price_text = price_elem.find("span", {"class": "a-offscreen"})
        if price_text:
            price = parse_price(price_text.get_text())
            if price:
                return price

    # Try to find price in structured data (JSON-LD)
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        if script.string:
            # Look for price in JSON
            price_match = re.search(r'"price"\s*:\s*([\d.]+)', script.string)
            if price_match:
                price = parse_price(price_match.group(1))
                if price:
                    return price
    
    # Try a-offscreen elements with better filtering
    offscreen_elements = soup.find_all(class_="a-offscreen")
    prices = []
    for elem in offscreen_elements:
        text = elem.get_text().strip()
        if text and (text.startswith(currency_symbol) or any(c in text for c in ['$', '£', '€', '₹'])):
            price = parse_price(text)
            if price and 50 < price < 100000:  # Reasonable price range filter (min 50 for INR/USD)
                prices.append(price)

    if prices:
        # Return a reasonable median price (not too low, not too high)
        prices.sort()
        return prices[len(prices)//2] if prices else None

    # Try span with a-size-medium or a-color-price
    price_elements = soup.find_all("span", class_=lambda x: x and "a-color-price" in x if x else False)
    for elem in price_elements:
        price = parse_price(elem.get_text())
        if price and 50 < price < 100000:  # Reasonable price range filter (min 50 for INR/USD)
            return price

    # Try inline-price data attributes
    inline_price = soup.find("span", {"data-a-color": True})
    if inline_price:
        price = parse_price(inline_price.get_text())
        if price and 50 < price < 100000:  # Reasonable price range filter (min 50 for INR/USD)
            return price

    # Legacy selectors as final fallback
    price_element = soup.find("span", {"id": "priceblock_ourprice"})
    if price_element:
        price = parse_price(price_element.get_text())
        if price and 50 < price < 100000:  # Reasonable price range filter (min 50 for INR/USD)
            return price

    price_element = soup.find("span", {"id": "priceblock_dealprice"})
    if price_element:
        price = parse_price(price_element.get_text())
        if price and 50 < price < 100000:  # Reasonable price range filter (min 50 for INR/USD)
            return price

    return None

def scrape_flipkart_price(soup):
    """Scrape price from Flipkart pages - improved to get selling price (not shipping/delivery fees)"""
    
    # Method 1: Try JSON-LD structured data first (most reliable)
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        if script.string:
            # Look for "price" field (usually selling price)
            price_match = re.search(r'"price"\s*:\s*([\d.]+)', script.string)
            if price_match:
                price = parse_price(price_match.group(1))
                if price and 100 < price < 100000:  # Higher minimum for real products
                    return price

            # Look for "lowPrice" (selling price)
            low_match = re.search(r'"lowPrice"\s*:\s*([\d.]+)', script.string)
            if low_match:
                price = parse_price(low_match.group(1))
                if price and 100 < price < 100000:  # Higher minimum for real products
                    return price

            # Look for "offers" > "price" structure
            offer_match = re.search(r'"offers".*?"price"\s*:\s*([\d.]+)', script.string, re.DOTALL)
            if offer_match:
                price = parse_price(offer_match.group(1))
                if price and 100 < price < 100000:
                    return price

    # Method 2: Try specific Flipkart price selectors with most reliable first
    # These are the modern Flipkart selectors for the main product price
    price_selectors = [
        "div._30jeq3._16Jk6d",  # Main selling price (most common modern selector)
        "div._25DpV",  # Alternative price container
        "div._1kMS",  # Price container
        "span._16Jk6d",  # Span variant
        "div[itemprop='price']",  # Schema selling price
        "span[itemprop='price']",  # Schema selling price span
        "[data-testid='price']",  # Test ID price
        "div._1uvC7F",  # Another Flipkart price class
        "span._1w3__o",  # Flipkart price span
        "div.flash-price",  # Flash sale price
        "div._1kX4qa",  # Price wrapper
    ]
    
    for selector in price_selectors:
        price_element = soup.select_one(selector)
        if price_element:
            text = price_element.get_text().strip()
            # Extract all prices from this element
            nums = re.findall(r'[\d,]+\.?\d*', text.replace(",", ""))
            for num_str in nums:
                try:
                    val = float(num_str.replace(",", ""))
                    if 100 < val < 100000:  # Reasonable price range (min 100 for INR)
                        return val
                except ValueError:
                    continue

    # Method 3: Find parent price containers and extract from there
    # Flipkart often wraps the price in specific containers
    price_containers = soup.find_all(class_=lambda x: x and any(kw in str(x).lower() for kw in ['price', 'cost', 'amount', 'selling']) if x else False)
    
    for container in price_containers:
        # Look for ₹ symbol within this container
        container_text = container.get_text()
        if '₹' in container_text:
            # Find prices in this container
            nums = re.findall(r'₹\s*([\d,]+\.?\d*)', container_text)
            for match in nums:
                try:
                    val = float(match.replace(",", ""))
                    if 100 < val < 100000:  # Reasonable price range
                        return val
                except ValueError:
                    continue

    # Method 4: Look for the main product price in the page
    # Focus on the area near product title or main image
    main_price_area = soup.select_one("div._2DqnCV, div._2X_du7")  # Try common main price areas
    if main_price_area:
        text = main_price_area.get_text()
        nums = re.findall(r'₹\s*([\d,]+\.?\d*)', text)
        for match in nums:
            try:
                val = float(match.replace(",", ""))
                if 100 < val < 100000:
                    return val
            except ValueError:
                continue

    # Method 5: Look for prices near "Buy" or "Add to Cart" buttons
    buy_button_area = soup.find_parent("div", class_=lambda x: x and "button" in str(x).lower() if x else False)
    if buy_button_area:
        # Look for price near the button
        parent = buy_button_area.find_parent()
        if parent:
            text = parent.get_text()
            nums = re.findall(r'₹\s*([\d,]+\.?\d*)', text)
            for match in nums:
                try:
                    val = float(match.replace(",", ""))
                    if 100 < val < 100000:
                        return val
                except ValueError:
                    continue

    # Method 6: Last resort - look for higher prices (products, not shipping)
    # Filter out likely shipping costs (usually under ₹100)
    all_prices = []
    all_elements = soup.find_all(string=lambda t: t and '₹' in t if t else False)
    for elem_text in all_elements:
        # Skip elements that look like shipping/delivery
        upper_text = elem_text.upper()
        skip_words = ['FREE', 'DELIVERY', 'SHIPPING', 'shipping', 'Delivery', 'Shipping', 
                     '₹0', '₹10', '₹20', '₹30', '₹40', '₹49', '₹50', '₹60', '₹70', '₹80', '₹90']
        
        if any(word in upper_text for word in skip_words):
            continue
            
        price = parse_price(elem_text)
        if price and 100 < price < 100000:  # Only reasonable product prices
            all_prices.append(price)

    if all_prices:
        # Return the most common price (most likely the product price)
        from collections import Counter
        price_counts = Counter(all_prices)
        return price_counts.most_common(1)[0][0]

    return None

def scrape_ebay_price(soup):
    """Scrape price from eBay pages"""
    selectors = [
        "span.notranslate",  # Main price
        "span[itemprop='price']",  # Schema.org price
        "div.u-flL > span",  # Alternative
    ]
    for selector in selectors:
        price_element = soup.select_one(selector)
        if price_element:
            price = parse_price(price_element.get_text())
            if price:
                return price
    return None

def scrape_myntra_price(soup):
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
            
            # Look for "discountedPrice" or "offerPrice"
            discount_matches = re.findall(r'(?:discountedPrice|offerPrice|finalPrice)["\']?\s*:\s*([\d.]+)', script_text, re.IGNORECASE)
            for match in discount_matches:
                try:
                    val = float(match)
                    if 200 < val < 100000:
                        return val
                except ValueError:
                    continue
    
    # Method 2: Look for price in the main price container - prioritize selling price (not struck-through)
    # Myntra shows: Original price (struck through) and Selling price (bold)
    
    # Look for the discount label which contains the selling price
    discount_label = soup.find(class_=lambda x: x and 'discountLabel' in str(x).lower() if x else False)
    if discount_label:
        text = discount_label.get_text()
        nums = re.findall(r'[\d,]+\.?\d*', text.replace(",", ""))
        for num_str in nums:
            try:
                val = float(num_str.replace(",", ""))
                if 100 < val < 100000:
                    return val
            except ValueError:
                continue
    
    # Method 3: Look for price sections - focus on items-pds-price or similar
    price_sections = soup.find_all(class_=lambda x: x and any(kw in str(x).lower() for kw in ['price', 'sell', 'final', 'current']) if x else False)
    
    for section in price_sections:
        section_text = section.get_text()
        # Skip sections with struck-through text (original prices)
        if 'text-decoration' in str(section) or 'line-through' in str(section):
            continue
        
        # Find ₹ followed by a price
        rs_matches = re.findall(r'₹\s*([\d,]+\.?\d*)', section_text)
        for match in rs_matches:
            try:
                val = float(match.replace(",", ""))
                if 100 < val < 100000:
                    # Make sure this isn't in a list of sizes (those are usually smaller)
                    if 'size' not in section_text.lower() and 'size:' not in section_text.lower():
                        return val
            except ValueError:
                continue
    
    # Method 4: Look for the main product price in the PDP (Product Detail Page)
    # Focus on the price-info or similar containers
    main_price_area = soup.select_one("div.price-info, span.price-info, div.pdp-price-container, span.pdp-price-container")
    if main_price_area:
        text = main_price_area.get_text()
        nums = re.findall(r'[\d,]+\.?\d*', text.replace(",", ""))
        for num_str in nums:
            try:
                val = float(num_str.replace(",", ""))
                if 100 < val < 100000:
                    return val
            except ValueError:
                continue
    
    # Method 5: Try specific Myntra selectors - prioritize selling price selectors
    selling_price_selectors = [
        "span[itemprop='price']",  # Schema selling price
        "[class*='selling-price']",  # Selling price class
        "[class*='sellingPrice']",  # SellingPrice in data
        "[class*='final-price']",  # Final price
        "[class*='current-price']",  # Current price
        "[class*='actualPrice']",  # Actual price
        ".pdp__selling-price",  # Myntra PDP selling price
        ".pdp-selling-price",  # Alternative
        "span.discounted-price",  # Discounted price
        "span.selling",  # Selling price
        ".price-item",  # Generic price item
        ".currentPrice",  # Current price class
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
    
    # Method 6: Try the standard price selectors
    price_selectors = [
        "span.pdp-price",
        "div.pdp-price", 
        "span.pdp__price",
        "div.pdp__price",
        "[data-testid='price']",
        ".pdpPrices",
        ".price-details",
        ".price-info",
        "span[class*='Price']",
        "div[class*='Price']",
    ]
    
    for selector in price_selectors:
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
    
    # Method 7: Look for price in buttons or buy sections (these usually have selling price)
    buy_button = None
    try:
        buy_button = soup.find_parent("button", class_=lambda x: x and 'buy' in str(x).lower() if x else False)
    except Exception:
        pass
    if buy_button:
        parent = buy_button.find_parent()
        if parent:
            text = parent.get_text()
            nums = re.findall(r'₹\s*([\d,]+\.?\d*)', text)
            for match in nums:
                try:
                    val = float(match.replace(",", ""))
                    if 100 < val < 100000:
                        return val
                except ValueError:
                    continue
    
    # Method 8: Look for the smallest price in the page (usually selling price is displayed prominently)
    # But exclude very small prices (shipping, etc.)
    all_prices = []
    all_elements = soup.find_all(string=lambda t: t and '₹' in t if t else False)
    
    for elem_text in all_elements:
        upper_text = elem_text.upper()
        # Skip shipping/delivery related text
        skip_words = ['FREE', 'DELIVERY', 'SHIPPING', 'DELIVERY FEE', 
                     '₹0', '₹10', '₹20', '₹30', '₹40', '₹49', '₹50', 
                     '₹60', '₹70', '₹80', '₹90', '₹99', '₹100',
                     '₹150', '₹199']
        
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
        # Return the most common price (most likely the selling price)
        from collections import Counter
        price_counts = Counter(all_prices)
        return price_counts.most_common(1)[0][0]
    
    # Method 9: Last resort - try JSON-LD structured data
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        if script.string:
            price_match = re.search(r'"price"\s*:\s*([\d.]+)', script.string)
            if price_match:
                price = parse_price(price_match.group(1))
                if price and 100 < price < 100000:
                    return price
    
    return None

def scrape_ajio_price(soup):
    """Scrape price from Ajio pages - tries multiple modern selectors"""
    # Try to find all elements with price-related classes
    price_elements = soup.find_all(class_=lambda x: x and any(kw in x.lower() for kw in ['price', 'discount', 'sell', 'final']) if x else False)
    
    for elem in price_elements:
        text = elem.get_text().strip()
        if '₹' in text:
            nums = re.findall(r'[\d,]+\.?\d*', text.replace(",", ""))
            for num_str in nums:
                try:
                    val = float(num_str.replace(",", ""))
                    if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                        return val
                except ValueError:
                    continue
    
    # Try specific Ajio selectors
    selectors = [
        "span.price",  # Main price
        "div.price",  # Alternative
        "span[itemprop='price']",  # Schema price
        "span.discounted-price",  # Discounted price
        "span.selling-price",  # Selling price
        "div.product-price",  # Product price
        "div.price-info",  # Price info
        "span.final-price",  # Final price
        "div[itemprop='price']",  # Schema div
        "[data-testid='price']",  # Test ID
        "span._1jOx",  # Ajio specific class
        "span._2e7",  # Ajio specific class
    ]
    
    for selector in selectors:
        price_element = soup.select_one(selector)
        if price_element:
            text = price_element.get_text().strip()
            nums = re.findall(r'[\d,]+\.?\d*', text.replace(",", ""))
            for num_str in nums:
                try:
                    val = float(num_str.replace(",", ""))
                    if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                        return val
                except ValueError:
                    continue
    
    # Try finding price in scripts or JSON data
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        if script.string:
            price_match = re.search(r'"price"\s*:\s*([\d.]+)', script.string)
            if price_match:
                try:
                    val = float(price_match.group(1))
                    if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                        return val
                except ValueError:
                    pass
    
    # Try finding price in any element containing ₹ symbol
    all_elements = soup.find_all(text=lambda t: t and '₹' in t)
    for elem_text in all_elements:
        nums = re.findall(r'[\d,]+\.?\d*', elem_text.replace(",", ""))
        for num_str in nums:
            try:
                val = float(num_str.replace(",", ""))
                if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                    return val
            except ValueError:
                continue
    
    # Last resort: look for any reasonable price pattern
    all_text = soup.get_text()
    price_matches = re.findall(r'₹\s*([\d,]+\.?\d*)', all_text)
    for match in price_matches:
        try:
            val = float(match.replace(",", ""))
            if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                return val
        except ValueError:
            continue
    
    return None

def scrape_meesho_price(soup):
    """Scrape price from Meesho pages - tries multiple modern selectors"""
    # Try to find all elements with price-related classes
    price_elements = soup.find_all(class_=lambda x: x and any(kw in x.lower() for kw in ['price', 'discount', 'sell', 'final', 'cost']) if x else False)

    for elem in price_elements:
        text = elem.get_text().strip()
        if '₹' in text:
            nums = re.findall(r'[\d,]+\.?\d*', text.replace(",", ""))
            for num_str in nums:
                try:
                    val = float(num_str.replace(",", ""))
                    if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                        return val
                except ValueError:
                    continue

    # Try specific Meesho selectors
    selectors = [
        "span[data-testid='price']",  # Price element
        "div[itemprop='price']",  # Schema price
        "span.sc-price",  # Alternative price class
        "span.discounted-price",  # Discounted price
        "span.selling-price",  # Selling price
        "div.product-price",  # Product price
        "div.price-info",  # Price info
        "span.final-price",  # Final price
        "[class*='Price']",  # Any class with Price
        "[class*='price']",  # Any class with price
        "span.ProductCard__Price",  # Meesho ProductCard Price
        "span.Text__StyledText",  # Meesho styled text
    ]

    for selector in selectors:
        price_element = soup.select_one(selector)
        if price_element:
            text = price_element.get_text().strip()
            nums = re.findall(r'[\d,]+\.?\d*', text.replace(",", ""))
            for num_str in nums:
                try:
                    val = float(num_str.replace(",", ""))
                    if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                        return val
                except ValueError:
                    continue

    # Try finding price in scripts or JSON data
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        if script.string:
            price_match = re.search(r'"price"\s*:\s*([\d.]+)', script.string)
            if price_match:
                try:
                    val = float(price_match.group(1))
                    if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                        return val
                except ValueError:
                    pass

    # Try finding price in any element containing ₹ symbol
    all_elements = soup.find_all(string=lambda t: t and '₹' in t)
    for elem_text in all_elements:
        nums = re.findall(r'[\d,]+\.?\d*', elem_text.replace(",", ""))
        for num_str in nums:
            try:
                val = float(num_str.replace(",", ""))
                if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                    return val
            except ValueError:
                continue
    
    # Last resort: look for any reasonable price pattern
    all_text = soup.get_text()
    price_matches = re.findall(r'₹\s*([\d,]+\.?\d*)', all_text)
    for match in price_matches:
        try:
            val = float(match.replace(",", ""))
            if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                return val
        except ValueError:
            continue
    
    return None

def scrape_snapdeal_price(soup):
    """Scrape price from Snapdeal pages - tries multiple modern selectors"""
    # Try to find all elements with price-related classes
    price_elements = soup.find_all(class_=lambda x: x and any(kw in x.lower() for kw in ['price', 'discount', 'sell', 'final', 'amount']) if x else False)
    
    for elem in price_elements:
        text = elem.get_text().strip()
        if '₹' in text:
            nums = re.findall(r'[\d,]+\.?\d*', text.replace(",", ""))
            for num_str in nums:
                try:
                    val = float(num_str.replace(",", ""))
                    if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                        return val
                except ValueError:
                    continue
    
    # Try specific Snapdeal selectors
    selectors = [
        "span[itemprop='price']",  # Schema price
        "div.pdp-price",  # Main price
        "span.pdp-final-price",  # Final price
        "span.discounted-price",  # Discounted price
        "span.selling-price",  # Selling price
        "div.product-price",  # Product price
        "div.price-info",  # Price info
        "span.final-price",  # Final price
        "div[itemprop='price']",  # Schema div
        "[data-testid='price']",  # Test ID
        "span.pdp__price",  # Snapdeal specific
        "div.pdp__price",  # Snapdeal specific
    ]
    
    for selector in selectors:
        price_element = soup.select_one(selector)
        if price_element:
            text = price_element.get_text().strip()
            nums = re.findall(r'[\d,]+\.?\d*', text.replace(",", ""))
            for num_str in nums:
                try:
                    val = float(num_str.replace(",", ""))
                    if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                        return val
                except ValueError:
                    continue
    
    # Try finding price in scripts or JSON data
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        if script.string:
            price_match = re.search(r'"price"\s*:\s*([\d.]+)', script.string)
            if price_match:
                try:
                    val = float(price_match.group(1))
                    if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                        return val
                except ValueError:
                    pass
    
    # Try finding price in any element containing ₹ symbol
    all_elements = soup.find_all(text=lambda t: t and '₹' in t)
    for elem_text in all_elements:
        nums = re.findall(r'[\d,]+\.?\d*', elem_text.replace(",", ""))
        for num_str in nums:
            try:
                val = float(num_str.replace(",", ""))
                if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                    return val
            except ValueError:
                continue
    
    # Last resort: look for any reasonable price pattern
    all_text = soup.get_text()
    price_matches = re.findall(r'₹\s*([\d,]+\.?\d*)', all_text)
    for match in price_matches:
        try:
            val = float(match.replace(",", ""))
            if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                return val
        except ValueError:
            continue
    
    return None

def scrape_tata_cliq_price(soup):
    """Scrape price from Tata CLiQ pages - tries multiple modern selectors"""
    # Try to find all elements with price-related classes
    price_elements = soup.find_all(class_=lambda x: x and any(kw in x.lower() for kw in ['price', 'discount', 'sell', 'final', 'amount', 'tata']) if x else False)

    for elem in price_elements:
        text = elem.get_text().strip()
        if '₹' in text:
            nums = re.findall(r'[\d,]+\.?\d*', text.replace(",", ""))
            for num_str in nums:
                try:
                    val = float(num_str.replace(",", ""))
                    if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                        return val
                except ValueError:
                    continue

    # Try specific Tata CLiQ selectors
    selectors = [
        "span.price",  # Main price
        "div.price",  # Alternative
        "[data-testid='price']",  # Test ID price
        "span.discounted-price",  # Discounted price
        "span.selling-price",  # Selling price
        "div.product-price",  # Product price
        "div.price-info",  # Price info
        "span.final-price",  # Final price
        "div[itemprop='price']",  # Schema div
        "[class*='price']",  # Any class with price
        "[class*='Price']",  # Any class with Price
        "span.TaC__Price",  # Tata CLiQ specific
        "div.TaC__Price",  # Tata CLiQ specific
        "span.Price",  # Capital P Price
    ]

    for selector in selectors:
        price_element = soup.select_one(selector)
        if price_element:
            text = price_element.get_text().strip()
            nums = re.findall(r'[\d,]+\.?\d*', text.replace(",", ""))
            for num_str in nums:
                try:
                    val = float(num_str.replace(",", ""))
                    if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                        return val
                except ValueError:
                    continue

    # Try finding price in scripts or JSON data
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        if script.string:
            price_match = re.search(r'"price"\s*:\s*([\d.]+)', script.string)
            if price_match:
                try:
                    val = float(price_match.group(1))
                    if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                        return val
                except ValueError:
                    pass

    # Try finding price in any element containing ₹ symbol
    all_elements = soup.find_all(string=lambda t: t and '₹' in t)
    for elem_text in all_elements:
        nums = re.findall(r'[\d,]+\.?\d*', elem_text.replace(",", ""))
        for num_str in nums:
            try:
                val = float(num_str.replace(",", ""))
                if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                    return val
            except ValueError:
                continue
    
    # Last resort: look for any reasonable price pattern
    all_text = soup.get_text()
    price_matches = re.findall(r'₹\s*([\d,]+\.?\d*)', all_text)
    for match in price_matches:
        try:
            val = float(match.replace(",", ""))
            if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                return val
        except ValueError:
            continue
    
    return None

def scrape_reliance_digital_price(soup):
    """Scrape price from Reliance Digital pages - tries multiple modern selectors"""
    # Try to find all elements with price-related classes
    price_elements = soup.find_all(class_=lambda x: x and any(kw in x.lower() for kw in ['price', 'discount', 'sell', 'final', 'amount', 'digital']) if x else False)
    
    for elem in price_elements:
        text = elem.get_text().strip()
        if '₹' in text:
            nums = re.findall(r'[\d,]+\.?\d*', text.replace(",", ""))
            for num_str in nums:
                try:
                    val = float(num_str.replace(",", ""))
                    if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                        return val
                except ValueError:
                    continue
    
    # Try specific Reliance Digital selectors
    selectors = [
        "span[itemprop='price']",  # Schema price
        "div.price",  # Main price
        "[data-testid='price']",  # Test ID price
        "span.discounted-price",  # Discounted price
        "span.selling-price",  # Selling price
        "div.product-price",  # Product price
        "div.price-info",  # Price info
        "span.final-price",  # Final price
        "div[itemprop='price']",  # Schema div
        "[class*='price']",  # Any class with price
        "[class*='Price']",  # Any class with Price
        "span.RD__Price",  # Reliance Digital specific
        "div.RD__Price",  # Reliance Digital specific
        "span.Price",  # Capital P Price
        "span.plp-price",  # PLP price
        "div.plp-price",  # PLP price
    ]
    
    for selector in selectors:
        price_element = soup.select_one(selector)
        if price_element:
            text = price_element.get_text().strip()
            nums = re.findall(r'[\d,]+\.?\d*', text.replace(",", ""))
            for num_str in nums:
                try:
                    val = float(num_str.replace(",", ""))
                    if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                        return val
                except ValueError:
                    continue
    
    # Try finding price in scripts or JSON data
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        if script.string:
            price_match = re.search(r'"price"\s*:\s*([\d.]+)', script.string)
            if price_match:
                try:
                    val = float(price_match.group(1))
                    if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                        return val
                except ValueError:
                    pass
    
    # Try finding price in any element containing ₹ symbol
    all_elements = soup.find_all(text=lambda t: t and '₹' in t)
    for elem_text in all_elements:
        nums = re.findall(r'[\d,]+\.?\d*', elem_text.replace(",", ""))
        for num_str in nums:
            try:
                val = float(num_str.replace(",", ""))
                if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                    return val
            except ValueError:
                continue
    
    # Last resort: look for any reasonable price pattern
    all_text = soup.get_text()
    price_matches = re.findall(r'₹\s*([\d,]+\.?\d*)', all_text)
    for match in price_matches:
        try:
            val = float(match.replace(",", ""))
            if 50 < val < 100000:  # Reasonable price range filter (min 50 for INR)
                return val
        except ValueError:
            continue
    
    return None

def create_session():
    """Create a requests session with proper headers for scraping"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "DNT": "1",
        "Sec-CH-UA": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": "\"macOS\""
    })
    return session

# Create a global session for reuse
http_session = create_session()

@app.route('/get-price', methods=['POST'])
def get_price():
    data = request.json
    url = data.get('url')
    
    # Test mode - return mock price for testing
    if url.startswith('test://'):
        import random
        mock_price = round(random.uniform(10, 500), 2)
        return jsonify({
            "price": mock_price,
            "currency": "USD",
            "currency_symbol": "$",
            "productName": "Test Product",
            "isTestMode": True
        })

    # For Myntra, add specific headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "DNT": "1"
    }
    
    # Add Myntra-specific headers
    if 'myntra' in url.lower():
        headers.update({
            "Referer": "https://www.myntra.com/",
            "Origin": "https://www.myntra.com",
            "sec-ch-ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\""
        })

    try:
        print(f"Fetching URL: {url}")
        
        # Use timeout to prevent hanging requests
        response = requests.get(url, headers=headers, timeout=8)
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            return jsonify({
                "error": f"Failed to fetch page (Status: {response.status_code})",
                "suggestion": "The site might be blocking requests or the product is unavailable"
            }), response.status_code
        
        soup = BeautifulSoup(response.content, "html.parser")

        site, currency, currency_symbol = get_site_info(url)
        print(f"Detected site: {site}, currency: {currency}")
        
        # Extract product name
        product_name = extract_product_name(soup, site, url)
        print(f"Product name: {product_name}")

        price = None
        if site == 'amazon':
            price = scrape_amazon_price(soup, currency_symbol)
        elif site == 'flipkart':
            price = scrape_flipkart_price(soup)
        elif site == 'ebay':
            price = scrape_ebay_price(soup)
        elif site == 'myntra':
            price = scrape_myntra_price(soup)
        elif site == 'ajio':
            price = scrape_ajio_price(soup)
        elif site == 'meesho':
            price = scrape_meesho_price(soup)
        elif site == 'snapdeal':
            price = scrape_snapdeal_price(soup)
        elif site == 'tatacliq':
            price = scrape_tata_cliq_price(soup)
        elif site == 'reliancedigital':
            price = scrape_reliance_digital_price(soup)
        else:
            # Fallback to Amazon scraping for unknown sites
            price = scrape_amazon_price(soup, currency_symbol)

        if price is None:
            print("Price element not found")
            body_text = soup.get_text().lower()
            
            # Check for common blocking reasons
            if any(word in body_text for word in ['captcha', 'robot', 'verification', 'automated access', 'opfcaptcha', 'human verification']):
                return jsonify({
                    "error": f"{site.capitalize()} is blocking automated requests",
                    "suggestion": "For testing, use URL: test://product to see demo mode",
                    "site": site
                }), 403
            
            # Check for CAPTCHA page
            if 'captcha' in body_text or 'verify you are human' in body_text:
                return jsonify({
                    "error": "CAPTCHA challenge detected",
                    "suggestion": "Sites like Amazon use CAPTCHA to block bots. Try using test://product for demo mode.",
                    "site": site
                }), 403
            
            # Check if product is unavailable
            if 'currently unavailable' in body_text or 'out of stock' in body_text:
                return jsonify({
                    "error": "This product is currently unavailable",
                    "suggestion": "Try a different product or use test://product for demo"
                }), 404
            
            return jsonify({
                "error": "Could not find price",
                "suggestion": "Site structure may have changed. Try test://product for demo mode."
            }), 404

        print(f"Extracted price: {price} {currency}")
        return jsonify({
            "price": price, 
            "currency": currency, 
            "currency_symbol": currency_symbol,
            "productName": product_name,
            "site": site
        })
    except requests.exceptions.Timeout:
        print("Request timed out")
        return jsonify({
            "error": "Request timed out",
            "suggestion": "The site is taking too long to respond. Try test://product for demo mode."
        }), 408
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {str(e)}")
        return jsonify({
            "error": "Connection error",
            "suggestion": "Could not connect to the site. Check your internet connection or try test://product for demo."
        }), 502
    except Exception as e:
        print(f"Exception: {str(e)}")
        return jsonify({
            "error": str(e),
            "suggestion": "An unexpected error occurred. Try test://product for demo mode."
        }), 500

@app.route('/api/user', methods=['GET'])
def get_user():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, phone FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({
            "id": user[0], 
            "username": user[1], 
            "email": user[2],
            "phone": user[3]
        })
    return jsonify({"error": "User not found"}), 404

@app.route('/api/trackers', methods=['GET'])
def get_trackers():
    if 'user_id' not in session:
        return jsonify([]), 401
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, url, product_name, current_price, target_price, currency, currency_symbol, site, created_at FROM trackers WHERE user_id = ? ORDER BY created_at DESC", (session['user_id'],))
    trackers = cursor.fetchall()
    conn.close()
    
    result = []
    for t in trackers:
        result.append({
            "id": t[0],
            "url": t[1],
            "productName": t[2] or "Product",
            "currentPrice": t[3],
            "targetPrice": t[4],
            "currency": t[5],
            "currencySymbol": t[6],
            "site": t[7],
            "createdAt": t[8]
        })
    
    return jsonify(result)

@app.route('/api/trackers', methods=['POST'])
def create_tracker():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.json
    url = data.get('url')
    current_price = data.get('currentPrice')
    target_price = data.get('targetPrice')
    currency = data.get('currency', 'USD')
    currency_symbol = data.get('currencySymbol', '$')
    product_name = data.get('productName', 'Product')
    site = data.get('site', 'unknown')
    
    if not url or not current_price or not target_price:
        return jsonify({"error": "Missing data"}), 400
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trackers (user_id, url, product_name, current_price, target_price, currency, currency_symbol, site)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (session['user_id'], url, product_name, current_price, target_price, currency, currency_symbol, site))
    tracker_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"id": tracker_id, "message": "Tracker created"}), 201

@app.route('/api/trackers/<int:tracker_id>', methods=['PUT'])
def update_tracker(tracker_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.json
    current_price = data.get('currentPrice')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("UPDATE trackers SET current_price = ? WHERE id = ? AND user_id = ?",
                   (current_price, tracker_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Tracker updated"})

@app.route('/api/trackers/<int:tracker_id>', methods=['DELETE'])
def delete_tracker(tracker_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trackers WHERE id = ? AND user_id = ?",
                   (tracker_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Tracker deleted"})

# ==================== MESSAGING FUNCTIONS ====================

def send_telegram_alert(chat_id, product_name, original_price, current_price, currency_symbol, url):
    """Send price drop alert to Telegram"""
    if not TELEGRAM_CONFIG['enabled'] or not TELEGRAM_CONFIG['bot_token']:
        # Demo mode
        print(f"\n{'='*50}")
        print(f"📱 TELEGRAM ALERT - DEMO MODE")
        print(f"{'='*50}")
        print(f"To: Chat ID {chat_id}")
        print(f"Product: {product_name}")
        print(f"Original: {currency_symbol}{original_price}")
        print(f"Current: {currency_symbol}{current_price}")
        savings = original_price - current_price
        savings_pct = (savings / original_price) * 100 if original_price > 0 else 0
        print(f"Save: {currency_symbol}{savings:.2f} ({savings_pct:.1f}%)")
        print(f"{'='*50}\n")
        return True
    
    try:
        import requests
        savings = original_price - current_price
        savings_pct = (savings / original_price) * 100 if original_price > 0 else 0
        
        message = f"""🔔 <b>Price Drop Alert!</b>

<b>{product_name}</b>

Original: <s>{currency_symbol}{original_price:.2f}</s>
Current: {currency_symbol}{current_price:.2f}
Save: {currency_symbol}{savings:.2f} ({savings_pct:.1f}%)

<a href="{url}">View Product</a>"""
        
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['bot_token']}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        
        response = requests.post(tg_url, json=data, timeout=10)
        if response.status_code == 200:
            print(f"Telegram alert sent to {chat_id}")
            return True
        else:
            print(f"Telegram send error: {response.text}")
            return False
    except Exception as e:
        print(f"Telegram alert error: {e}")
        return False

def send_whatsapp_alert(phone, product_name, original_price, current_price, currency_symbol, url):
    """Send price drop alert via WhatsApp (Twilio)"""
    if not WHATSAPP_CONFIG['enabled'] or not WHATSAPP_CONFIG.get('twilio_account_sid'):
        # Demo mode
        print(f"\n{'='*50}")
        print(f"📱 WHATSAPP ALERT - DEMO MODE")
        print(f"{'='*50}")
        print(f"To: {phone}")
        print(f"Product: {product_name}")
        print(f"Original: {currency_symbol}{original_price}")
        print(f"Current: {currency_symbol}{current_price}")
        savings = original_price - current_price
        savings_pct = (savings / original_price) * 100 if original_price > 0 else 0
        print(f"Save: {currency_symbol}{savings:.2f} ({savings_pct:.1f}%)")
        print(f"{'='*50}\n")
        return True
    
    try:
        from twilio.rest import Client
        
        savings = original_price - current_price
        savings_pct = (savings / original_price) * 100 if original_price > 0 else 0
        
        message = f"""🔔 *AI Price Alert - Price Drop!*

*{product_name}*

Price dropped from {currency_symbol}{original_price:.2f} to {currency_symbol}{current_price:.2f}!
You save: {currency_symbol}{savings:.2f} ({savings_pct:.1f}%)

Link: {url}"""
        
        client = Client(
            WHATSAPP_CONFIG['twilio_account_sid'],
            WHATSAPP_CONFIG['twilio_auth_token']
        )
        
        twilio_message = client.messages.create(
            body=message,
            from_=f"whatsapp:{WHATSAPP_CONFIG['twilio_whatsapp_number']}",
            to=f"whatsapp:{phone}"
        )
        
        print(f"WhatsApp alert sent to {phone}: {twilio_message.sid}")
        return True
    except Exception as e:
        print(f"WhatsApp alert error: {e}")
        return False

# ==================== MESSAGING ROUTES ====================

@app.route('/api/notifications/telegram/connect', methods=['POST'])
def connect_telegram():
    """Connect user's Telegram account for notifications"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.json
    chat_id = data.get('chat_id')
    
    if not chat_id:
        return jsonify({"error": "Chat ID is required"}), 400
    
    # For demo mode, just store it
    if not TELEGRAM_CONFIG['enabled']:
        return jsonify({
            "success": "Telegram connected (Demo Mode)",
            "message": "Configure telegram_config.json to enable real notifications",
            "demo_mode": True
        }), 200
    
    # In production, user would initiate via Telegram bot
    return jsonify({
        "success": "Telegram connected",
        "bot_username": TELEGRAM_CONFIG.get('bot_username', '')
    }), 200

@app.route('/api/notifications/telegram/disconnect', methods=['POST'])
def disconnect_telegram():
    """Disconnect user's Telegram account"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    # Remove telegram_chat_id from user profile
    return jsonify({"success": "Telegram disconnected"}), 200

@app.route('/api/notifications/telegram/status', methods=['GET'])
def telegram_status():
    """Get user's Telegram connection status"""
    if 'user_id' not in session:
        return jsonify({"connected": False}), 401
    
    return jsonify({
        "connected": False,
        "bot_username": TELEGRAM_CONFIG.get('bot_username', '')
    }), 200

@app.route('/api/notifications/whatsapp/connect', methods=['POST'])
def connect_whatsapp():
    """Connect user's WhatsApp number for notifications"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.json
    phone = data.get('phone')
    
    if not phone:
        return jsonify({"error": "Phone number is required"}), 400
    
    # Validate phone format
    phone_clean = re.sub(r'[^\d+]', '', phone)
    if len(phone_clean) < 10:
        return jsonify({"error": "Invalid phone number format"}), 400
    
    # For demo mode, just acknowledge
    if not WHATSAPP_CONFIG['enabled']:
        return jsonify({
            "success": "WhatsApp connected (Demo Mode)",
            "message": "Configure whatsapp_config.json to enable real notifications",
            "demo_mode": True
        }), 200
    
    return jsonify({
        "success": "WhatsApp connected",
        "phone": phone
    }), 200

@app.route('/api/notifications/whatsapp/disconnect', methods=['POST'])
def disconnect_whatsapp():
    """Disconnect user's WhatsApp"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    return jsonify({"success": "WhatsApp disconnected"}), 200

@app.route('/api/notifications/whatsapp/status', methods=['GET'])
def whatsapp_status():
    """Get user's WhatsApp connection status"""
    if 'user_id' not in session:
        return jsonify({"connected": False}), 401
    
    return jsonify({
        "connected": False
    }), 200

@app.route('/api/notifications/test', methods=['POST'])
def test_notification():
    """Send a test notification to the user"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.json
    channel = data.get('channel')  # 'telegram', 'whatsapp', or 'all'
    
    # Demo test
    return jsonify({
        "success": True,
        "message": f"Test notification sent via {channel or 'all'}",
        "demo_mode": True
    }), 200

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=8081, debug=True)
