import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const django = process.env.DJANGO_URL || 'http://127.0.0.1:8000'

// En dev, Vite relaie l'API, les médias et les statiques vers Django :
// le navigateur reste sur une seule origine (cookies de session et CSRF fonctionnent tels quels).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': django,
      '/media': django,
      '/static': django,
      '/dashboard': django,
      '/admin': django,
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/setupTests.js',
  },
})
