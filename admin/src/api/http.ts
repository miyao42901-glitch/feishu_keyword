import axios from 'axios'
import { ElMessage } from 'element-plus'
import { ADMIN_API_ORIGIN } from '@/config/adminApiOrigin'
import { useSessionStore } from '@/stores/session'

const http = axios.create({
  baseURL: import.meta.env.PROD ? ADMIN_API_ORIGIN : '',
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  const s = useSessionStore()
  if (s.token) {
    config.headers.token = s.token
  }
  return config
})

http.interceptors.response.use(
  (res) => {
    const data = res.data
    if (data && typeof data.code === 'number') {
      if (data.code === 200) {
        return res
      }
      ElMessage.error(data.msg || '请求失败')
      return Promise.reject(new Error(data.msg || 'biz_error'))
    }
    return res
  },
  (err) => {
    ElMessage.error(err?.message || '网络错误')
    return Promise.reject(err)
  },
)

export function unwrap<T>(res: { data: { code: number; msg: string; data: T } }): T {
  return res.data.data
}

export default http
