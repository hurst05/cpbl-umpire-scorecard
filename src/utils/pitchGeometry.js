import { getBatterBats } from './playerProfiles.js'

/**
 * 計算兩顆球在好球帶相對座標的距離 (公分)
 * - 左右邊界 (X): 本壘板寬度對所有打者固定，採用物理絕對距離 dx = (x1 - x2) * 100
 * - 上下邊界 (Z): 隨打者身高變化，採用各打者好球帶標準化高度比例換算 dz = (normZ1 - normZ2) * baseH * 100
 * @param {{x: number, z: number, sz_top?: number, sz_bottom?: number}} p1 基準球
 * @param {{x: number, z: number, sz_top?: number, sz_bottom?: number}} p2 比對球
 * @param {number} [targetZoneHeightM] 基準好球帶高度 (公尺, 預設取 p1 之好球帶高度)
 * @returns {number} 混合距離 (cm)
 */
export function calculateDistanceCm(p1, p2, targetZoneHeightM = null) {
  if (p1?.x == null || p1?.z == null || p2?.x == null || p2?.z == null) {
    return Infinity
  }
  // 左右 (X): 物理絕對距離
  const dxCm = (p1.x - p2.x) * 100

  // 上下 (Z): 依打者個別好球帶頂部與底部標準化
  const szTop1 = p1.sz_top || 0.963
  const szBot1 = p1.sz_bottom || 0.486
  const h1 = szTop1 - szBot1 > 0 ? szTop1 - szBot1 : 0.477
  const normZ1 = (p1.z - szBot1) / h1

  const szTop2 = p2.sz_top || 0.963
  const szBot2 = p2.sz_bottom || 0.486
  const h2 = szTop2 - szBot2 > 0 ? szTop2 - szBot2 : 0.477
  const normZ2 = (p2.z - szBot2) / h2

  // 基準好球帶高度 (以基準球 p1 為準)
  const baseH = targetZoneHeightM || h1
  const dzCm = (normZ1 - normZ2) * baseH * 100

  const dist = Math.sqrt(dxCm * dxCm + dzCm * dzCm)
  return Math.round(dist * 10) / 10
}

/**
 * 判斷兩顆球記錄是否為同一顆球
 * @param {object} p1 
 * @param {object} p2 
 * @returns {boolean}
 */
export function isSamePitch(p1, p2) {
  if (!p1 || !p2) return false
  if (p1 === p2) return true
  const pa1 = p1.pa_index ?? p1.pa_num
  const pa2 = p2.pa_index ?? p2.pa_num
  const pIdx1 = p1.pitch_index ?? p1.pitch_num
  const pIdx2 = p2.pitch_index ?? p2.pitch_num
  if (pa1 != null && pa2 != null) {
    if (pa1 !== pa2) return false
    if (pIdx1 != null && pIdx2 != null) {
      return pIdx1 === pIdx2
    }
  }
  if (p1.x != null && p2.x != null && p1.z != null && p2.z != null) {
    return (
      Math.abs(p1.x - p2.x) < 0.0005 &&
      Math.abs(p1.z - p2.z) < 0.0005 &&
      p1.inning_num === p2.inning_num &&
      p1.inning_half === p2.inning_half &&
      p1.called === p2.called
    )
  }
  return false
}

/**
 * 判斷基準球是否主要依據左右邊界 (X 軸) 判定
 * @param {object} pitch 
 * @returns {boolean}
 */
export function isPitchHorizontalDeviation(pitch) {
  if (!pitch || pitch.x == null || pitch.z == null) return false
  const wHalf = 0.22
  const szTop = pitch.sz_top || 0.963
  const szBot = pitch.sz_bottom || 0.486
  const absX = Math.abs(pitch.x)

  const dx = Math.max(0, absX - wHalf)
  let dz = 0
  if (pitch.z > szTop) dz = pitch.z - szTop
  else if (pitch.z < szBot) dz = szBot - pitch.z

  // 若在好球帶外：水平偏差大於等於垂直偏差
  if (dx > 0 || dz > 0) {
    return dx >= dz
  }

  // 若在好球帶內：距離左右側邊界較頂底更近
  const distH = wHalf - absX
  const distV = Math.min(szTop - pitch.z, pitch.z - szBot)
  return distH <= distV
}

