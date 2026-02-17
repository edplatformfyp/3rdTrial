import requests
import time

API_URL = "http://localhost:8000"

def test_parental_flow():
    # 1. Register Parent & Child
    ts = str(int(time.time()))
    parent_user = f"parent_{ts}"
    child_user = f"child_{ts}"
    pwd = "password123"
    
    # Register Parent
    try:
        requests.post(f"{API_URL}/auth/register", json={
            "username": parent_user,
            "email": f"{parent_user}@example.com",
            "password": pwd,
            "role": "parent"
        })
    except: pass
    
    # Register Child
    try:
        requests.post(f"{API_URL}/auth/register", json={
            "username": child_user,
            "email": f"{child_user}@example.com",
            "password": pwd,
            "role": "student"
        })
    except: pass
    
    # Login Parent
    res_p = requests.post(f"{API_URL}/auth/token", data={"username": parent_user, "password": pwd})
    token_p = res_p.json()["access_token"]
    headers_p = {"Authorization": f"Bearer {token_p}"}
    
    # Login Child
    res_c = requests.post(f"{API_URL}/auth/token", data={"username": child_user, "password": pwd})
    token_c = res_c.json()["access_token"]
    headers_c = {"Authorization": f"Bearer {token_c}"}
    
    # Get Child Profile for Secret ID
    profile_c = requests.get(f"{API_URL}/users/me", headers=headers_c).json()
    secret_id = profile_c["secret_id"]
    child_id = profile_c["id"]
    print(f"Child Secret ID: {secret_id}")
    
    # 2. Link Request
    print("Parent sending link request...")
    res = requests.post(f"{API_URL}/parent/link-request", params={"secret_id": secret_id}, headers=headers_p)
    if res.status_code == 200:
        print("Link request sent.")
    else:
        print(f"Link request failed: {res.text}")
        return

    # 3. Child Approves
    print("Child checking requests...")
    reqs = requests.get(f"{API_URL}/student/requests", headers=headers_c).json()
    if not reqs:
        print("No requests found!")
        return
        
    parent_id_from_req = reqs[0]["id"]
    print(f"Approving request from {parent_id_from_req}...")
    
    res = requests.post(f"{API_URL}/student/approve-request", params={"parent_id": parent_id_from_req}, headers=headers_c)
    if res.status_code == 200:
        print("Request approved.")
    else:
        print(f"Approval failed: {res.text}")
        return
        
    # 4. Parent Checks Dashboard
    print("Parent fetching children...")
    children = requests.get(f"{API_URL}/parent/children", headers=headers_p).json()
    if any(c['username'] == child_user for c in children):
        print("Verified: Child is linked.")
    else:
        print("Error: Child not found in parent list.")
        return
        
    # 5. Parent Assigns Course
    print("Parent assigning course...")
    course_payload = {"topic": "Parental Math", "grade_level": "Grade 8"}
    res = requests.post(f"{API_URL}/courses/generate-for-child", params={"child_id": child_id}, json=course_payload, headers=headers_p)
    if res.status_code == 200:
        print("Course assigned.")
    else:
        print(f"Assign failed: {res.text}")
        
    # 6. Parent Sends Message
    print("Parent sending message...")
    res = requests.post(f"{API_URL}/parent/message", params={"receiver_id": child_id, "content": "Hello Child!"}, headers=headers_p)
    if res.status_code == 200:
        print("Message sent.")
        
    # 7. Child Checks Messages
    print("Child checking messages...")
    msgs = requests.get(f"{API_URL}/student/messages", headers=headers_c).json()
    if any(m['content'] == "Hello Child!" for m in msgs):
        print("Verified: Child received message.")
    else:
        print("Error: Message not received.")

if __name__ == "__main__":
    test_parental_flow()
