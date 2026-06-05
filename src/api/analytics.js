import {
  ANALYTICS_OVERVIEW_MOCK,
  EXEC_RUNS_MOCK,
  API_CALLS_MOCK,
  PUSH_LOGS_MOCK,
  USERS_MOCK,
  USER_DETAIL_MOCK,
} from '@/mock/analyticsData'

const USE_MOCK = true

function mockDelay(ms = 300) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function fetchAnalyticsOverview(range = 'month') {
  if (USE_MOCK) {
    await mockDelay()
    return ANALYTICS_OVERVIEW_MOCK[range] ?? ANALYTICS_OVERVIEW_MOCK.month
  }
  const { default: pluginAPI } = await import('@/utils/request')
  const res = await pluginAPI.get('/analytics/overview', { params: { range } })
  return res.data?.data
}

export async function fetchExecRuns(range = 'day') {
  if (USE_MOCK) {
    await mockDelay()
    return EXEC_RUNS_MOCK[range] ?? EXEC_RUNS_MOCK.day
  }
  const { default: pluginAPI } = await import('@/utils/request')
  const res = await pluginAPI.get('/analytics/exec-runs', { params: { range } })
  return res.data?.data
}

export async function fetchApiCalls(range = 'day') {
  if (USE_MOCK) {
    await mockDelay()
    return API_CALLS_MOCK[range] ?? API_CALLS_MOCK.day
  }
  const { default: pluginAPI } = await import('@/utils/request')
  const res = await pluginAPI.get('/analytics/api-calls', { params: { range } })
  return res.data?.data
}

export async function fetchPushLogs(range = 'day') {
  if (USE_MOCK) {
    await mockDelay()
    return PUSH_LOGS_MOCK[range] ?? PUSH_LOGS_MOCK.day
  }
  const { default: pluginAPI } = await import('@/utils/request')
  const res = await pluginAPI.get('/analytics/push-logs', { params: { range } })
  return res.data?.data
}

export async function fetchUsers(range = 'month') {
  if (USE_MOCK) {
    await mockDelay()
    return USERS_MOCK[range] ?? USERS_MOCK.month
  }
  const { default: pluginAPI } = await import('@/utils/request')
  const res = await pluginAPI.get('/analytics/users', { params: { range } })
  return res.data?.data
}

export async function fetchUserDetail(userId) {
  if (USE_MOCK) {
    await mockDelay()
    return { ...USER_DETAIL_MOCK, userId }
  }
  const { default: pluginAPI } = await import('@/utils/request')
  const res = await pluginAPI.get(`/analytics/users/${userId}/detail`)
  return res.data?.data
}

export async function updateUserRemark(userId, remark) {
  if (USE_MOCK) {
    await mockDelay(100)
    return { updated: true }
  }
  const { default: pluginAPI } = await import('@/utils/request')
  const res = await pluginAPI.put(`/analytics/users/${userId}/remark`, { remark })
  return res.data?.data
}
