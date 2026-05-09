/**
 * 新建任务表单：与 UI 绑定的静态选项（标签 + 提交值）。
 */
import type { PlatformKey } from '@/components/PlatformIcon.vue'

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

/** 信源勾选区固定顺序与展示文案 */
export const sourcePlatforms: { id: PlatformKey; label: string }[] = [
  { id: 'xiaohongshu', label: '小红书' },
  { id: 'weibo', label: '微博' },
  { id: 'douyin', label: '抖音' },
  { id: 'gzh', label: '公众号' },
  { id: 'shipinhao', label: '视频号' },
  { id: 'kuaishou', label: '快手' },
]
