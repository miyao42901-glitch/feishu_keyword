<script setup lang="ts">
/**
 * 新建 / 编辑任务：整页表单入口，负责状态、校验、保存与子区块编排。
 */
import { computed, nextTick, reactive, ref, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import type { PlatformKey } from '@/components/PlatformIcon.vue'
import { createFeishuTaskConfig, updateFeishuTaskConfig } from '@/lib/api'
import type { FeishuTaskConfigDetail } from '@/lib/api'

import BasicInfoSection from '@/views/TaskCreateForm/components/BasicInfoSection.vue'
import KeywordsSection from '@/views/TaskCreateForm/components/KeywordsSection.vue'
import FilterSettingsSection from '@/views/TaskCreateForm/components/FilterSettingsSection.vue'
import SourceSelectionSection from '@/views/TaskCreateForm/components/SourceSelectionSection.vue'
import DataRetentionSection from '@/views/TaskCreateForm/components/DataRetentionSection.vue'

import { dataRangeOptions, sourcePlatforms } from '@/views/TaskCreateForm/constants'
import type { SourceFieldKey, TaskCreateFormModel } from '@/views/TaskCreateForm/types'

defineOptions({ name: 'TaskCreateForm' })

/** 编辑态任务 id；为空则保存时走创建接口 */
const props = withDefaults(
  defineProps<{
    taskConfigId?: number | null
    /** 详情接口回显用 */
    detail?: FeishuTaskConfigDetail | null
  }>(),
  { taskConfigId: null, detail: null },
)

const emit = defineEmits<{
  back: []
  saved: [id: number]
}>()

/** 各平台采集字段多选初始化为空数组，避免 undefined */
function emptySourceFieldSelection(): Record<PlatformKey, SourceFieldKey[]> {
  return {
    xiaohongshu: [],
    weibo: [],
    douyin: [],
    gzh: [],
    shipinhao: [],
    kuaishou: [],
  }
}

/** 表单默认值工厂（重置、合并前打底） */
function initialForm(): TaskCreateFormModel {
  return {
    planName: '',
    taskType: 'scheduled',
    crawlFrequency: '5',
    effectiveAt: '',
    expireAt: '',
    authCode: '',
    keywords: [],
    excludeKeywords: '',
    heatLikeMin: 0,
    heatCommentMin: 0,
    heatFavoriteMin: 0,
    heatShareMin: 0,
    sortOrder: 'latest',
    publishTime: 'unlimited',
    videoDuration: 'all',
    dataRange: dataRangeOptions[1],
    selectedSources: [],
    sourceFieldSelection: emptySourceFieldSelection(),
    tableMode: 'existing',
    existingTableId: '',
  }
}

/** 与 `el-form` 绑定的响应式模型 */
const form = reactive<TaskCreateFormModel>(initialForm())
/** Element Plus 表单实例，用于校验与 clearValidate */
const formRef = ref<FormInstance>()
/** 关键词输入框未完成提交的一行草稿（回车成 tag） */
const keywordDraft = ref('')

/** 已勾选信源按 `sourcePlatforms` 固定顺序排列，用于下方字段区展示顺序 */
const orderedSelectedPlatforms = computed(() =>
  sourcePlatforms.filter((p) => form.selectedSources.includes(p.id)),
)

const rules: FormRules = {
  authCode: [{ required: true, message: '请输入授权码', trigger: 'blur' }],
}

/** `el-collapse` 当前展开的面板 name 列表 */
const activePanels = ref<string[]>(['basic'])

/** 恢复默认并清空草稿与校验态 */
function resetForm() {
  Object.assign(form, initialForm())
  keywordDraft.value = ''
  void nextTick(() => formRef.value?.clearValidate())
}

/**
 * 将服务端 `config` 合并进表单；对 `sourceFieldSelection` 做白名单字段过滤。
 */
function mergeConfigIntoForm(raw: Record<string, unknown>) {
  Object.assign(form, initialForm(), raw as Partial<TaskCreateFormModel>)
  const sel = raw.sourceFieldSelection
  const merged = emptySourceFieldSelection()
  if (sel && typeof sel === 'object' && !Array.isArray(sel)) {
    for (const key of Object.keys(merged) as PlatformKey[]) {
      const v = (sel as Record<string, unknown>)[key]
      if (Array.isArray(v)) {
        merged[key] = v.filter(
          (x): x is SourceFieldKey => x === 'like' || x === 'comment' || x === 'share',
        )
      }
    }
  }
  form.sourceFieldSelection = merged
}

watch(
  () => [props.taskConfigId, props.detail] as const,
  ([id, d]) => {
    if (d?.config) {
      mergeConfigIntoForm(d.config)
      keywordDraft.value = ''
      void nextTick(() => formRef.value?.clearValidate())
    } else if (id == null) {
      resetForm()
    }
  },
  { immediate: true },
)

/** 深拷贝为普通对象便于 `JSON.stringify` 提交 */
function snapshotForm(): Record<string, unknown> {
  return JSON.parse(JSON.stringify(form)) as Record<string, unknown>
}

/** 校验通过后调用创建或更新接口 */
async function saveConfig() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  try {
    const payload = snapshotForm()
    if (props.taskConfigId != null) {
      await updateFeishuTaskConfig(props.taskConfigId, payload)
      ElMessage.success('配置已保存')
      emit('saved', props.taskConfigId)
    } else {
      const { id } = await createFeishuTaskConfig(payload)
      ElMessage.success('配置已保存')
      emit('saved', id)
    }
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '保存失败')
  }
}
</script>

