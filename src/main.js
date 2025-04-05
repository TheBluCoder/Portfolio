import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import Toast from 'vue-toastification'
import "vue-toastification/dist/index.css";


const app = createApp(App)
const options = {
  maxToasts:1,
}
app.use(createPinia())
app.use(Toast,options)

app.mount('#app')
