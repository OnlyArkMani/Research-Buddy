// Animation timing
const LOGO_DISPLAY_TIME = 3500; // Show logo for 3.5 seconds

// Elements
const logoSection = document.getElementById('logoSection');
const authSection = document.getElementById('authSection');
const authButtons = document.getElementById('authButtons');
const emailForm = document.getElementById('emailForm');
const loadingState = document.getElementById('loadingState');

// Buttons
const googleSignInBtn = document.getElementById('googleSignIn');
const emailSignInBtn = document.getElementById('emailSignIn');
const signInBtn = document.getElementById('signInBtn');
const signUpBtn = document.getElementById('signUpBtn');
const backBtn = document.getElementById('backBtn');

// Form inputs
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');

// Firebase Auth
const auth = firebase.auth();

// Initialize
window.addEventListener('DOMContentLoaded', () => {
    // Show logo animation, then transition to auth
    setTimeout(() => {
        transitionToAuth();
    }, LOGO_DISPLAY_TIME);
});

// Transition from logo to auth
function transitionToAuth() {
    logoSection.classList.add('fade-out');
    
    setTimeout(() => {
        logoSection.style.display = 'none';
        authSection.style.display = 'block';
    }, 500);
}

// Google Sign In
googleSignInBtn.addEventListener('click', async () => {
    showLoading();
    
    try {
        const provider = new firebase.auth.GoogleAuthProvider();
        const result = await auth.signInWithPopup(provider);
        
        // Send token to backend
        const token = await result.user.getIdToken();
        await verifyAuth(token, result.user.email);
        
    } catch (error) {
        hideLoading();
        showError('Google sign-in failed: ' + error.message);
    }
});

// Email Sign In Button
emailSignInBtn.addEventListener('click', () => {
    showEmailForm();
});

// Back Button
backBtn.addEventListener('click', () => {
    hideEmailForm();
});

// Sign In with Email
signInBtn.addEventListener('click', async () => {
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    
    if (!email || !password) {
        showError('Please enter email and password');
        return;
    }
    
    showLoading();
    
    try {
        const result = await auth.signInWithEmailAndPassword(email, password);
        const token = await result.user.getIdToken();
        await verifyAuth(token, result.user.email);
        
    } catch (error) {
        hideLoading();
        if (error.code === 'auth/user-not-found') {
            showError('No account found with this email');
        } else if (error.code === 'auth/wrong-password') {
            showError('Incorrect password');
        } else {
            showError('Sign in failed: ' + error.message);
        }
    }
});

// Sign Up with Email
signUpBtn.addEventListener('click', async () => {
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    
    if (!email || !password) {
        showError('Please enter email and password');
        return;
    }
    
    if (password.length < 6) {
        showError('Password must be at least 6 characters');
        return;
    }
    
    showLoading();
    
    try {
        const result = await auth.createUserWithEmailAndPassword(email, password);
        const token = await result.user.getIdToken();
        await verifyAuth(token, result.user.email);
        
    } catch (error) {
        hideLoading();
        if (error.code === 'auth/email-already-in-use') {
            showError('An account with this email already exists');
        } else if (error.code === 'auth/invalid-email') {
            showError('Invalid email address');
        } else if (error.code === 'auth/weak-password') {
            showError('Password is too weak');
        } else {
            showError('Sign up failed: ' + error.message);
        }
    }
});

// Verify auth with backend
async function verifyAuth(token, email) {
    try {
        const response = await fetch('/auth/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token, email })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Redirect to Chainlit app
            showSuccess('Authentication successful! Redirecting...');
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 1000);
        } else {
            hideLoading();
            showError('Authentication verification failed');
        }
        
    } catch (error) {
        hideLoading();
        showError('Failed to verify authentication: ' + error.message);
    }
}

// UI Helper Functions
function showEmailForm() {
    authButtons.style.display = 'none';
    emailForm.style.display = 'block';
}

function hideEmailForm() {
    emailForm.style.display = 'none';
    authButtons.style.display = 'flex';
    emailInput.value = '';
    passwordInput.value = '';
}

function showLoading() {
    authButtons.style.display = 'none';
    emailForm.style.display = 'none';
    loadingState.style.display = 'block';
}

function hideLoading() {
    loadingState.style.display = 'none';
    const isEmailFormVisible = emailForm.style.display === 'block';
    if (isEmailFormVisible) {
        emailForm.style.display = 'block';
    } else {
        authButtons.style.display = 'flex';
    }
}

function showError(message) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #ff4444;
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function showSuccess(message) {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #E85D75 0%, #c44569 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Add toast animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Enter key support
emailInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') signInBtn.click();
});

passwordInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') signInBtn.click();
});