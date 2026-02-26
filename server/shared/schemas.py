
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
    progress: float = 0.0


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
    title: str
    content: str
    course_id: Optional[str] = None
    chapter_id: Optional[str] = None
    note_type: str = "text" # text, sketch
    metadata: Optional[dict] = None # For sketch data or other props

class NoteResponse(BaseModel):
    id: str # MongoDB uses str for IDs
    title: str
    content: str
    course_id: Optional[str]
    chapter_id: Optional[str]
    note_type: str
    metadata: Optional[dict]
    created_at: str
    updated_at: Optional[str]
    topic: Optional[str] = None # Course Name
    chapter_title: Optional[str] = None # Chapter Name

# --- Org Dashboard Schemas ---

class OrgCourseCreate(BaseModel):
    title: str
    grade_level: str
    description: str
    structure_type: str = "week" # week, day, module
    price: float = 0.0  # 0 = free
    thumbnail_url: Optional[str] = None

class CourseEnroll(BaseModel):
    course_id: str
    access_key: Optional[str] = None

class CourseKeyCreate(BaseModel):
    count: int = 1

class CourseKeyResponse(BaseModel):
    key: str
    course_id: str
    is_used: bool
    used_by_student_name: Optional[str] = None
    created_at: str

# --- Mock Payment & Order Schemas ---
class OrderCreate(BaseModel):
    course_id: str

class OrderResponse(BaseModel):
    id: str
    order_id: str
    user_id: str
    course_id: str
    amount: float
    status: str
    payment_session_id: str
    payment_reference_id: Optional[str] = None
    created_at: str
    updated_at: str
    username: Optional[str] = None
    course_topic: Optional[str] = None

class VerificationAction(BaseModel):
    action: str # "approve" or "reject"

class TokenActivateRequest(BaseModel):
    token_value: str
    signature: str

class PendingTokenResponse(BaseModel):
    course_id: str
    course_topic: str
    token_value: str
    signature: str
    expiry_date: str

class OrgModuleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    order_index: int

class StudentStat(BaseModel):
    student_id: str
    student_name: str
    enrolled_courses: int
    avg_progress: float
    avg_score: float

class CourseStat(BaseModel):
    course_id: str
    topic: str
    enrolled_students: int
    avg_progress: float
    avg_score: float

class OrgAnalyticsResponse(BaseModel):
    total_students: int
    active_courses: int
    avg_completion: float
    course_stats: List[CourseStat]
    student_stats: List[StudentStat]

class ModuleContentUpdate(BaseModel):
    title: Optional[str] = None
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

# --- Certificate Schemas ---

class CertificateTemplateUpdate(BaseModel):
    title_text: str = "Certificate of Completion"
    body_text: str = "has successfully completed the course"
    signature_text: str = ""
    bg_color: str = "#0a0a1a"
    text_color: str = "#ffffff"
    accent_color: str = "#00f3ff"
    font_style: str = "Orbitron"  # Orbitron, Rajdhani, serif, sans-serif
    logo_url: Optional[str] = None
    custom_bg_url: Optional[str] = None

# --- Final Exam Schemas ---

class ExamQuestion(BaseModel):
    id: str
    type: str # mcq, msq, tf, text
    question: str
    options: List[str] = []
    correct_answers: List[int] = [] # Indices of correct options
    points: int = 1

class ExamConfig(BaseModel):
    enabled: bool = False
    title: str = "Final Examination"
    description: str = "Proctored final exam for this course."
    time_limit_minutes: int = 60
    passing_score: int = 70 # Percentage
    max_attempts: int = 1
    questions: List[ExamQuestion] = []

class ExamSubmission(BaseModel):
    items: dict # question_id: answer (int or List[int] or str)
    proctor_logs: List[str] = []
    malpractice_count: int = 0
    time_taken_seconds: int = 0

class ExamResult(BaseModel):
    score: int
    total_points: int
    percentage: float
    passed: bool
    attempts: int
    malpractice_count: int
    credibility_score: int
    analysis: List[dict] # Detailed breakdown per question
    timestamp: str
