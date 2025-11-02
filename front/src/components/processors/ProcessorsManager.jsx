import React, { useState, useEffect } from 'react'
import { List, Button, Space, Toast, Card, Checkbox, Modal, Input } from 'antd-mobile'
import { AddOutline, DeleteOutline, EditSOutline } from 'antd-mobile-icons'
import webserverApi from '../../services/api'

const ProcessorsManager = () => {
  const [processors, setProcessors] = useState([])
  const [chatnameProcessors, setChatnameProcessors] = useState([])
  const [loading, setLoading] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingChat, setEditingChat] = useState(null)
  const [newChatName, setNewChatName] = useState('')
  const [selectedProcessors, setSelectedProcessors] = useState([])

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [processorsRes, chatnameProcessorsRes] = await Promise.all([
        webserverApi.getProcessors(),
        webserverApi.getChatnameProcessors()
      ])

      console.log('processors 响应:', processorsRes)
      console.log('chatnameProcessors 响应:', chatnameProcessorsRes)
      
      setProcessors(processorsRes || [])
      setChatnameProcessors(chatnameProcessorsRes || [])
    } catch (error) {
      Toast.show('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAddChat = async () => {
    if (!newChatName.trim()) {
      Toast.show('请输入聊天名称')
      return
    }

    try {
      await webserverApi.addChatnameProcessor({ chat_name: newChatName.trim() })
      Toast.show('添加成功')
      setShowAddModal(false)
      setNewChatName('')
      loadData()
    } catch (error) {
      Toast.show('添加失败')
    }
  }

  const handleEditProcessors = async (chatName, currentProcessors) => {
    setEditingChat({ chatName, processors: currentProcessors })
    setSelectedProcessors(currentProcessors || [])
    setShowEditModal(true)
  }

  const handleUpdateProcessors = async () => {
    if (!editingChat) return

    try {
      await webserverApi.updateChatnameProcessor(editingChat.chatName, {
        processors: selectedProcessors
      })
      Toast.show('更新成功')
      setShowEditModal(false)
      setEditingChat(null)
      setSelectedProcessors([])
      loadData()
    } catch (error) {
      Toast.show('更新失败')
    }
  }

  const handleDeleteChat = async (chatName) => {
    Modal.confirm({
      content: `确定要删除 "${chatName}" 的配置吗？`,
      onConfirm: async () => {
        try {
          await webserverApi.deleteChatnameProcessor(chatName)
          Toast.show('删除成功')
          loadData()
        } catch (error) {
          Toast.show('删除失败')
        }
      }
    })
  }

  const toggleProcessor = (processorId) => {
    setSelectedProcessors(prev => 
      prev.includes(processorId)
        ? prev.filter(id => id !== processorId)
        : [...prev, processorId]
    )
  }

  const getProcessorName = (processorId) => {
    const processor = processors.find(p => p.id === processorId)
    return processor ? processor.name : processorId
  }

  const getProcessorDescription = (processorId) => {
    const processor = processors.find(p => p.id === processorId)
    let description = processor ? processor.description : ''
    
    // 如果描述以"处理器"结尾，删除这三个字
    if (description && description.endsWith('处理器')) {
      description = description.slice(0, -3)
    }
    
    return description
  }

  return (
    <div style={{ padding: '16px' }}>
      {/* 添加聊天配置 */}
      <div style={{ marginBottom: '16px' }}>
        <Button color="primary" onClick={() => setShowAddModal(true)} block>
          <AddOutline /> 添加聊天配置
        </Button>
      </div>

      {/* 聊天配置列表 */}
      <List>
        {chatnameProcessors.map(item => {
          console.log('正在渲染项目:', item)
          const processorList = Array.isArray(item.processors) 
            ? item.processors 
            : JSON.parse(item.processors || '[]')

            console.log('处理后的 processorList:', processorList)
          
          return (
            <List.Item
              key={item.id}
              extra={
                <Space>
                  <Button 
                    size='mini' 
                    onClick={() => handleEditProcessors(item.chat_name, processorList)}
                  >
                    <EditSOutline />
                  </Button>
                  <Button 
                    size='mini' 
                    color='danger' 
                    onClick={() => handleDeleteChat(item.chat_name)}
                  >
                    <DeleteOutline />
                  </Button>
                </Space>
              }
            >
              <div>
                <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                  {item.chat_name}
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  {processorList.length > 0 ? (
                    <Space wrap>
                      {processorList.map(processorId => (
                        <span key={processorId} style={{ 
                          background: '#f0f0f0', 
                          padding: '2px 6px', 
                          borderRadius: '4px',
                          fontSize: '10px'
                        }}>
                          {getProcessorDescription(processorId)}
                        </span>
                      ))}
                    </Space>
                  ) : (
                    <span style={{ color: '#999' }}>未配置处理器</span>
                  )}
                </div>
              </div>
            </List.Item>
          )
        })}
      </List>

      {/* 添加聊天模态框 */}
      <Modal
        visible={showAddModal}
        title="添加聊天配置"
        content={
          <div style={{ padding: '16px 0' }}>
            <Input
              placeholder="输入微信聊天名称"
              value={newChatName}
              onChange={setNewChatName}
            />
          </div>
        }
        closeOnAction
        onClose={() => setShowAddModal(false)}
        actions={[
          { key: 'cancel', text: '取消' },
          { key: 'confirm', text: '确定', primary: true, onClick: handleAddChat }
        ]}
      />

      {/* 配置处理器模态框 */}
      <Modal
        visible={showEditModal}
        title={`配置处理器 - ${editingChat?.chatName}`}
        content={
          <div style={{ padding: '16px 0', maxHeight: '400px', overflow: 'auto' }}>
            {processors.map(processor => (
              <Card key={processor.id} style={{ marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ fontWeight: 'bold' }}>{getProcessorDescription(processor.id)}</div>
                  </div>
                  <Checkbox
                    checked={selectedProcessors.includes(processor.id)}
                    onChange={() => toggleProcessor(processor.id)}
                  />
                </div>
              </Card>
            ))}
          </div>
        }
        closeOnAction
        onClose={() => {
          setShowEditModal(false)
          setEditingChat(null)
          setSelectedProcessors([])
        }}
        actions={[
          { key: 'cancel', text: '取消' },
          { key: 'confirm', text: '确定', primary: true, onClick: handleUpdateProcessors }
        ]}
      />
    </div>
  )
}

export default ProcessorsManager