FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app/contract-tests-kloc-cli

# Copy project config first for layer caching
COPY contract-tests-kloc-cli/pyproject.toml ./

# Install Python dependencies
RUN uv pip install --system -e "."

# Copy kloc-cli source (needed to run the CLI)
COPY kloc-cli/ /app/kloc-cli/

# Install kloc-cli
RUN cd /app/kloc-cli && uv pip install --system -e "."

# Copy the rest of the contract tests
COPY contract-tests-kloc-cli/ /app/contract-tests-kloc-cli/

# Default command
CMD ["pytest", "-v"]
