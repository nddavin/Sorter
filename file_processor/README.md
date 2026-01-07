# File Processor - Comprehensive File Processing System

A production-ready, enterprise-grade file processing system with advanced security, automation, and scalability features.

## 🚀 Features

### 🔐 Security & Authentication
- **JWT-based Authentication** with refresh tokens
- **Role-Based Access Control** (Admin/Manager/User)
- **Multi-layered Security** with input validation and sanitization
- **File Content Scanning** for dangerous signatures
- **Rate Limiting** and abuse prevention
- **Encrypted Storage** with access controls
- **Complete Audit Trail** for compliance

### 📁 Advanced File Processing
- **Multi-format Support**: 50+ formats (Documents, images, videos, audio, CAD, medical, geospatial)
- **Metadata Extraction**: Dimensions, duration, encoding info, EXIF, ID3 tags
- **Content Analysis**: Text extraction from PDFs, DOCX, images (OCR)
- **AI/ML Classification**: Intelligent document categorization
- **File Hashing**: SHA-256 for integrity and duplicate detection
- **Background Processing**: Async operations for performance

### 🔍 Search & Filtering
- **Full-text Search**: Content and metadata search
- **Advanced, size, date Filtering**: By type, category, tags
- **Pagination**: Efficient large dataset handling
- **Faceted Search**: Aggregations and analytics

### ⚙️ Automation & Workflows
- **Custom Sorting Rules**: JSON-based conditions and actions
- **Scheduled Workflows**: Cron-based automation
- **Event-driven Processing**: File upload triggers
- **Rule Engine**: Flexible automation logic
- **Batch Operations**: Multiple file processing

### 📊 Audit & Reporting
- **Complete Audit Trail**: All user actions logged
- **Compliance Reporting**: Detailed activity reports
- **Performance Monitoring**: System metrics and analytics
- **Admin Dashboard**: System statistics and user management

### ⚡ Scalability & Performance
- **Horizontal Scaling**: Load balancer ready
- **Database Sharding**: Large dataset support
- **Redis Caching**: Performance optimization
- **Async Processing**: Non-blocking operations
- **Background Jobs**: Celery integration

## 📚 Documentation

| Guide | Description | Link |
|-------|-------------|------|
| **User Guide** | End-user documentation, file upload, sorting rules | [docs/user-guide.md](../docs/user-guide.md) |
| **Developer Guide** | Development setup, API development, deployment | [docs/developer-guide.md](../docs/developer-guide.md) |
| **Security Guide** | Security features, RBAC, compliance, audit trails | [docs/security-guide.md](../docs/security-guide.md) |
| **File Format Support** | Comprehensive format matrix, processing capabilities | [docs/file-format-support.md](../docs/file-format-support.md) |
| **Processing Pipeline** | Pipeline architecture, workflows, error handling | [docs/processing-pipeline.md](../docs/processing-pipeline.md) |

## 🏗️ Architecture

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

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Elasticsearch 8+

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

3. **Start Services**
   ```bash
   docker-compose up --build
   ```

4. **Access the Application**
   - Frontend: http://localhost:5000
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 📋 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Current user info
- `POST /api/v1/auth/refresh` - Refresh access token

### File Management
- `POST /api/v1/upload` - Secure file upload
- `GET /api/v1/files` - List user files
- `GET /api/v1/files/{file_id}` - Get file details
- `GET /api/v1/download/{file_id}` - Download file
- `DELETE /api/v1/files/{file_id}` - Delete file

### AI Features
- `POST /api/v1/ai/classify` - AI document classification
- `POST /api/v1/ai/ocr` - OCR text extraction
- `POST /api/v1/ai/auto-tag` - Auto-tagging

### Sorting & Rules
- `POST /api/v1/sorting-rules` - Create sorting rule
- `GET /api/v1/sorting-rules` - List sorting rules
- `POST /api/v1/sort` - Apply sorting to files

### Workflows
- `POST /api/v1/workflows` - Create workflow
- `GET /api/v1/workflows` - List workflows
- `POST /api/v1/workflows/{id}/execute` - Execute workflow

### Administration
- `GET /api/v1/admin/stats` - System statistics
- `GET /api/v1/admin/audit-logs` - Audit logs
- `GET /api/v1/admin/users` - User management

