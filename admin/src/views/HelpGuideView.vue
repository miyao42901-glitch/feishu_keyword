<template>
  <div class="help-page">
    <div class="page-header">
      <el-button-group>
        <el-button :type="tab === 'all' ? 'primary' : ''" @click="tab = 'all'">全部</el-button>
        <el-button :type="tab === 'reg' ? 'primary' : ''" @click="tab = 'reg'">已登录</el-button>
        <el-button :type="tab === 'unreg' ? 'primary' : ''" @click="tab = 'unreg'">未登录</el-button>
      </el-button-group>
      <el-button-group>
        <el-button :type="range === 'day' ? 'primary' : ''" @click="range = 'day'">今日</el-button>
        <el-button :type="range === 'week' ? 'primary' : ''" @click="range = 'week'">本周</el-button>
        <el-button :type="range === 'month' ? 'primary' : ''" @click="range = 'month'">本月</el-button>
      </el-button-group>
    </div>

    <div class="kpi-row">
      <el-card shadow="never" class="kpi-card">
        <div class="kpi-label">使用指南点击率</div>
        <div class="kpi-value">28%</div>
      </el-card>
      <el-card shadow="never" class="kpi-card">
        <div class="kpi-label">了解更多点击率</div>
        <div class="kpi-value">13%</div>
      </el-card>
      <el-card shadow="never" class="kpi-card">
        <div class="kpi-label">加入交流群点击率</div>
        <div class="kpi-value">9%</div>
      </el-card>
    </div>

    <div class="charts-row">
      <el-card shadow="never" class="chart-card">
        <template #header><span class="chart-title">使用指南点击时机分布</span></template>
        <div ref="guideBarEl" class="bar-chart" />
      </el-card>

      <el-card shadow="never" class="chart-card">
        <template #header><span class="chart-title">新用户VS老用户点击对比</span></template>
        <div class="compare-table">
          <div class="compare-row compare-header">
            <div class="compare-cell">用户类型</div>
            <div class="compare-cell">指南点击率</div>
            <div class="compare-cell">了解更多点击率</div>
          </div>
          <div v-for="row in compareData" :key="row.label" class="compare-row">
            <div class="compare-cell label-cell">{{ row.label }}</div>
            <div class="compare-cell">
              <div class="bar-cell">
                <div class="bar-fill" :style="{ width: row.guide + '%', background: '#38bdf8' }" />
                <span class="bar-text">{{ row.guide }}%</span>
              </div>
            </div>
            <div class="compare-cell">
              <div class="bar-cell">
                <div class="bar-fill" :style="{ width: row.more + '%', background: '#fb923c' }" />
                <span class="bar-text">{{ row.more }}%</span>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const tab = ref('all')
const range = ref('month')
const guideBarEl = ref(null)
let guideBarChart = null

const compareData = [
  { label: '注册0~3天',   guide: 54, more: 19 },
  { label: '注册4~14天',  guide: 27, more: 27 },
  { label: '注册15天以上', guide: 12, more: 62 },
]

function renderGuideBar() {
  const labels = ['视频后点击', '结束中点击', '商订开单点击']
  const vals = [61, 27, 12]
  const colors = ['#ef4444', '#fb923c', '#fbbf24']

  if (!guideBarEl.value || !window.echarts) return
  if (!guideBarChart) guideBarChart = window.echarts.init(guideBarEl.value)

  guideBarChart.setOption({
    grid: { left: 100, right: 80, top: 10, bottom: 10, containLabel: false },
    xAxis: { type: 'value', show: false, max: Math.max(...vals) * 1.25 },
    yAxis: { type: 'category', data: labels, inverse: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { fontSize: 13, color: '#374151' } },
    series: [{
      type: 'bar',
      data: vals.map((v, i) => ({ value: v, itemStyle: { color: colors[i], borderRadius: [0, 4, 4, 0] } })),
      barWidth: 20,
      label: { show: true, position: 'right', formatter: (p) => `${p.value}%`, fontSize: 12, color: '#6b7280', distance: 8 },
      showBackground: true,
      backgroundStyle: { color: '#f3f4f6', borderRadius: [0, 4, 4, 0] },
    }],
  })
}

watch([tab, range], async () => { await nextTick(); renderGuideBar() })
onMounted(async () => { await nextTick(); renderGuideBar() })
onBeforeUnmount(() => { guideBarChart?.dispose() })
</script>

<style scoped>
.help-page { padding: 0; }

.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }

.kpi-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px; }
@media (max-width: 900px) { .kpi-row { grid-template-columns: 1fr; } }

.kpi-card { padding: 4px 0; }
.kpi-label { font-size: 13px; color: #6b7280; margin-bottom: 10px; }
.kpi-value { font-size: 36px; font-weight: 700; color: #111827; line-height: 1.1; margin-bottom: 8px; letter-spacing: -0.5px; }

.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 1000px) { .charts-row { grid-template-columns: 1fr; } }

.chart-title { font-size: 14px; font-weight: 600; color: #111827; }
.bar-chart { height: 220px; }

.compare-table { padding: 8px 0; }
.compare-row { display: grid; grid-template-columns: 120px 1fr 1fr; gap: 16px; padding: 12px 0; border-bottom: 1px solid #f3f4f6; }
.compare-row:last-child { border-bottom: none; }
.compare-header { font-size: 13px; font-weight: 600; color: #6b7280; background: #fafafa; padding: 10px 0; }
.compare-cell { display: flex; align-items: center; }
.label-cell { font-size: 13px; color: #374151; }

.bar-cell { position: relative; width: 100%; height: 28px; background: #f3f4f6; border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; transition: width 0.4s ease; }
.bar-text { position: absolute; left: 8px; top: 50%; transform: translateY(-50%); font-size: 12px; font-weight: 600; color: #111827; }
</style>
