<script setup lang="ts">
/**
 * 折叠块「关键词管理」：内联标签 + 尾部单行输入（与设计稿一致），回车添加，点 × 删除。
 */
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'
import InlineTagChipsInput from './InlineTagChipsInput.vue'

defineOptions({ name: 'KeywordsSection' })

const props = defineProps<{ form: TaskCreateFormModel; keywordDraft: string }>()
const emit = defineEmits<{ 'update:keywordDraft': [value: string] }>()

function onAddKeyword(word: string) {
  props.form.keywords.push(word)
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
      placeholder="输入后按回车添加关键词"
      @update:draft="emit('update:keywordDraft', $event)"
      @add="onAddKeyword"
      @close="onRemoveKeyword"
    />
  </div>
</template>
