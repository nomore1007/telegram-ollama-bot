# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory for app source code
WORKDIR /app/src

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
# Note: The Dockerfile itself is in the root, so COPY . . would copy everything including the Dockerfile itself to /app/src
# We want to copy the actual source code which is everything *except* the Dockerfile and entrypoint script from the context root.
# For simplicity and assuming typical project structure where the python source is at the root of the context:
COPY . /app/src

# Copy entrypoint script and make it executable to a standard bin location
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create non-root user for security
# Ensure ownership of /app/src is set for the app user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app/src
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Entrypoint to handle config creation and then execute the command
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command to run the bot, relative to the WORKDIR
CMD ["python", "bot.py"]