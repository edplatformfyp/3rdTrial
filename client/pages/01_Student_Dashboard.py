import streamlit as st
import requests
import time
import utils

# Check authentication
utils.check_auth()

utils.render_header()

API_URL = utils.API_URL

# Session State Initialization
if 'roadmap' not in st.session_state:
    st.session_state['roadmap'] = None
if 'content_cache' not in st.session_state:
    st.session_state['content_cache'] = {}
if 'current_chapter_index' not in st.session_state:
    st.session_state['current_chapter_index'] = None
if 'view_mode' not in st.session_state:
    st.session_state['view_mode'] = 'new' # new, course, notes, messages

# Fetch User Profile (for Secret ID)
user_profile = {}
try:
    res = requests.get(f"{API_URL}/users/me", headers=utils.get_auth_headers())
    if res.status_code == 200:
        user_profile = res.json()
except:
    pass

# Check for notifications (Friend Requests / Messages)
with st.sidebar:
    st.markdown(f"**My Secret ID:** `{user_profile.get('secret_id', 'N/A')}`")
    st.info("Share this ID with your parent to link accounts.")
    
    # Check Requests
    try:
        req_res = requests.get(f"{API_URL}/student/requests", headers=utils.get_auth_headers())
        if req_res.status_code == 200:
            requests_list = req_res.json()
            if requests_list:
                st.warning(f"🔔 {len(requests_list)} Parent Request(s)")
                for r in requests_list:
                    st.write(f"**{r['username']}** wants to link.")
                    if st.button("Approve", key=f"approve_{r['id']}"):
                        try:
                            # Verify 'approve-request' endpoint expects query param or body?
                            # Based on main.py: `approve_request(parent_id: str...)` -> Query param by default in FastAPI if not Pydantic model
                            app_res = requests.post(f"{API_URL}/student/approve-request", params={"parent_id": r['id']}, headers=utils.get_auth_headers())
                            if app_res.status_code == 200:
                                st.success("Linked!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
    except:
        pass
    
    # Check Messages
    try:
        msg_res = requests.get(f"{API_URL}/student/messages", headers=utils.get_auth_headers())
        if msg_res.status_code == 200:
            msgs = msg_res.json()
            unread_count = len([m for m in msgs if not m['is_read']])
            label = "📩 Messages"
            if unread_count > 0:
                label += f" ({unread_count})"
            
            if st.button(label, use_container_width=True):
                 st.session_state['view_mode'] = 'messages'
                 st.session_state['messages'] = msgs
                 st.session_state['roadmap'] = None
                 st.rerun()
    except:
        pass

    st.divider()
if 'content_cache' not in st.session_state:
    st.session_state['content_cache'] = {}
if 'current_chapter_index' not in st.session_state:
    st.session_state['current_chapter_index'] = None
if 'view_mode' not in st.session_state:
    st.session_state['view_mode'] = 'new' # new, course, notes

# Dashboard Header
st.title("Student Command Center")
st.markdown("<p style='color: #64748b; margin-top: -10px; margin-bottom: 2rem;'>Manage your learning journey and active modules.</p>", unsafe_allow_html=True)

# Input Section (Holo-Card Style)
# View Logic
view_mode = st.session_state.get('view_mode', 'new')

if view_mode == 'notes':
    st.header("📝 My Notes")
    
    # Fetch all notes
    try:
        notes_res = requests.get(f"{API_URL}/notes", headers=utils.get_auth_headers())
        if notes_res.status_code == 200:
            notes = notes_res.json()
            
            if not notes:
                st.info("No notes found. create one inside a course!")
            
            for note in notes:
                with st.expander(f"{note['created_at'][:10]} - {note.get('topic', 'General')}"):
                    st.write(note['content'])
                    c1, c2 = st.columns([1, 10])
                    with c1:
                        if st.button("🗑️", key=f"del_note_{note['id']}"):
                            try:
                                requests.delete(f"{API_URL}/notes/{note['id']}", headers=utils.get_auth_headers())
                                st.rerun()
                            except:
                                st.error("Failed to delete")
        else:
            st.error("Failed to fetch notes")
    except Exception as e:
        st.error(f"Error: {e}")

elif view_mode == 'messages':
    st.header("📩 Inbox")
    msgs = st.session_state.get('messages', [])
    if not msgs:
        st.info("No messages.")
    
    for m in msgs:
        with st.chat_message("user", avatar="👨‍👩‍👧‍👦"):
            st.write(f"**{m['sender']}** ({m['timestamp'][:16]})")
            st.write(m['content'])
            
    if st.button("Back to Dashboard"):
        st.session_state['view_mode'] = 'new'
        st.rerun()

elif view_mode == 'new' or not st.session_state['roadmap']:
    
    st.markdown('<div class="dashboard-input-container">', unsafe_allow_html=True)
    st.markdown('<h3 style="color: var(--neon-blue); margin-bottom: 1.5rem; display: flex; align-items: center; gap: 10px;">🚀 Initialize New Learning Module</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("Target Subject / Topic", "Quantum Physics", help="Enter the subject you want to master.")
    with col2:
        grade = st.selectbox("Complexity Level", ["Grade 8", "Grade 10", "Undergraduate", "PhD"])
    
    st.write("")
    
    # Center the button and constrain width
    b1, b2, b3 = st.columns([1, 1, 1])
    with b2:
        if st.button("Generate Roadmap ⚡", use_container_width=True, type="primary"):
            with st.spinner("Accessing Neural Network..."):
                try:
                    payload = {"topic": topic, "grade_level": grade}
                    # FIX: Correct endpoint
                    response = requests.post(f"{API_URL}/courses/generate", json=payload, headers=utils.get_auth_headers())
                    response.raise_for_status()
                    data = response.json()
                    
                    # FIX: Fetch full course details to get Chapter IDs
                    course_id = data.get('course_id')
                    st.session_state['course_id'] = course_id
                    
                    # Fetching full structure
                    res_details = requests.get(f"{API_URL}/courses/{course_id}", headers=utils.get_auth_headers())
                    res_details.raise_for_status()
                    roadmap_data = res_details.json()
                    
                    st.session_state['roadmap'] = roadmap_data
                    st.session_state['topic'] = topic
                    st.session_state['grade'] = grade
                    st.session_state['content_cache'] = {} 
                    st.session_state['current_chapter_index'] = 0
                    st.session_state['view_mode'] = 'course' # Force view mode
                    st.success("Roadmap Generated & Saved!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"System Error: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Recent / Recommended (Mock Data for Visuals)
    st.markdown("### 📡 Detected Learning Paths", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
         st.markdown("""
            <div class="course-card">
                <div class="card-icon" style="font-size: 2rem; margin-bottom: 1rem;">🤖</div>
                <div class="card-title">Artificial Intelligence</div>
                <div class="card-subtitle">Neural Networks & Deep Learning</div>
                <div style="height: 4px; width: 100%; background: #333; margin-top: auto; border-radius: 2px;">
                    <div style="height: 100%; width: 75%; background: var(--neon-blue); box-shadow: 0 0 10px var(--neon-blue);"></div>
                </div>
                <div style="text-align: right; font-size: 0.8rem; color: #aaa; margin-top: 5px;">75% Complete</div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
            <div class="course-card">
                <div class="card-icon" style="font-size: 2rem; margin-bottom: 1rem;">🛡️</div>
                <div class="card-title">Cybersecurity</div>
                <div class="card-subtitle">Network Defense Protocols</div>
                <div style="height: 4px; width: 100%; background: #333; margin-top: auto; border-radius: 2px;">
                    <div style="height: 100%; width: 40%; background: var(--neon-purple); box-shadow: 0 0 10px var(--neon-purple);"></div>
                </div>
                <div style="text-align: right; font-size: 0.8rem; color: #aaa; margin-top: 5px;">40% Complete</div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
            <div class="course-card">
                <div class="card-icon" style="font-size: 2rem; margin-bottom: 1rem;">🚀</div>
                <div class="card-title">Space Exploration</div>
                <div class="card-subtitle">Orbital Mechanics</div>
                 <div style="height: 4px; width: 100%; background: #333; margin-top: auto; border-radius: 2px;">
                    <div style="height: 100%; width: 10%; background: var(--neon-blue); box-shadow: 0 0 10px var(--neon-blue);"></div>
                </div>
                <div style="text-align: right; font-size: 0.8rem; color: #aaa; margin-top: 5px;">10% Complete</div>
            </div>
        """, unsafe_allow_html=True)
else:
    pass # Roadmap view triggers below

# Main Usage
# Main Usage
# Logic adjusted for sidebar persistence
    
    # Fetch User Courses
my_courses = []
try:
    res = requests.get(f"{API_URL}/courses", headers=utils.get_auth_headers())
    if res.status_code == 200:
        my_courses = res.json()
except Exception as e:
    st.error(f"Failed to load courses: {e}")

# --- Sidebar Navigation ---
with st.sidebar:
    st.header("📚 My Library")
    
    # Course Selector
    # Create a mapping for easy lookup
    course_options = {
        "Start New Module": None,
        "📝 My Notes": "NOTES_VIEW"
    }
    for c in my_courses:
        label = f"{c['topic']} ({c['grade_level']})"
        course_options[label] = c['id']
    
    # Determine current selection
    current_selection_index = 0
    
    # Check if we are in Notes view
    if st.session_state.get('view_mode') == 'notes':
        keys = list(course_options.keys())
        if "📝 My Notes" in keys:
            current_selection_index = keys.index("📝 My Notes")
    elif st.session_state['roadmap'] and 'course_id' in st.session_state:
        # Find the label for the current course_id
        for i, (label, cid) in enumerate(course_options.items()):
            if cid == st.session_state['course_id']:
                current_selection_index = i
                break
    
    selected_option = st.selectbox(
        "Select Active Course:", 
        list(course_options.keys()), 
        index=current_selection_index,
        key="course_selector"
    )

    # Handle Selection Change
    selected_course_id = course_options[selected_option]
    
    if selected_course_id == "NOTES_VIEW":
        if st.session_state.get('view_mode') != 'notes':
            st.session_state['view_mode'] = 'notes'
            st.session_state['roadmap'] = None
            st.rerun()
            
    elif selected_course_id is None:
        # User selected "Start New Module"
        if st.session_state.get('view_mode') != 'new':
            st.session_state['view_mode'] = 'new'
            st.session_state['roadmap'] = None
            st.session_state['content_cache'] = {}
            st.session_state['current_chapter_index'] = None
            # Do NOT delete course_id yet, just clear roadmap view
            # if 'course_id' in st.session_state:
            #     del st.session_state['course_id']
            st.rerun()
    else:
        # User selected an existing course
        # Load if not loaded OR if we are coming from a different view
        if (st.session_state.get('view_mode') != 'course') or ('course_id' not in st.session_state) or (st.session_state['course_id'] != selected_course_id):
            with st.spinner("Loading Course Blueprint..."):
                try:
                    res = requests.get(f"{API_URL}/courses/{selected_course_id}", headers=utils.get_auth_headers())
                    if res.status_code == 200:
                        roadmap_data = res.json()
                        st.session_state['roadmap'] = roadmap_data
                        st.session_state['topic'] = roadmap_data['topic']
                        st.session_state['course_id'] = selected_course_id
                        st.session_state['content_cache'] = {}
                        st.session_state['current_chapter_index'] = 0
                        st.session_state['view_mode'] = 'course'
                        st.rerun()
                except Exception as e:
                    st.error(f"Failed to load course: {e}")

    st.divider()

    # If a roadmap is loaded (even if hidden), calculate btn_type
    # BUT sidebar chapter internal nav should only show if view_mode is 'course'
    if st.session_state.get('view_mode') == 'course' and st.session_state['roadmap']:
        roadmap = st.session_state['roadmap']
        st.write(f"**chapters: {roadmap['topic']}**")
        
        # Ensure index is initialized
        if st.session_state['current_chapter_index'] is None:
             st.session_state['current_chapter_index'] = 0
             
        for i, chapter in enumerate(roadmap['chapters']):
            # Highlight current chapter
            btn_type = "primary" if st.session_state['current_chapter_index'] == i else "secondary"
            if st.button(f"{i+1}. {chapter['title']}", key=f"sidebar_btn_{i}", type=btn_type, use_container_width=True):
                st.session_state['current_chapter_index'] = i
                st.rerun()

        st.divider()
        if st.button("🗑️ Delete Course", type="secondary", use_container_width=True):
            if st.session_state.get('course_id'):
                try:
                    del_res = requests.delete(f"{API_URL}/courses/{st.session_state['course_id']}", headers=utils.get_auth_headers())
                    if del_res.status_code == 200:
                        st.success("Course deleted!")
                        st.session_state['roadmap'] = None
                        st.session_state['course_id'] = None
                        st.session_state['view_mode'] = 'new'
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete course: {e}")

    # --- Main Content Area (Coursera Style) ---
if st.session_state.get('view_mode') == 'course' and st.session_state['roadmap']:
    roadmap = st.session_state['roadmap']
    idx = st.session_state['current_chapter_index']
    chapter = roadmap['chapters'][idx]
    
    # Breadcrumbs / Header
    st.markdown(f"<div style='color: var(--neon-blue); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;'>{roadmap['topic']} // Chapter {idx+1}</div>", unsafe_allow_html=True)
    st.markdown(f"<h1>{chapter['title']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #e0e0ff; margin-bottom: 2rem; border-left: 2px solid var(--neon-purple); padding-left: 1rem;'>{chapter['description']}</p>", unsafe_allow_html=True)

    # Content Logic
    if idx in st.session_state['content_cache']:
        content = st.session_state['content_cache'][idx]
    else:
        with st.spinner(f"Agents are researching and generating content for: {chapter['title']}..."):
            try:
                # Payload not needed for backend logic, but keeping topic/grade might be useful if backend changes.
                # Currently backend looks up chapter by ID.
                # payload = { ... } 
                
                # Use a specific container for the content generation visual
                status_container = st.empty()
                status_container.info(f"🧠 Content Agent working on '{chapter['title']}'...")

                cid = st.session_state['course_id']
                chid = chapter['id']
                
                # st.info("DEBUG: Sending request to backend...")
                response = requests.post(f"{API_URL}/courses/{cid}/chapters/{chid}/generate", json={}, headers=utils.get_auth_headers(), timeout=120)
                # st.info(f"DEBUG: Response received. Status code: {response.status_code}")
                # st.info(f"DEBUG: Raw response text: {response.text[:500]}...")

                response.raise_for_status()
                content = response.json()
                

                
                st.session_state['content_cache'][idx] = content
                status_container.empty()
            except Exception as e:
                st.error(f"Failed to generate content: {e}")
                content = None

    if content:
        
        # Layout: Content on Left, Media/Quiz on Right (Desktop) or stacked (Mobile)
        # Using tabs for cleaner look
        
        tab_content, tab_video, tab_quiz, tab_notes = st.tabs(["📖 Reading Material", "🎥 Video Lecture", "📝 Quiz", "📒 Notes"])
        
        with tab_content:
             # Parse content into slides based on '## '
             raw_md = content['content_markdown']
             # Split by '## ' but keep the delimiter to re-attach
             # A simple split might lose the header, so let's try a regex or manual split
             # Manual:
             slides = []
             parts = raw_md.split('## ')
             for part in parts:
                 if not part.strip(): continue
                 # Re-add the header which was consumed by split, unless it's the very first empty part
                 # Actually, better to just prepend '## ' if it wasn't there, or handle title separate
                 
                 # Heuristic: split removes '## ', so we treat the first line as title
                 lines = part.strip().split('\n')
                 title = lines[0]
                 body = '\n'.join(lines[1:])
                 slides.append({"title": title, "body": body})
             
             if not slides:
                 # Fallback if no ## found
                 slides.append({"title": "Introduction", "body": raw_md})

             # Slide Navigation Session State
             slide_key = f"slide_idx_{idx}"
             if slide_key not in st.session_state:
                 st.session_state[slide_key] = 0
             
             current_slide = st.session_state[slide_key]
             
             # Slide Display (Card Style)
             slide = slides[current_slide]
             
             # Progress Bar
             progress = (current_slide + 1) / len(slides)
             st.progress(progress)
             
             # Navigation Buttons
             c_prev, c_cent, c_next = st.columns([1, 2, 1])
             with c_prev:
                 if st.button("⬅️ Previous", key=f"prev_{idx}", disabled=(current_slide == 0), use_container_width=True):
                     st.session_state[slide_key] -= 1
                     st.rerun()
             with c_next:
                 if st.button("Next ➡️", key=f"next_{idx}", disabled=(current_slide == len(slides) - 1), use_container_width=True):
                     st.session_state[slide_key] += 1
                     st.rerun()
             
             with c_cent:
                 st.markdown(f"<p style='text-align: center; color: #aaa;'>Slide {current_slide + 1} of {len(slides)}</p>", unsafe_allow_html=True)

             # The Slide Content
             # Using st.container with border for a card-like effect
             with st.container(border=True):
                 st.markdown(f"<h2 style='text-align: center; color: var(--neon-blue);'>{slide['title']}</h2>", unsafe_allow_html=True)
                 st.markdown("---")
                 
                 # Render body with increased font size for "Presentation" feel
                 st.markdown(f"<div style='font-size: 1.2rem; line-height: 1.6;'>", unsafe_allow_html=True)
                 st.markdown(slide['body'])
                 st.markdown("</div>", unsafe_allow_html=True)
             
             st.divider()
             
             # Fallback View Full Text
             with st.expander("📄 View Full Document"):
                 st.markdown(content['content_markdown'])
             
        with tab_video:
             st.subheader("Video Summary 🎥")
             video_key = f"video_{idx}"
             
             col_vid_left, col_vid_right = st.columns([2, 1])
             with col_vid_left:
                 if video_key not in st.session_state:
                     st.session_state[video_key] = None
                     
                 if st.session_state[video_key]:
                     video_url = f"{API_URL}{st.session_state[video_key]}"
                     st.video(video_url)
                 else:
                     st.info("Video simulation unavailable created yet.")
                     if st.button("Generate Video Summary", key=f"gen_vid_{idx}"):
                         with st.spinner("Generating video..."):
                             try:
                                 vid_payload = {
                                     "topic": roadmap['topic'],
                                     "content_markdown": content['content_markdown'],
                                     "chapter_title": chapter['title']
                                 }
                                 # FIX: We need to pass auth since we updated the endpoint
                                 vid_resp = requests.post(f"{API_URL}/generate/video", json=vid_payload, headers=utils.get_auth_headers())
                                 vid_resp.raise_for_status()
                                 vid_data = vid_resp.json()
                                 st.session_state[video_key] = vid_data['video_url']
                                 st.rerun()
                             except Exception as e:
                                 st.error(f"Video generation failed: {e}")

        with tab_quiz:
             st.subheader("Knowledge Check")
             quiz_key = f"quiz_started_{idx}"
             result_key = f"quiz_result_{idx}"
             
             # Check for existing result (One-time policy)
             if result_key not in st.session_state:
                 try:
                     # Use chapter['id'] instead of chid
                     q_res = requests.get(f"{API_URL}/quizzes/{chapter['id']}/result", headers=utils.get_auth_headers())
                     if q_res.status_code == 200:
                         st.session_state[result_key] = q_res.json()
                     else:
                         st.session_state[result_key] = None
                 except:
                     st.session_state[result_key] = None

             existing_result = st.session_state[result_key]

             if existing_result:
                 # Show Result View (Read Only)
                 score = existing_result['score']
                 total = existing_result['total_questions']
                 percentage = (score / total) * 100
                 
                 st.markdown(f"""
                    <div style="text-align: center; padding: 20px; border: 1px solid var(--neon-blue); border-radius: 10px; background: rgba(0,0,0,0.2);">
                        <h2 style="color: var(--neon-blue);">Quiz Completed! 🏆</h2>
                        <h1 style="font-size: 3rem;">{score}/{total}</h1>
                        <p style="font-size: 1.2rem;">You achieved {percentage:.1f}%</p>
                        <p style="color: #aaa; margin-top: 10px;">You have already taken this quiz. Attempts are limited to one.</p>
                    </div>
                 """, unsafe_allow_html=True)
                 
                 # Optional: Show breakdown if we want, but for now just the score is fine as per MVP
                 
             else:
                 # Show Quiz Interface
                 if quiz_key not in st.session_state:
                     st.session_state[quiz_key] = False
    
                 if not st.session_state[quiz_key]:
                     st.markdown("""
                        <div class="course-card" style="text-align: center;">
                            <h3>Ready to test your knowledge?</h3>
                            <p>Take a quick quiz to verify your understanding of this chapter.</p>
                            <p style="color: #fca5a5; font-size: 0.9rem;">⚠️ Note: You can only take this quiz once!</p>
                        </div>
                     """, unsafe_allow_html=True)
                     if st.button("Start Quiz 📝", key=f"start_{idx}"):
                         st.session_state[quiz_key] = True
                         st.rerun()
                 else:
                     with st.form(key=f"quiz_form_{idx}"):
                         user_answers = {}
                         for i, q in enumerate(content['quiz']):
                             st.write(f"**Q{i+1}: {q['question']}**")
                             user_detail = st.radio(
                                 "Select Answer:", 
                                 q['options'], 
                                 key=f"q_{idx}_{i}", 
                                 index=None, 
                                 label_visibility="collapsed"
                             )
                             user_answers[str(i)] = user_detail # Store as string keys
    
                         submitted = st.form_submit_button("Submit Answers 🚀")
                         
                         if submitted:
                             # Validate all answered?
                             if len(user_answers) < len(content['quiz']):
                                 st.warning("Please answer all questions before submitting.")
                             else:
                                 with st.spinner("Submitting quiz..."):
                                     try:
                                         payload = {
                                             "chapter_id": chapter['id'],
                                             "course_id": st.session_state['course_id'],
                                             "answers": user_answers
                                         }
                                         res = requests.post(f"{API_URL}/quizzes/submit", json=payload, headers=utils.get_auth_headers())
                                         
                                         if res.status_code == 200:
                                             data = res.json()
                                             st.session_state[result_key] = data
                                             st.balloons()
                                             st.success("Quiz submitted successfully!")
                                             time.sleep(2)
                                             st.rerun()
                                         elif res.status_code == 400:
                                             st.error(res.json().get('detail', 'Submission failed'))
                                         else:
                                             st.error("An error occurred during submission.")
                                     except Exception as e:
                                         st.error(f"Error submitting quiz: {e}")

        with tab_notes:
            st.subheader("📒 Study Notes")
            st.write("Jot down key takeaways from this chapter.")
            
            note_content = st.text_area("Your Notes", height=200, key=f"note_area_{idx}")
            
            if st.button("Save Note 💾", key=f"save_note_{idx}"):
                if note_content:
                    try:
                        n_payload = {
                            "content": f"**{chapter['title']}**: {note_content}",
                            "course_id": st.session_state['course_id']
                        }
                        res = requests.post(f"{API_URL}/notes", json=n_payload, headers=utils.get_auth_headers())
                        if res.status_code == 200:
                            st.success("Note saved!")
                        else:
                            st.error("Failed to save note.")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Note cannot be empty.")


utils.render_footer()
