# ─── JailbreakArena Dockerfile ────────────────────────────────────────────
# Usage:
#   docker build -t jailbreak-arena .
#   docker run --env-file .env jailbreak-arena
#   docker run --env-file .env jailbreak-arena --task task_001 --turns 3

FROM python:3.11-slim

# Metadata
LABEL maintainer="Mithilesh Kumar Lala"
LABEL description="JailbreakArena: Adversarial RL Security Testing for LLM Applications"
LABEL version="0.1.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer caching — dependencies won't
# reinstall unless requirements.txt changes)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy full project
COPY . .

# Create directory for reports output
RUN mkdir -p /app/reports

# Environment variables with safe defaults
# User must provide at least ONE provider key via --env-file
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV REPORT_OUTPUT_DIR=/app/reports

# Expose reports directory as volume
# docker run -v $(pwd)/reports:/app/reports --env-file .env jailbreak-arena
VOLUME ["/app/reports"]

# Default entrypoint — runs the full audit
ENTRYPOINT ["python", "-m", "jailbreak_arena.cli"]
CMD ["--help"]

# Default arguments — can be overridden at runtime
# docker run --env-file .env jailbreak-arena --task task_001 --turns 3 --quiet
