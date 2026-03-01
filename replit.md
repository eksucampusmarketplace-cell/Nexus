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

### Local Development (Replit)

The Replit environment is configured to run the **Mini App (frontend)** only.
- **URL:** The UI is available via the Replit webview (port 5000).
- **API Connectivity:** By default, it connects to the production API at `https://nexus-4uxn.onrender.com`.
- **Note on "Nonsense" Output:** If you see JSON like `{"name":"Nexus API"...}` when visiting the production URL root, that is the expected behavior of the Backend API. The actual UI is hosted at `/mini-app` on production or at the root in this Replit development environment.

### Key Configuration

- `mini-app/vite.config.ts` — Configured to run on port 5000, host `0.0.0.0`, `allowedHosts: 'all'` for Replit proxy compatibility

## Bot Troubleshooting (Production/Render)

If the bot is not responding in production:
1. **Webhook URL**: Ensure `WEBHOOK_URL` in Render is set to your base domain: `https://nexus-4uxn.onrender.com`
   - The code will automatically append `/webhook/shared`.
   - Final webhook URL will be `https://nexus-4uxn.onrender.com/webhook/shared`.
2. **BOT_TOKEN**: Verify `BOT_TOKEN` is correctly set in Render environment variables.
3. **Logs**: Check Render logs for `DEBUG: Received shared webhook data`.
4. **Manual Set**: You can trigger a webhook set by restarting the `nexus-bot` service on Render.

## Deployment

Configured as a **static** deployment:
- Build: `cd mini-app && npm run build`
- Public dir: `mini-app/dist`

## Dependencies

- `mini-app/package.json` — All frontend dependencies
- Install with: `cd mini-app && npm install --legacy-peer-deps` (needed due to `date-fns` peer dep conflict)
