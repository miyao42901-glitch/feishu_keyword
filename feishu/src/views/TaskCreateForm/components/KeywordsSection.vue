<script setup lang="ts">
/**
 * 折叠块「关键词管理」：内联标签 + 尾部单行输入（与设计稿一致），回车添加，点 × 删除。
 */
import {
  KEYWORD_COUNT_EXCEEDED_HINT,
  KEYWORD_DUPLICATE_HINT,
  KEYWORD_MAX_COUNT,
  KEYWORD_MAX_LEN,
  KEYWORD_TOO_LONG_HINT,
  truncateKeyword,
} from '@/lib/keyword-limits'
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'
import InlineTagChipsInput from './InlineTagChipsInput.vue'

defineOptions({ name: 'KeywordsSection' })

const props = defineProps<{ form: TaskCreateFormModel; keywordDraft: string }>()
const emit = defineEmits<{ 'update:keywordDraft': [value: string] }>()

function onAddKeyword(word: string) {
  if (props.form.keywords.length >= KEYWORD_MAX_COUNT) return
  const { value } = truncateKeyword(word)
  if (!value || props.form.keywords.includes(value)) return
  props.form.keywords.push(value)
}

function onRemoveKeyword(i: number) {
  props.form.keywords.splice(i, 1)
}
</script>

<template>
  <div>
    <InlineTagChipsInput
      class="w-full"
      :tags="form.keywords"
      :draft="keywordDraft"
      :tag-max-length="KEYWORD_MAX_LEN"
      :max-tags="KEYWORD_MAX_COUNT"
      :length-exceeded-hint="KEYWORD_TOO_LONG_HINT"
      :count-exceeded-hint="KEYWORD_COUNT_EXCEEDED_HINT"
      :duplicate-hint="KEYWORD_DUPLICATE_HINT"
      placeholder="输入后按回车添加关键词"
      @update:draft="emit('update:keywordDraft', $event)"
      @add="onAddKeyword"
      @close="onRemoveKeyword"
    />
  </div>
</template>
