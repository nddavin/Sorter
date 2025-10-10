# Sorter

## Overview

Sorter is a comprehensive file processing application with both web and API interfaces. It provides secure file upload, sorting capabilities, and data encryption for production environments.

## Features

- **File Processing**: Sort text files with automatic organization
- **Web Interface**: Responsive web application compatible with desktop and mobile devices
- **REST API**: FastAPI-based API with automatic documentation
- **Security**: Data encryption, secure file handling, and path traversal protection
- **Docker Support**: Containerized deployment with Docker Compose
- **Production Ready**: Logging, health checks, and environment-based configuration

## Architecture

- **Backend**: FastAPI application handling file processing and API endpoints
- **Frontend**: Flask web application providing user interface
- **Database**: SQLite with encrypted content storage
- **Security**: Fernet encryption for sensitive data

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
- **File Upload Security**: Filename sanitization and path traversal protection
- **CORS Configuration**: Configurable allowed origins for cross-origin requests
- **Input Validation**: File type restrictions and size limits

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
