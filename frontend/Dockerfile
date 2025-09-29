# Use official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy frontend code
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir flask requests

# Expose Flask port
EXPOSE 5000

# Start Flask app
CMD ["python", "frontend.py"]
