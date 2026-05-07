# Generated Dockerfile for spotify-playlist-generator (Skybridge)
# CONTRACT C-17, C-18: no embedded secrets; reads API keys from environment at runtime.
# Requires Node.js 22+.
FROM node:22-slim AS builder

WORKDIR /app
COPY package.json ./
RUN corepack enable pnpm && pnpm install

COPY . .
RUN pnpm build

FROM node:22-slim
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./

EXPOSE 8000
ENV MCP_TRANSPORT=http

CMD ["node", "dist/server.js"]
