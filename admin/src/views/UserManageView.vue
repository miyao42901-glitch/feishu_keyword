<template>
  <div class="user-manage-page">
    <div class="user-header">
      <el-button-group>
        <el-button :type="range === 'day' ? 'primary' : ''" @click="range = 'day'">今日</el-button>
        <el-button :type="range === 'week' ? 'primary' : ''" @click="range = 'week'">本周</el-button>
        <el-button :type="range === 'month' ? 'primary' : ''" @click="range = 'month'">本月</el-button>
      </el-button-group>
    </div>

    <div class="kpi-row">
      <el-card shadow="never" class="kpi-card">
        <div class="kpi-label">访问用户</div>
        <div class="kpi-value">{{ current.visitUsers }}</div>
        <div class="kpi-change up">{{ current.visitChange }}</div>
      </el-card>
      <el-card shadow="never" class="kpi-card">
        <div class="kpi-label">新注册用户</div>
        <div class="kpi-value">{{ current.newUsers }}</div>
        <div class="kpi-change up">{{ current.newChange }}</div>
      </el-card>
      <el-card shadow="never" class="kpi-card">
        <div class="kpi-label">有效用户</div>
        <div class="kpi-value">{{ current.activeUsers }}</div>
        <div class="kpi-change up">{{ current.activeChange }}</div>
      </el-card>
    </div>

    <el-card shadow="never" class="table-card">
      <div class="search-filter-row">
        <div class="search-box">
          <span class="filter-label">搜索用户：</span>
          <el-input v-model="searchQuery" placeholder="用户名/飞书ID" style="width: 200px" clearable />
        </div>
        <el-button-group size="small">
          <el-button :type="userType === 'all' ? 'primary' : ''" @click="userType = 'all'">全部</el-button>
          <el-button :type="userType === 'logged' ? 'primary' : ''" @click="userType = 'logged'">登录用户</el-button>
          <el-button :type="userType === 'unlogged' ? 'primary' : ''" @click="userType = 'unlogged'">未登录用户</el-button>
        </el-button-group>
      </div>

      <el-table :data="filteredUsers" stripe style="width: 100%">
        <el-table-column prop="userName" label="用户名" width="140">
          <template #default="{ row }">
            <el-link v-if="row.userName !== '-'" type="primary">{{ row.userName }}</el-link>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="feishuId" label="飞书ID" width="120" />
        <el-table-column prop="taskCount" label="采集次数（次）" width="140" align="right" sortable />
        <el-table-column prop="collectCount" label="采集条数（条）" width="140" align="right" sortable />
        <el-table-column prop="pointsCost" label="消耗金额（元）" width="140" align="right" sortable />
        <el-table-column prop="registerTime" label="最近活跃时间" width="180" sortable />
        <el-table-column prop="loginDays" label="注册天数（天）" width="140" align="right" sortable />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-link type="primary" @click="openDetail(row)">查看详情</el-link>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="totalUsers"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, prev, pager, next"
          background
        />
      </div>
    </el-card>

    <UserDetailDrawer v-model="showDetail" :user="selectedUser" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import UserDetailDrawer from './UserDetailDrawer.vue'

const range = ref('month')
const searchQuery = ref('')
const userType = ref('all')
const currentPage = ref(6)
const pageSize = ref(10)
const showDetail = ref(false)
const selectedUser = ref(null)

const KPI_DATA = {
  day: {
    visitUsers: '1,024',
    visitChange: '+58 较昨日',
    newUsers: '312',
    newChange: '+18 较昨日',
    activeUsers: '42',
    activeChange: '+5 较昨日',
  },
  week: {
    visitUsers: '2,140',
    visitChange: '+124 较上周',
    newUsers: '876',
    newChange: '+56 较上周',
    activeUsers: '89',
    activeChange: '+12 较上周',
  },
  month: {
    visitUsers: '3,528',
    visitChange: '+1123 较上月',
    newUsers: '1,528',
    newChange: '+113 较上月',
    activeUsers: '148',
    activeChange: '+23 较上月',
  },
}

const MOCK_USERS = [
  { userName: '-', feishuId: 'ihsfuufha', taskCount: 0, collectCount: 0, pointsCost: 0, registerTime: '2026-06-06 08:28:36', loginDays: 0 },
  { userName: '17812345678', feishuId: 'ihsfuufha', taskCount: 0, collectCount: 0, pointsCost: 0, registerTime: '2026-06-06 08:28:36', loginDays: 45 },
  { userName: '17812345678', feishuId: 'ihsfuufha', taskCount: 78, collectCount: 867, pointsCost: 318.98, registerTime: '2026-06-06 08:28:36', loginDays: 67 },
  { userName: '17812345678', feishuId: 'ihsfuufha', taskCount: 78, collectCount: 867, pointsCost: 318.98, registerTime: '2026-06-06 08:28:36', loginDays: 67 },
  { userName: '17812345678', feishuId: 'ihsfuufha', taskCount: 78, collectCount: 867, pointsCost: 318.98, registerTime: '2026-06-06 08:28:36', loginDays: 67 },
  { userName: '17812345678', feishuId: 'ihsfuufha', taskCount: 78, collectCount: 867, pointsCost: 318.98, registerTime: '2026-06-06 08:28:36', loginDays: 67 },
  { userName: '17812345678', feishuId: 'ihsfuufha', taskCount: 78, collectCount: 867, pointsCost: 318.98, registerTime: '2026-06-06 08:28:36', loginDays: 67 },
]

const totalUsers = ref(100)

const current = computed(() => KPI_DATA[range.value] ?? KPI_DATA.month)

const filteredUsers = computed(() => {
  let users = MOCK_USERS

  if (userType.value === 'logged') {
    users = users.filter((u) => u.userName !== '-')
  } else if (userType.value === 'unlogged') {
    users = users.filter((u) => u.userName === '-')
  }

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    users = users.filter(
      (u) =>
        u.userName.toLowerCase().includes(q) ||
        u.feishuId.toLowerCase().includes(q)
    )
  }

  return users
})

function openDetail(user) {
  selectedUser.value = user
  showDetail.value = true
}
</script>

<style scoped>
.user-manage-page { padding: 0; }

.user-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

@media (max-width: 900px) {
  .kpi-row { grid-template-columns: 1fr; }
}

.kpi-card { padding: 4px 0; }
.kpi-label { font-size: 13px; color: #6b7280; margin-bottom: 10px; }
.kpi-value { font-size: 36px; font-weight: 700; color: #111827; line-height: 1.1; margin-bottom: 8px; letter-spacing: -0.5px; }
.kpi-change { font-size: 12px; }
.kpi-change.up { color: #10b981; }

.table-card { padding: 0; }

.search-filter-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #fafafa;
  border-bottom: 1px solid #e5e7eb;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-label { font-size: 13px; color: #6b7280; }

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: 16px;
  background: #fafafa;
  border-top: 1px solid #e5e7eb;
}
</style>
