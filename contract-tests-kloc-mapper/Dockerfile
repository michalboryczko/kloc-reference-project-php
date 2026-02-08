FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/contract-tests-kloc-mapper

# Copy project config first for caching
COPY contract-tests-kloc-mapper/pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e . 2>/dev/null || pip install --no-cache-dir protobuf pytest pytest-json-report

# Copy kloc-mapper source (needed for running the mapper)
COPY kloc-mapper/ /app/kloc-mapper/

# Copy test framework
COPY contract-tests-kloc-mapper/ ./

# Install kloc-mapper as a module
RUN pip install --no-cache-dir -e /app/kloc-mapper 2>/dev/null || true

# Default command
CMD ["pytest", "-v"]
