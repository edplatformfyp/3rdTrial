
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from server import auth, database_mongo, models_mongo
from server.shared import schemas
import logging
from bson import ObjectId
from typing import List, Optional

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="EduCore AI Platform (MongoDB)")

# Mount static files
static_dir = os.path.join(os.getcwd(), "client", "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Dependency
get_db = database_mongo.get_database

@app.get("/")
def read_root():
    return {"message": "EduCore AI Platform is Running with MongoDB"}

# --- Auth Routes ---
@app.post("/auth/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db = Depends(get_db)):
    user = db.users.find_one({"username": form_data.username})
    if not user or not auth.verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user["role"]}

@app.post("/auth/register", response_model=schemas.UserResponse) # Need to create UserResponse in schemas or models? Using simple dict for now or existing Schema
def register_user(user: schemas.UserCreate, db = Depends(get_db)):
    # Check if user exists
    if db.users.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    
    user_doc = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
        "role": user.role,
        "is_active": True,
        "organization_id": user.organization_code, # Logic to lookup org needed if code provided
        "parent_id": None,
        "secret_id": f"{user.username}-{str(datetime.utcnow().timestamp())[-4:]}".replace(".", "") # Simple unique ID
    }
    
    # If organization code provided, find org
    if user.organization_code:
        org = db.organizations.find_one({"code": user.organization_code})
        if org:
            user_doc["organization_id"] = str(org["_id"])
        else:
            # For now, ignore invalid code or raise error?
            pass

    result = db.users.insert_one(user_doc)
    new_user = db.users.find_one({"_id": result.inserted_id})
    
    return {
        "id": str(new_user["_id"]),
        "username": new_user["username"],
        "email": new_user["email"],
        "role": new_user["role"],
        "organization_id": new_user.get("organization_id")
    }

@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models_mongo.UserModel = Depends(auth.get_current_active_user), db = Depends(get_db)):
    
    # Check if secret_id is missing (legacy users)
    if not current_user.secret_id:
        new_secret_id = f"{current_user.username}-{str(datetime.utcnow().timestamp())[-4:]}".replace(".", "")
        db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$set": {"secret_id": new_secret_id}}
        )
        current_user.secret_id = new_secret_id

    # Convert UserModel back to response dict if needed, or Pydantic handles it
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "organization_id": current_user.organization_id,
        "secret_id": current_user.secret_id
    }

# --- Parent/Child Linking Routes ---

@app.post("/parent/link-request")
def request_link(secret_id: str, 
                 current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                 db = Depends(get_db)):
    
    if current_user.role != "parent":
        raise HTTPException(status_code=403, detail="Only parents can initiate link requests")
        
    student = db.users.find_one({"secret_id": secret_id, "role": "student"})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found with this Secret ID")
        
    if student.get("parent_id") == current_user.id:
        raise HTTPException(status_code=400, detail="Already linked to this student")
        
    # Add to pending requests if not already there
    if current_user.id not in student.get("pending_parent_requests", []):
        db.users.update_one(
            {"_id": student["_id"]},
            {"$push": {"pending_parent_requests": current_user.id}}
        )
        
    return {"message": "Link request sent to student"}

@app.get("/student/requests")
def get_pending_requests(current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                         db = Depends(get_db)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Role must be student")
        
    pending_ids = current_user.pending_parent_requests
    requests = []
    for pid in pending_ids:
        parent = db.users.find_one({"_id": ObjectId(pid)})
        if parent:
            requests.append({"id": str(parent["_id"]), "username": parent["username"], "email": parent["email"]})
            
    return requests

@app.post("/student/approve-request")
def approve_request(parent_id: str,
                    current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                    db = Depends(get_db)):
    
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Role must be student")
        
    if parent_id not in current_user.pending_parent_requests:
         raise HTTPException(status_code=404, detail="Request not found")
         
    # Link parent and clear requests
    db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {
            "parent_id": parent_id,
            "pending_parent_requests": [] 
        }}
    )
    
    # Also verify parent exists? Yes.
    
    return {"message": "Parent linked successfully"}

