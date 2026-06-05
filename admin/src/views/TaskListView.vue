<template>
  <div class="task-list-page">
    <div class="task-header">
      <el-input v-model="searchQuery" placeholder="按任务ID/用户/采集类型搜索" style="width: 300px" clearable />
      <el-button-group>
        <el-button :type="range === 'day' ? 'primary' : ''" @click="range = 'day'">今日</el-button>
        <el-button :type="range === 'week' ? 'primary' : ''" @click="range = 'week'">本周</el-button>
        <el-button :type="range === 'month' ? 'primary' : ''" @click="range = 'month'">本月</el-button>
      </el-button-group>
    </div>

    <el-card shadow="never" class="table-card">
      <div class="filter-tags">
        <span class="filter-label">视图任务：</span>
        <span class="filter-value">用户名/平台/采集类型</span>
      </div>

      <el-table :data="filteredTasks" stripe style="width: 100%">
        <el-table-column prop="taskId" label="任务ID" width="120" />
        <el-table-column prop="userName" label="用户名" width="140">
          <template #default="{ row }">
            <el-link type="primary">{{ row.userName }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="platform" label="采集平台" width="120" />
        <el-table-column prop="taskType" label="采集类型" width="140" />
        <el-table-column prop="collectCount" label="采集条数" width="100" align="right" />
        <el-table-column prop="pointsCost" label="消耗金额" width="100" align="right" />
        <el-table-column prop="startTime" label="开始时间" width="180" />
        <el-table-column prop="endTime" label="结束时间" width="180" />
        <el-table-column prop="duration" label="耗时" width="90" />
        <el-table-column label="结果" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === '成功' ? 'success' : 'danger'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="totalTasks"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, prev, pager, next, sizes"
          background
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const range = ref('month')
const searchQuery = ref('')
const currentPage = ref(6)
const pageSize = ref(10)

const MOCK_TASKS = [
  { taskId: 'ihuhfuh32', userName: '17812345678', platform: '抖音', taskType: '采集账号数据', collectCount: 867, pointsCost: 318.98, startTime: '2026-06-06 08:28:36', endTime: '2026-06-06 08:28:36', duration: '4m 23s', status: '成功' },
  { taskId: 'ihuhfuh32', userName: '17812345678', platform: '视频号', taskType: '更新视频数据', collectCount: 398, pointsCost: '-', startTime: '2026-06-06 08:28:36', endTime: '2026-06-06 08:28:36', duration: '4m 23s', status: '失败' },
  { taskId: 'ihuhfuh32', userName: '17812345678', platform: '视频号', taskType: '采集视频数据', collectCount: 398, pointsCost: 318.98, startTime: '2026-06-06 08:28:36', endTime: '2026-06-06 08:28:36', duration: '4m 23s', status: '成功' },
  { taskId: 'ihuhfuh32', userName: '17812345678', platform: '视频号', taskType: '更新账号数据', collectCount: 398, pointsCost: 318.98, startTime: '2026-06-06 08:28:36', endTime: '2026-06-06 08:28:36', duration: '4m 23s', status: '成功' },
  { taskId: 'ihuhfuh32', userName: '17812345678', platform: '视频号', taskType: '采集视频数据', collectCount: 398, pointsCost: 318.98, startTime: '2026-06-06 08:28:36', endTime: '2026-06-06 08:28:36', duration: '4m 23s', status: '成功' },
  { taskId: 'ihuhfuh32', userName: '17812345678', platform: '视频号', taskType: '采集视频数据', collectCount: 398, pointsCost: 318.98, startTime: '2026-06-06 08:28:36', endTime: '2026-06-06 08:28:36', duration: '4m 23s', status: '成功' },
  { taskId: 'ihuhfuh32', userName: '17812345678', platform: '视频号', taskType: '采集视频数据', collectCount: 398, pointsCost: 318.98, startTime: '2026-06-06 08:28:36', endTime: '2026-06-06 08:28:36', duration: '4m 23s', status: '成功' },
  { taskId: 'ihuhfuh32', userName: '17812345678', platform: '视频号', taskType: '采集视频数据', collectCount: 398, pointsCost: 318.98, startTime: '2026-06-06 08:28:36', endTime: '2026-06-06 08:28:36', duration: '4m 23s', status: '成功' },
]

const totalTasks = ref(100)

const filteredTasks = computed(() => {
  if (!searchQuery.value) return MOCK_TASKS
  const q = searchQuery.value.toLowerCase()
  return MOCK_TASKS.filter(
    (t) =>
      t.taskId.toLowerCase().includes(q) ||
      t.userName.includes(q) ||
      t.taskType.includes(q)
  )
})
</script>

<style scoped>
.task-list-page { padding: 0; }

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.table-card { padding: 0; }

.filter-tags {
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #e5e7eb;
  font-size: 13px;
}

.filter-label { color: #6b7280; margin-right: 8px; }
.filter-value { color: #111827; }

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: 16px;
  background: #fafafa;
  border-top: 1px solid #e5e7eb;
}
</style>
