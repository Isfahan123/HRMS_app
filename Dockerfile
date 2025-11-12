# Dockerfile for HRMS Web Application
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (excluding PyQt5 for web-only deployment)
RUN pip install --no-cache-dir -r requirements.txt || \
    (grep -v "PyQt5" requirements.txt > requirements-web.txt && \
     pip install --no-cache-dir -r requirements-web.txt)

# Copy application code
COPY . .

# Create directories for logs
RUN mkdir -p /app/logs

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Run with gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "120", "app:app"]
