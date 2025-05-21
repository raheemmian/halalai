# Dockerfile
FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .


CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "backend.asgi:application"]
