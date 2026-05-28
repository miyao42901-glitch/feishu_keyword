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

  if (!yddmAuth.isLoggedIn) {
    throw new Error('请先登录账户')
  }

  let me = yddmAuth.me
  if (!me?.id || !me?.phone_num?.trim()) {
    me = await yddmAuth.refreshMe()
  }

  /** 顶部授权码与登录账户 `api_key` 不一致时，以 YDDM 登录态为准（避免旧 localStorage 导致 401） */
  const loginApiKey = String(me?.api_key ?? yddmAuth.me?.api_key ?? '').trim()
  let apiKey = String(globalSettings.authCode ?? '').trim()
  if (loginApiKey) {
    if (!apiKey || apiKey !== loginApiKey) {
      globalSettings.authCode = loginApiKey
      apiKey = loginApiKey
    }
  }
  if (!apiKey) {
    throw new Error('请先在顶部填写 API-Key（授权码），或重新登录同步')
  }

  const userId = me?.id ?? yddmAuth.me?.id
  if (userId == null || !String(userId).trim()) {
    throw new Error('缺少 X-User-Id：请先登录 YDDM 账户')
  }

  return {
    apiKey,
    userId,
    phoneNum: me?.phone_num ?? yddmAuth.me?.phone_num,
  }
}
