from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
FRAMES_FOLDER = "frames"
PROCESSED_FRAMES = "processed_frames"
OUTPUT_VIDEO = "output.mp4"

# Ensure required directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FRAMES_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FRAMES, exist_ok=True)

@app.route("/")
def home():
    return "🚀 API is Running! Send a POST request with a video file to /run_rvrt"

@app.route("/run_rvrt", methods=["POST"])
def run_rvrt():
    try:
        # Receive video file from request
        if "video" not in request.files:
            return jsonify({"error": "No video file provided"}), 400
        
        video_file = request.files["video"]
        video_path = os.path.join(UPLOAD_FOLDER, "input_video.mp4")
        video_file.save(video_path)

        # Extract frames from the video using ffmpeg
        subprocess.run([
            "ffmpeg", "-i", video_path, "-vf", "fps=30", f"{FRAMES_FOLDER}/frame_%04d.png"
        ], check=True)

        # Run RVRT on the extracted frames
        command = [
            "python", "main_test_rvrt.py",
            "--task", "001_RVRT_videosr_bi_REDS_30frames",
            "--folder_lq", FRAMES_FOLDER,
            "--tile", "50", "64", "64",
            "--tile_overlap", "2", "10", "10",
            "--num_workers", "4",
            "--save_result"
        ]
        subprocess.run(command, check=True)

        # Reassemble processed frames into a new video
        subprocess.run([
            "ffmpeg", "-framerate", "30", "-i", f"{PROCESSED_FRAMES}/frame_%04d.png",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", OUTPUT_VIDEO
        ], check=True)

        return jsonify({"message": "Processing complete", "output_video": OUTPUT_VIDEO})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)