FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 GRIDGUIDE_MODE=synthetic-demo GRIDGUIDE_AI_PROVIDER=none PORT=8000
WORKDIR /app
# Build context MUST be the inspected extracted package, never the repository.
COPY deploy/requirements.lock /tmp/requirements.lock
RUN python -m venv /opt/runtime && /opt/runtime/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock && rm /tmp/requirements.lock
COPY backend/ backend/
COPY benchmarks/ benchmarks/
COPY data/ data/
COPY static/ static/
COPY scripts/ scripts/
COPY deploy/ deploy/
COPY THIRD_PARTY_NOTICES.md DEPENDENCY_NOTICES.txt PUBLIC_MANIFEST.json ./
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s CMD /opt/runtime/bin/python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=2)"
CMD ["/opt/runtime/bin/python", "deploy/serve.py"]
