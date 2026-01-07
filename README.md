# 🚀 **SORTER - Enterprise File Processing System**

## 🎯 **Enterprise-Grade File Processing & Sorting Platform**

A production-ready, enterprise-grade file processing system with advanced security, automation, and scalability features. Built for modern organizations requiring robust file management, intelligent sorting, and comprehensive workflow automation.

---

## ✨ **Key Features**

### 🔐 **Advanced Security & Authentication**
- **JWT-based Authentication** with refresh tokens and secure session management
- **Role-Based Access Control** (Admin/Manager/User) with granular permissions
- **Multi-layered Security** with input validation, sanitization, and encryption
- **File Content Scanning** for dangerous signatures and malware detection
- **Rate Limiting & Abuse Prevention** with configurable thresholds
- **Encrypted Storage** with access controls and audit trails
- **Complete Audit Trail** for compliance and forensic analysis

### 📁 **Comprehensive File Processing**
- **Multi-format Support**: 50+ formats across Documents, Images, Videos, Audio, Archives, Business Files, CAD, Medical, Geospatial, and more
- **Intelligent Metadata Extraction** with type-specific processing
- **Advanced Sorting Engine** with customizable rules and criteria
- **Background Processing** for heavy operations and performance optimization
- **File Conversion & Transformation** capabilities
- **Content Analysis** with text extraction and indexing

### 🤖 **Workflow Automation**
- **Automated Processing Pipelines** with conditional logic
- **Scheduled Tasks** using cron expressions and event triggers
- **Rule-based Sorting** with intelligent categorization
- **Batch Processing** for thousands of files
- **Event-driven Workflows** responding to system changes
- **Approval Workflows** with multi-level validation

### 📊 **Analytics & Monitoring**
- **Real-time Performance Metrics** and system health monitoring
- **Comprehensive Logging** with structured output and search capabilities
- **Usage Analytics** with detailed reporting and insights
- **Scalability Monitoring** with load balancing and optimization
- **Error Tracking** with Sentry integration and automated alerts

---

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SORTER PROCESSING PIPELINE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────┐    ┌──────────────┐ │
│  │  UPLOAD  │───▶│  VALIDATION  │───▶│  EXTRACTION   │───▶│   SORTING    │ │
│  └──────────┘    └──────────────┘    └───────────────┘    └──────────────┘ │
│       │               │                   │                      │          │
│       ▼               ▼                   ▼                      ▼          │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────┐    ┌──────────────┐ │
│  │   Queue  │    │  Security    │    │   Metadata    │    │    Rules     │ │
│  │  System  │    │   Checks     │    │   Extractors  │    │    Engine    │ │
│  └──────────┘    └──────────────┘    └───────────────┘    └──────────────┘ │
│                                                                              │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────┐                      │
│  │   AI/ML  │◀───│   Workflow   │◀───│  Storage      │                      │
│  │ Processor│    │   Engine     │    │  (Encrypted)  │                      │
│  └──────────┘    └──────────────┘    └───────────────┘                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 **Supported File Types**

| Category | Formats | Processing Capabilities |
|----------|---------|------------------------|
| **Documents** | PDF, DOCX, XLSX, PPTX, TXT, CSV | OCR, metadata, text extraction |
| **Images** | JPG, PNG, GIF, TIFF, WebP, RAW | EXIF, dimensions, OCR |
| **Videos** | MP4, AVI, MOV, MKV, WebM | Duration, codec, thumbnails |
| **Audio** | MP3, WAV, FLAC, AAC, OGG | ID3 tags, duration, waveform |
| **Archives** | ZIP, RAR, 7Z, TAR, GZ | Contents listing, extraction |
| **Business** | XLSX, PDF, CSV, XML | Invoice processing, data extraction |
| **CAD** | DWG, DXF, STEP, IGES | Entity count, BOM extraction |
| **Medical** | DICOM, HL7, PDF/A | Patient info, PHI detection |
| **Geospatial** | Shapefile, GeoJSON, KML | Features, projection, bounds |
| **Code** | 35+ languages | Syntax analysis, complexity |

**Full format support matrix**: See [File Format Support](docs/file-format-support.md)

---

