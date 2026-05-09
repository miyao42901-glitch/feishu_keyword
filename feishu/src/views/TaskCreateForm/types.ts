/**
 * 新建任务表单：提交给后端 `config_json` 的 TypeScript 模型（与表单字段 camelCase 对齐）。
 */
import type { PlatformKey } from '@/components/PlatformIcon.vue'

/** 信源单行可勾选的采集指标（与勾选组 value 一致） */
export type SourceFieldKey = 'like' | 'comment' | 'share'

/** 定时 / 实时（影响采集频率显隐） */
export type TaskType = 'scheduled' | 'realtime'

/** 列表排序口径 */
export type SortOrder = 'latest' | 'hottest' | 'default'

/** 内容发布时间筛选 */
export type PublishTime = 'unlimited' | '1d' | '1w' | '6m'

/** 视频时长分段 */
export type VideoDuration = 'all' | 'lt1m' | '1to5m' | 'gt5m'

/** 多维表格：新建或关联已有 */
export type TableMode = 'new' | 'existing'

/** 整条任务配置快照（序列化后进库） */
export interface TaskCreateFormModel {
  /** 方案展示名，同步到服务端 `plan_name` */
  planName: string
  taskType: TaskType
  /** 分钟间隔字符串：`1`|`5`|`10`|`30`|`60` */
  crawlFrequency: string
  effectiveAt: string
  expireAt: string
  /** API 调用认证，必填 */
  authCode: string
  keywords: string[]
  /** 排除词：与 `keywords` 同为字符串数组入库 */
  excludeKeywords: string[]
  heatLikeMin: number
  heatCommentMin: number
  heatFavoriteMin: number
  heatShareMin: number
  sortOrder: SortOrder
  publishTime: PublishTime
  videoDuration: VideoDuration
  /** 列表条数上限 */
  dataRange: number
  selectedSources: PlatformKey[]
  /** 各平台已选采集字段 */
  sourceFieldSelection: Record<PlatformKey, SourceFieldKey[]>
  tableMode: TableMode
  /** 已有表标识，接口联调后填充选项 */
  existingTableId: string
}
