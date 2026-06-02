#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix all remaining forms style
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def refactor_form(filepath, platform_name, template_content):
    """Refactor a form file"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    template_start = content.find('<template>')
    template_end = content.find('</template>') + len('</template>')
    
    if template_start == -1 or template_end == -1:
        print(f"Error: Cannot find template tags in {platform_name}")
        return False
    
    script_part = content[:template_start]
    style_part = content[template_end:]
    
    new_content = script_part + template_content + style_part
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"{platform_name} form refactored successfully!")
    return True

# 公众号表单模板
gh_template = '''<template>
  <div class="collect-panel">
    <div class="section-title">采集内容</div>
    <div class="collect-sub-panel">
      <div class="section-block">
        <div class="toggle-wrapper">
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 0 }" @click="paneData.getDataType = 0">获取公众号数据</el-button>
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 1 }" @click="paneData.getDataType = 1">获取文章数据</el-button>
        </div>
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0">
        <div class="field-label">公众号文章表</div>
        <TableSelect v-model="paneData.workTableId" placeholder="未选自动创建" />
      </div>

      <div class="section-block" v-show="paneData.getDataType === 0 || paneData.getWorksType === 0">
        <div class="field-label">公众号表</div>
        <TableSelect v-model="paneData.userTableId" :placeholder="paneData.getDataType === 0 ? '未选自动创建' : '请选择公众号表'" />
      </div>

      <div class="section-block" v-show="paneData.getDataType === 0">
        <div class="field-label">公众号链接</div>
        <el-input v-model="paneData.shareLink" placeholder="请输入公众号文章链接" />
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0">
        <div class="field-label">数据范围</div>
        <el-select v-model="paneData.searchRange" class="custom-select" placeholder="请选择数据范围">
          <el-option v-for="item in Object.keys(ranges)" :key="item" :label="item" :value="item" />
        </el-select>
      </div>
    </div>

    <div class="collect-btn-container">
      <div class="collect-btn-item" v-show="paneData.getDataType === 0">
        <el-button class="collect-btn" :disabled="isLocked || !formData.key || !paneData.shareLink" @click="upsertUser">
          写入公众号数据
        </el-button>
      </div>

      <div class="collect-btn-item" v-show="paneData.getDataType === 0">
        <el-button class="update-btn" :disabled="isLocked || !formData.key || !paneData.userTableId" @click="batchUpdateUser">
          批量更新公众号数据
        </el-button>
      </div>

      <div class="collect-btn-item" v-show="paneData.getDataType !== 0">
        <el-button class="collect-btn" :disabled="isLocked || !formData.key || !paneData.userTableId" @click="getRecentWorks(paneData.searchRange)">
          {{ '获取' + paneData.searchRange + '文章'}}
        </el-button>
      </div>

      <div class="collect-btn-item" v-show="paneData.getDataType !== 0">
        <el-button class="update-btn" :disabled="isLocked || !formData.key || !paneData.workTableId" @click="updateWorks">
          批量更新文章数据
        </el-button>
      </div>
    </div>
  </div>
</template>
'''

# 视频号表单模板
v2_template = '''<template>
  <div class="collect-panel">
    <div class="section-title">采集内容</div>
    <div class="collect-sub-panel">
      <div class="section-block">
        <div class="toggle-wrapper">
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 0 }" @click="paneData.getDataType = 0">获取视频号数据</el-button>
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 1 }" @click="paneData.getDataType = 1">获取视频数据</el-button>
        </div>
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0">
        <div class="field-label">视频号视频表</div>
        <TableSelect v-model="paneData.workTableId" placeholder="未选自动创建" />
      </div>

      <div class="section-block" v-show="paneData.getDataType === 0 || paneData.getWorksType === 0">
        <div class="field-label">视频号表</div>
        <TableSelect v-model="paneData.userTableId" :placeholder="paneData.getDataType === 0 ? '未选自动创建' : '请选择视频号表'" />
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0 && paneData.getWorksType !== 0">
        <div class="field-label">视频号id</div>
        <el-input v-model="paneData.username" placeholder="请输入视频号id" />
      </div>

      <div class="section-block" v-show="paneData.getDataType === 0">
        <div class="field-label">视频号关键词</div>
        <el-input v-model="paneData.keywords" placeholder="请输入视频号关键词" />
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0">
        <div class="field-label">数据范围</div>
        <el-select v-model="paneData.searchRange" class="custom-select" placeholder="请选择数据范围">
          <el-option v-for="item in Object.keys(ranges)" :key="item" :label="item" :value="item" />
        </el-select>
      </div>
    </div>

    <div class="collect-btn-container">
      <div class="collect-btn-item" v-show="paneData.getDataType === 0">
        <el-button class="collect-btn" :disabled="isLocked || !formData.key || !paneData.keywords" @click="upsertUser">
          搜索视频号
        </el-button>
      </div>

      <div class="collect-btn-item" v-show="paneData.getDataType === 0">
        <el-button class="update-btn" :disabled="isLocked || !formData.key || !paneData.userTableId" @click="batchUpdateUser">
          批量更新视频号数据
        </el-button>
      </div>

      <div class="collect-btn-item" v-show="paneData.getDataType !== 0">
        <el-button class="collect-btn" :disabled="isLocked || !formData.key || (!paneData.userTableId && paneData.getWorksType === 0) || (!paneData.username && paneData.getWorksType !== 0)" @click="getRecentWorks(paneData.searchRange, paneData.getWorksType)">
          {{ '获取' + paneData.searchRange + '视频'}}
        </el-button>
      </div>

      <div class="collect-btn-item" v-show="paneData.getDataType !== 0">
        <el-button class="update-btn" :disabled="isLocked || !formData.key || !paneData.workTableId" @click="updateWorks">
          批量更新视频数据
        </el-button>
      </div>
    </div>
  </div>
</template>
'''

# 小红书表单模板
xhs_template = '''<template>
  <div class="collect-panel">
    <div class="section-title">采集内容</div>
    <div class="collect-sub-panel">
      <div class="section-block">
        <div class="toggle-wrapper">
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 0 }" @click="paneData.getDataType = 0">获取博主数据</el-button>
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 1 }" @click="paneData.getDataType = 1">获取笔记数据</el-button>
        </div>
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0">
        <div class="field-label">小红书笔记表</div>
        <TableSelect v-model="paneData.workTableId" placeholder="未选自动创建" />
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0">
        <div class="toggle-wrapper">
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.getWorksType === 1 }" @click="paneData.getWorksType = 1">根据博主id获取</el-button>
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.getWorksType === 0 }" @click="paneData.getWorksType = 0">根据博主表获取</el-button>
        </div>
      </div>

      <div class="section-block" v-show="paneData.getDataType === 0 || paneData.getWorksType === 0">
        <div class="field-label">小红书博主表</div>
        <TableSelect v-model="paneData.userTableId" :placeholder="paneData.getDataType === 0 ? '未选自动创建' : '请选择博主表'" />
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0 && paneData.getWorksType !== 0">
        <div class="field-label">小红书博主id</div>
        <el-input v-model="paneData.user_id" placeholder="请输入小红书博主id" />
      </div>

      <div class="section-block" v-show="paneData.getDataType === 0">
        <div class="field-label">博主主页链接</div>
        <el-input v-model="paneData.shareLink" placeholder="请输入小红书博主主页链接" />
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0">
        <div class="field-label">数据范围</div>
        <el-select v-model="paneData.searchRange" class="custom-select" placeholder="请选择数据范围">
          <el-option v-for="item in Object.keys(ranges)" :key="item" :label="item" :value="item" />
        </el-select>
      </div>
    </div>

    <div class="collect-btn-container">
      <div class="collect-btn-item" v-show="paneData.getDataType === 0">
        <el-button class="collect-btn" :disabled="isLocked || !formData.key || !paneData.shareLink" @click="upsertUser">
          写入博主数据
        </el-button>
      </div>

      <div class="collect-btn-item" v-show="paneData.getDataType === 0">
        <el-button class="update-btn" :disabled="isLocked || !formData.key || !paneData.userTableId" @click="batchUpdateUser">
          批量更新博主数据
        </el-button>
      </div>

      <div class="collect-btn-item" v-show="paneData.getDataType !== 0">
        <el-button class="collect-btn" :disabled="isLocked || !formData.key || (!paneData.userTableId && paneData.getWorksType === 0) || (!paneData.user_id && paneData.getWorksType !== 0)" @click="getRecentWorks(paneData.searchRange, paneData.getWorksType)">
          {{ '获取' + paneData.searchRange + '笔记'}}
        </el-button>
      </div>

      <div class="collect-btn-item" v-show="paneData.getDataType !== 0">
        <el-button class="update-btn" :disabled="isLocked || !formData.key || !paneData.workTableId" @click="updateWorks">
          批量更新笔记数据
        </el-button>
      </div>
    </div>
  </div>
</template>
'''

if __name__ == '__main__':
    base_dir = r"d:\project\FeishuPlugin\src\paneForms"
    
    forms = [
        (f"{base_dir}\\ghForm.vue", "Gongzhonghao", gh_template),
        (f"{base_dir}\\v2Form.vue", "Shipinhao", v2_template),
        (f"{base_dir}\\xhsForm.vue", "Xiaohongshu", xhs_template),
    ]
    
    for filepath, platform_name, template in forms:
        refactor_form(filepath, platform_name, template)
    
    print("\nAll forms refactored successfully!")
    print("All platforms now have consistent styles with Douyin and Kuaishou!")
