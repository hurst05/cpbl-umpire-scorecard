/**
 * Pure validation helper functions for static scorecard data
 * Independent of DOM, window, and build-time env
 */

/**
 * Check if a game ID exists in manifest games list
 * @param {object} manifest
 * @param {string} gameId
 * @returns {boolean}
 */
export function isGameInManifest(manifest, gameId) {
  if (!manifest || !Array.isArray(manifest.games) || !gameId) {
    return false
  }
  return manifest.games.some(g => g && typeof g === 'object' && g.game_id === gameId)
}

/**
 * Validate game detail top-level contract
 * @param {any} detail
 * @param {string} gameId
 * @returns {boolean}
 */
export function validateGameDetail(detail, gameId) {
  const targetId = gameId || 'unknown'

  if (!detail || typeof detail !== 'object' || Array.isArray(detail)) {
    const err = new Error(`賽事資料 (${targetId}) 格式損壞: 根節點必須為物件`)
    err.isCorrupted = true
    throw err
  }

  const { game_info, umpire_metrics, plate_appearances, all_called_pitches } = detail

  if (!game_info || typeof game_info !== 'object' || Array.isArray(game_info)) {
    const err = new Error(`賽事資料 (${targetId}) 格式損壞: game_info 必須為物件`)
    err.isCorrupted = true
    throw err
  }

  if (!umpire_metrics || typeof umpire_metrics !== 'object' || Array.isArray(umpire_metrics)) {
    const err = new Error(`賽事資料 (${targetId}) 格式損壞: umpire_metrics 必須為物件`)
    err.isCorrupted = true
    throw err
  }

  if (!Array.isArray(plate_appearances)) {
    const err = new Error(`賽事資料 (${targetId}) 格式損壞: plate_appearances 必須為陣列`)
    err.isCorrupted = true
    throw err
  }

  if (!Array.isArray(all_called_pitches)) {
    const err = new Error(`賽事資料 (${targetId}) 格式損壞: all_called_pitches 必須為陣列`)
    err.isCorrupted = true
    throw err
  }

  return true
}
