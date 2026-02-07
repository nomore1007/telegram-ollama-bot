#Version Control
ARG CACHE_BUST=1

# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory for app source code
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Create non-root user and ensure proper permissions
# Chown /app (including app code and data dir)
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app && \
    chmod -R 755 /app

# Use entrypoint script (handles volume mount permissions)
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command to run the bot, relative to the WORKDIR
CMD ["python", "run_bot.py"]