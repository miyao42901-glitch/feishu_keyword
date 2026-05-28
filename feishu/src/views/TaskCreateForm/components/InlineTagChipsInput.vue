<script setup lang="ts">
/**
 * 内联标签 + 单行输入：标签与光标同一行排列，回车添加，点 × 删除；点击空白处聚焦输入。
 */
import { computed, ref } from 'vue'

defineOptions({ name: 'InlineTagChipsInput' })

const props = withDefaults(
  defineProps<{
    tags: string[]
    draft: string
    placeholder: string
    /** 单行草稿最大长度 */
    inputMaxlength?: number
    /** 提交为标签时的最大长度；超出则截断并显示 `lengthExceededHint` */
    tagMaxLength?: number
    /** 输入被截断时展示在输入框下方的提示 */
    lengthExceededHint?: string
    /** 标签最多条数；达上限后拒绝继续添加 */
    maxTags?: number
    /** 标签数量达上限时的提示 */
    countExceededHint?: string
    /** 重复添加时的提示 */
    duplicateHint?: string
    /** 与外部列表冲突时禁止添加（如排除词不得与监控关键词相同） */
    conflictTags?: string[]
    /** 冲突时的提示 */
    conflictHint?: string
  }>(),
  { inputMaxlength: 256 },
)

const emit = defineEmits<{
  'update:draft': [value: string]
  add: [word: string]
  close: [index: number]
}>()

const inputRef = ref<HTMLInputElement | null>(null)
const showLengthHint = ref(false)
const showCountHint = ref(false)
const showDuplicateHint = ref(false)
const showConflictHint = ref(false)

const atTagCountLimit = computed(
  () => props.maxTags != null && props.tags.length >= props.maxTags,
)

const activeFieldHint = computed(() => {
  if (showCountHint.value && props.countExceededHint) return props.countExceededHint
  if (showConflictHint.value && props.conflictHint) return props.conflictHint
  if (showDuplicateHint.value && props.duplicateHint) return props.duplicateHint
  if (showLengthHint.value && props.lengthExceededHint) return props.lengthExceededHint
  return ''
})

const effectiveInputMaxlength = computed(() => {
  if (props.tagMaxLength != null) return props.tagMaxLength
  return props.inputMaxlength
})

function onFieldClick(e: MouseEvent) {
  const el = e.target as HTMLElement
  if (el.closest('.el-tag__close')) return
  inputRef.value?.focus()
}

function rejectAddAtCountLimit() {
  showCountHint.value = true
  showLengthHint.value = false
  showDuplicateHint.value = false
  showConflictHint.value = false
}

function rejectDuplicate() {
  showDuplicateHint.value = true
  showLengthHint.value = false
  showCountHint.value = false
  showConflictHint.value = false
}

function rejectConflict() {
  showConflictHint.value = true
  showLengthHint.value = false
  showCountHint.value = false
  showDuplicateHint.value = false
}

function commitDraft() {
  let segment = props.draft.trim()
  if (!segment) return
  if (atTagCountLimit.value) {
    rejectAddAtCountLimit()
    return
  }
  const max = props.tagMaxLength
  if (max != null && segment.length > max) {
    segment = segment.slice(0, max)
    showLengthHint.value = true
    showCountHint.value = false
    showDuplicateHint.value = false
    showConflictHint.value = false
  }
  if (props.conflictTags?.includes(segment)) {
    rejectConflict()
    return
  }
  if (props.tags.includes(segment)) {
    rejectDuplicate()
    return
  }
  emit('add', segment)
  emit('update:draft', '')
  showCountHint.value = false
  showDuplicateHint.value = false
  showConflictHint.value = false
}

function onInputKeydown(e: KeyboardEvent) {
  if (
    atTagCountLimit.value &&
    e.key.length === 1 &&
    !e.ctrlKey &&
    !e.metaKey &&
    !e.altKey
  ) {
    rejectAddAtCountLimit()
  }

  const max = props.tagMaxLength
  if (
    !atTagCountLimit.value &&
    max != null &&
    props.draft.length >= max &&
    e.key.length === 1 &&
    !e.ctrlKey &&
    !e.metaKey &&
    !e.altKey
  ) {
    showLengthHint.value = true
    showCountHint.value = false
    showDuplicateHint.value = false
    showConflictHint.value = false
  }

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
  const max = props.maxTags
  if (max != null && props.tags.length - 1 < max) showCountHint.value = false
  showDuplicateHint.value = false
  showConflictHint.value = false
}

function onDraftInput(e: Event) {
  const t = e.target as HTMLInputElement
  let value = t.value
  const max = props.tagMaxLength
  if (max != null && value.length > max) {
    value = value.slice(0, max)
    showLengthHint.value = true
  } else if (max == null || value.length < max) {
    showLengthHint.value = false
  }
  if (atTagCountLimit.value && value.length > 0) {
    rejectAddAtCountLimit()
  } else if (!atTagCountLimit.value) {
    showCountHint.value = false
  }
  showDuplicateHint.value = false
  showConflictHint.value = false
  if (t.value !== value) t.value = value
  emit('update:draft', value)
}
</script>

<template>
  <div class="inline-tag-field-wrap">
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
        :maxlength="effectiveInputMaxlength"
        :placeholder="placeholder"
        autocomplete="off"
        @click.stop
        @input="onDraftInput"
        @keydown="onInputKeydown"
      />
    </div>
    <p v-if="activeFieldHint" class="inline-tag-field__length-hint" role="alert">
      {{ activeFieldHint }}
    </p>
  </div>
</template>

<style scoped>
.inline-tag-field-wrap {
  width: 100%;
}

.inline-tag-field__length-hint {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.35;
  color: #f54a45;
}

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
