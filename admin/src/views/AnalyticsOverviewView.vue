<template>
  <div class="overview-page">
    <div class="overview-header">
      <el-button-group>
        <el-button :type="timeRange === 'day' ? 'primary' : ''" @click="timeRange = 'day'">ä»Šæ—¥</el-button>
        <el-button :type="timeRange === 'week' ? 'primary' : ''" @click="timeRange = 'week'">æœ¬å‘¨</el-button>
        <el-button :type="timeRange === 'month' ? 'primary' : ''" @click="timeRange = 'month'">æœ¬æœˆ</el-button>
      </el-button-group>
    </div>

    <div v-loading="loading">
      <div class="kpi-grid">
        <div v-for="kpi in kpiCards" :key="kpi.key" class="kpi-card">
          <div class="kpi-label">{{ kpi.label }}</div>
          <div class="kpi-value">{{ kpi.value }}</div>
          <div class="kpi-change" :class="kpi.changeType">{{ kpi.change }}</div>
        </div>
      </div>

      <div class="charts-row">
        <el-card shadow="never" class="chart-card">
          <template #header><span class="chart-title">å„å¹³å°æ•°æ®é‡‡é›†åˆ†å¸ƒ</span></template>
          <div ref="platformEl" class="chart-body" />
        </el-card>
        <el-card shadow="never" class="chart-card">
          <template #header><span class="chart-title">é‡‡é›†å¤±è´¥åŸå› åˆ†å¸ƒ</span></template>
          <div ref="failureEl" class="chart-body" />
        </el-card>
      </div>

      <el-card shadow="never" class="funnel-card">
        <template #header>
          <div class="funnel-card-header">
            <span class="chart-title">ä»»åŠ¡æ¼æ–—-ä»æ‰“å¼€æ’ä»¶åˆ°é‡‡é›†æˆåŠŸ</span>
            <el-link type="primary" style="font-size:13px">&lt; è¿”å›ç²¾ç®€ç‰ˆæ¼æ–—</el-link>
          </div>
        </template>
        <div class="funnel-body">

          <!-- é¡¶éƒ¨å…±åŒæ­¥éª¤ -->
          <div class="funnel-common">
            <template v-for="(step, idx) in funnelCommon" :key="step.label">
              <div class="funnel-step">
                <div class="funnel-bar-row">
                  <div class="funnel-step-label">{{ step.label }}</div>
                  <div class="funnel-bar-wrap">
                    <div class="funnel-bar" :style="{ width: pct(step.value, funnelCommon[0].value) + '%' }" />
                  </div>
                  <span class="funnel-bar-value">{{ Number(step.value).toLocaleString() }}</span>
                  <span class="funnel-bar-pct">{{ pct(step.value, funnelCommon[0].value) }}%</span>
                </div>
              </div>
              <div v-if="idx < funnelCommon.length - 1" class="funnel-drop-row">
                <span class="funnel-drop-label">{{ step.dropLabel }}</span>
                <span class="funnel-drop-pct">{{ step.dropPct }}</span>
              </div>
            </template>
          </div>

          <!-- åˆ†æ”¯åˆ†å‰²çº¿ -->
          <div class="funnel-divider">
            <span class="funnel-divider-text">æ ¹æ®ä»»åŠ¡ç±»å‹ è¿›è¡Œæ¼æ–—åˆ†æ”¯</span>
          </div>

          <!-- å·¦å³ä¸¤åˆ—åˆ†æ”¯ -->
          <div class="funnel-branches">
            <div class="funnel-branch">
              <div class="funnel-branch-title">é‡‡é›†è´¦å·æ•°æ®ï¼ˆåŒ…æ‹¬æ›´æ–°ï¼‰</div>
              <template v-for="step in funnelAccount" :key="step.label">
                <div v-if="step.dropLabel" class="funnel-drop-row">
                  <span class="funnel-drop-label">{{ step.dropLabel }}</span>
                  <span class="funnel-drop-pct">{{ step.dropPct }}</span>
                </div>
                <div class="funnel-step">
                  <div class="funnel-bar-row">
                    <div class="funnel-step-label">{{ step.label }}</div>
                    <div class="funnel-bar-wrap">
                      <div
                        class="funnel-bar"
                        :class="{ 'funnel-bar--success': step.isSuccess }"
                        :style="{ width: pct(step.value, funnelCommon[0].value) + '%' }"
                      />
                    </div>
                    <span class="funnel-bar-value">{{ step.value != null ? Number(step.value).toLocaleString() : 'xxx' }}</span>
                    <span class="funnel-bar-pct">{{ step.value != null ? pct(step.value, funnelCommon[0].value) + '%' : 'xx%' }}</span>
                  </div>
                </div>
              </template>
            </div>

            <div class="funnel-branch">
              <div class="funnel-branch-title">é‡‡é›†è§†é¢‘æ•°æ®ï¼ˆåŒ…æ‹¬æ›´æ–°ï¼‰</div>
              <template v-for="step in funnelVideo" :key="step.label + '_v'">
                <div v-if="step.dropLabel" class="funnel-drop-row">
                  <span class="funnel-drop-label">{{ step.dropLabel }}</span>
                  <span class="funnel-drop-pct">{{ step.dropPct }}</span>
                </div>
                <div class="funnel-step">
                  <div class="funnel-bar-row">
                    <div class="funnel-step-label">{{ step.label }}</div>
                    <div class="funnel-bar-wrap">
                      <div
                        class="funnel-bar"
                        :class="{ 'funnel-bar--success': step.isSuccess }"
                        :style="{ width: pct(step.value, funnelCommon[0].value) + '%' }"
                      />
                    </div>
                    <span class="funnel-bar-value">{{ step.value != null ? Number(step.value).toLocaleString() : 'xxx' }}</span>
                    <span class="funnel-bar-pct">{{ step.value != null ? pct(step.value, funnelCommon[0].value) + '%' : 'xx%' }}</span>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { fetchAnalyticsOverview } from '@/api/analytics'

