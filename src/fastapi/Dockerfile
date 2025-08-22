FROM python:alpine3.19

WORKDIR /app

# Install curl for healthchecks
RUN apk add curl

# Create necessary directories first as root
RUN mkdir -p /app/utils /app/letta

# Setup a nonroot user for security
RUN adduser -D nonroot
RUN chown -R nonroot:nonroot /app
USER nonroot

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies
COPY fastapi/requirements.txt .
RUN pip install --user --no-cache-dir --upgrade -r requirements.txt

# Copy the app and required modules
COPY fastapi/*.py ./
COPY utils/*.py ./utils/
COPY letta/*.py ./letta/

# Expose the app's port
EXPOSE 8000

# Run the FastAPI server
ENTRYPOINT ["python", "-m"]
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
