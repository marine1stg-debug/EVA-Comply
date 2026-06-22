# ─────────────────────────────────────────────────────────────────────────────
# EVA Comply API — multi-stage build.
#
# Stage 1 (builder) carries the GCC toolchain and -dev headers needed to install
# Python deps, then is thrown away. Stage 2 (runtime) ships ONLY the Python venv
# plus the runtime shared libraries WeasyPrint needs — no build-essential, no
# curl, no -dev packages. That removes the large majority of the CVEs Docker
# Scout reports for this image, and the final image runs as a non-root user.
# ─────────────────────────────────────────────────────────────────────────────

# ---- Stage 1: builder ----------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build-time-only toolchain and headers (NOT shipped in the final image).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Isolated virtualenv we can copy wholesale into the runtime stage.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# ---- Stage 2: runtime ----------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Patch the base OS packages, then install ONLY the runtime shared libraries
# (Pango/Cairo/GDK-Pixbuf/GLib + fonts for WeasyPrint PDF rendering, libpq5 for
# Postgres). No compilers, no headers, no curl.
RUN apt-get update && apt-get -y upgrade && apt-get install -y --no-install-recommends \
        libpq5 \
        libglib2.0-0 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libpangoft2-1.0-0 \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        shared-mime-info \
        fonts-dejavu-core \
        fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Bring in the prebuilt virtualenv from the builder stage.
COPY --from=builder /opt/venv /opt/venv

# Non-root runtime user; owns the app dir and the uploads mount point.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/uploads /app/backups \
    && chown -R appuser:appuser /app

# Application code (the .dockerignore keeps caches/secrets/VCS out).
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# Liveness check using stdlib (curl is intentionally not installed).
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status==200 else 1)" || exit 1

# Default command (docker-compose overrides this to also run migrations/seeds).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