const timeRange = ref('month')
const loading = ref(false)
const overview = ref(null)
const platformEl = ref(null)
const failureEl = ref(null)
let platformChart = null
let failureChart = null

async function loadData() {
  loading.value = true
  try {
    overview.value = await fetchAnalyticsOverview(timeRange.value)
    await nextTick()
    renderCharts()
  } finally {
    loading.value = false
  }
}

const KPI_BY_RANGE = {
  day: [
    { key: 'users',  label: 'ÓĞĞ§ÓÃ»§',       value: '312',    change: '+8 ½Ï×òÈÕ',    changeType: 'up' },
    { key: 'calls',  label: 'µ÷ÓÃ´ÎÊı',       value: '428',    change: '+32 ½Ï×òÈÕ',   changeType: 'up' },
    { key: 'points', label: 'ÏûºÄ½ğ¶î',       value: '1,204',  change: '+98 ½Ï×òÈÕ',   changeType: 'up' },
    { key: 'rate',   label: '²É¼¯ÈÎÎñ³É¹¦ÂÊ', value: '91.2%',  change: '+0.8% ½Ï×òÈÕ', changeType: 'up' },
    { key: 'time',   label: 'Æ½¾ùÈ«Á÷³ÌÊ±³¤', value: '3m 58s', change: '-5% ½Ï×òÈÕ',   changeType: 'up' },
  ],
  week: [
    { key: 'users',  label: 'ÓĞĞ§ÓÃ»§',       value: '876',    change: '+42 ½ÏÉÏÖÜ',   changeType: 'up' },
    { key: 'calls',  label: 'µ÷ÓÃ´ÎÊı',       value: '3,024',  change: '+215 ½ÏÉÏÖÜ',  changeType: 'up' },
    { key: 'points', label: 'ÏûºÄ½ğ¶î',       value: '8,340',  change: '+620 ½ÏÉÏÖÜ',  changeType: 'up' },
    { key: 'rate',   label: '²É¼¯ÈÎÎñ³É¹¦ÂÊ', value: '89.5%',  change: '+0.5% ½ÏÉÏÖÜ', changeType: 'up' },
    { key: 'time',   label: 'Æ½¾ùÈ«Á÷³ÌÊ±³¤', value: '4m 05s', change: '-2% ½ÏÉÏÖÜ',   changeType: 'up' },
  ],
  month: [
    { key: 'users',  label: 'ÓĞĞ§ÓÃ»§',       value: '1,231',  change: '+113 ½ÏÉÏÔÂ',   changeType: 'up' },
    { key: 'calls',  label: 'µ÷ÓÃ´ÎÊı',       value: '14,528', change: '+1,123 ½ÏÉÏÔÂ', changeType: 'up' },
    { key: 'points', label: 'ÏûºÄ½ğ¶î',       value: '14,528', change: '+1,123 ½ÏÉÏÔÂ', changeType: 'up' },
    { key: 'rate',   label: '²É¼¯ÈÎÎñ³É¹¦ÂÊ', value: '88.8%',  change: '+1.2% ½ÏÉÏÔÂ',  changeType: 'up' },
    { key: 'time',   label: 'Æ½¾ùÈ«Á÷³ÌÊ±³¤', value: '4m 23s', change: '-2% ½ÏÉÏÔÂ',    changeType: 'up' },
  ],
}

