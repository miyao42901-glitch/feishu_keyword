<script setup lang="ts">
/**
 * 折叠块「过滤设置」：排除词（交互同关键词管理）、排序/时间/时长/条数。
 */
import { computed } from 'vue'
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

const excludeEditorCompact = computed(
  () => props.form.excludeKeywords.length === 0 && !props.excludeKeywordDraft.trim(),
)

const excludeDraftAutosize = computed(() =>
  excludeEditorCompact.value ? { minRows: 1, maxRows: 12 } : { minRows: 2, maxRows: 12 },
)

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
      <p class="task-form-field-title mb-3">排除词</p>
      <div
        class="keyword-editor w-full px-2 py-2 transition-shadow focus-within:ring-1 focus-within:ring-[#1F22F6]/20"
      >
        <div
          class="flex flex-wrap gap-2"
          :class="form.excludeKeywords.length ? 'min-h-0 pb-1' : 'min-h-0 pb-0'"
        >
          <el-tag
            v-for="(kw, i) in form.excludeKeywords"
            :key="kw + '-' + i"
            class="keyword-chip"
            closable
            @close="removeExcludeKeyword(i)"
          >
            {{ kw }}
          </el-tag>
        </div>
        <p class="keyword-editor-hint">输入排除词后按回车添加，点击 × 删除标签</p>
        <el-input
          :model-value="excludeKeywordDraft"
          class="keyword-editor-textarea !w-full"
          type="textarea"
          :autosize="excludeDraftAutosize"
          resize="none"
          @update:model-value="emit('update:excludeKeywordDraft', $event)"
          @keydown.enter="onExcludeTextareaEnter"
        />
      </div>
    </div>

    <el-form-item label="排序方式">
      <el-select v-model="form.sortOrder" placeholder="请选择" class="w-full">
        <el-option v-for="opt in sortOrderOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
    </el-form-item>
    <el-form-item label="发布时间">
      <el-select v-model="form.publishTime" placeholder="请选择" class="w-full">
        <el-option v-for="opt in publishTimeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
    </el-form-item>
    <el-form-item label="视频时长">
      <el-select v-model="form.videoDuration" placeholder="请选择" class="w-full">
        <el-option v-for="opt in videoDurationOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
    </el-form-item>
    <el-form-item label="选择条数">
      <el-select v-model="form.dataRange" placeholder="请选择单次拉取条数" class="w-full">
        <el-option v-for="n in dataRangeOptions" :key="n" :label="`${n}条`" :value="n" />
      </el-select>
    </el-form-item>
  </div>
</template>

<style scoped>
.keyword-editor {
  box-sizing: border-box;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.keyword-editor-hint {
  margin: 0 0 0.375rem;
  padding: 0 0.25rem;
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--el-text-color-placeholder);
}

.keyword-editor :deep(.keyword-chip.el-tag) {
  height: auto;
  padding: 4px 8px;
  margin: 0;
  border: none;
  border-radius: 2px;
  background-color: #ededfe;
  color: #0f1114;
  font-weight: 500;
  font-size: 0.875rem;
  line-height: 1.35;
}

.keyword-editor :deep(.keyword-chip .el-tag__close) {
  color: #646a73;
}

.keyword-editor :deep(.keyword-chip .el-tag__close:hover) {
  color: #0f1114;
  background-color: rgb(31 34 246 / 0.08);
}

.keyword-editor-textarea :deep(.el-textarea__inner) {
  border: none;
  box-shadow: none;
  background-color: transparent;
  padding-left: 0.25rem;
  padding-right: 0.25rem;
}

.keyword-editor-textarea :deep(.el-textarea__inner:hover),
.keyword-editor-textarea :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}
</style>
