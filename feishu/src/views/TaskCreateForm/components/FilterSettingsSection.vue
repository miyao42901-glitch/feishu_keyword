<script setup lang="ts">
/**
 * 折叠块「过滤设置」：排除词、热度阈值、排序/时间/时长/条数。
 */
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'
import {
  dataRangeOptions,
  publishTimeOptions,
  sortOrderOptions,
  videoDurationOptions,
} from '@/views/TaskCreateForm/constants'

defineOptions({ name: 'FilterSettingsSection' })

defineProps<{ form: TaskCreateFormModel }>()
</script>

<template>
  <div>
    <el-form-item label="排除词">
      <el-input v-model="form.excludeKeywords" type="textarea" :rows="4" />
      <p class="mt-1.5 text-xs text-slate-500">输入需要排除的关键词，多个用逗号分隔</p>
    </el-form-item>

    <div class="mb-4">
      <p class="mb-3 text-sm font-medium text-slate-800">热度阈值</p>
      <div class="filter-heat-grid">
        <el-form-item class="filter-heat-item" label="点赞">
          <div class="flex w-full items-center gap-2">
            <span class="shrink-0 text-slate-500">&gt;</span>
            <el-input-number
              v-model="form.heatLikeMin"
              :min="0"
              :step="1"
              controls-position="right"
              class="min-w-0 flex-1"
            />
          </div>
        </el-form-item>
        <el-form-item class="filter-heat-item" label="评论">
          <div class="flex w-full items-center gap-2">
            <span class="shrink-0 text-slate-500">&gt;</span>
            <el-input-number
              v-model="form.heatCommentMin"
              :min="0"
              :step="1"
              controls-position="right"
              class="min-w-0 flex-1"
            />
          </div>
        </el-form-item>
        <el-form-item class="filter-heat-item" label="收藏">
          <div class="flex w-full items-center gap-2">
            <span class="shrink-0 text-slate-500">&gt;</span>
            <el-input-number
              v-model="form.heatFavoriteMin"
              :min="0"
              :step="1"
              controls-position="right"
              class="min-w-0 flex-1"
            />
          </div>
        </el-form-item>
        <el-form-item class="filter-heat-item" label="转发">
          <div class="flex w-full items-center gap-2">
            <span class="shrink-0 text-slate-500">&gt;</span>
            <el-input-number
              v-model="form.heatShareMin"
              :min="0"
              :step="1"
              controls-position="right"
              class="min-w-0 flex-1"
            />
          </div>
        </el-form-item>
      </div>
    </div>

    <el-form-item label="排序方式">
      <el-select v-model="form.sortOrder" placeholder="请选择" class="w-full max-w-md">
        <el-option v-for="opt in sortOrderOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
    </el-form-item>
    <el-form-item label="发布时间">
      <el-select v-model="form.publishTime" placeholder="请选择" class="w-full max-w-md">
        <el-option v-for="opt in publishTimeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
    </el-form-item>
    <el-form-item label="视频时长">
      <el-select v-model="form.videoDuration" placeholder="请选择" class="w-full max-w-md">
        <el-option v-for="opt in videoDurationOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
    </el-form-item>
    <el-form-item label="数据范围">
      <el-select v-model="form.dataRange" placeholder="请选择" class="w-full max-w-md">
        <el-option v-for="n in dataRangeOptions" :key="n" :label="`${n}条`" :value="n" />
      </el-select>
    </el-form-item>
  </div>
</template>

<style scoped>
.filter-heat-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem 1rem;
}

.filter-heat-grid :deep(.filter-heat-item) {
  margin-bottom: 0;
}

.filter-heat-grid :deep(.filter-heat-item .el-form-item__content) {
  min-width: 0;
}
</style>
