# --- Stage 1: Builder (Optional for dependencies) ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies for psycopg2, ffmpeg, etc.
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# --- Stage 2: Final Image ---
FROM python:3.11-slim

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libpq5 \
  && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy project files
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV HOST=0.0.0.0

# Create uploads folder inside container
RUN mkdir -p /app/uploads
# Expose port for FastAPI
EXPOSE 8000

# Run using uvicorn in production mode
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
