import React from 'react'
import { Tabs } from 'antd-mobile'
import RemindersManager from './reminders/RemindersManager'
import ProcessorsManager from './processors/ProcessorsManager'
import WeChatStatus from './wechat_status/WeChatStatus'

const MainTabs = () => {
  return (
    <Tabs>
      <Tabs.Tab title='提醒管理' key='reminders'>
        <RemindersManager />
      </Tabs.Tab>
      <Tabs.Tab title='处理器配置' key='processors'>
        <ProcessorsManager />
      </Tabs.Tab>
      <Tabs.Tab title='微信状态' key='wechat'>
        <WeChatStatus />
      </Tabs.Tab>
    </Tabs>
  )
}

export default MainTabs