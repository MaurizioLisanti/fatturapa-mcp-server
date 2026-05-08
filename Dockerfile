# ── Stage 1: Builder ────────────────────────────────────────────────────────
# Installs production dependencies into an isolated venv.
# gcc + libxml2-dev are only needed here (for lxml source builds on architectures
# that lack a prebuilt manylinux wheel).
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libxml2-dev \
        libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src/ ./src/

RUN python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir --upgrade pip \
    && /venv/bin/pip install --no-cache-dir .

# ── Stage 2: Runtime ────────────────────────────────────────────────────────
# Clean image: no build tools, no dev dependencies, non-root user.
FROM python:3.11-slim AS runtime

# Non-root user for reduced attack surface
RUN groupadd -r fatturapa \
    && useradd -r -g fatturapa -d /app -s /usr/sbin/nologin fatturapa

WORKDIR /app

# Copy only the installed venv from the builder stage
COPY --from=builder /venv /venv

# Ensure the non-root user owns the working directory
RUN chown fatturapa:fatturapa /app

USER fatturapa

ENV PATH="/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# MCP uses stdio transport — no port to expose
CMD ["fatturapa-mcp-server"]
