import { before, after, beforeEach, describe, test } from 'node:test'
import assert from 'node:assert/strict'
import { createServer } from 'vite'

describe('dataService keeps game types separate', () => {
  const servers = []
  const services = {}
  const games = ['A', 'G', 'E', 'C'].map((kind, index) => ({
    game_id: `2026-${kind}-1`,
    game_sno: 1,
    game_date: '2026-10-10',
    home_team: '主隊',
    visiting_team: '客隊',
    home_score: index + 3,
    visiting_score: 0,
    hp_umpire: kind,
    field: kind,
    overall_acc: (index + 3) * 10,
    game_duration_minutes: (index + 3) * 10
  }))
  const manifest = { schema_version: 1, available_years: [2026, 2025], games }
  const response = data => new Response(JSON.stringify(data))

  before(async () => {
    for (const mode of ['static', 'api']) {
      const server = await createServer({
        configFile: false,
        server: { middlewareMode: true, ws: false },
        optimizeDeps: { noDiscovery: true, include: [] },
        define: { 'import.meta.env.VITE_DATA_MODE': JSON.stringify(mode) }
      })
      servers.push(server)
      services[mode] = await server.ssrLoadModule('/src/services/dataService.js')
    }
  })
  after(async () => { await Promise.all(servers.map(server => server.close())) })
  beforeEach(() => services.static._resetManifestCache())

  test('static lists, years and default game use one type including legacy summaries', async t => {
    t.mock.method(globalThis, 'fetch', async () => response(manifest))
    assert.deepEqual((await services.static.fetchGameList('all')).map(g => g.game_id), ['2026-A-1'])
    assert.deepEqual((await services.static.fetchGameList('2026', 'E')).map(g => g.game_id), ['2026-E-1'])
    assert.deepEqual(await services.static.fetchAvailableYears('C'), [2026])
    assert.equal(await services.static.fetchDefaultGameId('G'), '2026-G-1')
  })

  test('static stats use independent files for each type', async t => {
    const urls = []
    t.mock.method(globalThis, 'fetch', async url => {
      urls.push(url)
      const kind = url.includes('/stats/') && !url.includes('/stats/all.json') ? url.split('/').at(-2) : 'A'
      return response({ kind_code: kind, total_games: 1 })
    })
    for (const kind of ['A', 'G', 'E', 'C']) {
      assert.equal((await services.static.fetchSeasonStats('all', kind)).kind_code, kind)
    }
    assert.deepEqual(urls, ['/data/stats/all.json', '/data/stats/G/all.json', '/data/stats/E/all.json', '/data/stats/C/all.json'])
  })

  test('missing or mismatched static stats fall back to only the selected type', async t => {
    t.mock.method(globalThis, 'fetch', async url => {
      if (url.endsWith('manifest.json')) return response(manifest)
      if (url.includes('/stats/C/')) return response({ kind_code: 'A', total_games: 99 })
      return new Response('', { status: 404 })
    })
    for (const [kind, score] of [['A', 3], ['G', 4], ['E', 5], ['C', 6]]) {
      const stats = await services.static.fetchSeasonStats('all', kind)
      assert.equal(stats.total_games, 1)
      assert.equal(stats.kind_code, kind)
      assert.equal(stats.scores.total_runs, score)
      assert.equal(stats.umpire_leaderboard[0].hp_umpire, kind)
      assert.equal(stats.team_standings[0].runs_scored, score)
      assert.equal(stats.stadium_stats[0].field, kind)
    }
    assert.equal((await services.static.fetchSeasonStats('2025', 'E')).total_games, 0)
  })

  test('API requests always include a single type and batch collect keeps the selection', async t => {
    const urls = []
    t.mock.method(globalThis, 'fetch', async url => {
      urls.push(url)
      if (url.startsWith('/api/seasons')) return response({ seasons: [2026] })
      if (url.startsWith('/api/games/cached')) return response([games[2]])
      return response({ kind_code: 'E', total_games: 1 })
    })
    await services.api.fetchAvailableYears('E')
    await services.api.fetchGameList('all', 'E')
    await services.api.fetchSeasonStats('all', 'E')
    await services.api.runBatchCollect('2026-10-10', 'E')
    assert.deepEqual(urls, [
      '/api/seasons?kind_code=E',
      '/api/games/cached?kind_code=E',
      '/api/stats/season/all?kind_code=E',
      '/api/batch-collect?date=2026-10-10&kind_code=E'
    ])
  })

  test('game errors expose the backend explanation instead of only Bad Request', async t => {
    const detail = '官網目前缺少可分析的 Trackman 球點，請稍後重試'
    t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify({ detail }), {
      status: 400, statusText: 'Bad Request'
    }))
    await assert.rejects(services.api.fetchGame('2026-E-3'), { message: detail })
  })

  test('game errors retain a readable fallback for non-JSON or non-text details', async t => {
    for (const body of ['unavailable', JSON.stringify({ detail: [{ msg: 'invalid' }] })]) {
      t.mock.method(globalThis, 'fetch', async () => new Response(body, { status: 400, statusText: 'Bad Request' }))
      await assert.rejects(services.api.fetchGame('2026-E-3'), { message: '擷取賽事資料失敗 (Bad Request)' })
    }
  })
})
