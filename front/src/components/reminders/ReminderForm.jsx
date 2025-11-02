import React, { useState, useEffect } from 'react'
import {
  Form,
  Input,
  Button,
  Radio,
  Space,
  Toast,
  Picker,
  Tag,
} from 'antd-mobile'
import webserverApi from '../../services/api'

const ReminderForm = ({ reminder, onSave, onCancel }) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [monthVisible, setMonthVisible] = useState(false)
  const [dayVisible, setDayVisible] = useState(false)
  const [currentMonth, setCurrentMonth] = useState(null)
  const [currentDay, setCurrentDay] = useState(null)
  const [currentCalendarType, setCurrentCalendarType] = useState('solar')
  const [currentEnabled, setCurrentEnabled] = useState(true)
  const [chatnamesInput, setChatnamesInput] = useState('') // 联系人输入状态

  // 月份选项
  const monthOptions = [
    { label: '每月', value: null },
    { label: '1月', value: 1 },
    { label: '2月', value: 2 },
    { label: '3月', value: 3 },
    { label: '4月', value: 4 },
    { label: '5月', value: 5 },
    { label: '6月', value: 6 },
    { label: '7月', value: 7 },
    { label: '8月', value: 8 },
    { label: '9月', value: 9 },
    { label: '10月', value: 10 },
    { label: '11月', value: 11 },
    { label: '12月', value: 12 },
  ]

  // 日期选项
  const dayOptions = [
    { label: '每天', value: null },
    { label: '1日', value: 1 },
    { label: '2日', value: 2 },
    { label: '3日', value: 3 },
    { label: '4日', value: 4 },
    { label: '5日', value: 5 },
    { label: '6日', value: 6 },
    { label: '7日', value: 7 },
    { label: '8日', value: 8 },
    { label: '9日', value: 9 },
    { label: '10日', value: 10 },
    { label: '11日', value: 11 },
    { label: '12日', value: 12 },
    { label: '13日', value: 13 },
    { label: '14日', value: 14 },
    { label: '15日', value: 15 },
    { label: '16日', value: 16 },
    { label: '17日', value: 17 },
    { label: '18日', value: 18 },
    { label: '19日', value: 19 },
    { label: '20日', value: 20 },
    { label: '21日', value: 21 },
    { label: '22日', value: 22 },
    { label: '23日', value: 23 },
    { label: '24日', value: 24 },
    { label: '25日', value: 25 },
    { label: '26日', value: 26 },
    { label: '27日', value: 27 },
    { label: '28日', value: 28 },
    { label: '29日', value: 29 },
    { label: '30日', value: 30 },
    { label: '31日', value: 31 },
  ]

  useEffect(() => {
    if (reminder) {
      // 处理 chatnames - 从 JSON 字符串解析回数组
      let chatnamesArray = []
      if (reminder.chatnames) {
        try {
          if (typeof reminder.chatnames === 'string') {
            chatnamesArray = JSON.parse(reminder.chatnames)
          } else if (Array.isArray(reminder.chatnames)) {
            chatnamesArray = reminder.chatnames
          }
        } catch (error) {
          console.error('解析 chatnames 失败:', error)
          chatnamesArray = []
        }
      }
      
      // 确保所有字段都有正确的值
      const formData = {
        title: reminder.title || '',
        description: reminder.description || '',
        calendar_type: reminder.calendar_type || 'solar',
        month: reminder.month !== undefined ? reminder.month : null,
        day: reminder.day !== undefined ? reminder.day : null,
        hour: reminder.hour || 8,
        minute: reminder.minute || 0,
        enabled: reminder.enabled !== false,
        chatnames: chatnamesArray // 使用解析后的数组
      }
      
      console.log('设置表单数据:', formData) // 调试
      form.setFieldsValue(formData)
      setCurrentMonth(reminder.month)
      setCurrentDay(reminder.day)
      setCurrentCalendarType(reminder.calendar_type || 'solar')
      setCurrentEnabled(reminder.enabled !== false)
      setChatnamesInput(chatnamesArray.join('、'))
    } else {
      const defaultData = {
        calendar_type: 'solar',
        hour: 8,
        minute: 0,
        enabled: true,
        month: null,
        day: null,
        chatnames: [] // 明确设置为空数组
      }
      console.log('设置默认数据:', defaultData) // 调试
      form.setFieldsValue(defaultData)
      setCurrentMonth(null)
      setCurrentDay(null)
      setCurrentCalendarType('solar')
      setCurrentEnabled(true)
      setChatnamesInput('')
    }
  }, [reminder, form])

  // 修改 Picker 的 onConfirm
  const handleMonthConfirm = (value) => {
    form.setFieldValue('month', value[0])
    setCurrentMonth(value[0])
    setMonthVisible(false)
  }

  const handleDayConfirm = (value) => {
    form.setFieldValue('day', value[0])
    setCurrentDay(value[0])
    setDayVisible(false)
  }

  const handleChatnamesChange = (value) => {
    setChatnamesInput(value)
    form.setFieldValue('chatnames', value)
  }

  const handleSubmit = async (values) => {
    setLoading(true)
    try {
      console.log('提交的数据:', values)
      var chatnames = values.chatnames
      var names
      if (!Array.isArray(chatnames)) {
        // 将输入的字符串转换为数组（用顿号、逗号或空格分隔）
        names = chatnames.split(/[、,，\s]+/).filter(name => name.trim() !== '')
        console.log('转换后的数组:', names)  
      } else {
        names = chatnames
      }
      
      // 确保数据格式正确
      const submitData = {
        title: values.title,
        description: values.description || '',
        calendar_type: values.calendar_type,
        month: values.month,
        day: values.day,
        hour: parseInt(values.hour) || 0,
        minute: parseInt(values.minute) || 0,
        enabled: values.enabled !== false,
        chatnames: JSON.stringify(names || [])
      }
      
      console.log('最终提交的数据:', submitData)
      
      if (reminder) {
        const response = await webserverApi.updateReminder(reminder.id, submitData)
        console.log('更新响应:', response)
        Toast.show('更新成功')
      } else {
        const response = await webserverApi.addReminder(submitData)
        console.log('添加响应:', response)
        Toast.show('添加成功')
      }
      onSave()
    } catch (error) {
      console.error('提交错误:', error)
      Toast.show(reminder ? '更新失败' : '添加失败')
    } finally {
      setLoading(false)
    }
  }

  // 获取显示的文本
  const getDisplayText = (value, options) => {
    if (value === null || value === undefined) {
      return options[0].label
    }
    const item = options.find(item => item.value === value)
    return item ? item.label : options[0].label
  }

  const getCurrentChatnames = () => {
    const value = form.getFieldValue('chatnames')
    // 确保返回的是数组
    if (Array.isArray(value)) {
      return value
    }
    // 如果是字符串，尝试解析
    if (typeof value === 'string') {
      try {
        const parsed = JSON.parse(value)
        return Array.isArray(parsed) ? parsed : []
      } catch {
        return []
      }
    }
    // 其他情况返回空数组
    return []
  }

  return (
    <div style={{ padding: '16px' }}>
      <Form
        form={form}
        onFinish={handleSubmit}
        footer={
          <Space direction='vertical' block>
            <Button 
              type='submit' 
              color='primary' 
              block 
              loading={loading}
            >
              {reminder ? '更新' : '添加'}
            </Button>
            <Button block onClick={onCancel}>
              取消
            </Button>
          </Space>
        }
      >
        <Form.Item
          name='title'
          label='提醒标题'
          rules={[{ required: true, message: '请输入提醒标题' }]}
        >
          <Input placeholder='例如：生日快乐' />
        </Form.Item>

        <Form.Item name='description' label='描述'>
          <Input placeholder='提醒的详细描述（可选）' />
        </Form.Item>

        {/* 联系人设置 */}
        <Form.Item
          name='chatnames'
          label='提醒对象'
          help='输入微信联系人姓名，用顿号、逗号或空格分隔'
        >
          <div>
            <Input 
              value={chatnamesInput}
              onChange={handleChatnamesChange}
              placeholder='例如：张三、李四、王五'
            />
            {getCurrentChatnames().length > 0 && (
              <div style={{ marginTop: '8px' }}>
                <Space wrap>
                  {getCurrentChatnames().map((name, index) => (
                    <Tag key={index} color='primary' style={{ fontSize: '12px' }}>
                      {name}
                    </Tag>
                  ))}
                </Space>
              </div>
            )}
          </div>
        </Form.Item>

        <Form.Item
          name='calendar_type'
          label='日历类型'
          rules={[{ required: true, message: '请选择日历类型' }]}
        >
          <Radio.Group
            value={form.getFieldValue('calendar_type')}
            onChange={(value) => form.setFieldValue('calendar_type', value)}
            >
            <Space>
              <Radio value='solar'>公历</Radio>
              <Radio value='lunar'>农历</Radio>
            </Space>
          </Radio.Group>
        </Form.Item>

        {/* 月份选择 */}
        <Form.Item name='month' label='月份'>
          <div 
            onClick={() => setMonthVisible(true)}
            style={{ 
              padding: '8px 12px', 
              border: '1px solid #e5e5e5', 
              borderRadius: '4px',
              background: '#fff',
              color: form.getFieldValue('month') ? '#000' : '#999'
            }}
          >
            {getDisplayText(form.getFieldValue('month'), monthOptions)}
          </div>
          <Picker
            columns={[monthOptions]}
            visible={monthVisible}
            onClose={() => setMonthVisible(false)}
            onConfirm={handleMonthConfirm}
          />
        </Form.Item>

        {/* 日期选择 */}
        <Form.Item name='day' label='日期'>
          <div 
            onClick={() => setDayVisible(true)}
            style={{ 
              padding: '8px 12px', 
              border: '1px solid #e5e5e5', 
              borderRadius: '4px',
              background: '#fff',
              color: form.getFieldValue('day') ? '#000' : '#999'
            }}
          >
            {getDisplayText(form.getFieldValue('day'), dayOptions)}
          </div>
          <Picker
            columns={[dayOptions]}
            visible={dayVisible}
            onClose={() => setDayVisible(false)}
            onConfirm={handleDayConfirm}
          />
        </Form.Item>

        {/* 时间设置 */}
        <Form.Item
          name='time'
          label='时间'
        >
          <Space align='center' style={{ '--gap': '8px' }}>
            <Form.Item
              name='hour'
              noStyle
              rules={[{ required: true, message: '请设置小时' }]}
            >
              <Input 
                type='number' 
                min='0' 
                max='23' 
                placeholder='0'
                style={{ width: '60px', textAlign: 'center' }}
              />
            </Form.Item>
            <span style={{ color: '#999' }}>点</span>
            <Form.Item
              name='minute'
              noStyle
              rules={[{ required: true, message: '请设置分钟' }]}
            >
              <Input 
                type='number' 
                min='0' 
                max='59' 
                placeholder='0'
                style={{ width: '60px', textAlign: 'center' }}
              />
            </Form.Item>
            <span style={{ color: '#999' }}>分</span>
          </Space>
        </Form.Item>

        <Form.Item name='enabled' label='状态'>
          <Radio.Group
            value={form.getFieldValue('enabled')}
            onChange={(value) => form.setFieldValue('enabled', value)}
            >
            <Space>
              <Radio value={true}>启用</Radio>
              <Radio value={false}>禁用</Radio>
            </Space>
          </Radio.Group>
        </Form.Item>
      </Form>
    </div>
  )
}

export default ReminderForm