/**
 * 找出指定目標球在給定半徑內的所有相似判決球
 * @param {object} targetPitch 目標球物件
 * @param {Array<object>} allPitches 候選球清單
 * @param {number} radiusCm 搜尋半徑 (公分, 預設 7.5)
 * @param {{ viewMode?: 'absolute' | 'batter_relative' }} [options]
 * @returns {Array<object>} 符合半徑內條件的球物件清單 (附帶 distance_to_target_cm，按距離由近至遠排序)
 */
export function findSimilarPitches(targetPitch, allPitches = [], radiusCm = 7.5, options = {}) {
  if (!targetPitch || !Array.isArray(allPitches)) return []

  const viewMode = options.viewMode || 'absolute'
  const isBatterRelative = viewMode === 'batter_relative'
  const targetBats = getBatterBats(targetPitch)

  const results = []
  const targetZoneH = (targetPitch.sz_top && targetPitch.sz_bottom) ? (targetPitch.sz_top - targetPitch.sz_bottom) : null

  for (const p of allPitches) {
    if (isSamePitch(p, targetPitch)) continue

    let comparePitch = p
    let isMirrored = false
    const pBats = getBatterBats(p)

    if (isBatterRelative) {
      // 若為打者對比視角：
      // 同側打者 (L vs L, R vs R) -> 保持原座標 (p.x, p.z)
      // 異側打者 (L vs R, R vs L) -> 水平座標鏡像翻轉 (-p.x, p.z)
      if (targetBats !== 'S' && pBats !== 'S' && targetBats !== pBats) {
        comparePitch = {
          ...p,
          x: -p.x
        }
        isMirrored = true
      }
    }

    const distanceCm = calculateDistanceCm(targetPitch, comparePitch, targetZoneH)
    if (distanceCm <= radiusCm) {
      results.push({
        ...p,
        distance_to_target_cm: distanceCm,
        is_mirrored: isMirrored,
        effective_x: comparePitch.x,
        batter_bats: pBats,
        target_bats: targetBats
      })
    }
  }

  return results.sort((a, b) => a.distance_to_target_cm - b.distance_to_target_cm)
}

/**
 * 分析目標球周圍類似進壘點的主審判決一致性與好球帶傾向
 * @param {object} targetPitch 
 * @param {Array<object>} similarPitches 
 * @returns {object} 統計與診斷結果
 */
export function analyzeConsistency(targetPitch, similarPitches = []) {
  const neighborCount = similarPitches.length
  if (neighborCount === 0) {
    return {
      totalCount: targetPitch ? 1 : 0,
      strikeCount: targetPitch?.called === 'STRIKE' ? 1 : 0,
      ballCount: targetPitch?.called === 'BALL' ? 1 : 0,
      strikeRate: targetPitch?.called === 'STRIKE' ? 100 : 0,
      ballRate: targetPitch?.called === 'BALL' ? 100 : 0,
      sameCallCount: 0,
      oppositeCallCount: 0,
      isConflicting: false,
      diagnosisType: 'isolated',
      diagnosis: '此區域無其他判決可供比對（孤立點）'
    }
  }

  // 包含基準球與鄰近球的完整區域判決統計
  const allClusterPitches = targetPitch ? [targetPitch, ...similarPitches] : similarPitches
  const total = allClusterPitches.length

  const strikeCount = allClusterPitches.filter(p => p.called === 'STRIKE').length
  const ballCount = allClusterPitches.filter(p => p.called === 'BALL').length
  const strikeRate = Math.round((strikeCount / total) * 1000) / 10
  const ballRate = Math.round((ballCount / total) * 1000) / 10

  const sameCallCount = similarPitches.filter(p => p.called === targetPitch?.called).length
  const oppositeCallCount = neighborCount - sameCallCount
  const isConflicting = oppositeCallCount > 0

  let diagnosis
  let diagnosisType

  const targetCalled = targetPitch?.called
  const targetTrue = targetPitch?.true_call

  if (targetCalled === 'BALL' && targetTrue === 'STRIKE') {
    // 實為好球卻判壞球 (漏判好球)
    if (ballCount === total) {
      diagnosis = `主審在此區域標準一致（偏窄）：同區域 ${total} 顆均判壞球（含基準球）`
      diagnosisType = 'strict'
    } else {
      diagnosis = `執法標準矛盾（雙標）：同區域有 ${ballCount} 顆判壞球、${strikeCount} 顆判好球（含基準球）`
      diagnosisType = 'conflict'
    }
  } else if (targetCalled === 'STRIKE' && targetTrue === 'BALL') {
    // 實為壞球卻判好球 (擴大好球帶)
    if (strikeCount === total) {
      diagnosis = `主審在此區域標準一致（偏寬）：同區域 ${total} 顆均判好球（含基準球）`
      diagnosisType = 'generous'
    } else {
      diagnosis = `執法標準矛盾（雙標）：同區域有 ${ballCount} 顆判壞球、${strikeCount} 顆判好球（含基準球）`
      diagnosisType = 'conflict'
    }
  } else {
    // 正常判決比對
    if (isConflicting) {
      diagnosis = `同區域存在不同判決（共 ${strikeCount} 好 / ${ballCount} 壞）`
      diagnosisType = 'conflict'
    } else {
      diagnosis = `主審在此區域判決百分之百一致（共 ${total} 顆）`
      diagnosisType = 'consistent'
    }
  }

  return {
    totalCount: total,
    strikeCount,
    ballCount,
    strikeRate,
    ballRate,
    sameCallCount,
    oppositeCallCount,
    isConflicting,
    diagnosisType,
    diagnosis
  }
}

