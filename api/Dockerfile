# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-freefont-ttf libxss1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application code
COPY . .

# Create non-root user (but run as root for Railway compatibility)
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
# USER app  # Temporarily run as root for debugging

# Expose port
EXPOSE 8001

# Health check (removed curl dependency)
# Railway will use the healthcheckPath from railway.json

# Start the application with logging
CMD uvicorn api:app --host 0.0.0.0 --port ${PORT:-8001} --log-level info
