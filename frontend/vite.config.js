import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// During `npm run dev`, forward backend-owned paths to FastAPI.
// In production the built `dist/` folder is served directly by FastAPI.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/rs': 'http://localhost:8000',
      '/data': 'http://localhost:8000',
      '/sparql': 'http://localhost:8000',
      '/docs': 'http://localhost:8000',
      '/openapi.json': 'http://localhost:8000',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
