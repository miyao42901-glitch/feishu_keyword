<template>
  <div class="analytics-page">
    <div class="analytics-stats-grid analytics-stats-grid--4">
      <div class="analytics-stat-card">
        <div class="analytics-stat-label">推送次数</div>
        <div class="analytics-stat-value">{{ data?.total ?? 0 }}</div>
      </div>
      <div class="analytics-stat-card">
        <div class="analytics-stat-label">推送触达率</div>
        <div class="analytics-stat-value">{{ data?.deliveryRate ?? '-' }}</div>
      </div>
      <div class="analytics-stat-card">
        <div class="analytics-stat-label">通知打开（本月）</div>
        <div class="analytics-stat-value">{{ data?.notifyOnCount ?? 0 }}</div>
      </div>
      <div class="analytics-stat-card">
        <div class="analytics-stat-label">通知关闭（本月）</div>
        <div class="analytics-stat-value">{{ data?.notifyOffCount ?? 0 }}</div>
      </div>
    </div>

    <el-card shadow="never" class="analytics-table-card">
      <template #header>
        <div class="analytics-table-head">
          <h3>推送记录</h3>
          <div class="analytics-table-toolbar">
            <el-select v-model="range" style="width: 100px; margin-right: 12px" @change="loadData">
              <el-option label="今日" value="day" />
              <el-option label="本周" value="week" />
              <el-option label="本月" value="month" />
            </el-select>
            <el-input v-model="keyword" placeholder="搜索推送ID / 任务ID..." clearable style="width: 200px" />
          </div>
        </div>
      </template>
      <div v-loading="loading">
        <el-table :data="pagedRows" stripe size="small" style="width: 100%">
          <el-table-column prop="pushId" label="推送ID" width="110" />
          <el-table-column prop="taskId" label="任务ID" min-width="140" />
          <el-table-column prop="webhook" label="Webhook" min-width="160" show-overflow-tooltip />
          <el-table-column prop="sendAt" label="发送时间" width="150" />
          <el-table-column prop="sendResult" label="发送结果" width="90">
            <template #default="{ row }">
              <el-tag :type="row.sendResult === '成功' ? 'success' : 'danger'" size="small">
                {{ row.sendResult }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="callbackResult" label="回调结果" width="90">
            <template #default="{ row }">
              <el-tag v-if="row.callbackResult" :type="callbackTagType(row.callbackResult)" size="small">
                {{ row.callbackResult }}
              </el-tag>
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
        <el-pagination
          style="margin-top: 16px; justify-content: flex-end"
          background
          layout="total, prev, pager, next"
          :total="filteredRows.length"
          :page-size="pageSize"
          v-model:current-page="page"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchPushLogs } from '@/api/analytics'

const keyword = ref('')
const page = ref(1)
const pageSize = 10
const range = ref('day')
const loading = ref(false)
const data = ref(null)

async function loadData() {
  loading.value = true
  try {
    data.value = await fetchPushLogs(range.value)
  } finally {
    loading.value = false
  }
}

function callbackTagType(value) {
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
