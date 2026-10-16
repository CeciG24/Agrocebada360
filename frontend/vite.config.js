import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', 'VITE_')
  const target = env.VITE_API_TARGET || 'http://127.0.0.1:8000'
  const proxy = Object.fromEntries([
    '^/health(?:\\?|$)', '^/parcels(?:\\?|$)', '^/parcel/', '^/predict/', '^/explain/', '^/risk/', '^/regions/',
  ].map((route) => [route, { target, changeOrigin: true }]))
  return {
  plugins: [
    react(),
    babel({ presets: [reactCompilerPreset()] })
  ],
  server: { proxy },
  preview: { proxy },
  }
})
