import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)

console.log('[DEBUG] createApp done')
app.use(createPinia())
console.log('[DEBUG] Pinia installed')
app.use(router)
console.log('[DEBUG] Router installed')
app.use(ElementPlus)
console.log('[DEBUG] ElementPlus installed')

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}
console.log('[DEBUG] Icons registered')

app.mount('#app')
console.log('[DEBUG] App mounted')
