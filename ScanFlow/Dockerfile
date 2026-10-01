FROM python:3.14-slim AS builder

WORKDIR /build

COPY requirements.txt .

RUN python -m venv /opt/venv

RUN /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


FROM python:3.14-slim AS production

WORKDIR /code

COPY --from=builder /opt/venv /opt/venv

COPY app /code/app
COPY alembic /code/alembic
COPY alembic.ini /code/alembic.ini
COPY entrypoint.sh /code/entrypoint.sh

RUN useradd --create-home --shell /bin/bash appuser \
    && chmod +x /code/entrypoint.sh

USER appuser

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:80/healthz', timeout=3)"

ENTRYPOINT ["/code/entrypoint.sh"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers", "--forwarded-allow-ips", "172.19.0.4"]