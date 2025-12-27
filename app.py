# app.py - Flask Backend with Playwright + Gemini Vision for gamety.org
from flask import Flask, render_template, request, jsonify, send_file
from playwright.async_api import async_playwright
import random
import string
import os
import base64
import asyncio
import re
import requests

app = Flask(__name__)

# Gemini API configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDzJbv97PW8mSa1ThJ7bfCq6-eeWlGkq2w')
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def generate_credentials():
    nickname = f"user{generate_random_string(6)}"
    email = f"{generate_random_string(10)}@gmail.com"
    password = generate_random_string(12)
    return nickname, email, password

def solve_captcha_with_gemini(image_bytes):
    """Solve numeric captcha using Gemini Vision API"""
    try:
        # Convert image to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Prepare request for Gemini
        payload = {
            "contents": [{
                "parts": [
                    {
                        "text": "This is a captcha image containing only 4 digits. Extract ONLY the 4 digits you see. Respond with ONLY the 4 digits, nothing else. No explanation, no other text."
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": image_base64
                        }
                    }
                ]
            }]
        }
        
        # Call Gemini API
        response = requests.post(GEMINI_API_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            text = result['candidates'][0]['content']['parts'][0]['text']
            
            # Extract only digits
            digits = re.sub(r'[^0-9]', '', text)
            
            return digits[:4] if len(digits) >= 4 else digits
        else:
            print(f"Gemini API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Gemini Error: {e}")
        return None

async def register_account_with_playwright(ref_link, captcha_answer=None):
    """Register account on gamety.org using Playwright with auto Gemini captcha solving"""
    logs = []
    
    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            
            # Create context and page
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # Step 1: Visit referral link
            logs.append(f"📡 Visiting referral link: {ref_link}")
            await page.goto(ref_link, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)
            logs.append("✅ Referral link visited - cookie set")
            
            # Step 2: Go to registration page
            logs.append("📡 Navigating to registration page...")
            await page.goto('https://gamety.org/?pages=reg', wait_until='networkidle', timeout=30000)
            await asyncio.sleep(1)
            logs.append("✅ Registration page loaded")
            
            # Step 3: Solve captcha automatically if not provided
            if not captcha_answer:
                logs.append("🤖 Auto-solving captcha with Gemini AI...")
                
                # Get captcha image
                captcha_element = await page.query_selector('#cap_img')
                if captcha_element:
                    captcha_screenshot = await captcha_element.screenshot()
                    captcha_text = solve_captcha_with_gemini(captcha_screenshot)
                    
                    if captcha_text and len(captcha_text) >= 4:
                        captcha_answer = captcha_text[:4]
                        logs.append(f"✅ Gemini AI solved captcha: {captcha_answer}")
                    else:
                        logs.append("❌ Gemini AI failed to solve captcha")
                        await browser.close()
                        return {'success': False, 'logs': logs, 'error': 'GEMINI_FAILED'}
                else:
                    logs.append("❌ Captcha element not found")
                    await browser.close()
                    return {'success': False, 'logs': logs}
            else:
                logs.append(f"✅ Using provided captcha: {captcha_answer}")
            
            # Generate credentials
            nickname, email, password = generate_credentials()
            logs.append(f"📝 Generated credentials: {nickname}")
            
            # Step 4: Fill registration form
            logs.append("✍️ Filling registration form...")
            
            # Fill login (username)
            await page.fill('input[name="login"]', nickname)
            await asyncio.sleep(0.5)
            
            # Fill email
            await page.fill('input[name="email"]', email)
            await asyncio.sleep(0.5)
            
            # Fill password
            await page.fill('input[name="pass"]', password)
            await asyncio.sleep(0.5)
            
            # Fill captcha
            await page.fill('input[name="cap"]', captcha_answer)
            await asyncio.sleep(0.5)
            
            logs.append("✅ Form filled successfully")
            
            # Step 5: Submit form
            logs.append("🚀 Submitting registration...")
            await page.click('button[name="sub_reg"]')
            
            # Wait for navigation
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
                await asyncio.sleep(2)
            except:
                pass
            
            # Check if registration successful
            current_url = page.url
            
            if '?pages=games' not in current_url:
                logs.append("❌ Registration failed - wrong captcha or error")
                await browser.close()
                return {'success': False, 'logs': logs}
            
            logs.append("✅ Account created successfully!")
            
            # Step 6: Buy person (Detector)
            logs.append("🛒 Navigating to person purchase...")
            await page.goto('https://gamety.org/?pages=games', wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)
            
            # Find and click buy button for Detector (p11)
            try:
                # Look for the form with p=p11
                buy_button = await page.query_selector('button[name="person_buy"]')
                
                if buy_button:
                    logs.append("💰 Purchasing Detector (500 coins)...")
                    await buy_button.click()
                    await asyncio.sleep(3)
                    
                    logs.append("✅ Person purchased successfully!")
                else:
                    logs.append("⚠️ Person buy button not found")
            except Exception as e:
                logs.append(f"⚠️ Person purchase failed: {str(e)}")
            
            await browser.close()
            
            logs.append(f"👤 Username: {nickname}")
            logs.append(f"📧 Email: {email}")
            logs.append(f"🔑 Password: {password}")
            
            # Save to file
            with open('accounts.txt', 'a', encoding='utf-8') as f:
                f.write(f"{nickname}|{email}|{password}|PERSON_BOUGHT\n")
            
            return {
                'success': True,
                'logs': logs,
                'account': {
                    'nickname': nickname,
                    'email': email,
                    'password': password
                }
            }
        
    except Exception as e:
        logs.append(f"❌ Error: {str(e)}")
        return {'success': False, 'logs': logs}

async def get_captcha_with_playwright(ref_link):
    """Get captcha image from gamety.org using Playwright"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # Visit ref link first
            await page.goto(ref_link, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(1)
            
            # Go to registration page
            await page.goto('https://gamety.org/?pages=reg', wait_until='networkidle', timeout=30000)
            await asyncio.sleep(1)
            
            # Find captcha image
            captcha_element = await page.query_selector('#cap_img')
            
            if captcha_element:
                # Take screenshot of captcha
                captcha_screenshot = await captcha_element.screenshot()
                await browser.close()
                
                # Convert to base64
                captcha_base64 = base64.b64encode(captcha_screenshot).decode('utf-8')
                return {
                    'success': True,
                    'image': f"data:image/png;base64,{captcha_base64}"
                }
            else:
                await browser.close()
                return {'success': False, 'error': 'Captcha not found'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    """Register a single account with optional manual captcha"""
    data = request.json
    
    ref_link = data.get('refLink', '')
    captcha = data.get('captcha', '')  # Optional - Gemini will solve if empty
    
    if not ref_link:
        return jsonify({'success': False, 'error': 'Missing ref link'}), 400
    
    # Validate ref link
    if 'gamety.org' not in ref_link:
        return jsonify({'success': False, 'error': 'Invalid gamety.org link'}), 400
    
    # Run async function (with or without manual captcha)
    result = asyncio.run(register_account_with_playwright(ref_link, captcha if captcha else None))
    return jsonify(result)

@app.route('/get_captcha')
def get_captcha():
    """Fetch captcha image using Playwright"""
    try:
        ref_link = request.args.get('ref_link', '')
        if not ref_link:
            return jsonify({'error': 'No ref link provided'}), 400
        
        # Validate ref link
        if 'gamety.org' not in ref_link:
            return jsonify({'error': 'Invalid gamety.org link'}), 400
        
        # Run async function
        result = asyncio.run(get_captcha_with_playwright(ref_link))
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download')
def download_accounts():
    if os.path.exists('accounts.txt'):
        return send_file('accounts.txt', as_attachment=True)
    return "No accounts file found", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
