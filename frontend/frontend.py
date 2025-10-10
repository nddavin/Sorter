import os
import requests
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Environment-configurable settings
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/tmp/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DEBUG = os.getenv("DEBUG", "false").lower() in ["1", "true", "yes"]
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 5000))

# Backend URLs inside Docker Compose network
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000/sort")
BACKEND_DOWNLOAD_URL = os.getenv("BACKEND_DOWNLOAD_URL", "http://backend:8000/download")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return {"status": "healthy"}

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return render_template("result.html", error="No file part"), 400

    file = request.files["file"]
    if file.filename == "":
        return render_template("result.html", error="No selected file"), 400

    # Secure the filename
    filename = secure_filename(file.filename)
    if not filename.lower().endswith(".txt"):
        return render_template("result.html", error="Only .txt files are allowed"), 400

    try:
        # Stream file directly to backend without temporary file
        response = requests.post(
            BACKEND_URL,
            files={"file": (filename, file.stream)},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        if "sorted_file" not in data:
            return render_template("result.html", error="Invalid response from backend")

        return render_template("result.html", sorted_file=data["sorted_file"])

    except requests.Timeout:
        return render_template("result.html", error="Backend request timed out. Please try again."), 504
    except requests.RequestException as e:
        return render_template("result.html", error=f"Backend request failed: {str(e)}"), 502
    except ValueError:
        return render_template("result.html", error="The backend returned malformed data"), 502

@app.route("/download/<filename>")
def download_file(filename):
    # Sanitize filename to prevent path traversal
    safe_filename = secure_filename(filename)

    try:
        response = requests.get(f"{BACKEND_DOWNLOAD_URL}/{safe_filename}", timeout=30)
        response.raise_for_status()
        return response.content, response.status_code, response.headers.items()
    except requests.Timeout:
        return "Backend request timed out", 504
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return "File not found", 404
        return f"Backend error: {e.response.status_code}", 502
    except requests.RequestException as e:
        return f"Backend request failed: {str(e)}", 502

if __name__ == "__main__":
    app.run(debug=DEBUG, host=HOST, port=PORT)
