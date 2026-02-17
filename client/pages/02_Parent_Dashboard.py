import streamlit as st
import requests
import utils

# Check authentication
utils.check_auth()
utils.render_header()

API_URL = utils.API_URL

st.title("Parent Portal 👨‍👩‍👧‍👦")

if st.session_state.get('role') != 'parent':
    st.error("Access Denied. This page is for Parents only.")
    st.stop()

# --- Sidebar: Link New Child ---
with st.sidebar:
    st.subheader("🔗 Link Child Account")
    secret_id_input = st.text_input("Enter Child's Secret ID", placeholder="username-1234")
    if st.button("Send Link Request"):
        if secret_id_input:
            try:
                # API Call to request link
                res = requests.post(f"{API_URL}/parent/link-request", params={"secret_id": secret_id_input}, headers=utils.get_auth_headers())
                if res.status_code == 200:
                    st.success("Request Sent! Ask your child to approve it.")
                else:
                    st.error(f"Error: {res.json().get('detail')}")
            except Exception as e:
                st.error(f"Connection Error: {e}")
    
    st.divider()

# --- Main Dashboard ---
st.subheader("My Children")

# 1. Fetch Children
my_children = []
try:
    res = requests.get(f"{API_URL}/parent/children", headers=utils.get_auth_headers())
    if res.status_code == 200:
        my_children = res.json()
except Exception as e:
    st.error(f"Failed to load children: {e}")

if not my_children:
    st.info("No children linked yet. Use the sidebar to link an account.")
else:
    # Child Selector
    child_names = [c['username'] for c in my_children]
    selected_child_name = st.selectbox("Select Child to Monitor", child_names)
    
    # Get ID of selected child
    selected_child_id = next(c['id'] for c in my_children if c['username'] == selected_child_name)
    
    # 2. Fetch Child Data
    try:
        prog_res = requests.get(f"{API_URL}/parent/child/{selected_child_id}/progress", headers=utils.get_auth_headers())
        if prog_res.status_code == 200:
            data = prog_res.json()
            
            # --- Metrics ---
            c1, c2, c3 = st.columns(3)
            c1.metric("Active Courses", len(data['courses']))
            c2.metric("Avg Quiz Score", f"{data['average_score']}%")
            c3.metric("Quizzes Taken", len(data['recent_quizzes']))
            
            st.divider()
            
            # --- Detailed Views ---
            tab1, tab2, tab3 = st.tabs(["📚 Courses", "📝 Recent Quizzes", "⚙️ Actions"])
            
            with tab1:
                if not data['courses']:
                    st.info("No active courses.")
                for course in data['courses']:
                    st.markdown(f"""
                    <div style="padding: 10px; border: 1px solid #333; border-radius: 5px; margin-bottom: 5px;">
                        <strong>{course['topic']}</strong> <span style="color: #888;">({course['grade_level']})</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            with tab2:
                if not data['recent_quizzes']:
                    st.info("No quizzes taken yet.")
                for q in data['recent_quizzes']:
                    st.write(f"Timestamp: {q['timestamp'][:16]} | Score: **{q['score']}/{q['total']}**")
                    
            with tab3:
                st.subheader("Control Panel")
                
                # Action 1: Assign Course
                with st.expander("Assign New Course"):
                    with st.form("assign_course"):
                        topic = st.text_input("Topic")
                        grade = st.selectbox("Grade Level", ["Grade 8", "Grade 10", "Undergraduate"])
                        if st.form_submit_button("Generate & Assign"):
                            with st.spinner("Creating course..."):
                                try:
                                    payload = {"topic": topic, "grade_level": grade}
                                    # Note: Query param for child_id
                                    gen_res = requests.post(f"{API_URL}/courses/generate-for-child", params={"child_id": selected_child_id}, json=payload, headers=utils.get_auth_headers())
                                    if gen_res.status_code == 200:
                                        st.success("Course assigned successfully!")
                                    else:
                                        st.error("Failed to assign course")
                                except Exception as e:
                                    st.error(f"Error: {e}")

                # Action 2: Message
                with st.expander("Send Message"):
                    msg_content = st.text_input("Message Content")
                    if st.button("Send Notification"):
                         try:
                             # Query param receiver_id, content
                             # Endpoints definition: request_link(secret_id...), receive_id is for message
                             # app.post("/parent/message")(receiver_id: str, content: str...)
                             msg_res = requests.post(f"{API_URL}/parent/message", params={"receiver_id": selected_child_id, "content": msg_content}, headers=utils.get_auth_headers())
                             if msg_res.status_code == 200:
                                 st.success("Message sent!")
                         except Exception as e:
                             st.error(f"Error: {e}")

        else:
            st.error("Failed to load progress data")
    except Exception as e:
        st.error(f"Error fetching data: {e}")

utils.render_footer()
