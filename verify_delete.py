import requests
import sys

API_URL = "http://localhost:8000"

def test_delete_flow():
    # 1. Login/Register
    username = "test_user_del"
    password = "password123"
    
    # Try register
    try:
        requests.post(f"{API_URL}/auth/register", json={
            "username": username,
            "email": "test_del@example.com",
            "password": password,
            "role": "student"
        })
    except:
        pass # Might exist
        
    # Login
    res = requests.post(f"{API_URL}/auth/token", data={
        "username": username,
        "password": password
    })
    
    if res.status_code != 200:
        print(f"Login failed: {res.text}")
        return
        
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Logged in successfully.")

    # 2. Create Course
    print("Creating dummy course...")
    course_res = requests.post(f"{API_URL}/courses/generate", headers=headers, json={
        "topic": "Delete Test",
        "grade_level": "Grade 8",
        "structure_type": "standard??" # Check schemas if needed, or if this arg is used
    })
    
    # The current generate endpoint might need structure_type or defaults. 
    # Let's check schemas.CourseRequest from previous file view...
    # schemas not fully viewed, but main.py uses request.structure_type
    
    if course_res.status_code != 200:
        # Maybe schema validation error?
        # Let's try with minimal payload if defaulting, or check error.
        print(f"Course creation failed: {course_res.text}")
        
        # Retry with likely valid payload based on common sense
        course_res = requests.post(f"{API_URL}/courses/generate", headers=headers, json={
            "topic": "Delete Test",
            "grade_level": "Grade 8",
            "structure_type": "Academic" 
        })
        
    if course_res.status_code != 200:
         print(f"Course creation failed retry: {course_res.text}")
         return

    course_id = course_res.json()["course_id"]
    print(f"Course created: {course_id}")
    
    # 3. Create Note
    print("Creating dummy note...")
    note_res = requests.post(f"{API_URL}/notes", headers=headers, json={
        "content": "This is a test note to be deleted.",
        "course_id": course_id
    })
    
    if note_res.status_code != 200:
        print(f"Note creation failed: {note_res.text}")
        return
        
    note_id = note_res.json()["id"]
    print(f"Note created: {note_id}")
    
    # 4. Verify Note Exists
    all_notes = requests.get(f"{API_URL}/notes", headers=headers).json()
    if not any(n['id'] == note_id for n in all_notes):
        print("Error: Note not found in list")
        return
        
    # 5. Delete Note
    print(f"Deleting note {note_id}...")
    del_note = requests.delete(f"{API_URL}/notes/{note_id}", headers=headers)
    if del_note.status_code == 200:
        print("Note deleted successfully.")
    else:
        print(f"Failed to delete note: {del_note.text}")
        
    # Verify Note Gone
    all_notes = requests.get(f"{API_URL}/notes", headers=headers).json()
    if any(n['id'] == note_id for n in all_notes):
        print("Error: Note still exists!")
    else:
        print("Verified: Note is gone.")
        
    # 6. Delete Course
    print(f"Deleting course {course_id}...")
    del_course = requests.delete(f"{API_URL}/courses/{course_id}", headers=headers)
    if del_course.status_code == 200:
        print("Course deleted successfully.")
        print(f"Debug Info: {del_course.json()}")
    else:
        print(f"Failed to delete course: {del_course.text}")
        
    # Verify Course Gone
    all_courses = requests.get(f"{API_URL}/courses", headers=headers).json()
    if any(c['id'] == course_id for c in all_courses):
         print("Error: Course still exists!")
    else:
         print("Verified: Course is gone.")

if __name__ == "__main__":
    test_delete_flow()
