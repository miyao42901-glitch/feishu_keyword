<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAccountPointsStore } from '@/stores/accountPoints'

defineOptions({ name: 'AccountMemberView' })

const accountPoints = useAccountPointsStore()

/** 可选充值档位：点数、价格（元）、可选「省 xx 元」文案 */
const packages: { id: string; points: number; priceYuan: number; saveLabel?: string }[] = [
  { id: 'p500', points: 500, priceYuan: 29 },
  { id: 'p2000', points: 2000, priceYuan: 99, saveLabel: '省19元' },
  { id: 'p5000', points: 5000, priceYuan: 199, saveLabel: '省90元' },
]

const selectedId = ref<string>('p500')
const submitting = ref(false)

function selectPackage(id: string) {
  selectedId.value = id
}

async function onRecharge() {
  const pkg = packages.find((p) => p.id === selectedId.value)
  if (!pkg || submitting.value) return
  submitting.value = true
  try {
    await new Promise((r) => setTimeout(r, 280))
    accountPoints.setCurrentBalancePoints(accountPoints.currentBalancePoints + pkg.points)
    ElMessage.success(`已充值 ${pkg.points} 点`)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="-m-4 min-h-full bg-[#f8f9fa] p-4 pb-8">
    <!-- 点数充值 -->
    <section
      class="rounded-2xl border border-slate-100/80 bg-white p-5 shadow-sm"
      style="box-shadow: 0 1px 3px rgb(0 0 0 / 0.04)"
    >
      <div class="mb-4 flex items-start justify-between gap-3">
        <div class="flex min-w-0 items-center gap-2">
          <span class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#eef2ff] text-[#2b4dfc]">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M12 2l2.2 5.5L20 9l-4.5 3.4L17 18l-5-3-5 3 1.5-5.6L4 9l5.8-1.5L12 2z" />
            </svg>
          </span>
          <span class="text-base font-bold text-slate-900">点数充值</span>
        </div>
        <div class="shrink-0 text-right">
          <span class="text-2xl font-bold tabular-nums text-[#2b4dfc]">{{ accountPoints.currentBalancePoints }}点</span>
        </div>
      </div>

      <div class="mb-5 grid grid-cols-3 gap-2 sm:gap-3">
        <button
          v-for="p in packages"
          :key="p.id"
          type="button"
          class="flex min-h-[88px] flex-col items-center justify-center rounded-xl border-2 px-2 py-3 text-center transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#2b4dfc]/35"
          :class="
            selectedId === p.id
              ? 'border-[#2b4dfc] bg-[#eef2ff]'
              : 'border-transparent bg-slate-100/90 hover:bg-slate-100'
          "
          @click="selectPackage(p.id)"
        >
          <span class="text-sm font-bold text-slate-900">{{ p.points }}点</span>
          <span class="mt-1 text-sm font-semibold text-[#2b4dfc]">¥{{ p.priceYuan }}</span>
          <span
            v-if="p.saveLabel"
            class="mt-1 text-xs font-medium text-[#28a745]"
          >
            {{ p.saveLabel }}
          </span>
        </button>
      </div>

      <button
        type="button"
        class="flex h-12 w-full items-center justify-center rounded-xl bg-[#2b4dfc] text-base font-semibold text-white shadow-sm transition-opacity hover:opacity-95 active:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="submitting"
        @click="onRecharge"
      >
        {{ submitting ? '处理中…' : '立即充值' }}
      </button>
    </section>

    <p class="my-4 px-1 text-center text-xs leading-relaxed text-slate-400">
      点数永不过期，用于采集数据，如需发票请联系客服
    </p>

    <!-- 联系客服 -->
    <section
      class="rounded-2xl border border-slate-100/80 bg-white p-5 shadow-sm"
      style="box-shadow: 0 1px 3px rgb(0 0 0 / 0.04)"
    >
      <div class="mb-4 flex items-center justify-center gap-2">
        <span class="text-red-500" aria-hidden="true">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
            <path
              d="M6.62 10.79a15.15 15.15 0 006.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"
            />
          </svg>
        </span>
        <span class="text-base font-bold text-slate-900">联系客服</span>
      </div>

      <div
        class="mx-auto flex aspect-square max-w-[200px] items-center justify-center rounded-xl border-2 border-dashed border-slate-200 bg-slate-50/80 text-sm text-slate-400"
      >
        客服二维码
      </div>

      <p class="mt-3 text-center text-xs text-slate-400">
        扫码添加客服，获取专属支持
      </p>
    </section>
  </div>
</template>
