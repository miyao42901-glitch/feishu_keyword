<template>
  <div class="ops-page">
    <OpsStatGrid
      :stats="[
        { label: '注册用户总数', value: '312', sub: '本月新增 23', tone: 'up' },
        { label: '月活跃用户', value: '148', sub: '活跃率 47.4%', tone: 'up' },
        { label: '月留存率', value: '67.2%', sub: '↑ 3.5% vs 上月', tone: 'up' },
      ]"
    />

    <el-card shadow="never" class="ops-table-card">
      <div class="ops-table-head">
        <h3>用户列表</h3>
        <div class="ops-table-toolbar">
          <el-input v-model="keyword" placeholder="搜索用户ID / 手机号 / 备注..." clearable style="width: 240px" />
        </div>
      </div>
      <div class="admin-table-scroll">
        <el-table :data="pagedRows" stripe>
          <el-table-column prop="name" label="用户" width="90">
            <template #default="{ row }">
              <strong>{{ row.name }}</strong>
            </template>
          </el-table-column>
          <el-table-column prop="feishuId" label="飞书ID" min-width="140">
            <template #default="{ row }">
              <span style="font-family: monospace; font-size: 12px">{{ row.feishuId }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="phone" label="手机号" width="120" />
          <el-table-column prop="device" label="设备" width="80">
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{ row.device }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="version" label="插件版本" width="100" />
          <el-table-column prop="tasks" label="任务数" width="80" align="right" />
          <el-table-column prop="points" label="月消耗点数" width="110" align="right">
            <template #default="{ row }">{{ row.points.toLocaleString() }}</template>
          </el-table-column>
          <el-table-column prop="lastActive" label="最近活跃" width="150" />
          <el-table-column prop="remark" label="运营备注" min-width="120">
            <template #default="{ row }">
              <span v-if="row.remark">{{ row.remark }}</span>
              <span v-else style="color: var(--el-text-color-placeholder)">-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openDetail(row.id)">查看详情</el-button>
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

    <el-drawer v-model="drawerVisible" :title="drawerTitle" size="720px" destroy-on-close>
      <template v-if="activeUser">
        <div class="ops-user-profile">
          <div class="ops-user-avatar">{{ activeUser.name[0] }}</div>
          <div>
            <h4 style="margin: 0 0 8px">{{ activeUser.name }}</h4>
            <p style="margin: 0 0 4px; color: var(--el-text-color-secondary)">
              飞书ID: {{ activeUser.feishuId }} · {{ activeUser.phone }}
            </p>
            <p style="margin: 0 0 4px; color: var(--el-text-color-secondary)">
              设备: {{ activeUser.device }} · 版本: {{ activeUser.version }} · 首次使用: {{ activeUser.firstUse }}
            </p>
            <p style="margin: 0; color: var(--el-text-color-secondary)">活跃时段: {{ activeUser.activeHours }}</p>
            <el-tag v-if="activeUser.remark" type="info" size="small" style="margin-top: 8px">{{ activeUser.remark }}</el-tag>
          </div>
        </div>

        <div class="ops-detail-section">
          <div class="ops-detail-section-title">核心数据</div>
          <div class="ops-detail-kpi-grid">
            <div v-for="item in detailKpis" :key="item.label" class="ops-detail-kpi">
              <div style="font-size: 12px; color: var(--el-text-color-secondary)">{{ item.label }}</div>
              <div style="font-size: 20px; font-weight: 700; margin-top: 4px">{{ item.value }}</div>
            </div>
          </div>
        </div>

        <div class="ops-detail-section">
          <div class="ops-detail-section-title">任务列表 ({{ userTasks.length }})</div>
          <div class="admin-table-scroll">
            <el-table :data="userTasks" size="small" stripe>
              <el-table-column prop="id" label="任务ID" min-width="140" />
              <el-table-column prop="taskType" label="类型" width="90" />
              <el-table-column label="关键词" min-width="140">
                <template #default="{ row }">
                  <div class="ops-tag-gap">
                    <el-tag v-for="k in row.keywords" :key="k" size="small" effect="plain">{{ k }}</el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="80" />
              <el-table-column prop="points" label="消耗点数" width="90" align="right" />
            </el-table>
          </div>
        </div>

        <div class="ops-detail-section">
          <div class="ops-detail-section-title">点数消耗趋势</div>
          <VChart class="ops-chart" :option="pointTrendOption" autoresize />
        </div>

        <div class="ops-detail-section">
          <div class="ops-detail-section-title">点数消耗明细 ({{ userPoints.length }})</div>
          <div class="admin-table-scroll">
            <el-table :data="userPoints" size="small" stripe>
              <el-table-column prop="id" label="消耗ID" width="90" />
              <el-table-column prop="taskId" label="任务" min-width="140" />
              <el-table-column prop="platform" label="平台" width="100" />
              <el-table-column prop="amount" label="消耗量" width="80" align="right" />
              <el-table-column prop="balance" label="剩余余额" width="90" align="right" />
              <el-table-column prop="time" label="消耗时间" min-width="150" />
            </el-table>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { OpsChartOption } from '@/types/opsCharts'
import VChart from 'vue-echarts'
import OpsStatGrid from '@/components/ops/OpsStatGrid.vue'
import { useOpsEcharts } from '@/composables/useOpsEcharts'
import { EXEC_RECORDS, POINT_RECORDS, TASKS, USERS } from '@/mock/opsMockData'

useOpsEcharts()

const keyword = ref('')
const page = ref(1)
const pageSize = 10
const drawerVisible = ref(false)
const activeUserId = ref('')

const filteredRows = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  return USERS.filter((row) => {
    if (!q) return true
    const blob = [row.id, row.name, row.phone, row.remark].join(' ').toLowerCase()
    return blob.includes(q)
  })
})

