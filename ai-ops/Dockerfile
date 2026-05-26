FROM python:3.9-slim

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

# Set ownership for app directory
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Run AI inference script
CMD ["python", "live_inference.py"]