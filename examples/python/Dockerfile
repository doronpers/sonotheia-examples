FROM python:3.11-slim

# Install system dependencies including ffmpeg for streaming example
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all Python examples
COPY *.py .

# Create directory for audio files
RUN mkdir -p /audio

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command shows usage
CMD ["python", "main.py", "--help"]
