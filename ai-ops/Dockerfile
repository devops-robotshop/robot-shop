FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "live_inference.py"]
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import requests; requests.get('http://localhost:8000')" || exit 1