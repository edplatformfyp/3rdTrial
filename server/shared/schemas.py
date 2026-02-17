
from typing import List, Optional
from pydantic import BaseModel

# --- Course Generation Schemas ---

class CourseRequest(BaseModel):
    topic: str
    grade_level: str
    framework: Optional[str] = "General"  # e.g., "CBSE", "IGCSE", "General"
    structure_type: str = "week" # week, day, module

class CourseResponse(BaseModel):
    id: str
    topic: str
    grade_level: str
    status: Optional[str] = "Ready"


class Chapter(BaseModel):
    chapter_number: int
    title: str
    description: str

class CourseRoadmap(BaseModel):
    topic: str
    chapters: List[Chapter]

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: int  # Index of the correct option

class ChapterContent(BaseModel):
    chapter_title: str
    content_markdown: str
    quiz: List[QuizQuestion]

class ChapterRequest(BaseModel):
    chapter: Chapter
    topic: str
    grade_level: str

# --- Proctoring Schemas ---

class ProctorStatus(BaseModel):
    user_id: str
    attention_score: float  # 0.0 to 1.0
    is_looking_away: bool
    fraud_detected: bool
    timestamp: float

class NoteRequest(BaseModel):
    content: str
    course_id: Optional[str] = None # MongoDB uses str for IDs

class NoteResponse(BaseModel):
    id: str # MongoDB uses str for IDs
    content: str
    course_id: Optional[str]
    created_at: str
    updated_at: Optional[str]
    topic: Optional[str] = None # For display purposes

# --- Org Dashboard Schemas ---

class OrgCourseCreate(BaseModel):
    title: str
    grade_level: str
    description: str
    structure_type: str = "week" # week, day, module

class OrgModuleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    order_index: int

class ModuleContentUpdate(BaseModel):
    content_markdown: Optional[str] = None
    video_url: Optional[str] = None
    quiz: Optional[List[QuizQuestion]] = None

class EnrollmentResponse(BaseModel):
    id: str # MongoDB uses str for IDs
    user_id: str # MongoDB uses str for IDs
    course_id: str # MongoDB uses str for IDs
    progress: float
    student_name: str
    joined_at: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "student"
    organization_code: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    organization_id: Optional[str] = None
    secret_id: Optional[str] = None

class QuizSubmission(BaseModel):
    chapter_id: str
    course_id: str
    answers: dict

class QuizResultResponse(BaseModel):
    id: str
    score: int
    total_questions: int
    timestamp: str
    chapter_id: str
    answers: dict
