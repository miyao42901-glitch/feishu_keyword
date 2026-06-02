#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add tooltips to toggle buttons for all platforms
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def add_tooltips_to_form(filepath, platform_name):
    """Add tooltips to toggle buttons"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找切换按钮的位置
    if '<div class="toggle-wrapper">' not in content:
        print(f"  {platform_name}: No toggle-wrapper found, skipping")
        return False
    
    # 定义提示文字
    blogger_tip = "将采集账号的ID、粉丝数、简介、点赞数等基础信息"
    post_tip = "将采集作品的点赞、评论、查看、转发、发布时间等数据"
    
    # 替换第一个切换按钮（采集博主数据）
    # 查找模式：<el-button type="info" class="toggle-btn" :class="{ active: ... }" @click="...">采集博主数据</el-button>
    
    # 为抖音表单
    if 'paneData.collectionType' in content:
        old_blogger_btn = '<el-button type="info" class="toggle-btn" :class="{ active: paneData.collectionType === \'blogger\' }" @click="changecollectionType(\'blogger\')">采集博主数据</el-button>'
        new_blogger_btn = f'''<el-tooltip content="{blogger_tip}" placement="top">
            <el-button type="info" class="toggle-btn" :class="{{ active: paneData.collectionType === 'blogger' }}" @click="changecollectionType('blogger')">采集博主数据</el-button>
          </el-tooltip>'''
        
        old_post_btn = '<el-button type="info" class="toggle-btn" :class="{ active: paneData.collectionType === \'post\' }" @click="changecollectionType(\'post\')">采集作品数据</el-button>'
        new_post_btn = f'''<el-tooltip content="{post_tip}" placement="top">
            <el-button type="info" class="toggle-btn" :class="{{ active: paneData.collectionType === 'post' }}" @click="changecollectionType('post')">采集作品数据</el-button>
          </el-tooltip>'''
        
        content = content.replace(old_blogger_btn, new_blogger_btn)
        content = content.replace(old_post_btn, new_post_btn)
    
    # 为其他平台（使用 getDataType）
    elif 'paneData.getDataType' in content:
        # 采集博主数据按钮
        old_blogger_btn = '<el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 0 }" @click="paneData.getDataType = 0">采集博主数据</el-button>'
        new_blogger_btn = f'''<el-tooltip content="{blogger_tip}" placement="top">
            <el-button type="info" class="toggle-btn" :class="{{ active: paneData.getDataType === 0 }}" @click="paneData.getDataType = 0">采集博主数据</el-button>
          </el-tooltip>'''
        
        # 采集作品数据按钮
        old_post_btn = '<el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 1 }" @click="paneData.getDataType = 1">采集作品数据</el-button>'
        new_post_btn = f'''<el-tooltip content="{post_tip}" placement="top">
            <el-button type="info" class="toggle-btn" :class="{{ active: paneData.getDataType === 1 }}" @click="paneData.getDataType = 1">采集作品数据</el-button>
          </el-tooltip>'''
        
        content = content.replace(old_blogger_btn, new_blogger_btn)
        content = content.replace(old_post_btn, new_post_btn)
    
    # 为快手、公众号等其他平台（可能使用不同的文字）
    # 获取账号数据 -> 采集博主数据
    old_account_btn = '<el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 0 }" @click="paneData.getDataType = 0">获取账号数据</el-button>'
    new_account_btn = f'''<el-tooltip content="{blogger_tip}" placement="top">
            <el-button type="info" class="toggle-btn" :class="{{ active: paneData.getDataType === 0 }}" @click="paneData.getDataType = 0">获取账号数据</el-button>
          </el-tooltip>'''
    
    # 获取视频数据 -> 采集作品数据
    old_video_btn = '<el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 1 }" @click="paneData.getDataType = 1">获取视频数据</el-button>'
    new_video_btn = f'''<el-tooltip content="{post_tip}" placement="top">
            <el-button type="info" class="toggle-btn" :class="{{ active: paneData.getDataType === 1 }}" @click="paneData.getDataType = 1">获取视频数据</el-button>
          </el-tooltip>'''
    
    content = content.replace(old_account_btn, new_account_btn)
    content = content.replace(old_video_btn, new_video_btn)
    
    # 获取文章数据
    old_article_btn = '<el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 1 }" @click="paneData.getDataType = 1">获取文章数据</el-button>'
    new_article_btn = f'''<el-tooltip content="{post_tip}" placement="top">
            <el-button type="info" class="toggle-btn" :class="{{ active: paneData.getDataType === 1 }}" @click="paneData.getDataType = 1">获取文章数据</el-button>
          </el-tooltip>'''
    
    content = content.replace(old_article_btn, new_article_btn)
    
    # 获取公众号数据
    old_gh_btn = '<el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 0 }" @click="paneData.getDataType = 0">获取公众号数据</el-button>'
    new_gh_btn = f'''<el-tooltip content="{blogger_tip}" placement="top">
            <el-button type="info" class="toggle-btn" :class="{{ active: paneData.getDataType === 0 }}" @click="paneData.getDataType = 0">获取公众号数据</el-button>
          </el-tooltip>'''
    
    content = content.replace(old_gh_btn, new_gh_btn)
    
    # 获取笔记数据
    old_note_btn = '<el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 1 }" @click="paneData.getDataType = 1">获取笔记数据</el-button>'
    new_note_btn = f'''<el-tooltip content="{post_tip}" placement="top">
            <el-button type="info" class="toggle-btn" :class="{{ active: paneData.getDataType === 1 }}" @click="paneData.getDataType = 1">获取笔记数据</el-button>
          </el-tooltip>'''
    
    content = content.replace(old_note_btn, new_note_btn)
    
    # 获取博主数据
    old_blogger_btn2 = '<el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 0 }" @click="paneData.getDataType = 0">获取博主数据</el-button>'
    new_blogger_btn2 = f'''<el-tooltip content="{blogger_tip}" placement="top">
            <el-button type="info" class="toggle-btn" :class="{{ active: paneData.getDataType === 0 }}" @click="paneData.getDataType = 0">获取博主数据</el-button>
          </el-tooltip>'''
    
    content = content.replace(old_blogger_btn2, new_blogger_btn2)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  {platform_name}: Tooltips added successfully!")
    return True

if __name__ == '__main__':
    base_dir = r"d:\project\FeishuPlugin\src\paneForms"
    
    forms = {
        'dyForm_new.vue': '抖音',
        'ksForm.vue': '快手',
        'ghForm.vue': '公众号',
        'v2Form.vue': '视频号',
        'xhsForm.vue': '小红书',
    }
    
    print("Adding tooltips to all platform forms...")
    print("=" * 60)
    
    for form_file, platform_name in forms.items():
        filepath = f"{base_dir}\\{form_file}"
        add_tooltips_to_form(filepath, platform_name)
    
    print("=" * 60)
    print("All tooltips added successfully!")
    print("\nTooltip content:")
    print("- Blogger data: 将采集账号的ID、粉丝数、简介、点赞数等基础信息")
    print("- Post data: 将采集作品的点赞、评论、查看、转发、发布时间等数据")
