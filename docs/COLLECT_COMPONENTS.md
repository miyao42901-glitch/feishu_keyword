# 可复用组件使用文档

## 组件列表

### 1. FieldLabel - 字段标签组件

用于显示表单字段的标签文字。

**Props:**
- `label` (String, required) - 标签文字

**使用示例:**

```vue
<FieldLabel label="采集到表格" />
```

---

### 2. SectionTitle - 区域标题组件

用于显示区域标题，支持帮助图标。

**Props:**
- `title` (String, required) - 标题文字
- `showHelp` (Boolean, default: false) - 是否显示帮助图标

**Events:**
- `help-click` - 点击帮助图标时触发

**使用示例:**

```vue
<SectionTitle 
  title="采集账号" 
  :showHelp="true" 
  @help-click="openTip" 
/>
```

---

### 3. CollectSection - 内容区域组件

用于包裹表单内容区域，提供统一的灰色背景。

**Props:**
- `title` (String, optional) - 区域标题

**Slots:**
- `default` - 内容插槽

**使用示例:**

```vue
<CollectSection title="作品数据范围">
  <el-select v-model="searchRange">
    <el-option label="1页" value="1" />
  </el-select>
</CollectSection>
```

---

### 4. ToggleButtons - 切换按钮组组件

用于显示切换按钮组，支持单选。

**Props:**
- `modelValue` (String|Number, required) - 当前选中的值
- `options` (Array, required) - 选项数组，每项包含 `value` 和 `label`

**Events:**
- `update:modelValue` - 选中值变化时触发

**使用示例:**

```vue
<ToggleButtons
  v-model="collectionType"
  :options="[
    { value: 'blogger', label: '采集博主数据' },
    { value: 'post', label: '采集作品数据' }
  ]"
/>
```

---

### 5. CollectButton - 操作按钮组件

用于显示主要/次要操作按钮。

**Props:**
- `type` (String, default: 'primary') - 按钮类型，可选 'primary' 或 'secondary'
- `disabled` (Boolean, default: false) - 是否禁用
- `loading` (Boolean, default: false) - 是否显示加载状态
- `text` (String, optional) - 按钮文字

**Events:**
- `click` - 点击按钮时触发

**Slots:**
- `default` - 按钮内容插槽

**使用示例:**

```vue
<!-- 使用 text prop -->
<CollectButton
  type="primary"
  text="采集数据"
  :disabled="isLocked"
  @click="handleCollect"
/>

<!-- 使用插槽 -->
<CollectButton
  type="secondary"
  :disabled="isLocked"
  @click="handleUpdate"
>
  批量更新作品数据
</CollectButton>
```

---

## 完整使用示例

```vue
<template>
  <div class="collect-panel">
    <!-- 采集内容区域 -->
    <SectionTitle title="采集内容" />
    <CollectSection>
      <div class="section-block">
        <ToggleButtons
          v-model="collectionType"
          :options="[
            { value: 'blogger', label: '采集博主数据' },
            { value: 'post', label: '采集作品数据' }
          ]"
        />
      </div>

      <div class="section-block" v-if="collectionType === 'post'">
        <FieldLabel label="作品数据范围" />
        <el-select v-model="searchRange" class="custom-select">
          <el-option label="1页" value="1" />
          <el-option label="2页" value="2" />
        </el-select>
      </div>

      <div class="section-block">
        <FieldLabel label="采集到表格" />
        <TableSelect v-model="selectedTableId" placeholder="默认新建表格" />
      </div>
    </CollectSection>

    <!-- 采集账号区域 -->
    <SectionTitle 
      title="采集账号" 
      :showHelp="true" 
      @help-click="openTip" 
    />
    <CollectSection>
      <div class="section-block">
        <!-- 账号输入内容 -->
      </div>
    </CollectSection>

    <!-- 按钮区域 -->
    <div class="collect-btn-container">
      <CollectButton
        type="primary"
        text="采集数据"
        :disabled="isLocked"
        @click="handleCollect"
      />
      <CollectButton
        v-if="showUpdateButton"
        type="secondary"
        text="批量更新作品数据"
        :disabled="isLocked"
        @click="handleUpdate"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { 
  SectionTitle, 
  CollectSection, 
  FieldLabel, 
  ToggleButtons, 
  CollectButton 
} from '@/components/collect'
import TableSelect from '@/components/TableSelect.vue'

const collectionType = ref('blogger')
const searchRange = ref('1')
const selectedTableId = ref(null)
const isLocked = ref(false)
const showUpdateButton = ref(true)

const openTip = () => {
  console.log('打开帮助提示')
}

const handleCollect = () => {
  console.log('开始采集')
}

const handleUpdate = () => {
  console.log('开始更新')
}
</script>
```

---

## 样式说明

所有组件都使用 `form-styles.css` 中定义的全局样式类，不需要在组件中添加自定义样式。

主要样式类：
- `.collect-panel` - 最外层容器
- `.collect-sub-panel` - 内容区域容器
- `.section-block` - 内容区块
- `.section-title` - 区域标题
- `.field-label` - 字段标签
- `.toggle-wrapper` - 切换按钮容器
- `.toggle-btn` - 切换按钮
- `.collect-btn` - 主要操作按钮
- `.update-btn` - 次要操作按钮
- `.collect-btn-container` - 按钮容器
- `.collect-btn-item` - 单个按钮项

---

## 注意事项

1. 所有组件都已经包含必要的样式类，不需要额外添加样式
2. 切换按钮组件会自动处理激活状态的样式
3. 操作按钮组件会自动应用正确的样式类
4. 使用 `v-model` 绑定切换按钮组的值
5. 使用 `@click` 监听按钮点击事件
6. 所有组件都支持 Props 验证，传入错误的参数会在控制台显示警告
