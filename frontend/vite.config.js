import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:6543',
      '/admin': 'http://localhost:6543',
      '/health': 'http://localhost:6543',
      '/ready': 'http://localhost:6543',
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
