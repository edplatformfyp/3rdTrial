import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',      // allow external access
    port: 3000,           // ensure correct port
    strictPort: true,     // fail if 3000 is taken
    allowedHosts: true    // allow Cloudflare tunnel domain
  }
})
