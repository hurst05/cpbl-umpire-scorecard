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
 * Fetch available years / seasons
 */
export async function fetchAvailableYears() {
  if (isStaticMode()) {
    const manifest = await fetchManifest()
    if (manifest.available_years && manifest.available_years.length > 0) {
      return manifest.available_years
    }
    const years = Array.from(
      new Set(
        (manifest.games || [])
          .map(g => (g.game_date ? g.game_date.slice(0, 4) : ''))
          .filter(Boolean)
      )
    ).map(Number).sort((a, b) => b - a)
    return years
  } else {
    try {
      const res = await fetch('/api/seasons')
      if (!res.ok) {
        throw new Error(`無法取得年度清單 (${res.statusText})`)
      }
      const data = await res.json()
      return data.seasons || []
    } catch (e) {
      console.warn('[dataService] Failed to load /api/seasons, fallback:', e)
      const games = await fetchGameList()
      const years = Array.from(
        new Set(
          games
            .map(g => (g.game_date ? g.game_date.slice(0, 4) : ''))
            .filter(Boolean)
        )
      ).map(Number).sort((a, b) => b - a)
      return years
    }
  }
}

/**
 * Fetch all available / cached games summary list with optional year filter
 */
export async function fetchGameList(year = null) {
  const targetYear = (!year || year === 'all' || year === '全部') ? null : String(year)
  if (isStaticMode()) {
    const manifest = await fetchManifest()
    const allGames = manifest.games || []
    if (!targetYear) {
      return allGames
    }
    return allGames.filter(g => g.game_date && g.game_date.startsWith(targetYear))
  } else {
    const url = targetYear
      ? `/api/games/cached?year=${encodeURIComponent(targetYear)}`
      : '/api/games/cached'
    const res = await fetch(url)
    if (!res.ok) {
      throw new Error(`無法取得本機快取賽事 (${res.statusText})`)
    }
    return res.json()
  }
}

/**
 * Fetch aggregated season stats for a given year (or 'all')
 */
export async function fetchSeasonStats(year = '2026') {
  const targetYear = (!year || year === 'all' || year === '全部') ? 'all' : String(year)
  if (isStaticMode()) {
    const baseUrl = getBaseUrl()
    const url = `${baseUrl}data/stats/${encodeURIComponent(targetYear)}.json`
    try {
      const res = await fetch(url)
      if (res.ok) {
        return await res.json()
      }
    } catch (e) {
      console.warn(`[dataService] Static stats ${targetYear}.json not found, computing on client...`, e)
    }

    // Fallback: Compute stats directly from manifest games on client
    const manifest = await fetchManifest()
    const games = targetYear === 'all'
      ? (manifest.games || [])
      : (manifest.games || []).filter(g => g.game_date && g.game_date.startsWith(targetYear))
    return computeStatsFromGames(games, targetYear === 'all' ? '全部' : targetYear)
  } else {
    const res = await fetch(`/api/stats/season/${encodeURIComponent(targetYear)}`)
    if (!res.ok) {
      throw new Error(`無法取得年度統計數據 (${res.statusText})`)
    }
    return res.json()
  }
}

/**
 * Client-side calculation helper for season statistics
 */
