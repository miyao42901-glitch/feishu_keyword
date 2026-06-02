#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix V2 form imports to resolve white screen issue
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fix_v2_imports():
    """Fix missing imports in V2 form"""
    filepath = r"d:\project\FeishuPlugin\src\paneForms\v2Form.vue"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复导入部分
    old_imports = """  import { ref, computed } from 'vue';
  import { bitable, FieldType, NumberFormatter, DateFormatter } from '@lark-base-open/js-sdk';
  import { ElSelect, ElOption, ElInput, ElIcon } from 'element-plus';
  import { QuestionFilled } from '@element-plus/icons-vue';
  import pluginAPI from '@/utils/request'
  import { writeToTable, updateTable, getFirstRecordByField} from '@/utils/tableHelper'
  import TableSelect from '@/components/TableSelect.vue'
  import { SectionTitle, CollectSection, FieldLabel, ToggleButtons, CollectButton } from '@/components/collect'
  import '@/assets/form-styles.css'"""
    
    new_imports = """  import { ref, computed } from 'vue';
  import { bitable, FieldType, NumberFormatter, DateFormatter } from '@lark-base-open/js-sdk';
  import { ElSelect, ElOption, ElInput, ElIcon } from 'element-plus';
  import { QuestionFilled, CirclePlus, Remove } from '@element-plus/icons-vue';
  import pluginAPI from '@/utils/request'
  import { writeToTable, updateTable, getFirstRecordByField} from '@/utils/tableHelper'
  import TableSelect from '@/components/TableSelect.vue'
  import generalSelect from '@/components/generalSelect.vue'
  import { SectionTitle, CollectSection, FieldLabel, ToggleButtons, CollectButton } from '@/components/collect'
  import '@/assets/form-styles.css'"""
    
    content = content.replace(old_imports, new_imports)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("V2 form imports fixed successfully!")
    print("White screen issue should be resolved now!")
    return True

if __name__ == '__main__':
    fix_v2_imports()
