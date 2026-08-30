import { test, describe } from 'node:test'
import assert from 'node:assert/strict'
import { isGameInManifest, validateGameDetail } from '../src/services/staticDataValidation.js'

describe('staticDataValidation', () => {
  describe('isGameInManifest', () => {
    const mockManifest = {
      schema_version: 1,
      games: [
        { game_id: '2026-A-295' },
        { game_id: '2026-A-296' }
      ]
    }

    test('returns true when gameId exists in manifest', () => {
      assert.equal(isGameInManifest(mockManifest, '2026-A-295'), true)
      assert.equal(isGameInManifest(mockManifest, '2026-A-296'), true)
    })

    test('returns false when gameId does not exist in manifest', () => {
      assert.equal(isGameInManifest(mockManifest, '2026-A-999'), false)
      assert.equal(isGameInManifest(mockManifest, ''), false)
      assert.equal(isGameInManifest(mockManifest, null), false)
    })

    test('returns false when manifest is invalid or empty', () => {
      assert.equal(isGameInManifest(null, '2026-A-295'), false)
      assert.equal(isGameInManifest({}, '2026-A-295'), false)
      assert.equal(isGameInManifest({ games: [] }, '2026-A-295'), false)
    })
  })

  describe('validateGameDetail', () => {
    const createValidDetail = () => ({
      game_info: { game_id: '2026-A-295' },
      umpire_metrics: { overall_accuracy: 92.5 },
      plate_appearances: [],
      all_called_pitches: []
    })

    test('passes on complete valid structure', () => {
      const valid = createValidDetail()
      assert.equal(validateGameDetail(valid, '2026-A-295'), true)
    })

    test('rejects non-object or null root', () => {
      assert.throws(() => validateGameDetail(null, '2026-A-295'), /格式損壞.*根節點/)
      assert.throws(() => validateGameDetail([], '2026-A-295'), /格式損壞.*根節點/)
      assert.throws(() => validateGameDetail('string', '2026-A-295'), /格式損壞.*根節點/)
    })

    test('rejects missing or non-object game_info', () => {
      const detail1 = createValidDetail()
      detail1.game_info = null
      assert.throws(() => validateGameDetail(detail1, '2026-A-295'), /game_info/)

      const detail2 = createValidDetail()
      detail2.game_info = []
      assert.throws(() => validateGameDetail(detail2, '2026-A-295'), /game_info/)
    })

    test('rejects missing or non-object umpire_metrics', () => {
      const detail1 = createValidDetail()
      detail1.umpire_metrics = []
      assert.throws(() => validateGameDetail(detail1, '2026-A-295'), /umpire_metrics/)

      const detail2 = createValidDetail()
      delete detail2.umpire_metrics
      assert.throws(() => validateGameDetail(detail2, '2026-A-295'), /umpire_metrics/)
    })

    test('rejects missing or non-array plate_appearances', () => {
      const detail1 = createValidDetail()
      detail1.plate_appearances = {}
      assert.throws(() => validateGameDetail(detail1, '2026-A-295'), /plate_appearances/)

      const detail2 = createValidDetail()
      detail2.plate_appearances = null
      assert.throws(() => validateGameDetail(detail2, '2026-A-295'), /plate_appearances/)
    })

    test('rejects missing or non-array all_called_pitches', () => {
      const detail1 = createValidDetail()
      detail1.all_called_pitches = null
      assert.throws(() => validateGameDetail(detail1, '2026-A-295'), /all_called_pitches/)

      const detail2 = createValidDetail()
      detail2.all_called_pitches = {}
      assert.throws(() => validateGameDetail(detail2, '2026-A-295'), /all_called_pitches/)
    })
  })
})
