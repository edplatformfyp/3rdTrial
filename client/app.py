import streamlit as st
import utils
import time

st.set_page_config(page_title="EduCore Login", layout="wide")

# Load Custom CSS
# Load Custom CSS
utils.load_css("client/static/style.css")

# Hide sidebar on Login page too
# st.markdown("""
#         <style>
#             [data-testid="stSidebar"] {display: none;}
#         </style>
#     """, unsafe_allow_html=True)

# Attempt to restore session from cookies
if 'token' not in st.session_state:
    try:
        # We access the cookie manager directly or via utils to check
        # But utils.check_auth is a blocking call (stops execution), 
        # so we need a non-blocking restore function or carefully use check_auth
        
        # Let's peek at cookies using the manager in utils
        token = utils.cookie_manager.get("token")
        if token:
            st.session_state['token'] = token
            st.session_state['role'] = utils.cookie_manager.get("role")
            st.session_state['username'] = utils.cookie_manager.get("username")
            st.rerun() # Rerun to pick up the logged-in state
    except Exception as e:
        pass

st.title("Welcome to EduCore 🚀")

if 'token' in st.session_state:
    st.success(f"Logged in as {st.session_state.get('username', 'User')} ({st.session_state.get('role', 'Unknown')})")
    
    # If we are here, it means we are logged in but maybe caught on the landing page
    # offering a button to go back to dashboard in case of manual navigation
    role = st.session_state.get('role')
    
    col1, col2 = st.columns([1, 1])
    with col1:
         if role == 'student':
            if st.button("Go to Student Dashboard 🎓", use_container_width=True):
                st.switch_page("pages/01_Student_Dashboard.py")
         elif role == 'parent':
            if st.button("Go to Parent Portal 👨‍👩‍👧‍👦", use_container_width=True):
                st.switch_page("pages/02_Parent_Dashboard.py")
    
    with col2:
        if st.button("Logout", type="secondary", use_container_width=True):
            utils.logout()
    
    utils.render_footer()
    st.stop()

tab1, tab2 = st.tabs(["Login", "Sign Up"])

with tab1:
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            res = utils.login(username, password)
            if res:
                st.session_state['token'] = res['access_token']
                st.session_state['role'] = res['role']
                st.session_state['username'] = username
                st.success("Login Successful! Redirecting...")
                time.sleep(0.5)
                
                # Auto-Redirect based on role
                if res['role'] == 'student':
                    st.switch_page("pages/01_Student_Dashboard.py")
                elif res['role'] == 'parent':
                    st.switch_page("pages/02_Parent_Dashboard.py")
                elif res['role'] == 'organization':
                     st.switch_page("pages/03_Org_Dashboard.py")
                elif res['role'] == 'admin':
                     st.switch_page("pages/04_Admin_Dashboard.py")
                else:
                    st.rerun()
            else:
                st.error("Invalid credentials")

with tab2:
    with st.form("signup_form"):
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        email = st.text_input("Email")
        role = st.selectbox("Role", ["student", "parent", "organization", "admin"])
        
        # Conditional fields (mocked for now)
        org_id = None
        parent_id = None
        
        if role == "student":
            parent_username = st.text_input("Parent Username (Optional)")
            # In a real app, we'd lookup the ID
        
        submit_signup = st.form_submit_button("Sign Up")
        
        if submit_signup:
            res = utils.register(new_user, new_pass, email, role)
            if res and res.status_code == 200:
                st.success("Account created! Please login.")
            else:
                msg = res.json().get('detail') if res else "Unknown error"
                st.error(f"Signup failed: {msg}")

utils.render_footer()
