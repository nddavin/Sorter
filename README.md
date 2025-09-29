# Sorter: Multimedia Processor API

A production-ready, containerized, and fully tested multimedia processing API. This project handles file uploads (PDF, DOCX, audio, video), extracts/analyses their content, stores results in a database, and exposes REST endpoints for retrieval.

---

## 1. Overview

**Purpose:**

* Automate processing of various file types (text, audio transcription, video placeholders)
* Provide an API to upload, process, and fetch results
* Support bulk processing (CLI) and database persistence
* Enable CI/CD and Docker-based deployment

---

## 2. Project Structure

```
sorter/
├── api.py             # FastAPI routes (upload, list, retrieve)
├── config.py          # App configuration (database URL, upload path)
├── factory.py         # DB session and app factory setup
├── main.py            # FastAPI entry point
├── media_usage.py     # CLI tool for bulk file processing
├── models.py          # SQLAlchemy ORM models
├── processors.py      # Core file processing functions
├── seed_admin.py      # Seed script for populating DB with sample files
├── uploads/           # Directory for uploaded files
├── tests/             # Pytest-based automated tests
│   └── test_api.py
├── Dockerfile         # Production-ready container definition
├── .dockerignore      # Excluded files from image build
├── requirements.txt   # Dependencies
└── .github/workflows/ci.yml  # GitHub Actions CI/CD pipeline
```

---

## 3. Key Components

### **config.py**

* Centralizes configuration (DB URL, upload folder)
* Ensures upload directory exists
* Reads from `.env` if present

### **factory.py**

* Creates SQLAlchemy engine, session, and base
* Provides `get_db()` dependency for FastAPI

### **models.py**

* Defines `ProcessedFile` model with:

  * `id` (PK)
  * `file_type` (pdf, audio, video, unknown)
  * `content` (text transcription or extracted text)

### **processors.py**

* `process_file_auto(path)` detects file type and dispatches:

  * PDF → extract text
  * DOCX → extract text
  * Audio → transcribe (placeholder for speech-to-text engine)
  * Video → placeholder (metadata extraction)
* Returns standardized dictionary `{"type": ..., "content": ...}`

### **api.py**

* `POST /api/process-file/` → upload + process file + save to DB
* `GET /api/processed-files/` → list processed files
* `GET /api/processed-files/{id}` → fetch single processed file

### **media_usage.py**

* CLI utility for processing all files in `uploads/` folder
* Saves results to DB in bulk

### **seed_admin.py**

* Helps populate DB with sample data after migration

### **tests/test_api.py**

* Uses `pytest` + `TestClient`
* Covers upload, DB persistence, list & fetch endpoints
* Uses temporary SQLite DB for isolation

### **Dockerfile**

* Multi-stage build for optimized image size
* Installs system packages for media processing
* Runs `uvicorn` server inside container

### **GitHub Actions CI/CD**

* Runs tests on every push/PR to `main`
* Builds & pushes Docker image to Docker Hub
* (Optional) Deploys container to production server

---

## 4. Setup & Usage

### **1. Local Development**

```bash
# Clone repo
 git clone <repo-url>
 cd sorter

# Install dependencies
 pip install -r requirements.txt

# Run migrations (if using Alembic)
 alembic upgrade head

# Start API
 uvicorn main:app --reload
```

Visit: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### **2. Bulk Processing**

```bash
python media_usage.py
```

### **3. Seeding Sample Data**

```bash
python seed_admin.py
```

### **4. Run Tests**

```bash
pytest -v --cov=. --cov-report=term-missing
```

### **5. Docker Build & Run**

```bash
docker build -t sorter:latest .
docker run -p 8000:8000 sorter:latest
```

### **6. CI/CD**

* Every push runs tests automatically
* If successful, builds & pushes Docker image to Docker Hub
* Can auto-deploy to production server

---

## 5. Deployment Options

* **Docker Hub + VPS:** Pull and run latest container on server
* **Docker Compose:** (Optional) Run API + DB locally for dev/testing
* **Kubernetes:** Deploy via Helm chart or manifest

---

## 6. Future Improvements

* Real speech-to-text integration (Whisper / Vosk)
* Video metadata & frame analysis
* Authentication & user-specific storage
* Pagination & filtering for results endpoint
* Web UI dashboard

---

## 7. License

MIT License — Open for modification and deployment.