function computeStatsFromGames(games, yearLabel) {
  if (!games || games.length === 0) {
    return {
      year: yearLabel,
      total_games: 0,
      duration: { avg_minutes: 0, formatted_avg: '無資料', valid_games_count: 0, shortest_game: null, longest_game: null },
      scores: {
        avg_margin: 0.0, avg_winner_score: 0.0, avg_loser_score: 0.0, avg_total_runs: 0.0,
        total_runs: 0, one_run_games_count: 0, one_run_games_pct: 0.0, blowout_games_count: 0,
        blowout_games_pct: 0.0, tie_games_count: 0, margin_distribution: { '1': 0, '2': 0, '3-4': 0, '5+': 0 }
      },
      home_away: { home_wins: 0, visiting_wins: 0, ties: 0, home_win_pct: 0.0, visiting_win_pct: 0.0 },
      umpire_summary: { avg_overall_acc: 0.0, avg_ball_acc: 0.0, avg_strike_acc: 0.0, avg_missed_calls: 0.0, total_missed_calls: 0, highest_acc_game: null, lowest_acc_game: null },
      umpire_leaderboard: [],
      team_standings: [],
      stadium_stats: []
    }
  }

  const totalGames = games.length
  const durations = []
  const durGames = []
  let homeWins = 0
  let visitingWins = 0
  let tieCount = 0
  let oneRunCount = 0
  let blowoutCount = 0
  const marginDist = { '1': 0, '2': 0, '3-4': 0, '5+': 0 }

  let totalMargin = 0
  let totalWinnerScore = 0
  let totalLoserScore = 0
  let totalRuns = 0

  let totalOverallAcc = 0
  let totalBallAcc = 0
  let totalStrikeAcc = 0
  let totalMissed = 0

  const umpireMap = {}
  const teamMap = {}
  const stadiumMap = {}

  let highestAccGame = null
  let lowestAccGame = null

  games.forEach(g => {
    const dur = g.game_duration_minutes
    if (dur && dur > 0) {
      durations.push(dur)
      durGames.push(g)
    }

    const hScore = Number(g.home_score) || 0
    const vScore = Number(g.visiting_score) || 0
    const hTeam = g.home_team || '主隊'
    const vTeam = g.visiting_team || '客隊'
    const stadium = g.field || '未知球場'
    const umpire = g.hp_umpire || '未知主審'

    const overallAcc = Number(g.overall_acc) || 0
    const ballAcc = Number(g.ball_acc) || 0
    const strikeAcc = Number(g.strike_acc) || 0
    const missed = Number(g.missed_count) || 0

    const margin = Math.abs(hScore - vScore)
    const wScore = Math.max(hScore, vScore)
    const lScore = Math.min(hScore, vScore)
    const gameRuns = hScore + vScore

    totalMargin += margin
    totalWinnerScore += wScore
    totalLoserScore += lScore
    totalRuns += gameRuns

    totalOverallAcc += overallAcc
    totalBallAcc += ballAcc
    totalStrikeAcc += strikeAcc
    totalMissed += missed

    if (margin === 0) {
      tieCount++
    } else if (margin === 1) {
      oneRunCount++
      marginDist['1']++
    } else if (margin === 2) {
      marginDist['2']++
    } else if (margin === 3 || margin === 4) {
      marginDist['3-4']++
    } else {
      marginDist['5+']++
    }

    if (margin >= 5) blowoutCount++
    if (hScore > vScore) homeWins++
    else if (vScore > hScore) visitingWins++

    const gameAccInfo = {
      game_id: g.game_id,
      game_sno: g.game_sno,
      date: g.game_date,
      matchup: `${vTeam} vs ${hTeam}`,
      hp_umpire: umpire,
      overall_acc: overallAcc,
      missed_count: missed
    }
    if (!highestAccGame || overallAcc > highestAccGame.overall_acc) highestAccGame = gameAccInfo
    if (!lowestAccGame || overallAcc < lowestAccGame.overall_acc) lowestAccGame = gameAccInfo

    // Umpire map
    if (!umpireMap[umpire]) {
      umpireMap[umpire] = { name: umpire, games: 0, totalOverall: 0, totalBall: 0, totalStrike: 0, totalMissed: 0 }
    }
    const u = umpireMap[umpire]
    u.games++
    u.totalOverall += overallAcc
    u.totalBall += ballAcc
    u.totalStrike += strikeAcc
    u.totalMissed += missed

    // Team map
    ;[
      { name: hTeam, isHome: true, scored: hScore, allowed: vScore },
      { name: vTeam, isHome: false, scored: vScore, allowed: hScore }
    ].forEach(({ name, isHome, scored, allowed }) => {
      if (!teamMap[name]) {
        teamMap[name] = { team: name, games: 0, wins: 0, losses: 0, ties: 0, runsScored: 0, runsAllowed: 0, oneRunWins: 0, oneRunLosses: 0, homeGames: 0, homeWins: 0, awayGames: 0, awayWins: 0 }
      }
      const t = teamMap[name]
      t.games++
      t.runsScored += scored
      t.runsAllowed += allowed
      if (isHome) t.homeGames++
      else t.awayGames++

      if (scored > allowed) {
        t.wins++
        if (isHome) t.homeWins++
        else t.awayWins++
        if (margin === 1) t.oneRunWins++
      } else if (scored < allowed) {
        t.losses++
        if (margin === 1) t.oneRunLosses++
      } else {
        t.ties++
      }
    })

    // Stadium map
    if (!stadiumMap[stadium]) {
      stadiumMap[stadium] = { field: stadium, games: 0, totalRuns: 0, durations: [], totalAcc: 0 }
    }
    const s = stadiumMap[stadium]
    s.games++
    s.totalRuns += gameRuns
    s.totalAcc += overallAcc
    if (dur && dur > 0) s.durations.push(dur)
  })

  const avgDurMins = durations.length > 0 ? Math.round((durations.reduce((a, b) => a + b, 0) / durations.length) * 10) / 10 : 0
  const formatDur = (mins) => {
    if (!mins || mins <= 0) return '無資料'
    const totalMins = Math.round(mins)
    const h = Math.floor(totalMins / 60)
    const m = totalMins % 60
    return h > 0 ? `${h}小時 ${m}分` : `${m}分`
  }

  const decidedGames = homeWins + visitingWins
  const homeWinPct = decidedGames > 0 ? Math.round((homeWins / decidedGames) * 1000) / 10 : 0
  const visitingWinPct = decidedGames > 0 ? Math.round((visitingWins / decidedGames) * 1000) / 10 : 0

  const umpireLeaderboard = Object.values(umpireMap).map(u => ({
    hp_umpire: u.name,
    games: u.games,
    overall_acc: Math.round((u.totalOverall / u.games) * 100) / 100,
    ball_acc: Math.round((u.totalBall / u.games) * 100) / 100,
    strike_acc: Math.round((u.totalStrike / u.games) * 100) / 100,
    total_missed: u.totalMissed,
    missed_per_game: Math.round((u.totalMissed / u.games) * 10) / 10
  })).sort((a, b) => b.games - a.games || b.overall_acc - a.overall_acc)

  const teamStandings = Object.values(teamMap).map(t => {
    const decided = t.wins + t.losses
    const winRate = decided > 0 ? Math.round((t.wins / decided) * 1000) / 1000 : 0
    const oneRunTotal = t.oneRunWins + t.oneRunLosses
    const oneRunWinRate = oneRunTotal > 0 ? Math.round((t.oneRunWins / oneRunTotal) * 1000) / 1000 : 0
    return {
      team: t.team,
      games: t.games,
      wins: t.wins,
      losses: t.losses,
      ties: t.ties,
      win_rate: winRate,
      win_rate_str: winRate < 1 ? winRate.toFixed(3).replace(/^0/, '') : '1.000',
      runs_scored: t.runsScored,
      runs_allowed: t.runsAllowed,
      run_diff: t.runsScored - t.runsAllowed,
      avg_runs_scored: Math.round((t.runsScored / t.games) * 100) / 100,
      avg_runs_allowed: Math.round((t.runsAllowed / t.games) * 100) / 100,
      one_run_record: `${t.oneRunWins}勝-${t.oneRunLosses}敗`,
      one_run_win_rate: oneRunWinRate,
      home_record: `${t.homeWins}勝-${t.homeGames - t.homeWins}敗`,
      away_record: `${t.awayWins}勝-${t.awayGames - t.awayWins}敗`
    }
  }).sort((a, b) => b.win_rate - a.win_rate || b.run_diff - a.run_diff)

  const stadiumStats = Object.values(stadiumMap).map(s => {
    const sAvgDur = s.durations.length > 0 ? Math.round((s.durations.reduce((a, b) => a + b, 0) / s.durations.length) * 10) / 10 : 0
    return {
      field: s.field,
      games: s.games,
      avg_duration_minutes: sAvgDur,
      formatted_avg_duration: formatDur(sAvgDur),
      avg_total_runs: Math.round((s.totalRuns / s.games) * 100) / 100,
      avg_accuracy: Math.round((s.totalAcc / s.games) * 100) / 100
    }
  }).sort((a, b) => b.games - a.games)

  return {
    year: yearLabel,
    total_games: totalGames,
    duration: {
      avg_minutes: avgDurMins,
      formatted_avg: formatDur(avgDurMins),
      valid_games_count: durations.length,
      shortest_game: null,
      longest_game: null
    },
    scores: {
      avg_margin: Math.round((totalMargin / totalGames) * 100) / 100,
      avg_winner_score: Math.round((totalWinnerScore / totalGames) * 100) / 100,
      avg_loser_score: Math.round((totalLoserScore / totalGames) * 100) / 100,
      avg_total_runs: Math.round((totalRuns / totalGames) * 100) / 100,
      total_runs: totalRuns,
      one_run_games_count: oneRunCount,
      one_run_games_pct: Math.round((oneRunCount / totalGames) * 1000) / 10,
      blowout_games_count: blowoutCount,
      blowout_games_pct: Math.round((blowoutCount / totalGames) * 1000) / 10,
      tie_games_count: tieCount,
      margin_distribution: marginDist
    },
    home_away: {
      home_wins: homeWins,
      visiting_wins: visitingWins,
      ties: tieCount,
      home_win_pct: homeWinPct,
      visiting_win_pct: visitingWinPct
    },
    umpire_summary: {
      avg_overall_acc: Math.round((totalOverallAcc / totalGames) * 100) / 100,
      avg_ball_acc: Math.round((totalBallAcc / totalGames) * 100) / 100,
      avg_strike_acc: Math.round((totalStrikeAcc / totalGames) * 100) / 100,
      avg_missed_calls: Math.round((totalMissed / totalGames) * 10) / 10,
      total_missed_calls: totalMissed,
      highest_acc_game: highestAccGame,
      lowest_acc_game: lowestAccGame
    },
    umpire_leaderboard: umpireLeaderboard,
    team_standings: teamStandings,
    stadium_stats: stadiumStats
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
