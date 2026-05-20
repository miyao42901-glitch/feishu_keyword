import { afterEach, describe, expect, it, vi } from 'vitest'

import { getAsyncTaskStatus } from '@/lib/async-task-api'

describe('getAsyncTaskStatus', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('GET /api/v1/async/tasks/{id}，Header x-api-key、X-User-Id，Query X-API-KEY', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      text: async () =>
        JSON.stringify({
          code: 0,
          data: { result: { task_id: 2, status: 'running', platform: 'xhs' } },
        }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const result = await getAsyncTaskStatus({ apiKey: 'my-key', userId: 30 }, '2')

    expect(result.lifecycle).toBe('running')
    expect(result.taskId).toBe('2')
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toMatch(/\/api\/v1\/async\/tasks\/2\?X-API-KEY=my-key$/)
    expect(init.method).toBe('GET')
    const headers = init.headers as Record<string, string>
    expect(headers['x-api-key']).toBe('my-key')
    expect(headers['X-User-Id']).toBe('30')
  })
})
