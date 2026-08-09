import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// Config exclusiva de la suite `contract` (Wave 5, anti-drift FE/BE).
// Se corre con `npm run test:contract`; requiere backend VIVO en :8000.
// El run normal (`vitest run`) la excluye vía vite.config.ts → test.exclude.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    include: ['src/tests/contract/**/*.test.{ts,tsx}'],
    exclude: ['**/node_modules/**', '**/dist/**'],
  },
})
