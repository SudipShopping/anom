# app.py - Flask Backend
from flask import Flask, render_template, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import random
import string
import time
import threading
import os
import re
import base64

app = Flask(__name__)

# Store registration status
registration_status = {
    'running': False,
    'current': 0,
    'total': 0,
    'success': 0,
    'failed': 0,
    'logs': []
}

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def generate_credentials():
    nickname = f"user{generate_random_string(6)}"
    email = f"{generate_random_string(10)}@gmail.com"
    password = generate_random_string(12)
    return nickname, email, password

def add_log(message):
    registration_status['logs'].append(message)
    print(message)

def login_account(session, base_url, nickname, password):
    """Login to account after registration"""
    try:
        add_log(f"🔐 Logging in as {nickname}...")
        
        # Go to home page first to get session
        home_response = session.get(base_url)
        
        # Parse to get login key
        soup = BeautifulSoup(home_response.text, 'html.parser')
        login_form = soup.find('form', {'action': '?pages=aut'})
        
        if not login_form:
            add_log(f"❌ Login form not found")
            return False
        
        key_input = login_form.find('input', {'name': 'key'})
        if not key_input:
            add_log(f"❌ Login key not found")
            return False
        
        # Prepare login data
        login_data = {
            'email': nickname,
            'pass': password,
            'key': key_input.get('value'),
            'sub_aut': ''
        }
        
        # Submit login
        login_url = f"{base_url}/?pages=aut"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': base_url,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        login_response = session.post(login_url, data=login_data, headers=headers, allow_redirects=True)
        
        if login_response.status_code == 200 and '?pages=game' in login_response.url:
            add_log(f"✅ Login successful!")
            return True
        else:
            add_log(f"❌ Login failed")
            return False
            
    except Exception as e:
        add_log(f"❌ Login error: {str(e)}")
        return False

def buy_person(session, base_url):
    """Buy the first person after registration"""
    try:
        add_log(f"🛒 Navigating to person page...")
        
        # Go to person page
        person_url = f"{base_url}/?pages=person"
        person_response = session.get(person_url)
        
        if person_response.status_code != 200:
            add_log(f"❌ Failed to load person page")
            return False
        
        # Parse page to get form data
        soup = BeautifulSoup(person_response.text, 'html.parser')
        
        # Find the buy form
        buy_form = soup.find('form', {'method': 'POST'})
        
        if not buy_form:
            add_log(f"❌ Buy form not found")
            return False
        
        # Extract hidden fields
        type_input = buy_form.find('input', {'name': 'type'})
        key_input = buy_form.find('input', {'name': 'key'})
        
        if not type_input or not key_input:
            add_log(f"❌ Required form fields not found")
            return False
        
        # Prepare buy data
        buy_data = {
            'type': type_input.get('value'),
            'key': key_input.get('value'),
            'sub_person': 'true'
        }
        
        add_log(f"💰 Purchasing person (slot_15)...")
        
        # Submit buy request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': person_url,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        buy_response = session.post(person_url, data=buy_data, headers=headers, allow_redirects=True)
        
        # Check success
        if buy_response.status_code == 200:
            add_log(f"✅ Person purchased successfully!")
            return True
        else:
            add_log(f"❌ Purchase failed")
            return False
            
    except Exception as e:
        add_log(f"❌ Error during purchase: {str(e)}")
        return False

