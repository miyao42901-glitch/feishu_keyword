import { afterEach, describe, expect, it, vi } from 'vitest'

import { deleteAsyncTask } from '@/lib/async-task-api'

describe('deleteAsyncTask', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('POST /api/v1/async/tasks/{task_id}/delete，携带 x-api-key 与 X-User-Id', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({ code: 0, data: null }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await deleteAsyncTask({ apiKey: 'test-key', userId: 14 }, '4')

    expect(fetchMock).toHaveBeenCalledOnce()
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toMatch(/\/api\/v1\/async\/tasks\/4\/delete$/)
    expect(init.method).toBe('POST')
    const headers = init.headers as Record<string, string>
    expect(headers['x-api-key']).toBe('test-key')
    expect(headers['X-User-Id']).toBe('14')
    expect(init.body).toBe('{}')
  })

  it('task_id 为空时抛出', async () => {
    await expect(deleteAsyncTask({ apiKey: 'k', userId: 1 }, '  ')).rejects.toThrow(/task_id/)
  })
})
