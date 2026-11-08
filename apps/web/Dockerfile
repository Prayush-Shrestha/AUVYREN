# Stage 1: Build the web application
FROM node:22-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

# Copy source code
COPY apps/web ./apps/web
COPY apps/api ./apps/api

# Build the Next.js application
RUN npm run build --workspace @auvyren/web

# Stage 2: Runtime
FROM node:22-slim AS runner

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy built application
COPY --from=builder /app/apps/web/.next ./apps/web/.next
COPY --from=builder /app/apps/web/public ./apps/web/public
COPY --from=builder /app/apps/web/package.json ./apps/web/package.json
COPY --from=builder /app/node_modules ./node_modules

# Create non-root user
RUN groupadd -r auvyren && useradd -r -g auvyren auvyren
USER auvyren

# Expose web port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Run the web server
CMD ["npm", "run", "start", "--workspace", "@auvyren/web"]
