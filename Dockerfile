FROM python:3.14-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY assets ./assets

RUN pip install --no-cache-dir . \
    && mkdir -p /data/publishers /data/searchables

ENV PYTHONUNBUFFERED=1
ENV SCHEMA_ROOT=/app/assets/schemas
ENV ASSETS_ROOT=/app/assets/validate
ENV TEMPLATES_DIR=/app/assets/templates
ENV STATIC_DIR=/app/assets/static
ENV PUBLISHERS_DATA_DIR=/data/publishers
ENV PUBLISHERS_REGISTRY_FILE=/data/publishers/publishers.json
ENV SEARCHABLES_CACHE_DIR=/data/searchables
ENV BENSON_PROXY_HEADERS=true
ENV FORWARDED_ALLOW_IPS=*

VOLUME ["/data"]

EXPOSE 8000

CMD ["benson", "--host", "0.0.0.0", "--port", "8000"]
