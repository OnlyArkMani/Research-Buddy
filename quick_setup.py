"""
Quick setup script to create all required files for Research Buddy landing page
Run this in your ResearchBuddy folder: python quick_setup.py
"""

import os

# Create folder structure
folders = [
    'templates',
    'static',
    'static/css',
    'static/js'
]

print("🚀 Setting up Research Buddy Landing Page...")
print("=" * 60)

for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f"✅ Created folder: {folder}")

# Create index.html
index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Buddy - AI-Powered Research Assistant</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <!-- Animated Background -->
    <div class="background-animation">
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
    </div>

    <!-- Main Container -->
    <div class="container" id="mainContainer">
        
        <!-- Logo Animation Section -->
        <div class="logo-section" id="logoSection">
            <div class="logo-container">
                <svg class="logo-svg" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
                    <!-- Magnifying Glass Circle -->
                    <circle class="logo-circle" cx="80" cy="80" r="50" stroke-width="8" fill="none"/>
                    
                    <!-- Brain/Network inside circle -->
                    <g class="logo-brain" transform="translate(80, 80)">
                        <!-- Center R -->
                        <text x="0" y="8" font-size="40" font-weight="bold" text-anchor="middle" fill="#E85D75">R</text>
                        
                        <!-- Connection lines -->
                        <line x1="0" y1="-15" x2="0" y2="-30" stroke-width="3" class="brain-line"/>
                        <line x1="12" y1="-10" x2="24" y2="-20" stroke-width="3" class="brain-line"/>
                        <line x1="15" y1="0" x2="30" y2="0" stroke-width="3" class="brain-line"/>
                        <line x1="12" y1="10" x2="24" y2="20" stroke-width="3" class="brain-line"/>
                        <line x1="0" y1="15" x2="0" y2="30" stroke-width="3" class="brain-line"/>
                        <line x1="-12" y1="10" x2="-24" y2="20" stroke-width="3" class="brain-line"/>
                        <line x1="-15" y1="0" x2="-30" y2="0" stroke-width="3" class="brain-line"/>
                        <line x1="-12" y1="-10" x2="-24" y2="-20" stroke-width="3" class="brain-line"/>
                        
                        <!-- Connection nodes -->
                        <circle cx="0" cy="-30" r="4" class="brain-node"/>
                        <circle cx="24" cy="-20" r="4" class="brain-node"/>
                        <circle cx="30" cy="0" r="4" class="brain-node"/>
                        <circle cx="24" cy="20" r="4" class="brain-node"/>
                        <circle cx="0" cy="30" r="4" class="brain-node"/>
                        <circle cx="-24" cy="20" r="4" class="brain-node"/>
                        <circle cx="-30" cy="0" r="4" class="brain-node"/>
                        <circle cx="-24" cy="-20" r="4" class="brain-node"/>
                    </g>
                    
                    <!-- Magnifying Glass Handle -->
                    <line class="logo-handle" x1="115" y1="115" x2="145" y2="145" stroke-width="8" stroke-linecap="round"/>
                </svg>
                
                <h1 class="app-title">Research Buddy</h1>
                <p class="app-subtitle">AI-Powered Research Assistant</p>
            </div>
        </div>

        <!-- Authentication Section -->
        <div class="auth-section" id="authSection" style="display: none;">
            <div class="auth-container">
                <div class="auth-card">
                    <h2 class="auth-title">Welcome Back</h2>
                    <p class="auth-description">Sign in to continue your research journey</p>
                    
                    <!-- Loading State -->
                    <div class="loading-state" id="loadingState" style="display: none;">
                        <div class="spinner"></div>
                        <p>Authenticating...</p>
                    </div>

                    <!-- Auth Buttons -->
                    <div class="auth-buttons" id="authButtons">
                        <button class="auth-btn google-btn" id="googleSignIn">
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M19.8055 10.2292C19.8055 9.55207 19.7501 8.86929 19.6319 8.20374H10.2V12.0492H15.6014C15.3775 13.2911 14.6573 14.3898 13.6025 15.0879V17.5866H16.825C18.7171 15.8449 19.8055 13.2728 19.8055 10.2292Z" fill="#4285F4"/>
                                <path d="M10.2 20C12.9567 20 15.2713 19.1045 16.8286 17.5866L13.6061 15.0879C12.7096 15.6979 11.5522 16.0433 10.2036 16.0433C7.5442 16.0433 5.29016 14.2834 4.50008 11.9167H1.1781V14.4927C2.76878 17.8521 6.31529 20 10.2 20Z" fill="#34A853"/>
                                <path d="M4.49647 11.9167C4.06472 10.6748 4.06472 9.32924 4.49647 8.08734V5.51135H1.17811C-0.392703 8.83699 -0.392703 12.7669 1.17811 16.0925L4.49647 13.5165V11.9167Z" fill="#FBBC04"/>
                                <path d="M10.2 3.95671C11.6234 3.93524 13.0029 4.47269 14.0396 5.45614L16.8937 2.60203C15.1862 0.990678 12.7348 0.100088 10.2 0.130018C6.31529 0.130018 2.76878 2.27791 1.1781 5.51138L4.49647 8.08738C5.28294 5.71695 7.54059 3.95671 10.2 3.95671Z" fill="#EA4335"/>
                            </svg>
                            Continue with Google
                        </button>
                        
                        <button class="auth-btn email-btn" id="emailSignIn">
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M3.33333 3.33334H16.6667C17.5833 3.33334 18.3333 4.08334 18.3333 5.00001V15C18.3333 15.9167 17.5833 16.6667 16.6667 16.6667H3.33333C2.41667 16.6667 1.66667 15.9167 1.66667 15V5.00001C1.66667 4.08334 2.41667 3.33334 3.33333 3.33334Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                <path d="M18.3333 5L10 10.8333L1.66667 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            Continue with Email
                        </button>
                    </div>

                    <!-- Email/Password Form (initially hidden) -->
                    <div class="email-form" id="emailForm" style="display: none;">
                        <div class="form-group">
                            <label for="email">Email</label>
                            <input type="email" id="email" placeholder="your@email.com" required>
                        </div>
                        <div class="form-group">
                            <label for="password">Password</label>
                            <input type="password" id="password" placeholder="••••••••" required>
                        </div>
                        <div class="form-actions">
                            <button class="primary-btn" id="signInBtn">Sign In</button>
                            <button class="secondary-btn" id="signUpBtn">Sign Up</button>
                        </div>
                        <button class="back-btn" id="backBtn">← Back</button>
                    </div>

                    <div class="auth-footer">
                        <p>By continuing, you agree to our Terms of Service and Privacy Policy</p>
                    </div>
                </div>
            </div>
        </div>

    </div>

    <!-- Firebase SDK -->
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-auth-compat.js"></script>
    
    <!-- Firebase Config -->
    <script>
        const firebaseConfig = {{ firebase_config | tojson }};
        firebase.initializeApp(firebaseConfig);
    </script>
    
    <!-- Main Script -->
    <script src="{{ url_for('static', filename='js/auth.js') }}"></script>
</body>
</html>'''

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(index_html)
print("✅ Created file: templates/index.html")

print("\n" + "=" * 60)
print("✨ Setup complete! Now create these files manually:")
print("   1. static/css/style.css")
print("   2. static/js/auth.js")
print("\n💡 Or I can provide the content for you to copy-paste!")
print("=" * 60)