FROM python:3.10-slim

WORKDIR /opt/todolist

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=off \
    PYTHONPATH=/opt/todolist \
    POETRY_VERSION=1.1.13
#    POETRY_HOME="/opt/poetry"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    curl \
    build-essential \
    && apt-get autoclean  \
    && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/* /tmp* /var/tmp*

# install poetry - respects $POETRY_VERSION
RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-dev

COPY ./todolist ./todolist
COPY ./core ./core
COPY ./front ./front
COPY manage.py README.md ./
