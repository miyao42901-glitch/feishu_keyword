import { describe, expect, it } from 'vitest'

import { mapItemToColumnValues } from '@/lib/test-data-field-map'

const sampleItem = {
  post_id: '6763769a000000000900d09b',
  title: '教你认识：纳斯达克',
  summary: '#财经知识 正文',
  page_url: 'https://www.xiaohongshu.com/explore/6763769a000000000900d09b',
  nickname: '努力赚钱养家的董爸爸',
  sec_uid: '5c7a132e000000001203a7fa',
  content_type: 'normal',
  publish_time_ms: 1734571674000,
  like_count: 1474,
  comment_count: 91,
  collect_count: 1217,
  avatar_url: 'https://sns-avatar-qc.xhscdn.com/avatar/example.jpg',
  cover_url: 'https://sns-na-i1.xhscdn.com/cover.jpg',
}

describe('mapItemToColumnValues xiaohongshu (YDDM results)', () => {
  it('异步 results 字段名可映射到飞书列', () => {
    const cols = mapItemToColumnValues(sampleItem, 'xiaohongshu', {
      sourceFieldSelection: {
        xiaohongshu: [
          'noteId',
          'title',
          'noteBody',
          'publishedAt',
          'like',
          'comment',
          'favorite',
          'authorNickname',
          'authorId',
          'authorAvatar',
          'noteType',
          'noteImages',
        ],
      },
    })

    expect(cols['笔记ID']).toBe('6763769a000000000900d09b')
    expect(cols['笔记标题']).toContain('纳斯达克')
    expect(cols['笔记正文内容']).toContain('财经知识')
    expect(cols['点赞数']).toBe('1474')
    expect(cols['评论数']).toBe('91')
    expect(cols['收藏数']).toBe('1217')
    expect(cols['用户昵称']).toBe('努力赚钱养家的董爸爸')
    expect(cols['笔记类型（图文/视频）']).toBe('图文')
    expect(cols['作者用户ID']).toBe('5c7a132e000000001203a7fa')
    expect(cols['头像链接']).toContain('sns-avatar')
    expect(cols['图片URL数组']).toContain('cover.jpg')
    expect(cols['发布时间']).toMatch(/2024/)
  })
})
