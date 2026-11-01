import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backend = process.env.VITE_BACKEND_URL || env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'

  return {
    plugins: [react()],
    server: {
      host: '127.0.0.1',
      port: 5174,
      proxy: {
        '/api': { target: backend, changeOrigin: true },
        '/healthz': { target: backend, changeOrigin: true },
      },
    },
    build: {
      sourcemap: false, // Disables source maps in production so code is not visible in DevTools
      minify: true,
      cssMinify: true,
    },
  }
})
