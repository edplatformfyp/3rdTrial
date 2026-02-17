import streamlit as st
import requests
import time
import extra_streamlit_components as stx

# Cookie Manager (Singleton-ish)
@st.cache_resource
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()


def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        print(f"Error loading CSS: {e}")

API_URL = "http://localhost:8000"

def login(username, password):
    try:
        response = requests.post(
            f"{API_URL}/auth/token",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            # Set cookies for persistence (expires in 7 days)
            cookie_manager.set("token", data['access_token'], expires_at=None, key="set_token")
            cookie_manager.set("role", data['role'], expires_at=None, key="set_role")
            cookie_manager.set("username", username, expires_at=None, key="set_user")
            return data
        return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

def register(username, password, email, role, organization_id=None, parent_id=None):
    try:
        payload = {
            "username": username, 
            "password": password, 
            "email": email, 
            "role": role,
            "organization_id": organization_id,
            "parent_id": parent_id
        }
        response = requests.post(f"{API_URL}/auth/register", json=payload)
        return response
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

def get_auth_headers():
    if 'token' in st.session_state:
        return {"Authorization": f"Bearer {st.session_state['token']}"}
    return {}

def logout():
    # Clear cookies
    cookie_manager.delete("token", key="del_token")
    cookie_manager.delete("role", key="del_role")
    cookie_manager.delete("username", key="del_user")
    
    # Clear session state
    for key in ['token', 'role', 'username', 'roadmap']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def check_auth():
    # If not in session, check cookies
    if 'token' not in st.session_state:
        token = cookie_manager.get("token")
        role = cookie_manager.get("role")
        username = cookie_manager.get("username")
        
        if token and role:
            st.session_state['token'] = token
            st.session_state['role'] = role
            st.session_state['username'] = username if username else "User"
            # Optional: Verify token with backend here if needed
            return

    if 'token' not in st.session_state:
        st.warning("Please log in to continue.")
        st.stop()

def render_header():
    # Sidebar is now enabled for navigation
    pass

    # Standard Header Layout
    with st.container():
        load_css("client/static/style.css")
        st.markdown('<style>div.block-container{padding-top: 2rem;}</style>', unsafe_allow_html=True) 
        
        # We use a custom container for styling
        h1, h2, h3 = st.columns([2, 4, 2])
        
        with h1:
            st.markdown(f"""
                <div style="font-family: 'Orbitron', sans-serif; font-size: 1.5rem; color: white; display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.8rem;">⚛️</span> EduCore
                </div>
            """, unsafe_allow_html=True)
            
        with h3:
            if 'token' in st.session_state:
                u_col1, u_col2 = st.columns([2, 1])
                with u_col1:
                    st.markdown(f"""
                        <div style="text-align: right; color: #a0a0ff; display: flex; align-items: center; justify-content: flex-end; height: 100%; gap: 10px;">
                            <span>{st.session_state.get('username', 'User')}</span>
                            <div style="width: 30px; height: 30px; background: var(--neon-purple); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                                {st.session_state.get('username', 'U')[0].upper()}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                with u_col2:
                    if st.button("Logout", key="header_logout", type="secondary"):
                        logout()
        
        st.markdown("---") # Divider

def render_footer():
    st.markdown("""
        <div class="footer-container">
            <div style="display: flex; justify-content: space-around; max-width: 1200px; margin: 0 auto; flex-wrap: wrap;">
                <div class="footer-col">
                    <h4>EduCore</h4>
                    <a href="#" class="footer-link">About Us</a>
                    <a href="#" class="footer-link">Careers</a>
                    <a href="#" class="footer-link">Catalog</a>
                </div>
                <div class="footer-col">
                    <h4>Community</h4>
                    <a href="#" class="footer-link">Learners</a>
                    <a href="#" class="footer-link">Partners</a>
                    <a href="#" class="footer-link">Blog</a>
                </div>
                <div class="footer-col">
                    <h4>More</h4>
                    <a href="#" class="footer-link">Terms</a>
                    <a href="#" class="footer-link">Privacy</a>
                    <a href="#" class="footer-link">Help</a>
                </div>
                 <div class="footer-col">
                    <h4>Mobile App</h4>
                    <a href="#" class="footer-link">iOS</a>
                    <a href="#" class="footer-link">Android</a>
                </div>
            </div>
            <div style="text-align: center; color: #64748b; margin-top: 40px; font-size: 0.8rem; font-family: 'Rajdhani', sans-serif;">
                © 2026 EduCore Systems Inc. | <span style="color: var(--neon-blue);">Status: Operational</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
