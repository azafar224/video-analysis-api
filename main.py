import os
import time
import concurrent.futures
import google.generativeai as genai
from flask import Flask, request, jsonify

# Configure Gemini API
genai.configure(api_key=os.getenv("AIzaSyBfLy0FDAKNvMBsvC7hf1_U8sEmqMvk2X8"))  # Store API key in environment variables
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# Constants
UPLOAD_FOLDER = "/tmp/uploads"  # Use /tmp to avoid read-only file system issues
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure upload folder exists

app = Flask(__name__)

def check_file_size(file_path):
    """Check file size and warn if it exceeds the 100MB limit."""
    size = os.path.getsize(file_path)
    if size > MAX_FILE_SIZE:
        print(f"Warning: {file_path} is {size / (1024 * 1024):.2f} MB, exceeding the 100MB limit.")
    return size

def upload_video(video_path):
    """Upload video to Gemini AI and wait for it to be ready."""
    print(f"🚀 Uploading {video_path}...")
    video = genai.upload_file(video_path)

    for _ in range(30):  # Max 30 attempts
        status = video.state
        print(f"⏳ Status: {status}")

        if status in ["ACTIVE", 2]:
            print(f"✅ {video_path} is ready!")
            return video

        time.sleep(5)  # Wait before retrying

    raise RuntimeError(f"❌ {video_path} did not become ready in time.")

def analyze_videos(video_paths):
    """Uploads videos and generates an analysis using Gemini AI."""
    uploaded_videos = {}
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_path = {executor.submit(upload_video, path): path for path in video_paths}
        for future in concurrent.futures.as_completed(future_to_path):
            path = future_to_path[future]
            try:
                uploaded_videos[path] = future.result()
            except Exception as exc:
                print(f"Error uploading {path}: {exc}")
    
    if len(uploaded_videos) != len(video_paths):
        return "Error: Some videos failed to upload."

    # Create prompt for Gemini AI
    prompt_lines = [
        "Analyze and compare the following videos:",
        "Provide structured feedback:",
        "Video [n] Engagement Score: [score]",
        "Video [n] Hook Score: [score]",
        "Strengths:\n- [point1]\n- [point2]",
        "Weaknesses:\n- [point1]\n- [point2]",
        "Suggestions:\n- [suggestion1]\n- [suggestion2]",
    ]
    
    # Add video references to the prompt
    for path in video_paths:
        prompt_lines.append(str(uploaded_videos[path]))  # Convert video object to string
    
    response = model.generate_content(prompt_lines)
    return response.text

@app.route("/upload", methods=["POST"])
def upload():
    """Handle video file upload and analysis."""
    if "video" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["video"]
    
    # Ensure file does not exceed size limit
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    check_file_size(file_path)

    # Perform analysis
    result = analyze_videos([file_path])

    return jsonify({"analysis": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
