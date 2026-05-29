import { createApp } from 'vue'
import App from './App.vue'
import './assets/main.css'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { i18n } from './locales/i18n.js'

const app = createApp(App)
app.use(i18n)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
