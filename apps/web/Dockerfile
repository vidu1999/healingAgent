# SentinelOps AI frontend container image.
# Build: docker build -t sentinelops-frontend:latest -f apps/web/Dockerfile .
# Run:   docker run -e NEXT_PUBLIC_API_BASE=http://backend:8000/api/v1 -p 3000:3000 sentinelops-frontend:latest
FROM node:20-slim AS builder

WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm ci

COPY apps/web ./apps/web
WORKDIR /app/apps/web

# Next.js 14 App Router production build.
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-slim AS runner

WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

COPY --from=builder /app/apps/web/.next ./.next
COPY --from=builder /app/apps/web/public ./public
COPY --from=builder /app/apps/web/package.json ./package.json
COPY --from=builder /app/apps/web/node_modules ./node_modules

EXPOSE 3000

CMD ["npm", "start"]
