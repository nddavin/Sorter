import os
import tempfile
import requests
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Environment-configurable settings
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/tmp/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DEBUG = os.getenv("DEBUG", "false").lower() in ["1", "true", "yes"]
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 5000))

# Backend URL inside Docker Compose network
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000/sort")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Secure the filename
    filename = secure_filename(file.filename)
    if not filename.lower().endswith(".txt"):
        return jsonify({"error": "Only .txt files are allowed"}), 400

    # Save file temporarily
    temp_path = os.path.join(UPLOAD_FOLDER, filename)
    try:
        file.save(temp_path)

        # POST to backend
        with open(temp_path, "rb") as f:
            try:
                response = requests.post(
                    BACKEND_URL,
                    files={"file": f},
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                if "sorted_file" not in data or not data["sorted_file"]:
                    return jsonify({"error": "Backend did not return sorted file"}), 502

                return jsonify(data)

            except requests.Timeout:
                return jsonify({"error": "Backend request timed out"}), 504
            except requests.RequestException as e:
                return jsonify({"error": f"Backend request failed: {e}"}), 502
            except ValueError:
                return jsonify({"error": "Invalid JSON from backend"}), 502

    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    app.run(debug=DEBUG, host=HOST, port=PORT)
