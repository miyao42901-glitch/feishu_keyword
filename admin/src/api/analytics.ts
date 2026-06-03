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
