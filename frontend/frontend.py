from flask import Flask, request, render_template_string, redirect, url_for
import requests
import os

app = Flask(__name__)

# Backend service URL in Docker Compose network
BACKEND_URL = "http://backend:8000"

UPLOAD_FOLDER = "uploads"
SORTED_FOLDER = "sorted"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SORTED_FOLDER, exist_ok=True)

# Simple HTML template
HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Sorter App</title>
</head>
<body>
    <h1>File Sorter</h1>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload & Sort">
    </form>
    {% if sorted_file %}
    <h2>Sorted File Ready:</h2>
    <a href="{{ url_for('download_file', filename=sorted_file) }}">{{ sorted_file }}</a>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/upload", methods=["POST"])
def upload_file():
    uploaded_file = request.files.get("file")
    if uploaded_file:
        filepath = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
        uploaded_file.save(filepath)

        # Send file to backend for sorting
        with open(filepath, "rb") as f:
            files = {"file": (uploaded_file.filename, f)}
            response = requests.post(f"{BACKEND_URL}/sort", files=files)

        if response.status_code == 200:
            sorted_filename = response.json().get("sorted_file")
            return render_template_string(HTML_TEMPLATE, sorted_file=sorted_filename)
        else:
            return f"Error from backend: {response.text}", 500

    return "No file uploaded", 400

@app.route("/download/<filename>")
def download_file(filename):
    return redirect(f"{BACKEND_URL}/download/{filename}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
