import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const proxy = { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false } };

export default defineConfig({
  plugins: [react()],
  build: { manifest: true, rollupOptions: { input: { app: 'index.html', preparedness: 'preparedness/index.html' } } },
  server: { proxy },
  preview: { proxy },
});
