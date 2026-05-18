FROM python:3.11-slim

WORKDIR /workspace

# System deps for scipy/matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ git \
    && rm -rf /var/lib/apt/lists/*

# Pin exact deps first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the package itself
COPY . .
RUN pip install --no-cache-dir -e ".[dev]"

# Default: run tests
CMD ["pytest", "-v", "--tb=short"]
