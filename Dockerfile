# ---- Base image ----
FROM python:3.11-slim

# Prevent Python from writing .pyc files and using buffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install OS deps (for building some wheels etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Install Python dependencies first (layer cache friendly)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . /app/

# Ensure entrypoint is executable
RUN chmod +x /app/entrypoint.sh

# Environment variables (can be overridden at runtime)
ENV DJANGO_SETTINGS_MODULE=webapp.settings \
    DEBUG=0 \
    ALLOWED_HOSTS="*"

# Expose the port gunicorn will run on
EXPOSE 8000

# Run the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
