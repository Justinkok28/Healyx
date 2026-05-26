FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY . /app/
RUN mkdir -p /var/log/healyx

RUN useradd --create-home --shell /bin/bash healyx && \
    chown -R healyx:healyx /var/log/healyx /app
USER healyx

ENTRYPOINT ["python", "-m", "redteam.main"]
CMD ["--help"]
