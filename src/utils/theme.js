import { ref, onMounted, watch } from 'vue';
import { bitable } from '@lark-base-open/js-sdk';

// 全局主题变量
const globalTheme = ref('');

// 主题样式定义
const themeStyles = {
  LIGHT: {
    // '--el-color-primary': '#409eff',
    // '--el-color-primary-light-3': '#79bbff',
    // '--el-color-primary-light-5': '#a0cfff',
    // '--el-color-primary-light-7': '#c6e2ff',
    // '--el-color-primary-light-8': '#d1e7ff',
    // '--el-color-primary-light-9': '#ecf5ff',
    // '--el-color-primary-dark-2': '#337ecc',
    // '--el-bg-color': '#ffffff',
    // '--el-bg-color-page': '#f2f3f5',
    // '--el-bg-color-overlay': '#ffffff',
    // '--el-border-color': '#dcdfe6',
    // '--el-border-color-light': '#e4e7ed',
    // '--el-border-color-lighter': '#ebeef5',
    // '--el-border-color-extra-light': '#f2f6fc',
    // '--el-text-color-primary': '#303133',
    // '--el-text-color-regular': '#606266',
    // '--el-text-color-secondary': '#909399',
    // '--el-text-color-placeholder': '#a8abb2',
    // '--el-card-bg-color': '#ffffff',
    // '--el-card-border-color': '#ebeef5',
    // '--el-fill-color': '#f5f7fa',
    // '--el-fill-color-light': '#fafafa',
    // '--el-fill-color-lighter': '#fafafa',
    // '--el-fill-color-extra-light': '#fafafa',
    // '--el-fill-color-dark': '#f5f5f5',
    // '--el-fill-color-blank': '#ffffff',
    // '--el-overlay-color': 'rgba(255, 255, 255, 0.9)',
    // '--el-overlay-color-light': 'rgba(255, 255, 255, 0.8)',
    // '--el-overlay-color-dark': 'rgba(0, 0, 0, 0.5)',
    // '--el-mask-color': 'rgba(255, 255, 255, 0.9)',
    // '--el-mask-color-extra-light': 'rgba(255, 255, 255, 0.7)',
    // '--el-disabled-bg-color': '#f5f7fa',
    // '--el-disabled-color': '#c0c4cc',
  },
  DARK: {
    '--el-color-primary': '#4571e1',
    '--el-color-primary-light-3': '#5a81e6',
    '--el-color-primary-light-5': '#6f91eb',
    '--el-color-primary-light-7': '#84a1f0',
    '--el-color-primary-light-8': '#90abf2',
    '--el-color-primary-light-9': '#b8c6f6',
    '--el-color-primary-dark-2': '#3a61c1',
    '--el-bg-color': '#252525',
    '--el-bg-color-page': '#1f1f1f',
    '--el-bg-color-overlay': '#252525',
    '--el-border-color': '#434343',
    '--el-border-color-light': '#4e4e4e',
    '--el-border-color-lighter': '#545454',
    '--el-border-color-extra-light': '#2f2f2f',
    '--el-text-color-primary': '#e6e6e6',
    '--el-text-color-regular': '#c0c4cc',
    '--el-text-color-secondary': '#909399',
    '--el-text-color-placeholder': '#606266',
    '--el-card-bg-color': '#2f2f2f',
    '--el-card-border-color': '#434343',
    '--el-fill-color': '#2f2f2f',
    '--el-fill-color-light': '#363636',
    '--el-fill-color-lighter': '#3a3a3a',
    '--el-fill-color-extra-light': '#404040',
    '--el-fill-color-dark': '#262626',
    '--el-fill-color-blank': '#2f2f2f',
    '--el-overlay-color': 'rgba(37, 37, 37, 0.8)',
    '--el-overlay-color-light': 'rgba(37, 37, 37, 0.9)',
    '--el-overlay-color-dark': 'rgba(0, 0, 0, 0.8)',
    '--el-mask-color': 'rgba(37, 37, 37, 0.8)',
    '--el-mask-color-extra-light': 'rgba(37, 37, 37, 0.6)',
    '--el-disabled-bg-color': '#2a2a2a',
    '--el-disabled-color': '#5a5a5a',
  },
};

// 设置主题颜色
const setThemeColor = (themeValue) => {
  return
  const el = document.documentElement;
  const currentThemeStyles = themeStyles[themeValue];

  if (currentThemeStyles) {
    const themeKey = themeValue.toUpperCase();
    const previousTheme = el.dataset.currentTheme;

    if (previousTheme) {
      Object.keys(themeStyles[previousTheme] || {}).forEach(property => {
        el.style.removeProperty(property);
      });
    }

    Object.entries(currentThemeStyles).forEach(([property, value]) => {
      el.style.setProperty(property, value);
    });

    el.dataset.currentTheme = themeKey;
    document.documentElement.classList.remove('el-theme-dark');
    document.body.classList.remove('light-theme', 'dark-theme');
    if (themeValue.toLowerCase() === 'dark') {
      document.documentElement.classList.add('el-theme-dark');
    }
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