/**
 * 計算全場判決一致性 (Method A：鄰域球對比對法)
 * 找出全場所有距離 <= radiusCm 的判決球對，計算判決相同 (同好或同壞) 的比率
 * @param {Array<object>} allPitches 該場比賽所有判決球
 * @param {number} radiusCm 鄰近比對半徑 (公分, 預設 7.5)
 * @returns {{
 *   consistencyRate: number,
 *   consistentPairs: number,
 *   totalPairs: number,
 *   conflictingPitchesCount: number,
 *   isolatedCount: number,
 *   totalPitches: number,
 *   ratioStr: string
 * }}
 */
export function calculateGameConsistency(allPitches = [], radiusCm = 7.5) {
  if (!Array.isArray(allPitches) || allPitches.length <= 1) {
    const total = Array.isArray(allPitches) ? allPitches.length : 0
    return {
      consistencyRate: 100.0,
      consistentPairs: 0,
      totalPairs: 0,
      conflictingPitchesCount: 0,
      isolatedCount: total,
      totalPitches: total,
      ratioStr: '0/0'
    }
  }

  const validPitches = allPitches.filter(p => p && p.x != null && p.z != null && p.called)
  const n = validPitches.length

  if (n <= 1) {
    return {
      consistencyRate: 100.0,
      consistentPairs: 0,
      totalPairs: 0,
      conflictingPitchesCount: 0,
      isolatedCount: n,
      totalPitches: n,
      ratioStr: '0/0'
    }
  }

  let totalPairs = 0
  let consistentPairs = 0
  const conflictingPitchesSet = new Set()
  const hasNeighborSet = new Set()

  for (let i = 0; i < n; i++) {
    const p1 = validPitches[i]
    const targetZoneH = (p1.sz_top && p1.sz_bottom && p1.sz_top > p1.sz_bottom)
      ? (p1.sz_top - p1.sz_bottom)
      : null

    for (let j = i + 1; j < n; j++) {
      const p2 = validPitches[j]
      if (isSamePitch(p1, p2)) continue

      const dist = calculateDistanceCm(p1, p2, targetZoneH)
      if (dist <= radiusCm) {
        totalPairs++
        hasNeighborSet.add(i)
        hasNeighborSet.add(j)

        if (p1.called === p2.called) {
          consistentPairs++
        } else {
          conflictingPitchesSet.add(i)
          conflictingPitchesSet.add(j)
        }
      }
    }
  }

  const isolatedCount = n - hasNeighborSet.size
  const consistencyRate = totalPairs > 0
    ? Math.round((consistentPairs / totalPairs) * 1000) / 10
    : 100.0

  return {
    consistencyRate,
    consistentPairs,
    totalPairs,
    conflictingPitchesCount: conflictingPitchesSet.size,
    isolatedCount,
    totalPitches: n,
    ratioStr: `${consistentPairs}/${totalPairs}`
  }
}
