<script setup lang="ts">
/**
 * 第三步「采集数据写入表格」：自动新建需展开高级配置；使用现有表格直接展示平台映射。
 */
import { ArrowRight } from '@element-plus/icons-vue'
import { computed, onMounted, ref, watch } from 'vue'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import { fetchBitableTableMetaList } from '@/lib/feishu-bitable-tables'
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'

defineOptions({ name: 'DataRetentionSection' })

const props = defineProps<{
  form: TaskCreateFormModel
  orderedPlatforms: { id: PlatformKey; label: string }[]
}>()

const bitableTableOptions = ref<{ id: string; name: string }[]>([])
const tableListLoading = ref(false)
const tableListError = ref('')
const advancedExpanded = ref(false)

async function loadBitableTables() {
  tableListLoading.value = true
  tableListError.value = ''
  try {
    bitableTableOptions.value = await fetchBitableTableMetaList()
  } catch {
    bitableTableOptions.value = []
    tableListError.value = '无法读取表格列表（请在多维表格插件内使用）'
  } finally {
    tableListLoading.value = false
  }
}

watch(
  () => props.form.tableMode,
  (mode) => {
    if (mode === 'existing') void loadBitableTables()
  },
)

watch(
  () => props.orderedPlatforms.map((p) => p.id),
  (ids) => {
    for (const p of props.orderedPlatforms) {
      if (!props.form.platformNewTableNames[p.id]?.trim()) {
        props.form.platformNewTableNames[p.id] = `${p.label}数据表`
      }
    }
    for (const key of Object.keys(props.form.platformNewTableNames) as PlatformKey[]) {
      if (!ids.includes(key) && props.form.platformNewTableNames[key]) {
        props.form.platformNewTableNames[key] = ''
      }
    }
    for (const key of Object.keys(props.form.platformExistingTableIds) as PlatformKey[]) {
      if (!ids.includes(key) && props.form.platformExistingTableIds[key]) {
        props.form.platformExistingTableIds[key] = ''
      }
    }
  },
  { immediate: true },
)

onMounted(() => {
  if (props.form.tableMode === 'existing') void loadBitableTables()
})

const duplicateExistingTableIds = computed(() => {
  const dupes = new Set<string>()
  const seen = new Set<string>()
  for (const p of props.orderedPlatforms) {
    const id = props.form.platformExistingTableIds[p.id]?.trim()
    if (!id) continue
    if (seen.has(id)) dupes.add(id)
    else seen.add(id)
  }
  return dupes
})

const hasDuplicateExistingTables = computed(() => duplicateExistingTableIds.value.size > 0)

/** 使用现有表格：直接展示；自动新建：需展开高级配置 */
const showMappingPanel = computed(() => {
  if (props.orderedPlatforms.length === 0) return false
  if (props.form.tableMode === 'existing') return true
  return advancedExpanded.value
})

const isWriteTableBoxExpanded = computed(() => showMappingPanel.value)

function isDuplicateExistingTable(platform: PlatformKey): boolean {
  const id = props.form.platformExistingTableIds[platform]?.trim()
  if (!id) return false
  return duplicateExistingTableIds.value.has(id)
}

function onPickAutoTable() {
  props.form.tableMode = 'new'
  props.form.existingTableId = ''
}

function onPickExistingTable() {
  props.form.tableMode = 'existing'
  void loadBitableTables()
}

function toggleAdvanced() {
  advancedExpanded.value = !advancedExpanded.value
}
</script>

<template>
  <div class="write-table-section">
    <div class="write-table-box" :class="{ 'write-table-box--expanded': isWriteTableBoxExpanded }">
      <div class="write-table-segmented" role="tablist" aria-label="采集数据写入表格">
        <button
          type="button"
          role="tab"
          :aria-selected="form.tableMode === 'new'"
          class="write-table-segment"
          :class="{ 'write-table-segment--active': form.tableMode === 'new' }"
          @click="onPickAutoTable"
        >
          <span class="write-table-segment__label whitespace-nowrap">自动新建表格</span>
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="form.tableMode === 'existing'"
          class="write-table-segment"
          :class="{ 'write-table-segment--active': form.tableMode === 'existing' }"
          @click="onPickExistingTable"
        >
          <span class="write-table-segment__label whitespace-nowrap">使用现有表格</span>
        </button>
      </div>

      <button
        v-if="form.tableMode === 'new'"
        type="button"
        class="advanced-config-trigger"
        :aria-expanded="advancedExpanded"
        aria-controls="write-table-advanced-panel"
        @click="toggleAdvanced"
      >
        <span class="advanced-config-trigger__text">高级配置</span>
        <span
          class="advanced-config-trigger__icon-wrap"
          :class="{ 'advanced-config-trigger__icon-wrap--open': advancedExpanded }"
        >
          <el-icon class="advanced-config-trigger__icon" :size="12">
            <ArrowRight />
          </el-icon>
        </span>
      </button>

      <div
        id="write-table-advanced-panel"
        v-show="showMappingPanel"
        class="advanced-config-panel"
      >
        <div class="platform-table-mapping__header">
          <span class="platform-table-mapping__title">平台-表格映射</span>
          <span class="platform-table-mapping__hint">*为每个平台指定数据写入的目标表格</span>
        </div>

        <div class="platform-table-mapping__rows">
          <div
            v-for="p in orderedPlatforms"
            :key="p.id"
            class="platform-table-mapping__row"
          >
            <span class="platform-table-mapping__platform">{{ p.label }}</span>
            <span class="platform-table-mapping__arrow" aria-hidden="true">→</span>

            <el-input
              v-if="form.tableMode === 'new'"
              v-model="form.platformNewTableNames[p.id]"
              class="platform-table-mapping__control"
              placeholder="请输入表格名称"
              clearable
            />

            <el-select
              v-else
              v-model="form.platformExistingTableIds[p.id]"
              class="platform-table-mapping__control"
              :class="{ 'platform-table-mapping__control--error': isDuplicateExistingTable(p.id) }"
              placeholder="请选择表格"
              clearable
              filterable
              :loading="tableListLoading"
            >
              <el-option
                v-for="opt in bitableTableOptions"
                :key="opt.id"
                :label="opt.name"
                :value="opt.id"
              />
            </el-select>
          </div>
        </div>

        <div
          v-if="form.tableMode === 'existing' && hasDuplicateExistingTables"
          class="platform-table-mapping__error"
          role="alert"
        >
          <span class="platform-table-mapping__error-icon" aria-hidden="true">!</span>
          <span>请为每个平台选择不同的表格，不可重复</span>
        </div>

        <p
          v-if="form.tableMode === 'existing' && tableListError"
          class="platform-table-mapping__list-hint"
        >
          {{ tableListError }}
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.write-table-section {
  width: 100%;
}

