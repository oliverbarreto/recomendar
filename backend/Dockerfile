FROM python:3.12-slim

# Install curl for health checks, uv, FFmpeg for audio processing, libmagic for file type detection, and deno for yt-dlp JS runtime
RUN apt-get update && apt-get install -y curl ffmpeg libmagic1 unzip && \
    curl -fsSL https://deno.land/install.sh | sh && \
    mv /root/.deno/bin/deno /usr/local/bin/ && \
    rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container
COPY . /app

# Remove any existing .venv directory that might have been copied
RUN rm -rf .venv venv

# Install the application dependencies
WORKDIR /app
RUN uv sync --frozen --no-cache

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]