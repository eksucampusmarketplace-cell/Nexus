import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

// Initialize Telegram WebApp
const tg = (window as any).Telegram?.WebApp
if (tg) {
  tg.ready()
  tg.expand()
  // Set theme colors to match our dark theme (only if supported)
  // Version check: setHeaderColor with color_key requires 6.1+, setBackgroundColor requires 6.1+
  const version = parseFloat(tg.version || '6.0')
  if (version >= 6.1) {
    try {
      tg.setHeaderColor('#020617')
      tg.setBottomBarColor('#020617')
      tg.setBackgroundColor('#020617')
    } catch (e) {
      console.log('[Telegram] Color settings not supported in this version')
    }
  } else {
    // For older versions, use color_key syntax if available
    try {
      tg.setHeaderColor({ color_key: 'bg_color' })
    } catch (e) {
      console.log('[Telegram] Header color not supported in version', tg.version)
    }
  }
}

// Get the base path from the document base or use default
// This handles both /mini-app/ (when served from API) and / (when served from static site)
const getBasename = () => {
  const baseTag = document.querySelector('base')
  if (baseTag) {
    return baseTag.getAttribute('href') || '/mini-app'
  }
  // Check if we're at the root path
  if (window.location.pathname.startsWith('/mini-app')) {
    return '/mini-app'
  }
  return '/'
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter basename={getBasename()}>
      <App />
      <Toaster
        position="top-center"
        toastOptions={{
          duration: 3000,
          style: {
            background: '#1e293b',
            color: '#fff',
            border: '1px solid #334155',
          },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>,
)
