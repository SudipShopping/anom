# app.py - Flask Backend
from flask import Flask, render_template, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import random
import string
import time
import os
import base64

app = Flask(__name__)

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def generate_credentials():
    nickname = f"user{generate_random_string(6)}"
    email = f"{generate_random_string(10)}@gmail.com"
    password = generate_random_string(12)
    return nickname, email, password

def register_single_account(ref_link, captcha_answer):
    """Register a single account"""
    try:
        session = requests.Session()
        base_url = "https://amingo.top"
        
        # Extract ref ID
        ref_id = ""
        if '?ref=' in ref_link:
            ref_id = ref_link.split('?ref=')[-1]
        elif '&ref=' in ref_link:
            ref_id = ref_link.split('&ref=')[-1]
        
        logs = []
        
        # STEP 1: Visit referral link to set cookie
        logs.append("📡 Visiting referral link...")
        if ref_id:
            initial_ref_url = f"{base_url}/?ref={ref_id}"
            initial_response = session.get(initial_ref_url)
            
            if initial_response.status_code != 200:
                logs.append(f"❌ Failed to load ref link")
                return {'success': False, 'logs': logs}
            
            logs.append(f"✅ Referral cookie set (ref: {ref_id})")
            time.sleep(1)
        
        # STEP 2: Go to registration page
        reg_url = f"{base_url}/?pages=reg"
        logs.append("📡 Loading registration page...")
        response = session.get(reg_url)
        
        if response.status_code != 200:
            logs.append("❌ Failed to load registration page")
            return {'success': False, 'logs': logs}
        
        # Generate credentials
        nickname, email, password = generate_credentials()
        logs.append(f"📝 Generated: {nickname}")
        
        # Prepare registration data
        registration_data = {
            'login': nickname,
            'email': email,
            'pass': password,
            'cap': captcha_answer
        }
        
        # Submit registration
        submit_url = f"{base_url}/?pages=reg"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': reg_url,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        logs.append("🚀 Submitting registration...")
        reg_response = session.post(submit_url, data=registration_data, headers=headers, allow_redirects=True)
        
        # Check success
        if reg_response.status_code == 200:
            if ('?pages=game' in reg_response.url or 
                'success' in reg_response.text.lower() or 
                'welcome' in reg_response.text.lower()):
                
                logs.append(f"✅ Account created successfully!")
                logs.append(f"👤 Username: {nickname}")
                logs.append(f"📧 Email: {email}")
                logs.append(f"🔑 Password: {password}")
                
                # Save to file
                with open('accounts.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{nickname}|{email}|{password}\n")
                
                return {
                    'success': True, 
                    'logs': logs,
                    'account': {
                        'nickname': nickname,
                        'email': email,
                        'password': password
                    }
                }
        
        logs.append("❌ Registration failed - please try again")
        return {'success': False, 'logs': logs}
            
    except Exception as e:
        return {'success': False, 'logs': [f"❌ Error: {str(e)}"]}

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
    
    result = register_single_account(ref_link, captcha)
    return jsonify(result)

@app.route('/get_captcha')
def get_captcha():
    """Fetch captcha image from registration page"""
    try:
        ref_link = request.args.get('ref_link', '')
        if not ref_link:
            return jsonify({'error': 'No ref link provided'}), 400
        
        base_url = "https://amingo.top"
        
        # Create session and visit ref link first
        session = requests.Session()
        if '?ref=' in ref_link:
            session.get(ref_link)
            time.sleep(0.5)
        
        # Go to registration page
        reg_url = f"{base_url}/?pages=reg"
        response = session.get(reg_url)
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to load registration page'}), 400
        
        # Parse HTML to find captcha
        soup = BeautifulSoup(response.text, 'html.parser')
        captcha_img = soup.find('img', {'id': 'cap_img'})
        
        if captcha_img:
            img_src = captcha_img.get('src', '')
            
            if img_src and not img_src.startswith('http'):
                img_src = base_url + ('/' if not img_src.startswith('/') else '') + img_src
            
            if img_src:
                img_response = session.get(img_src)
                if img_response.status_code == 200:
                    img_base64 = base64.b64encode(img_response.content).decode('utf-8')
                    return jsonify({
                        'success': True,
                        'image': f"data:image/png;base64,{img_base64}"
                    })
        
        return jsonify({'error': 'Captcha not found'}), 404
        
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
