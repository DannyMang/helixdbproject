FROM python:3.11-slim as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package management
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY fastapi/requirements.txt .
RUN uv pip install --no-cache-dir --system -r requirements.txt

FROM python:3.11-slim as runtime

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python environment from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Create necessary directories and copy application files
RUN mkdir -p /app/utils /app/letta /app/helix /app/neon
COPY fastapi/*.py ./
COPY utils/*.py ./utils/
COPY letta/*.py ./letta/
COPY helix/mcp_server.py ./helix/
COPY neon/*.py ./neon/

# Create and switch to a non-root user for security
RUN adduser --system --group --no-create-home nonroot
RUN chown -R nonroot:nonroot /app
USER nonroot

# Expose the app's port
EXPOSE 8000

# Run the FastAPI server as the non-root user
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
