import { onMounted, onUnmounted, ref } from 'vue'

/** 与 theme.css 中 @media (max-width: …) 保持一致 */
const MOBILE_MAX_PX = 899

export function useAdminMobileLayout() {
  const isMobile = ref(false)
  let mql: MediaQueryList | null = null

  function sync() {
    if (typeof window === 'undefined') {
      return
    }
    isMobile.value = window.matchMedia(`(max-width: ${MOBILE_MAX_PX}px)`).matches
  }

  function onChange() {
    sync()
  }

  onMounted(() => {
    if (typeof window === 'undefined') {
      return
    }
    mql = window.matchMedia(`(max-width: ${MOBILE_MAX_PX}px)`)
    isMobile.value = mql.matches
    mql.addEventListener('change', onChange)
  })

  onUnmounted(() => {
    mql?.removeEventListener('change', onChange)
    mql = null
  })

  return { isMobile, mobileMaxPx: MOBILE_MAX_PX }
}
