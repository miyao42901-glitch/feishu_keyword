# 快手表单重构示例

## 重构前后对比

### 旧的模板结构（使用 el-form）

```vue
<template>
  <el-form class="ghForm" label-position="left" label-width="auto">  
    <el-form-item label-width="null">
      <el-radio-group v-model="paneData.getDataType">
        <el-radio :label="0">获取账号数据</el-radio>
        <el-radio :label="1">获取视频数据</el-radio>
      </el-radio-group>
    </el-form-item>

    <el-form-item :label="'快手视频表'" v-show="paneData.getDataType !== 0">
      <TableSelect v-model="paneData.workTableId" :placeholder="'未选自动创建'" />
    </el-form-item>

    <el-form-item label-width="null" v-show="paneData.getDataType === 0">
      <el-button 
        type="primary" 
        :disabled="isLocked"
        @click="upsertUser"
        plain
      >
        写入快手账号数据
      </el-button>
    </el-form-item>
  </el-form>
</template>
```

### 新的模板结构（使用可复用组件）

```vue
<template>
  <div class="collect-panel">
    <!-- 采集内容区域 -->
    <SectionTitle title="采集内容" />
    <CollectSection>
      <div class="section-block">
        <ToggleButtons
          v-model="paneData.getDataType"
          :options="[
            { value: 0, label: '获取账号数据' },
            { value: 1, label: '获取视频数据' }
          ]"
        />
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0">
        <FieldLabel label="快手视频表" />
        <TableSelect v-model="paneData.workTableId" placeholder="未选自动创建" />
      </div>
    </CollectSection>

    <!-- 按钮区域 -->
    <div class="collect-btn-container">
      <CollectButton
        v-show="paneData.getDataType === 0"
        type="primary"
        text="写入快手账号数据"
        :disabled="isLocked"
        @click="upsertUser"
      />
    </div>
  </div>
</template>

<script setup>
import { 
  SectionTitle, 
  CollectSection, 
  FieldLabel, 
  ToggleButtons, 
  CollectButton 
} from '@/components/collect'
import TableSelect from '@/components/TableSelect.vue'
</script>
```

## 重构要点

### 1. 整体结构变化

**旧结构：**
- 使用 `<el-form>` 作为容器
- 使用 `<el-form-item>` 包裹每个字段
- 使用 `<el-radio-group>` 作为切换按钮

**新结构：**
- 使用 `<div class="collect-panel">` 作为容器
- 使用 `<CollectSection>` 包裹内容区域
- 使用 `<ToggleButtons>` 作为切换按钮
- 使用 `<CollectButton>` 作为操作按钮

### 2. 组件导入变化

**旧导入：**
```javascript
import {
  ElForm,
  ElFormItem,
  ElRadioGroup,
  ElRadio,
  ElButton,
} from 'element-plus';

export default {
  components: {
    ElForm,
    ElFormItem,
    ElRadioGroup,
    ElRadio,
    ElButton,
  },
  // ...
}
```

**新导入：**
```javascript
import { 
  SectionTitle, 
  CollectSection, 
  FieldLabel, 
  ToggleButtons, 
  CollectButton 
} from '@/components/collect'
```

### 3. 切换按钮重构

**旧代码：**
```vue
<el-radio-group v-model="paneData.getDataType">
  <el-radio :label="0">获取账号数据</el-radio>
  <el-radio :label="1">获取视频数据</el-radio>
</el-radio-group>
```

**新代码：**
```vue
<ToggleButtons
  v-model="paneData.getDataType"
  :options="[
    { value: 0, label: '获取账号数据' },
    { value: 1, label: '获取视频数据' }
  ]"
/>
```

### 4. 操作按钮重构

**旧代码：**
```vue
<el-button 
  type="primary" 
  :disabled="isLocked"
  @click="upsertUser"
  plain
  style="flex: 1;"
>
  写入快手账号数据
</el-button>
```

**新代码：**
```vue
<CollectButton
  type="primary"
  text="写入快手账号数据"
  :disabled="isLocked"
  @click="upsertUser"
/>
```

### 5. 字段标签重构

**旧代码：**
```vue
<el-form-item :label="'快手视频表'">
  <TableSelect v-model="paneData.workTableId" />
</el-form-item>
```

**新代码：**
```vue
<div class="section-block">
  <FieldLabel label="快手视频表" />
  <TableSelect v-model="paneData.workTableId" />
</div>
```

## 完整的快手表单重构模板

由于完整代码太长，这里提供重构后的模板结构框架：

