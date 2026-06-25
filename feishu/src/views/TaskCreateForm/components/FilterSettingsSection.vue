<script setup lang="ts">
/**
 * 折叠块「过滤设置」：排除词（内联标签 + 输入，同关键词管理）、排序/时间/时长/条数。
 */
import { computed } from 'vue'
import { EXCLUDE_KEYWORD_CONFLICT_HINT } from '@/lib/keyword-limits'
import type { TaskCreateFormModel } from '@/views/TaskCreateForm/types'
import InlineTagChipsInput from './InlineTagChipsInput.vue'
import {
  dataRangeOptions,
  publishTimeOptions,
  sortOrderOptions,
  videoDurationOptions,
} from '@/views/TaskCreateForm/constants'

defineOptions({ name: 'FilterSettingsSection' })

const props = defineProps<{
  form: TaskCreateFormModel
  excludeKeywordDraft: string
  /** 非 pending 编辑态：作品数据范围不可改 */
  scheduleLocked?: boolean
}>()
const emit = defineEmits<{ 'update:excludeKeywordDraft': [value: string] }>()

/** 仅「最新」排序时展示发布时间筛选 */
const showPublishTime = computed(() => props.form.sortOrder === 'latest')

/** 第二步暂隐藏视频时长（表单字段仍保留，便于后续恢复） */
const showVideoDuration = false

function onAddExclude(word: string) {
  const value = word.trim()
  if (!value || props.form.keywords.includes(value)) return
  if (props.form.excludeKeywords.includes(value)) return
  props.form.excludeKeywords.push(value)
}

function onRemoveExclude(i: number) {
  props.form.excludeKeywords.splice(i, 1)
}
</script>

<template>
  <div>
    <!-- 与「关键词管理」折叠块内编辑器同宽：不用 el-form-item，避免内容区被收窄 -->
    <div class="mb-6">
      <p class="task-form-field-title mb-3">排除词</p>
      <InlineTagChipsInput
        class="w-full"
        :tags="form.excludeKeywords"
        :draft="excludeKeywordDraft"
        :conflict-tags="form.keywords"
        :conflict-hint="EXCLUDE_KEYWORD_CONFLICT_HINT"
        placeholder="输入后按回车添加排除词"
        @update:draft="emit('update:excludeKeywordDraft', $event)"
        @add="onAddExclude"
        @close="onRemoveExclude"
      />
    </div>

    <el-form-item label="排序方式">
      <el-select v-model="form.sortOrder" placeholder="请选择" class="w-full">
        <el-option v-for="opt in sortOrderOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
    </el-form-item>
    <el-form-item v-if="showPublishTime" label="发布时间">
      <el-select v-model="form.publishTime" placeholder="请选择" class="w-full">
        <el-option v-for="opt in publishTimeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
    </el-form-item>
    <el-form-item v-if="showVideoDuration" label="视频时长">
      <el-select v-model="form.videoDuration" placeholder="请选择" class="w-full">
        <el-option v-for="opt in videoDurationOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
    </el-form-item>
    <el-form-item label="作品数据范围">
      <el-select
        v-model="form.dataRange"
        placeholder="请选择采集页数"
        class="w-full"
        :disabled="scheduleLocked"
      >
        <el-option v-for="n in dataRangeOptions" :key="n" :label="`${n}页`" :value="n" />
      </el-select>
    </el-form-item>
  </div>
</template>

