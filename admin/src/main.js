import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as echarts from 'echarts'
import './assets/styles.css'

const app = createApp(App)
app.use(ElementPlus, { locale: zhCn })

window.echarts = echarts

app.mount('#app')
