import streamlit as st
import utils
import requests
import time

# Check auth
utils.check_auth()
utils.render_header()

st.title("Organization Dashboard 🏫")

if st.session_state.get('role') != 'organization':
    st.error("Access Denied. This page is for Organizations only.")
    st.stop()

API_URL = utils.API_URL

# --- State Management ---
if 'org_view_mode' not in st.session_state:
    st.session_state['org_view_mode'] = 'dashboard' # dashboard, create_course, view_course
if 'selected_course_id' not in st.session_state:
    st.session_state['selected_course_id'] = None

# --- Tabs ---
tab_dash, tab_courses, tab_students = st.tabs(["📊 Overview", "📚 Course Manager", "mortar_board: Student Progress"])

# --- TAB 1: Overview ---
with tab_dash:
    st.markdown("### Welcome back, Administrator")
    
    # Mock Metrics for now, eventually query API
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Students", "150", "+12%")
    c2.metric("Active Courses", "12", "+2")
    c3.metric("Avg. Completion Rate", "78%", "+5%")
    
    st.markdown("### Recent Activity")
    st.info("No recent activity logs available.")

# --- TAB 2: Course Manager ---
with tab_courses:
    
    if st.session_state['org_view_mode'] == 'dashboard':
        col_header, col_btn = st.columns([5, 1])
        with col_header:
            st.subheader("Your Courses")
        with col_btn:
            if st.button("➕ Launch New Course", type="primary"):
                st.session_state['org_view_mode'] = 'create_course'
                st.rerun()
        
        # List Courses
        try:
            res = requests.get(f"{API_URL}/org/courses", headers=utils.get_auth_headers())
            if res.status_code == 200:
                courses = res.json()
                if not courses:
                    st.info("No courses found. Create your first one!")
                
                for c in courses:
                    with st.expander(f"{c['topic']} ({c['grade_level']})"):
                        st.write(f"**Structure**: {c.get('structure_type', 'Week')}-based")
                        st.write(f"**Description**: {c.get('description', 'No description')}")
                        
                        b1, b2, b3 = st.columns([1, 1, 3])
                        with b1:
                            if st.button("Manage", key=f"manage_{c['id']}"):
                                st.session_state['selected_course_id'] = c['id']
                                st.session_state['org_view_mode'] = 'view_course'
                                st.rerun()
                        with b2:
                            if st.button("🗑️", key=f"del_init_{c['id']}", help="Delete Course"):
                                st.session_state[f"confirm_delete_{c['id']}"] = True
                                st.rerun()
                        
                        # Delete Confirmation
                        if st.session_state.get(f"confirm_delete_{c['id']}"):
                            st.warning("Are you sure you want to delete this course? This cannot be undone.")
                            d1, d2 = st.columns([1, 4])
                            with d1:
                                if st.button("Yes, Delete", key=f"del_conf_{c['id']}", type="primary"):
                                    try:
                                        del_res = requests.delete(f"{API_URL}/courses/{c['id']}", headers=utils.get_auth_headers())
                                        if del_res.status_code == 200:
                                            st.success("Course deleted successfully.")
                                            del st.session_state[f"confirm_delete_{c['id']}"]
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to delete: {del_res.text}")
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                            with d2:
                                if st.button("Cancel", key=f"del_cancel_{c['id']}"):
                                    del st.session_state[f"confirm_delete_{c['id']}"]
                                    st.rerun()
            else:
                st.error("Failed to fetch courses.")
        except Exception as e:
            st.error(f"Connection error: {e}")

    elif st.session_state['org_view_mode'] == 'create_course':
        st.subheader("🚀 Launch New Course")
        if st.button("← Back to List"):
            st.session_state['org_view_mode'] = 'dashboard'
            st.rerun()
            
        st.markdown("---")
        
        # Creation Wizard
        with st.form("create_course_form"):
            title = st.text_input("Course Title", placeholder="e.g., Advanced Python Programming")
            grade = st.selectbox("Grade / Difficulty Level", ["Grade 8", "Grade 10", "Undergraduate", "Professional"])
            desc = st.text_area("Course Description")
            structure = st.selectbox("Structure Type", ["week", "day", "module"], help="How should the course be organized?")
            
            creation_mode = st.radio("Creation Mode", ["Manual Build", "AI Assisted Plan"], horizontal=True)
            
            submitted = st.form_submit_button("Initialize Course")
            
            if submitted:
                if not title:
                    st.error("Title is required")
                else:
                    if creation_mode == "Manual Build":
                        # Create empty course
                        payload = {
                            "title": title,
                            "grade_level": grade,
                            "description": desc,
                            "structure_type": structure
                        }
                        try:
                            res = requests.post(f"{API_URL}/org/courses/create", json=payload, headers=utils.get_auth_headers())
                            if res.status_code == 200:
                                st.success("Course Initialized!")
                                st.session_state['selected_course_id'] = res.json()['course_id']
                                st.session_state['org_view_mode'] = 'view_course'
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Failed to create: {res.text}")
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        # AI Mode - call plan_ai then create
                        # For MVP: We assume AI plan returns a structure, we need to create the course first then apply structure?
                        # Or better: Create course -> Then use AI to populate modules.
                        # Let's do: Create Course first -> Then redirect to Manage -> Trigger AI
                        payload = {
                            "title": title,
                            "grade_level": grade,
                            "description": desc,
                            "structure_type": structure
                        }
                        try:
                            res = requests.post(f"{API_URL}/org/courses/create", json=payload, headers=utils.get_auth_headers())
                            if res.status_code == 200:
                                cid = res.json()['course_id']
                                st.session_state['selected_course_id'] = cid
                                st.session_state['org_view_mode'] = 'view_course'
                                # Trigger AI Planning immediately in next view?
                                # We'll set a flag
                                st.session_state['trigger_ai_plan'] = True
                                st.rerun()
                            else:
                                st.error(f"Failed to create: {res.text}")
                        except Exception as e:
                            st.error(f"Error: {e}")

    elif st.session_state['org_view_mode'] == 'view_course':
        cid = st.session_state['selected_course_id']
        st.subheader(f"Manage Course (ID: {cid})")
        if st.button("← Back to List", key="back_manage"):
            st.session_state['org_view_mode'] = 'dashboard'
            st.rerun()
            
        # 1. Fetch Course Details
        # We misuse the student endpoint for getting details for now or need a dedicated org one
        # Actually `get_course_details` in main checks `user_id`, so org admin (who created it) can see it.
        try:
            res = requests.get(f"{API_URL}/courses/{cid}", headers=utils.get_auth_headers())
            if res.status_code == 200:
                roadmap = res.json()
                
                # Check for AI Trigger
                if st.session_state.get('trigger_ai_plan'):
                    # Clear flag
                    del st.session_state['trigger_ai_plan']
                    with st.spinner("🤖 AI Architect is designing your course structure..."):
                        # Call AI Plan endpoint
                        ai_payload = {
                            "topic": roadmap['topic'],
                            "grade_level": "Undergraduate", # TODO: fetch from course details if available in roadmap, or store in session
                            # Wait, roadmap might be empty. `get_course_details` returns `roadmap_json`.
                            # We need the other fields (grade, structure_type).
                            # Our `get_course_details` only returns JSON. We should update it or use `db` access.
                            # For MVP: We trust the user input or just pass defaults.
                            "structure_type": "week" 
                        }
                        # We need a robust way to get correct grade/structure. 
                        # Let's assume defaults for now or update backend to return full course obj.
                        
                        # Use the new endpoint that updates the DB directly
                        plan_res = requests.post(f"{API_URL}/org/courses/{cid}/plan", json=ai_payload, headers=utils.get_auth_headers())
                        if plan_res.status_code == 200:
                            new_roadmap = plan_res.json()
                            st.success("AI Plan Generated & Saved!")
                            st.rerun() # Rerun to show the new modules
                        else:
                            st.error(f"AI Planning failed: {plan_res.text}")

                st.markdown(f"**Topic**: {roadmap.get('topic', 'Unknown')}")
                
                # Modules List
                st.markdown("### 📑 Course Modules")
                
                chapters = roadmap.get('chapters', [])
                if not chapters:
                    st.info("No modules defined yet.")
                
                for mod in chapters:
                    with st.expander(f"Module {mod.get('chapter_number')}: {mod.get('title')}"):
                        st.write(mod.get('description'))
                        
                        # Edit Content UI
                        # We use a toggle state for editing
                        is_editing = st.session_state.get(f"editing_mod_{mod['id']}", False)
                        
                        if not is_editing:
                            if st.button("Edit Content", key=f"edit_btn_{mod['id']}"):
                                st.session_state[f"editing_mod_{mod['id']}"] = True
                                st.rerun()
                        else:
                            st.info("Editing Module Content")
                            # Fetch current content
                            try:
                                mod_res = requests.get(f"{API_URL}/org/courses/{cid}/modules/{mod['id']}", headers=utils.get_auth_headers())
                                if mod_res.status_code == 200:
                                    mod_data = mod_res.json()
                                    
                                    # Initialize session state for this module's quiz if not present
                                    import uuid
                                    if f"quiz_{mod['id']}" not in st.session_state:
                                        # Load data and assign temp UIDs for UI tracking
                                        loaded_quiz = mod_data.get('quiz_json') or []
                                        for q in loaded_quiz:
                                            q['_uid'] = str(uuid.uuid4())
                                        st.session_state[f"quiz_{mod['id']}"] = loaded_quiz
                                    
                                    # --- Main Content Form ---
                                    st.markdown("##### Lecture Content")
                                    c_markdown = st.text_area("Lecture Notes", value=mod_data.get('content_markdown') or "", height=300, key=f"md_{mod['id']}")
                                    c_video = st.text_input("Video URL", value=mod_data.get('video_url') or "", key=f"vid_{mod['id']}")
                                    
                                    st.markdown("##### Quiz Questions")
                                    
                                    quiz_list = st.session_state[f"quiz_{mod['id']}"]
                                    
                                    # We iterate by index but use _uid for keys
                                    indices_to_remove = []
                                    
                                    for i, q in enumerate(quiz_list):
                                        # Ensure UID exists (validity check)
                                        if '_uid' not in q: q['_uid'] = str(uuid.uuid4())
                                        
                                        with st.expander(f"Q{i+1}: {q.get('question', '')[:50]}...", expanded=False):
                                            q_uid = q['_uid']
                                            
                                            q_text = st.text_input(f"Question {i+1}", value=q.get('question', ''), key=f"q_{q_uid}")
                                            
                                            opts = q.get('options', ["", "", "", ""])
                                            if len(opts) < 4: opts += [""] * (4 - len(opts))
                                            
                                            c1, c2 = st.columns(2)
                                            o1 = c1.text_input("Option A", value=opts[0], key=f"o_{q_uid}_0")
                                            o2 = c2.text_input("Option B", value=opts[1], key=f"o_{q_uid}_1")
                                            o3 = c1.text_input("Option C", value=opts[2], key=f"o_{q_uid}_2")
                                            o4 = c2.text_input("Option D", value=opts[3], key=f"o_{q_uid}_3")
                                            
                                            curr_idx = q.get('correct_answer', 0)
                                            if curr_idx >= 4: curr_idx = 0
                                            
                                            corr = st.selectbox("Correct Answer", options=[0, 1, 2, 3], format_func=lambda x: ["Option A", "Option B", "Option C", "Option D"][x], index=curr_idx, key=f"ans_{q_uid}")
                                            
                                            if st.button("Delete Question", key=f"del_{q_uid}"):
                                                indices_to_remove.append(i)
                                            
                                            # Update in place (memory reference)
                                            q['question'] = q_text
                                            q['options'] = [o1, o2, o3, o4]
                                            q['correct_answer'] = corr
                                    
                                    # Process deletes
                                    if indices_to_remove:
                                        for idx in sorted(indices_to_remove, reverse=True):
                                            quiz_list.pop(idx)
                                        st.session_state[f"quiz_{mod['id']}"] = quiz_list
                                        st.rerun()

                                    if st.button("➕ Add Question", key=f"add_q_{mod['id']}"):
                                        quiz_list.append({
                                            "_uid": str(uuid.uuid4()),
                                            "question": "New Question",
                                            "options": ["", "", "", ""],
                                            "correct_answer": 0
                                        })
                                        st.session_state[f"quiz_{mod['id']}"] = quiz_list
                                        st.rerun()

                                    st.markdown("---")
                                    col_save, col_cancel = st.columns(2)
                                    with col_save:
                                        if st.button("Save Changes", key=f"save_{mod['id']}", type="primary"):
                                            final_quiz = st.session_state[f"quiz_{mod['id']}"]
                                            # Clean up UIDs before sending
                                            payload_quiz = []
                                            for q in final_quiz:
                                                new_q = q.copy()
                                                if '_uid' in new_q: del new_q['_uid']
                                                payload_quiz.append(new_q)
                                            
                                            update_payload = {
                                                "content_markdown": c_markdown,
                                                "video_url": c_video,
                                                "quiz": payload_quiz
                                            }
                                            
                                            try:
                                                up_res = requests.put(f"{API_URL}/org/courses/{cid}/modules/{mod['id']}", json=update_payload, headers=utils.get_auth_headers())
                                                if up_res.status_code == 200:
                                                    st.success("Content Updated!")
                                                    del st.session_state[f"editing_mod_{mod['id']}"]
                                                    del st.session_state[f"quiz_{mod['id']}"] # Cleanup
                                                    time.sleep(1)
                                                    st.rerun()
                                                else:
                                                    st.error(f"Save failed: {up_res.text}")
                                            except Exception as e:
                                                st.error(f"Error: {e}")
                                    
                                    with col_cancel:
                                        if st.button("Cancel", key=f"cancel_{mod['id']}"):
                                            del st.session_state[f"editing_mod_{mod['id']}"]
                                            if f"quiz_{mod['id']}" in st.session_state:
                                                del st.session_state[f"quiz_{mod['id']}"]
                                            st.rerun()
                                    
                                else:
                                     st.error("Failed to load module content")
                            except Exception as e:
                                st.error(f"Connection error: {e}")
                
                st.markdown("---")
                st.markdown("#### Add New Module")
                with st.form("add_module_form"):
                    m_title = st.text_input("Module Title")
                    m_desc = st.text_input("Description")
                    m_order = st.number_input("Order Index", min_value=1, value=len(chapters)+1)
                    
                    sub_mod = st.form_submit_button("Add Module")
                    if sub_mod:
                        mod_payload = {
                            "title": m_title,
                            "description": m_desc,
                            "order_index": m_order
                        }
                        res_mod = requests.post(f"{API_URL}/org/courses/{cid}/modules", json=mod_payload, headers=utils.get_auth_headers())
                        if res_mod.status_code == 200:
                            st.success("Module Added!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to add module")

            else:
                st.error("Course not found or access denied.")
        except Exception as e:
            st.error(f"Error loading course: {e}")


# --- TAB 3: Student Progress ---
with tab_students:
    st.subheader("🎓 Student Progress Tracking")
    
    try:
        res = requests.get(f"{API_URL}/org/students", headers=utils.get_auth_headers())
        if res.status_code == 200:
            enrollments = res.json()
            if enrollments:
                # Convert to DataFrame for better table
                import pandas as pd
                df = pd.DataFrame(enrollments)
                
                # Display proper columns
                st.dataframe(
                    df[['student_name', 'course_id', 'progress', 'joined_at']],
                    column_config={
                        "progress": st.column_config.ProgressColumn(
                            "Completion",
                            help="Course completion percentage",
                            format="%.0f%%",
                            min_value=0,
                            max_value=100,
                        ),
                        "joined_at": st.column_config.DatetimeColumn("Enrolled Date")
                    },
                    use_container_width=True
                )
            else:
                st.info("No students enrolled yet.")
        else:
            st.error("Failed to fetch student data.")
    except Exception as e:
        st.error(f"Error: {e}")

utils.render_footer()
