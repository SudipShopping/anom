# app.py - Flask Backend with Playwright
from flask import Flask, render_template, request, jsonify, send_file
from playwright.sync_api import sync_playwright
import random
import string
import time
import os
import base64
import threading

app = Flask(__name__)

# Global playwright instance
playwright_instance = None
browser = None

def init_browser():
    """Initialize Playwright browser"""
    global playwright_instance, browser
    if browser is None:
        playwright_instance = sync_playwright().start()
        browser = playwright_instance.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
    return browser

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def generate_credentials():
    nickname = f"user{generate_random_string(6)}"
    email = f"{generate_random_string(10)}@gmail.com"
    password = generate_random_string(12)
    return nickname, email, password

def register_account_with_playwright(ref_link, captcha_answer):
    """Register account using Playwright browser automation"""
    try:
        logs = []
        browser = init_browser()
        
        # Create new page
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        # Step 1: Visit referral link
        logs.append(f"📡 Visiting referral link: {ref_link}")
        page.goto(ref_link, wait_until='networkidle', timeout=30000)
        time.sleep(2)
        logs.append("✅ Referral link visited - cookie set")
        
        # Step 2: Go to registration page
        logs.append("📡 Navigating to registration page...")
        page.goto('https://amingo.top/?pages=reg', wait_until='networkidle', timeout=30000)
        time.sleep(1)
        logs.append("✅ Registration page loaded")
        
        # Generate credentials
        nickname, email, password = generate_credentials()
        logs.append(f"📝 Generated credentials: {nickname}")
        
        # Step 3: Fill registration form
        logs.append("✍️ Filling registration form...")
        
        # Fill nickname
        page.fill('input[name="login"]', nickname)
        time.sleep(0.5)
        
        # Fill email
        page.fill('input[name="email"]', email)
        time.sleep(0.5)
        
        # Fill password
        page.fill('input[name="pass"]', password)
        time.sleep(0.5)
        
        # Fill captcha
        page.fill('input[name="cap"]', captcha_answer)
        time.sleep(0.5)
        
        logs.append("✅ Form filled successfully")
        
        # Step 4: Submit form
        logs.append("🚀 Submitting registration...")
        page.click('button[name="sub_reg"]')
        
        # Wait for navigation
        try:
            page.wait_for_load_state('networkidle', timeout=10000)
            time.sleep(2)
        except:
            pass
        
        # Check if registration successful
        current_url = page.url
        page_content = page.content()
        
        if '?pages=game' in current_url or 'success' in page_content.lower():
            logs.append("✅ Account created successfully!")
            logs.append(f"👤 Username: {nickname}")
            logs.append(f"📧 Email: {email}")
            logs.append(f"🔑 Password: {password}")
            
            # Save to file
            with open('accounts.txt', 'a', encoding='utf-8') as f:
                f.write(f"{nickname}|{email}|{password}\n")
            
            context.close()
            
            return {
                'success': True,
                'logs': logs,
                'account': {
                    'nickname': nickname,
                    'email': email,
                    'password': password
                }
            }
        else:
            logs.append("❌ Registration failed - please check captcha")
            context.close()
            return {'success': False, 'logs': logs}
        
    except Exception as e:
        logs.append(f"❌ Error: {str(e)}")
        try:
            context.close()
        except:
            pass
        return {'success': False, 'logs': logs}

def get_captcha_with_playwright(ref_link):
    """Get captcha image using Playwright"""
    try:
        browser = init_browser()
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        # Visit ref link first
        page.goto(ref_link, wait_until='networkidle', timeout=30000)
        time.sleep(1)
        
        # Go to registration page
        page.goto('https://amingo.top/?pages=reg', wait_until='networkidle', timeout=30000)
        time.sleep(1)
        
        # Find captcha image
        captcha_element = page.query_selector('#cap_img')
        
        if captcha_element:
            # Take screenshot of captcha
            captcha_screenshot = captcha_element.screenshot()
            context.close()
            
            # Convert to base64
            captcha_base64 = base64.b64encode(captcha_screenshot).decode('utf-8')
            return {
                'success': True,
                'image': f"data:image/png;base64,{captcha_base64}"
            }
        else:
            context.close()
            return {'success': False, 'error': 'Captcha not found'}
            
    except Exception as e:
        try:
            context.close()
        except:
            pass
        return {'success': False, 'error': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    """Register a single account"""
    data = request.json
    
    ref_link = data.get('refLink', '')
    captcha = data.get('captcha', '')
    
    if not ref_link or not captcha:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    # Validate ref link
    if 'amingo.top' not in ref_link:
        return jsonify({'success': False, 'error': 'Invalid amingo.top link'}), 400
    
    result = register_account_with_playwright(ref_link, captcha)
    return jsonify(result)

@app.route('/get_captcha')
def get_captcha():
    """Fetch captcha image using Playwright"""
    try:
        ref_link = request.args.get('ref_link', '')
        if not ref_link:
            return jsonify({'error': 'No ref link provided'}), 400
        
        # Validate ref link
        if 'amingo.top' not in ref_link:
            return jsonify({'error': 'Invalid amingo.top link'}), 400
        
        result = get_captcha_with_playwright(ref_link)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download')
def download_accounts():
    if os.path.exists('accounts.txt'):
        return send_file('accounts.txt', as_attachment=True)
    return "No accounts file found", 404

if __name__ == '__main__':
    # Initialize browser on startup
    init_browser()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
