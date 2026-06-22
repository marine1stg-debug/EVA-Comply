# Node 20 reached EOL April 30, 2026. Node 24 is the active LTS (supported to
# April 2028); next planned bump: Node 26 LTS, before Node 24 EOL.
FROM node:24-alpine

# Patch Alpine OS packages to clear base-layer CVEs flagged by Docker Scout.
RUN apk update && apk upgrade --no-cache

WORKDIR /app

# Install dependencies (no lockfile in repo, so npm install; quiet output).
COPY package*.json ./
RUN npm install --no-fund --no-audit && npm cache clean --force

COPY . .

# Drop to the unprivileged 'node' user that ships with the base image.
RUN chown -R node:node /app
USER node

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
