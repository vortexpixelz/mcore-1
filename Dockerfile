FROM python:3.11-slim

WORKDIR /workspace

# System deps for scipy/matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ git \
    && rm -rf /var/lib/apt/lists/*

# Install the package and its dependencies via pyproject.toml extras
COPY . .
RUN pip install --no-cache-dir -e ".[dev,analysis]"

# Default: run tests
CMD ["pytest", "-v", "--tb=short"]
