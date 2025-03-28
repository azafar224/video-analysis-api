from fastapi import FastAPI, File, UploadFile, HTTPException
import google.generativeai as genai
import os
import time

app = FastAPI()

# Configure Google Gemini API
genai.configure(api_key="AIzaSyBfLy0FDAKNvMBsvC7hf1_U8sEmqMvk2X8")
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# Constants
UPLOAD_FOLDER = "uploads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB in bytes
MAX_RETRIES = 30  # Max attempts to check upload status
WAIT_TIME = 5  # Wait time between attempts

# Create an uploads folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def check_file_size(file_size: int):
    """Ensure file size is within the allowed limit."""
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File size exceeds 100MB limit.")

def wait_for_video_ready(video, retries=MAX_RETRIES, wait_time=WAIT_TIME):
    """Wait until the uploaded video is marked as 'READY'."""
    for attempt in range(retries):
        status = video.state
        print(f"⏳ Checking upload status (Attempt {attempt+1}): {status}")

        if status == "ACTIVE" or status == 2:
            print("✅ Video is ready for analysis!")
            return True
        
        time.sleep(wait_time)
    
    raise HTTPException(status_code=500, detail="Video did not become ready in time.")

@app.post("/analyze-video/")
async def analyze_video(file: UploadFile = File(...)):
    """Handles video upload, waits for readiness, then analyzes it."""
    video_path = os.path.join(UPLOAD_FOLDER, file.filename)

    # Check file size before saving
    check_file_size(file.size)

    # Save the uploaded file
    with open(video_path, "wb") as buffer:
        buffer.write(await file.read())

    print(f"✅ Video saved: {video_path}")

    # Upload video to Gemini AI
    video = genai.upload_file(video_path)

    # Wait for the video to be ready
    wait_for_video_ready(video)

    # Generate structured analysis
    response = model.generate_content([
        {"file": video},
        {"text": "Analyze this video and provide structured output in the format:\n"
                 "Engagement Score: [score out of 10]\n"
                 "Hook Score: [score out of 10]\n"
                 "Strengths:\n- [point1]\n- [point2]\n"
                 "Weaknesses:\n- [point1]\n- [point2]\n"
                 "Suggestions for Improvement:\n- [point1]\n- [point2]\n"
                 "Ensure no section is repeated."}
    ])

    return {"analysis": response.text}
