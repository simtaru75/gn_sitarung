# Plan: Container Frontend Next.js + Tailwind (Starter "Selamat Datang") Bersama GeoNode Docker

## Status

Proyek **membuat service `frontend`** di `docker-compose.yml` yang berjalan bersama GeoNode:

- Frontend **Next.js 15 + Tailwind CSS 4** di folder `frontend/`
- Berjalan di `http://localhost:3000`
- Terintegrasi dalam network yang sama dengan GeoNode (docker-compose otomatis bikin default network)
- Multi-stage Docker build (node:22-alpine)

## Arsitektur Docker

```
┌──────────────────────────────────────────────────────────────────┐
│ docker-compose.yml → default network                             │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐   │
│  │   frontend   │  │    django    │  │      geoserver        │   │
│  │    :3000     │  │    :8000     │  │      :8080            │   │
│  │   Next.js    │  │   GeoNode    │  │   GeoServer Java      │   │
│  │ (node:22)    │  │   (Python)   │  │                       │   │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬───────────┘   │
│         │                 │                       │              │
│  ┌──────┴───────┐  ┌──────┴───────┐               │              │
│  │    nginx     │  │    redis     │               │              │
│  │    :80/:443  │  │    :6379     │               │              │
│  │   reverse    │  │   broker     │      ┌────────┴────────┐     │
│  │   proxy      │  │   + cache    │      │    postgis      │     │
│  └──────────────┘  └──────────────┘      │    :5432        │     │
│                                          │   PostgreSQL    │     │
│  ┌──────────────┐                        └─────────────────┘     │
│  │  memcached   │                                                │
│  │    :11211    │  ┌──────────────────────────┐                  │
│  └──────────────┘  │      letsencrypt         │                  │
│                    │   auto SSL renewal       │                  │
│  ┌──────────────┐  └──────────────────────────┘                  │
│  │   celery     │                                                │
│  │   worker     │                                                │
│  │   (GeoNode)  │                                                │
│  └──────────────┘                                                │
└──────────────────────────────────────────────────────────────────┘
```

**Poin penting:**
- **Frontend tidak bergantung ke service GeoNode manapun** — tidak ada `depends_on` ke django/geoserver
- Semua container berbagi **default network** — nanti frontend bisa panggil `http://django:8000/api/` untuk integrasi
- Port **3000** terbuka ke host → akses di `http://localhost:3000`
- Frontend adalah **standalone Next.js production server** (bukan dev server)

## Langkah Eksekusi

### 1. Struktur folder

```
frontend/
├── .dockerignore
├── Dockerfile
├── package.json
├── next.config.ts
├── postcss.config.mjs
├── tsconfig.json
└── src/
    └── app/
        ├── globals.css            ← Tailwind import + font + CSS variables
        ├── layout.tsx             ← Root layout (html, body, metadata)
        └── page.tsx               ← Halaman "Selamat Datang"
```

### 2. Isi file `frontend/package.json`

```json
{
  "name": "frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4.0.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.0.0",
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0"
  }
}
```

### 3. Isi file `frontend/next.config.ts`

```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
};

export default nextConfig;
```

> `output: "standalone"` diperlukan agar build Next.js menghasilkan `server.js` + semua dependensi yang bisa di-copy langsung ke container Docker tanpa `node_modules`.

### 4. Isi file `frontend/postcss.config.mjs`

```js
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
```

### 5. Isi file `frontend/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### 6. Isi file `frontend/Dockerfile`

```dockerfile
# Stage 1: Install dependencies
FROM node:22-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --omit=dev

# Stage 2: Build application
FROM node:22-alpine AS builder
WORKDIR /app

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
```

### 7. Isi file `frontend/.dockerignore`

```
node_modules
.next
.git
.gitignore
*.md
.env
.env.local
```

### 8. Isi file `frontend/src/app/page.tsx`

```tsx
export default function LandingPage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-primary-navy to-primary-teal">
      <div className="text-center text-white px-6">
        <h1 className="text-5xl md:text-7xl font-serif font-bold mb-4 tracking-tight">
          Selamat Datang
        </h1>
        <p className="text-lg md:text-xl opacity-80 font-medium">
          FOLUR — Lestari untuk Negeri
        </p>
        <div className="mt-8 flex items-center justify-center gap-4">
          <span className="w-16 h-px bg-white/30" />
          <i className="fas fa-leaf text-white/60" />
          <span className="w-16 h-px bg-white/30" />
        </div>
      </div>
    </main>
  );
}
```

### 9. Isi file `frontend/src/app/layout.tsx`

```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FOLUR — Selamat Datang",
  description: "Platform FOLUR Lestari untuk Negeri",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <head>
        <link
          rel="stylesheet"
          href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
        />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
```

### 10. Isi file `frontend/src/app/globals.css`

```css
@import "tailwindcss";

@theme {
  --color-primary-navy: #0f2742;
  --color-primary-teal: #1a5c3a;
  --color-accent-gold: #c29a5b;
  --font-serif: Georgia, serif;
}

html {
  scroll-behavior: smooth;
}

body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  margin: 0;
  padding: 0;
}
```

### 11. Service di `docker-compose.yml`

```yaml
  # Frontend — landing page "Selamat Datang"
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: frontend4${COMPOSE_PROJECT_NAME}
    environment:
      - HOSTNAME=0.0.0.0
    ports:
      - "3000:3000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "node", "-e", "require('http').get('http://localhost:3000/', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) })"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s
```

### 12. Build & Deploy

```bash
# Build image frontend
docker-compose build frontend

# Jalankan container
docker-compose up -d frontend

# Cek health
docker ps --filter "name=frontend4" --format "table {{.Names}}\t{{.Status}}"

# Akses di browser
# http://localhost:3000
```

## Rencana Integrasi ke Depan

Setelah landing page selesai, integrasi dengan GeoNode sebagai backend:

### Tahap 1 — Koneksi API

```yaml
# docker-compose.yml → frontend service
environment:
  - HOSTNAME=0.0.0.0
  - NEXT_PUBLIC_API_URL=http://django:8000
```

```ts
// frontend/src/lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchLayers() {
  const res = await fetch(`${API_URL}/api/v2/layers/`);
  return res.json();
}
```

### Tahap 2 — Halaman WebGIS
- Buat halaman `/webgis` dengan Leaflet map
- Tampilkan layer dari GeoNode GeoServer
- Gunakan WMS/WFS untuk overlay peta

### Tahap 3 — Autentikasi
- Gunakan OAuth2 GeoNode
- Login/logout redirect ke GeoNode OAuth endpoint

## Checklist Eksekusi

- [x] Buat folder `frontend/` dan subfolder `src/app/`
- [x] Tulis `package.json`
- [x] Tulis `next.config.ts` dengan `output: "standalone"`
- [x] Tulis `postcss.config.mjs`
- [x] Tulis `tsconfig.json`
- [x] Tulis `Dockerfile` (multi-stage build)
- [x] Tulis `.dockerignore`
- [x] Tulis `src/app/page.tsx` — halaman "Selamat Datang"
- [x] Tulis `src/app/layout.tsx` — root layout + metadata + FontAwesome CDN
- [x] Tulis `src/app/globals.css` — Tailwind @theme + CSS variables
- [x] Tambah service `frontend` di `docker-compose.yml`
- [ ] `docker-compose build frontend` — build image
- [ ] `docker-compose up -d frontend` — deploy container
- [ ] Buka `http://localhost:3000` — verifikasi "Selamat Datang — FOLUR"
- [ ] Commit perubahan ke git
