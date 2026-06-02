#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch fix all forms style
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

# 公众号表单模板（需要根据实际业务逻辑调整）
gh_template = '''<template>
  <div class="collect-panel">
    <div class="section-title">采集内容</div>
    <div class="collect-sub-panel">
      <div class="section-block">
        <div class="field-label">公众号表</div>
        <TableSelect v-model="paneData.userTableId" placeholder="未选自动创建" />
      </div>

      <div class="section-block">
        <div class="field-label">公众号链接</div>
        <el-input v-model="paneData.shareLink" placeholder="请输入公众号文章链接" />
      </div>
    </div>

    <div class="collect-btn-container">
      <div class="collect-btn-item">
        <el-button class="collect-btn" :disabled="isLocked || !formData.key || !paneData.shareLink" @click="upsertUser">
          采集公众号数据
        </el-button>
      </div>

      <div class="collect-btn-item">
        <el-button class="update-btn" :disabled="isLocked || !formData.key || !paneData.userTableId" @click="batchUpdateUser">
          批量更新数据
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
        <div class="field-label">视频号表</div>
        <TableSelect v-model="paneData.userTableId" placeholder="未选自动创建" />
      </div>

      <div class="section-block">
        <div class="field-label">视频号链接</div>
        <el-input v-model="paneData.shareLink" placeholder="请输入视频号链接" />
      </div>
    </div>

    <div class="collect-btn-container">
      <div class="collect-btn-item">
        <el-button class="collect-btn" :disabled="isLocked || !formData.key || !paneData.shareLink" @click="upsertUser">
          采集视频号数据
        </el-button>
      </div>

      <div class="collect-btn-item">
        <el-button class="update-btn" :disabled="isLocked || !formData.key || !paneData.userTableId" @click="batchUpdateUser">
          批量更新数据
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
        <div class="field-label">小红书表</div>
        <TableSelect v-model="paneData.userTableId" placeholder="未选自动创建" />
      </div>

      <div class="section-block">
        <div class="field-label">小红书链接</div>
        <el-input v-model="paneData.shareLink" placeholder="请输入小红书链接" />
      </div>
    </div>

    <div class="collect-btn-container">
      <div class="collect-btn-item">
        <el-button class="collect-btn" :disabled="isLocked || !formData.key || !paneData.shareLink" @click="upsertUser">
          采集小红书数据
        </el-button>
      </div>

      <div class="collect-btn-item">
        <el-button class="update-btn" :disabled="isLocked || !formData.key || !paneData.userTableId" @click="batchUpdateUser">
          批量更新数据
        </el-button>
      </div>
    </div>
  </div>
</template>
'''

if __name__ == '__main__':
    base_dir = r"d:\project\FeishuPlugin\src\paneForms"
    
    # 注意：这些是简化的模板，实际使用时需要根据每个平台的具体业务逻辑调整
    # 建议先手动检查每个表单的业务逻辑，然后再运行此脚本
    
    print("Warning: These are simplified templates.")
    print("Please manually check each form's business logic before running.")
    print("Skipping automatic refactoring for gh/v2/xhs forms.")
    print("Please refactor them manually based on ksForm.vue as reference.")
