# Use official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy backend code
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn

# Create directories for uploads and sorted files
RUN mkdir -p uploads sorted

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI app
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
