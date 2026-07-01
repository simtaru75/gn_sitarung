# Stage 1: Install dependencies (browser-sync)
FROM node:22-alpine AS deps
RUN npm install -g browser-sync@3.0.3
WORKDIR /app
EXPOSE 3030
CMD ["browser-sync", "start", \
     "--server", "/app", \
     "--port", "3030", \
     "--host", "0.0.0.0", \
     "--files", "**/*", \
     "--no-notify", \
     "--no-open", \
     "--reload-delay", "300"]

# Stage 2: Production runner (with files baked in)
FROM node:22-alpine AS runner
RUN npm install -g browser-sync@3.0.3
WORKDIR /app
COPY ./ADMINSITARUNG /app
EXPOSE 3030
CMD ["browser-sync", "start", \
     "--server", "/app", \
     "--port", "3030", \
     "--host", "0.0.0.0", \
     "--files", "**/*", \
     "--no-notify", \
     "--no-open", \
     "--reload-delay", "300"]
