# Root Dockerfile wrapper for the generated Skybridge server.
# Secrets are read from environment variables at runtime.
FROM node:22-slim AS builder

WORKDIR /app
COPY skybridge/package.json skybridge/pnpm-lock.yaml* ./
RUN corepack enable pnpm && pnpm install --frozen-lockfile

COPY skybridge/ .
RUN pnpm build

FROM node:22-slim
WORKDIR /app
COPY --from=builder --chown=node:node /app/dist ./dist
COPY --from=builder --chown=node:node /app/node_modules ./node_modules
COPY --from=builder --chown=node:node /app/package*.json ./

ENV MCP_TRANSPORT=stdio
USER node
CMD ["node", "dist/server.js"]
