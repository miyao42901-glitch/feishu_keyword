import axios from 'axios'

// 创建axios实例
const pluginAPI = axios.create({
  // baseURL: 'api',
  // baseURL: 'https://api.yddm.com', // 设置baseURL
  baseURL: 'http://127.0.0.1:8181/public',
  timeout: 10000, // 请求超时时间
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

export default pluginAPI
