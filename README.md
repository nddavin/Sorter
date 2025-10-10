# Sorter

## Overview

Sorter is a Dockerized application designed to efficiently organize and manage datasets. The project includes automated workflows via GitHub Actions for seamless deployment and testing.

## Features

1. Automated data sorting and management
1. Dockerized environment for consistent deployment
1. GitHub Actions workflows for CI/CD
1. Easy-to-use CLI and API interface
1. Modular and extensible design

## Project Structure

1. `backend/` - FastAPI backend API
1. `frontend/` - Web interface for interacting with the sorter
1. `docker/` - Docker configurations
1. `workflows/` - GitHub Actions CI/CD pipelines
1. `README.md` - Project documentation

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
