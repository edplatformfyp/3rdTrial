<<<<<<< HEAD
# EduCore - AI Learning Platform

## Overview
EduCore is a headless, zero-cost AI learning and proctoring engine built with FastAPI, Streamlit, and autonomous agents.

## Setup

1. **Environment Variables**:
   Current directory has a `.env` file. Fill in your API keys:
   ```
   GROQ_API_KEY=...
   GEMINI_API_KEY=...
   ```

2. **Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: For MediaPipe/OpenCV, ensure you have necessary system libraries if on Linux. On Windows, wheels should work.*

## Running the Application

You need two terminals to run the platform (Frontend and Backend).

**Terminal 1 (Backend):**
```bash
python server/main.py
```
*Server runs on http://localhost:8000*

**Terminal 2 (Frontend):**
```bash
streamlit run client/app.py
```
*Frontend runs on http://localhost:8501*

## System Architecture

- **server/agents/**: Contains the logic for Planner, Content, Proctor, and Media agents.
- **server/shared/**: Pydantic models shared across the app.
- **client/**: Dumb terminal frontend logic.

## Usage

1. Open the Streamlit app.
2. Enter a Topic and Grade.
3. Click "Generate Course".
4. The Planner Agent creates a roadmap (Console logs show progress).
5. The Content Agent generates the first chapter.
6. (Stub) Media agent video generation is available in code but not connected to the UI flow in this MVP to save time.
=======
# firstTrial
>>>>>>> 8fbd2f33007d81ef6d72f7bea48a234fbf1539d7
