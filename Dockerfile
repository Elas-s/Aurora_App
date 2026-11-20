FROM python:3.11-slim

# 🛠️ install uv (copied from uv's own image)
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /bin/
WORKDIR /app
COPY . .
RUN uv sync --frozen --no-dev
CMD ["uv", "run", "--no-dev", "fastapi", "run", "main.py"]