<script setup lang="ts">
/**
 * 信源：按 `mode` 仅展示「采集平台」勾选，或仅展示各平台「采集字段」下拉多选。
 */
import { nextTick, ref } from 'vue'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import type { SourceFieldKey } from '@/views/TaskCreateForm/types'
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'
import { sourcePlatforms } from '@/views/TaskCreateForm/constants'
import { sourceFieldFlatOptionsByPlatform } from '@/views/TaskCreateForm/source-field-catalog'

defineOptions({ name: 'SourceSelectionSection' })

const props = defineProps<{
  form: TaskCreateFormModel
  orderedPlatforms: { id: PlatformKey; label: string }[]
  /** `platforms`：采集平台勾选；`fields`：已选平台下的采集字段 */
  mode: 'platforms' | 'fields'
}>()

/** 当前展开的下拉（同时只展开一个） */
const openPlatform = ref<PlatformKey | null>(null)
/** 下拉层宽度与触发器对齐 */
const fieldPopoverWidth = ref(320)
const fieldTriggerRefs = ref<Partial<Record<PlatformKey, HTMLElement>>>({})

function setFieldTriggerRef(platform: PlatformKey, el: unknown) {
  if (el instanceof HTMLElement) fieldTriggerRefs.value[platform] = el
  else delete fieldTriggerRefs.value[platform]
}

async function setPopoverVisible(platform: PlatformKey, v: boolean) {
  if (v) {
    openPlatform.value = platform
    await nextTick()
    const w = fieldTriggerRefs.value[platform]?.offsetWidth
    if (w && w > 0) fieldPopoverWidth.value = w
  } else if (openPlatform.value === platform) {
    openPlatform.value = null
  }
}

function flatOptions(platform: PlatformKey) {
  return sourceFieldFlatOptionsByPlatform[platform] ?? []
}

function selectedCount(platform: PlatformKey) {
  return props.form.sourceFieldSelection[platform]?.length ?? 0
}

function totalCount(platform: PlatformKey) {
  return flatOptions(platform).length
}

function isChecked(platform: PlatformKey, key: SourceFieldKey) {
  return props.form.sourceFieldSelection[platform]?.includes(key) ?? false
}

function hasOptionalSelected(platform: PlatformKey) {
  const opts = flatOptions(platform)
  const selected = props.form.sourceFieldSelection[platform] ?? []
  return selected.some((key) => {
    const opt = opts.find((o) => o.value === key)
    return opt && !opt.required
  })
}

/** 未选可选字段时显示占位计数；已选则展示字段名列表 */
function triggerDisplayText(platform: PlatformKey): string {
  const count = selectedCount(platform)
  const total = totalCount(platform)
  if (!hasOptionalSelected(platform)) {
    return `请选择采集字段（默认已选${count}/${total}）`
  }
  const opts = flatOptions(platform)
  const selected = props.form.sourceFieldSelection[platform] ?? []
  const labels = opts.filter((o) => selected.includes(o.value)).map((o) => o.label)
  const text = labels.join('，')
  return text.length > 56 ? `${text.slice(0, 56)}...` : text
}

function isTriggerPlaceholder(platform: PlatformKey) {
  return !hasOptionalSelected(platform)
}

function setChecked(
  platform: PlatformKey,
  key: SourceFieldKey,
  checked: boolean,
  required?: boolean,
) {
  if (required) return
  const opts = flatOptions(platform)
  const requiredKeys = opts.filter((o) => o.required).map((o) => o.value)
  const next = new Set(props.form.sourceFieldSelection[platform] ?? [])
  if (checked) next.add(key)
  else next.delete(key)
  for (const r of requiredKeys) next.add(r)
  props.form.sourceFieldSelection[platform] = opts.map((o) => o.value).filter((v) => next.has(v))
}

function optionalOptions(platform: PlatformKey) {
  return flatOptions(platform).filter((o) => !o.required)
}

function isAllOptionalSelected(platform: PlatformKey): boolean {
  const optional = optionalOptions(platform)
  if (!optional.length) return true
  const selected = props.form.sourceFieldSelection[platform] ?? []
  return optional.every((o) => selected.includes(o.value))
}

function isSelectAllIndeterminate(platform: PlatformKey): boolean {
  const optional = optionalOptions(platform)
  if (!optional.length) return false
  const selected = props.form.sourceFieldSelection[platform] ?? []
  const n = optional.filter((o) => selected.includes(o.value)).length
  return n > 0 && n < optional.length
}

function selectAllCheckboxState(platform: PlatformKey): 'checked' | 'indeterminate' | 'empty' {
  if (isAllOptionalSelected(platform)) return 'checked'
  if (isSelectAllIndeterminate(platform)) return 'indeterminate'
  return 'empty'
}