<template>
  <div class="flex min-h-0 flex-col gap-6 pb-8">
    <div class="flex items-center gap-3">
      <el-button link type="primary" @click="emit('back')">← 返回任务列表</el-button>
    </div>
    <h2 class="text-lg font-medium text-slate-800">新建任务</h2>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="max-w-3xl">
      <el-collapse v-model="activePanels" class="task-form-collapse">
        <el-collapse-item title="基础信息" name="basic">
          <BasicInfoSection :form="form" />
        </el-collapse-item>

        <el-collapse-item title="关键词管理" name="keywords">
          <KeywordsSection
            :form="form"
            :keyword-draft="keywordDraft"
            @update:keyword-draft="keywordDraft = $event"
          />
        </el-collapse-item>

        <el-collapse-item title="过滤设置" name="filter">
          <FilterSettingsSection :form="form" />
        </el-collapse-item>

        <el-collapse-item title="信源选择" name="sources">
          <SourceSelectionSection :form="form" :ordered-platforms="orderedSelectedPlatforms" />
        </el-collapse-item>

        <el-collapse-item name="retention">
          <template #title>
            <span class="retention-collapse-title inline-flex items-center gap-2 text-sm font-semibold text-slate-800">
              <svg
                class="size-4 shrink-0 text-slate-600"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.75"
                aria-hidden="true"
              >
                <path d="M6 4h9l3 3v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1z" />
                <path d="M8 12h8M8 16h5" stroke-linecap="round" />
              </svg>
              数据沉淀配置
            </span>
          </template>

          <DataRetentionSection :form="form" />
        </el-collapse-item>
      </el-collapse>
    </el-form>

    <div class="flex flex-wrap gap-3 border-t border-slate-100 pt-6">
      <el-button @click="resetForm">重置</el-button>
      <el-button type="primary" @click="saveConfig">保存配置</el-button>
    </div>
  </div>
</template>

<style scoped>
.task-form-collapse {
  border: none;
}

.task-form-collapse :deep(.el-collapse-item) {
  margin-bottom: 0.5rem;
  border: 1px solid rgb(226 232 240);
  border-radius: 0.5rem;
  overflow: hidden;
  background: #fff;
}

.task-form-collapse :deep(.el-collapse-item__header) {
  height: auto;
  min-height: 48px;
  padding: 0 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: rgb(30 41 59);
  background: rgb(248 250 252);
}

.task-form-collapse :deep(.el-collapse-item__wrap) {
  border-bottom: none;
}

.task-form-collapse :deep(.el-collapse-item__content) {
  padding: 1rem 1rem 1.25rem;
  padding-bottom: 1.25rem;
}
</style>
