FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_PORT=8000 \
    DATA_DIR=/app/data \
    TZ=Asia/Ho_Chi_Minh

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
COPY pyproject.toml ./pyproject.toml
COPY README.md ./README.md

RUN mkdir -p /app/data/json/year /app/data/csv /app/data/ics/year \
    && python -m app.main build-dataset --from-year 2000 --to-year 2100 --data-dir /app/data \
    && python -m app.main verify --from-year 2000 --to-year 2100 --data-dir /app/data --load-existing \
    && chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=5).read()"]

CMD ["python", "-m", "app.main", "serve", "--host", "0.0.0.0", "--port", "8000", "--data-dir", "/app/data"]

