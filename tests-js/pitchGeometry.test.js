import test, { describe } from 'node:test'
import assert from 'node:assert/strict'
import {
  calculateDistanceCm,
  isSamePitch,
  findSimilarPitches,
  analyzeConsistency,
  calculateGameConsistency,
  isPitchHorizontalDeviation
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
    assert.equal(diag.totalCount, 2)
    assert.equal(diag.strikeCount, 2)
    assert.equal(diag.ballCount, 0)
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
  test('isPitchHorizontalDeviation correctly identifies left/right edge pitches', () => {
    const horizontalOut = { x: 0.28, z: 0.70, sz_top: 0.95, sz_bottom: 0.48 }
    const verticalOut = { x: 0.05, z: 1.10, sz_top: 0.95, sz_bottom: 0.48 }
    const horizontalIn = { x: 0.20, z: 0.70, sz_top: 0.95, sz_bottom: 0.48 }
    const verticalIn = { x: 0.05, z: 0.93, sz_top: 0.95, sz_bottom: 0.48 }

    assert.equal(isPitchHorizontalDeviation(horizontalOut), true)
    assert.equal(isPitchHorizontalDeviation(verticalOut), false)
    assert.equal(isPitchHorizontalDeviation(horizontalIn), true)
    assert.equal(isPitchHorizontalDeviation(verticalIn), false)
  })

  test('findSimilarPitches supports batter_relative view mode with horizontal mirroring', () => {
    // Target: Left-handed batter near left edge (x = 0.23, z = 0.70)
    const targetLeft = { pa_index: 1, pitch_index: 1, batter: '邱智呈', bats: 'L', x: 0.23, z: 0.70, called: 'STRIKE', sz_top: 0.95, sz_bottom: 0.48 }
    // Candidate 1: Left-handed batter also near left edge (x = 0.24, z = 0.70) -> same physical side
    const sameSideLeft = { pa_index: 2, pitch_index: 1, batter: '陳傑憲', bats: 'L', x: 0.24, z: 0.70, called: 'STRIKE', sz_top: 0.95, sz_bottom: 0.48 }
    // Candidate 2: Right-handed batter near right edge (x = -0.23, z = 0.70) -> opposite side, mirrored to +0.23!
    const mirroredRight = { pa_index: 3, pitch_index: 1, batter: '林立', bats: 'R', x: -0.23, z: 0.70, called: 'STRIKE', sz_top: 0.95, sz_bottom: 0.48 }
    // Candidate 3: Right-handed batter at left edge (x = 0.23, z = 0.70) -> mirrored to -0.23 (far from +0.23 in batter relative view)
    const nonMirroredRight = { pa_index: 4, pitch_index: 1, batter: '詹子賢', bats: 'R', x: 0.23, z: 0.70, called: 'STRIKE', sz_top: 0.95, sz_bottom: 0.48 }

    const all = [targetLeft, sameSideLeft, mirroredRight, nonMirroredRight]

    // 1. Absolute view: matches same physical location (sameSideLeft and nonMirroredRight)
    const absResults = findSimilarPitches(targetLeft, all, 7.5, { viewMode: 'absolute' })
    assert.equal(absResults.length, 2)
    assert.ok(absResults.some(p => p.pa_index === 2))
    assert.ok(absResults.some(p => p.pa_index === 4))

    // 2. Batter relative view: matches same relative location (sameSideLeft and mirroredRight)
    const relResults = findSimilarPitches(targetLeft, all, 7.5, { viewMode: 'batter_relative' })
    assert.equal(relResults.length, 2)
    assert.ok(relResults.some(p => p.pa_index === 2 && !p.is_mirrored))
    assert.ok(relResults.some(p => p.pa_index === 3 && p.is_mirrored))
    assert.ok(!relResults.some(p => p.pa_index === 4))
  })
})