# --- Parent Dashboard Routes ---

@app.get("/parent/children")
def get_my_children(current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                    db = Depends(get_db)):
    if current_user.role != "parent":
        raise HTTPException(status_code=403, detail="Role must be parent")
        
    children_cursor = db.users.find({"parent_id": current_user.id})
    children = []
    for child in children_cursor:
        children.append({
            "id": str(child["_id"]),
            "username": child["username"],
            "email": child["email"]
        })
    return children

@app.get("/parent/child/{child_id}/progress")
def get_child_progress(child_id: str,
                       current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                       db = Depends(get_db)):
    
    # Verify child belongs to parent
    child = db.users.find_one({"_id": ObjectId(child_id), "parent_id": current_user.id})
    if not child:
        raise HTTPException(status_code=404, detail="Child not found or not linked")
        
    # Fetch Courses
    courses_cursor = db.courses.find({"user_id": child_id})
    courses = []
    for c in courses_cursor:
        courses.append({
            "topic": c["topic"],
            "grade_level": c["grade_level"],
            "status": "Active" # Mock
        })
        
    # Fetch Quiz Results
    quizzes_cursor = db.quiz_results.find({"user_id": child_id}).sort("timestamp", -1).limit(5)
    recent_quizzes = []
    total_score = 0
    quiz_count = 0
    
    for q in quizzes_cursor:
        recent_quizzes.append({
            "score": q["score"],
            "total": q["total_questions"],
            "timestamp": q["timestamp"],
            # Fetch Chapter Title?
            "chapter_id": q["chapter_id"]
        })
        total_score += (q["score"] / q["total_questions"]) * 100
        quiz_count += 1
        
    avg_score = int(total_score / quiz_count) if quiz_count > 0 else 0
    
    return {
        "courses": courses,
        "recent_quizzes": recent_quizzes,
        "average_score": avg_score,
        "courses_completed": len(courses) # Approximation
    }

# --- Actions (Message, etc) ---

@app.post("/courses/generate-for-child")
def generate_course_for_child(request: schemas.CourseRequest, 
                              child_id: str, # passed as query param or body? Let's use Query for simplicity or update schema. 
                              # Actually schema defines body. Let's add child_id to query param.
                              current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                              db = Depends(get_db)):
    
    if current_user.role != "parent":
        raise HTTPException(status_code=403, detail="Role must be parent")
        
    child = db.users.find_one({"_id": ObjectId(child_id), "parent_id": current_user.id})
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
        
    # Reuse generation logic but assign to child_id
    from server.agents.planner_agent.planner import PlannerAgent
    planner = PlannerAgent()
    roadmap = planner.generate_roadmap(request.topic, request.grade_level, request.structure_type)
    
    if not roadmap:
         raise HTTPException(status_code=500, detail="Failed to generate roadmap")
         
    course_doc = {
        "topic": request.topic,
        "grade_level": request.grade_level,
        "roadmap_json": roadmap.dict(),
        "structure_type": request.structure_type,
        "is_published": False,
        "user_id": child_id, # Assigned to Child
        "organization_id": child.get("organization_id")
    }
    
    result = db.courses.insert_one(course_doc)
    
    for i, chapter in enumerate(roadmap.chapters):
        chapter_doc = {
            "chapter_number": chapter.chapter_number,
            "order_index": i,
            "title": chapter.title,
            "description": getattr(chapter, "description", f"Chapter {chapter.chapter_number}: {chapter.title}"),
            "content_markdown": "",
            "quiz_json": [],
            "course_id": str(result.inserted_id)
        }
        db.chapters.insert_one(chapter_doc)
        
    return {"message": "Course assigned to child", "course_id": str(result.inserted_id)}