function selectAllLabel(platform: PlatformKey): string {
  return isAllOptionalSelected(platform) ? '取消全选' : '全选'
}

function toggleSelectAll(platform: PlatformKey) {
  const opts = flatOptions(platform)
  const requiredKeys = opts.filter((o) => o.required).map((o) => o.value)
  if (isAllOptionalSelected(platform)) {
    props.form.sourceFieldSelection[platform] = opts
      .map((o) => o.value)
      .filter((v) => requiredKeys.includes(v))
  } else {
    props.form.sourceFieldSelection[platform] = opts.map((o) => o.value)
  }
}
</script>

<template>
  <div>
    <template v-if="props.mode === 'platforms'">
      <el-checkbox-group v-model="form.selectedSources" class="source-platform-group">
        <div class="source-platform-grid">
          <el-checkbox
            v-for="p in sourcePlatforms"
            :key="p.id"
            :value="p.id"
            border
            class="source-platform-checkbox"
          >
            <span class="source-platform-checkbox__label">{{ p.label }}</span>
          </el-checkbox>
        </div>
      </el-checkbox-group>
    </template>

    <template v-else>
      <div v-if="orderedPlatforms.length" class="source-field-list">
        <div v-for="p in orderedPlatforms" :key="p.id" class="source-field-block">
          <p class="task-form-field-title source-field-block__label">{{ p.label }}-采集字段</p>

          <el-popover
            :visible="openPlatform === p.id"
            trigger="click"
            placement="bottom-start"
            :width="fieldPopoverWidth"
            popper-class="source-field-popper"
            @update:visible="(v: boolean) => setPopoverVisible(p.id, v)"
          >
            <template #reference>
              <button
                :ref="(el) => setFieldTriggerRef(p.id, el)"
                type="button"
                class="source-field-trigger"
                :class="{ 'source-field-trigger--open': openPlatform === p.id }"
              >
                <span
                  class="source-field-trigger__text min-w-0 flex-1 truncate"
                  :class="
                    isTriggerPlaceholder(p.id)
                      ? 'source-field-trigger__text--placeholder'
                      : 'source-field-trigger__text--value'
                  "
                >
                  {{ triggerDisplayText(p.id) }}
                </span>
                <svg
                  class="source-field-trigger__chevron shrink-0"
                  :class="{ 'source-field-trigger__chevron--open': openPlatform === p.id }"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  aria-hidden="true"
                >
                  <path d="M6 9l6 6 6-6" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </button>
            </template>

            <div class="source-field-dropdown">
              <button
                v-if="optionalOptions(p.id).length > 0"
                type="button"
                class="source-field-option source-field-option--select-all"
                @click="toggleSelectAll(p.id)"
              >
                <span
                  class="source-field-option__checkbox"
                  :class="{
                    'source-field-option__checkbox--checked':
                      selectAllCheckboxState(p.id) === 'checked',
                    'source-field-option__checkbox--indeterminate':
                      selectAllCheckboxState(p.id) === 'indeterminate',
                    'source-field-option__checkbox--empty': selectAllCheckboxState(p.id) === 'empty',
                  }"
                  aria-hidden="true"
                >
                  <svg
                    v-if="selectAllCheckboxState(p.id) === 'checked'"
                    class="source-field-option__check-icon"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2.5"
                  >
                    <path d="M20 6L9 17l-5-5" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                  <span
                    v-else-if="selectAllCheckboxState(p.id) === 'indeterminate'"
                    class="source-field-option__minus"
                  />
                </span>
                <span class="source-field-option__label source-field-option__label--strong">
                  {{ selectAllLabel(p.id) }}
                </span>
              </button>
              <button
                v-for="opt in flatOptions(p.id)"
                :key="opt.value"
                type="button"
                class="source-field-option"
                :class="{
                  'source-field-option--required': opt.required,
                  'source-field-option--checked': isChecked(p.id, opt.value),
                }"
                :disabled="!!opt.required"
                @click="setChecked(p.id, opt.value, !isChecked(p.id, opt.value), !!opt.required)"
              >
                <span
                  class="source-field-option__checkbox"
                  :class="{
                    'source-field-option__checkbox--checked': isChecked(p.id, opt.value) && !opt.required,
                    'source-field-option__checkbox--required': isChecked(p.id, opt.value) && !!opt.required,
                    'source-field-option__checkbox--empty': !isChecked(p.id, opt.value),
                  }"
                  aria-hidden="true"
                >
                  <svg
                    v-if="isChecked(p.id, opt.value)"
                    class="source-field-option__check-icon"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2.5"
                  >
                    <path d="M20 6L9 17l-5-5" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </span>
                <span class="source-field-option__label">
                  {{ opt.label }}<template v-if="opt.required"> (必选)</template>
                </span>
              </button>
            </div>
          </el-popover>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.source-platform-group {
  display: block;
  width: 100%;
}

