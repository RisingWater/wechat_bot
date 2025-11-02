import React, { useState, useEffect } from 'react'
import { List, Button, Space, Toast, Tag } from 'antd-mobile'
import { AddOutline, DeleteOutline, EditSOutline } from 'antd-mobile-icons'
import ReminderForm from './ReminderForm'
import webserverApi from '../../services/api'

const RemindersManager = () => {
  const [reminders, setReminders] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [editingReminder, setEditingReminder] = useState(null)

  useEffect(() => {
    loadReminders()
  }, [])

  const loadReminders = async () => {
    try {
      const response = await webserverApi.getReminders()
      setReminders(response.data || [])
    } catch (error) {
      Toast.show('加载失败')
    }
  }

  // 格式化提醒时间描述
  const formatReminderTime = (reminder) => {
    const { calendar_type, month, day, hour, minute } = reminder
    
    // 处理月份
    let monthText = ''
    if (month === null) {
      monthText = '每月'
    } else {
      monthText = `${month}月`
    }
    
    // 处理日期
    let dayText = ''
    if (day === null) {
      dayText = '每天'
    } else {
      dayText = `${day}号`
    }
    
    // 处理时间
    const timeText = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`
    
    // 处理日历类型
    const calendarText = calendar_type === 'solar' ? '公历' : '农历'
    
    return `${calendarText} ${monthText}${dayText} ${timeText}`
  }

  const handleAdd = () => {
    setEditingReminder(null)
    setShowForm(true)
  }

  const handleEdit = (reminder) => {
    setEditingReminder(reminder)
    setShowForm(true)
  }

  const handleSave = () => {
    setShowForm(false)
    loadReminders()
  }

  const handleDelete = async (id) => {
    try {
      await webserverApi.deleteReminder(id)
      Toast.show('删除成功')
      loadReminders()
    } catch (error) {
      Toast.show('删除失败')
    }
  }

  if (showForm) {
    return (
      <ReminderForm
        reminder={editingReminder}
        onSave={handleSave}
        onCancel={() => setShowForm(false)}
      />
    )
  }

  return (
    <div style={{ padding: '16px' }}>
      <div style={{ marginBottom: '16px' }}>
        <Button color="primary" onClick={handleAdd} block>
          <AddOutline /> 添加提醒
        </Button>
      </div>

      <List>
        {reminders.map(reminder => (
          <List.Item
            key={reminder.id}
            extra={
              <Space>
                <Button size='mini' onClick={() => handleEdit(reminder)}>
                  <EditSOutline />
                </Button>
                <Button size='mini' color='danger' onClick={() => handleDelete(reminder.id)}>
                  <DeleteOutline />
                </Button>
              </Space>
            }
          >
            <div>
              <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                {reminder.title}
              </div>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                <Space align='center'>
                  <Tag 
                    color={reminder.enabled ? 'success' : 'default'}
                    style={{ fontSize: '10px', padding: '2px 6px' }}
                  >
                    {reminder.enabled ? '已启用' : '已禁用'}
                  </Tag>
                  <span>{formatReminderTime(reminder)}</span>
                </Space>
              </div>
              {reminder.description && (
                <div style={{ fontSize: '12px', color: '#999' }}>
                  {reminder.description}
                </div>
              )}
            </div>
          </List.Item>
        ))}
      </List>
    </div>
  )
}

export default RemindersManager