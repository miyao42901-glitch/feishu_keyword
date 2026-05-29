/** `public/images/task-list/` 下任务列表卡片静态资源 */
const TASK_LIST_RASTER_BASE = `${import.meta.env.BASE_URL}images/task-list`

/** 任务卡片元信息行「平台」图标（原 `public/Frame.png`） */
export const taskListPlatformIcon = {
  '1x': `${TASK_LIST_RASTER_BASE}/platform.png`,
  '2x': `${TASK_LIST_RASTER_BASE}/platform@2x.png`,
} as const

/** `<img>` 用：默认 1x，`srcset` 指向 2x */
export function taskListPlatformIconImgAttrs(): { src: string; srcset: string } {
  const { '1x': one, '2x': two } = taskListPlatformIcon
  return { src: one, srcset: `${two} 2x` }
}
