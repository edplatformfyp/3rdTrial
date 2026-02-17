# How to Manually Start EduCore

You need to open **two separate terminal windows** (Command Prompt or PowerShell).

### Terminal 1: Backend (FastAPI)
Run this command from the `d:\Desktop\Learning Platfrom` folder:

```bash
python -m server.main
```

*Wait until you see "Application startup complete".*

### Terminal 2: Frontend (Streamlit)
Run this command from the same folder:

```bash
python -m streamlit run client/app.py
```

*This will automatically open your browser to http://localhost:8501*

### Notes
- If you see "ModuleNotFound", ensure you are in the root directory (`d:\Desktop\Learning Platfrom`).
- The Proctoring (Webcam) feature is currently disabled to prevent crashes.
