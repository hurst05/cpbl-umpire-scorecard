import { test } from 'node:test'
import assert from 'node:assert/strict'
import { GAME_TYPES, getGameKindCode, filterGamesByKind } from '../src/utils/gameTypes.js'

test('supported game types match the official CPBL codes', () => {
  assert.deepEqual(GAME_TYPES, {
    A: '一軍例行賽',
    G: '一軍熱身賽',
    E: '一軍季後挑戰賽',
    C: '一軍總冠軍賽'
  })
})

test('legacy summaries derive their type from game ID and keep equal game numbers separate', () => {
  const games = ['A', 'G', 'E', 'C', 'D', 'F'].map(code => ({ game_id: `2026-${code}-1` }))
  for (const kind of Object.keys(GAME_TYPES)) {
    assert.equal(getGameKindCode({ game_id: `2026-${kind}-1` }), kind)
    assert.deepEqual(filterGamesByKind(games, kind), [{ game_id: `2026-${kind}-1` }])
  }
  assert.equal(getGameKindCode({ kind_code: 'E' }), 'E')
  assert.deepEqual(filterGamesByKind([{}, null, { game_id: 'invalid' }], 'A'), [])
})
