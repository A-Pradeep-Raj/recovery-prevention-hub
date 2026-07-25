# Multi-stage build: compile the Vite/React app, then serve it via Nginx.
# The browser calls the backend directly at build-time-baked VITE_API_BASE_URL
# (see src/api.ts) rather than proxying through nginx, to avoid fragile
# Cloud-Run-to-Cloud-Run HTTPS proxy timeouts.
FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
ARG VITE_API_BASE_URL="https://recovery-hub-backend-566288522012.us-central1.run.app"
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

ENV PORT=8080
EXPOSE 8080
