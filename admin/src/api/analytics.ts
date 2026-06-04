import http, { unwrap } from '@/api/http'

export type AnalyticsRange = 'day' | 'week' | 'month'

export interface AnalyticsOverviewKpis {
  activeTasks: string | number
  execRate: string
  apiRate: string
  points: string | number
  retention: string
  avgTasks: string
  pushRate: string
  activeUsers: string | number
  compare: string
  newUsers: string
}

export interface AnalyticsOverviewCharts {
  trend: {
    labels: string[]
    activeUsers: number[]
    execCounts: number[]
  }
  taskStatus: Array<{ name: string; value: number }>
  platformApi: { labels: string[]; values: number[] }
  topUsers: { labels: string[]; values: number[] }
}

export interface AnalyticsOverviewFunnel {
  steps: Array<{ label: string; value: number; note: string; loss: string }>
  losses: Array<{ title: string; count: string; desc: string }>
  conversionRate: string
  rangeLabel?: string
}

export interface AnalyticsOverviewData {
  range: AnalyticsRange
  kpis: AnalyticsOverviewKpis
  charts: AnalyticsOverviewCharts
  funnel: AnalyticsOverviewFunnel
  empty?: boolean
}

export async function fetchAnalyticsOverview(range: AnalyticsRange): Promise<AnalyticsOverviewData> {
  const res = await http.get<{ code: number; msg: string; data: AnalyticsOverviewData }>(
    '/api/admin/v1/analytics/overview',
    { params: { range } },
  )
  return unwrap(res)
}

export interface ExecRecord {
  execId: string
  taskId: string
  userId: string
  taskType: string
  startedAt: string
  endedAt: string
  durationMs: number
  result: string
  failReason: string
  points: number
  collectCount: number
}

export interface ExecRunsData {
  range: AnalyticsRange
  total: number
  success: number
  successRate: string
  avgDurationMs: number
  records: ExecRecord[]
}

export async function fetchExecRuns(range: AnalyticsRange): Promise<ExecRunsData> {
  const res = await http.get<{ code: number; msg: string; data: ExecRunsData }>(
    '/api/admin/v1/analytics/exec-runs',
    { params: { range } },
  )
  return unwrap(res)
}

export interface ApiCallRecord {
  requestId: string
  taskId: string
  execId: string
  platform: string
  calledAt: string
  result: string
  errorCode: string
  latencyMs: number
}

export interface PlatformStat {
  platform: string
  total: number
  success: number
  successRate: string
}

export interface ApiCallsData {
  range: AnalyticsRange
  total: number
  success: number
  successRate: string
  avgLatencyMs: number
  platformStats: PlatformStat[]
  records: ApiCallRecord[]
}

export async function fetchApiCalls(range: AnalyticsRange): Promise<ApiCallsData> {
  const res = await http.get<{ code: number; msg: string; data: ApiCallsData }>(
    '/api/admin/v1/analytics/api-calls',
    { params: { range } },
  )
  return unwrap(res)
}

export interface PushLogRecord {
  pushId: string
  taskId: string
  userId: string
  webhook: string
  sendAt: string
  sendResult: string
  callbackAt: string
  callbackResult: string
  newDataCount: number
  errorCode: string
  retryCount: number
}

export interface PushLogsData {
  range: AnalyticsRange
  total: number
  sendSuccess: number
  callbackSuccess: number
  deliveryRate: string
  notifyOnCount: number
  notifyOffCount: number
  records: PushLogRecord[]
}

export async function fetchPushLogs(range: AnalyticsRange): Promise<PushLogsData> {
  const res = await http.get<{ code: number; msg: string; data: PushLogsData }>(
    '/api/admin/v1/analytics/push-logs',
    { params: { range } },
  )
  return unwrap(res)
}

export interface AnalyticsUserRecord {
  userId: string
  feishuId: string
  phone: string
  deviceType: string
  pluginVersion: string
  remark: string
  firstUseAt: string
  lastActiveAt: string
  activeHours: string
  taskCount: number
  pointsConsumed: number
}

export interface UsersData {
  range: AnalyticsRange
  totalUsers: number
  activeUsers: number
  newUsers: number
  retention: string
  records: AnalyticsUserRecord[]
}

export interface UserDetailTask {
  taskId: string
  taskType: string
  keywordCount: number
  platforms: string[]
  status: string
  createdAt: string
}

export interface UserDetailPoint {
  consumeId: string
  taskId: string
  platform: string
  amount: number
  balance: number
  consumedAt: string
}

export interface UserDetail {
  userId: string
  feishuId: string
  phone: string
  deviceType: string
  pluginVersion: string
  remark: string
  firstUseAt: string
  lastActiveAt: string
  activeHours: string
  taskCount: number
  execCount: number
  execSuccessRate: string
  totalPoints: number
  tasks: UserDetailTask[]
  points: UserDetailPoint[]
}

export async function fetchUsers(range: AnalyticsRange): Promise<UsersData> {
  const res = await http.get<{ code: number; msg: string; data: UsersData }>(
    '/api/admin/v1/analytics/users',
    { params: { range } },
  )
  return unwrap(res)
}

export async function fetchUserDetail(userId: string): Promise<UserDetail> {
  const res = await http.get<{ code: number; msg: string; data: UserDetail }>(
    `/api/admin/v1/analytics/users/${userId}/detail`,
  )
  return unwrap(res)
}

export async function updateUserRemark(userId: string, remark: string): Promise<void> {
  await http.put(`/api/admin/v1/analytics/users/${userId}/remark`, { remark })
}

export interface AdminTaskRecord {
  id: string
  taskName: string
  status: string
  statusRaw: string
  action: string
  platform: string
  keywords: string[]
  userId: string
  intervalMinutes: number
  fetchCount: number
  successCount: number
  failedCount: number
  errorMessage: string
  taskStartTime: string
  taskEndTime: string
  nextRunAt: string
  createdAt: string
  updatedAt: string
}

export interface AdminTaskStats {
  total: number
  running: number
  stopped: number
  completed: number
}

export interface AdminTasksData {
  total: number
  page: number
  limit: number
  records: AdminTaskRecord[]
  stats: AdminTaskStats
}

export interface AdminTasksParams {
  page?: number
  limit?: number
  keyword?: string
  status?: string
  created_start?: string
  created_end?: string
}

export async function fetchAdminTasks(params: AdminTasksParams = {}): Promise<AdminTasksData> {
  const res = await http.get<{ code: number; msg: string; data: AdminTasksData }>(
    '/api/admin/v1/analytics/tasks',
    { params },
  )
  return unwrap(res)
}
