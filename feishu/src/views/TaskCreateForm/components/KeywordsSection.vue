<script setup lang="ts">
/**
 * 折叠块「关键词管理」：标签列表 + 多行输入；回车提交首行为关键词，Shift+Enter 换行。
 */
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'

defineOptions({ name: 'KeywordsSection' })

const props = defineProps<{ form: TaskCreateFormModel; keywordDraft: string }>()
const emit = defineEmits<{ 'update:keywordDraft': [value: string] }>()

/** 关闭标签时按索引移除 */
function removeKeyword(i: number) {
  props.form.keywords.splice(i, 1)
}

/**
 * Enter：取第一行当关键词余下留草稿；Shift+Enter 不设拦由默认行为换行。
 * 忽略空串与重复词。
 */
function onKeywordTextareaEnter(evt: KeyboardEvent | Event) {
  if (!(evt instanceof KeyboardEvent)) return
  if (evt.shiftKey) return
  evt.preventDefault()
  const raw = props.keywordDraft
  const nl = raw.indexOf('\n')
  const segment = (nl >= 0 ? raw.slice(0, nl) : raw).trim()
  emit('update:keywordDraft', nl >= 0 ? raw.slice(nl + 1) : '')
  if (!segment || props.form.keywords.includes(segment)) return
  props.form.keywords.push(segment)
}
</script>

<template>
  <div>
    <div
      class="keyword-editor w-full rounded-md border border-slate-200 bg-white px-2 py-2 transition-shadow focus-within:border-indigo-400 focus-within:ring-1 focus-within:ring-indigo-400/30"
    >
      <div class="flex min-h-8 flex-wrap gap-2 pb-1">
        <el-tag v-for="(kw, i) in form.keywords" :key="kw + '-' + i" closable type="info" @close="removeKeyword(i)">
          {{ kw }}
        </el-tag>
      </div>
      <el-input
        :model-value="keywordDraft"
        class="keyword-editor-textarea !w-full"
        type="textarea"
        :autosize="{ minRows: 3, maxRows: 12 }"
        resize="none"
        @update:model-value="emit('update:keywordDraft', $event)"
        @keydown.enter="onKeywordTextareaEnter"
      />
    </div>
    <p class="mt-2 text-xs text-slate-500">输入关键词后按回车添加，点击 × 删除标签</p>
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
