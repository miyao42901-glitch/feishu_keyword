/**
 * 采集请求上下文：API Key、用户 id、手机号（折扣接口需要）。
 */

import type { SyncFetchContext } from '@/lib/sync-api-common'
import { useGlobalSettingsStore } from '@/stores/globalSettings'
import { useYddmAuthStore } from '@/stores/yddmAuth'

/** 构建采集鉴权上下文；登录态下若缺手机号则先 `GET /users/me` */
export async function buildCollectionFetchContext(): Promise<SyncFetchContext> {
  const globalSettings = useGlobalSettingsStore()
  const yddmAuth = useYddmAuthStore()

  const apiKey = String(globalSettings.authCode ?? '').trim()
  if (!apiKey) {
    throw new Error('请先在顶部填写 API-Key（授权码）')
  }
  if (!yddmAuth.isLoggedIn) {
    throw new Error('请先登录账户')
  }

  let me = yddmAuth.me
  if (!me?.phone_num?.trim()) {
    me = await yddmAuth.refreshMe()
  }

  return {
    apiKey,
    userId: me?.id ?? yddmAuth.me?.id,
    phoneNum: me?.phone_num ?? yddmAuth.me?.phone_num,
  }
}
