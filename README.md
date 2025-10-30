# 🚀 **ULTIMATE COMPREHENSIVE FILE PROCESSING SYSTEM**

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
- **Multi-format Support**: Documents, Images, Videos, Audio, Archives, Code, Logs, Business Files
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
┌─────────────────────────────────────────────────────────────┐
│                    WORKFLOW ENGINE                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Event Triggers  │  Scheduled Jobs  │  API Calls   │    │
│  └─────────────────────────────────────────────────────┘    │
│           │                    │                    │        │
│           ▼                    ▼                    ▼        │
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ File Upload │  │ Processing  │  │ Validation │         │
│  │             │  │ Engine      │  │ & Security │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│          │                    │                    │        │
│          └────────────────────┼────────────────────┘        │
│                               │                             │
│                    ┌─────────────┐                         │
│                    │ Intelligent │                         │
│                    │   Sorting   │                         │
│                    └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 **Supported File Types**

### 📄 **Documents**
- **Word Files**: .doc, .docx with author, title, keywords extraction
- **PDFs**: .pdf with page count, metadata, and text extraction
- **Spreadsheets**: .xls, .xlsx with sheet analysis and data validation
- **Presentations**: .ppt, .pptx with slide count and content analysis
- **Text Files**: .txt, .rtf with encoding detection and content indexing

### 🖼️ **Images**
- **Photos**: .jpg, .jpeg, .png, .gif, .tiff, .raw with EXIF data
- **Graphics**: .webp, .svg, .ico with resolution and format analysis
- **Metadata**: Camera info, GPS coordinates, creation date, dimensions

### 🎥 **Videos**
- **Formats**: .mp4, .avi, .mov, .mkv, .wmv, .flv, .webm
- **Analysis**: Duration, resolution, frame rate, bitrate, codec
- **Metadata**: Creation date, camera info, audio specifications

### 🎵 **Audio Files**
- **Music**: .mp3, .wav, .flac, .aac, .ogg, .wma
- **Metadata**: Artist, album, title, genre, year, track number
- **Technical**: Duration, bitrate, sample rate, channels, encoding

### 📦 **Archives**
- **Compressed**: .zip, .rar, .7z, .tar, .gz, .bz2, .xz
- **Analysis**: Compression ratio, contents count, archive type
- **Security**: Nested file scanning and validation

### 💻 **Code & Scripts**
- **Languages**: Python, JavaScript, Java, C++, C#, PHP, Ruby, Go, Rust
- **Analysis**: Line count, complexity, imports, functions, classes
- **Project**: Language detection, project structure analysis

### 📋 **Log Files**
- **System Logs**: Application and system logs with timestamp analysis
- **Severity**: Debug, info, warning, error, critical level classification
- **Patterns**: Error count, time range, source identification

### 💼 **Business Files**
- **Reports**: Excel reports, invoices, purchase orders
- **Sorting**: Date, amount, reference number, department, status
- **Workflow**: Approval chains, priority levels, project categorization

---

## 🚀 **Quick Start**

### Prerequisites
- Docker & Docker Compose
- Python 3.9+
- PostgreSQL (optional, uses SQLite by default)

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

## 🔧 **Configuration**

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret

# File Storage
UPLOAD_DIR=/path/to/uploads
MAX_FILE_SIZE=52428800  # 50MB

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### Advanced Configuration
- **Rate Limiting**: Configure upload/download limits
- **File Types**: Enable/disable specific file type processing
- **Workflow Rules**: Customize automated processing rules
- **Security Policies**: Configure validation and scanning rules

---

## 📚 **API Documentation**

### Core Endpoints

#### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/refresh` - Token refresh
- `GET /api/auth/me` - Current user info

#### File Management
- `POST /api/upload` - Upload files with processing
- `GET /api/files` - List user files with filtering
- `GET /api/files/{id}` - Get file details
- `GET /api/download/{id}` - Download files securely
- `DELETE /api/files/{id}` - Delete files

#### Sorting & Rules
- `POST /api/sorting-rules` - Create sorting rules
- `GET /api/sorting-rules` - List sorting rules
- `POST /api/sort` - Apply sorting to files

#### Administration
- `GET /api/admin/stats` - System statistics
- `GET /api/admin/audit-logs` - Audit logs

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

# List files with sorting
response = requests.get(
    'http://localhost:8000/api/files?sort_by=created_at&sort_order=desc',
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)
```

---

## 🔒 **Security Features**

### Authentication & Authorization
- JWT tokens with configurable expiration
- Role-based permissions (user, manager, admin)
- Secure password hashing with bcrypt
- Session management and invalidation

### File Security
- Content-type validation and sanitization
- File signature verification
- Path traversal protection
- Size limits and rate limiting
- Virus scanning integration

### Data Protection
- End-to-end encryption for sensitive files
- Secure file storage with access controls
- Audit logging for all operations
- GDPR compliance features

---

## 📊 **Monitoring & Analytics**

### System Metrics
- File upload/download statistics
- Processing performance metrics
- User activity tracking
- Error rates and system health

### Logging
- Structured logging with multiple levels
- Searchable audit trails
- Performance monitoring
- Automated alerting

### Reporting
- Usage reports and analytics
- Security incident reports
- Performance optimization insights
- Compliance documentation

---

## 🚀 **Deployment Options**

### Docker (Recommended)
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Development with hot reload
docker-compose -f docker-compose.dev.yml up
```

