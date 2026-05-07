# Root Dockerfile wrapper for the generated Skybridge server.
# Secrets are read from environment variables at runtime.
FROM node:22-slim AS builder

WORKDIR /app
COPY skybridge/package.json ./
RUN corepack enable pnpm && pnpm install

COPY skybridge/ .
RUN pnpm build

FROM node:22-slim
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package*.json ./

ENV MCP_TRANSPORT=stdio
CMD ["node", "dist/server.js"]