const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredRows.value.slice(start, start + pageSize)
})

const activeUser = computed(() => USERS.find((u) => u.id === activeUserId.value) ?? null)

const drawerTitle = computed(() => (activeUser.value ? `用户详情 - ${activeUser.value.name}` : '用户详情'))

const userTasks = computed(() => {
  if (!activeUser.value) return []
  return TASKS.filter((t) => t.user === activeUser.value!.name)
})

const userExecs = computed(() => {
  const ids = new Set(userTasks.value.map((t) => t.id))
  return EXEC_RECORDS.filter((e) => ids.has(e.taskId))
})

const userPoints = computed(() => POINT_RECORDS.filter((r) => r.userId === activeUserId.value))

const detailKpis = computed(() => {
  const user = activeUser.value
  if (!user) return []
  const execs = userExecs.value
  const successRate = execs.length ? Math.round((execs.filter((e) => e.result === '成功').length / execs.length) * 100) : 0
  return [
    { label: '任务总数', value: user.tasks },
    { label: '运行中任务', value: userTasks.value.filter((t) => t.status === '运行中').length },
    { label: '累计消耗点数', value: user.points.toLocaleString() },
    { label: '执行次数（今日）', value: execs.length },
    { label: '执行成功率', value: `${successRate}%` },
    { label: '最近活跃', value: user.lastActive },
  ]
})

const pointTrendOption = computed(
  (): OpsChartOption => ({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 16, top: 16, bottom: 28 },
    xAxis: { type: 'category', data: ['5/22', '5/23', '5/24', '5/25', '5/26', '5/27', '5/28'] },
    yAxis: { type: 'value' },
    series: [
      {
        name: '点数消耗',
        type: 'line',
        smooth: true,
        data: [42, 58, 36, 51, 47, 63, 55],
        itemStyle: { color: '#4073fa' },
        areaStyle: { color: 'rgba(64,115,250,0.1)' },
      },
    ],
  }),
)

function openDetail(userId: string) {
  activeUserId.value = userId
  drawerVisible.value = true
}
</script>
