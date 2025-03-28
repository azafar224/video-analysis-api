from fastapi import FastAPI, File, UploadFile
import google.generativeai as genai
import os

app = FastAPI()

# Configure Google Gemini API
genai.configure(api_key="YOUR_GEMINI_API_KEY")
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# Create an uploads folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/analyze-video/")
async def analyze_video(file: UploadFile = File(...)):
    """Handles video upload and analysis."""
    video_path = os.path.join(UPLOAD_FOLDER, file.filename)
    
    # Save the uploaded file
    with open(video_path, "wb") as buffer:
        buffer.write(await file.read())

    print(f"✅ Video saved: {video_path}")

    # Upload video to Gemini AI
    uploaded_video = genai.upload_file(video_path)

    # Generate structured analysis
    response = model.generate_content([
        {"file": uploaded_video}, 
        {"text": "Analyze this video and provide structured output in the format:\n"
                 "Engagement Score: [score out of 10]\n"
                 "Hook Score: [score out of 10]\n"
                 "Strengths:\n- [point1]\n- [point2]\n"
                 "Weaknesses:\n- [point1]\n- [point2]\n"
                 "Suggestions for Improvement:\n- [point1]\n- [point2]\n"
                 "Ensure no section is repeated."}
    ])

    return {"analysis": response.text}