@app.post("/parent/message")
def send_message(receiver_id: str, content: str,
                 current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                 db = Depends(get_db)):
    
    # Basic validation: can only send to linked users?
    # For now, open or check relationship
    
    msg = {
        "sender_id": current_user.id,
        "receiver_id": receiver_id,
        "content": content,
        "timestamp": datetime.utcnow(),
        "is_read": False
    }
    db.messages.insert_one(msg)
    return {"message": "Message sent"}

@app.get("/student/messages")
def get_my_messages(current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                    db = Depends(get_db)):
    
    msgs = db.messages.find({"receiver_id": current_user.id}).sort("timestamp", -1)
    result = []
    for m in msgs:
        # Get sender name
        sender = db.users.find_one({"_id": ObjectId(m["sender_id"])})
        sender_name = sender["username"] if sender else "Unknown"
        
        result.append({
            "id": str(m["_id"]),
            "sender": sender_name,
            "content": m["content"],
            "timestamp": m["timestamp"],
            "is_read": m["is_read"]
        })
    return result

# --- Course Routes ---

@app.post("/courses/generate")
def generate_course(request: schemas.CourseRequest, 
                   current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                   db = Depends(get_db)):
    
    # 1. Call Planner Agent (Stubbed/integrated logic)
    # For MVP, we just create a placeholder course
    
    
    # 1. Call Planner Agent
    from server.agents.planner_agent.planner import PlannerAgent
    planner = PlannerAgent()
    roadmap = planner.generate_roadmap(request.topic, request.grade_level, request.structure_type)
    
    if not roadmap:
        raise HTTPException(status_code=500, detail="Failed to generate roadmap")

    course_doc = {
        "topic": request.topic,
        "grade_level": request.grade_level,
        "roadmap_json": roadmap.dict(),
        "structure_type": request.structure_type,
        "is_published": False,
        "user_id": current_user.id,
        "organization_id": current_user.organization_id
    }
    
    result = db.courses.insert_one(course_doc)
    
    # Create Chapters
    for i, chapter in enumerate(roadmap.chapters):
        chapter_doc = {
            "chapter_number": chapter.chapter_number,
            "order_index": i,
            "title": chapter.title,
            "description": getattr(chapter, "description", f"Chapter {chapter.chapter_number}: {chapter.title}"),
            "content_markdown": "", # To be generated
            "quiz_json": [],
            "course_id": str(result.inserted_id)
        }
        db.chapters.insert_one(chapter_doc)

    return {"message": "Course generation started", "course_id": str(result.inserted_id)}

@app.get("/courses", response_model=List[schemas.CourseResponse]) 
def get_courses(current_user: models_mongo.UserModel = Depends(auth.get_current_active_user), db = Depends(get_db)):
    # If student, return enrolled courses + public courses? 
    # For MVP, returning all courses created by user
    
    courses_cursor = db.courses.find({"user_id": current_user.id})
    courses = []
    for c in courses_cursor:
        courses.append({
            "id": str(c["_id"]),
            "topic": c["topic"],
            "grade_level": c["grade_level"],
            "status": "Ready" # Stub
        })
    return courses

@app.get("/courses/{course_id}")
def get_course_details(course_id: str, db = Depends(get_db)):
    course = db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    chapters_cursor = db.chapters.find({"course_id": course_id}).sort("order_index", 1)
    chapters = []
    for ch in chapters_cursor:
        chapters.append({
            "id": str(ch["_id"]),
            "title": ch["title"],
            "chapter_number": ch["chapter_number"],
            "description": ch.get("description", f"Chapter {ch['chapter_number']}: {ch['title']}"),
            "content_markdown": ch.get("content_markdown", "")
        })
        
    return {
        "id": str(course["_id"]),
        "topic": course["topic"],
        "roadmap": course["roadmap_json"],
        "chapters": chapters
    }

