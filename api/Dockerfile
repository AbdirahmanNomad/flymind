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
# Note: Build from repository root (not api/) for this to work correctly
COPY api/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# Build context should be the repository root, not api/
# This ensures both api/ and flights/ directories are available
COPY api/ ./api/
COPY flights/ ./flights/

# Install fast_flights from local directory
RUN pip install -e ./flights

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app

# Set PYTHONPATH to ensure Python can find the flights package
ENV PYTHONPATH=/app

# Install Playwright browsers as root (needs system permissions)
RUN playwright install chromium

# Change ownership to non-root user
RUN chown -R app:app /app

# Switch to non-root user
# Note: Railway supports non-root users, but if you encounter permission issues,
# you can temporarily comment out the USER line
USER app

# Expose port
EXPOSE 8000

# Health check (removed curl dependency)
# Railway will use the healthcheckPath from railway.json

# Start the FastAPI app dynamically for Railway
CMD ["sh", "-c", "uvicorn api.api:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info"]
