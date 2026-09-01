<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col transition-colors duration-200">
    <!-- Navbar Header -->
    <header class="sticky top-0 z-40 bg-white/95 dark:bg-slate-900/95 border-b border-slate-200 dark:border-slate-800 backdrop-blur-md px-4 lg:px-8 py-2.5 flex items-center justify-between gap-3 shadow-xs dark:shadow-none transition-colors overflow-x-auto">
      <!-- Brand Logo & Title -->
      <div class="flex items-center gap-2.5 shrink-0">
        <div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-black text-white text-base shadow-sm shadow-blue-500/20">
          CP
        </div>
        <div class="flex items-center gap-2">
          <h1 class="text-sm sm:text-base font-black tracking-tight text-slate-900 dark:text-white whitespace-nowrap">
            CPBL 逐球數據與主審分析系統
          </h1>
          <span class="hidden sm:inline-block text-[10px] px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-500/30 font-bold whitespace-nowrap">Trackman</span>
        </div>
      </div>

      <!-- Quick Search Bar with Keyboard +/- Support and Clean Styling -->
      <div class="flex items-center gap-2 shrink-0">
        <div class="relative flex items-center">
          <input 
            type="number"
            min="1"
            max="400"
            v-model.number="inputSno"
            placeholder="輸入場次 (例: 295)" 
            class="px-3 py-1.5 pr-14 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-xs text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono w-36 transition-colors"
            @keydown="handleKeydown"
            title="可用鍵盤 ↑ / ↓ 或 + / - 切換場次，按 Enter 搜尋"
          />
          <button 
            @click="loadGameBySno"
            :disabled="isLoading"
            class="absolute right-1 px-2.5 py-1 rounded bg-blue-600 hover:bg-blue-500 text-[11px] font-bold text-white transition-all disabled:opacity-50 shadow-sm"
          >
            搜尋
          </button>
        </div>

        <!-- Theme Toggle Button -->
        <button 
          @click="toggleTheme" 
          class="px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 transition-all flex items-center gap-1 text-xs font-medium shrink-0 shadow-xs cursor-pointer"
          :title="isDark ? '切換為淺色模式' : '切換為深色模式'"
        >
          <span>{{ isDark ? '☀️ 淺色' : '🌙 深色' }}</span>
        </button>
      </div>

      <!-- Navigation Tabs -->
      <div class="flex items-center gap-1 bg-slate-100 dark:bg-slate-800/80 p-1 rounded-xl border border-slate-200 dark:border-slate-700/80 text-xs shrink-0">
        <button 
          @click="activeTab = 'multi-game'"
          :class="['px-3 py-1.5 rounded-lg font-bold transition-all whitespace-nowrap cursor-pointer', activeTab === 'multi-game' ? 'bg-blue-600 text-white shadow-xs' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white']"
        >
          跨場次數據庫
        </button>
        <button 
          @click="activeTab = 'season-stats'"
          :class="['px-3 py-1.5 rounded-lg font-bold transition-all whitespace-nowrap cursor-pointer', activeTab === 'season-stats' ? 'bg-blue-600 text-white shadow-xs' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white']"
        >
          年度數據統計
        </button>
        <button 
          @click="activeTab = 'scorecard'"
          :class="['px-3 py-1.5 rounded-lg font-bold transition-all whitespace-nowrap cursor-pointer', activeTab === 'scorecard' ? 'bg-blue-600 text-white shadow-xs' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white']"
        >
          主審評分卡
        </button>
        <button 
          @click="activeTab = 'at-bat'"
          :class="['px-3 py-1.5 rounded-lg font-bold transition-all whitespace-nowrap cursor-pointer', activeTab === 'at-bat' ? 'bg-blue-600 text-white shadow-xs' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white']"
        >
          逐打席檢視
        </button>
      </div>
    </header>

    <!-- Main Body -->
    <main class="flex-1 max-w-[1440px] w-full mx-auto p-4 lg:p-6 flex flex-col gap-5">
      <!-- Loading State for Single Game Views -->
      <div v-if="isLoading && isSingleGameTab" class="flex flex-col items-center justify-center py-24 gap-3">
        <div class="w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <span class="text-sm font-medium text-slate-500 dark:text-slate-400">
          {{ isStatic ? '正在載入已發布賽事數據...' : '正在直接從 CPBL 官方進階數據網擷取並解析賽事數據...' }}
        </span>
      </div>

      <!-- Error State for Single Game Views -->
      <div v-else-if="errorMessage && isSingleGameTab" class="p-4 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500/50 text-red-700 dark:text-red-300 text-sm flex items-center justify-between gap-4">
        <span>{{ errorMessage }}</span>
        <button
          v-if="defaultGameId && gameData?.game_info?.game_id !== defaultGameId"
          @click="loadDefaultGame"
          class="underline font-bold shrink-0 hover:text-red-900 dark:hover:text-red-200 cursor-pointer"
        >
          返回預設場次 ({{ defaultGameId }})
        </button>
      </div>

      <template v-else>
        <!-- Game Summary Banner (Shown on Single Game tabs: scorecard / at-bat) -->
        <div v-if="gameData && isSingleGameTab" class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 sm:p-5 shadow-xs dark:shadow-xl flex flex-col md:flex-row items-center justify-between gap-4 transition-colors">
          <div class="flex flex-wrap items-center gap-3">
            <span class="px-2.5 py-1 rounded-md bg-blue-50 dark:bg-blue-600/20 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-500/30 text-xs font-mono font-bold">
              例行賽 第 {{ gameData.game_info.game_sno }} 場
            </span>
            <span class="text-xs text-slate-600 dark:text-slate-400">
              日期：<strong class="text-slate-900 dark:text-white">{{ gameData.game_info.date }}</strong> | 地點：<strong class="text-slate-900 dark:text-white">{{ gameData.game_info.field }}</strong>
            </span>
            <span class="text-xs text-slate-600 dark:text-slate-400">
              主審：<strong class="text-amber-600 dark:text-amber-400">{{ gameData.game_info.hp_umpire }}</strong>
            </span>
            <span v-if="gameData.game_info.game_duration_minutes" class="text-xs text-slate-600 dark:text-slate-400">
              比賽時間：<strong class="text-blue-600 dark:text-blue-400 font-mono">{{ formatMinutes(gameData.game_info.game_duration_minutes) }}</strong>
            </span>
          </div>

          <!-- Teams & Score Matchup -->
          <div class="flex items-center gap-5">
            <div class="text-right">
              <div class="text-base sm:text-lg font-black text-slate-900 dark:text-white">{{ gameData.game_info.visiting_team }}</div>
              <div class="text-[11px] text-slate-500 dark:text-slate-400">客隊</div>
            </div>
            <div class="flex items-center gap-2.5 px-3.5 py-1 rounded-xl bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 font-mono text-xl sm:text-2xl font-black text-slate-900 dark:text-white shadow-inner">
              <span>{{ gameData.game_info.visiting_score }}</span>
              <span class="text-slate-400 dark:text-slate-600">:</span>
              <span>{{ gameData.game_info.home_score }}</span>
            </div>
            <div class="text-left">
              <div class="text-base sm:text-lg font-black text-slate-900 dark:text-white">{{ gameData.game_info.home_team }}</div>
              <div class="text-[11px] text-slate-500 dark:text-slate-400">主隊</div>
            </div>
          </div>
        </div>

        <!-- Tab 1: Plate Appearance Breakdown -->
        <div v-show="activeTab === 'at-bat'">
          <AtBatViewer 
            v-if="gameData"
            :plate-appearances="gameData.plate_appearances" 
            :all-pitches="gameData.all_called_pitches"
          />
          <div v-else class="text-center py-16 text-slate-400 text-sm">
            請先由上方搜尋場次或至「跨場次數據庫」載入賽事
          </div>
        </div>

        <!-- Tab 2: Umpire Scorecard -->
        <div v-show="activeTab === 'scorecard'">
          <ScorecardSummary 
            v-if="gameData"
            :metrics="gameData.umpire_metrics"
            :all-pitches="gameData.all_called_pitches"
            :plate-appearances="gameData.plate_appearances"
            :game-info="gameData.game_info"
          />
          <div v-else class="text-center py-16 text-slate-400 text-sm">
            請先由上方搜尋場次或至「跨場次數據庫」載入賽事
          </div>
        </div>

        <!-- Tab 3: Multi-Game Database Explorer -->
        <div v-show="activeTab === 'multi-game'">
          <MultiGameStats 
            @load-game="(id) => loadGame(id, 'scorecard')" 
            @view-season-stats="handleViewSeasonStats"
          />
        </div>

        <!-- Tab 4: Yearly Season Stats Explorer -->
        <div v-show="activeTab === 'season-stats'">
          <SeasonStatsView 
            @load-game="(id) => loadGame(id, 'scorecard')" 
          />
        </div>
      </template>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AtBatViewer from './components/AtBatViewer.vue'
