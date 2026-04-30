FROM python:3.11-slim

ENV INSTANA_AUTO_PROFILE=true

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    wget \
    && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser appuser

EXPOSE 8080
WORKDIR /app

RUN chown -R appuser:appuser /app

COPY --chown=appuser:appuser requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser *.py /app/

USER appuser

HEALTHCHECK --interval=30s --timeout=3s CMD wget --quiet --tries=1 --spider http://localhost:8080/ || exit 1

CMD ["python", "payment.py"]