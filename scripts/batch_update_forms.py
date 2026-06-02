#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修改表单样式脚本
将旧的 el-form 样式改为抖音的新样式
只修改样式，不改变业务逻辑
"""

import re
import os
import sys

def replace_template_section(filepath, platform_name):
    """替换模板部分，使用与抖音相同的样式"""
    
    print(f"\n处理 {platform_name} 表单: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 备份原文件
        backup_path = filepath + '.style_backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  已备份到: {backup_path}")
        
        # 查找 <template> 和 </template> 的位置
        template_start = content.find('<template>')
        template_end = content.find('</template>') + len('</template>')
        
        if template_start == -1 or template_end == -1:
            print("  错误: 找不到 template 标签")
            return False
        
        # 提取 script 部分和 style 部分
        script_part = content[:template_start]
        style_part = content[template_end:]
        
        # 根据不同平台生成新的模板
        # 这里需要根据每个平台的具体业务逻辑来定制
        # 暂时先输出提示信息
        
        print(f"  提示: 请手动修改 {platform_name} 表单的模板部分")
        print(f"  参考文件: dyForm_new.vue")
        print(f"  需要修改的内容:")
        print(f"    1. <el-form> → <div class=\"collect-panel\">")
        print(f"    2. <el-radio-group> → <div class=\"toggle-wrapper\"> + <el-button class=\"toggle-btn\">")
        print(f"    3. <el-form-item> → <div class=\"section-block\"> + <div class=\"field-label\">")
        print(f"    4. <el-button type=\"primary\"> → <el-button class=\"collect-btn\">")
        print(f"    5. 移除所有 <el-tooltip>")
        
        return True
        
    except Exception as e:
        print(f"  错误: {e}")
        return False

def main():
    """主函数"""
    base_dir = r"d:\project\FeishuPlugin\src\paneForms"
    
    # 需要处理的表单
    forms = {
        'ksForm.vue': '快手',
        'ghForm.vue': '公众号',
        'v2Form.vue': '视频号',
        'xhsForm.vue': '小红书',
    }
    
    print("=" * 60)
    print("表单样式批量修改脚本")
    print("=" * 60)
    print("\n说明:")
    print("1. 导入部分已经更新完成")
    print("2. 现在需要手动修改每个表单的模板部分")
    print("3. 参考 dyForm_new.vue 的样式结构")
    print("4. 所有文件将自动备份")
    
    for form_file, platform_name in forms.items():
        filepath = os.path.join(base_dir, form_file)
        if os.path.exists(filepath):
            replace_template_section(filepath, platform_name)
        else:
            print(f"\n文件不存在: {filepath}")
    
    print("\n" + "=" * 60)
    print("处理完成！")
    print("=" * 60)
    print("\n下一步:")
    print("1. 打开每个表单文件")
    print("2. 参考 dyForm_new.vue 的模板结构")
    print("3. 手动修改模板部分，保留所有业务逻辑")
    print("4. 测试功能是否正常")

if __name__ == '__main__':
    main()
