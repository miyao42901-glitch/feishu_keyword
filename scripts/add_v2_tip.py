#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add v2Tip component to V2 form
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def add_v2_tip():
    """Add v2Tip component and logic to V2 form"""
    filepath = r"d:\project\FeishuPlugin\src\paneForms\v2Form.vue"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加 v2Tip 组件导入
    if 'v2Tip' not in content:
        content = content.replace(
            "import generalSelect from '@/toolComponents/generalSelect.vue'",
            "import generalSelect from '@/toolComponents/generalSelect.vue'\n  import v2Tip from '@/tipDialogs/v2Tip.vue'"
        )
    
    # 添加 v2Tip 到 components
    if 'v2Tip,' not in content:
        content = content.replace(
            """      generalSelect,
      SectionTitle,""",
            """      generalSelect,
      v2Tip,
      SectionTitle,"""
        )
    
    # 添加 tipVisible 状态
    if 'const tipVisible = ref' not in content:
        # 找到 searchValues 定义的位置
        searchvalues_pos = content.find('const searchValues = ref({')
        if searchvalues_pos != -1:
            # 找到 removeSearchRow 函数结束的位置
            removesearchrow_end = content.find('delete searchValues.value[key]', searchvalues_pos)
            if removesearchrow_end != -1:
                # 找到这一行的结束位置
                line_end = content.find('\n', removesearchrow_end)
                if line_end != -1:
                    # 找到下一个 }
                    closing_brace = content.find('}', line_end)
                    if closing_brace != -1:
                        insert_pos = closing_brace + 1
                        # 插入 tipVisible 和 openTip
                        tip_code = '''

      const tipVisible = ref(false)

      const openTip = () => {
        tipVisible.value = true
      }
'''
                        content = content[:insert_pos] + tip_code + content[insert_pos:]
    
    # 在 return 语句中添加 tipVisible 和 openTip
    if 'tipVisible,' not in content:
        content = content.replace(
            """      return {
        paneData,
        dateRange,
        ranges,
        searchValues,
        addSearchRow,
        removeSearchRow,""",
            """      return {
        paneData,
        dateRange,
        ranges,
        searchValues,
        addSearchRow,
        removeSearchRow,
        tipVisible,
        openTip,"""
        )
    
    # 在模板中添加 v2Tip 组件
    if '<v2Tip' not in content:
        # 找到 </template> 之前的位置
        template_end = content.find('</template>')
        if template_end != -1:
            # 在 </template> 之前插入 v2Tip 组件
            tip_component = '''

  <v2Tip v-model:visible="tipVisible" />
'''
            content = content[:template_end] + tip_component + '\n' + content[template_end:]
    
    # 更新小问号的点击事件
    content = content.replace(
        '<el-icon class="icon-hint"><QuestionFilled /></el-icon>',
        '<el-icon class="icon-hint" @click="openTip"><QuestionFilled /></el-icon>'
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("v2Tip component added successfully!")
    print("Question mark icon now opens the help dialog!")
    return True

if __name__ == '__main__':
    add_v2_tip()
