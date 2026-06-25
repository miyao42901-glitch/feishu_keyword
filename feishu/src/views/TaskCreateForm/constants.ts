/**
 * 新建任务表单：与 UI 绑定的静态选项（标签 + 提交值）。
 */
import type { PlatformKey } from '@/components/PlatformIcon.vue'

/** 列表/回显用：含历史任务中可能出现的全部平台 id */
export const platformDisplayNames: Record<PlatformKey, string> = {
  douyin: '抖音',
  xiaohongshu: '小红书',
  weibo: '微博',
  gzh: '公众号',
  shipinhao: '视频号',
  kuaishou: '快手',
}

/** 任务名称（planName / task_name）最大字符数 */
export const TASK_NAME_MAX_LEN = 30

/** Element Plus 日期时间展示与 v-model 字符串格式 */
export const DATETIME_FORMAT = 'YYYY-MM-DD HH:mm:ss'

/** 定时任务采集间隔默认值（分钟） */
export const DEFAULT_CRAWL_FREQUENCY = '60'

/** 定时任务采集间隔（value 为分钟数字符串） */
export const frequencyOptions = [
  { label: '每5分钟', value: '5' },
  { label: '每15分钟', value: '15' },
  { label: '每1小时', value: '60' },
  { label: '每6小时', value: '360' },
  { label: '每24小时', value: '1440' },
] as const

/** 排序方式下拉 */
export const sortOrderOptions = [
  { label: '最新', value: 'latest' },
  { label: '最热', value: 'hottest' },
  { label: '默认', value: 'default' },
] as const

/** 发布时间筛选 */
export const publishTimeOptions = [
  { label: '不限', value: 'unlimited' },
  { label: '一天之内', value: '1d' },
  { label: '一周之内', value: '1w' },
  { label: '半年之内', value: '6m' },
] as const

/** 视频时长分段 */
export const videoDurationOptions = [
  { label: '所有', value: 'all' },
  { label: '1分钟以下', value: 'lt1m' },
  { label: '1-5分钟', value: '1to5m' },
  { label: '5分钟以上', value: 'gt5m' },
] as const

/** 作品数据范围：各平台 search-page 请求页数 */
export const dataRangeOptions = [1, 2, 5, 10, 20, 50] as const

/** 作品数据范围默认页数 */
export const DEFAULT_DATA_PAGE_COUNT = 1

/** 信源勾选区固定顺序与展示文案（已接入 search-page 的平台） */
export const sourcePlatforms: { id: PlatformKey; label: string }[] = [
  { id: 'douyin', label: '抖音' },
  { id: 'xiaohongshu', label: '小红书' },
  { id: 'shipinhao', label: '视频号' },
  { id: 'gzh', label: '公众号' },
]