.source-platform-grid {
  display: grid;
  width: 100%;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.source-platform-group :deep(.source-platform-checkbox.el-checkbox) {
  box-sizing: border-box;
  width: 100%;
  max-width: none;
  margin-right: 0;
  margin-left: 0;
  height: auto;
  align-items: center;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  border: 1px solid #dee0e3;
  background: #ffffff;
  transition:
    background-color 0.15s ease,
    border-color 0.15s ease;
}

.source-platform-group :deep(.source-platform-checkbox.el-checkbox.is-checked) {
  background: #ededfe;
  border-color: #1f22f6;
}

.source-platform-group :deep(.source-platform-checkbox.el-checkbox.is-checked .el-checkbox__label) {
  color: #0f1114;
}

.source-platform-checkbox__label {
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.35;
  color: #0f1114;
}

.source-platform-group :deep(.source-platform-checkbox .el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #ffffff;
  border-color: #1f22f6;
}

.source-platform-group :deep(.source-platform-checkbox .el-checkbox__input.is-checked .el-checkbox__inner::after) {
  border-color: #1f22f6;
}

/* —— 第三步：采集字段 —— */
.source-field-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.source-field-block__label {
  margin: 0 0 8px;
}

.source-field-trigger {
  box-sizing: border-box;
  display: flex;
  width: 100%;
  min-height: 36px;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #dee0e3;
  border-radius: 4px;
  background: #ffffff;
  cursor: pointer;
  text-align: left;
  outline: none;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.source-field-trigger:hover {
  border-color: #bbbfc4;
}

.source-field-trigger--open,
.source-field-trigger:focus-visible {
  border-color: #1f22f6;
  box-shadow: 0 0 0 1px rgb(31 34 246 / 0.15);
}

.source-field-trigger__text {
  font-size: 14px;
  line-height: 1.4;
}

.source-field-trigger__text--placeholder {
  color: #8f959e;
  font-weight: 400;
}

.source-field-trigger__text--value {
  color: #2b2f36;
  font-weight: 400;
}

.source-field-trigger__chevron {
  width: 16px;
  height: 16px;
  color: #8f959e;
  transition: transform 0.2s ease;
}

.source-field-trigger__chevron--open {
  transform: rotate(180deg);
}

.source-field-dropdown {
  max-height: 280px;
  overflow-y: auto;
  padding: 4px 0;
}

.source-field-option--select-all {
  position: sticky;
  top: 0;
  z-index: 1;
  border-bottom: 1px solid #e5e7eb;
  background: #ffffff;
}

.source-field-option--select-all:hover {
  background: #f5f6f7;
}

.source-field-option__label--strong {
  font-weight: 500;
  color: #1f22f6;
}

.source-field-option__checkbox--indeterminate {
  border: 1px solid #1f22f6;
  background: #1f22f6;
}

.source-field-option__minus {
  display: block;
  width: 8px;
  height: 2px;
  border-radius: 1px;
  background: #ffffff;
}

.source-field-option {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 10px;
  margin: 0;
  padding: 8px 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
  transition: background-color 0.12s ease;
}

.source-field-option:hover:not(:disabled) {
  background: #f5f5f5;
}

.source-field-option--required {
  cursor: default;
}

.source-field-option:disabled {
  opacity: 1;
}

.source-field-option__checkbox {
  box-sizing: border-box;
  display: inline-flex;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
  transition:
    background-color 0.12s ease,
    border-color 0.12s ease;
}

.source-field-option__checkbox--empty {
  border: 1px solid #dee0e3;
  background: #ffffff;
}

.source-field-option__checkbox--checked {
  border: 1px solid #1f22f6;
  background: #1f22f6;
  color: #ffffff;
}

.source-field-option__checkbox--required {
  border: 1px solid rgb(31 34 246 / 0.35);
  background: rgb(237 237 254 / 0.85);
  color: #1f22f6;
}

.source-field-option__check-icon {
  width: 12px;
  height: 12px;
}

.source-field-option__label {
  min-width: 0;
  flex: 1;
  font-size: 14px;
  font-weight: 400;
  line-height: 1.4;
  color: #2b2f36;
}

.source-field-option--required .source-field-option__label {
  color: #646a73;
}
</style>

<style>
/* 下拉层 Teleport 到 body */
.source-field-popper.el-popover.el-popper {
  padding: 0;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgb(15 17 20 / 0.08);
}
</style>
