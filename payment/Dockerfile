FROM python:3.9-slim

RUN apt-get update && apt-get upgrade -y && apt-get clean

ENV INSTANA_AUTO_PROFILE true
EXPOSE 8080
WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY payment.js /app/
COPY *.py /app/

CMD ["python", "payment.py"]
