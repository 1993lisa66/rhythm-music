import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: '127.0.0.1',
    port: 5173,
    open: false,
    // 开发期把接口与封面转发到本机后端（uvicorn 默认 8000），避免前端出现跨域
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/covers': { target: 'http://127.0.0.1:8000', changeOrigin: true }
    }
  }
})
