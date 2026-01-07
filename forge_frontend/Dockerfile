# Use official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY frontend.py .
COPY templates ./templates

# Create upload folder inside container
ENV UPLOAD_FOLDER=/tmp/uploads
RUN mkdir -p ${UPLOAD_FOLDER}

# Set environment variables for default host and port
ENV DEBUG=false
ENV HOST=0.0.0.0
ENV PORT=5000

# Run the application
CMD ["python", "frontend.py"]
