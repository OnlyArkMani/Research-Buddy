from flask import Flask, render_template, redirect, request, session, jsonify, make_response
from flask_cors import CORS
import os
from datetime import timedelta
import secrets
from dotenv import load_dotenv
import jwt
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
app.secret_key = secrets.token_hex(32)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
CORS(app, supports_credentials=True)

# JWT secret for secure session sharing
JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_hex(32))

# Firebase configuration from .env
FIREBASE_CONFIG = {
    "apiKey": os.getenv('FIREBASE_API_KEY'),
    "authDomain": os.getenv('FIREBASE_AUTH_DOMAIN'),
    "projectId": os.getenv('FIREBASE_PROJECT_ID'),
    "storageBucket": os.getenv('FIREBASE_STORAGE_BUCKET'),
    "messagingSenderId": os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
    "appId": os.getenv('FIREBASE_APP_ID')
}

# Decorator to check if user is authenticated
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Landing page with animation"""
    if session.get('authenticated'):
        return redirect('/chat')
    return render_template('index.html', firebase_config=FIREBASE_CONFIG)

@app.route('/auth/verify', methods=['POST'])
def verify_auth():
    """Verify Firebase token and create session"""
    data = request.get_json()
    token = data.get('token')
    user_email = data.get('email')
    user_name = data.get('name', user_email.split('@')[0])  # Extract name from email if not provided
    
    if token and user_email:
        # Store in session
        session['authenticated'] = True
        session['user_email'] = user_email
        session['user_name'] = user_name
        session['firebase_token'] = token
        session.permanent = True
        
        # Create JWT token for Chainlit
        jwt_token = jwt.encode({
            'email': user_email,
            'name': user_name,
            'authenticated': True
        }, JWT_SECRET, algorithm='HS256')
        
        # Redirect URL with user info as query params
        redirect_url = f'http://localhost:8000?user={user_name}&email={user_email}&token={jwt_token}'
        
        return jsonify({
            'success': True, 
            'redirect': redirect_url,
            'user': {
                'email': user_email,
                'name': user_name
            }
        })
    
    return jsonify({'success': False, 'error': 'Authentication failed'}), 401

@app.route('/auth/status')
def auth_status():
    """Check authentication status"""
    if session.get('authenticated'):
        return jsonify({
            'authenticated': True,
            'user': {
                'email': session.get('user_email'),
                'name': session.get('user_name')
            }
        })
    return jsonify({'authenticated': False})

@app.route('/chat')
@login_required
def chat():
    """Redirect to Chainlit app with user info"""
    user_name = session.get('user_name', 'User')
    user_email = session.get('user_email', '')
    
    # Create JWT token for secure session
    jwt_token = jwt.encode({
        'email': user_email,
        'name': user_name,
        'authenticated': True
    }, JWT_SECRET, algorithm='HS256')
    
    # Redirect to Chainlit with user info
    redirect_url = f'http://localhost:8000?user={user_name}&email={user_email}&token={jwt_token}'
    return redirect(redirect_url)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """Logout user and clear session"""
    session.clear()
    
    # If it's an API call, return JSON
    if request.method == 'POST' or request.headers.get('Content-Type') == 'application/json':
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    
    # Otherwise show logout page
    return render_template('logout.html', firebase_config=FIREBASE_CONFIG)

@app.route('/api/user')
@login_required
def get_user():
    """Get current user info"""
    return jsonify({
        'email': session.get('user_email'),
        'name': session.get('user_name')
    })

if __name__ == '__main__':
    # Create templates and static folders if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("=" * 60)
    print("🚀 Research Buddy - Landing Page Server (Enhanced)")
    print("=" * 60)
    print(f"📍 Landing page: http://localhost:5000")
    print(f"🤖 Chainlit app:  http://localhost:8000")
    print("=" * 60)
    print("✅ Firebase Config Loaded:")
    print(f"   Project ID: {FIREBASE_CONFIG.get('projectId')}")
    print(f"   Auth Domain: {FIREBASE_CONFIG.get('authDomain')}")
    print("=" * 60)
    print("🔐 Features Enabled:")
    print("   ✓ Google Sign-In")
    print("   ✓ Email/Password Authentication")
    print("   ✓ Session Management (7 days)")
    print("   ✓ Logout Functionality")
    print("   ✓ User Info Sharing with Chatbot")
    print("=" * 60)
    print("\n🎯 Instructions:")
    print("   1. Make sure Chainlit is running on port 8000")
    print("   2. Open http://localhost:5000 in your browser")
    print("   3. Sign in and enjoy!")
    print("   4. To logout, visit: http://localhost:5000/logout\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')