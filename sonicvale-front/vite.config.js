import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  base: './',  // 关键设置：让资源路径相对
  plugins: [vue()],
})
