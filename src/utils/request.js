import axios from 'axios'

// 创建axios实例
const pluginAPI = axios.create({
  // baseURL: 'api',
  // baseURL: 'https://api.yddm.com', // 设置baseURL
  baseURL: 'https://feishu.jzl.com/api/v1/public',
  // baseURL: 'http://192.168.1.151:8181/public',
  timeout: 15 * 1000, // 请求超时时间
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
    console.log(error)
    return Promise.reject(error)
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
      
      // 延迟重试，使用指数退避
      return new Promise(resolve => setTimeout(resolve, RETRY_DELAY * config._retryCount))
        .then(() => pluginAPI.request(config))
    }
    
    // 重试次数用尽，返回原始响应（由调用方处理）
    console.error(`请求失败，重试${MAX_RETRY_COUNT}次后仍未成功，响应码不为0`)
    return response
  },
  error => {
    console.log('请求错误：', error)
    
    // 如果是请求错误，尝试重试
    const config = error.config
    if (config) {
      config._retryCount = config._retryCount || 0
      
      if (config._retryCount < MAX_RETRY_COUNT) {
        config._retryCount++
        console.log(`请求失败，正在进行第 ${config._retryCount} 次重试: ${error.message}`)
        
        // 延迟重试，使用指数退避
        return new Promise(resolve => setTimeout(resolve, RETRY_DELAY * config._retryCount))
          .then(() => pluginAPI.request(config))
      }
    }
    
    return Promise.reject(error)
  }
)

export default pluginAPI