def register_single_account(ref_link, captcha_answer):
    try:
        session = requests.Session()
        base_url = "https://amingo.top"
        
        # Extract ref ID
        ref_id = ""
        if '?ref=' in ref_link:
            ref_id = ref_link.split('?ref=')[-1]
        elif '&ref=' in ref_link:
            ref_id = ref_link.split('&ref=')[-1]
        
        # Build registration URL
        reg_url = f"{base_url}/?pages=reg"
        if ref_id:
            reg_url = f"{base_url}/?pages=reg&ref={ref_id}"
        
        # Load registration page to get cookies/session
        add_log(f"📡 Loading registration page...")
        response = session.get(reg_url)
        
        if response.status_code != 200:
            add_log(f"❌ Failed to load page. Status: {response.status_code}")
            return False
        
        # Generate credentials
        nickname, email, password = generate_credentials()
        add_log(f"📝 Generated: {nickname} | {email}")
        
        # Prepare registration data
        registration_data = {
            'login': nickname,
            'email': email,
            'pass': password,
            'cap': captcha_answer
        }
        
        # If ref exists, add it
        if ref_id:
            registration_data['ref'] = ref_id
        
        # Submit registration
        submit_url = f"{base_url}/?pages=reg"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': reg_url,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        add_log(f"🚀 Submitting registration...")
        reg_response = session.post(submit_url, data=registration_data, headers=headers, allow_redirects=True)
        
        # Check if registration successful
        registration_success = False
        if reg_response.status_code == 200:
            if ('?pages=game' in reg_response.url or 
                'success' in reg_response.text.lower() or 
                'welcome' in reg_response.text.lower()):
                add_log(f"✅ Account created: {nickname}")
                registration_success = True
            else:
                # Try to login manually
                add_log(f"⚠️ Registration unclear, attempting login...")
                if login_account(session, base_url, nickname, password):
                    registration_success = True
        
        if not registration_success:
            add_log(f"❌ Registration failed for {nickname}")
            return False
        
        # Wait a bit before buying
        time.sleep(2)
        
        # Now buy the person
        if buy_person(session, base_url):
            add_log(f"✅ Complete! Account ready with person purchased")
            
            # Save to file
            with open('accounts.txt', 'a', encoding='utf-8') as f:
                f.write(f"{nickname}|{email}|{password}|PERSON_BOUGHT\n")
            
            return True
        else:
            add_log(f"⚠️ Account created but person purchase failed")
            
            # Save anyway but mark as incomplete
            with open('accounts.txt', 'a', encoding='utf-8') as f:
                f.write(f"{nickname}|{email}|{password}|NO_PERSON\n")
            
            return False
            
    except Exception as e:
        add_log(f"❌ Error: {str(e)}")
        return False

def registration_worker(ref_link, count, delay, captcha_answer):
    global registration_status
    
    registration_status['running'] = True
    registration_status['total'] = count
    registration_status['current'] = 0
    registration_status['success'] = 0
    registration_status['failed'] = 0
    registration_status['logs'] = []
    
    add_log(f"🎯 Starting registration for {count} accounts...")
    
    for i in range(1, count + 1):
        registration_status['current'] = i
        add_log(f"\n[{i}/{count}] Creating account #{i}")
        
        if register_single_account(ref_link, captcha_answer):
            registration_status['success'] += 1
        else:
            registration_status['failed'] += 1
        
        if i < count:
            add_log(f"⏳ Waiting {delay} seconds...")
            time.sleep(delay)
    
    add_log(f"\n✅ Complete! Success: {registration_status['success']}, Failed: {registration_status['failed']}")
    registration_status['running'] = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_registration():
    data = request.json
    
    ref_link = data.get('refLink', '')
    count = int(data.get('count', 1))
    delay = int(data.get('delay', 3))
    captcha = data.get('captcha', '')
    
    if not ref_link or not captcha:
        return jsonify({'error': 'Missing required fields'}), 400
    
    if registration_status['running']:
        return jsonify({'error': 'Registration already running'}), 400
    
    # Start in background thread
    thread = threading.Thread(
        target=registration_worker,
        args=(ref_link, count, delay, captcha)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Registration started'})

@app.route('/get_captcha')
def get_captcha():
    """Fetch captcha image from registration page"""
    try:
        ref_link = request.args.get('ref_link', '')
        if not ref_link:
            return jsonify({'error': 'No ref link provided'}), 400
        
        # Build registration URL
        base_url = "https://amingo.top"
        reg_url = f"{base_url}/?pages=reg"
        if '?ref=' in ref_link:
            ref_id = ref_link.split('?ref=')[-1]
            reg_url = f"{base_url}/?pages=reg&ref={ref_id}"
        
        session = requests.Session()
        response = session.get(reg_url)
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to load registration page'}), 400
        
        # Parse HTML to find captcha image
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find captcha image with id="cap_img"
        captcha_img = soup.find('img', {'id': 'cap_img'})
        
        if captcha_img:
            img_src = captcha_img.get('src', '')
            
            # Handle relative URLs (load/cap/image.php?id=...)
            if img_src and not img_src.startswith('http'):
                img_src = base_url + ('/' if not img_src.startswith('/') else '') + img_src
            
            if img_src:
                # Download captcha image
                img_response = session.get(img_src)
                if img_response.status_code == 200:
                    # Convert to base64
                    img_base64 = base64.b64encode(img_response.content).decode('utf-8')
                    return jsonify({
                        'success': True,
                        'image': f"data:image/png;base64,{img_base64}"
                    })
        
        return jsonify({'error': 'Captcha not found in page'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def get_status():
    return jsonify(registration_status)

@app.route('/download')
def download_accounts():
    if os.path.exists('accounts.txt'):
        return send_file('accounts.txt', as_attachment=True)
    return "No accounts file found", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