const FUNNEL_COMMON = {
  day: [
    { label: '´ò¿ª²å¼ş', value: 1840,  dropLabel: '¨‹ Î´µÇÂ¼Á÷Ê§',        dropPct: '8%' },
    { label: 'Íê³ÉµÇÂ¼', value: 1693,  dropLabel: '¨‹ Ñ¡ÔñÈÎÎñÀàĞÍÊ±·ÅÆú', dropPct: '0%' },
    { label: 'ÈÎÎñÀàĞÍ', value: 1693,  dropLabel: null, dropPct: null },
  ],
  week: [
    { label: '´ò¿ª²å¼ş', value: 9240,  dropLabel: '¨‹ Î´µÇÂ¼Á÷Ê§',        dropPct: '9%' },
    { label: 'Íê³ÉµÇÂ¼', value: 8408,  dropLabel: '¨‹ Ñ¡ÔñÈÎÎñÀàĞÍÊ±·ÅÆú', dropPct: '0%' },
    { label: 'ÈÎÎñÀàĞÍ', value: 8408,  dropLabel: null, dropPct: null },
  ],
  month: [
    { label: '´ò¿ª²å¼ş', value: 12840, dropLabel: '¨‹ Î´µÇÂ¼Á÷Ê§',        dropPct: '8%' },
    { label: 'Íê³ÉµÇÂ¼', value: 11813, dropLabel: '¨‹ Ñ¡ÔñÈÎÎñÀàĞÍÊ±·ÅÆú', dropPct: '0%' },
    { label: 'ÈÎÎñÀàĞÍ', value: 11813, dropLabel: null, dropPct: null },
  ],
}

const FUNNEL_ACCOUNT = {
  day: [
    { label: 'Ğ´Èë±í¸ñ', value: null, dropLabel: '¨‹ Ñ¡Ôñ±í¸ñÊ±·ÅÆú',  dropPct: '16%' },
    { label: '²É¼¯ÕËºÅ', value: null, dropLabel: '¨‹ ÊäÈëÕËºÅÊ±·ÅÆú',  dropPct: '17%' },
    { label: 'µã»÷²É¼¯', value: null, dropLabel: '¨‹ ÅäÖÃÍê³Éºó·ÅÆú',  dropPct: '2%'  },
    { label: '²É¼¯³É¹¦', value: 384,  dropLabel: '¨‹ Ö´ĞĞÊ§°Ü',       dropPct: '5%', isSuccess: true },
  ],
  week: [
    { label: 'Ğ´Èë±í¸ñ', value: null, dropLabel: '¨‹ Ñ¡Ôñ±í¸ñÊ±·ÅÆú',  dropPct: '16%' },
    { label: '²É¼¯ÕËºÅ', value: null, dropLabel: '¨‹ ÊäÈëÕËºÅÊ±·ÅÆú',  dropPct: '17%' },
    { label: 'µã»÷²É¼¯', value: null, dropLabel: '¨‹ ÅäÖÃÍê³Éºó·ÅÆú',  dropPct: '2%'  },
    { label: '²É¼¯³É¹¦', value: 2053, dropLabel: '¨‹ Ö´ĞĞÊ§°Ü',       dropPct: '5%', isSuccess: true },
  ],
  month: [
    { label: 'Ğ´Èë±í¸ñ', value: null, dropLabel: '¨‹ Ñ¡Ôñ±í¸ñÊ±·ÅÆú',  dropPct: '16%' },
    { label: '²É¼¯ÕËºÅ', value: null, dropLabel: '¨‹ ÊäÈëÕËºÅÊ±·ÅÆú',  dropPct: '17%' },
    { label: 'µã»÷²É¼¯', value: null, dropLabel: '¨‹ ÅäÖÃÍê³Éºó·ÅÆú',  dropPct: '2%'  },
    { label: '²É¼¯³É¹¦', value: 4542, dropLabel: '¨‹ Ö´ĞĞÊ§°Ü',       dropPct: '5%', isSuccess: true },
  ],
}

