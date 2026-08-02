# define an alias for the specific python version used in this file.
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim AS python

# Python build stage
FROM python AS python-build-stage

ARG APP_HOME=/app

WORKDIR ${APP_HOME}

# virtualenv is placed outside $APP_HOME so it won't be overridden by the docker compose bind mount
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0 UV_PROJECT_ENVIRONMENT=/opt/venv

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  gettext \
  wait-for-it

# Requirements are installed here to ensure they will be cached.
# libs/ is bind-mounted so uv can discover workspace members and their deps.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock:rw \
    --mount=type=bind,source=libs,target=libs \
    uv sync --no-install-project

COPY . ${APP_HOME}

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock:rw \
    uv sync

# devcontainer dependencies and utils
RUN apt-get update && apt-get install --no-install-recommends -y \
  sudo git bash-completion nano ssh

# Create devcontainer user and add it to sudoers
RUN groupadd --gid 1000 dev-user \
  && useradd --uid 1000 --gid dev-user --shell /bin/bash --create-home dev-user \
  && echo dev-user ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/dev-user \
  && chmod 0440 /etc/sudoers.d/dev-user

ENV PATH="/opt/venv/bin:$PATH"

COPY ./docker/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./docker/local/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start


COPY ./docker/local/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker
RUN chmod +x /start-celeryworker

COPY ./docker/local/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat
RUN chmod +x /start-celerybeat

COPY ./docker/local/django/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /start-flower
RUN chmod +x /start-flower


ENTRYPOINT ["/entrypoint"]
