/**
 * 任务采集与 Webhook 通知的衔接（定时任务：按采集频率、采集失败）。
 */

import {
  listFailedAsyncTaskRefsFromStatusMap,
  isRealtimeTaskConfig,
  type AsyncTaskStatusResult,
} from '@/lib/async-task-api'
import type { SyncFetchContext } from '@/lib/sync-api-common'
import {
  buildAsyncRunKey,
  maybeNotifyCollectionFailed,
  maybeNotifyExecutionComplete,
  maybeNotifyScheduledRoundByFrequency,
  resetTaskWebhookCompleteDedupe,
  resetTaskWebhookRoundDedupe,
  syncGlobalNotifyWebhookFromConfig,
} from '@/lib/feishu-webhook-notify'

/** 保存/重新提交采集前：同步全局 Webhook；定时任务清除轮次/失败/已完成去重 */
export function prepareTaskWebhookForNewRun(
  taskId: number,
  config: Record<string, unknown>,
): void {
  syncGlobalNotifyWebhookFromConfig(config)
  if (!isRealtimeTaskConfig(config)) {
    resetTaskWebhookCompleteDedupe(taskId)
    resetTaskWebhookRoundDedupe(taskId)
  }
}

/** 列表轮询或写入飞书后：按采集频率推送本轮摘要，并检查异步子任务失败 */
export async function notifyWebhookAfterScheduledPoll(input: {
  taskId: number
  taskName: string
  config: Record<string, unknown>
  writtenRowCount: number
  totalRowCount: number
  sync: SyncFetchContext
  /** 与本轮 `buildTestDataFeedFromConfig` 共用，避免重复查询 status */
  asyncStatusMap?: Map<string, AsyncTaskStatusResult>
}): Promise<void> {
  if (isRealtimeTaskConfig(input.config)) return

  const failedRefs = input.asyncStatusMap
    ? listFailedAsyncTaskRefsFromStatusMap(input.config, input.asyncStatusMap)
    : []
  await maybeNotifyCollectionFailed({
    taskId: input.taskId,
    taskName: input.taskName,
    config: input.config,
    failedRefs,
  })

  await maybeNotifyScheduledRoundByFrequency({
    taskId: input.taskId,
    taskName: input.taskName,
    config: input.config,
    writtenRowCount: input.writtenRowCount,
    totalRowCount: input.totalRowCount,
  })
}

/** 本地执行采集失败（无异步子任务详情） */
export async function notifyWebhookCollectionRunFailed(input: {
  taskId: number
  taskName: string
  config: Record<string, unknown>
  message: string
}): Promise<void> {
  await maybeNotifyCollectionFailed({
    taskId: input.taskId,
    taskName: input.taskName,
    config: input.config,
    detailLines: [input.message.trim() || '采集执行失败'],
  })
}

/** 定时任务异步子任务全部完成 */
export async function notifyScheduledExecutionComplete(input: {
  taskId: number
  taskName: string
  config: Record<string, unknown>
}): Promise<void> {
  await maybeNotifyExecutionComplete({
    taskId: input.taskId,
    taskName: input.taskName,
    config: input.config,
    runKey: buildAsyncRunKey(input.config),
  })
}
