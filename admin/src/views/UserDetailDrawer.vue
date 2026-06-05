<template>
  <el-drawer
    v-model="visible"
    title="用户详情"
    direction="rtl"
    size="600px"
    :before-close="close"
  >
    <div class="detail-body">
      <!-- 用户基本信息 -->
      <div class="user-profile">
        <el-avatar :size="48" style="background:#dde3ec;color:#374151;font-size:18px;flex-shrink:0">
          {{ (user?.userName ?? '-').slice(0, 1) }}
        </el-avatar>
        <div class="profile-info">
          <div class="profile-name">{{ user?.userName ?? '-' }}</div>
          <div class="profile-meta">飞书ID：{{ user?.feishuId ?? '-' }}</div>
          <div class="profile-meta">注册天数：{{ user?.loginDays != null ? user.loginDays + '天' : 'XX天' }}</div>
          <div class="profile-meta">最近活跃：{{ user?.registerTime ?? '-' }}</div>
          <div class="profile-meta">账户余额：XX元</div>
          <div class="profile-meta">累计使用金额：XXXX元</div>
        </div>
      </div>

      <!-- 点数消耗趋势图 -->
      <div class="section">
        <div class="section-title">点数消耗趋势</div>
        <div ref="trendEl" class="trend-chart" />
      </div>

      <!-- 点数消耗明细 -->
      <div class="section">
        <div class="section-title">点数消耗明细（{{ consumeRecords.length }}）</div>
        <el-table :data="consumeRecords" style="width:100%" size="small">
          <el-table-column prop="consumeId" label="消耗ID" width="100" />
          <el-table-column prop="taskId" label="任务" width="100" />
          <el-table-column prop="platform" label="平台" width="80" />
          <el-table-column prop="amount" label="消耗量" width="80" align="right" />
          <el-table-column prop="balance" label="剩余金额" width="90" align="right" />
          <el-table-column prop="consumedAt" label="消耗时间" min-width="140" />
        </el-table>
        <div v-if="consumeRecords.length === 0" class="empty-hint">暂无消耗记录</div>
      </div>

      <!-- 用户任务详情 -->
      <div class="section">
        <div class="section-title">用户任务详情</div>
        <el-table :data="taskRecords" style="width:100%" size="small">
          <el-table-column prop="taskId" label="任务ID" width="100">
            <template #default="{ row }">
              <el-link type="primary">{{ row.taskId }}</el-link>
            </template>
          </el-table-column>
          <el-table-column prop="platform" label="采集平台" width="90" />
          <el-table-column prop="taskType" label="采集类型" width="110" />
          <el-table-column prop="collectCount" label="采集条数" width="80" align="right" />
          <el-table-column prop="pointsCost" label="消耗金额" width="80" align="right" />
          <el-table-column prop="duration" label="耗时" width="80" />
          <el-table-column label="结果" width="70">
            <template #default="{ row }">
              <span :class="row.status === '成功' ? 'status-success' : 'status-fail'">
                ● {{ row.status }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  user: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue'])

const visible = ref(props.modelValue)
const trendEl = ref(null)
let trendChart = null

watch(() => props.modelValue, (val) => { visible.value = val })
watch(visible, (val) => { emit('update:modelValue', val) })

const consumeRecords = ref([])

const taskRecords = ref([
  { taskId: 'ihuhfuh32', platform: '抖音', taskType: '采集账号数据', collectCount: 867, pointsCost: 318.98, duration: '4m 23s', status: '成功' },
  { taskId: 'ihuhfuh32', platform: '视频号', taskType: '更新视频数据', collectCount: 398, pointsCost: 318.98, duration: '4m 23s', status: '失败' },
])

function close() {
  visible.value = false
}

function renderTrend() {
  if (!trendEl.value || !window.echarts) return
  if (!trendChart) trendChart = window.echarts.init(trendEl.value)

  const labels = ['5/22', '5/23', '5/24', '5/25', '5/26', '5/27', '5/28']
  const values = [60, 55, 70, 85, 45, 48, 44]

  trendChart.setOption({
    grid: { left: 40, right: 16, top: 16, bottom: 28 },
    xAxis: {
      type: 'category',
      data: labels,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { fontSize: 12, color: '#6b7280' },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 90,
      interval: 10,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
      axisLabel: { fontSize: 11, color: '#9ca3af' },
    },
    series: [{
      type: 'line',
      data: values,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      itemStyle: { color: '#4e7bef' },
      lineStyle: { color: '#4e7bef', width: 2 },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(78,123,239,0.25)' }, { offset: 1, color: 'rgba(78,123,239,0.02)' }] } },
    }],
  })
}

watch(visible, async (val) => {
  if (val) {
    await nextTick()
    renderTrend()
  } else {
    trendChart?.dispose()
    trendChart = null
  }
})

import { onBeforeUnmount } from 'vue'
onBeforeUnmount(() => { trendChart?.dispose() })
</script>

<style scoped>
.detail-body { padding: 0 4px 24px; }

.user-profile {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  padding: 16px 0 24px;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 24px;
}

.profile-info { display: flex; flex-direction: column; gap: 6px; }
.profile-name { font-size: 16px; font-weight: 700; color: #111827; }
.profile-meta { font-size: 13px; color: #6b7280; }

.section { margin-bottom: 28px; }
.section-title { font-size: 14px; font-weight: 600; color: #111827; margin-bottom: 12px; }

.trend-chart { height: 220px; width: 100%; }

.empty-hint { text-align: center; padding: 20px; font-size: 13px; color: #9ca3af; }

.status-success { font-size: 12px; color: #10b981; }
.status-fail    { font-size: 12px; color: #ef4444; }
</style>
