/**
 * 新建任务表单：提交给后端 `config_json` 的 TypeScript 模型（与表单字段 camelCase 对齐）。
 */
import type { PlatformKey } from '@/components/PlatformIcon.vue'

/** 信源单行可勾选的采集指标（与勾选组 value 一致） */
export type SourceFieldKey = 'like' | 'comment' | 'share'

/** 定时任务需填写生效/过期时间；实时任务不展示时间选择 */
export type TaskType = 'scheduled' | 'realtime'

/** 列表排序口径 */
export type SortOrder = 'latest' | 'hottest' | 'default'

/** 内容发布时间筛选 */
export type PublishTime = 'unlimited' | '1d' | '1w' | '6m'

/** 视频时长分段 */
export type VideoDuration = 'all' | 'lt1m' | '1to5m' | 'gt5m'

/** 多维表格：新建或关联已有 */
export type TableMode = 'new' | 'existing'

/** 列表卡片展示用运行态（由生效/过期时间与 taskPaused、失败标记推导） */
export type TaskRunStatus = 'running' | 'completed' | 'stopped' | 'failed'

/** 已停止子类：未到生效时间 vs 窗口内暂停 */
export type TaskStoppedKind = 'before_effective' | 'paused_in_window' | 'neutral'

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
  /**
   * 配置中的 `runStatus`：表单保存用；失败任务为 `failed`，其它情况多为 `stopped`。
   * 列表卡片主色状态由时间推导，不完全依赖本字段。
   */
  runStatus: TaskRunStatus
  /** 生效窗口内用户点击「停止」后为 true，对应列表 `task_paused` */
  taskPaused: boolean
  /** 任务异常（如采集/飞书等接口失败）后为 true，列表与 `runStatus: failed` 同为失败态 */
  taskAbnormal: boolean
}
