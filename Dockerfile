# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install yt-dlp
RUN pip install --no-cache-dir yt-dlp

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create downloads directory
RUN mkdir -p downloads

# Expose port for Render
EXPOSE $PORT

# Update app.py to use PORT environment variable
RUN sed -i 's/app.run()/app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))/' app.py

# Add os import to app.py if not present
RUN grep -q "import os" app.py || sed -i '1i import os' app.py

# Start both Flask app and Telegram bot
CMD gunicorn --bind 0.0.0.0:$PORT app:app & python3 main.py
