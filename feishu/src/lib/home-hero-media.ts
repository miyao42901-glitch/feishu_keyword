/** `public/images/home/` 下首页横幅静态资源 */
const HOME_HERO_RASTER_BASE = '/images/home'

/** 横幅右侧「剩余积分」钻石图标（原 `public/Frame.png`） */
export const homeHeroAccountPointsIcon = {
  '1x': `${HOME_HERO_RASTER_BASE}/account-points.png`,
  '2x': `${HOME_HERO_RASTER_BASE}/account-points@2x.png`,
} as const

/** 横幅右侧装饰背景（原 `public/im.png`） */
export const homeHeroBannerBg = {
  '1x': `${HOME_HERO_RASTER_BASE}/hero-banner.png`,
  '2x': `${HOME_HERO_RASTER_BASE}/hero-banner@2x.png`,
} as const

/** `<img>` 用：默认 1x，`srcset` 指向 2x */
export function homeHeroAccountPointsIconImgAttrs(): { src: string; srcset: string } {
  const { '1x': one, '2x': two } = homeHeroAccountPointsIcon
  return { src: one, srcset: `${two} 2x` }
}
