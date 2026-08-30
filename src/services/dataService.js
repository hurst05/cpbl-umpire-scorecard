/**
 * CPBL Scorecard Data Service
 * Supports Dual-Mode:
 * - Local Mode ('api'): Communicates with FastAPI backend for on-demand fetch & batch collection
 * - Static Mode ('static'): Reads pre-generated static JSON files from public/data/ or dist/data/
 */

import { isGameInManifest, validateGameDetail } from './staticDataValidation'

const dataMode = import.meta.env.VITE_DATA_MODE || (import.meta.env.DEV ? 'api' : 'static')

if (!['api', 'static'].includes(dataMode)) {
  throw new Error(`Unsupported data mode: ${dataMode}`)
}

export function isStaticMode() {
  return dataMode === 'static'
}

export function getDataMode() {
  return dataMode
}

function getBaseUrl() {
  const base = import.meta.env.BASE_URL || '/'
  return base.endsWith('/') ? base : `${base}/`
}

let cachedManifestPromise = null

export function _resetManifestCache() {
  cachedManifestPromise = null
}

/**
 * Fetch manifest.json with validation & promise caching (Static mode only)
 */
export async function fetchManifest() {
  if (!isStaticMode()) {
    throw new Error('fetchManifest 僅可在 static 模式下使用')
  }

  if (cachedManifestPromise) {
    return cachedManifestPromise
  }

  cachedManifestPromise = (async () => {
    const baseUrl = getBaseUrl()
    const url = `${baseUrl}data/manifest.json`

    let res
    try {
      res = await fetch(url)
    } catch (e) {
      throw new Error(`網路連線異常，無法載入賽事索引: ${e.message}`, { cause: e })
    }

    if (!res.ok) {
      throw new Error(`無法載入賽事索引清單 (HTTP ${res.status})`)
    }

    let manifest
    try {
      manifest = await res.json()
    } catch (e) {
      throw new Error(`賽事索引清單 (manifest.json) 格式損壞: ${e.message}`, { cause: e })
    }

    if (
      !manifest ||
      typeof manifest !== 'object' ||
      manifest.schema_version !== 1 ||
      !Array.isArray(manifest.games)
    ) {
      throw new Error(
        `賽事索引版本或結構不相容 (schema_version: ${manifest ? manifest.schema_version : 'unknown'})`
      )
    }

    return manifest
  })()

  try {
    return await cachedManifestPromise
  } catch (err) {
    // Clear cache on error so subsequent attempts can retry
    cachedManifestPromise = null
    throw err
  }
}

/**
 * Fetch all available / cached games summary list
 */
export async function fetchGameList() {
  if (isStaticMode()) {
    const manifest = await fetchManifest()
    return manifest.games || []
  } else {
    const res = await fetch('/api/games/cached')
    if (!res.ok) {
      throw new Error(`無法取得本機快取賽事 (${res.statusText})`)
    }
    return res.json()
  }
}

/**
 * Get the default initial game ID to load
 */
export async function fetchDefaultGameId() {
  if (isStaticMode()) {
    const manifest = await fetchManifest()
    return manifest.default_game_id || null
  } else {
    try {
      const res = await fetch('/api/games/cached')
      if (res.ok) {
        const games = await res.json()
        if (games && games.length > 0) {
          return games[0].game_id
        }
      }
    } catch (e) {
      console.warn('[dataService] Failed to load cached games for default ID:', e)
    }
    return null
  }
}

/**
 * Fetch full analysis JSON for a specific game
 */
export async function fetchGame(gameId) {
  if (!gameId) {
    throw new Error('請提供欲查詢的場次 ID')
  }

  if (isStaticMode()) {
    // Check manifest first as authoritative index
    const manifest = await fetchManifest()
    if (!isGameInManifest(manifest, gameId)) {
      const err = new Error(`此場次 (${gameId}) 尚未發布。`)
      err.isNotFound = true
      throw err
    }

    const baseUrl = getBaseUrl()
    const url = `${baseUrl}data/games/${encodeURIComponent(gameId)}.json`

    let res
    try {
      res = await fetch(url)
    } catch (e) {
      throw new Error(`網路連線異常，無法載入賽事: ${e.message}`, { cause: e })
    }

    if (res.status === 404) {
      const err = new Error(`此場次 (${gameId}) 尚未發布。`)
      err.isNotFound = true
      throw err
    }
    if (!res.ok) {
      throw new Error(`載入已發布賽事失敗 (HTTP ${res.status})`)
    }

    let detail
    try {
      detail = await res.json()
    } catch (e) {
      const err = new Error(`賽事資料 (${gameId}) 格式損壞: ${e.message}`, { cause: e })
      err.isCorrupted = true
      throw err
    }

    validateGameDetail(detail, gameId)
    return detail
  } else {
    const res = await fetch(`/api/game/${encodeURIComponent(gameId)}`)
    if (!res.ok) {
      throw new Error(`擷取賽事資料失敗 (${res.statusText})`)
    }
    return res.json()
  }
}

/**
 * Fetch game by sno
 */
export async function fetchGameBySno(sno, year = 2026, kindCode = 'A') {
  if (!sno) return null
  const gameId = `${year}-${kindCode}-${sno}`
  return fetchGame(gameId)
}

/**
 * Run batch collect for a given date (Local API mode only)
 */
export async function runBatchCollect(dateStr) {
  if (isStaticMode()) {
    throw new Error('線上靜態模式不支援即時批次抓取，請於本機執行。')
  }
  const res = await fetch(`/api/batch-collect?date=${encodeURIComponent(dateStr)}`, {
    method: 'POST'
  })
  if (!res.ok) {
    throw new Error(`批次抓取失敗 (${res.statusText})`)
  }
  return res.json()
}
