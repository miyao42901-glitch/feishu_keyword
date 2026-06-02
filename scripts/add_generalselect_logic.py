#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add generalSelect component and related logic to V2 form
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def add_generalselect_logic():
    """Add generalSelect component and related logic"""
    filepath = r"d:\project\FeishuPlugin\src\paneForms\v2Form.vue"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加 generalSelect 组件导入
    if 'generalSelect' not in content:
        content = content.replace(
            "import TableSelect from '@/components/TableSelect.vue'",
            "import TableSelect from '@/components/TableSelect.vue'\n  import generalSelect from '@/components/generalSelect.vue'"
        )
    
    # 添加 CirclePlus 和 Remove 图标导入
    if 'CirclePlus' not in content:
        content = content.replace(
            "import { QuestionFilled } from '@element-plus/icons-vue';",
            "import { QuestionFilled, CirclePlus, Remove } from '@element-plus/icons-vue';"
        )
    
    # 添加 generalSelect 到 components
    if 'generalSelect,' not in content:
        content = content.replace(
            """    components: {
      ElSelect,
      ElOption,
      ElInput,
      ElIcon,
      QuestionFilled,
      TableSelect,""",
            """    components: {
      ElSelect,
      ElOption,
      ElInput,
      ElIcon,
      QuestionFilled,
      CirclePlus,
      Remove,
      TableSelect,
      generalSelect,"""
        )
    
    # 在 paneData 后添加 searchValues
    if 'const searchValues = ref' not in content:
        # 找到 paneData 定义的位置
        panedata_pos = content.find('const paneData = ref({')
        if panedata_pos != -1:
            # 找到 paneData 定义结束的位置
            closing_brace = content.find('})', panedata_pos)
            if closing_brace != -1:
                insert_pos = closing_brace + 2
                # 插入 searchValues 定义
                searchvalues_code = '''

      const searchValues = ref({
        0: null,
      })

      const addSearchRow = () => {
        const keys = Object.keys(searchValues.value).map(Number)
        const maxKey = Math.max(...keys)
        searchValues.value[maxKey + 1] = null
      }

      const removeSearchRow = (key) => {
        delete searchValues.value[key]
      }
'''
                content = content[:insert_pos] + searchvalues_code + content[insert_pos:]
    
    # 在 return 语句中添加 searchValues, addSearchRow, removeSearchRow
    if 'searchValues,' not in content:
        content = content.replace(
            """      return {
        paneData,
        dateRange,
        ranges,""",
            """      return {
        paneData,
        dateRange,
        ranges,
        searchValues,
        addSearchRow,
        removeSearchRow,"""
        )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("generalSelect component and logic added successfully!")
    print("V2 form now has the same account input functionality as Douyin!")
    return True

if __name__ == '__main__':
    add_generalselect_logic()