### Cloud Deployment
- **AWS**: ECS, EKS, Lambda
- **Google Cloud**: Cloud Run, GKE
- **Azure**: Container Instances, AKS
- **Heroku**: Container deployment

### Scaling
- Horizontal scaling with load balancers
- Database read replicas
- Redis for session and cache management
- CDN integration for static assets

---

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation
- Ensure security best practices

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 **Support & Documentation**

### Documentation
- 📖 [API Documentation](http://localhost:8000/docs) (when running)
- 📚 [User Guide](docs/user-guide.md)
- 🛠️ [Developer Guide](docs/developer-guide.md)
- 🔒 [Security Guide](docs/security-guide.md)

### Support
- 📧 Email: support@sorter-app.com
- 📖 Documentation: https://docs.sorter-app.com
- 🐛 Issues: https://github.com/your-org/sorter/issues
- 💬 Discussions: https://github.com/your-org/sorter/discussions

### Community
- 🌟 Star this repository if you find it useful!
- 📢 Share your use cases and feedback
- 🤝 Contribute improvements and features

---

**Sorter** - Enterprise-grade file processing with intelligent automation and comprehensive security. Built for modern organizations requiring robust, scalable file management solutions.

## Installation

### Clone the Repository

```bash
git clone https://github.com/your-username/sorter.git
cd sorter
````

### Using Docker

```bash
docker-compose up --build
```

This will start the backend and frontend services.

### Production Deployment

For production, ensure the following environment variables are set:

- `DATABASE_URL`: Database connection string (e.g., PostgreSQL URL)
- `ENCRYPTION_KEY`: Key for encrypting sensitive data (generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins (e.g., "http://localhost:3000,https://yourdomain.com")
- `BACKEND_DOWNLOAD_URL`: URL for the backend download endpoint (default: "http://backend:8000/download")
- `UPLOAD_FOLDER`: Directory for uploads
- `SORTED_FOLDER`: Directory for sorted files

Use Docker Compose with production overrides or set environment variables accordingly.

## Usage

### Web Interface

Access the web interface at `http://localhost:5000` (or the configured frontend port). The interface is responsive and works on both desktop and mobile devices.

### API

The API is documented with OpenAPI/Swagger. Access the documentation at `/docs` or `/redoc` when the multimedia_processor is running.

For direct API usage:

```python
import requests

# Upload and sort a file
with open('input.txt', 'rb') as f:
    response = requests.post('http://localhost:8000/api/upload', files={'file': f})
    print(response.json())
```

## Security

- **Data Encryption**: All processed file content is encrypted using Fernet symmetric encryption
- **File Upload Security**: Filename sanitization and path traversal protection with strict validation
- **CORS Configuration**: Configurable allowed origins for cross-origin requests
- **Input Validation**: File type restrictions, size limits, and XSS prevention
- **Path Traversal Protection**: Multiple layers of validation including regex patterns and path resolution checks
- **Content Security**: File downloads served as attachments to prevent XSS in browser rendering

## Production Deployment

### Environment Variables

Set the following environment variables for production:

- `DATABASE_URL`: Database connection string (default: SQLite)
- `ENCRYPTION_KEY`: Required encryption key (generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
- `ALLOWED_ORIGINS`: CORS allowed origins (default: localhost URLs)
- `BACKEND_URL`: Backend API URL (default: http://backend:8000/sort)
- `BACKEND_DOWNLOAD_URL`: Backend download URL (default: http://backend:8000/download)
- `UPLOAD_FOLDER`: Upload directory path
- `SORTED_FOLDER`: Sorted files directory path
- `DEBUG`: Set to "false" for production
- `HOST`: Host to bind to (default: 0.0.0.0)
- `PORT`: Port to bind to

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build -d

# Check logs
docker-compose logs -f

# Scale services if needed
docker-compose up -d --scale backend=2

# Run security scan
docker-compose --profile security run --rm security-scan
```

### Health Checks

The application includes health check endpoints:
- Backend: `GET /health`
- Services monitored via Docker health checks

### Monitoring

- Structured logging with configurable levels
- Docker logging with size limits and rotation
- API documentation available at runtime

### CLI

```bash
python sorter_cli.py --input input_file.csv --output output_file.csv
```

## GitHub Workflows

The project includes CI/CD workflows for:

1. Running automated tests on every push
2. Building and publishing Docker images
3. Deploying to staging or production environments

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature-name`)
3. Commit your changes (`git commit -m 'Add feature'`)
4. Push to the branch (`git push origin feature-name`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.
