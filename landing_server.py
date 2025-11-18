from flask import Flask, render_template, redirect, request, session, jsonify
from flask_cors import CORS
import os
from datetime import timedelta
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
app.secret_key = secrets.token_hex(32)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
CORS(app)

# Firebase configuration from .env
FIREBASE_CONFIG = {
    "apiKey": os.getenv('FIREBASE_API_KEY'),
    "authDomain": os.getenv('FIREBASE_AUTH_DOMAIN'),
    "projectId": os.getenv('FIREBASE_PROJECT_ID'),
    "storageBucket": os.getenv('FIREBASE_STORAGE_BUCKET'),
    "messagingSenderId": os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
    "appId": os.getenv('FIREBASE_APP_ID')
}

@app.route('/')
def index():
    """Landing page with animation"""
    if session.get('authenticated'):
        return redirect('/chat')
    return render_template('index.html', firebase_config=FIREBASE_CONFIG)

@app.route('/auth/verify', methods=['POST'])
def verify_auth():
    """Verify Firebase token"""
    data = request.get_json()
    token = data.get('token')
    user_email = data.get('email')
    
    # Here you would verify the Firebase token
    # For now, we'll trust the client-side authentication
    if token and user_email:
        session['authenticated'] = True
        session['user_email'] = user_email
        session.permanent = True
        return jsonify({'success': True, 'redirect': 'http://localhost:8000'})
    
    return jsonify({'success': False, 'error': 'Authentication failed'}), 401

@app.route('/chat')
def chat():
    """Redirect to Chainlit app"""
    if not session.get('authenticated'):
        return redirect('/')
    # Redirect to Chainlit running on port 8000
    return redirect('http://localhost:8000')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    # Create templates and static folders if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("=" * 60)
    print("🚀 Research Buddy - Landing Page Server")
    print("=" * 60)
    print(f"📍 Landing page: http://localhost:5000")
    print(f"🤖 Chainlit app:  http://localhost:8000")
    print("=" * 60)
    print("✅ Firebase Config Loaded:")
    print(f"   Project ID: {FIREBASE_CONFIG.get('projectId')}")
    print(f"   Auth Domain: {FIREBASE_CONFIG.get('authDomain')}")
    print("=" * 60)
    print("\n🎯 Instructions:")
    print("   1. Make sure Chainlit is running on port 8000")
    print("   2. Open http://localhost:5000 in your browser")
    print("   3. Enjoy your animated authentication experience!\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')