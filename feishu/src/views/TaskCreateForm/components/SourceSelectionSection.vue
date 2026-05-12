<script setup lang="ts">
/**
 * 折叠块「信源选择」：抖音 / 小红书；各平台用下拉多选（扁平列表，必选灰显）。
 */
import { ref } from 'vue'
import PlatformIcon from '@/components/PlatformIcon.vue'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import type { SourceFieldKey } from '@/views/TaskCreateForm/types'
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'
import { sourcePlatforms } from '@/views/TaskCreateForm/constants'
import { sourceFieldFlatOptionsByPlatform } from '@/views/TaskCreateForm/source-field-catalog'

defineOptions({ name: 'SourceSelectionSection' })

const props = defineProps<{
  form: TaskCreateFormModel
  orderedPlatforms: { id: PlatformKey; label: string }[]
}>()

/** 当前展开的下拉（同时只展开一个） */
const openPlatform = ref<PlatformKey | null>(null)

function setPopoverVisible(platform: PlatformKey, v: boolean) {
  if (v) openPlatform.value = platform
  else if (openPlatform.value === platform) openPlatform.value = null
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
</script>

<template>
  <div>
    <p class="mb-3 text-xs leading-relaxed text-slate-500">
      当前仅支持抖音与小红书。请在各平台下拉框中选择需要写入表格的采集字段；必选字段不可取消。
    </p>
    <el-checkbox-group v-model="form.selectedSources" class="source-platform-group">
      <div class="flex flex-wrap gap-3">
        <el-checkbox v-for="p in sourcePlatforms" :key="p.id" :value="p.id" border class="source-platform-checkbox">
          <div class="flex items-center gap-2.5 py-0.5 pr-1">
            <PlatformIcon :platform="p.id" />
            <span class="text-sm font-medium text-slate-800">{{ p.label }}</span>
          </div>
        </el-checkbox>
      </div>
    </el-checkbox-group>

    <div v-if="orderedPlatforms.length" class="mt-5 space-y-4">
      <div
        v-for="p in orderedPlatforms"
        :key="p.id"
        class="rounded-lg border border-slate-200 bg-slate-50/90 px-4 py-3"
      >
        <div class="mb-2 flex items-center gap-2">
          <PlatformIcon class="!size-7" :platform="p.id" />
          <span class="text-sm font-medium text-slate-800">{{ p.label }} - 选择采集字段</span>
        </div>

        <el-popover
          :visible="openPlatform === p.id"
          trigger="click"
          placement="bottom-start"
          :width="320"
          popper-class="source-field-popper p-0"
          @update:visible="(v: boolean) => setPopoverVisible(p.id, v)"
        >
          <template #reference>
            <button
              type="button"
              class="flex w-full max-w-md cursor-pointer items-center justify-between rounded border bg-white px-3 py-2.5 text-left text-sm transition-colors outline-none hover:border-slate-400 focus-visible:ring-2 focus-visible:ring-[#3355FF]/30"
              :class="openPlatform === p.id ? 'border-[#3355FF] shadow-[0_0_0_1px_rgba(51,85,255,0.2)]' : 'border-slate-300'"
            >
              <span class="text-slate-600">选择采集字段（已选{{ selectedCount(p.id) }}/{{ totalCount(p.id) }}）</span>
              <svg
                class="size-4 shrink-0 text-slate-500 transition-transform"
                :class="openPlatform === p.id ? '-rotate-180' : ''"
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

          <div class="max-h-64 overflow-y-auto py-1">
            <button
              v-for="opt in flatOptions(p.id)"
              :key="opt.value"
              type="button"
              class="field-row-btn flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm"
              :class="
                opt.required
                  ? 'cursor-default bg-slate-50 text-slate-400'
                  : 'cursor-pointer text-slate-800 hover:bg-slate-50'
              "
              :disabled="!!opt.required"
              @click="setChecked(p.id, opt.value, !isChecked(p.id, opt.value), !!opt.required)"
            >
              <span
                class="flex size-[18px] shrink-0 items-center justify-center rounded border transition-colors"
                :class="
                  isChecked(p.id, opt.value)
                    ? opt.required
                      ? 'border-transparent text-slate-400'
                      : 'border-transparent text-[#3355FF]'
                    : 'border-slate-300 bg-white'
                "
                aria-hidden="true"
              >
                <svg
                  v-if="isChecked(p.id, opt.value)"
                  class="size-3.5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.5"
                >
                  <path d="M20 6L9 17l-5-5" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
              <span class="min-w-0 flex-1 leading-snug">{{ opt.label }}</span>
              <span
                v-if="opt.required"
                class="shrink-0 rounded bg-slate-200/80 px-1.5 py-0.5 text-[10px] font-medium text-slate-500"
              >
                必选
              </span>
            </button>
          </div>
        </el-popover>
      </div>
    </div>
  </div>
</template>

<style scoped>
.source-platform-group :deep(.source-platform-checkbox) {
  margin-right: 0;
  margin-left: 0;
  height: auto;
  align-items: center;
  padding: 0.5rem 0.75rem;
}

.field-row-btn:disabled {
  opacity: 1;
}
</style>

<style>
/* 下拉层由 Teleport 挂到 body，需非 scoped */
.source-field-popper.el-popover.el-popper {
  padding: 0;
}
</style>
