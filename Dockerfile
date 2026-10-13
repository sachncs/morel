# Multi-stage Dockerfile for the morel inference service.
# Stage 1 installs the build toolchain; stage 2 contains only runtime deps.

FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

ARG MOREL_VERSION=0.0.0+docker
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_MOREL=${MOREL_VERSION}

COPY pyproject.toml README.md LICENSE ./
COPY morel ./morel
RUN pip install --upgrade pip build && python -m build

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MOREL_DATA_DIR=/data

RUN groupadd --system morel && \
    useradd --system --gid morel --uid 1000 --create-home --home-dir /home/morel morel

WORKDIR /app
RUN mkdir -p /app/runs && chown -R morel:morel /app

ARG TORCH_VERSION=2.14.1
ARG TORCHVISION_VERSION=0.29.1
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        --extra-index-url https://pypi.org/simple \
        "torch==${TORCH_VERSION}" "torchvision==${TORCHVISION_VERSION}" && \
    pip install --no-cache-dir \
        "fastapi>=0.110" "uvicorn[standard]>=0.27" \
        "prometheus-client>=0.20" "httpx>=0.27" && \
    pip install --no-cache-dir /tmp/*.whl && \
    rm -rf /tmp/*.whl

USER morel

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health', timeout=3).read()" || exit 1

ENTRYPOINT ["python", "-m", "morel"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8080"]