.write-table-box {
  box-sizing: border-box;
  display: flex;
  width: 378px;
  max-width: 100%;
  min-height: 106px;
  flex-direction: column;
  align-items: stretch;
  justify-content: flex-start;
  gap: 10px;
  padding: 12px 10px 14px;
  border-radius: 6px;
  background: #f8f9fa;
}

.write-table-box--expanded {
  min-height: auto;
}

.write-table-segmented {
  box-sizing: border-box;
  display: flex;
  width: 100%;
  max-width: 358px;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: stretch;
  align-self: center;
  gap: 6px;
  padding: 4px 0;
  border-radius: 6px;
  background: transparent;
}

.write-table-segment {
  box-sizing: border-box;
  display: inline-flex;
  min-width: 0;
  height: 40px;
  flex: 1 1 0;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin: 0;
  padding: 0 8px;
  border: 1px solid #dee0e3;
  border-radius: 4px;
  background: #ffffff;
  font-size: 14px;
  font-weight: 500;
  line-height: 1;
  color: #0f1114;
  cursor: pointer;
  transition:
    background-color 0.15s ease,
    border-color 0.15s ease,
    color 0.15s ease;
}

.write-table-segment:hover:not(.write-table-segment--active) {
  border-color: #bbbfc4;
}

.write-table-segment--active {
  background: #ededfe;
  border-color: #1f22f6;
  color: #1f22f6;
}

.write-table-segment--active .write-table-segment__label {
  color: #1f22f6;
}

.advanced-config-trigger {
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  gap: 6px;
  margin: 0;
  padding: 0;
  border: none;
  background: none;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.35;
  color: #8f959e;
  cursor: pointer;
  text-align: left;
}

.advanced-config-trigger:hover {
  color: #646a73;
}

.advanced-config-trigger:focus-visible {
  outline: none;
  border-radius: 4px;
  box-shadow: 0 0 0 2px rgb(31 34 246 / 0.2);
}

.advanced-config-trigger__icon-wrap {
  box-sizing: border-box;
  display: inline-flex;
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border: 1px dashed #c9cdd4;
  border-radius: 2px;
  color: #8f959e;
  transition: transform 0.2s ease;
}

.advanced-config-trigger__icon-wrap--open {
  transform: rotate(90deg);
}

.advanced-config-trigger__icon {
  display: flex;
}

.advanced-config-panel {
  width: 100%;
  padding-top: 4px;
}

.platform-table-mapping__header {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px 8px;
  margin-bottom: 12px;
}

.platform-table-mapping__title {
  font-size: 12px;
  font-weight: 500;
  line-height: 1.4;
  color: #2b2f36;
}

.platform-table-mapping__hint {
  font-size: 12px;
  font-weight: 400;
  line-height: 1.4;
  color: #8f959e;
}

.platform-table-mapping__rows {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.platform-table-mapping__row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.platform-table-mapping__platform {
  flex-shrink: 0;
  min-width: 3.5rem;
  font-size: 14px;
  font-weight: 400;
  line-height: 1.4;
  color: #2b2f36;
}

.platform-table-mapping__arrow {
  flex-shrink: 0;
  font-size: 14px;
  line-height: 1;
  color: #8f959e;
}

.platform-table-mapping__control {
  min-width: 0;
  flex: 1 1 auto;
}

.platform-table-mapping__control :deep(.el-input__wrapper),
.platform-table-mapping__control :deep(.el-select__wrapper) {
  min-height: 36px;
  border-radius: 4px;
  box-shadow: 0 0 0 1px #dee0e3 inset !important;
  background: #ffffff;
}

.platform-table-mapping__control :deep(.el-input__wrapper.is-focus),
.platform-table-mapping__control :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 1px #1f22f6 inset !important;
}

.platform-table-mapping__control--error :deep(.el-select__wrapper) {
  box-shadow: 0 0 0 1px #f54a45 inset !important;
}

.platform-table-mapping__error {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 4px;
  background: #fef0f0;
  font-size: 12px;
  line-height: 1.5;
  color: #f54a45;
}

.platform-table-mapping__error-icon {
  display: inline-flex;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f54a45;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  color: #ffffff;
}

.platform-table-mapping__list-hint {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.4;
  color: #d97706;
}
</style>
