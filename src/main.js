import { createApp } from 'vue'
import App from './App.vue'

// 1. 引入 Vant 样式
import 'vant/lib/index.css';

// 2. 引入 Vant 组件
// 新增了 Tab, Tabs, Icon 等组件
import { 
  Button, 
  NavBar, 
  Card, 
  Tag, 
  Empty, 
  PullRefresh, 
  Tab, 
  Tabs, 
  Icon, 
  Loading 
} from 'vant';

import './assets/main.css'

const app = createApp(App)

// 3. 注册组件
app.use(Button)
app.use(NavBar)
app.use(Card)
app.use(Tag)
app.use(Empty)
app.use(PullRefresh)
app.use(Tab)  // 必须注册
app.use(Tabs) // 必须注册
app.use(Icon)
app.use(Loading)

app.mount('#app')