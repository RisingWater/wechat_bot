import React from 'react'
import { ConfigProvider } from 'antd-mobile'
import zhCN from 'antd-mobile/es/locales/zh-CN'
import MainTabs from './components/MainTabs'
import './App.css'

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <div className="app">
        <MainTabs />
      </div>
    </ConfigProvider>
  )
}

export default App