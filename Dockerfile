FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential portaudio19-dev && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml .
COPY README.md .
RUN pip install --no-cache-dir .
COPY app.py .
EXPOSE 9854
CMD ["python", "app.py"]
