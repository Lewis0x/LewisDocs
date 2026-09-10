import assert from 'node:assert/strict'
import test from 'node:test'

import {
  readAiLanguage,
  resolveAiLanguage,
  writeAiLanguage,
} from '../../../docs/.vitepress/ai-state.mjs'

const memoryStorage = () => {
  const values = new Map()
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
  }
}

test('AI language preference follows saved, page, browser, then English priority', () => {
  assert.equal(
    resolveAiLanguage({
      stored: 'zh-CN',
      pageLanguage: 'en',
      browserLanguage: 'en-US',
    }),
    'zh-CN',
  )
  assert.equal(
    resolveAiLanguage({
      stored: 'invalid',
      pageLanguage: 'en',
      browserLanguage: 'zh-CN',
    }),
    'en',
  )
  assert.equal(
    resolveAiLanguage({ browserLanguage: 'zh-Hans' }),
    'zh-CN',
  )
  assert.equal(resolveAiLanguage({ browserLanguage: 'fr-FR' }), 'en')
})

test('AI language storage is defensive', () => {
  const storage = memoryStorage()
  assert.equal(writeAiLanguage(storage, 'zh-CN'), true)
  assert.equal(readAiLanguage(storage, 'en', 'en-US'), 'zh-CN')

  const broken = {
    getItem() {
      throw new Error('blocked')
    },
    setItem() {
      throw new Error('blocked')
    },
  }
  assert.equal(readAiLanguage(broken, undefined, 'zh-CN'), 'zh-CN')
  assert.equal(writeAiLanguage(broken, 'en'), false)
})