## 📁 Supported File Types

| Category | Formats | Count | Processing |
|----------|---------|-------|------------|
| Documents | PDF, DOCX, XLSX, PPTX, TXT, CSV, ODT | 15+ | OCR, metadata, text extraction |
| Images | JPG, PNG, GIF, TIFF, WebP, RAW, HEIC | 15+ | EXIF, dimensions, OCR |
| Videos | MP4, AVI, MOV, MKV, WebM, WMV, FLV | 12+ | Duration, codec, thumbnails |
| Audio | MP3, WAV, FLAC, AAC, OGG, WMA, M4A | 12+ | ID3 tags, duration, waveform |
| Archives | ZIP, RAR, 7Z, TAR, GZ, BZ2, XZ | 12+ | Contents listing, extraction |
| Business | XLSX, PDF, CSV, XML, JSON | 8+ | Invoice processing, data extraction |
| CAD | DWG, DXF, STEP, STP, IGES | 5+ | Entity count, BOM extraction |
| Medical | DICOM, HL7, XHL7, PDF/A | 5+ | Patient info, PHI detection |
| Geospatial | Shapefile, GeoJSON, KML, KMZ, GPX | 7+ | Features, projection, bounds |
| Code | 35+ languages (py, js, java, etc.) | 35+ | Syntax analysis, complexity |
| Logs | LOG, TXT, ERR, DEBUG, SYSLOG | 10+ | Pattern analysis, severity |
| Email | EML, MSG, PST, MBOX | 4+ | Attachment extraction |
| E-books | EPUB, MOBI, FB2, HTML, CHM | 6+ | Metadata, TOC extraction |
| Disk Images | DMG, ISO, IMG, VHD, VMDK | 6+ | Filesystem detection |

**Full format matrix**: [docs/file-format-support.md](../docs/file-format-support.md)

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/file_processor

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Storage
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=104857600

# Security
ENCRYPTION_KEY=your-32-char-encryption-key

# External Services
REDIS_URL=redis://localhost:6379
ELASTICSEARCH_URL=http://localhost:9200

# AI/ML Features
OCR_ENABLED=true
CLASSIFICATION_ENABLED=true
AUTO_TAGGING_ENABLED=true
```

## 🧪 Testing

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with coverage
pytest --cov=file_processor --cov-report=html
```

## 📊 Monitoring

### Health Checks
- `/health` - Application health status
- `/ready` - Readiness probe (all dependencies)
- `/metrics` - Prometheus metrics (if enabled)

### Logging
- Structured logging with JSON format
- Sentry integration for error tracking
- Configurable log levels

## 🔒 Security Best Practices

### File Upload Security
- ✅ Filename sanitization
- ✅ MIME type validation
- ✅ File size limits
- ✅ Content signature scanning
- ✅ Path traversal prevention
- ✅ Secure storage outside webroot
- ✅ Malware scanning integration

### Authentication & Authorization
- ✅ JWT tokens with expiration
- ✅ Password hashing (bcrypt)
- ✅ Role-based permissions
- ✅ API key support
- ✅ Session management
- ✅ MFA support

### Data Protection
- ✅ Database encryption
- ✅ File encryption at rest (Fernet/AES-256)
- ✅ Secure API communication
- ✅ Audit logging (7+ year retention)
- ✅ Rate limiting

**Full security documentation**: [docs/security-guide.md](../docs/security-guide.md)

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run
docker-compose up --build -d

# Scale services
docker-compose up -d --scale file-processor=3

# Run with production config
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment
```bash
# Deploy to K8s
kubectl apply -f k8s/

# Scale
kubectl scale deployment sorter-file-processor --replicas=5
```

### Production Checklist
- [ ] Environment variables configured
- [ ] SSL/TLS certificates installed
- [ ] Database backups configured
- [ ] Monitoring and alerting set up
- [ ] Security headers configured
- [ ] Rate limiting tuned
- [ ] CDN integration (optional)

**Full deployment guide**: [docs/developer-guide.md](../docs/developer-guide.md#operations--deployment)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- 📧 Email: support@sorter-app.com
- 📖 Documentation: https://docs.sorter-app.com
- 🐛 Issues: https://github.com/your-org/sorter/issues

---

**File Processor** - Secure, scalable, and automated file processing for the modern enterprise.
