FROM python:3.11-slim

# System deps (psycopg2 needs gcc & libpq)
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code (mounted at runtime too)
COPY app ./app

EXPOSE 8000
