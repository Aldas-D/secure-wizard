FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /build

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip install --no-cache-dir --upgrade \
        "pip>=26.1.2" \
        "setuptools>=78.1.1" \
        "wheel>=0.45.1"

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/app/.local/bin:$PATH" \
    FLASK_ENV=production \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        wget \
        ca-certificates \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/doc/* /usr/share/man/* \
    && useradd --create-home --shell /usr/sbin/nologin --uid 10001 app

RUN pip install --no-cache-dir --upgrade \
        "pip>=26.1.2" \
        "setuptools>=78.1.1" \
        "wheel>=0.45.1"

WORKDIR /app

COPY --from=builder --chown=app:app /root/.local /home/app/.local
COPY --chown=app:app . .

RUN mkdir -p /app/instance \
    && chown -R app:app /app/instance \
    && chmod 755 /app/instance

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider "http://localhost:${PORT:-8000}/healthz" || exit 1

CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]
