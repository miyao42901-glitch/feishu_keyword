<script setup lang="ts">
/**
 * 折叠块「信源选择」：平台多选 + 各平台采集字段多选。
 */
import PlatformIcon from '@/components/PlatformIcon.vue'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'
import { sourcePlatforms } from '@/views/TaskCreateForm/constants'

defineOptions({ name: 'SourceSelectionSection' })

defineProps<{
  form: TaskCreateFormModel
  /** 父组件按 `sourcePlatforms` 顺序过滤后的已选平台，用于下方卡片顺序 */
  orderedPlatforms: { id: PlatformKey; label: string }[]
}>()
</script>

<template>
  <div>
    <el-checkbox-group v-model="form.selectedSources" class="source-platform-group">
      <div class="flex flex-wrap gap-3">
        <el-checkbox v-for="p in sourcePlatforms" :key="p.id" :value="p.id" border class="source-platform-checkbox">
          <div class="flex items-center gap-2.5 py-0.5 pr-1">
            <PlatformIcon :platform="p.id" />
            <span class="text-sm font-medium text-slate-800">{{ p.label }}</span>
          </div>
        </el-checkbox>
      </div>
    </el-checkbox-group>

    <div v-if="orderedPlatforms.length" class="mt-5 space-y-4">
      <div
        v-for="p in orderedPlatforms"
        :key="p.id"
        class="rounded-lg border border-slate-200 bg-slate-50/90 px-4 py-3"
      >
        <p class="mb-2 text-sm font-medium text-slate-800">{{ p.label }} - 选择采集字段</p>
        <p class="mb-2 text-xs text-slate-500">固定字段（后续可扩展更多指标）</p>
        <el-checkbox-group v-model="form.sourceFieldSelection[p.id]" class="flex flex-wrap gap-x-6 gap-y-2">
          <el-checkbox value="like">点赞数</el-checkbox>
          <el-checkbox value="comment">评论数</el-checkbox>
          <el-checkbox value="share">转发数</el-checkbox>
        </el-checkbox-group>
      </div>
    </div>
  </div>
</template>

<style scoped>
.source-platform-group :deep(.source-platform-checkbox) {
  margin-right: 0;
  margin-left: 0;
  height: auto;
  align-items: center;
  padding: 0.5rem 0.75rem;
}
</style>
