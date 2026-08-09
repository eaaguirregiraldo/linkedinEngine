import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// Configuración base (batch A1) + bloque `test` de vitest agregado en H1.4.
// La suite `contract` (src/tests/contract, Wave 5) queda FUERA del run normal
// (design §15: se omite sin backend vivo). `npm run test:contract` la corre
// con su propio config (frontend/vitest.contract.config.ts).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  test: {
    environment: 'jsdom',
    include: ['src/tests/**/*.test.{ts,tsx}'],
    exclude: ['src/tests/contract/**', '**/node_modules/**', '**/dist/**'],
  },
})
