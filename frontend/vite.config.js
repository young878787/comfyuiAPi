import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

const projectRoot = fileURLToPath(new URL('..', import.meta.url))

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, projectRoot, '')
  // 優先使用 process.env 的環境變數，以利啟動腳本動態傳入
  const backendPort = process.env.BACKEND_PORT || env.BACKEND_PORT || env.APP_PORT || '8000'
  const backendHost = process.env.APP_HOST || (env.APP_HOST && env.APP_HOST !== '0.0.0.0' ? env.APP_HOST : '127.0.0.1')
  const backendTarget = `http://${backendHost}:${backendPort}`

  const frontendPort = parseInt(process.env.PORT || env.PORT || '15005')

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    server: {
      port: frontendPort,
      proxy: {
        '/api': {
          target: backendTarget,
          changeOrigin: true,
        }
      }
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets'
    }
  }
})
