import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  buildResultsAcceptanceBody,
  postResultsAcceptance,
  type AsyncTaskRef,
} from '@/lib/async-task-api'

describe('buildResultsAcceptanceBody', () => {
  it('按平台汇总有结果的异步 task_id', () => {
    const refs: AsyncTaskRef[] = [
      { taskId: '3', platform: 'douyin', keyword: 'a' },
      { taskId: '7', platform: 'xiaohongshu', keyword: 'b' },
      { taskId: '9', platform: 'gzh', keyword: 'c' },
    ]
    const resultsMap = new Map<string, Record<string, unknown>[]>()
    resultsMap.set('3', [{ aweme_id: '1' }])
    resultsMap.set('7', [{ note_id: '2' }])
    resultsMap.set('9', [])

    expect(buildResultsAcceptanceBody(refs, resultsMap)).toEqual({
      douyin: [3],
      xhs: [7],
    })
  })
})

describe('postResultsAcceptance', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('POST /api/v1/results/acceptance', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ code: 0, data: null }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await postResultsAcceptance(
      { apiKey: 'test-key', userId: 14 },
      { douyin: [3], xhs: [7] },
    )

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toMatch(/\/api\/v1\/results\/acceptance$/)
    expect(init.method).toBe('POST')
    const headers = init.headers as Record<string, string>
    expect(headers['x-api-key']).toBe('test-key')
    expect(headers['X-User-Id']).toBe('14')
    expect(JSON.parse(String(init.body))).toEqual({ douyin: [3], xhs: [7] })
  })
})