import ScorecardSummary from './components/ScorecardSummary.vue'
import MultiGameStats from './components/MultiGameStats.vue'
import SeasonStatsView from './components/SeasonStatsView.vue'
import { fetchGame, fetchDefaultGameId, isStaticMode } from './services/dataService'

const activeTab = ref('multi-game')
const inputSno = ref(295)
const defaultGameId = ref(null)
const gameData = ref(null)
const isLoading = ref(false)
const errorMessage = ref('')
const isDark = ref(false)
const isStatic = ref(isStaticMode())

const isSingleGameTab = computed(() => activeTab.value === 'scorecard' || activeTab.value === 'at-bat')

function formatMinutes(mins) {
  if (!mins) return '-'
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return h > 0 ? `${h}小時 ${m}分` : `${m}分`
}

function handleViewSeasonStats() {
  activeTab.value = 'season-stats'
}

function toggleTheme() {
  isDark.value = !isDark.value
  if (isDark.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

function handleKeydown(e) {
  if (e.key === 'ArrowUp' || e.key === '+' || e.key === '=') {
    e.preventDefault()
    incrementSno()
  } else if (e.key === 'ArrowDown' || e.key === '-' || e.key === '_') {
    e.preventDefault()
    decrementSno()
  } else if (e.key === 'Enter') {
    loadGameBySno()
  }
}

function incrementSno() {
  const current = Number(inputSno.value) || 0
  inputSno.value = current + 1
}

function decrementSno() {
  const current = Number(inputSno.value) || 1
  if (current > 1) {
    inputSno.value = current - 1
  }
}

async function loadGame(gameId, targetTab = null) {
  if (targetTab) {
    activeTab.value = targetTab
  }
  isLoading.value = true
  errorMessage.value = ''
  try {
    const data = await fetchGame(gameId)
    gameData.value = data
    if (data?.game_info?.game_sno) {
      inputSno.value = data.game_info.game_sno
    }
  } catch (e) {
    errorMessage.value = e.message || `擷取賽事資料失敗 (${gameId})`
  } finally {
    isLoading.value = false
  }
}

async function loadGameBySno() {
  if (!inputSno.value) return
  const gameId = `2026-A-${inputSno.value}`
  await loadGame(gameId, activeTab.value === 'multi-game' ? 'scorecard' : null)
}

async function loadDefaultGame() {
  if (defaultGameId.value) {
    await loadGame(defaultGameId.value, 'scorecard')
  }
}

onMounted(async () => {
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')
  } else {
    isDark.value = false
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }

  // Pre-fetch default game in background so single game views are ready immediately
  try {
    const defId = await fetchDefaultGameId()
    defaultGameId.value = defId
    if (defId) {
      const data = await fetchGame(defId)
      gameData.value = data
      if (data?.game_info?.game_sno) {
        inputSno.value = data.game_info.game_sno
      }
    }
  } catch (e) {
    console.warn('Initial game prefetch:', e)
  }
})
</script>
