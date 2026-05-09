<script setup lang="ts">
/** 信源平台标识，与任务表单 `selectedSources` 一致 */
export type PlatformKey =
  | 'xiaohongshu'
  | 'weibo'
  | 'douyin'
  | 'gzh'
  | 'shipinhao'
  | 'kuaishou'

defineProps<{
  platform: PlatformKey
}>()
</script>

<template>
  <span
    class="inline-flex size-9 shrink-0 items-center justify-center overflow-hidden rounded-lg shadow-sm ring-1 ring-black/5"
    aria-hidden="true"
  >
    <!-- 抽象色块图标，非各平台官方商标 -->
    <svg
      v-if="platform === 'xiaohongshu'"
      class="size-full"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect width="24" height="24" fill="#FF2442" />
      <path
        d="M12 6c-2.5 0-4 1.6-4 4.2 0 2.2 1.2 3.6 3 4.2l-.5 2.1 2.3-1.4c2.3-.4 3.7-2.1 3.7-4.5C16 7.6 14.5 6 12 6z"
        fill="#fff"
        opacity=".95"
      />
    </svg>
    <svg
      v-else-if="platform === 'weibo'"
      class="size-full"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect width="24" height="24" fill="#E6162D" />
      <circle cx="12" cy="12" r="5" fill="#fff" opacity=".95" />
      <circle cx="12" cy="12" r="2" fill="#E6162D" />
    </svg>
    <svg
      v-else-if="platform === 'douyin'"
      class="size-full"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect width="24" height="24" fill="#111" />
      <path d="M9 7h2v10H9V7zm4 3h2v7c0 1-1 2-2.5 2S10 18 10 17h2c0 .3.3.5.5.5s.5-.2.5-.5V10z" fill="#25F4EE" />
      <path d="M13 7h2v3h-2V7z" fill="#FE2C55" opacity=".95" />
    </svg>
    <svg
      v-else-if="platform === 'gzh'"
      class="size-full"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect width="24" height="24" fill="#07C160" />
      <path
        d="M8 7h8v2H8V7zm0 3.5h8V13H8v-2.5zm0 3.5h5v2H8v-2z"
        fill="#fff"
        opacity=".95"
      />
    </svg>
    <svg
      v-else-if="platform === 'shipinhao'"
      class="size-full"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect width="24" height="24" fill="#FA9D3B" />
      <path d="M9 8l7 4-7 4V8z" fill="#fff" opacity=".95" />
    </svg>
    <svg
      v-else-if="platform === 'kuaishou'"
      class="size-full"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect width="24" height="24" fill="#FF4906" />
      <path
        d="M8 10c0-1.1.9-2 2-2h4c1.1 0 2 .9 2 2v4c0 1.1-.9 2-2 2h-4c-1.1 0-2-.9-2-2v-4z"
        fill="#fff"
        opacity=".9"
      />
      <path d="M11 11h2v2h-2v-2z" fill="#FF4906" />
    </svg>
  </span>
</template>
