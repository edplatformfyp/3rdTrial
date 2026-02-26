
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from server import auth, database_mongo, models_mongo
from server.shared import schemas
import logging
from bson import ObjectId
from typing import List, Optional

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import shutil
import uuid
import hmac
import hashlib

app = FastAPI(title="EduCore AI Platform (MongoDB)")

# CORS Configuration
origins = [
    "http://localhost:5173", # React Dev Server
    "http://localhost:5174", # React Dev Server (Alternative)
    "http://localhost:8501", # Streamlit (Legacy)
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(os.getcwd(), "client", "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Video uploads directory
videos_dir = os.path.join(static_dir, "videos")
os.makedirs(videos_dir, exist_ok=True)

# Cover image uploads directory
covers_dir = os.path.join(static_dir, "covers")
os.makedirs(covers_dir, exist_ok=True)

# Dependency
get_db = database_mongo.get_database

@app.get("/")
def read_root():
    return {"message": "EduCore AI Platform is Running with MongoDB"}

# --- Auth Routes ---

@app.post("/upload/video")
async def upload_video(file: UploadFile = File(...),
                       current_user: models_mongo.UserModel = Depends(auth.get_current_active_user)):
    # Validate file type
    allowed_types = ["video/mp4", "video/webm", "video/ogg", "video/avi", "video/mov", "video/quicktime", "video/x-msvideo"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Invalid file type: {file.content_type}. Allowed: mp4, webm, ogg, avi, mov")
    
    # Generate unique filename
    ext = os.path.splitext(file.filename)[1] or ".mp4"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(videos_dir, unique_name)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")
    finally:
        file.file.close()
    
    video_url = f"/static/videos/{unique_name}"
    return {"video_url": video_url, "filename": file.filename}

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
        course_id = str(c["_id"])
        
        # Calculate Progress
        total_chapters = db.chapters.count_documents({"course_id": course_id})
        
        # Get unique chapters completed (passed quiz)
        completed_chapters = len(db.quiz_results.distinct("chapter_id", {
            "course_id": course_id,
            "user_id": current_user.id
        }))
        
        progress = 0.0
        if total_chapters > 0:
            progress = (completed_chapters / total_chapters) * 100

        courses.append({
            "id": course_id,
            "topic": c["topic"],
            "grade_level": c["grade_level"],
            "status": "Ready",
            "progress": round(progress, 1),
            "source": "self"
        })
    
    # Also include enrolled org courses
    enrollments = db.enrollments.find({"user_id": current_user.id})
    for enr in enrollments:
        ec = db.courses.find_one({"_id": ObjectId(enr["course_id"])})
        if not ec:
            continue
        course_id = str(ec["_id"])
        total_chapters = db.chapters.count_documents({"course_id": course_id})
        completed_chapters = len(db.quiz_results.distinct("chapter_id", {
            "course_id": course_id,
            "user_id": current_user.id
        }))
        progress = 0.0
        if total_chapters > 0:
            progress = (completed_chapters / total_chapters) * 100
        courses.append({
            "id": course_id,
            "topic": ec["topic"],
            "grade_level": ec["grade_level"],
            "status": "Ready",
            "progress": round(progress, 1),
            "source": "enrolled"
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
        "thumbnail_url": course.get("thumbnail_url", ""),
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
                             force: bool = False,
                             current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                             db = Depends(get_db)):
    
    chapter = db.chapters.find_one({"_id": ObjectId(chapter_id), "course_id": course_id})
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
        
    # Check if content already exists to avoid re-generation (optional, but good for cost)
    if chapter.get("content_markdown") and not force:
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
@app.post("/notes", response_model=schemas.NoteResponse)
def create_note(note: schemas.NoteRequest,
                current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                db = Depends(get_db)):
    
    # Fetch Course Topic and Chapter Title for denormalization
    course_topic = ""
    chapter_title = ""
    
    if note.course_id:
        course = db.courses.find_one({"_id": ObjectId(note.course_id)})
        if course:
            course_topic = course["topic"]
            
    if note.chapter_id:
        chapter = db.chapters.find_one({"_id": ObjectId(note.chapter_id)})
        if chapter:
            chapter_title = chapter["title"]

    note_doc = {
        "title": note.title,
        "content": note.content,
        "user_id": current_user.id,
        "course_id": note.course_id,
        "chapter_id": note.chapter_id,
        "note_type": note.note_type,
        "metadata": note.metadata,
        "course_topic": course_topic,
        "chapter_title": chapter_title,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    result = db.notes.insert_one(note_doc)
    
    return {
        "id": str(result.inserted_id),
        "title": note.title,
        "content": note.content,
        "course_id": note.course_id,
        "chapter_id": note.chapter_id,
        "note_type": note.note_type,
        "metadata": note.metadata,
        "created_at": note_doc["created_at"],
        "updated_at": note_doc["updated_at"],
        "topic": course_topic,
        "chapter_title": chapter_title
    }

@app.get("/notes", response_model=List[schemas.NoteResponse])
def get_notes(course_id: Optional[str] = None,
              chapter_id: Optional[str] = None,
              current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
              db = Depends(get_db)):
    
    filter_query = {"user_id": current_user.id}
    if course_id:
        filter_query["course_id"] = course_id
    if chapter_id:
        filter_query["chapter_id"] = chapter_id
        
    notes_cursor = db.notes.find(filter_query).sort("updated_at", -1)
    notes = []
    
    for n in notes_cursor:
        # Backward compatibility for old notes without title/type
        notes.append({
            "id": str(n["_id"]),
            "title": n.get("title", "Untitled Note"),
            "content": n["content"],
            "course_id": n.get("course_id"),
            "chapter_id": n.get("chapter_id"),
            "note_type": n.get("note_type", "text"),
            "metadata": n.get("metadata"),
            "created_at": n["created_at"] if isinstance(n["created_at"], str) else n["created_at"].isoformat(),
            "updated_at": n["updated_at"] if isinstance(n["updated_at"], str) else n["updated_at"].isoformat(),
            "topic": n.get("course_topic", ""),
            "chapter_title": n.get("chapter_title", "")
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

@app.post("/upload/cover/{course_id}")
def upload_cover_image(course_id: str, file: UploadFile = File(...),
                       current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                       db = Depends(get_db)):
    if current_user.role != "organization":
        raise HTTPException(status_code=403, detail="Role must be organization")
    
    course = db.courses.find_one({"_id": ObjectId(course_id), "user_id": current_user.id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Validate image type
    allowed = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="File must be an image (JPEG, PNG, WebP, GIF)")
    
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{course_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(covers_dir, filename)
    
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    url_path = f"/static/covers/{filename}"
    db.courses.update_one({"_id": ObjectId(course_id)}, {"$set": {"thumbnail_url": url_path}})
    
    return {"message": "Cover uploaded", "thumbnail_url": url_path}

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
            "description": c.get("description", ""),
            "is_published": c.get("is_published", False),
            "price": c.get("price", 0)
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
            "price": course_data.price,
            "thumbnail_url": course_data.thumbnail_url or "",
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
    if update_data.title is not None:
        update_fields["title"] = update_data.title
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
         
    # Get next chapter number
    last = db.chapters.find_one({"course_id": course_id}, sort=[("chapter_number", -1)])
    next_num = (last["chapter_number"] + 1) if last else 1

    chapter_doc = {
        "chapter_number": next_num,
        "order_index": module_data.order_index,
        "title": module_data.title,
        "description": module_data.description,
        "content_markdown": "",
        "quiz_json": [],
        "course_id": course_id
    }
    db.chapters.insert_one(chapter_doc)
    return {"message": "Module added"}

@app.delete("/org/courses/{course_id}/modules/{module_id}")
def delete_module(course_id: str, module_id: str,
                 current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                 db = Depends(get_db)):
    if current_user.role != "organization":
         raise HTTPException(status_code=403, detail="Role must be organization")
         
    result = db.chapters.delete_one({"_id": ObjectId(module_id), "course_id": course_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Module not found")
    return {"message": "Module deleted"}

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

# --- Certificate Endpoints ---

# Cert logos/backgrounds directory
cert_assets_dir = os.path.join(static_dir, "cert_assets")
os.makedirs(cert_assets_dir, exist_ok=True)

@app.post("/org/courses/{course_id}/certificate-template")
def save_certificate_template(course_id: str, 
                               template: schemas.CertificateTemplateUpdate,
                               current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                               db = Depends(get_db)):
    if current_user.role != "organization":
        raise HTTPException(status_code=403, detail="Role must be organization")
    
    course = db.courses.find_one({"_id": ObjectId(course_id), "user_id": current_user.id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    template_data = template.dict()
    template_data["course_id"] = course_id
    template_data["org_id"] = current_user.id
    
    # Upsert: update if exists, create if not
    db.certificate_templates.update_one(
        {"course_id": course_id},
        {"$set": template_data},
        upsert=True
    )
    return {"message": "Certificate template saved"}

@app.get("/org/courses/{course_id}/certificate-template")
def get_certificate_template(course_id: str,
                              current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                              db = Depends(get_db)):
    template = db.certificate_templates.find_one({"course_id": course_id})
    if not template:
        # Return defaults
        return {
            "title_text": "Certificate of Completion",
            "body_text": "has successfully completed the course",
            "signature_text": "",
            "bg_color": "#0a0a1a",
            "text_color": "#ffffff",
            "accent_color": "#00f3ff",
            "font_style": "Orbitron",
            "logo_url": None,
            "custom_bg_url": None
        }
    
    return {
        "title_text": template.get("title_text", "Certificate of Completion"),
        "body_text": template.get("body_text", "has successfully completed the course"),
        "signature_text": template.get("signature_text", ""),
        "bg_color": template.get("bg_color", "#0a0a1a"),
        "text_color": template.get("text_color", "#ffffff"),
        "accent_color": template.get("accent_color", "#00f3ff"),
        "font_style": template.get("font_style", "Orbitron"),
        "logo_url": template.get("logo_url"),
        "custom_bg_url": template.get("custom_bg_url")
    }

@app.post("/upload/cert-logo/{course_id}")
def upload_cert_logo(course_id: str, file: UploadFile = File(...),
                     current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                     db = Depends(get_db)):
    if current_user.role != "organization":
        raise HTTPException(status_code=403, detail="Role must be organization")
    
    allowed = ["image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"]
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="File must be an image")
    
    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    filename = f"logo_{course_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(cert_assets_dir, filename)
    
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    url_path = f"/static/cert_assets/{filename}"
    db.certificate_templates.update_one(
        {"course_id": course_id},
        {"$set": {"logo_url": url_path, "course_id": course_id, "org_id": current_user.id}},
        upsert=True
    )
    return {"message": "Logo uploaded", "logo_url": url_path}

@app.post("/upload/cert-template/{course_id}")
def upload_cert_bg(course_id: str, file: UploadFile = File(...),
                   current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                   db = Depends(get_db)):
    if current_user.role != "organization":
        raise HTTPException(status_code=403, detail="Role must be organization")
    
    allowed = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="File must be an image (JPEG, PNG, WebP)")
    
    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    filename = f"certbg_{course_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(cert_assets_dir, filename)
    
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    url_path = f"/static/cert_assets/{filename}"
    db.certificate_templates.update_one(
        {"course_id": course_id},
        {"$set": {"custom_bg_url": url_path, "course_id": course_id, "org_id": current_user.id}},
        upsert=True
    )
    return {"message": "Certificate background uploaded", "custom_bg_url": url_path}


# --- Final Exam Endpoints ---

@app.post("/org/courses/{course_id}/exam-config")
def save_exam_config(course_id: str, config: schemas.ExamConfig,
                     current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                     db = Depends(get_db)):
    if current_user.role != "organization":
        raise HTTPException(status_code=403, detail="Role must be organization")
    
    course = db.courses.find_one({"_id": ObjectId(course_id), "user_id": current_user.id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Save exam config embedded in course or separate collection?
    # Separate collection is cleaner for grading logic
    db.exams.update_one(
        {"course_id": course_id},
        {"$set": {
            "course_id": course_id,
            "org_id": current_user.id,
            "config": config.dict()
        }},
        upsert=True
    )
    return {"message": "Exam configuration saved"}

@app.get("/org/courses/{course_id}/exam-config")
def get_exam_config_org(course_id: str,
                        current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                        db = Depends(get_db)):
    # Allow org to see full config including answers
    if current_user.role != "organization":
        raise HTTPException(status_code=403, detail="Role must be organization")
        
    exam = db.exams.find_one({"course_id": course_id})
    if not exam:
        return {"enabled": False, "questions": []}
    
    return exam["config"]

@app.get("/courses/{course_id}/exam")
def get_student_exam(course_id: str,
                     current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                     db = Depends(get_db)):
    # For students: hide correct answers
    exam = db.exams.find_one({"course_id": course_id})
    if not exam or not exam["config"].get("enabled", False):
        raise HTTPException(status_code=404, detail="No final exam for this course")
        
    # Check attempts
    attempts = db.exam_results.count_documents({
        "course_id": course_id, 
        "user_id": current_user.id
    })
    
    # If passed previously, maybe allow review but not retake? 
    # Logic: if passed, return status. If max attempts reached and failed, return status.
    # ideally we return the exam paper only if they can attempt it.
    
    # Strip answers
    config = exam["config"]
    safe_questions = []
    for q in config["questions"]:
        q_copy = q.copy()
        if "correct_answers" in q_copy:
            del q_copy["correct_answers"]
        safe_questions.append(q_copy)
        
    return {
        "title": config["title"],
        "description": config["description"],
        "time_limit_minutes": config["time_limit_minutes"],
        "questions": safe_questions,
        "max_attempts": config["max_attempts"],
        "attempts_used": attempts
    }

@app.post("/courses/{course_id}/exam/submit")
def submit_exam(course_id: str, submission: schemas.ExamSubmission,
                current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                db = Depends(get_db)):
    
    exam = db.exams.find_one({"course_id": course_id})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    config = exam["config"]
    if not config.get("enabled"):
        raise HTTPException(status_code=400, detail="Exam is disabled")
        
    # Check max attempts
    attempts = db.exam_results.count_documents({"course_id": course_id, "user_id": current_user.id})
    
    # Check if already passed
    passed_check = db.exam_results.find_one({"course_id": course_id, "user_id": current_user.id, "passed": True})
    if passed_check:
        raise HTTPException(status_code=400, detail="You have already passed this exam")
        
    if attempts >= config["max_attempts"]:
        raise HTTPException(status_code=400, detail="Max attempts reached")
        
    # Grading Logic
    total_score = 0
    total_points = 0
    analysis = []
    
    questions_map = {q["id"]: q for q in config["questions"]}
    
    for q_id, q_data in questions_map.items():
        total_points += q_data["points"]
        user_ans = submission.items.get(q_id)
        
        is_correct = False
        feedback = "Incorrect"
        
        # Grading based on type
        if q_data["type"] in ["mcq", "tf", "msq"]:
            correct_set = set(q_data["correct_answers"])
            # Normalize user_ans to list of ints
            if isinstance(user_ans, int): 
                user_set = {user_ans}
            elif isinstance(user_ans, list):
                user_set = set(user_ans)
            else:
                user_set = set()
            
            if user_set == correct_set:
                is_correct = True
                total_score += q_data["points"]
                feedback = "Correct"
        
        elif q_data["type"] == "text":
            # Simple keyword matching for MVP (or just mark as manual review needed?)
            # For now: auto-mark correct if not empty (placeholder) or exact match if keywords provided?
            # User requirement: "final output... complete analysis".
            # Let's assume manual grading not in scope for MVP automation -> mark as 0 or full?
            # Let's give points if length > 10 chars as a heuristic for now.
             if user_ans and len(str(user_ans)) > 10:
                 is_correct = True # Very naive
                 total_score += q_data["points"]
                 feedback = "Review Pending (Prov. Correct)"
        
        analysis.append({
            "question_id": q_id,
            "question": q_data["question"],
            "user_answer": user_ans,
            "correct": is_correct,
            "feedback": feedback
        })
        
    percentage = (total_score / total_points * 100) if total_points > 0 else 0
    passed = percentage >= config["passing_score"]
    
    credibility_score = max(0, 100 - (submission.malpractice_count * 10))
    
    # Auto-fail if malpractice count > 3?
    # User said "thrice the test automatically...". Does it mean auto-submit? Yes.
    # The frontend submits. Backend records it.
    
    result_doc = {
        "course_id": course_id,
        "user_id": current_user.id,
        "score": total_score,
        "total_points": total_points,
        "percentage": percentage,
        "passed": passed,
        "attempts": attempts + 1,
        "malpractice_count": submission.malpractice_count,
        "credibility_score": credibility_score,
        "analysis": analysis,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    db.exam_results.insert_one(result_doc)
    
    return {
        "score": total_score,
        "total_points": total_points,
        "percentage": percentage,
        "passed": passed,
        "attempts": attempts + 1,
        "malpractice_count": submission.malpractice_count,
        "credibility_score": credibility_score,
        "analysis": analysis,
        "timestamp": result_doc["timestamp"]
    }

@app.get("/courses/{course_id}/exam/result")
def get_last_exam_result(course_id: str,
                         current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                         db = Depends(get_db)):
    result = db.exam_results.find_one(
        {"course_id": course_id, "user_id": current_user.id},
        sort=[("timestamp", -1)]
    )
    if not result:
        raise HTTPException(status_code=404, detail="No exam result found")
    
    # helper to convert ObjectId if necessary (though result has no _id in schema usually)
    result["id"] = str(result["_id"])
    del result["_id"]
    return result

@app.get("/courses/{course_id}/certificate/check")
def check_certificate_eligibility(course_id: str,
                                   current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                                   db = Depends(get_db)):
    """Check if student has completed all quizzes AND passed exam if enabled."""
    total_chapters = db.chapters.count_documents({"course_id": course_id})
    
    # Quiz completion
    completed_quizzes = len(db.quiz_results.distinct("chapter_id", {
        "course_id": course_id,
        "user_id": current_user.id
    }))
    
    quiz_eligible = True
    if total_chapters > 0:
        quiz_eligible = completed_quizzes >= total_chapters
        
    # check exam
    exam_eligible = True
    exam = db.exams.find_one({"course_id": course_id})
    if exam and exam["config"].get("enabled"):
        # Check if passed
        passed = db.exam_results.find_one({
            "course_id": course_id,
            "user_id": current_user.id,
            "passed": True
        })
        if not passed:
            exam_eligible = False
            
    is_eligible = quiz_eligible and exam_eligible
    
    return {
        "eligible": is_eligible,
        "completed": completed_quizzes,
        "total": total_chapters,
        "exam_required": bool(exam and exam["config"].get("enabled")),
        "exam_passed": exam_eligible
    }

@app.get("/courses/{course_id}/certificate")
def get_certificate(course_id: str,
                    current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
                    db = Depends(get_db)):
    """Get certificate data if student is eligible."""
    # Re-use check logic
    eligibility = check_certificate_eligibility(course_id, current_user, db)
    if not eligibility["eligible"]:
        detail = "Course not completed."
        if not eligibility["exam_passed"] and eligibility["exam_required"]:
            detail += " Final Exam not passed."
        raise HTTPException(status_code=400, detail=detail)
    
    course = db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get org name
    creator = db.users.find_one({"_id": ObjectId(course["user_id"])})
    org_name = creator["username"] if creator else "Unknown Organization"
    
    # Get template
    template = db.certificate_templates.find_one({"course_id": course_id})
    if not template:
        template = {}
    
    # Check for existing certificate
    existing = db.certificates.find_one({
        "course_id": course_id,
        "user_id": current_user.id
    })
    
    if not existing:
        # Auto-issue certificate
        cert_doc = {
            "course_id": course_id,
            "user_id": current_user.id,
            "student_name": current_user.username,
            "course_name": course["topic"],
            "org_name": org_name,
            "issued_at": datetime.utcnow().isoformat(),
            "certificate_id": f"EDUCORE-{uuid.uuid4().hex[:8].upper()}"
        }
        db.certificates.insert_one(cert_doc)
        existing = cert_doc
    
    return {
        "certificate_id": existing.get("certificate_id", ""),
        "student_name": existing.get("student_name", current_user.username),
        "course_name": existing.get("course_name", course["topic"]),
        "org_name": existing.get("org_name", org_name),
        "issued_at": existing.get("issued_at", ""),
        "template": {
            "title_text": template.get("title_text", "Certificate of Completion"),
            "body_text": template.get("body_text", "has successfully completed the course"),
            "signature_text": template.get("signature_text", ""),
            "bg_color": template.get("bg_color", "#0a0a1a"),
            "text_color": template.get("text_color", "#ffffff"),
            "accent_color": template.get("accent_color", "#00f3ff"),
            "font_style": template.get("font_style", "Orbitron"),
            "logo_url": template.get("logo_url"),
            "custom_bg_url": template.get("custom_bg_url")
        }
    }

# --- Marketplace Endpoints ---

@app.get("/marketplace/courses")
def get_marketplace_courses(
    current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
    db = Depends(get_db)):
    """Browse all published org courses for the marketplace."""
    courses_cursor = db.courses.find({"is_published": True})
    
    # Get user's enrolled course IDs for badge
    enrolled_ids = set()
    if current_user.role == "student":
        for enr in db.enrollments.find({"user_id": current_user.id}):
            enrolled_ids.add(enr["course_id"])
    
    # Also treat self-created courses as owned
    for own in db.courses.find({"user_id": current_user.id}):
        enrolled_ids.add(str(own["_id"]))
    
    courses = []
    for c in courses_cursor:
        course_id = str(c["_id"])
        
        # Get org/creator name
        creator = db.users.find_one({"_id": ObjectId(c["user_id"])})
        org_name = creator["username"] if creator else "Unknown"
        
        # Module count
        module_count = db.chapters.count_documents({"course_id": course_id})
        
        courses.append({
            "id": course_id,
            "topic": c["topic"],
            "description": c.get("description", ""),
            "grade_level": c["grade_level"],
            "price": c.get("price", 0),
            "thumbnail_url": c.get("thumbnail_url", ""),
            "org_name": org_name,
            "module_count": module_count,
            "is_enrolled": course_id in enrolled_ids
        })
    
    return courses

@app.post("/marketplace/enroll")
def enroll_in_course(
    data: schemas.CourseEnroll,
    current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
    db = Depends(get_db)):
    """Student enrolls/purchases a course."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can enroll")
    
    # Check course exists and is published
    course = db.courses.find_one({"_id": ObjectId(data.course_id), "is_published": True})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or not published")
    
    # Check if already enrolled
    existing = db.enrollments.find_one({"user_id": current_user.id, "course_id": data.course_id})
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")
        
    # Check if course is paid and validate key
    if course.get("price", 0) > 0:
        if not data.access_key:
            raise HTTPException(status_code=400, detail="Access Key is required for paid courses.")
            
        key_doc = db.course_keys.find_one({"course_id": data.course_id, "key": data.access_key})
        if not key_doc:
            raise HTTPException(status_code=400, detail="Invalid Access Key.")
        if key_doc.get("is_used"):
            raise HTTPException(status_code=400, detail="This Access Key has already been used.")
            
        # Burn the key
        db.course_keys.update_one(
            {"_id": key_doc["_id"]},
            {"$set": {
                "is_used": True, 
                "used_by_student_name": current_user.username,
                "used_at": datetime.utcnow().isoformat()
            }}
        )
    
    # Also check if student owns this course (self-created)
    if course.get("user_id") == current_user.id:
        raise HTTPException(status_code=400, detail="You already own this course")
    
    # Create enrollment (simulated purchase)
    enrollment_doc = {
        "user_id": current_user.id,
        "course_id": data.course_id,
        "enrolled_at": datetime.utcnow().isoformat(),
        "progress": 0.0
    }
    db.enrollments.insert_one(enrollment_doc)
    
    return {"message": "Successfully enrolled", "course_id": data.course_id}

@app.put("/org/courses/{course_id}/publish")
def toggle_publish_course(
    course_id: str,
    current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
    db = Depends(get_db)):
    """Toggle publish status of a course."""
    if current_user.role != "organization":
        raise HTTPException(status_code=403, detail="Role must be organization")
    
    course = db.courses.find_one({"_id": ObjectId(course_id), "user_id": current_user.id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    new_status = not course.get("is_published", False)
    db.courses.update_one(
        {"_id": ObjectId(course_id)},
        {"$set": {"is_published": new_status}}
    )
    return {"message": f"Course {'published' if new_status else 'unpublished'}", "is_published": new_status}

@app.post("/org/courses/{course_id}/keys", response_model=List[schemas.CourseKeyResponse])
def generate_course_keys(
    course_id: str,
    data: schemas.CourseKeyCreate,
    current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
    db = Depends(get_db)):
    """Generate access keys for a course."""
    if current_user.role != "organization":
        raise HTTPException(status_code=403, detail="Only organizations can generate keys")
    
    course = db.courses.find_one({"_id": ObjectId(course_id), "user_id": current_user.id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or unauthorized")
    
    keys = []
    for _ in range(data.count):
        # Generate EDU-XXXX-XXXX
        key = f"EDU-{str(uuid.uuid4()).split('-')[0].upper()}-{str(uuid.uuid4()).split('-')[1].upper()}"
        key_doc = {
            "key": key,
            "course_id": course_id,
            "is_used": False,
            "used_by_student_name": None,
            "created_at": datetime.utcnow().isoformat()
        }
        db.course_keys.insert_one(key_doc)
        keys.append(key_doc)
        
    return keys

@app.get("/org/courses/{course_id}/keys", response_model=List[schemas.CourseKeyResponse])
def get_course_keys(
    course_id: str,
    current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
    db = Depends(get_db)):
    """Get all access keys for a course."""
    if current_user.role != "organization":
        raise HTTPException(status_code=403, detail="Only organizations can get keys")
        
    course = db.courses.find_one({"_id": ObjectId(course_id), "user_id": current_user.id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or unauthorized")
        
    # Return keys without ObjectId wrapping
    keys_cursor = db.course_keys.find({"course_id": course_id}).sort("created_at", -1)
    keys = []
    for k in keys_cursor:
        # Pydantic schema expects standard fields
        keys.append(schemas.CourseKeyResponse(**k))
    return keys

@app.get("/org/analytics", response_model=schemas.OrgAnalyticsResponse)
def get_org_analytics(current_user: models_mongo.UserModel = Depends(auth.get_current_active_user), db = Depends(get_db)):
    if current_user.role != "organization":
        raise HTTPException(status_code=403, detail="Only organizations can view analytics")
        
    courses = list(db.courses.find({"user_id": current_user.id}))
    course_ids = [str(c["_id"]) for c in courses]
    
    total_students = len(db.enrollments.distinct("user_id", {"course_id": {"$in": course_ids}}))
    active_courses = len([c for c in courses if c.get("is_published", False)])
    
    course_stats = []
    student_map = {}
    
    overall_progress_sum = 0
    overall_progress_count = 0
    
    for c in courses:
        cid = str(c["_id"])
        enrollments = list(db.enrollments.find({"course_id": cid}))
        
        c_progress_sum = 0
        c_score_sum = 0
        c_score_count = 0
        
        exam_results = list(db.exam_results.find({"course_id": cid}))
        total_chapters = db.chapters.count_documents({"course_id": cid})
        
        for e in enrollments:
            uid = e["user_id"]
            if uid not in student_map:
                u_doc = db.users.find_one({"_id": ObjectId(uid)})
                student_map[uid] = {
                    "student_name": u_doc["username"] if u_doc else "Unknown",
                    "enrolled_courses": 0,
                    "progress_sum": 0,
                    "score_sum": 0,
                    "score_count": 0
                }
            
            completed_quizzes = db.quiz_results.count_documents({"course_id": cid, "user_id": uid})
            progress = (completed_quizzes / total_chapters * 100) if total_chapters > 0 else 0
            progress = min(100.0, progress)
            
            student_exams = [xr for xr in exam_results if xr["user_id"] == uid]
            if student_exams:
                score = max([float(xr.get("percentage", 0)) for xr in student_exams])
            else:
                student_quizzes = list(db.quiz_results.find({"course_id": cid, "user_id": uid}))
                if student_quizzes:
                    q_scores = [(float(q.get("score", 0)) / float(q.get("total_questions", 1)) * 100) for q in student_quizzes if q.get("total_questions", 0) > 0]
                    score = sum(q_scores) / len(q_scores) if q_scores else 0
                else:
                    score = 0
                    
            c_progress_sum += progress
            if score > 0 or student_exams or completed_quizzes > 0:
                c_score_sum += score
                c_score_count += 1
                
                student_map[uid]["score_sum"] += score
                student_map[uid]["score_count"] += 1
                
            student_map[uid]["enrolled_courses"] += 1
            student_map[uid]["progress_sum"] += progress
            
            overall_progress_sum += progress
            overall_progress_count += 1
            
        c_avg_progress = c_progress_sum / len(enrollments) if enrollments else 0
        c_avg_score = c_score_sum / c_score_count if c_score_count > 0 else 0
        
        course_stats.append({
            "course_id": cid,
            "topic": c["topic"],
            "enrolled_students": len(enrollments),
            "avg_progress": c_avg_progress,
            "avg_score": c_avg_score
        })
        
    student_stats = []
    for uid, data in student_map.items():
        avg_p = data["progress_sum"] / data["enrolled_courses"] if data["enrolled_courses"] > 0 else 0
        avg_s = data["score_sum"] / data["score_count"] if data["score_count"] > 0 else 0
        student_stats.append({
            "student_id": str(uid),
            "student_name": data["student_name"],
            "enrolled_courses": data["enrolled_courses"],
            "avg_progress": avg_p,
            "avg_score": avg_s
        })
        
    avg_completion = overall_progress_sum / overall_progress_count if overall_progress_count > 0 else 0
    
    return {
        "total_students": total_students,
        "active_courses": active_courses,
        "avg_completion": avg_completion,
        "course_stats": course_stats,
        "student_stats": student_stats
    }


# --- Mock Payment & Secure Registration System ---

def get_hmac_signature(token_value: str) -> str:
    """Generate a secure HMAC SHA-256 signature for a token."""
    secret = auth.SECRET_KEY.encode('utf-8')
    return hmac.new(secret, token_value.encode('utf-8'), hashlib.sha256).hexdigest()

@app.post("/marketplace/orders/create", response_model=schemas.OrderResponse)
def create_order(
    data: schemas.OrderCreate,
    current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
    db = Depends(get_db)):
    """Initialize a mock payment order."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can create orders")
        
    course = db.courses.find_one({"_id": ObjectId(data.course_id), "is_published": True})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    if course.get("price", 0) <= 0:
        raise HTTPException(status_code=400, detail="Course is free, enroll directly")
        
    # Check existing access
    existing = db.enrollments.find_one({"user_id": current_user.id, "course_id": data.course_id})
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled")
        
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    payment_session_id = f"pi_mock_{uuid.uuid4().hex}"
    
    order_doc = {
        "order_id": order_id,
        "user_id": current_user.id,
        "course_id": data.course_id,
        "amount": course.get("price", 0),
        "status": "pending",
        "payment_session_id": payment_session_id,
        "payment_reference_id": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "ip_address": None # Capturing IP is tricky locally, skipping for prototype
    }
    
    res = db.orders.insert_one(order_doc)
    
    order_doc["id"] = str(res.inserted_id)
    return order_doc

@app.post("/marketplace/orders/{payment_session_id}/pay")
def simulate_payment(
    payment_session_id: str,
    current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
    db = Depends(get_db)):
    """Simulate user paying on the mock gateway."""
    order = db.orders.find_one({"payment_session_id": payment_session_id, "user_id": current_user.id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order["status"] != "pending":
        raise HTTPException(status_code=400, detail="Order already processed")
        
    payment_reference_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"
    
    db.orders.update_one(
        {"_id": order["_id"]},
        {"$set": {
            "status": "payment_submitted",
            "payment_reference_id": payment_reference_id,
            "updated_at": datetime.utcnow().isoformat()
        }}
    )
    
    return {"message": "Payment submitted, awaiting admin verification", "payment_reference_id": payment_reference_id}


@app.get("/org/orders", response_model=List[schemas.OrderResponse])
def get_org_orders(
    current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
    db = Depends(get_db)):
    """Get all orders for the organization's courses."""
    if current_user.role != "organization":
        raise HTTPException(status_code=403, detail="Only organizations can view orders")
        
    courses = list(db.courses.find({"user_id": current_user.id}))
    course_ids = [str(c["_id"]) for c in courses]
    
    orders = list(db.orders.find({"course_id": {"$in": course_ids}}).sort("created_at", -1))
    
    # Enrich with user and course info
    for o in orders:
        o["id"] = str(o["_id"])
        user = db.users.find_one({"_id": ObjectId(o["user_id"])})
        course = next((c for c in courses if str(c["_id"]) == o["course_id"]), None)
        o["username"] = user["username"] if user else "Unknown"
        o["course_topic"] = course["topic"] if course else "Unknown"
        
    return orders


@app.post("/org/orders/{order_id}/verify")
def verify_order(
    order_id: str,
    action_data: schemas.VerificationAction,
    current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
    db = Depends(get_db)):
    """Admin verifies and generates a secure token."""
    if current_user.role != "organization":
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    order = db.orders.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    # Verify org owns this course
    course = db.courses.find_one({"_id": ObjectId(order["course_id"]), "user_id": current_user.id})
    if not course:
        raise HTTPException(status_code=403, detail="Unauthorized for this course's orders")
        
    if action_data.action == "reject":
        db.orders.update_one({"_id": order["_id"]}, {"$set": {"status": "rejected", "updated_at": datetime.utcnow().isoformat()}})
        return {"message": "Order rejected"}
        
    if action_data.action == "approve":
        if order["status"] == "paid":
             raise HTTPException(status_code=400, detail="Order already approved")
             
        # Mark as paid
        db.orders.update_one({"_id": order["_id"]}, {"$set": {"status": "paid", "updated_at": datetime.utcnow().isoformat()}})
        
        # Generate Secure Token
        token_value = str(uuid.uuid4()) + uuid.uuid4().hex  # 32+ char random string
        signature = get_hmac_signature(token_value)
        expiry_date = datetime.utcnow() + timedelta(hours=24) # 24 hour expiry
        
        token_doc = {
            "token_value": token_value,
            "signature": signature,
            "user_id": order["user_id"],
            "course_id": order["course_id"],
            "is_used": False,
            "expiry_date": expiry_date.isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        db.enrollment_tokens.insert_one(token_doc)
        
        # Simulated Email / Output
        activation_link = f"/activate?token={token_value}&signature={signature}"
        logger.info(f"SIMULATED EMAIL TO USER: Your course is ready. Activation Link: {activation_link}")
        
        return {
            "message": "Order approved and token generated securely.",
            "activation_link": activation_link # Returning it for the UI prototype demo purposes
        }
        
    raise HTTPException(status_code=400, detail="Invalid action")


@app.post("/marketplace/activate")
def activate_secure_token(
    data: schemas.TokenActivateRequest,
    current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
    db = Depends(get_db)):
    """Student activates their secure token to enroll."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can enroll")
        
    # Rate Limiting & Signature parsing (prototype level)
    expected_signature = get_hmac_signature(data.token_value)
    if not hmac.compare_digest(data.signature, expected_signature):
        raise HTTPException(status_code=400, detail="Invalid token signature. Token tampered.")
        
    token_doc = db.enrollment_tokens.find_one({
        "token_value": data.token_value,
        "signature": data.signature,
        "user_id": current_user.id
    })
    
    if not token_doc:
        raise HTTPException(status_code=404, detail="Token not found or does not belong to you.")
        
    if token_doc["is_used"]:
        raise HTTPException(status_code=400, detail="Token has already been activated.")
        
    expiry = datetime.fromisoformat(token_doc["expiry_date"])
    if datetime.utcnow() > expiry:
        raise HTTPException(status_code=400, detail="Token has expired.")
        
    # Idempotent Atomic Update
    res = db.enrollment_tokens.update_one(
        {"_id": token_doc["_id"], "is_used": False},
        {"$set": {"is_used": True, "used_at": datetime.utcnow().isoformat()}}
    )
    
    if res.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to activate token. Possibly a duplicate request.")
        
    # Check if already enrolled
    existing = db.enrollments.find_one({"user_id": current_user.id, "course_id": token_doc["course_id"]})
    if existing:
        return {"message": "Successfully activated, but you were already enrolled."}
        
    # Create valid enrollment
    enrollment_doc = {
        "user_id": current_user.id,
        "course_id": token_doc["course_id"],
        "enrolled_at": datetime.utcnow().isoformat(),
        "progress": 0.0
    }
    db.enrollments.insert_one(enrollment_doc)
    
    return {"message": "Token activated successfully. You are now enrolled.", "course_id": token_doc["course_id"]}


@app.get("/marketplace/tokens/pending", response_model=List[schemas.PendingTokenResponse])
def get_pending_tokens(
    current_user: models_mongo.UserModel = Depends(auth.get_current_active_user),
    db = Depends(get_db)):
    """Get pending token activation links for a student."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can view pending tokens")
        
    now = datetime.utcnow().isoformat()
    # Find tokens that are not used and not expired
    tokens = list(db.enrollment_tokens.find({
        "user_id": current_user.id,
        "is_used": False,
        "expiry_date": {"$gt": now}
    }))
    
    result = []
    for t in tokens:
        course = db.courses.find_one({"_id": ObjectId(t["course_id"])})
        if course:
            result.append({
                "course_id": t["course_id"],
                "course_topic": course.get("topic", "Unknown Course"),
                "token_value": t["token_value"],
                "signature": t["signature"],
                "expiry_date": t["expiry_date"]
            })
            
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
