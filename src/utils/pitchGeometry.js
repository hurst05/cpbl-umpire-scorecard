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
 * 找出指定目標球在給定半徑內的所有相似判決球
 * @param {object} targetPitch 目標球物件
 * @param {Array<object>} allPitches 候選球清單
 * @param {number} radiusCm 搜尋半徑 (公分, 預設 8.0)
 * @returns {Array<object>} 符合半徑內條件的球物件清單 (附帶 distance_to_target_cm，按距離由近至遠排序)
 */
export function findSimilarPitches(targetPitch, allPitches = [], radiusCm = 8.0) {
  if (!targetPitch || !Array.isArray(allPitches)) return []

  const results = []
  const targetPa = targetPitch.pa_index ?? targetPitch.pa_num
  const targetPitchIdx = targetPitch.pitch_index ?? targetPitch.pitch_num
  const targetZoneH = (targetPitch.sz_top && targetPitch.sz_bottom) ? (targetPitch.sz_top - targetPitch.sz_bottom) : null

  for (const p of allPitches) {
    const pPa = p.pa_index ?? p.pa_num
    const pPitchIdx = p.pitch_index ?? p.pitch_num

    // 排除同一顆球 (若記憶體相同、或 PA 與球數序號皆相同、或座標相同且為同局同打席)
    const isSamePitch = 
      p === targetPitch ||
      (targetPa != null && pPa != null && targetPa === pPa && targetPitchIdx != null && pPitchIdx != null && targetPitchIdx === pPitchIdx) ||
      (Math.abs(p.x - targetPitch.x) < 0.0005 && Math.abs(p.z - targetPitch.z) < 0.0005 && p.inning_num === targetPitch.inning_num && p.inning_half === targetPitch.inning_half && p.pitcher === targetPitch.pitcher && p.batter === targetPitch.batter && p.called === targetPitch.called)

    if (isSamePitch) continue

    const distanceCm = calculateDistanceCm(targetPitch, p, targetZoneH)
    if (distanceCm <= radiusCm) {
      results.push({
        ...p,
        distance_to_target_cm: distanceCm
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
  const total = similarPitches.length
  if (total === 0) {
    return {
      totalCount: 0,
      strikeCount: 0,
      ballCount: 0,
      strikeRate: 0,
      ballRate: 0,
      sameCallCount: 0,
      oppositeCallCount: 0,
      isConflicting: false,
      diagnosisType: 'isolated',
      diagnosis: '此區域無其他判決可供比對（孤立點）'
    }
  }

  const strikeCount = similarPitches.filter(p => p.called === 'STRIKE').length
  const ballCount = similarPitches.filter(p => p.called === 'BALL').length
  const strikeRate = Math.round((strikeCount / total) * 1000) / 10
  const ballRate = Math.round((ballCount / total) * 1000) / 10

  const sameCallCount = similarPitches.filter(p => p.called === targetPitch.called).length
  const oppositeCallCount = total - sameCallCount
  const isConflicting = oppositeCallCount > 0

  let diagnosis
  let diagnosisType

  const targetCalled = targetPitch?.called
  const targetTrue = targetPitch?.true_call

  if (targetCalled === 'BALL' && targetTrue === 'STRIKE') {
    // 實為好球卻判壞球 (漏判好球)
    if (ballCount === total) {
      diagnosis = `主審在此區域標準一致（偏窄）：周圍 ${total} 顆均判壞球`
      diagnosisType = 'strict'
    } else {
      diagnosis = `執法標準矛盾（雙標）：同區域有 ${strikeCount} 顆被判好球、${ballCount} 顆被判壞球`
      diagnosisType = 'conflict'
    }
  } else if (targetCalled === 'STRIKE' && targetTrue === 'BALL') {
    // 實為壞球卻判好球 (擴大好球帶)
    if (strikeCount === total) {
      diagnosis = `主審在此區域標準一致（偏寬）：周圍 ${total} 顆均判好球`
      diagnosisType = 'generous'
    } else {
      diagnosis = `執法標準矛盾（雙標）：同區域有 ${ballCount} 顆被判壞球、${strikeCount} 顆被判好球`
      diagnosisType = 'conflict'
    }
  } else {
    // 正常判決比對
    if (isConflicting) {
      diagnosis = `同區域存在不同判決（${strikeCount} 好 / ${ballCount} 壞）`
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
