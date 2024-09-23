FROM python:3.11.10-slim-bullseye AS base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN export DEBIAN_FRONTEND=noninteractive &&  apt-get update && \
    apt-get install -y curl build-essential ffmpeg nano git &&  \
    apt-get clean
COPY --from=ghcr.io/astral-sh/uv:0.4.10 /uv /bin/uv

WORKDIR /server_code
# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to pyproject.toml to avoid having to copy them into this layer.
ARG ARG_CI=0
ENV UV_SYSTEM_PYTHON=1
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_SYSTEM_PYTHON=1
ENV UV_NO_CACHE=${ARG_CI}

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=/server_code/pyproject.toml \
    uv pip install -r pyproject.toml

ENV FTLANG_CACHE='/fasttext-cache'

ARG ARG_LOW_MEM=1
RUN python3 -c "from ftlangdetect.detect import get_or_load_model; low_mem=bool(${ARG_LOW_MEM});get_or_load_model(low_mem);"
ENV LOW_MEM=${ARG_LOW_MEM}

VOLUME [ "/var/log" ]

FROM base AS clean_base

RUN python3 -m pip cache purge  \
    && apt-get purge -y --auto-remove git cmake ncurses-dev &&  \
    apt-get clean && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

ENV HOME_ROOT="/home/python-master"
ENV MEDIA_ROOT="$HOME_ROOT/media"

RUN groupadd -g 1001 python && useradd -u 1001 -g python python-master &&  \
    mkdir -p "$HOME_ROOT" "$MEDIA_ROOT" /server_code/static "$HOME_ROOT/.cache" && \
    chmod -R 755 /root && \
    chown -R 1001:1001 "$FTLANG_CACHE" "$MEDIA_ROOT" "$HOME_ROOT" /server_code/static

VOLUME [ "$HOME_ROOT", "$FTLANG_CACHE"]
ENTRYPOINT [ "/docker-entrypoint.sh" ]
FROM clean_base AS web

COPY docker/web-entrypoint.sh /docker-entrypoint.sh

RUN chown 1001:1001 /docker-entrypoint.sh && chmod 755 /docker-entrypoint.sh

ENV WEB_PORT=8080
EXPOSE 8080

COPY docker /server_code
RUN chown -R 1001:1001 /server_code
USER python-master
HEALTHCHECK --timeout=15s --retries=20 CMD curl -X POST -d '{}' --fail "http://localhost:${WEB_PORT}/api/v1/misc/ping" || exit 1

FROM clean_base AS worker

COPY docker/python-worker-entrypoint.sh /docker-entrypoint.sh

RUN chown 1001:1001 /docker-entrypoint.sh && chmod 755 /docker-entrypoint.sh

COPY docker /server_code

RUN chown -R 1001:1001 /server_code
USER python-master
ENV WEB_PORT=8080
HEALTHCHECK --timeout=15s --retries=20 CMD curl --fail "http://localhost:${WEB_PORT}/api/v1/misc/health" || exit 1

FROM clean_base AS celery_worker
ENV LOG_LEVEL=INFO
ENV POOL=threads
ENV WORKER_NAME=worker
ENV WORKERS_QUEUES="celery_default,default"

COPY docker/celery-worker-entrypoint.sh /docker-entrypoint.sh

RUN chown 1001:1001 /docker-entrypoint.sh && chmod 755 /docker-entrypoint.sh

COPY docker /server_code
RUN chown -R 1001:1001 /server_code
USER python-master
HEALTHCHECK --timeout=120s --retries=20 CMD celery inspect ping || exit 1

FROM clean_base AS celery_beat
ENV LOG_LEVEL=INFO
ENV POOL=threads
ENV WORKER_NAME=worker
ENV WORKERS_QUEUES="celery_default,default"
RUN pip install celery

COPY docker/beat-entrypoint.sh /docker-entrypoint.sh

RUN chown 1001:1001 /docker-entrypoint.sh && chmod 755 /docker-entrypoint.sh

COPY docker /server_code
RUN chown -R 1001:1001 /server_code
USER python-master
HEALTHCHECK --timeout=35s --retries=20 CMD celery inspect ping || exit 1
