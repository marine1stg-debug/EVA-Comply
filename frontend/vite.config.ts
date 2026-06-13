import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    // The app is served behind nginx on a public hostname (Render/Cloudflare),
    // which forwards that Host header. Vite's dev server rejects unknown hosts
    // by default — allow them since access is already gated by nginx basic auth.
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://api:8000',
        changeOrigin: true,
      }
    }
  }
})
