import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Get base path from environment or use default for mini-app
const base = process.env.VITE_BASE_PATH || '/mini-app/'

export default defineConfig({
  plugins: [react()],
  base: base,
  server: {
    port: 5000,
    host: '0.0.0.0',
    allowedHosts: 'all',
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    // Ensure assets use relative paths when served from API
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        // Ensure consistent asset naming
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.')
          const ext = info[info.length - 1]
          if (/\.(png|jpe?g|gif|svg|webp|ico)$/i.test(assetInfo.name)) {
            return 'assets/images/[name]-[hash][extname]'
          }
          if (/\.(woff2?|ttf|otf|eot)$/i.test(assetInfo.name)) {
            return 'assets/fonts/[name]-[hash][extname]'
          }
          return 'assets/[name]-[hash][extname]'
        },
      },
    },
  },
})
