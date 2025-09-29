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

## Usage

### API

```python
from sorter import SorterAPI

api = SorterAPI()
api.sort_data("input_file.csv", "output_file.csv")
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