## 🚀 **Quick Start**

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- PostgreSQL (optional, SQLite for dev)
- Redis (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sorter
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Docker Deployment**
   ```bash
   docker-compose up -d
   ```

4. **Access the Application**
   - Frontend: http://localhost:5000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   python -m file_processor.database
   ```

3. **Run the Application**
   ```bash
   # Backend
   uvicorn file_processor.main:app --host 0.0.0.0 --port 8000

   # Frontend
   python frontend/frontend.py
   ```

---

## 📚 **Documentation**

| Guide | Description | Link |
|-------|-------------|------|
| **User Guide** | End-user documentation, file upload, sorting rules | [docs/user-guide.md](docs/user-guide.md) |
| **Developer Guide** | Development setup, API development, deployment | [docs/developer-guide.md](docs/developer-guide.md) |
| **Security Guide** | Security features, RBAC, compliance, audit trails | [docs/security-guide.md](docs/security-guide.md) |
| **File Format Support** | Comprehensive format matrix, processing capabilities | [docs/file-format-support.md](docs/file-format-support.md) |
| **Processing Pipeline** | Pipeline architecture, workflows, error handling | [docs/processing-pipeline.md](docs/processing-pipeline.md) |
| **API Documentation** | OpenAPI/Swagger docs (available at /docs when running) | [docs/]() |

---

## 🔒 **Security & Compliance**

### Enterprise Security Features
- ✅ **RBAC**: Admin, Manager, User roles with granular permissions
- ✅ **Encryption**: Fernet (AES-128) for files, AES-256 for sensitive data
- ✅ **Audit Logging**: 7+ year retention for compliance
- ✅ **Rate Limiting**: Configurable request throttling
- ✅ **Input Validation**: File type, size, content validation

### Compliance Certifications
| Standard | Status | Coverage |
|----------|--------|----------|
| **GDPR** | ✅ Compliant | Data protection, DPA, consent |
| **HIPAA** | ✅ Ready | PHI detection, redaction, audit |
| **GoBD** | ✅ Ready | German accounting standards |
| **SOC 2** | ✅ Ready | Security, availability, confidentiality |

**Full security documentation**: [docs/security-guide.md](docs/security-guide.md)

---

## 🔧 **Configuration**

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
ENCRYPTION_KEY=your-encryption-key

# File Storage
UPLOAD_DIR=/path/to/uploads
MAX_FILE_SIZE=52428800  # 50MB

# AI/ML Features
OCR_ENABLED=true
CLASSIFICATION_ENABLED=true
AUTO_TAGGING_ENABLED=true

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

**Full configuration guide**: [docs/developer-guide.md](docs/developer-guide.md#configuration)

---

## 📊 **API Documentation**

### Core Endpoints

#### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/register` | User registration |
| POST | `/api/auth/refresh` | Token refresh |
| GET | `/api/auth/me` | Current user info |

#### File Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload files |
| GET | `/api/files` | List files |
| GET | `/api/files/{id}` | Get file details |
| GET | `/api/download/{id}` | Download files |
| DELETE | `/api/files/{id}` | Delete files |

#### Sorting & Rules
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sorting-rules` | Create sorting rules |
| GET | `/api/sorting-rules` | List sorting rules |
| POST | `/api/sort` | Apply sorting |

#### AI Features
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ai/classify` | AI document classification |
| POST | `/api/ai/ocr` | OCR text extraction |
| POST | `/api/ai/auto-tag` | Auto-tagging |

#### Workflows
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/workflows` | Create workflow |
| GET | `/api/workflows` | List workflows |
| POST | `/api/workflows/{id}/execute` | Execute workflow |

### API Examples

```python
import requests

# Upload a file
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/upload',
        files={'file': f},
        headers={'Authorization': 'Bearer YOUR_TOKEN'}
    )
    print(response.json())

# AI Classification
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/ai/classify',
        files={'file': f},
        headers={'Authorization': 'Bearer YOUR_TOKEN'}
    )
    print(response.json())
```

---

## 🚀 **Deployment Options**

### Docker (Recommended)

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale file-processor=4
```

### Kubernetes

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Scale backend
kubectl scale deployment sorter-backend --replicas=5

# View HPA status
kubectl get hpa
```

### Cloud Deployment
- **AWS**: ECS, EKS, Lambda
- **Google Cloud**: Cloud Run, GKE
- **Azure**: Container Instances, AKS

**Full deployment guide**: [docs/developer-guide.md](docs/developer-guide.md#operations--deployment)

---

## 📈 **Scaling & Performance**

| Component | Min | Max | Scaling Trigger |
|-----------|-----|-----|-----------------|
| Backend API | 2 | 10 | CPU > 70% or RPS > 500 |
| File Processor | 2 | 5 | Queue length > 100 |
| Frontend | 1 | 3 | CPU > 80% |
| Redis | 1 | Cluster | Memory > 80% |
| PostgreSQL | 1 | Read replicas | CPU > 80% |

---

## 🛠️ **Development**

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r file_processor/requirements.txt

# Run development server
uvicorn file_processor.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=file_processor --cov-report=html
```

### Contributing
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 **Support**

### Documentation
- 📖 [User Guide](docs/user-guide.md)
- 🛠️ [Developer Guide](docs/developer-guide.md)
- 🔒 [Security Guide](docs/security-guide.md)
- 📋 [File Format Support](docs/file-format-support.md)
- 🔄 [Processing Pipeline](docs/processing-pipeline.md)

### Support Channels
- 📧 Email: support@sorter-app.com
- 📖 Docs: https://docs.sorter-app.com
- 🐛 Issues: https://github.com/your-org/sorter/issues
- 💬 Discussions: https://github.com/your-org/sorter/discussions

---

**Sorter** - Enterprise-grade file processing with intelligent automation and comprehensive security. Built for modern organizations requiring robust, scalable file management solutions.
