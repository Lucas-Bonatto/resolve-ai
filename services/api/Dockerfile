FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

COPY services/api /workspace/services/api
COPY packages/novapay-mcp /workspace/packages/novapay-mcp
COPY evals/results/latest.json /workspace/evals/results/latest.json
RUN python -m pip install --upgrade pip && \
    python -m pip install /workspace/services/api /workspace/packages/novapay-mcp

EXPOSE 8000
CMD ["sh", "-c", "python -m uvicorn app.main:app --app-dir services/api --host 0.0.0.0 --port ${PORT:-8000}"]
