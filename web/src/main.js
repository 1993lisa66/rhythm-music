import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
/* 1. normalize.css 抹平浏览器默认差异 → 2. 设计令牌 → 3. 项目基础样式 */
import 'normalize.css'
import './styles/tokens.css'
import './styles/base.css'

createApp(App).use(router).mount('#app')
