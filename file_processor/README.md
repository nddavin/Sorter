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
- **Multi-format Support**: Documents, images, videos, audio files
- **Metadata Extraction**: Dimensions, duration, encoding info
- **Content Analysis**: Text extraction from PDFs, DOCX, images
- **File Hashing**: SHA-256 for integrity and duplicate detection
- **Background Processing**: Async operations for performance

### 🔍 Search & Filtering
- **Full-text Search**: Content and metadata search
- **Advanced Filtering**: By type, size, date, category, tags
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

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │  File Processor │    │   Background    │
│    (Flask)      │◄──►│    API (FastAPI)│◄──►│   Workers       │
│                 │    │                 │    │   (Celery)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  PostgreSQL DB  │    │     Redis       │    │  Elasticsearch  │
│   (Primary)     │    │   (Cache)       │    │   (Search)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
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
   cd file-processor
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

### Sorting & Rules
- `POST /api/v1/sorting-rules` - Create sorting rule
- `GET /api/v1/sorting-rules` - List sorting rules
- `POST /api/v1/sort` - Apply sorting to files

### Administration
- `GET /api/v1/admin/stats` - System statistics
- `GET /api/v1/admin/audit-logs` - Audit logs
- `GET /api/v1/admin/users` - User management

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

### Authentication & Authorization
- ✅ JWT tokens with expiration
- ✅ Password hashing (bcrypt)
- ✅ Role-based permissions
- ✅ API key support
- ✅ Session management

### Data Protection
- ✅ Database encryption
- ✅ File encryption at rest
- ✅ Secure API communication
- ✅ Audit logging
- ✅ Rate limiting

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run
docker-compose up --build -d

# Scale services
docker-compose up -d --scale file-processor=3
```

### Production Checklist
- [ ] Environment variables configured
- [ ] SSL/TLS certificates installed
- [ ] Database backups configured
- [ ] Monitoring and alerting set up
- [ ] Security headers configured
- [ ] Rate limiting tuned
- [ ] CDN integration (optional)

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
- 📧 Email: support@file-processor.com
- 📖 Documentation: https://docs.file-processor.com
- 🐛 Issues: https://github.com/your-org/file-processor/issues

---

**File Processor** - Secure, scalable, and automated file processing for the modern enterprise.