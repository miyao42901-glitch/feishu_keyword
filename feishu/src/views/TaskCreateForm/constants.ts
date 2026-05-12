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

/** Element Plus 日期时间展示与 v-model 字符串格式 */
export const DATETIME_FORMAT = 'YYYY-MM-DD HH:mm:ss'

/** 定时任务采集间隔（value 为分钟数字符串） */
export const frequencyOptions = [
  { label: '每1分钟', value: '1' },
  { label: '每5分钟', value: '5' },
  { label: '每10分钟', value: '10' },
  { label: '每30分钟', value: '30' },
  { label: '每1小时', value: '60' },
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

/** 单次拉取/展示条数候选 */
export const dataRangeOptions = [10, 20, 30, 50, 70, 100] as const

/** 信源勾选区固定顺序与展示文案（当前仅开放抖音、小红书） */
export const sourcePlatforms: { id: PlatformKey; label: string }[] = [
  { id: 'douyin', label: '抖音' },
  { id: 'xiaohongshu', label: '小红书' },
]