const FUNNEL_VIDEO = {
  day: [
    { label: 'Ğ´Èë±í¸ñ', value: null, dropLabel: '¨‹ Ñ¡Ôñ±í¸ñÊ±·ÅÆú',  dropPct: '16%' },
    { label: '²É¼¯ÕËºÅ', value: null, dropLabel: '¨‹ ÊäÈëÕËºÅÊ±·ÅÆú',  dropPct: '34%' },
    { label: 'Êı¾İ·¶Î§', value: null, dropLabel: '¨‹ Ñ¡Ôñ·¶Î§Ê±·ÅÆú',  dropPct: '0%'  },
    { label: 'µã»÷²É¼¯', value: null, dropLabel: '¨‹ ÅäÖÃÍê³Éºó·ÅÆú',  dropPct: '2%'  },
    { label: '²É¼¯³É¹¦', value: 384,  dropLabel: '¨‹ Ö´ĞĞÊ§°Ü',       dropPct: '5%', isSuccess: true },
  ],
  week: [
    { label: 'Ğ´Èë±í¸ñ', value: null, dropLabel: '¨‹ Ñ¡Ôñ±í¸ñÊ±·ÅÆú',  dropPct: '16%' },
    { label: '²É¼¯ÕËºÅ', value: null, dropLabel: '¨‹ ÊäÈëÕËºÅÊ±·ÅÆú',  dropPct: '34%' },
    { label: 'Êı¾İ·¶Î§', value: null, dropLabel: '¨‹ Ñ¡Ôñ·¶Î§Ê±·ÅÆú',  dropPct: '0%'  },
    { label: 'µã»÷²É¼¯', value: null, dropLabel: '¨‹ ÅäÖÃÍê³Éºó·ÅÆú',  dropPct: '2%'  },
    { label: '²É¼¯³É¹¦', value: 2053, dropLabel: '¨‹ Ö´ĞĞÊ§°Ü',       dropPct: '5%', isSuccess: true },
  ],
  month: [
    { label: 'Ğ´Èë±í¸ñ', value: null, dropLabel: '¨‹ Ñ¡Ôñ±í¸ñÊ±·ÅÆú',  dropPct: '16%' },
    { label: '²É¼¯ÕËºÅ', value: null, dropLabel: '¨‹ ÊäÈëÕËºÅÊ±·ÅÆú',  dropPct: '34%' },
    { label: 'Êı¾İ·¶Î§', value: null, dropLabel: '¨‹ Ñ¡Ôñ·¶Î§Ê±·ÅÆú',  dropPct: '0%'  },
    { label: 'µã»÷²É¼¯', value: null, dropLabel: '¨‹ ÅäÖÃÍê³Éºó·ÅÆú',  dropPct: '2%'  },
    { label: '²É¼¯³É¹¦', value: 4542, dropLabel: '¨‹ Ö´ĞĞÊ§°Ü',       dropPct: '5%', isSuccess: true },
  ],
}

const kpiCards    = computed(() => KPI_BY_RANGE[timeRange.value]  ?? KPI_BY_RANGE.month)
const funnelCommon  = computed(() => FUNNEL_COMMON[timeRange.value]  ?? FUNNEL_COMMON.month)
const funnelAccount = computed(() => FUNNEL_ACCOUNT[timeRange.value] ?? FUNNEL_ACCOUNT.month)
const funnelVideo   = computed(() => FUNNEL_VIDEO[timeRange.value]   ?? FUNNEL_VIDEO.month)

function pct(value, base) {
  if (!value || !base) return 0
  return Math.round((value / base) * 100)
}

const PLATFORM_BY_RANGE = { day: [52,23,13,8,4], week: [49,25,14,7,5], month: [52,23,13,8,4] }
const FAILURE_BY_RANGE  = { day: [85,18,12,8],   week: [86,16,13,7],   month: [88,15,11,6]  }
const PLATFORM_COLORS   = ['#a78bfa','#fb7185','#4ade80','#38bdf8','#fb923c']
const FAILURE_COLORS    = ['#ef4444','#fb923c','#fbbf24','#a3b899']

