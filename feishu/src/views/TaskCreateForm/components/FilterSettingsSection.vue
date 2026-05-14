<script setup lang="ts">
/**
 * 折叠块「过滤设置」：排除词（交互同关键词管理）、排序/时间/时长/条数。
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
    <el-form-item label="选择条数">
      <el-select v-model="form.dataRange" placeholder="请选择单次拉取条数" class="w-full max-w-md">
        <el-option v-for="n in dataRangeOptions" :key="n" :label="`${n}条`" :value="n" />
      </el-select>
    </el-form-item>
  </div>
</template>

<style scoped>
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
