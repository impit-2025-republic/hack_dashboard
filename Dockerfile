FROM python:3.12-slim

ARG POETRY_VERSION=1.7.1

RUN apt-get update -y --fix-missing \
    && apt-get install -y --no-install-recommends \
    libffi-dev \
    libc6-dev \
    libpq-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get -y clean

WORKDIR /opt/app

ENV VIRTUAL_ENV=/opt/app/venv \
    PATH="/opt/app/venv/bin:${PATH}" \
    PYTHONPATH=/opt/app \
    PYTHONUNBUFFERED=1

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

COPY src /opt/app/src
COPY pyproject.toml /opt/app
COPY .streamlit /opt/app/.streamlit

RUN python -m venv --system-site-packages "$VIRTUAL_ENV" \
    && pip install --upgrade pip \
    && pip install "poetry==${POETRY_VERSION}" \
    && poetry install -vvv --no-interaction --no-root \
    && rm -rf /root/.cache/pypoetry

RUN groupadd --gid=65532 nonroot \
    && useradd --uid=65532 --gid=65532 --home=/nonexistent --shell=/usr/sbin/nologin nonroot \
    && chown -R 65532:65532 /opt/app \
    && chown -R 65532:65532 /tmp \
    && chmod -R 755 /tmp

USER nonroot

# При желании можно раскомментировать и добавить команду запуска, например:
CMD ["poetry", "run", "streamlit", "run", "/opt/app/src/app.py"]

# Либо оставить образ без CMD, чтобы команда указывалась при запуске контейнера:
# docker run --rm -it <image_name> poetry run python src/app.py
