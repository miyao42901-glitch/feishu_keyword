<script setup lang="ts">
/**
 * 折叠块「过滤设置」：排除词（交互同关键词管理）、热度阈值、排序/时间/时长/条数。
 */
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'
import {
  dataRangeOptions,
  publishTimeOptions,
  sortOrderOptions,
  videoDurationOptions,
} from '@/views/TaskCreateForm/constants'

defineOptions({ name: 'FilterSettingsSection' })

const props = defineProps<{ form: TaskCreateFormModel; excludeKeywordDraft: string }>()
const emit = defineEmits<{ 'update:excludeKeywordDraft': [value: string] }>()

function removeExcludeKeyword(i: number) {
  props.form.excludeKeywords.splice(i, 1)
}

function onExcludeTextareaEnter(evt: KeyboardEvent | Event) {
  if (!(evt instanceof KeyboardEvent)) return
  if (evt.shiftKey) return
  evt.preventDefault()
  const raw = props.excludeKeywordDraft
  const nl = raw.indexOf('\n')
  const segment = (nl >= 0 ? raw.slice(0, nl) : raw).trim()
  emit('update:excludeKeywordDraft', nl >= 0 ? raw.slice(nl + 1) : '')
  if (!segment || props.form.excludeKeywords.includes(segment)) return
  props.form.excludeKeywords.push(segment)
}

/** 热度阈值：与设计稿一致，四项标签 + 单位 */
const heatThresholdRows = [
  { field: 'heatLikeMin' as const, label: '点赞>', unit: '赞' },
  { field: 'heatCommentMin' as const, label: '评论>', unit: '条' },
  { field: 'heatFavoriteMin' as const, label: '收藏>', unit: '条' },
  { field: 'heatShareMin' as const, label: '转发>', unit: '条' },
]
</script>

<template>
  <div>
    <!-- 与「关键词管理」折叠块内编辑器同宽：不用 el-form-item，避免内容区被收窄 -->
    <div class="mb-6">
      <p class="mb-3 text-sm font-medium text-slate-800">排除词</p>
      <div
        class="keyword-editor w-full rounded-md border border-slate-200 bg-white px-2 py-2 transition-shadow focus-within:border-indigo-400 focus-within:ring-1 focus-within:ring-indigo-400/30"
      >
        <div class="flex min-h-8 flex-wrap gap-2 pb-1">
          <el-tag
            v-for="(kw, i) in form.excludeKeywords"
            :key="kw + '-' + i"
            closable
            type="info"
            @close="removeExcludeKeyword(i)"
          >
            {{ kw }}
          </el-tag>
        </div>
        <el-input
          :model-value="excludeKeywordDraft"
          class="keyword-editor-textarea !w-full"
          type="textarea"
          :autosize="{ minRows: 3, maxRows: 12 }"
          resize="none"
          @update:model-value="emit('update:excludeKeywordDraft', $event)"
          @keydown.enter="onExcludeTextareaEnter"
        />
      </div>
      <p class="mt-2 text-xs text-slate-500">输入排除词后按回车添加，点击 × 删除标签</p>
    </div>

    <div class="mb-4">
      <p class="mb-3 text-sm font-medium text-slate-800">热度阈值</p>
      <div class="filter-heat-grid">
        <div
          v-for="row in heatThresholdRows"
          :key="row.field"
          class="heat-threshold-cell flex min-w-0 items-center gap-1.5 rounded-lg border border-slate-200/90 bg-slate-100 px-2 py-2 sm:gap-2 sm:px-2.5"
        >
          <span class="shrink-0 text-xs text-slate-700">{{ row.label }}</span>
          <el-input-number
            v-model="form[row.field]"
            size="small"
            :min="0"
            :step="1"
            controls-position="right"
            class="heat-threshold-input min-w-0 flex-1"
          />
          <span class="shrink-0 text-xs text-slate-600">{{ row.unit }}</span>
        </div>
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

/* 卡片内数字框：小号、白底，两位数仍可辨认 */
.heat-threshold-input :deep(.el-input__wrapper) {
  background-color: #fff;
  box-shadow: 0 0 0 1px rgb(226 232 240) inset;
  padding-left: 6px;
  padding-right: 4px;
}

.heat-threshold-input :deep(.el-input__wrapper:hover),
.heat-threshold-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px rgb(203 213 225) inset;
}

.heat-threshold-input :deep(.el-input__inner) {
  font-size: 12px;
  line-height: 1.25;
  text-align: center;
  min-width: 2ch;
}

/* 缩小右侧步进按钮，把横向空间让给数字区 */
.heat-threshold-input :deep(.el-input-number__decrease),
.heat-threshold-input :deep(.el-input-number__increase) {
  width: 18px;
}

.keyword-editor-textarea :deep(.el-textarea__inner) {
  border: none;
  box-shadow: none;
  padding-left: 0.25rem;
  padding-right: 0.25rem;
}

.keyword-editor-textarea :deep(.el-textarea__inner:hover),
.keyword-editor-textarea :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}
</style>
