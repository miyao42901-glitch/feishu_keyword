import { ref, onMounted, watch } from 'vue';
import { bitable } from '@lark-base-open/js-sdk';

// 全局主题变量
const globalTheme = ref('');

// 主题样式定义
const themeStyles = {
  LIGHT: {
    //使用默认主题色
  },
  DARK: {
    // 主题色
    '--el-color-primary': '#4571e1',
    '--el-color-primary-light-3': '#5a81e6',
    '--el-color-primary-light-5': '#6f91eb',
    '--el-color-primary-light-7': '#84a1f0',
    '--el-color-primary-light-8': '#90abf2',
    '--el-color-primary-light-9': '#b8c6f6',
    '--el-color-primary-dark-2': '#3a61c1',
    
    // 背景色
    '--el-bg-color': '#252525',
    '--el-bg-color-page': '#1f1f1f',
    '--el-bg-color-overlay': '#252525',
    
    // 边框色
    '--el-border-color': '#434343',
    '--el-border-color-light': '#4e4e4e',
    '--el-border-color-lighter': '#434343',
    '--el-border-color-extra-light': '#2f2f2f',
    
    // 文本色
    '--el-text-color-primary': '#e6e6e6',
    '--el-text-color-regular': '#c0c4cc',
    '--el-text-color-secondary': '#909399',
    '--el-text-color-placeholder': '#606266',
    
    // 卡片样式
    '--el-card-bg-color': '#2f2f2f',
    '--el-card-border-color': '#434343',
    
    // 加载遮罩
    '--el-overlay-color': 'rgba(37, 37, 37, 0.8)',
    '--el-overlay-color-light': 'rgba(37, 37, 37, 0.9)',
    '--el-overlay-color-dark': 'rgba(0, 0, 0, 0.8)',
  },
};

// 设置主题颜色
const setThemeColor = (themeValue) => {
  const el = document.documentElement;
  const currentThemeStyles = themeStyles[themeValue];

  if (currentThemeStyles) {
    // 清除所有已设置的主题变量
    Object.keys(themeStyles.DARK).forEach(property => {
      el.style.removeProperty(property);
    });

    // 设置新的主题变量
    Object.entries(currentThemeStyles).forEach(([property, value]) => {
      el.style.setProperty(property, value);
    });

    // 添加主题类名到body
    document.body.classList.remove('light-theme', 'dark-theme');
    document.body.classList.add(themeValue.toLowerCase() + '-theme');
  }
};

// 初始化主题
const initTheme = async () => {
  try {
    const themeValue = await bitable.bridge.getTheme();
    globalTheme.value = themeValue;
    setThemeColor(themeValue);
  } catch (error) {
    console.error('获取主题失败:', error);
    // 默认使用亮色主题
    globalTheme.value = 'LIGHT';
    setThemeColor('LIGHT');
  }
};

// 监听主题变化
const setupThemeListener = () => {
  bitable.bridge.onThemeChange((event) => {
    const themeValue = event.data.theme;
    globalTheme.value = themeValue;
    setThemeColor(themeValue);
  });
};

// 导出主题钩子
export const useTheme = () => {
  // 挂载时初始化主题
  onMounted(() => {
    initTheme();
    setupThemeListener();
  });

  // 监听主题变化
  watch(globalTheme, (newTheme) => {
    setThemeColor(newTheme);
  });

  // 抛出当前主题变量
  return {
    theme: globalTheme
  };
};

// 导出全局主题变量，供其他组件使用
export { globalTheme };