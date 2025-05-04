# Use a slim Python image based on Alpine Linux
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for FFmpeg and build tools
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .

# Create a directory for model cache to persist models between runs
RUN mkdir -p /root/.cache/whisper

# Expose the port the server runs on
EXPOSE 5000

# Set environment variable to specify which model to use
# Options: tiny, base, small, medium, large
ENV WHISPER_MODEL="base"

# Command to run the server
CMD ["python", "server.py"]