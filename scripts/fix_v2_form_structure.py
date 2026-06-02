#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix V2 (Shipinhao) form to match Douyin structure
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def refactor_v2_form():
    """Refactor V2 form to match Douyin structure"""
    filepath = r"d:\project\FeishuPlugin\src\paneForms\v2Form.vue"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    template_start = content.find('<template>')
    template_end = content.find('</template>') + len('</template>')
    
    if template_start == -1 or template_end == -1:
        print("Error: Cannot find template tags")
        return False
    
    script_part = content[:template_start]
    style_part = content[template_end:]
    
    # 新的模板内容（与抖音结构完全一致）
    new_template = '''<template>
  <div class="collect-panel">
    <div class="section-title">采集内容</div>
    <div class="collect-sub-panel">
      <div class="section-block">
        <div class="toggle-wrapper">
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 0 }" @click="paneData.getDataType = 0">采集博主数据</el-button>
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 1 }" @click="paneData.getDataType = 1">采集作品数据</el-button>
        </div>
      </div>

      <div class="section-block" v-if="paneData.getDataType === 1">
        <div class="field-label">作品数据范围</div>
        <el-select v-model="paneData.searchRange" class="custom-select" placeholder="请选择数据范围">
          <el-option v-for="item in Object.keys(ranges)" :key="item" :label="item" :value="item" />
        </el-select>
      </div>

      <div class="section-block">
        <div class="field-label">采集到表格</div>
        <TableSelect v-model="paneData.userTableId" placeholder="默认新建表格" />
      </div>
    </div>

    <div class="section-title">采集账号</div>
    <div class="collect-sub-panel">
      <div class="section-block">
        <div class="field-label">视频号关键词</div>
        <el-input v-model="paneData.keywords" placeholder="请输入视频号关键词搜索" />
      </div>
    </div>

    <div class="collect-btn-container">
      <div class="collect-btn-item">
        <el-button class="collect-btn" :disabled="isLocked || !formData.key || (paneData.getDataType === 0 && !paneData.keywords)" @click="paneData.getDataType === 0 ? upsertUser() : getRecentWorks(paneData.searchRange, paneData.getWorksType)">
          {{ paneData.getDataType === 0 ? '搜索视频号' : '获取' + paneData.searchRange + '视频' }}
        </el-button>
      </div>

      <div class="collect-btn-item" v-if="paneData.getDataType === 1">
        <el-button class="update-btn" :disabled="isLocked || !formData.key || !paneData.workTableId" @click="updateWorks()">
          批量更新作品数据
        </el-button>
      </div>
    </div>
  </div>
</template>
'''
    
    new_content = script_part + new_template + style_part
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("V2 (Shipinhao) form refactored successfully!")
    print("Now matches Douyin structure with separate content and account sections!")
    return True

if __name__ == '__main__':
    refactor_v2_form()
