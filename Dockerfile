FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.prod.txt requirements.txt ./

# Install Python dependencies (use prod requirements for smaller image)
RUN pip install --no-cache-dir -r requirements.prod.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Create non-root user and set permissions
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 12000

# Environment variables with defaults
ENV HOST=0.0.0.0 \
    PORT=12000 \
    DEBUG=false \
    LOG_LEVEL=INFO \
    LOG_DIR=/app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the application
CMD ["python", "main.py"]