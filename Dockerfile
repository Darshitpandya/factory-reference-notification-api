FROM python:3.12-slim

RUN pip install uv --no-cache-dir

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY src/ ./src/
COPY contracts/ ./contracts/
COPY scripts/ ./scripts/

ENV HOST=0.0.0.0

RUN groupadd -r notifications && useradd -r -g notifications notifications
USER notifications

CMD ["uv", "run", "python", "-m", "src.notifications.app"]
