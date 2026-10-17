import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'
import { createServer } from 'vite'

let server
let downloadScorecardScreenshot
let renderer

before(async () => {
  const rendererId = '\0test:screenshot-renderer'
  server = await createServer({
    cacheDir: 'node_modules/.vite-test-screenshot',
    optimizeDeps: { noDiscovery: true, include: [] },
    server: { middlewareMode: true, hmr: false, watch: null },
    ssr: { noExternal: ['modern-screenshot'] },
    plugins: [{
      name: 'test-screenshot-renderer',
      enforce: 'pre',
      resolveId: id => id === 'modern-screenshot' ? rendererId : null,
      load: id => id === rendererId
        ? 'export let render; export function setRenderer(fn) { render = fn } export const domToBlob = (...args) => render(...args)'
        : null
    }]
  })
  renderer = await server.ssrLoadModule(rendererId)
  downloadScorecardScreenshot = (await server.ssrLoadModule('/src/utils/scorecardScreenshot.js')).downloadScorecardScreenshot
})

after(async () => { await server?.close() })

function createPage(t) {
  const list = { style: { maxHeight: '', overflowY: '' }, scrollTop: 210 }
  const element = { querySelectorAll: () => [list] }
  const downloads = []
  const link = { click: () => downloads.push({ href: link.href, download: link.download }), remove() {} }
  const previousDocument = globalThis.document
  const previousGetComputedStyle = globalThis.getComputedStyle
  globalThis.document = {
    fonts: { ready: Promise.resolve() },
    body: { append() {} },
    createElement: () => link
  }
  globalThis.getComputedStyle = node => ({ display: node.display || 'block', backgroundColor: '#f8fafc' })
  t.after(() => {
    globalThis.document = previousDocument
    globalThis.getComputedStyle = previousGetComputedStyle
  })
  t.mock.method(URL, 'createObjectURL', () => 'blob:scorecard')
  const revoke = t.mock.method(URL, 'revokeObjectURL', () => {})
  let release
  t.mock.method(globalThis, 'setTimeout', callback => { release = callback })
  return { element, list, downloads, revoke, release: () => release() }
}

test('downloads a PNG at the displayed card height without expanding or scrolling the missed-call list', async t => {
  const page = createPage(t)
  renderer.setRenderer(async (element, options) => {
    assert.equal(element, page.element)
    assert.deepEqual(page.list.style, { maxHeight: '', overflowY: '' })
    assert.equal(page.list.scrollTop, 210)
    assert.equal(options.scale, 2)
    assert.equal(options.features.restoreScrollPosition, true)
    assert.equal(options.backgroundColor, '#f8fafc')
    assert.equal(options.filter({ nodeType: 3 }), true)
    assert.equal(options.filter({ nodeType: 1, hasAttribute: () => false }), true)
    assert.equal(options.filter({ nodeType: 1, hasAttribute: () => true }), false)
    assert.equal(options.filter({ nodeType: 1, hasAttribute: () => false, display: 'none' }), false)
    const checkbox = { tagName: 'INPUT', type: 'checkbox', checked: true, toggleAttribute: t.mock.fn() }
    options.onCloneEachNode(checkbox)
    assert.deepEqual(checkbox.toggleAttribute.mock.calls[0].arguments, ['checked', true])
    return new Blob(['png'], { type: 'image/png' })
  })

  await downloadScorecardScreenshot(page.element, 'cpbl-scorecard-2026-C-1.png')

  assert.deepEqual(page.downloads, [{ href: 'blob:scorecard', download: 'cpbl-scorecard-2026-C-1.png' }])
  assert.deepEqual(page.list.style, { maxHeight: '', overflowY: '' })
  assert.equal(page.list.scrollTop, 210)
  page.release()
  assert.equal(page.revoke.mock.calls[0].arguments[0], 'blob:scorecard')
})

test('leaves the displayed list unchanged and does not download when image rendering fails', async t => {
  const page = createPage(t)
  page.list.style.maxHeight = '300px'
  renderer.setRenderer(async () => {
    throw new Error('image rendering failed')
  })

  await assert.rejects(downloadScorecardScreenshot(page.element, 'scorecard.png'), /image rendering failed/)

  assert.deepEqual(page.list.style, { maxHeight: '300px', overflowY: '' })
  assert.equal(page.list.scrollTop, 210)
  assert.equal(page.downloads.length, 0)
})
