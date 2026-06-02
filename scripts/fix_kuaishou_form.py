#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Kuaishou form style
"""

import sys
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def refactor_kuaishou_form():
    """Refactor Kuaishou form"""
    filepath = r"d:\project\FeishuPlugin\src\paneForms\ksForm.vue"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    template_start = content.find('<template>')
    template_end = content.find('</template>') + len('</template>')
    
    if template_start == -1 or template_end == -1:
        print("Error: Cannot find template tags")
        return False
    
    script_part = content[:template_start]
    style_part = content[template_end:]
    
    new_template = '''<template>
  <div class="collect-panel">
    <div class="section-title">采集内容</div>
    <div class="collect-sub-panel">
      <div class="section-block">
        <div class="toggle-wrapper">
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 0 }" @click="paneData.getDataType = 0">获取账号数据</el-button>
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 1 }" @click="paneData.getDataType = 1">获取视频数据</el-button>
        </div>
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0">
        <div class="field-label">快手视频表</div>
        <TableSelect v-model="paneData.workTableId" placeholder="未选自动创建" />
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0">
        <div class="toggle-wrapper">
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.getWorksType === 1 }" @click="paneData.getWorksType = 1">根据账号id获取</el-button>
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.getWorksType === 0 }" @click="paneData.getWorksType = 0">根据账号表获取</el-button>
        </div>
      </div>

      <div class="section-block" v-show="paneData.getDataType === 0 || paneData.getWorksType === 0">
        <div class="field-label">快手账号表</div>
        <TableSelect v-model="paneData.userTableId" :placeholder="paneData.getDataType === 0 ? '未选自动创建' : '请选择快手账号表'" />
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0 && paneData.getWorksType !== 0">
        <div class="field-label">快手账号id</div>
        <el-input v-model="paneData.user_id" placeholder="请输入快手账号id" />
      </div>

      <div class="section-block" v-show="paneData.getDataType === 0">
        <div class="field-label">账号分享链接</div>
        <el-input v-model="paneData.shareLink" placeholder="请输入快手账号分享链接" />
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
          写入快手账号数据
        </el-button>
      </div>

      <div class="collect-btn-item" v-show="paneData.getDataType === 0">
        <el-button class="update-btn" :disabled="isLocked || !formData.key || !paneData.userTableId" @click="batchUpdateUser">
          批量更新快手账号数据
        </el-button>
      </div>

      <div class="collect-btn-item" v-show="paneData.getDataType !== 0">
        <el-button class="collect-btn" :disabled="isLocked || !formData.key || (!paneData.userTableId && paneData.getWorksType === 0) || (!paneData.user_id && paneData.getWorksType !== 0)" @click="getRecentWorks(paneData.searchRange, paneData.getWorksType)">
          {{ '获取' + paneData.searchRange + '发布视频'}}
        </el-button>
      </div>

      <div class="collect-btn-item" v-show="paneData.getDataType !== 0">
        <el-button class="update-btn" :disabled="isLocked || !formData.key || !paneData.workTableId" @click="updateWorks">
          批量更新快手视频数据
        </el-button>
      </div>
    </div>
  </div>
</template>
'''
    
    new_content = script_part + new_template + style_part
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Kuaishou form refactored successfully!")
    return True

if __name__ == '__main__':
    refactor_kuaishou_form()
