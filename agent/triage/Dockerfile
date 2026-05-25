FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY . /app/
RUN mkdir -p /var/log/ouroboros

# Drop to non-root
RUN useradd --create-home --shell /bin/bash ouroboros && \
    chown -R ouroboros:ouroboros /var/log/ouroboros /app
USER ouroboros

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8001/health', timeout=3).raise_for_status()"

CMD ["uvicorn", "triage.main:app", "--host", "0.0.0.0", "--port", "8001"]
