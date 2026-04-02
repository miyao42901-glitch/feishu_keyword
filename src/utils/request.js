import axios from 'axios'

// 创建axios实例
const pluginAPI = axios.create({
  // baseURL: 'api',
  // baseURL: 'https://api.yddm.com', // 设置baseURL
  baseURL: 'https://www.dajiala.com',
  timeout: 10000 // 请求超时时间
})

// 网络错误消息
const NETWORK_ERROR = '网络连接错误'

// 请求拦截器
pluginAPI.interceptors.request.use(
  config => {
    // 在发送请求之前可以做些什么，比如添加token
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers['Authorization'] = 'Bearer ' + token
    // }
    return config
  },
  error => {
    console.log(error)
    return Promise.reject(error)
  }
)

// 响应拦截器
pluginAPI.interceptors.response.use(
  response => {
    // 对响应数据做点什么
    return response
  },
  error => {
    console.log('请求错误：', error)
    return Promise.reject(error)
  }
)

// 添加重试功能的包装函数
const withRetry = async (requestFn, maxRetries = 3, retryDelay = 1000) => {
  let lastResponse = null
  let lastError = null
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await requestFn()
      
      if (response.data && response.data.code){
        lastResponse = response
      }
      // 检查是否有 code 字段，并且 code 为 0
      if (response.data && response.data.code === 0) {
        return response
      }
      
      // 如果 code 不为 0，继续重试
      console.log(`请求返回 code 不为 0 (${response.data.code})，正在重试 ${i + 1}/${maxRetries}...`)
    } catch (error) {
      lastError = error
      console.log(`请求失败，正在重试 ${i + 1}/${maxRetries}...`)
    }
    
    // 等待指定时间后重试
    if (i < maxRetries - 1) {
      await new Promise(resolve => setTimeout(resolve, retryDelay))
    }
  }
  if (lastResponse) {
    return lastResponse
  }
  else{
    return {
      data: {
        code: -1,
        msg: NETWORK_ERROR,
      }
    }
  }
  
}

// 包装 pluginAPI 的方法，添加重试功能
const enhancedPluginAPI = {
  ...pluginAPI,
  get: async (url, config) => {
    return withRetry(() => pluginAPI.get(url, config))
  },
  post: async (url, data, config) => {
    return withRetry(() => pluginAPI.post(url, data, config))
  },
  put: async (url, data, config) => {
    return withRetry(() => pluginAPI.put(url, data, config))
  },
  delete: async (url, config) => {
    return withRetry(() => pluginAPI.delete(url, config))
  }
}

export default enhancedPluginAPI