FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY . /app/
RUN mkdir -p /var/log/ouroboros

RUN useradd --create-home --shell /bin/bash ouroboros && \
    chown -R ouroboros:ouroboros /var/log/ouroboros /app
USER ouroboros

ENTRYPOINT ["python", "-m", "redteam.main"]
CMD ["--help"]
