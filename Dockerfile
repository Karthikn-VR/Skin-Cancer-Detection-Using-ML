# syntax=docker/dockerfile:1

# Single runtime image with Python 3.11 base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=10000

# Install system dependencies and Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git bash ca-certificates \
    libglib2.0-0 libgl1 libgomp1 \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r backend/requirements.txt

# Install frontend dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy all project files
COPY app ./app
COPY components ./components
COPY lib ./lib
COPY public ./public
COPY styles ./styles
COPY backend ./backend
COPY WorkingModels ./WorkingModels
COPY next.config.* ./
COPY tsconfig.json ./
COPY next-env.d.ts ./
COPY components.json ./

# Build the Next.js frontend
RUN npm run build

# Copy entrypoint script and set permissions
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the frontend port
EXPOSE 10000

# Start the application using entrypoint
CMD ["/bin/bash", "/entrypoint.sh"]
