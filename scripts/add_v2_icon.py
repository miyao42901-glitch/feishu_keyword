#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add QuestionFilled icon import to V2 form
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def add_icon_import():
    """Add QuestionFilled icon import to V2 form"""
    filepath = r"d:\project\FeishuPlugin\src\paneForms\v2Form.vue"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经导入了 QuestionFilled
    if 'QuestionFilled' in content and 'from \'@element-plus/icons-vue\'' in content:
        print("QuestionFilled icon already imported!")
        return True
    
    # 添加 ElIcon 到 element-plus 导入
    content = content.replace(
        "import { ElSelect, ElOption, ElInput } from 'element-plus';",
        "import { ElSelect, ElOption, ElInput, ElIcon } from 'element-plus';"
    )
    
    # 添加 QuestionFilled 图标导入
    content = content.replace(
        "import { ElSelect, ElOption, ElInput, ElIcon } from 'element-plus';",
        "import { ElSelect, ElOption, ElInput, ElIcon } from 'element-plus';\n  import { QuestionFilled } from '@element-plus/icons-vue';"
    )
    
    # 添加 ElIcon 和 QuestionFilled 到 components
    content = content.replace(
        """  export default {
    components: {
      ElSelect,
      ElOption,
      ElInput,
      TableSelect,""",
        """  export default {
    components: {
      ElSelect,
      ElOption,
      ElInput,
      ElIcon,
      QuestionFilled,
      TableSelect,"""
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("QuestionFilled icon import added successfully!")
    print("The question mark icon will now display correctly!")
    return True

if __name__ == '__main__':
    add_icon_import()
