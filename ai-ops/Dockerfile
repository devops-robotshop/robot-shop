FROM python:3.9-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    openssl \
    && apt-get upgrade -y openssl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
    
# Create non-root user
RUN useradd -m appuser

# Set working directory
WORKDIR /app

# Copy dependency file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Healthcheck for AI worker process
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD pgrep -f live_inference.py || exit 1

# Run AI inference
CMD ["python", "live_inference.py"]