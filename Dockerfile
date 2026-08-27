# ── Stage 1: typst binary ─────────────────────────────────────────────────
FROM debian:bookworm-slim AS typst-dl

ARG TYPST_VERSION=0.15.1
RUN apt-get update && apt-get install -y --no-install-recommends wget xz-utils \
    && rm -rf /var/lib/apt/lists/*
RUN wget -qO /tmp/typst.tar.xz \
        "https://github.com/typst/typst/releases/download/v${TYPST_VERSION}/typst-x86_64-unknown-linux-musl.tar.xz" \
    && tar -xJf /tmp/typst.tar.xz -C /tmp \
    && mv /tmp/typst-x86_64-unknown-linux-musl/typst /usr/local/bin/typst \
    && chmod +x /usr/local/bin/typst

# ── Stage 2: application ──────────────────────────────────────────────────
FROM python:3.12-slim

COPY --from=typst-dl /usr/local/bin/typst /usr/local/bin/typst

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY src/ ./src/
RUN uv sync --frozen --no-dev

COPY app/     ./app/
COPY flyer/   ./flyer/
COPY static/  ./static/
COPY main.py  ./

EXPOSE 5001

CMD ["uv", "run", "python", "main.py"]
