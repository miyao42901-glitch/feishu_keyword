export type KpiRange = 'day' | 'week' | 'month'

export interface OpsUser {
  id: string
  name: string
  feishuId: string
  phone: string
  device: string
  version: string
  tasks: number
  points: number
  lastActive: string
  remark: string
  firstUse: string
  activeHours: string
}

export interface OpsTask {
  id: string
  taskType: string
  user: string
  keywords: string[]
  platforms: string[]
  status: string
  notify: string
  created: string
  lastExec: string
  points: number
}

export interface ExecRecord {
  id: string
  taskId: string
  taskType: string
  execCount: number | string
  start: string
  end: string
  duration: string
  result: string
  points: number
  count: number
  failReason: string
}

export interface ApiRecord {
  id: string
  taskId: string
  platform: string
  time: string
  result: string
  code: string
  latency: string
}

export interface PushRecord {
  id: string
  taskId: string
  webhook: string
  sendTime: string
  sendResult: string
  callbackResult: string
  newData: number
  retry: number
}

export interface PointRecord {
  id: string
  userId: string
  userName: string
  taskId: string
  platform: string
  amount: number
  balance: number
  time: string
}

export const KPI_DATA: Record<
  KpiRange,
  {
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
> = {
  day: {
    activeTasks: 42,
    execRate: '97.2%',
    apiRate: '99.5%',
    points: 486,
    retention: '-',
    avgTasks: '-',
    pushRate: '94.1%',
    activeUsers: 52,
    compare: '较昨日',
    newUsers: '今日新增: 3',
  },
  week: {
    activeTasks: 287,
    execRate: '96.5%',
    apiRate: '99.2%',
    points: '3,420',
    retention: '-',
    avgTasks: '-',
    pushRate: '93.8%',
    activeUsers: 89,
    compare: '较上周',
    newUsers: '本周新增: 12',
  },
  month: {
    activeTasks: 623,
    execRate: '96.8%',
    apiRate: '99.1%',
    points: '14,528',
    retention: '67.2%',
    avgTasks: '4.2',
    pushRate: '93.6%',
    activeUsers: 148,
    compare: '较上月',
    newUsers: '本月新增: 23',
  },
}

export const USERS: OpsUser[] = [
  { id: 'U001', name: '张明', feishuId: 'fid_zhangming', phone: '138****1234', device: '桌面', version: 'v2.3.1', tasks: 8, points: 2340, lastActive: '2025-05-28 14:32', remark: 'VIP客户', firstUse: '2025-01-15', activeHours: '09:00-18:00' },
  { id: 'U002', name: '李婷', feishuId: 'fid_liting', phone: '139****5678', device: '手机', version: 'v2.3.0', tasks: 5, points: 1820, lastActive: '2025-05-28 13:15', remark: '媒体行业', firstUse: '2025-02-03', activeHours: '10:00-20:00' },
  { id: 'U003', name: '王磊', feishuId: 'fid_wanglei', phone: '137****9012', device: 'Web', version: 'v2.2.8', tasks: 3, points: 960, lastActive: '2025-05-27 17:45', remark: '', firstUse: '2025-03-12', activeHours: '14:00-22:00' },
  { id: 'U004', name: '赵雪', feishuId: 'fid_zhaoxue', phone: '136****3456', device: '桌面', version: 'v2.3.1', tasks: 12, points: 4100, lastActive: '2025-05-28 15:01', remark: '高频用户', firstUse: '2024-11-20', activeHours: '08:00-22:00' },
  { id: 'U005', name: '陈浩', feishuId: 'fid_chenhao', phone: '135****7890', device: '手机', version: 'v2.3.0', tasks: 2, points: 420, lastActive: '2025-05-25 09:30', remark: '新用户-待跟进', firstUse: '2025-05-10', activeHours: '09:00-12:00' },
  { id: 'U006', name: '刘芳', feishuId: 'fid_liufang', phone: '133****2345', device: '桌面', version: 'v2.2.9', tasks: 6, points: 1560, lastActive: '2025-05-28 11:20', remark: '公关公司', firstUse: '2025-01-28', activeHours: '09:00-19:00' },
  { id: 'U007', name: '孙伟', feishuId: 'fid_sunwei', phone: '132****6789', device: 'Web', version: 'v2.3.1', tasks: 4, points: 880, lastActive: '2025-05-26 16:40', remark: '', firstUse: '2025-04-05', activeHours: '13:00-18:00' },
  { id: 'U008', name: '周静', feishuId: 'fid_zhoujing', phone: '131****0123', device: '手机', version: 'v2.2.8', tasks: 1, points: 120, lastActive: '2025-05-20 08:15', remark: '流失风险', firstUse: '2025-04-22', activeHours: '08:00-09:00' },
  { id: 'U009', name: '吴强', feishuId: 'fid_wuqiang', phone: '130****4567', device: '桌面', version: 'v2.3.1', tasks: 7, points: 1980, lastActive: '2025-05-28 16:05', remark: '政府客户', firstUse: '2024-12-10', activeHours: '09:00-17:00' },
  { id: 'U010', name: '郑丽', feishuId: 'fid_zhengli', phone: '158****8901', device: '手机', version: 'v2.3.0', tasks: 3, points: 640, lastActive: '2025-05-27 10:50', remark: '', firstUse: '2025-03-28', activeHours: '10:00-15:00' },
]

export const TASKS: OpsTask[] = [
  { id: 'T-20250528-001', taskType: '定时任务', user: '张明', keywords: ['品牌舆情', '竞品动态'], platforms: ['微博', '抖音', '百度'], status: '运行中', notify: '开', created: '2025-05-10', lastExec: '2025-05-28 14:30', points: 580 },
  { id: 'T-20250528-002', taskType: '定时任务', user: '李婷', keywords: ['娱乐热搜', '明星八卦'], platforms: ['微博', '小红书'], status: '运行中', notify: '关', created: '2025-05-15', lastExec: '2025-05-28 13:10', points: 420 },
  { id: 'T-20250528-003', taskType: '定时任务', user: '赵雪', keywords: ['政策法规', '行业报告', '市场分析'], platforms: ['百度', '知乎', '微信公众号'], status: '运行中', notify: '开', created: '2025-01-20', lastExec: '2025-05-28 15:00', points: 1200 },
  { id: 'T-20250528-004', taskType: '单次任务', user: '王磊', keywords: ['技术趋势', 'AI动态'], platforms: ['GitHub', '知乎', 'CSDN'], status: '已完成', notify: '开', created: '2025-03-12', lastExec: '2025-05-20 18:00', points: 340 },
  { id: 'T-20250528-005', taskType: '单次任务', user: '陈浩', keywords: ['招聘信息'], platforms: ['拉勾', 'BOSS直聘'], status: '已停止', notify: '开', created: '2025-05-10', lastExec: '2025-05-24 10:00', points: 80 },
  { id: 'T-20250528-006', taskType: '定时任务', user: '刘芳', keywords: ['客户反馈', '产品评价'], platforms: ['微博', '小红书', '抖音'], status: '运行中', notify: '关', created: '2025-02-01', lastExec: '2025-05-28 11:15', points: 760 },
  { id: 'T-20250528-007', taskType: '定时任务', user: '吴强', keywords: ['政策解读', '通知公告'], platforms: ['政府网', '新华网', '人民网'], status: '运行中', notify: '开', created: '2024-12-15', lastExec: '2025-05-28 16:00', points: 920 },
  { id: 'T-20250528-008', taskType: '定时任务', user: '赵雪', keywords: ['竞品价格', '促销活动'], platforms: ['京东', '淘宝', '拼多多'], status: '运行中', notify: '关', created: '2025-02-20', lastExec: '2025-05-28 14:55', points: 880 },
  { id: 'T-20250528-009', taskType: '定时任务', user: '张明', keywords: ['行业会议', '峰会动态'], platforms: ['微博', '微信公众号', '活动行'], status: '运行中', notify: '开', created: '2025-04-05', lastExec: '2025-05-28 09:00', points: 560 },
  { id: 'T-20250528-010', taskType: '单次任务', user: '孙伟', keywords: ['股市行情', '财经新闻'], platforms: ['东方财富', '新浪财经', '雪球'], status: '已完成', notify: '开', created: '2025-04-10', lastExec: '2025-05-18 15:30', points: 280 },
]

export const EXEC_RECORDS: ExecRecord[] = [
  { id: 'E-10001', taskId: 'T-20250528-001', taskType: '定时任务', execCount: 156, start: '2025-05-28 14:30:00', end: '2025-05-28 14:30:45', duration: '45s', result: '成功', points: 12, count: 23, failReason: '-' },
  { id: 'E-10002', taskId: 'T-20250528-002', taskType: '定时任务', execCount: 89, start: '2025-05-28 13:10:00', end: '2025-05-28 13:10:38', duration: '38s', result: '成功', points: 8, count: 15, failReason: '-' },
  { id: 'E-10003', taskId: 'T-20250528-003', taskType: '定时任务', execCount: 234, start: '2025-05-28 15:00:00', end: '2025-05-28 15:01:52', duration: '112s', result: '成功', points: 35, count: 67, failReason: '-' },
  { id: 'E-10004', taskId: 'T-20250528-006', taskType: '定时任务', execCount: 128, start: '2025-05-28 11:15:00', end: '2025-05-28 11:15:22', duration: '22s', result: '成功', points: 10, count: 18, failReason: '-' },
  { id: 'E-10005', taskId: 'T-20250528-007', taskType: '定时任务', execCount: 312, start: '2025-05-28 16:00:00', end: '2025-05-28 16:01:10', duration: '70s', result: '成功', points: 28, count: 42, failReason: '-' },
  { id: 'E-10006', taskId: 'T-20250528-008', taskType: '定时任务', execCount: 156, start: '2025-05-28 14:55:00', end: '2025-05-28 14:55:58', duration: '58s', result: '成功', points: 22, count: 31, failReason: '-' },
  { id: 'E-10007', taskId: 'T-20250528-009', taskType: '定时任务', execCount: 98, start: '2025-05-28 09:00:00', end: '2025-05-28 09:00:33', duration: '33s', result: '成功', points: 15, count: 20, failReason: '-' },
  { id: 'E-10008', taskId: 'T-20250528-001', taskType: '定时任务', execCount: 155, start: '2025-05-28 08:00:00', end: '2025-05-28 08:00:41', duration: '41s', result: '成功', points: 11, count: 19, failReason: '-' },
  { id: 'E-10009', taskId: 'T-20250528-005', taskType: '单次任务', execCount: '-', start: '2025-05-28 10:00:00', end: '2025-05-28 10:00:05', duration: '5s', result: '失败', points: 0, count: 0, failReason: '任务已停止' },
  { id: 'E-10010', taskId: 'T-20250528-003', taskType: '定时任务', execCount: 233, start: '2025-05-28 07:00:00', end: '2025-05-28 07:01:48', duration: '108s', result: '成功', points: 33, count: 58, failReason: '-' },
]

export const API_RECORDS: ApiRecord[] = [
  { id: 'A-50001', taskId: 'T-20250528-001', platform: '微博', time: '2025-05-28 14:30:12', result: '成功', code: '-', latency: '1.2s' },
  { id: 'A-50002', taskId: 'T-20250528-001', platform: '抖音', time: '2025-05-28 14:30:18', result: '成功', code: '-', latency: '2.1s' },
  { id: 'A-50003', taskId: 'T-20250528-001', platform: '百度', time: '2025-05-28 14:30:25', result: '成功', code: '-', latency: '0.8s' },
  { id: 'A-50004', taskId: 'T-20250528-003', platform: '百度', time: '2025-05-28 15:00:15', result: '成功', code: '-', latency: '0.9s' },
  { id: 'A-50005', taskId: 'T-20250528-003', platform: '知乎', time: '2025-05-28 15:00:32', result: '成功', code: '-', latency: '1.5s' },
  { id: 'A-50006', taskId: 'T-20250528-003', platform: '微信公众号', time: '2025-05-28 15:00:58', result: '失败', code: 'E40301', latency: '3.2s' },
  { id: 'A-50007', taskId: 'T-20250528-006', platform: '微博', time: '2025-05-28 11:15:08', result: '成功', code: '-', latency: '1.1s' },
  { id: 'A-50008', taskId: 'T-20250528-006', platform: '小红书', time: '2025-05-28 11:15:15', result: '成功', code: '-', latency: '1.8s' },
  { id: 'A-50009', taskId: 'T-20250528-007', platform: '政府网', time: '2025-05-28 16:00:10', result: '成功', code: '-', latency: '2.5s' },
  { id: 'A-50010', taskId: 'T-20250528-007', platform: '新华网', time: '2025-05-28 16:00:28', result: '成功', code: '-', latency: '1.9s' },
]

export const PUSH_RECORDS: PushRecord[] = [
  { id: 'P-3001', taskId: 'T-20250528-001', webhook: 'https://hooks.feishu...', sendTime: '2025-05-28 14:31:00', sendResult: '成功', callbackResult: '成功', newData: 5, retry: 0 },
  { id: 'P-3002', taskId: 'T-20250528-003', webhook: 'https://hooks.feishu...', sendTime: '2025-05-28 15:02:00', sendResult: '成功', callbackResult: '成功', newData: 12, retry: 0 },
  { id: 'P-3003', taskId: 'T-20250528-006', webhook: 'https://hooks.feishu...', sendTime: '2025-05-28 11:16:00', sendResult: '成功', callbackResult: '失败', newData: 0, retry: 2 },
  { id: 'P-3004', taskId: 'T-20250528-007', webhook: 'https://hooks.feishu...', sendTime: '2025-05-28 16:02:00', sendResult: '成功', callbackResult: '成功', newData: 8, retry: 0 },
  { id: 'P-3005', taskId: 'T-20250528-008', webhook: 'https://hooks.feishu...', sendTime: '2025-05-28 14:56:00', sendResult: '成功', callbackResult: '成功', newData: 3, retry: 0 },
  { id: 'P-3006', taskId: 'T-20250528-009', webhook: 'https://hooks.feishu...', sendTime: '2025-05-28 09:01:00', sendResult: '失败', callbackResult: '-', newData: 0, retry: 3 },
  { id: 'P-3007', taskId: 'T-20250528-002', webhook: 'https://hooks.feishu...', sendTime: '2025-05-28 13:11:00', sendResult: '成功', callbackResult: '成功', newData: 7, retry: 0 },
  { id: 'P-3008', taskId: 'T-20250528-001', webhook: 'https://hooks.feishu...', sendTime: '2025-05-28 08:01:00', sendResult: '成功', callbackResult: '成功', newData: 2, retry: 0 },
]

export const POINT_RECORDS: PointRecord[] = [
  { id: 'C-2001', userId: 'U001', userName: '张明', taskId: 'T-20250528-001', platform: '微博', amount: 12, balance: 988, time: '2025-05-28 14:30:45' },
  { id: 'C-2002', userId: 'U001', userName: '张明', taskId: 'T-20250528-001', platform: '抖音', amount: 8, balance: 980, time: '2025-05-28 14:30:45' },
  { id: 'C-2003', userId: 'U004', userName: '赵雪', taskId: 'T-20250528-003', platform: '百度', amount: 15, balance: 4085, time: '2025-05-28 15:01:52' },
  { id: 'C-2004', userId: 'U004', userName: '赵雪', taskId: 'T-20250528-003', platform: '知乎', amount: 12, balance: 4073, time: '2025-05-28 15:01:52' },
  { id: 'C-2005', userId: 'U004', userName: '赵雪', taskId: 'T-20250528-003', platform: '微信公众号', amount: 8, balance: 4065, time: '2025-05-28 15:01:52' },
  { id: 'C-2006', userId: 'U006', userName: '刘芳', taskId: 'T-20250528-006', platform: '微博', amount: 5, balance: 1555, time: '2025-05-28 11:15:22' },
  { id: 'C-2007', userId: 'U006', userName: '刘芳', taskId: 'T-20250528-006', platform: '小红书', amount: 3, balance: 1552, time: '2025-05-28 11:15:22' },
  { id: 'C-2008', userId: 'U009', userName: '吴强', taskId: 'T-20250528-007', platform: '政府网', amount: 18, balance: 1962, time: '2025-05-28 16:01:10' },
  { id: 'C-2009', userId: 'U009', userName: '吴强', taskId: 'T-20250528-007', platform: '新华网', amount: 10, balance: 1952, time: '2025-05-28 16:01:10' },
  { id: 'C-2010', userId: 'U002', userName: '李婷', taskId: 'T-20250528-002', platform: '微博', amount: 6, balance: 1814, time: '2025-05-28 13:10:38' },
]

export const FUNNEL_STEPS = [
  { label: '首页访问', value: 1240, note: '主要来源：飞书市场', loss: '69% 未点击直接离开', color: '#4073fa' },
  { label: '登录注册页', value: 384, note: '进入登录流程', loss: '22% 放弃登录', color: '#ff7d00' },
  { label: '新建任务页', value: 298, note: '登录成功后进入', loss: '38% 未完成创建', color: '#00b42a' },
  { label: '创建成功', value: 186, note: '全链路转化完成', loss: '', color: '#00b42a' },
]

export const FUNNEL_LOSSES = [
  { title: '首页 → 登录页', count: '-856人', desc: '未点击获取 API-Key，直接离开首页' },
  { title: '登录页 → 新建任务', count: '-86人', desc: '进入登录页后放弃登录' },
  { title: '新建任务 → 创建成功', count: '-112人', desc: '进入创建页后未完成创建' },
]