function buildHBarOption(labels, values, colors) {
  const maxVal = Math.max(...values)
  return {
    grid: { left: 110, right: 80, top: 10, bottom: 10, containLabel: false },
    xAxis: { type: 'value', show: false, max: maxVal * 1.3 },
    yAxis: {
      type: 'category', data: labels, inverse: true,
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { fontSize: 13, color: '#374151' },
    },
    series: [{
      type: 'bar',
      data: values.map((v, i) => ({ value: v, itemStyle: { color: colors[i], borderRadius: [0,4,4,0] } })),
      barWidth: 20,
      label: { show: true, position: 'right', formatter: (p) => `${p.value}%`, fontSize: 12, color: '#6b7280', distance: 8 },
      showBackground: true,
      backgroundStyle: { color: '#f3f4f6', borderRadius: [0,4,4,0] },
    }],
  }
}

function renderCharts() {
  if (!window.echarts) return
  const pv = PLATFORM_BY_RANGE[timeRange.value] ?? PLATFORM_BY_RANGE.month
  const fv = FAILURE_BY_RANGE[timeRange.value]  ?? FAILURE_BY_RANGE.month
  if (platformEl.value) {
    if (!platformChart) platformChart = window.echarts.init(platformEl.value)
    platformChart.setOption(buildHBarOption(['¶¶Òô','Ğ¡ºìÊé','¹«ÖÚºÅ','ÊÓÆµºÅ','¿ìÊÖ'], pv, PLATFORM_COLORS))
  }
  if (failureEl.value) {
    if (!failureChart) failureChart = window.echarts.init(failureEl.value)
    failureChart.setOption(buildHBarOption(['ÕËºÅID´íÎó','Óà¶î²»×ã','ÍøÂç³¬Ê±','ÆäËûÔ­Òò'], fv, FAILURE_COLORS))
  }
}

watch(timeRange, () => loadData())
onMounted(() => loadData())
onBeforeUnmount(() => { platformChart?.dispose(); failureChart?.dispose() })
</script>

<style scoped>
.overview-page { padding: 0; }
.overview-header { display: flex; justify-content: flex-end; margin-bottom: 20px; }

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}
@media (max-width: 1300px) { .kpi-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 768px)  { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }

.kpi-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px 18px 16px; }
.kpi-label { font-size: 13px; color: #6b7280; margin-bottom: 8px; }
.kpi-value { font-size: 30px; font-weight: 700; color: #111827; line-height: 1.15; margin-bottom: 6px; letter-spacing: -0.5px; }
.kpi-change { font-size: 12px; }
.kpi-change.up   { color: #10b981; }
.kpi-change.down { color: #ef4444; }

.charts-row { display: flex; gap: 16px; margin-bottom: 20px; }
.chart-card { flex: 1; min-width: 0; }
.chart-title { font-size: 14px; font-weight: 600; color: #111827; }
.chart-body { height: 230px; }

.funnel-card { margin-bottom: 20px; }
.funnel-card-header { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.funnel-body { padding: 16px 0; }
.funnel-common { margin-bottom: 0; }

.funnel-step { padding: 8px 0; }
.funnel-bar-row { display: flex; align-items: center; gap: 12px; }
.funnel-step-label { font-size: 13px; color: #374151; font-weight: 500; min-width: 90px; flex-shrink: 0; }
.funnel-bar-wrap { flex: 1; height: 32px; background: #f3f4f6; border-radius: 0 4px 4px 0; overflow: hidden; }
.funnel-bar { height: 100%; background: #4e7bef; border-radius: 0 4px 4px 0; transition: width 0.5s ease; min-width: 2px; }
.funnel-bar--success { background: #34c759; }
.funnel-bar-value { font-size: 14px; font-weight: 600; color: #111827; min-width: 60px; text-align: right; flex-shrink: 0; }
.funnel-bar-pct   { font-size: 13px; color: #6b7280; min-width: 40px; flex-shrink: 0; }

.funnel-drop-row { padding: 4px 0 4px 102px; font-size: 12px; color: #6b7280; }
.funnel-drop-label { margin-right: 6px; }
.funnel-drop-pct   { color: #f59e0b; font-weight: 600; }

.funnel-divider {
  border-top: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb;
  padding: 10px 0;
  margin: 20px 0;
  text-align: center;
  background: #fafafa;
}
.funnel-divider-text { font-size: 13px; font-weight: 600; color: #6b7280; }

.funnel-branches { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
@media (max-width: 1100px) { .funnel-branches { grid-template-columns: 1fr; gap: 20px; } }
.funnel-branch { min-width: 0; }
.funnel-branch-title {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  text-align: center;
  background: #f3f4f6;
  border-radius: 6px;
  padding: 8px 12px;
  margin-bottom: 4px;
}
</style>
