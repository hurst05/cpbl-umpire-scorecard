import test, { describe } from 'node:test'
import assert from 'node:assert/strict'
import {
  calculateDistanceCm,
  isSamePitch,
  findSimilarPitches,
  analyzeConsistency,
  calculateGameConsistency
} from '../src/utils/pitchGeometry.js'

describe('pitchGeometry utilities', () => {
  test('calculateDistanceCm calculates hybrid distance with batter height normalization', () => {
    const p1 = { x: 0.18, z: 1.02, sz_top: 0.883, sz_bottom: 0.446 }
    const p2 = { x: 0.19, z: 1.112, sz_top: 0.963, sz_bottom: 0.486 }
    const dist = calculateDistanceCm(p1, p2)
    assert.ok(dist >= 0.8 && dist <= 1.5)
  })

  test('isSamePitch correctly identifies identical pitches', () => {
    const p1 = { pa_index: 1, pitch_index: 2, called: 'STRIKE' }
    const p2 = { pa_index: 1, pitch_index: 2, called: 'STRIKE' }
    const p3 = { pa_index: 1, pitch_index: 3, called: 'BALL' }
    assert.equal(isSamePitch(p1, p2), true)
    assert.equal(isSamePitch(p1, p3), false)
  })

  test('findSimilarPitches and analyzeConsistency handle neighbors properly', () => {
    const target = { pa_index: 1, pitch_index: 1, x: 0.10, z: 0.70, called: 'STRIKE', true_call: 'BALL', sz_top: 0.95, sz_bottom: 0.48 }
    const neighbor = { pa_index: 2, pitch_index: 1, x: 0.11, z: 0.71, called: 'STRIKE', true_call: 'BALL', sz_top: 0.95, sz_bottom: 0.48 }
    const far = { pa_index: 3, pitch_index: 1, x: -0.30, z: 0.20, called: 'BALL', true_call: 'BALL', sz_top: 0.95, sz_bottom: 0.48 }
    const sim = findSimilarPitches(target, [target, neighbor, far], 8.0)
    assert.equal(sim.length, 1)
    assert.equal(sim[0].pa_index, 2)

    const diag = analyzeConsistency(target, sim)
    assert.equal(diag.diagnosisType, 'generous')
  })

  test('calculateGameConsistency handles empty and single pitch inputs', () => {
    assert.equal(calculateGameConsistency([])?.consistencyRate, 100.0)
    assert.equal(calculateGameConsistency([{ x: 0.1, z: 0.6, called: 'STRIKE' }])?.consistencyRate, 100.0)
  })

  test('calculateGameConsistency evaluates consistent and conflicting clusters', () => {
    const consistentPitches = [
      { pa_index: 1, pitch_index: 1, x: 0.10, z: 0.70, called: 'STRIKE', sz_top: 0.95, sz_bottom: 0.48 },
      { pa_index: 2, pitch_index: 1, x: 0.12, z: 0.71, called: 'STRIKE', sz_top: 0.95, sz_bottom: 0.48 },
      { pa_index: 3, pitch_index: 1, x: -0.30, z: 0.20, called: 'BALL', sz_top: 0.95, sz_bottom: 0.48 }
    ]
    const res1 = calculateGameConsistency(consistentPitches, 8.0)
    assert.equal(res1.totalPairs, 1)
    assert.equal(res1.consistentPairs, 1)
    assert.equal(res1.consistencyRate, 100.0)
    assert.equal(res1.ratioStr, '1/1')
    assert.equal(res1.conflictingPitchesCount, 0)
    assert.equal(res1.isolatedCount, 1)

    const conflictPitches = [
      { pa_index: 1, pitch_index: 1, x: 0.10, z: 0.70, called: 'STRIKE', sz_top: 0.95, sz_bottom: 0.48 },
      { pa_index: 2, pitch_index: 1, x: 0.12, z: 0.71, called: 'BALL', sz_top: 0.95, sz_bottom: 0.48 }
    ]
    const res2 = calculateGameConsistency(conflictPitches, 8.0)
    assert.equal(res2.totalPairs, 1)
    assert.equal(res2.consistentPairs, 0)
    assert.equal(res2.consistencyRate, 0.0)
    assert.equal(res2.conflictingPitchesCount, 2)
  })
})
