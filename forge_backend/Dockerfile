# Base image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app sources
COPY . .

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]
