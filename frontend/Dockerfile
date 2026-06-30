# Stage 1: Install dependencies
FROM node:22-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json ./
RUN npm install

# Stage 2: Build application
FROM node:22-alpine AS builder
WORKDIR /app

# Base publik GeoNode untuk referensi NEXT_PUBLIC_* sisi-client (di-inline saat
# build). Base utama tetap dibaca runtime di Server Component.
ARG NEXT_PUBLIC_GEONODE_URL=http://localhost
ENV NEXT_PUBLIC_GEONODE_URL=${NEXT_PUBLIC_GEONODE_URL}

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN npm run build

# Stage 3: Production runner
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
