# Nexus - AI-Native Telegram Bot Platform

## Project Overview

Nexus is a comprehensive, AI-native Telegram bot platform with 27+ production-ready modules. It includes a React-based Mini App (web dashboard) for administrative control of Telegram groups.

## Architecture

- **Frontend (Mini App):** React 18 + TypeScript + Vite + Tailwind CSS — located in `mini-app/`
- **Backend (not running in Replit):** Python FastAPI + aiogram 3.x + Celery + PostgreSQL + Redis
- **State Management:** Zustand
- **Charts:** Chart.js, Recharts

## Running in Replit

Only the frontend Mini App is set up to run in Replit. The backend services (bot, API, worker) require PostgreSQL, Redis, and Telegram credentials which are not configured here.

### Workflow

- **Start application:** `cd mini-app && npm run dev` — runs the Vite dev server on port 5000

### Key Configuration

- `mini-app/vite.config.ts` — Configured to run on port 5000, host `0.0.0.0`, `allowedHosts: 'all'` for Replit proxy compatibility

## Deployment

Configured as a **static** deployment:
- Build: `cd mini-app && npm run build`
- Public dir: `mini-app/dist`

## Dependencies

- `mini-app/package.json` — All frontend dependencies
- Install with: `cd mini-app && npm install --legacy-peer-deps` (needed due to `date-fns` peer dep conflict)
