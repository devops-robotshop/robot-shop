FROM python:3.11-slim

ENV INSTANA_AUTO_PROFILE=true

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 8080
WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY *.py /app/

CMD ["python", "payment.py"]
#test