@app.delete("/courses/{course_id}")
def delete_course(course_id: str,
                  current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                  db = Depends(get_db)):
    
    # Check if course exists and belongs to user
    course = db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    if course["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this course")
    
    # Cascading Delete
    print(f"Deleting course {course_id} for user {current_user.id}")
    
    # 1. Delete Chapters
    res_chapters = db.chapters.delete_many({"course_id": course_id})
    print(f"Deleted {res_chapters.deleted_count} chapters")
    
    # 2. Delete Notes related to this course
    res_notes = db.notes.delete_many({"course_id": course_id})
    print(f"Deleted {res_notes.deleted_count} notes")
    
    # 3. Delete Quiz Results related to this course
    res_quizzes = db.quiz_results.delete_many({"course_id": course_id})
    print(f"Deleted {res_quizzes.deleted_count} quiz results")
    
    # 4. Delete the Course itself
    res_course = db.courses.delete_one({"_id": ObjectId(course_id)})
    print(f"Deleted {res_course.deleted_count} courses (ObjectId)")
    
    deleted_count = res_course.deleted_count
    method = "ObjectId"

    if deleted_count == 0:
        print(f"WARNING: Course {course_id} was NOT deleted from DB with ObjectId!")
        # Try string ID just in case (legacy data?)
        res_course_str = db.courses.delete_one({"_id": course_id})
        print(f"Deleted {res_course_str.deleted_count} courses (String ID)")
        if res_course_str.deleted_count > 0:
            deleted_count = res_course_str.deleted_count
            method = "String ID"
        else:
            # Check if it still exists
            check = db.courses.find_one({"_id": ObjectId(course_id)})
            if check:
                print(f"Course still exists: {check['_id']}")
            else:
                print("Course not found after delete_one (maybe already gone?)")
    
    return {
        "message": "Course deletion attempted",
        "deleted_chapters": res_chapters.deleted_count,
        "deleted_notes": res_notes.deleted_count,
        "deleted_quizzes": res_quizzes.deleted_count,
        "deleted_course_count": deleted_count,
        "deletion_method": method
    }

@app.post("/courses/{course_id}/chapters/{chapter_id}/generate")
def generate_chapter_content(course_id: str, chapter_id: str, 
                             current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                             db = Depends(get_db)):
    
    chapter = db.chapters.find_one({"_id": ObjectId(chapter_id), "course_id": course_id})
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
        
    # Check if content already exists to avoid re-generation (optional, but good for cost)
    if chapter.get("content_markdown"):
         return {
             "message": "Content already exists", 
             "content_markdown": chapter["content_markdown"],
             "quiz": chapter.get("quiz_json", [])
         }

    from server.agents.content_agent.content import ContentAgent
    content_agent = ContentAgent()
    
    # Create simple Chapter object for agent
    chapter_obj = schemas.Chapter(
        chapter_number=chapter["chapter_number"],
        title=chapter["title"],
        description=chapter.get("description", f"Chapter {chapter['chapter_number']}")
    )
    
    generated_content = content_agent.generate_chapter_content(chapter_obj)
    
    if not generated_content:
        raise HTTPException(status_code=500, detail="Failed to generate content")
        
    # Update Chapter in DB
    quiz_data = [q.dict() for q in generated_content.quiz]
    db.chapters.update_one(
        {"_id": ObjectId(chapter_id)},
        {"$set": {
            "content_markdown": generated_content.content_markdown,
            "quiz_json": quiz_data
        }}
    )
    
    return {
        "message": "Content generated successfully", 
        "content_markdown": generated_content.content_markdown,
        "quiz": quiz_data
    }

# --- Video Generation Route ---
class VideoRequest(BaseModel):
    topic: str
    content_markdown: str
    chapter_title: str

@app.post("/generate/video")
async def generate_video_summary(request: VideoRequest, current_user: models_mongo.UserModel = Depends(auth.get_current_active_user)):
    try:
        from server.agents.media_agent.media import MediaAgent
        media_agent = MediaAgent()
        
        # Correctly calling the async method generate_video
        video_path = await media_agent.generate_video(
            topic=request.topic,
            content_markdown=request.content_markdown
        )
        
        if not video_path:
             raise HTTPException(status_code=500, detail="Video generation failed")
             
        # video_path is returning a relative path like "/static/videos/..." from the agent.
        
        return {"video_url": video_path}
        
    except Exception as e:
        print(f"Video Generation Error: {e}")
        # import traceback
        # traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# --- Note Routes ---
