import axios from 'axios'

const API_BASE_URL = import.meta.env.DEV
  ? '/api/v1/public'
  : 'https://feishu.jzl.com/api/v1/public'

const DIRECT_API_BASE_URL = import.meta.env.DEV
  ? '/direct-api'
  : 'https://www.dajiala.com'

// 创建axios实例
const pluginAPI = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20 * 1000, // 请求超时时间
})

export const directAPI = axios.create({
  baseURL: DIRECT_API_BASE_URL,
  timeout: 20 * 1000,
})

// 网络错误消息
const NETWORK_ERROR = '网络连接错误'

// 最大重试次数
const MAX_RETRY_COUNT = 3
// 重试延迟（毫秒）
const RETRY_DELAY = 1000

// 检查响应是否合法（code=0 或 error_code=0）
const isValidResponse = (response) => {
  if (!response || !response.data) return false

  const data = response.data
  // 检查 code 或 error_code 是否为 0
  return (data.code !== undefined && data.code === 0) || 
         (data.error_code !== undefined && data.error_code === 0)
}

// 请求拦截器
pluginAPI.interceptors.request.use(
  config => {
    // 在发送请求之前可以做些什么，比如添加token
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers['Authorization'] = 'Bearer ' + token
    // }
    // 初始化重试计数
    config._retryCount = config._retryCount || 0
    return config
  },
  error => {
    console.error('请求配置错误：', error)
    return Promise.resolve({
      data: {
        code: -1,
        error_code: -1,
        msg: NETWORK_ERROR,
        data: null
      }
    })
  }
)

// 响应拦截器 - 包含重试机制
pluginAPI.interceptors.response.use(
  response => {
    // 检查响应是否合法
    if (isValidResponse(response)) {
      return response
    }
    
    // 如果响应不合法，触发重试逻辑
    const config = response.config
    config._retryCount = config._retryCount || 0
    
    if (config._retryCount < MAX_RETRY_COUNT) {
      config._retryCount++
      console.log(`响应不合法(code不为0)，正在进行第 ${config._retryCount} 次重试...`)
      
      // 延迟重试，使用线性退避
      return new Promise(resolve => setTimeout(resolve, RETRY_DELAY * config._retryCount))
        .then(() => pluginAPI.request(config))
    }
    
    // 重试次数用尽，非网络错误直接返回最后一次原始响应
    console.error(`请求失败，重试${MAX_RETRY_COUNT}次后仍未成功，返回最后一次响应`)
    return response
  },
  error => {
    console.error('请求错误：', error)
    
    // 如果是请求错误，尝试重试
    const config = error.config
    if (config) {
      config._retryCount = config._retryCount || 0
      
      if (config._retryCount < MAX_RETRY_COUNT) {
        config._retryCount++
        console.log(`请求失败，正在进行第 ${config._retryCount} 次重试: ${error.message}`)
        
        // 延迟重试，使用线性退避
        return new Promise(resolve => setTimeout(resolve, RETRY_DELAY * config._retryCount))
          .then(() => pluginAPI.request(config))
      }
    }
    
    // 获取HTTP响应码，没有则使用-1
    const httpCode = error.response?.status || -1
    const errorMsg = error.response?.statusText || NETWORK_ERROR
    
    // 网络错误返回统一错误响应
    console.warn(`网络错误，已达到最大重试次数，HTTP响应码: ${httpCode}，返回默认响应`)
    return {
      data: {
        code: httpCode,
        error_code: httpCode,
        msg: errorMsg,
        data: null
      }
    }
  }
)

export default pluginAPI