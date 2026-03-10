# syntax=docker/dockerfile:1

# Use Python 3.11 as the base image for both build and runtime
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=10000

# Install system dependencies (including those for OpenCV and Node.js)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    bash \
    ca-certificates \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Build Stage ---
FROM base AS builder

# Set NODE_ENV to development to ensure devDependencies are installed for the build
ENV NODE_ENV=development

# Install Python dependencies in a virtualenv
COPY backend/requirements.txt ./backend/
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r backend/requirements.txt

# Install Node.js dependencies and build the frontend
COPY package.json package-lock.json* ./
RUN npm ci

# Copy the rest of the source code
COPY . .

# Build Next.js
RUN npm run build

# --- Runtime Stage ---
FROM base AS production

# Copy the virtualenv from the builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the built frontend artifacts and node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/styles ./styles
COPY --from=builder /app/app ./app
COPY --from=builder /app/next.config.* ./

# Copy the backend source and models
COPY --from=builder /app/backend ./backend
COPY --from=builder /app/WorkingModels ./WorkingModels

# Copy and set permissions for the entrypoint script
COPY --from=builder /app/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the port Render expects
EXPOSE 10000

# Start the application using the entrypoint script
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
