FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including those for pgvector/postgres if needed
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Expose ports (Streamlit default 8501, or others if needed)
EXPOSE 8501

# Default command (can be overridden in docker-compose)
CMD ["python", "main.py"]
