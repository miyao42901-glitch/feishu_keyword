<template>
  <el-dialog
    v-model="dialogVisible"
    width="378px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    class="collect-success-dialog"
    :show-close="true"
  >
    <template v-if="showStatsLayout">
      <div class="dialog-title">
        <img
          src="/icon/collect-success-icon.png"
          srcset="/icon/collect-success-icon@2x.png 2x"
          alt="采集成功"
          class="success-icon-img"
        />
        <span class="title-text">{{ props.title }}</span>
      </div>

      <div class="stats-panel">
        <template v-if="isAddAccountLayout">
          <div class="stats-row">
            <span class="stats-label">新增账号</span>
            <span class="stats-value stats-value-primary">
              {{ formatCollectCount(props.newAccounts, '个') }}
            </span>
          </div>
          <div class="stats-row">
            <span class="stats-label">本次消耗</span>
            <span class="stats-value stats-value-primary">
              {{ formatCollectMoney(props.cost) }}
            </span>
          </div>
          <div class="stats-row">
            <span class="stats-label">剩余余额</span>
            <span class="stats-value stats-value-balance">
              {{ formatCollectMoney(props.remainMoney) }}
            </span>
          </div>
        </template>

        <template v-else-if="isUpdateAccountLayout">
          <div class="stats-row">
            <span class="stats-label">新增账号</span>
            <span class="stats-value stats-value-primary">
              {{ formatCollectCount(props.newAccounts, '个') }}
            </span>
          </div>
          <div class="stats-row">
            <span class="stats-label">更新账号数据</span>
            <span class="stats-value stats-value-primary">
              {{ formatCollectCount(props.updatedAccounts, '条') }}
            </span>
          </div>
          <div class="stats-row">
            <span class="stats-label">本次消耗</span>
            <span class="stats-value stats-value-primary">
              {{ formatCollectMoney(props.cost) }}
            </span>
          </div>
          <div class="stats-row">
            <span class="stats-label">剩余余额</span>
            <span class="stats-value">
              {{ formatCollectMoney(props.remainMoney) }}
            </span>
          </div>
        </template>

        <template v-else-if="isUpdateWorksLayout">
          <div class="stats-row">
            <span class="stats-label">更新作品数</span>
            <span class="stats-value stats-value-primary">
              {{ formatCollectCount(props.updatedWorks, '条') }}
            </span>
          </div>
          <div class="stats-row">
            <span class="stats-label">本次消耗</span>
            <span class="stats-value stats-value-primary">
              {{ formatCollectMoney(props.cost) }}
            </span>
          </div>
          <div class="stats-row">
            <span class="stats-label">剩余余额</span>
            <span class="stats-value">
              {{ formatCollectMoney(props.remainMoney) }}
            </span>
          </div>
        </template>

        <template v-else>
          <div class="stats-row">
            <span class="stats-label">成功账号</span>
            <span class="stats-value">{{ formatCollectCount(props.successAccounts, '个') }}</span>
          </div>
          <div class="stats-row">
            <span class="stats-label">采集作品数</span>
            <span class="stats-value">{{ formatCollectCount(props.workCount, '条') }}</span>
          </div>
          <div class="stats-row">
            <span class="stats-label">本次消耗</span>
            <span class="stats-value">{{ formatCollectMoney(props.cost) }}</span>
          </div>
          <div class="stats-row">
            <span class="stats-label">剩余余额</span>
            <span class="stats-value">{{ formatCollectMoney(props.remainMoney) }}</span>
          </div>
        </template>
      </div>
    </template>

    <template v-else>
      <div class="dialog-title legacy-title">
        <el-icon v-if="props.resultType === 'success'" style="color: #2563eb;">
          <SuccessFilled />
        </el-icon>
        <el-icon v-else-if="props.resultType === 'warning'" style="color: orange;">
          <WarningFilled />
        </el-icon>
        <el-icon v-else-if="props.resultType === 'error'" style="color: red;">
          <CircleCheckFilled />
        </el-icon>
        <el-icon v-else style="color: gray;">
          <InfoFilled />
        </el-icon>
        <div>{{ props.title }}</div>
      </div>
      <div class="dialog-content">
        {{ props.displayInfo }}
      </div>
    </template>

    <template #footer>
      <span class="dialog-footer">
        <el-button class="close-btn" @click="dialogVisible = false">关闭</el-button>
        <el-button
          v-if="props.showStatsLayout"
          @click="handleJump"
          class="jump-btn"
          :disabled="!props.resultTableId"
        >
          查看采集
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { bitable } from '@lark-base-open/js-sdk'
import { SuccessFilled, WarningFilled, CircleCheckFilled, InfoFilled } from '@element-plus/icons-vue'
import { formatCollectCount, formatCollectMoney } from '@/utils/errorMessage'

