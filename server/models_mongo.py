
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise ValueError('Invalid ObjectId')
        return v

class UserModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    username: str
    email: Optional[str] = None  # Made optional to handle legacy data
    hashed_password: str
    role: str # "admin", "organization", "student", "parent"
    is_active: bool = True
    organization_id: Optional[str] = None # Reference to Organization _id
    parent_id: Optional[str] = None # Reference to User _id
    secret_id: Optional[str] = None # Unique ID for linking
    pending_parent_requests: List[str] = [] # List of parent User IDs requesting access

class MessageModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    sender_id: str
    receiver_id: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = False

class OrganizationModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    code: str

class CourseModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    topic: str
    grade_level: str
    roadmap_json: dict # Store as dict/json directly
    description: Optional[str] = None
    structure_type: str = "week"
    is_published: bool = False
    organization_id: Optional[str] = None
    user_id: Optional[str] = None # Creator

class ChapterModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    chapter_number: int
    order_index: int = 0
    title: str
    content_markdown: str
    quiz_json: list
    video_url: Optional[str] = None
    course_id: str 

class NoteModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    user_id: str
    course_id: Optional[str] = None

class EnrollmentModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    course_id: str
    progress: float = 0.0
    joined_at: datetime = Field(default_factory=datetime.utcnow)

class TestResultModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    score: float
    total_score: float
    timestamp: float
    proctor_logs: dict
    user_id: str
    course_id: Optional[str] = None

class QuizResultModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    chapter_id: str
    course_id: str
    score: int
    total_questions: int
    answers: dict # Map of question_index (str) -> selected_option (str)
    question_details: List[dict] = [] # [{question, selected_answer, is_correct}]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
