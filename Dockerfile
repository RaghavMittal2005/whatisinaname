# Multi-stage Dockerfile for minimum size and security
FROM python:3.12-slim AS builder
WORKDIR /app

# Install uv compiler securely
RUN pip install uv

# Create cached dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source and install project
COPY . .
RUN uv sync --frozen --no-dev

# Final executing stage
FROM python:3.12-slim
WORKDIR /app

# Non-root user setup
RUN useradd -m -u 1000 appuser

# Copy binaries and venv
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder /app/.venv ./.venv

COPY . .
RUN chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "hoja.server.app"]
