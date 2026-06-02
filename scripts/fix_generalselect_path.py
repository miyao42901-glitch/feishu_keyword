#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix generalSelect import path in V2 form
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fix_generalselect_path():
    """Fix generalSelect import path"""
    filepath = r"d:\project\FeishuPlugin\src\paneForms\v2Form.vue"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复 generalSelect 导入路径
    content = content.replace(
        "import generalSelect from '@/components/generalSelect.vue'",
        "import generalSelect from '@/toolComponents/generalSelect.vue'"
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("generalSelect import path fixed successfully!")
    print("Changed from: @/components/generalSelect.vue")
    print("Changed to: @/toolComponents/generalSelect.vue")
    return True

if __name__ == '__main__':
    fix_generalselect_path()
