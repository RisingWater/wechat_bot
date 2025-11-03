import React, { useState, useEffect } from 'react'
import {
  Card,
  Button,
  SpinLoading,
  Toast,
  Image,
  List,
  Badge,
  Space,
  Divider,
  Modal
} from 'antd-mobile'
import {
  CheckCircleOutline,
  ClockCircleOutline,
  ExclamationCircleOutline,
  TransportQRcodeOutline,
  RedoOutline,
} from 'antd-mobile-icons'
import webserverApi from '../../services/api'

const WeChatStatus = () => {
  const [status, setStatus] = useState('checking') // checking, online, offline, logining, qrcode_required
  const [loading, setLoading] = useState(false)
  const [qrcodeData, setQrcodeData] = useState('')
  const [showQRCode, setShowQRCode] = useState(false)

  // 检查微信状态
  const checkWeChatStatus = async () => {
    try {
      setLoading(true)
      const result = await webserverApi.getWeChatStatus()
      
      if (result.status === 'success') {
        // 这里根据实际API返回的数据结构调整
        const wechatStatus = result.data.data?.status || 'offline'
        setStatus(wechatStatus)
        
        if (wechatStatus === 'online') {
          Toast.show('微信在线')
        } else if (wechatStatus === 'offline') {
          Toast.show('微信已离线')
        }
      } else {
        Toast.show('状态检查失败')
        setStatus('offline')
      }
    } catch (error) {
      Toast.show('网络错误')
      setStatus('offline')
    } finally {
      setLoading(false)
    }
  }

  // 尝试登录
  const handleLogin = async () => {
    try {
      setLoading(true)
      const result = await webserverApi.wechatLogin()
      
      if (result.status === 'success') {
        Toast.show('登录指令已发送，请等待...')
        setStatus('logining')
        // 30秒后重新检查状态
        setTimeout(() => {
          checkWeChatStatus()
        }, 30000)
      } else {
        Toast.show('登录失败，请尝试扫码登录')
        setStatus('qrcode_required')
      }
    } catch (error) {
      Toast.show('登录请求失败')
    } finally {
      setLoading(false)
    }
  }

  // 获取二维码
  const getQRCode = async () => {
    try {
      setLoading(true)
      const result = await webserverApi.getWeChatQRCode()
      
      if (result.status === 'success' && result.data.data?.qrcode_base64) {
        setQrcodeData(result.data.data.qrcode_base64)
        setShowQRCode(true)
        setStatus('qrcode_required')
      } else {
        Toast.show('获取二维码失败')
      }
    } catch (error) {
      Toast.show('获取二维码失败')
    } finally {
      setLoading(false)
    }
  }

  // 组件挂载时检查状态
  useEffect(() => {
    checkWeChatStatus()
    
    // 每30秒自动检查状态
    const interval = setInterval(() => {
      if (status !== 'logining' && status !== 'qrcode_required') {
        checkWeChatStatus()
      }
    }, 30000)
    
    return () => clearInterval(interval)
  }, [])

  // 状态显示配置
  const statusConfig = {
    checking: {
      icon: <ClockCircleOutline />,
      color: 'default',
      text: '检查中...',
      description: '正在检查微信状态'
    },
    online: {
      icon: <CheckCircleOutline />,
      color: 'success',
      text: '在线',
      description: '微信正常运行中'
    },
    offline: {
      icon: <ExclamationCircleOutline />,
      color: 'danger',
      text: '离线',
      description: '微信已断开连接'
    },
    logining: {
      icon: <ClockCircleOutline />,
      color: 'warning',
      text: '登录中',
      description: '微信正在登录，请等待约30秒...'
    },
    qrcode_required: {
      icon: <TransportQRcodeOutline />,
      color: 'warning',
      text: '需要扫码',
      description: '请扫描二维码登录微信'
    }
  }

  const currentStatus = statusConfig[status]

  return (
    <div style={{ padding: '16px' }}>
      <Card>
        {/* 状态显示 */}
        <List header="微信状态">
          <List.Item
            prefix={currentStatus.icon}
            extra={
              <Badge color={currentStatus.color}>
                {currentStatus.text}
              </Badge>
            }
            description={currentStatus.description}
          >
            微信连接状态
          </List.Item>
        </List>

        <Divider />

        {/* 操作按钮 */}
        <Space direction='vertical' style={{ width: '100%' }}>
          <Button
            color='primary'
            loading={loading}
            onClick={checkWeChatStatus}
            block
          >
            <RedoOutline /> 刷新状态
          </Button>

          {status === 'offline' && (
            <Button
              color='warning'
              loading={loading}
              onClick={handleLogin}
              block
            >
              尝试登录
            </Button>
          )}

          {(status === 'offline' || status === 'qrcode_required') && (
            <Button
              color='primary'
              loading={loading}
              onClick={getQRCode}
              block
            >
              <TransportQRcodeOutline /> 获取登录二维码
            </Button>
          )}
        </Space>
      </Card>

      {/* 二维码弹窗 */}
      <Modal
        visible={showQRCode}
        onClose={() => setShowQRCode(false)}
        title='微信登录二维码'
        content={
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            {qrcodeData ? (
              <>
                <Image
                  src={qrcodeData}
                  alt='微信登录二维码'
                  style={{ width: '200px', height: '200px', margin: '0 auto' }}
                />
                <p style={{ marginTop: '16px', color: '#999' }}>
                  请使用微信扫描二维码登录
                </p>
              </>
            ) : (
              <SpinLoading />
            )}
          </div>
        }
        actions={[
          {
            key: 'close',
            text: '关闭',
            onClick: () => setShowQRCode(false)
          }
        ]}
      />
    </div>
  )
}

export default WeChatStatus