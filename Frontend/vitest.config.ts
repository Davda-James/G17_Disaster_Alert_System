import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['../tests/frontend/**/*.{test,spec}.{ts,tsx}'],
    setupFiles: ['../tests/frontend/setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@testing-library/jest-dom': path.resolve(__dirname, './node_modules/@testing-library/jest-dom'),
      'react': path.resolve(__dirname, './node_modules/react'),
      '@testing-library/react': path.resolve(__dirname, './node_modules/@testing-library/react'),
      'react-dom': path.resolve(__dirname, './node_modules/react-dom'),
    },
  },
  server: {
    fs: {
      allow: ['..'],
    },
  },
})
