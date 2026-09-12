# ── Stage 1: typst binary ─────────────────────────────────────────────────
FROM debian:bookworm-slim AS typst-dl

ARG TYPST_VERSION=0.15.1
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        wget \
        xz-utils \
    && rm -rf /var/lib/apt/lists/* \
    && wget --progress=dot:giga -O /tmp/typst.tar.xz \
        "https://github.com/typst/typst/releases/download/v${TYPST_VERSION}/typst-x86_64-unknown-linux-musl.tar.xz" \
    && tar -xJf /tmp/typst.tar.xz -C /tmp \
    && mv /tmp/typst-x86_64-unknown-linux-musl/typst /usr/local/bin/typst \
    && chmod +x /usr/local/bin/typst \
    && rm /tmp/typst.tar.xz

# ── Stage 2: application ──────────────────────────────────────────────────
FROM python:3.12-slim-bookworm

COPY --from=typst-dl /usr/local/bin/typst /usr/local/bin/typst

COPY --from=ghcr.io/astral-sh/uv:0.9.2 /uv /uvx /bin/

ADD . /app

WORKDIR /app

RUN uv sync --locked --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
