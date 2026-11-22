import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'
import crypto from 'crypto'

function templateManifestPlugin() {
  return {
    name: 'vite-plugin-template-manifest',
    closeBundle() {
      try {
        const srcManifestPath = path.resolve(__dirname, 'src/templates/template-manifest.json')
        const distDir = path.resolve(__dirname, 'dist')
        const distManifestPath = path.resolve(distDir, 'template-manifest.json')

        if (fs.existsSync(srcManifestPath) && fs.existsSync(distDir)) {
          const raw = fs.readFileSync(srcManifestPath, 'utf-8')
          const data = JSON.parse(raw)

          // Calculate hash of emitted assets
          const assets = fs.readdirSync(path.resolve(distDir, 'assets'))
          const hashes = {}
          for (const asset of assets) {
            const buf = fs.readFileSync(path.resolve(distDir, 'assets', asset))
            hashes[asset] = crypto.createHash('sha256').update(buf).digest('hex')
          }

          data.build_timestamp = new Date().toISOString()
          data.bundle_hashes = hashes

          fs.writeFileSync(distManifestPath, JSON.stringify(data, null, 2), 'utf-8')
          console.log('✓ Generated dist/template-manifest.json with chunk integrity hashes')
        }
      } catch (err) {
        console.warn('Could not generate dist/template-manifest.json:', err.message)
      }
    },
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backend = env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'
  return {
    plugins: [react(), templateManifestPlugin()],
    server: {
      host: '127.0.0.1',
      port: 5173,
      proxy: {
        '/api': { target: backend, changeOrigin: true },
        '/healthz': { target: backend, changeOrigin: true },
      },
    },
  }
})
