from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, Float, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from server.database import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    code = Column(String, unique=True, index=True) # Unique code for students to join
    
    users = relationship("User", back_populates="organization")
    courses = relationship("Course", back_populates="organization")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String) # "admin", "organization", "student", "parent"
    is_active = Column(Boolean, default=True)
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    organization = relationship("Organization", back_populates="users")
    
    # Relationships
    courses = relationship("Course", back_populates="student")
    test_results = relationship("TestResult", back_populates="student")
    test_results = relationship("TestResult", back_populates="student")
    notes = relationship("Note", back_populates="user")
    enrollments = relationship("Enrollment", back_populates="student")
    
    # Parent-Child relationship (Self-referential)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    children = relationship("User", backref="parent", remote_side=[id])

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    grade_level = Column(String)
    roadmap_json = Column(JSON) # Store the generated roadmap structure
    
    description = Column(Text, nullable=True)
    structure_type = Column(String, default="week") # "week", "day", "module"
    is_published = Column(Boolean, default=False)
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    organization = relationship("Organization", back_populates="courses")
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Creator (if student) or Org Admin
    student = relationship("User", back_populates="courses")
    chapters = relationship("Chapter", back_populates="course", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="course")
    enrollments = relationship("Enrollment", back_populates="course")

class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    score = Column(Float)
    total_score = Column(Float)
    timestamp = Column(Float)
    proctor_logs = Column(JSON) # Store proctoring data/alerts
    
    user_id = Column(Integer, ForeignKey("users.id"))
    student = relationship("User", back_populates="test_results")
    
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)

class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    chapter_number = Column(Integer)
    order_index = Column(Integer, default=0)
    title = Column(String)
    content_markdown = Column(Text)
    quiz_json = Column(JSON)
    video_url = Column(String, nullable=True)
    
    course_id = Column(Integer, ForeignKey("courses.id"))
    course = relationship("Course", back_populates="chapters")

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="notes")
    
    # Set to NULL if course is deleted
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    course = relationship("Course", back_populates="notes")

class Enrollment(Base):
    __tablename__ = "enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    progress = Column(Float, default=0.0)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
