# Nexus - Telegram Mini App

## Project Overview
Nexus is a comprehensive AI-native Telegram bot platform. This Replit workspace contains the **React/TypeScript/Vite frontend** (Mini App dashboard).

## Environment Configuration
- **Development Server**: Runs on port 5000 (`npm run dev`).
- **Production Build**: Located in `mini-app/dist`.
- **Backend API**: Connects to `https://nexus-4uxn.onrender.com`.

## URL Routing and Redirects
To ensure the Mini App UI is always accessible:
1. **Local Dev**: Access directly via the Replit webview on port 5000.
2. **UI Redirect**: The backend root (`/`) is now configured to automatically redirect all browser and Telegram-based requests to the Mini App interface (`/mini-app`).
3. **API Status**: To check the API status without being redirected, use the explicit status endpoint:
   - Endpoint: `/api/status`
   - Response: `{"name":"Nexus API","version":"1.0.0","status":"running"}`

## Key Files
- `mini-app/src/App.tsx`: Main application logic and routing.
- `api/main.py`: Backend entry point with the new redirect logic.
- `mini-app/vite.config.ts`: Vite configuration.

## Deployment
The project serves the static build from the root and `mini-app/dist` to ensure maximum compatibility with Replit's webview.