```vue
<template>
  <div class="collect-panel">
    <!-- 1. 采集内容区域 -->
    <SectionTitle title="采集内容" />
    <CollectSection>
      <!-- 切换按钮：获取账号数据 / 获取视频数据 -->
      <div class="section-block">
        <ToggleButtons v-model="paneData.getDataType" :options="dataTypeOptions" />
      </div>

      <!-- 条件显示：快手视频表 -->
      <div class="section-block" v-show="paneData.getDataType !== 0">
        <FieldLabel label="快手视频表" />
        <TableSelect v-model="paneData.workTableId" placeholder="未选自动创建" />
      </div>

      <!-- 条件显示：获取方式切换 -->
      <div class="section-block" v-show="paneData.getDataType !== 0">
        <ToggleButtons v-model="paneData.getWorksType" :options="worksTypeOptions" />
      </div>

      <!-- 条件显示：快手账号表 -->
      <div class="section-block" v-show="paneData.getDataType === 0 || paneData.getWorksType === 0">
        <FieldLabel label="快手账号表" />
        <TableSelect v-model="paneData.userTableId" :placeholder="tablePlaceholder" />
      </div>

      <!-- 条件显示：快手账号id -->
      <div class="section-block" v-show="paneData.getDataType !== 0 && paneData.getWorksType !== 0">
        <FieldLabel label="快手账号id" />
        <el-input v-model="paneData.user_id" placeholder="请输入快手账号id" />
      </div>

      <!-- 条件显示：账号分享链接 -->
      <div class="section-block" v-show="paneData.getDataType === 0">
        <FieldLabel label="账号分享链接" />
        <el-input v-model="paneData.shareLink" placeholder="请输入快手账号分享链接" />
      </div>

      <!-- 条件显示：数据范围 -->
      <div class="section-block" v-show="paneData.getDataType !== 0">
        <FieldLabel label="数据范围" />
        <el-select v-model="paneData.searchRange" class="custom-select" placeholder="请选择数据范围">
          <el-option v-for="item in Object.keys(ranges)" :key="item" :label="item" :value="item" />
        </el-select>
      </div>
    </CollectSection>

    <!-- 2. 按钮区域 -->
    <div class="collect-btn-container">
      <!-- 写入快手账号数据 -->
      <CollectButton
        v-show="paneData.getDataType === 0"
        type="primary"
        text="写入快手账号数据"
        :disabled="isLocked || !formData.key || !paneData.shareLink"
        @click="upsertUser"
      />

      <!-- 批量更新快手账号数据 -->
      <CollectButton
        v-show="paneData.getDataType === 0"
        type="secondary"
        text="批量更新快手账号数据"
        :disabled="isLocked || !formData.key || !paneData.userTableId"
        @click="batchUpdateUser"
      />

      <!-- 获取发布视频 -->
      <CollectButton
        v-show="paneData.getDataType !== 0"
        type="primary"
        :text="'获取' + paneData.searchRange + '发布视频'"
        :disabled="isLocked || !formData.key || (!paneData.userTableId && paneData.getWorksType === 0) || (!paneData.user_id && paneData.getWorksType !== 0)"
        @click="getRecentWorks(paneData.searchRange, paneData.getWorksType)"
      />

      <!-- 批量更新快手视频数据 -->
      <CollectButton
        v-show="paneData.getDataType !== 0"
        type="secondary"
        text="批量更新快手视频数据"
        :disabled="isLocked || !formData.key || !paneData.workTableId"
        @click="updateWorks"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { 
  SectionTitle, 
  CollectSection, 
  FieldLabel, 
  ToggleButtons, 
  CollectButton 
} from '@/components/collect'
import TableSelect from '@/components/TableSelect.vue'
import { ElInput, ElSelect, ElOption } from 'element-plus'

// 计算属性
const dataTypeOptions = [
  { value: 0, label: '获取账号数据' },
  { value: 1, label: '获取视频数据' }
]

const worksTypeOptions = [
  { value: 1, label: '根据账号id获取' },
  { value: 0, label: '根据账号表获取' }
]

const tablePlaceholder = computed(() => {
  return paneData.value.getDataType === 0 ? '未选自动创建' : '请选择快手账号表'
})
</script>
```

## 注意事项

1. **保留所有业务逻辑**：`<script>` 部分的所有函数和逻辑保持不变
2. **移除 el-form**：不再使用 `<el-form>` 和 `<el-form-item>`
3. **使用新组件**：使用 `ToggleButtons`、`CollectButton` 等新组件
4. **移除 scoped 样式**：使用全局样式类，不需要 `<style scoped>`
5. **保持功能一致**：所有条件显示、事件绑定保持不变

## 下一步

确认这个重构方案后，我会：
1. 应用到快手表单 `ksForm.vue`
2. 应用到公众号表单 `ghForm.vue`
3. 应用到视频号表单 `v2Form.vue`
4. 应用到小红书表单 `xhsForm.vue`
