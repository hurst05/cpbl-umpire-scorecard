import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

function staticDataPlugin(isStatic) {
  return {
    name: 'static-data-copy',
    closeBundle() {
      if (!isStatic) return
      const srcDir = path.resolve(__dirname, '.static-export', 'data')
      const destDir = path.resolve(__dirname, 'dist', 'data')

      if (!fs.existsSync(srcDir)) {
        throw new Error('[Vite Static Build Error] .static-export/data 目錄不存在。請先執行 "pnpm run export:static"。')
      }

      fs.cpSync(srcDir, destDir, { recursive: true })
      const destManifest = path.join(destDir, 'manifest.json')
      if (!fs.existsSync(destManifest)) {
        throw new Error('[Vite Static Build Error] 複製靜態資料失敗，未在 dist/data 找到 manifest.json。')
      }

      console.log('[Vite Build] Copied .static-export/data to dist/data')
    }
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const isStatic = mode === 'static' || env.VITE_DATA_MODE === 'static'
  const basePath = env.VITE_BASE_PATH || (process.env.NODE_ENV === 'production' ? '/cpbl-umpire-scorecard/' : '/')

  return {
    base: basePath,
    plugins: [
      vue(),
      tailwindcss(),
      staticDataPlugin(isStatic)
    ],
    server: {
      host: '127.0.0.1',
      port: 5173,
      strictPort: true,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true
        }
      }
    }
  }
})
