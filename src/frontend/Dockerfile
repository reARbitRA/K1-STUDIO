# SPEC-004
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
COPY src/frontend/package.json ./src/frontend/package.json
RUN npm ci --no-audit --no-fund
COPY src/frontend ./src/frontend
COPY tests/frontend ./tests/frontend
RUN npm --prefix src/frontend run build
FROM nginxinc/nginx-unprivileged:1.28-alpine
COPY src/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/src/frontend/dist /usr/share/nginx/html
EXPOSE 8080
