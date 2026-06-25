import type { TaskRunStatus } from '@/views/TaskCreateForm/types'

/** `public/images/task-status/` 下静态资源根路径（Vite 下以 `/` 引用） */
const TASK_STATUS_RASTER_BASE = `${import.meta.env.BASE_URL}images/task-status`

/**
 * 任务展示态角标位图（与 `TaskRunStatus` 一一对应）。
 * 原 `public/1.png`～`5.png`：待运行、运行中、已完成、已停止、失败。
 */
export const taskStatusRaster: Record<
  TaskRunStatus,
  { '1x': string; '2x': string }
> = {
  pending_run: {
    '1x': `${TASK_STATUS_RASTER_BASE}/pending-run.png`,
    '2x': `${TASK_STATUS_RASTER_BASE}/pending-run@2x.png`,
  },
  running: {
    '1x': `${TASK_STATUS_RASTER_BASE}/running.png`,
    '2x': `${TASK_STATUS_RASTER_BASE}/running@2x.png`,
  },
  completed: {
    '1x': `${TASK_STATUS_RASTER_BASE}/completed.png`,
    '2x': `${TASK_STATUS_RASTER_BASE}/completed@2x.png`,
  },
  stopped: {
    '1x': `${TASK_STATUS_RASTER_BASE}/stopped.png`,
    '2x': `${TASK_STATUS_RASTER_BASE}/stopped@2x.png`,
  },
  failed: {
    '1x': `${TASK_STATUS_RASTER_BASE}/failed.png`,
    '2x': `${TASK_STATUS_RASTER_BASE}/failed@2x.png`,
  },
}

/** `<img>` 用：默认 1x，`srcset` 指向 2x */
export function taskStatusRasterImgAttrs(status: TaskRunStatus): { src: string; srcset: string } {
  const { '1x': one, '2x': two } = taskStatusRaster[status]
  return { src: one, srcset: `${two} 2x` }
}

/** 单次采集成功弹窗角标（仅 2x 资源） */
export const collectionSuccessIconSrc = `${TASK_STATUS_RASTER_BASE}/collect-success-icon@2x.png`
