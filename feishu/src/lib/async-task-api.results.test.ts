import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  fetchAsyncTaskResultsPage,
  fetchAsyncTaskStatusAndResultsMaps,
  parseAsyncTaskStatusResponse,
  shouldFetchAsyncResultsAfterStatus,
} from '@/lib/async-task-api'

describe('fetchAsyncTaskResultsPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('GET /api/v1/async/tasks/{task_id}/results，携带 Header 与可选 page', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      text: async () =>
        JSON.stringify({
          code: 0,
          data: { result: { items: [{ aweme_id: '1', title: 't' }] } },
        }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await fetchAsyncTaskResultsPage({ apiKey: 'test-key', userId: 14 }, '113', { page: '2' })

    expect(fetchMock).toHaveBeenCalledOnce()
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toMatch(/\/api\/v1\/async\/tasks\/113\/results\?page=2$/)
    expect(init.method).toBe('GET')
    const headers = init.headers as Record<string, string>
    expect(headers['x-api-key']).toBe('test-key')
    expect(headers['X-User-Id']).toBe('14')
    expect(init.body).toBeUndefined()
  })
})

describe('fetchAsyncTaskStatusAndResultsMaps', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('data.result 为 running 时先 GET 状态再 GET results', async () => {
    const calls: string[] = []
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      calls.push(`${init?.method ?? 'GET'} ${url}`)
      if (url.includes('/127') && !url.includes('/results')) {
        return Promise.resolve({
          ok: true,
          text: async () =>
            JSON.stringify({
              code: 0,
              data: { result: { task_id: 127, status: 'running' } },
            }),
        })
      }
      if (url.includes('/127/results')) {
        return Promise.resolve({
          ok: true,
          text: async () =>
            JSON.stringify({
              code: 0,
              data: { result: { items: [{ aweme_id: '99' }] } },
            }),
        })
      }
      return Promise.resolve({ ok: true, text: async () => JSON.stringify({ code: 0, data: {} }) })
    })
    vi.stubGlobal('fetch', fetchMock)

    const { statusMap, resultsMap } = await fetchAsyncTaskStatusAndResultsMaps(
      { apiKey: 'k', userId: 1 },
      ['127'],
    )

    expect(statusMap.get('127')?.lifecycle).toBe('running')
    expect(resultsMap.get('127')).toHaveLength(1)
    expect(calls.some((c) => c.includes('/127/results'))).toBe(true)
  })

  it('先 GET 状态再 GET results', async () => {
    const calls: string[] = []
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      calls.push(`${init?.method ?? 'GET'} ${url}`)
      if (url.includes('/113') && !url.includes('/results')) {
        return Promise.resolve({
          ok: true,
          text: async () =>
            JSON.stringify({ code: 0, data: { task_id: '113', status: 'running' } }),
        })
      }
      if (url.includes('/113/results')) {
        return Promise.resolve({
          ok: true,
          text: async () =>
            JSON.stringify({
              code: 0,
              data: { result: { items: [{ aweme_id: '99' }] } },
            }),
        })
      }
      return Promise.resolve({ ok: true, text: async () => JSON.stringify({ code: 0, data: {} }) })
    })
    vi.stubGlobal('fetch', fetchMock)

    const { statusMap, resultsMap } = await fetchAsyncTaskStatusAndResultsMaps(
      { apiKey: 'k', userId: 1 },
      ['113'],
    )

    expect(statusMap.get('113')?.lifecycle).toBe('running')
    expect(resultsMap.get('113')).toHaveLength(1)
    const statusIdx = calls.findIndex((c) => c.startsWith('GET') && c.includes('/113') && !c.includes('/results'))
    const resultsIdx = calls.findIndex((c) => c.startsWith('GET') && c.includes('/113/results'))
    expect(statusIdx).toBeGreaterThanOrEqual(0)
    expect(resultsIdx).toBeGreaterThan(statusIdx)
  })

  it('status 为 pending 时不请求 results', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/113') && !url.includes('/results')) {
        return Promise.resolve({
          ok: true,
          text: async () =>
            JSON.stringify({ code: 0, data: { task_id: '113', status: 'pending' } }),
        })
      }
      throw new Error(`不应请求 results: ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    const { statusMap, resultsMap } = await fetchAsyncTaskStatusAndResultsMaps(
      { apiKey: 'k', userId: 1 },
      ['113'],
    )

    expect(statusMap.get('113')?.lifecycle).toBe('pending')
    expect(resultsMap.get('113')).toEqual([])
    expect(fetchMock).toHaveBeenCalledOnce()
  })
})

describe('parseAsyncTaskStatusResponse', () => {
  it('识别 data.result.status（与列表接口同构）', () => {
    const status = parseAsyncTaskStatusResponse(
      {
        code: 0,
        data: {
          result: {
            task_id: 127,
            status: 'running',
            platform: 'wxvideo',
          },
        },
      },
      '127',
    )
    expect(status.lifecycle).toBe('running')
    expect(status.taskId).toBe('127')
  })
})

describe('shouldFetchAsyncResultsAfterStatus', () => {
  it('仅 running 为 true', () => {
    expect(shouldFetchAsyncResultsAfterStatus('running')).toBe(true)
    expect(shouldFetchAsyncResultsAfterStatus('pending')).toBe(false)
    expect(shouldFetchAsyncResultsAfterStatus('completed')).toBe(false)
    expect(shouldFetchAsyncResultsAfterStatus('failed')).toBe(false)
  })
})
