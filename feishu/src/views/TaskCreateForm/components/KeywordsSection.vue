<script setup lang="ts">
/**
 * 折叠块「关键词管理」：标签列表 + 多行输入；回车提交首行为关键词，Shift+Enter 换行。
 */
import { computed } from 'vue'
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'

defineOptions({ name: 'KeywordsSection' })

const props = defineProps<{ form: TaskCreateFormModel; keywordDraft: string }>()
const emit = defineEmits<{ 'update:keywordDraft': [value: string] }>()

/** 无标签且无草稿时整体压低；有任一内容后随 autosize 增高 */
const keywordEditorCompact = computed(
  () => props.form.keywords.length === 0 && !props.keywordDraft.trim(),
)

const keywordDraftAutosize = computed(() =>
  keywordEditorCompact.value ? { minRows: 1, maxRows: 12 } : { minRows: 2, maxRows: 12 },
)

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
      class="keyword-editor w-full px-2 py-2 transition-shadow focus-within:ring-1 focus-within:ring-[#1F22F6]/20"
    >
      <div
        class="flex flex-wrap gap-2"
        :class="form.keywords.length ? 'min-h-0 pb-1' : 'min-h-0 pb-0'"
      >
        <el-tag
          v-for="(kw, i) in form.keywords"
          :key="kw + '-' + i"
          class="keyword-chip"
          closable
          @close="removeKeyword(i)"
        >
          {{ kw }}
        </el-tag>
      </div>
      <p class="keyword-editor-hint">输入关键词后按回车添加，点击 × 删除标签</p>
      <el-input
        :model-value="keywordDraft"
        class="keyword-editor-textarea !w-full"
        type="textarea"
        :autosize="keywordDraftAutosize"
        resize="none"
        @update:model-value="emit('update:keywordDraft', $event)"
        @keydown.enter="onKeywordTextareaEnter"
      />
    </div>
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
