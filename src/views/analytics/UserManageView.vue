<template>
  <div class="analytics-page">
    <div class="analytics-stats-grid analytics-stats-grid--3">
      <div class="analytics-stat-card">
        <div class="analytics-stat-label">注册用户总数</div>
        <div class="analytics-stat-value">{{ data?.totalUsers ?? 0 }}</div>
        <div class="analytics-stat-sub">本月新增 {{ data?.newUsers ?? 0 }}</div>
      </div>
      <div class="analytics-stat-card">
        <div class="analytics-stat-label">月活跃用户</div>
        <div class="analytics-stat-value">{{ data?.activeUsers ?? 0 }}</div>
      </div>
      <div class="analytics-stat-card">
        <div class="analytics-stat-label">月留存率</div>
        <div class="analytics-stat-value">{{ data?.retention ?? '-' }}</div>
      </div>
    </div>

    <el-card shadow="never" class="analytics-table-card">
      <template #header>
        <div class="analytics-table-head">
          <h3>用户列表</h3>
          <div class="analytics-table-toolbar">
            <el-select v-model="range" style="width: 100px; margin-right: 12px" @change="loadData">
              <el-option label="今日" value="day" />
              <el-option label="本周" value="week" />
              <el-option label="本月" value="month" />
            </el-select>
            <el-input v-model="keyword" placeholder="搜索用户ID / 手机号 / 备注..." clearable style="width: 220px" />
          </div>
        </div>
      </template>
      <div v-loading="loading">
        <el-table :data="pagedRows" stripe size="small" style="width: 100%">
          <el-table-column prop="userId" label="用户ID" width="110" />
          <el-table-column prop="phone" label="手机号" width="120" />
          <el-table-column prop="deviceType" label="设备" width="80">
            <template #default="{ row }">
              <el-tag v-if="row.deviceType" size="small" effect="plain">{{ row.deviceType }}</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="pluginVersion" label="插件版本" width="100" />
          <el-table-column prop="taskCount" label="任务数" width="80" align="right" />
          <el-table-column prop="pointsConsumed" label="月消耗点数" width="110" align="right">
            <template #default="{ row }">{{ row.pointsConsumed.toLocaleString() }}</template>
          </el-table-column>
          <el-table-column label="最近活跃" width="150">
            <template #default="{ row }">
              {{ row.lastActiveAt ? row.lastActiveAt.replace('T', ' ').slice(0, 16) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="运营备注" min-width="120">
            <template #default="{ row }">
              <span v-if="row.remark">{{ row.remark }}</span>
              <span v-else style="color: var(--el-text-color-placeholder)">-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="90" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openDetail(row.userId)">详情</el-button>
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

    <el-drawer v-model="drawerVisible" :title="drawerTitle" size="640px" destroy-on-close>
      <div v-loading="drawerLoading" style="min-height: 200px; padding: 4px">
        <template v-if="activeDetail">
          <div class="analytics-user-profile">
            <div class="analytics-user-avatar">{{ activeDetail.userId[0] }}</div>
            <div style="flex: 1">
              <h4 style="margin: 0 0 6px">{{ activeDetail.userId }}</h4>
              <p style="margin: 0 0 4px; color: var(--el-text-color-secondary); font-size: 13px">
                飞书ID: {{ activeDetail.feishuId || '-' }} · {{ activeDetail.phone || '-' }}
              </p>
              <p style="margin: 0 0 4px; color: var(--el-text-color-secondary); font-size: 13px">
                设备: {{ activeDetail.deviceType || '-' }} · 版本: {{ activeDetail.pluginVersion || '-' }}
              </p>
              <p style="margin: 0 0 10px; color: var(--el-text-color-secondary); font-size: 13px">
                活跃时段: {{ activeDetail.activeHours || '-' }}
              </p>
              <div style="display: flex; gap: 8px; align-items: center">
                <el-input
                  v-model="editingRemark"
                  placeholder="运营备注（点击保存）"
                  style="flex: 1"
                  size="small"
                />
                <el-button size="small" :loading="remarkSaving" @click="saveRemark">保存</el-button>
              </div>
            </div>
          </div>

          <div class="analytics-detail-section">
            <div class="analytics-detail-section-title">核心数据</div>
            <div class="analytics-detail-kpi-grid">
              <div v-for="item in detailKpis" :key="item.label" class="analytics-detail-kpi">
                <div style="font-size: 11px; color: var(--el-text-color-secondary)">{{ item.label }}</div>
                <div style="font-size: 18px; font-weight: 700; margin-top: 4px">{{ item.value }}</div>
              </div>
            </div>
          </div>

          <div class="analytics-detail-section">
            <div class="analytics-detail-section-title">任务列表 ({{ activeDetail.tasks.length }})</div>
            <el-table :data="activeDetail.tasks" size="small" stripe>
              <el-table-column prop="taskId" label="任务ID" min-width="140" />
              <el-table-column prop="taskType" label="类型" width="90" />
              <el-table-column label="平台" min-width="120">
                <template #default="{ row }">
                  <el-tag v-for="p in row.platforms" :key="p" size="small" effect="plain" style="margin-right: 2px">
                    {{ p }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag
                    :type="row.status === '运行中' ? 'success' : row.status === '已停止' ? 'warning' : 'info'"
                    size="small"
                  >{{ row.status }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div class="analytics-detail-section">
            <div class="analytics-detail-section-title">点数消耗明细</div>
            <el-table :data="activeDetail.points" size="small" stripe>
              <el-table-column prop="consumeId" label="消耗ID" width="100" />
              <el-table-column prop="taskId" label="任务" min-width="130" />
              <el-table-column prop="platform" label="平台" width="90" />
              <el-table-column prop="amount" label="消耗量" width="80" align="right" />
              <el-table-column prop="balance" label="剩余余额" width="90" align="right" />
              <el-table-column label="时间" min-width="140">
                <template #default="{ row }">
                  {{ row.consumedAt ? row.consumedAt.replace('T', ' ').slice(0, 16) : '-' }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchUsers, fetchUserDetail, updateUserRemark } from '@/api/analytics'
import { ElMessage } from 'element-plus'

const keyword = ref('')
const page = ref(1)
const pageSize = 10
const range = ref('month')
const loading = ref(false)
const drawerLoading = ref(false)
const drawerVisible = ref(false)
const data = ref(null)
const activeDetail = ref(null)
const editingRemark = ref('')
const remarkSaving = ref(false)

async function loadData() {
  loading.value = true
  try {
    data.value = await fetchUsers(range.value)
  } finally {
    loading.value = false
  }
}

async function openDetail(userId) {
  drawerVisible.value = true
  drawerLoading.value = true
  activeDetail.value = null
  try {
    activeDetail.value = await fetchUserDetail(userId)
    editingRemark.value = activeDetail.value?.remark ?? ''
  } finally {
    drawerLoading.value = false
  }
}

async function saveRemark() {
  if (!activeDetail.value) return
  remarkSaving.value = true
  try {
    await updateUserRemark(activeDetail.value.userId, editingRemark.value)
    activeDetail.value.remark = editingRemark.value
    const rec = data.value?.records.find((r) => r.userId === activeDetail.value.userId)
    if (rec) rec.remark = editingRemark.value
    ElMessage.success('备注已保存')
  } finally {
    remarkSaving.value = false
  }
}

const filteredRows = computed(() => {
  if (!data.value) return []
  const q = keyword.value.trim().toLowerCase()
  return data.value.records.filter((row) => {
    if (!q) return true
    return [row.userId, row.phone, row.remark, row.feishuId].join(' ').toLowerCase().includes(q)
  })
})

const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredRows.value.slice(start, start + pageSize)
})

const drawerTitle = computed(() =>
  activeDetail.value ? `用户详情 - ${activeDetail.value.userId}` : '用户详情',
)

const detailKpis = computed(() => {
  const d = activeDetail.value
  if (!d) return []
  return [
    { label: '任务总数', value: d.taskCount },
    { label: '运行中任务', value: d.tasks.filter((t) => t.status === '运行中').length },
    { label: '累计消耗点数', value: d.totalPoints.toLocaleString() },
    { label: '总执行次数', value: d.execCount },
    { label: '执行成功率', value: d.execSuccessRate },
    {
      label: '最近活跃',
      value: d.lastActiveAt ? d.lastActiveAt.replace('T', ' ').slice(0, 16) : '-',
    },
  ]
})

onMounted(() => {
  loadData()
})
</script>
