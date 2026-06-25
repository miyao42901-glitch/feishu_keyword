/**
 * 新建任务表单：提交给后端 `config_json` 的 TypeScript 模型（与表单字段 camelCase 对齐）。
 */
import type { PlatformKey } from '@/components/PlatformIcon.vue'

/**
 * 信源采集字段勾选值（与下拉多选、`config_json.sourceFieldSelection` 一致）。
 * 含各平台基础项与互动/作者等；必选项（如视频唯一 ID、笔记 ID）由表单逻辑强制保留在数组中。
 */
export type SourceFieldKey =
  | 'videoUniqueId'
  | 'title'
  | 'videoDescription'
  | 'playPageUrl'
  | 'externalDownloadUrl'
  | 'coverUrl'
  | 'videoTypeTag'
  | 'durationSeconds'
  | 'publishedAt'
  /** 本条数据采集完成时刻（非接口字段，写入时由前端生成） */
  | 'collectedAt'
  | 'like'
  | 'comment'
  | 'share'
  | 'favorite'
  | 'authorNickname'
  | 'authorId'
  | 'authorFollowers'
  | 'authorAvatar'
  /** 抖音：作者个人简介 `author_signature` */
  | 'authorSignature'
  /** 抖音：星标认证 `verify_name` */
  | 'verifyName'
  | 'hashtagList'
  | 'city'
  | 'ipLocation'
  | 'noteId'
  | 'noteBody'
  | 'topicTags'
  | 'noteImages'
  | 'videoMedia'
  | 'location'
  | 'noteType'
  | 'mentionedUsers'
  /** 公众号专用 */
  | 'gzhArticleId'
  | 'gzhArticleTitle'
  | 'gzhArticleBody'
  | 'gzhArticleSummary'
  | 'gzhArticleUrl'
  | 'gzhArticleType'
  | 'gzhAccountId'
  | 'gzhAccountNickname'
  | 'gzhAccountAvatar'
  | 'gzhAccountBio'
  | 'gzhReadCount'
  | 'gzhLikeCount'
  | 'gzhRepostCount'
  | 'gzhCollectCount'
  | 'gzhWowCount'
  | 'gzhFeaturedCommentCount'
  /** 视频号专用 */
  | 'wxvVideoUniqueId'
  | 'wxvVideoUrl'
  | 'wxvVideoTitle'
  | 'wxvVideoDescription'
  | 'wxvAuthorNickname'
  | 'wxvAuthorAvatar'
  | 'wxvAuthorBio'
  | 'wxvAuthorId'
  | 'wxvLikeCount'
  | 'wxvCommentCount'
  | 'wxvRepostCount'
  | 'wxvHeartCount'
  | 'wxvCoverUrl'
  | 'wxvDuration'

/** 定时任务需填写开始/结束时间；单次任务不展示时间选择 */
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
export type TaskRunStatus = 'running' | 'completed' | 'stopped' | 'failed' | 'pending_run'

/** 已停止子类：未到生效时间 vs 窗口内暂停 */
export type TaskStoppedKind = 'before_effective' | 'paused_in_window' | 'neutral'

/** 整条任务配置快照（序列化后进库） */
export interface TaskCreateFormModel {
  /** 任务展示名，同步到服务端 `plan_name` */
  planName: string
  /** 定时任务完成后是否推送飞书群机器人消息（单次任务不推送） */
  feishuNotifyEnabled: boolean
  /** 飞书自定义机器人 Webhook；仅在 `feishuNotifyEnabled` 时必填 */
  feishuWebhookUrl: string
  taskType: TaskType
  /** 分钟间隔字符串：`1`|`5`|`10`|`30`|`60` */
  crawlFrequency: string
  effectiveAt: string
  expireAt: string
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
  /** 作品数据范围（search-page 请求页数：1/2/5/10/20/50） */
  dataRange: number
  selectedSources: PlatformKey[]
  /** 各平台已选采集字段 */
  sourceFieldSelection: Record<PlatformKey, SourceFieldKey[]>
  tableMode: TableMode
  /** 已有表标识（单表模式遗留；高级配置用 platformExistingTableIds） */
  existingTableId: string
  /** 自动新建：各平台目标表格名称 */
  platformNewTableNames: Record<PlatformKey, string>
  /** 使用现有：各平台关联的数据表 id */
  platformExistingTableIds: Record<PlatformKey, string>
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
