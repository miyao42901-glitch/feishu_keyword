<template>
  <div class="ops-page">
    <OpsStatGrid
      :col-sm="6"
      :stats="[
        { label: '今日推送次数', value: data?.total ?? 0, sub: '', tone: 'neutral' },
        { label: '推送触达率', value: data?.deliveryRate ?? '-', sub: '', tone: 'neutral' },
        { label: '通知打开次数（本月）', value: data?.notifyOnCount ?? 0, sub: '', tone: 'neutral' },
        { label: '通知关闭次数（本月）', value: data?.notifyOffCount ?? 0, sub: '', tone: 'neutral' },
      ]"
    />

    <el-card shadow="never" class="ops-table-card">
      <div class="ops-table-head">
        <h3>推送记录</h3>
        <div class="ops-table-toolbar">
          <el-select v-model="range" style="width: 100px; margin-right: 12px" @change="loadData">
            <el-option label="今日" value="day" />
            <el-option label="本周" value="week" />
            <el-option label="本月" value="month" />
          </el-select>
          <el-input v-model="keyword" placeholder="搜索推送ID / 任务ID..." clearable style="width: 220px" />
        </div>
      </div>
      <div class="admin-table-scroll">
        <el-table :data="pagedRows" stripe v-loading="loading">
          <el-table-column prop="pushId" label="推送ID" width="120" />
          <el-table-column prop="taskId" label="任务ID" min-width="120">
            <template #default="{ row }">
              <el-link v-if="row.taskId" type="primary" :underline="false">{{ row.taskId }}</el-link>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="webhook" label="Webhook" min-width="180" show-overflow-tooltip />
          <el-table-column prop="sendAt" label="发送时间" width="160" />
          <el-table-column prop="sendResult" label="发送结果" width="90">
            <template #default="{ row }">
              <el-tag :type="row.sendResult === '成功' ? 'success' : 'danger'" size="small">{{ row.sendResult }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="callbackResult" label="回调结果" width="90">
            <template #default="{ row }">
              <el-tag v-if="row.callbackResult" :type="callbackTagType(row.callbackResult)" size="small">{{
                row.callbackResult
              }}</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="newDataCount" label="新增数据" width="90" align="right" />
          <el-table-column prop="retryCount" label="重试次数" width="90" align="right">
            <template #default="{ row }">
              <span :style="{ color: row.retryCount > 0 ? '#ff7d00' : undefined }">{{ row.retryCount }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-pagination
        class="admin-pagination"
        style="margin-top: 16px; justify-content: flex-end"
        background
        layout="total, prev, pager, next"
        :total="filteredRows.length"
        :page-size="pageSize"
        v-model:current-page="page"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import OpsStatGrid from '@/components/ops/OpsStatGrid.vue'
import { fetchPushLogs, type PushLogsData, type AnalyticsRange } from '@/api/analytics'

const keyword = ref('')
const page = ref(1)
const pageSize = 10
const range = ref<AnalyticsRange>('day')
const loading = ref(false)
const data = ref<PushLogsData | null>(null)

async function loadData() {
  loading.value = true
  try {
    data.value = await fetchPushLogs(range.value)
  } finally {
    loading.value = false
  }
}

function callbackTagType(value: string) {
  if (value === '成功') return 'success'
  if (value === '失败') return 'danger'
  return 'warning'
}

const filteredRows = computed(() => {
  if (!data.value) return []
  const q = keyword.value.trim().toLowerCase()
  return data.value.records.filter((row) => {
    if (!q) return true
    return `${row.pushId} ${row.taskId}`.toLowerCase().includes(q)
  })
})

const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredRows.value.slice(start, start + pageSize)
})

onMounted(() => {
  loadData()
})
</script>
