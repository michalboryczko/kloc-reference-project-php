FROM python:3.12-slim

# Install system dependencies (Docker CLI for scip-php execution)
RUN apt-get update && apt-get install -y --no-install-recommends \
    docker.io \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

WORKDIR /app/contract-tests-e2e

# Copy project config first for layer caching
COPY contract-tests-e2e/pyproject.toml ./

# Install Python dependencies
RUN uv pip install --system -e "."

# Copy kloc-mapper source and install
COPY kloc-mapper/ /app/kloc-mapper/
RUN cd /app/kloc-mapper && uv pip install --system -e "."

# Copy kloc-cli source and install
COPY kloc-cli/ /app/kloc-cli/
RUN cd /app/kloc-cli && uv pip install --system -e "."

# Copy scip-php scripts (for Docker-based indexing)
COPY scip-php/bin/ /app/scip-php/bin/

# Copy the reference PHP project
COPY . /app/kloc-reference-project-php/

# Copy the rest of the E2E test framework
COPY contract-tests-e2e/ /app/contract-tests-e2e/

# Default command
CMD ["pytest", "-v"]
