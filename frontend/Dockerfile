# Node 20 reached EOL April 30, 2026. Node 24 is the active LTS (supported to
# April 2028); next planned bump: Node 26 LTS, before Node 24 EOL.
FROM node:24-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