const emit = defineEmits(['update:visible'])
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  resultTableId: {
    type: String,
    default: ''
  },
  displayInfo: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    default: '提示'
  },
  resultType: {
    type: String,
    default: 'success'
  },
  showStatsLayout: {
    type: Boolean,
    default: false
  },
  statsLayoutType: {
    type: String,
    default: 'collect'
  },
  newAccounts: {
    type: Number,
    default: null
  },
  updatedWorks: {
    type: Number,
    default: null
  },
  updatedAccounts: {
    type: Number,
    default: null
  },
  successAccounts: {
    type: Number,
    default: null
  },
  workCount: {
    type: Number,
    default: null
  },
  cost: {
    type: Number,
    default: null
  },
  remainMoney: {
    type: Number,
    default: null
  }
})

const dialogVisible = ref(props.visible)
const isAddAccountLayout = computed(() => props.statsLayoutType === 'addAccount')
const isUpdateAccountLayout = computed(() => props.statsLayoutType === 'updateAccount')
const isUpdateWorksLayout = computed(() => props.statsLayoutType === 'updateWorks')

const handleJump = async () => {
  if (!props.resultTableId) {
    return
  }
  await bitable.ui.switchToTable(props.resultTableId)
  dialogVisible.value = false
}

watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
})

watch(dialogVisible, (newVal) => {
  emit('update:visible', newVal)
})
</script>

<style scoped>
.collect-success-dialog :deep(.el-dialog) {
  border-radius: 8px;
  overflow: hidden;
}

.collect-success-dialog :deep(.el-dialog__header) {
  padding: 0;
  margin: 0;
}

.collect-success-dialog :deep(.el-dialog__headerbtn) {
  top: 32px;
  right: 32px;
}

.collect-success-dialog :deep(.el-dialog__body) {
  padding: 32px 32px 0;
}

.collect-success-dialog :deep(.el-dialog__footer) {
  padding: 0 32px 32px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.dialog-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.success-icon-img {
  width: 24px;
  height: 24px;
  object-fit: contain;
  flex-shrink: 0;
}

.title-text {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.stats-panel {
  margin: 25px 0 32px;
  background-color: #f5f6f7;
  border-radius: 6px;
  padding: 4px 16px;
}

.stats-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  font-size: 14px;
  color: #374151;
}

.stats-label {
  color: #0F1114
}

.stats-value {
  color: #1f2937;
  font-weight: 500;
}

.stats-value-primary {
  color: #021446;
}

.stats-value-balance {
  color: #F54A45;
}

.close-btn {
  border-radius: 8px;
  border-color: #d1d5db;
  color: #374151;
  background-color: #ffffff;
}

.close-btn:hover {
  border-color: #9ca3af;
  color: #1f2937;
  background-color: #ffffff;
}

.jump-btn {
  border-radius: 8px;
  background-color: #0e1e3d !important;
  border-color: #0e1e3d !important;
  color: #ffffff !important;
}

.jump-btn:hover {
  background-color: #1a2f58 !important;
  border-color: #1a2f58 !important;
}

.jump-btn:active {
  transform: scale(0.97);
}

.legacy-title {
  font-size: 18px;
  font-weight: bold;
  color: #1890ff;
}

.dialog-content {
  font-size: 14px;
  margin: 25px 0 32px;
}
</style>
