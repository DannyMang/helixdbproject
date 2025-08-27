FROM python:3.11

WORKDIR /app

# Install system dependencies as root
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies globally as root
RUN pip install uv
COPY fastapi/requirements.txt .
RUN uv pip install --no-cache-dir --upgrade --system -r requirements.txt

# Create necessary directories and copy application files as root
RUN mkdir -p /app/utils /app/letta
COPY fastapi/*.py ./
COPY utils/*.py ./utils/
COPY letta/*.py ./letta/
COPY helix/mcp_server.py ./helix/

# Create and switch to a non-root user for security
RUN adduser --system --group nonroot
RUN chown -R nonroot:nonroot /app
USER nonroot

# Expose the app's port
EXPOSE 8000

# Run the FastAPI server as the non-root user
CMD ["/bin/sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000"]