@app.post("/notes", response_model=schemas.NoteResponse)
def create_note(note: schemas.NoteRequest,
                current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                db = Depends(get_db)):
    
    note_doc = {
        "content": note.content,
        "user_id": current_user.id,
        "course_id": note.course_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    result = db.notes.insert_one(note_doc)
    
    return {
        "id": str(result.inserted_id),
        "content": note.content,
        "course_id": note.course_id,
        "created_at": note_doc["created_at"],
        "updated_at": note_doc["updated_at"],
        "topic": "" # Todo: fetch course topic
    }

@app.get("/notes", response_model=List[schemas.NoteResponse])
def get_notes(course_id: Optional[str] = None,
              current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
              db = Depends(get_db)):
    
    filter_query = {"user_id": current_user.id}
    if course_id:
        filter_query["course_id"] = course_id
        
    notes_cursor = db.notes.find(filter_query).sort("updated_at", -1)
    notes = []
    
    for n in notes_cursor:
        # Fetch course topic if needed, for optimization maybe do a lookup or store topic in note
        topic = ""
        if n.get("course_id"):
            course = db.courses.find_one({"_id": ObjectId(n["course_id"])})
            if course:
                topic = course["topic"]

        notes.append({
            "id": str(n["_id"]),
            "content": n["content"],
            "course_id": n.get("course_id"),
            "created_at": n["created_at"] if isinstance(n["created_at"], str) else n["created_at"].isoformat(),
            "updated_at": n["updated_at"] if isinstance(n["updated_at"], str) else n["updated_at"].isoformat(),
            "topic": topic
        })
        
    return notes

@app.delete("/notes/{note_id}")
def delete_note(note_id: str,
                current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                db = Depends(get_db)):
    
    # Check if note exists and belongs to user
    note = db.notes.find_one({"_id": ObjectId(note_id)})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    if note["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this note")
        
    db.notes.delete_one({"_id": ObjectId(note_id)})
    
    return {"message": "Note deleted successfully"}


# --- Import remaining logic from previous main.py ---
# (Agent routes, specific functionality need to be ported)

# For now, let's ensure the migration is minimal but functional.
# --- Quiz Routes ---

@app.post("/quizzes/submit", response_model=schemas.QuizResultResponse)
def submit_quiz(submission: schemas.QuizSubmission, 
                current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                db = Depends(get_db)):
    
    # Check if already submitted
    existing = db.quiz_results.find_one({
        "user_id": current_user.id,
        "chapter_id": submission.chapter_id
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="You have already engaged in this quiz. One attempt only!")

    # Fetch chapter to get correct answers
    chapter = db.chapters.find_one({"_id": ObjectId(submission.chapter_id)})
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
        
    quiz_data = chapter.get("quiz_json", [])
    if not quiz_data:
        raise HTTPException(status_code=400, detail="No quiz available for this chapter")

    # Calculate Score
    score = 0
    total_questions = len(quiz_data)
    question_details = []
    
    for i, q in enumerate(quiz_data):
        # submission.answers is dict of { "0": "Option A", "1": "Option B" }
        # q['correct_answer'] is int index
        # q['options'] is list of strings
        
        user_ans = submission.answers.get(str(i)) # JSON keys are strings
        is_correct = False
        
        # Determine correctness
        if user_ans:
            correct_opt = q['options'][q['correct_answer']]
            if user_ans == correct_opt:
                score += 1
                is_correct = True
                
        # Store detailed breakdown (excluding options as requested)
        question_details.append({
            "question": q['question'],
            "selected_answer": user_ans,
            "is_correct": is_correct
        })

    # Create Result Record
    result_doc = {
        "user_id": current_user.id,
        "chapter_id": submission.chapter_id,
        "course_id": submission.course_id,
        "score": score,
        "total_questions": total_questions,
        "answers": submission.answers,
        "question_details": question_details,
        "timestamp": datetime.utcnow()
    }
    
    res = db.quiz_results.insert_one(result_doc)
    
    return {
        "id": str(res.inserted_id),
        "score": score,
        "total_questions": total_questions,
        "timestamp": result_doc["timestamp"].isoformat(),
        "chapter_id": submission.chapter_id,
        "answers": submission.answers
    }

@app.get("/quizzes/{chapter_id}/result", response_model=schemas.QuizResultResponse)
def get_quiz_result(chapter_id: str, 
                    current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                    db = Depends(get_db)):
    
    result = db.quiz_results.find_one({
        "user_id": current_user.id,
        "chapter_id": chapter_id
    })
    
    if not result:
        raise HTTPException(status_code=404, detail="No quiz result found")
        
    return {
        "id": str(result["_id"]),
        "score": result["score"],
        "total_questions": result["total_questions"],
        "timestamp": result["timestamp"].isoformat(),
        "chapter_id": result["chapter_id"],
        "answers": result["answers"]
    }


# --- Organization Dashboard Routes ---

@app.get("/org/courses")
def get_org_courses(current_user: models_mongo.UserModel = Depends(auth.get_current_active_user), db = Depends(get_db)):
    if current_user.role != "organization":
         raise HTTPException(status_code=403, detail="Role must be organization")
         
    # Fetch courses created by this org user
    courses_cursor = db.courses.find({"user_id": current_user.id})
    courses = []
    for c in courses_cursor:
        courses.append({
            "id": str(c["_id"]),
            "topic": c["topic"],
            "grade_level": c["grade_level"],
            "structure_type": c.get("structure_type", "week"),
            "description": c.get("description", "")
        })
    return courses

@app.post("/org/courses/create")
def create_org_course(course_data: schemas.OrgCourseCreate, 
                      current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                      db = Depends(get_db)):
    try:
        print(f"[CREATE_COURSE] User: {current_user.username}, Role: {current_user.role}")
        print(f"[CREATE_COURSE] Course Data: {course_data.dict()}")
        
        if current_user.role != "organization":
             print(f"[CREATE_COURSE] ERROR: Role check failed. Expected 'organization', got '{current_user.role}'")
             raise HTTPException(status_code=403, detail="Role must be organization")
             
        course_doc = {
            "topic": course_data.title, # Mapping title to topic
            "grade_level": course_data.grade_level,
            "description": course_data.description,
            "structure_type": course_data.structure_type,
            "is_published": False,
            "user_id": current_user.id,
            "organization_id": current_user.organization_id,
            "roadmap_json": {"topic": course_data.title, "chapters": []} # Empty roadmap initially
        }
        
        print(f"[CREATE_COURSE] Inserting course doc: {course_doc}")
        result = db.courses.insert_one(course_doc)
        print(f"[CREATE_COURSE] Success! Course ID: {str(result.inserted_id)}")
        return {"message": "Course created", "course_id": str(result.inserted_id)}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CREATE_COURSE] EXCEPTION: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Course creation failed: {str(e)}")

@app.post("/org/courses/{course_id}/plan")
def plan_org_course(course_id: str, request: schemas.CourseRequest,
                    current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                    db = Depends(get_db)):
    if current_user.role != "organization":
         raise HTTPException(status_code=403, detail="Role must be organization")
         
    # Verify ownership
    course = db.courses.find_one({"_id": ObjectId(course_id), "user_id": current_user.id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    from server.agents.planner_agent.planner import PlannerAgent
    planner = PlannerAgent()
    roadmap = planner.generate_roadmap(request.topic, request.grade_level, request.structure_type)
    
    if not roadmap:
         raise HTTPException(status_code=500, detail="Failed to generate roadmap")

    # Update Course
    db.courses.update_one(
        {"_id": ObjectId(course_id)},
        {"$set": {"roadmap_json": roadmap.dict()}}
    )
    
    # Create/Overwrite Chapters
    # First delete existing (simple approach for MVP re-planning)
    db.chapters.delete_many({"course_id": course_id})
    
    for i, chapter in enumerate(roadmap.chapters):
        chapter_doc = {
            "chapter_number": chapter.chapter_number,
            "order_index": i,
            "title": chapter.title,
            "description": getattr(chapter, "description", f"Chapter {chapter.chapter_number}: {chapter.title}"),
            "content_markdown": "",
            "quiz_json": [],
            "course_id": course_id
        }
        db.chapters.insert_one(chapter_doc)
        
    return roadmap.dict()

@app.get("/org/courses/{course_id}/modules/{module_id}")
def get_module_details(course_id: str, module_id: str,
                       current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                       db = Depends(get_db)):
    if current_user.role != "organization":
         raise HTTPException(status_code=403, detail="Role must be organization")
         
    chapter = db.chapters.find_one({"_id": ObjectId(module_id), "course_id": course_id})
    if not chapter:
        raise HTTPException(status_code=404, detail="Module not found")
        
    return {
        "id": str(chapter["_id"]),
        "title": chapter["title"],
        "content_markdown": chapter.get("content_markdown", ""),
        "video_url": chapter.get("video_url", ""),
        "quiz_json": chapter.get("quiz_json", [])
    }

@app.put("/org/courses/{course_id}/modules/{module_id}")
def update_module_content(course_id: str, module_id: str, update_data: schemas.ModuleContentUpdate,
                          current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                          db = Depends(get_db)):
    if current_user.role != "organization":
         raise HTTPException(status_code=403, detail="Role must be organization")

    update_fields = {}
    if update_data.content_markdown is not None:
        update_fields["content_markdown"] = update_data.content_markdown
    if update_data.video_url is not None:
        update_fields["video_url"] = update_data.video_url
    if update_data.quiz is not None:
        update_fields["quiz_json"] = [q.dict() for q in update_data.quiz]
        
    if not update_fields:
        return {"message": "No changes provided"}

    result = db.chapters.update_one(
        {"_id": ObjectId(module_id), "course_id": course_id},
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Module not found")
        
    return {"message": "Module updated"}

@app.post("/org/courses/{course_id}/modules")
def add_module(course_id: str, module_data: schemas.OrgModuleCreate,
               current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
               db = Depends(get_db)):
    if current_user.role != "organization":
         raise HTTPException(status_code=403, detail="Role must be organization")
         
    chapter_doc = {
        "chapter_number": 999, # Sort order handles position, number is label
        "order_index": module_data.order_index,
        "title": module_data.title,
        "description": module_data.description,
        "content_markdown": "",
        "quiz_json": [],
        "course_id": course_id
    }
    db.chapters.insert_one(chapter_doc)
    return {"message": "Module added"}

@app.get("/org/students")
def get_org_students(current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                     db = Depends(get_db)):
    if current_user.role != "organization":
         raise HTTPException(status_code=403, detail="Role must be organization")
         
    # Mock implementation: Fetch all students? Or students linked to Org?
    # Schema has 'organization_id' in User.
    students = db.users.find({"organization_id": current_user.organization_id, "role": "student"})
    
    # For now, return ALL students if org_id is not set strictly, or just all students for demo
    # But let's try to be specific if we can.
    # If current_user.organization_id is None (admin?), fetch all?
    # Let's fetch all students for now to populate the table.
    
    students_cursor = db.users.find({"role": "student"})
    enrollments = []
    
    for s in students_cursor:
        # Check enrollments (mock: assume enrolled in 1 course)
        enrollments.append({
            "student_name": s["username"],
            "course_id": "Math 101", # Stub
            "progress": 45.0, # Stub
            "joined_at": "2023-01-01"
        })
        
    return enrollments

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
