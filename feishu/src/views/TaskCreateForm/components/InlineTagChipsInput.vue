<script setup lang="ts">
/**
 * 内联标签 + 单行输入：标签与光标同一行排列，回车添加，点 × 删除；点击空白处聚焦输入。
 */
import { ref } from 'vue'

defineOptions({ name: 'InlineTagChipsInput' })

const props = withDefaults(
  defineProps<{
    tags: string[]
    draft: string
    placeholder: string
    /** 单行草稿最大长度 */
    inputMaxlength?: number
  }>(),
  { inputMaxlength: 256 },
)

const emit = defineEmits<{
  'update:draft': [value: string]
  add: [word: string]
  close: [index: number]
}>()

const inputRef = ref<HTMLInputElement | null>(null)

function onFieldClick(e: MouseEvent) {
  const el = e.target as HTMLElement
  if (el.closest('.el-tag__close')) return
  inputRef.value?.focus()
}

function commitDraft() {
  const segment = props.draft.trim()
  if (!segment) return
  if (props.tags.includes(segment)) return
  emit('add', segment)
  emit('update:draft', '')
}

function onInputKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault()
    commitDraft()
    return
  }
  if (e.key === 'Backspace' && !props.draft && props.tags.length > 0) {
    e.preventDefault()
    emit('close', props.tags.length - 1)
  }
}

function onTagClose(i: number) {
  emit('close', i)
}

function onDraftInput(e: Event) {
  const t = e.target as HTMLInputElement
  emit('update:draft', t.value)
}
</script>

<template>
  <div
    class="inline-tag-field"
    role="group"
    :aria-label="placeholder"
    @click="onFieldClick"
  >
    <el-tag
      v-for="(kw, i) in tags"
      :key="kw + '-' + i"
      class="inline-tag-field__chip"
      closable
      @close="onTagClose(i)"
    >
      {{ kw }}
    </el-tag>
    <input
      ref="inputRef"
      type="text"
      class="inline-tag-field__input"
      :value="draft"
      :maxlength="inputMaxlength"
      :placeholder="placeholder"
      autocomplete="off"
      @click.stop
      @input="onDraftInput"
      @keydown="onInputKeydown"
    />
  </div>
</template>

<style scoped>
.inline-tag-field {
  box-sizing: border-box;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 6px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #ffffff;
  cursor: text;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.inline-tag-field:focus-within {
  border-color: #1f22f6;
  box-shadow: 0 0 0 1px #1f22f6;
}

.inline-tag-field__input {
  box-sizing: border-box;
  flex: 1 1 160px;
  min-width: 10em;
  max-width: 100%;
  border: none;
  margin: 0;
  padding: 4px 2px;
  background: transparent;
  color: #0f1114;
  font-size: 14px;
  line-height: 22px;
  outline: none;
}

.inline-tag-field__input::placeholder {
  color: var(--el-text-color-placeholder);
}

.inline-tag-field :deep(.inline-tag-field__chip.el-tag) {
  height: auto;
  padding: 4px 10px;
  margin: 0;
  border: none;
  border-radius: 4px;
  background-color: #e8edff;
  color: #1f22f6;
  font-weight: 500;
  font-size: 14px;
  line-height: 1.35;
}

.inline-tag-field :deep(.inline-tag-field__chip .el-tag__close) {
  color: #4e5969;
}

.inline-tag-field :deep(.inline-tag-field__chip .el-tag__close:hover) {
  color: #1f22f6;
  background-color: rgb(31 34 246 / 0.1);
}
</style>
