import axios from 'axios'

// 根据你的后端地址调整
//const API_BASE = 'http://localhost:6017'
const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const webserverApi = {
  // 提醒相关
  getReminders: () => api.get('/reminders'),
  addReminder: (data) => api.post('/reminders', data),
  updateReminder: (id, data) => api.put(`/reminders/${id}`, data),
  deleteReminder: (id) => api.delete(`/reminders/${id}`),
  
  // chatname_processors 相关
  getChatnameProcessors: () => api.get('/chatname_processors'),
  addChatnameProcessor: (data) => api.post('/chatname_processors', data),
  updateChatnameProcessor: (chatName, data) => api.put(`/chatname_processors/${chatName}`, data),
  deleteChatnameProcessor: (chatName) => api.delete(`/chatname_processors/${chatName}`),
  
  // processors 相关
  getProcessors: () => api.get('/processors'),
}

export default webserverApi