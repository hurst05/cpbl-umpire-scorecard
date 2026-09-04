<template>
  <div class="flex flex-col gap-6">
    <!-- Batch Collector / Mode Status Banner -->
    <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm dark:shadow-xl flex flex-col md:flex-row items-center justify-between gap-4 transition-colors">
      <div>
        <div class="flex items-center gap-2">
          <h3 class="text-base font-bold text-slate-900 dark:text-white">
            {{ isStatic ? '已發布賽事數據庫 (靜態唯讀)' : '批次賽事抓取與主審數據庫' }}
          </h3>
          <span
            :class="[
              'text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider',
              isStatic ? 'bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-700/50' : 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-700/50'
            ]"
          >
            {{ isStatic ? '線上靜態模式' : '本機全功能模式' }}
          </span>
        </div>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
          {{ isStatic
              ? `目前為線上靜態展示模式，已收錄 ${cachedGames.length} 場賽事。${generatedAtStr ? `(資料產生於: ${generatedAtStr})` : ''}`
              : '從 CPBL 官方進階數據網抓取指定日期的全部完賽比賽並自動完成主審好球帶分析。' }}
        </p>
      </div>

      <!-- Controls: Only available in Local API Mode -->
      <div v-if="!isStatic" class="flex items-center gap-3">
        <input 
          type="date" 
          v-model="batchDate"
          class="px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white text-xs focus:ring-1 focus:ring-blue-500 outline-none"
        />
        <button 
          @click="handleBatchCollect"
          :disabled="isCollecting"
          class="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs transition-all disabled:opacity-50 flex items-center gap-1.5 shadow-sm cursor-pointer"
        >
          <span v-if="isCollecting" class="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>
          {{ isCollecting ? '抓取與分析中...' : '批次抓取此日賽事' }}
        </button>
      </div>
      <div v-else class="flex items-center gap-3">
        <span class="text-xs text-slate-500 dark:text-slate-400 font-mono">
          已收錄總計：<strong class="text-slate-900 dark:text-white">{{ cachedGames.length }}</strong> 場
        </span>
      </div>
    </div>

    <!-- Year Filter & Quick Stats Summary Strip -->
    <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 transition-colors">
      <!-- Year Filter Pills -->
      <div class="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
        <span class="text-xs font-bold text-slate-500 dark:text-slate-400 mr-1 shrink-0">年度篩選:</span>
        <button
          v-for="yr in yearFilterOptions"
          :key="yr.value"
          @click="selectedYearFilter = yr.value"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer',
            selectedYearFilter === yr.value
              ? 'bg-blue-600 text-white shadow-xs'
              : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
          ]"
        >
          {{ yr.label }}
        </button>
      </div>

      <!-- Quick Metrics Summary & Direct Link -->
      <div class="flex flex-wrap items-center gap-4 text-xs">
        <div class="flex items-center gap-3 font-mono">
          <span class="text-slate-600 dark:text-slate-400">
            場次: <strong class="text-slate-900 dark:text-white">{{ filteredGames.length }}</strong>
          </span>
          <span class="text-slate-300 dark:text-slate-700">|</span>
          <span class="text-slate-600 dark:text-slate-400">
            均時: <strong class="text-slate-900 dark:text-white">{{ quickStats.avgDuration }}</strong>
          </span>
          <span class="text-slate-300 dark:text-slate-700">|</span>
          <span class="text-slate-600 dark:text-slate-400">
            分差: <strong class="text-slate-900 dark:text-white">{{ quickStats.avgMargin }}分</strong>
          </span>
          <span class="text-slate-300 dark:text-slate-700">|</span>
          <span class="text-slate-600 dark:text-slate-400">
            勝得分: <strong class="text-emerald-600 dark:text-emerald-400">{{ quickStats.avgWinnerScore }}分</strong>
          </span>
        </div>

        <button
          @click="$emit('view-season-stats', selectedYearFilter)"
          class="px-3 py-1.5 rounded-lg bg-blue-50 dark:bg-blue-950/50 hover:bg-blue-100 dark:hover:bg-blue-900/60 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-700/50 text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer shrink-0"
        >
          <span>📊</span>
          <span>查看完整年度統計</span>
        </button>
      </div>
    </div>

    <!-- Error State for MultiGameStats -->
    <div v-if="errorMessage" class="p-4 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500/50 text-red-700 dark:text-red-300 text-sm flex items-center justify-between gap-4">
      <span>{{ errorMessage }}</span>
      <button
        @click="loadCachedGames"
        class="underline font-bold shrink-0 hover:text-red-900 dark:hover:text-red-200 cursor-pointer"
      >
        重新嘗試
      </button>
    </div>

    <!-- Cached Games Table -->
    <div v-else class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm dark:shadow-xl flex flex-col gap-4 transition-colors">
      <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
        <h3 class="text-sm font-bold text-slate-900 dark:text-white">
          {{ selectedYearFilter === 'all' ? '全部已儲存賽事' : `${selectedYearFilter} 年度賽事清單` }} ({{ filteredGames.length }} 場)
        </h3>
        <div class="flex items-center gap-2">
          <button 
            @click="exportFilteredJSON"
            class="px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-all border border-slate-200 dark:border-slate-700 cursor-pointer"
          >
            匯出 JSON
          </button>
          <button 
            @click="exportFilteredCSV"
            class="px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-all border border-slate-200 dark:border-slate-700 cursor-pointer"
          >
            匯出 CSV 統計表
          </button>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-950/60 uppercase font-mono border-b border-slate-200 dark:border-slate-800">
            <tr>
              <th
                @click="toggleSort('game_sno')"
                class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                :class="{ 'text-blue-600 dark:text-blue-400 font-bold': sortKey === 'game_sno' }"
                title="點擊切換場次排序"
              >
                <div class="flex items-center gap-1.5">
                  <span>場次</span>
                  <span class="text-[10px] font-mono" :class="sortKey === 'game_sno' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                    {{ sortKey === 'game_sno' ? (sortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                  </span>
                </div>
              </th>
              <th
                @click="toggleSort('game_date')"
                class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                :class="{ 'text-blue-600 dark:text-blue-400 font-bold': sortKey === 'game_date' }"
                title="點擊切換日期排序"
              >
                <div class="flex items-center gap-1.5">
                  <span>日期</span>
                  <span class="text-[10px] font-mono" :class="sortKey === 'game_date' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                    {{ sortKey === 'game_date' ? (sortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                  </span>
                </div>
              </th>
              <th
                @click="toggleSort('field')"
                class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                :class="{ 'text-blue-600 dark:text-blue-400 font-bold': sortKey === 'field' }"
                title="點擊切換球場排序"
              >
                <div class="flex items-center gap-1.5">
                  <span>球場</span>
                  <span class="text-[10px] font-mono" :class="sortKey === 'field' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                    {{ sortKey === 'field' ? (sortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                  </span>
                </div>
              </th>
              <th class="p-3 whitespace-nowrap">對戰隊伍</th>
              <th class="p-3 whitespace-nowrap">比分</th>
              <th
                @click="toggleSort('game_duration_minutes')"
                class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                :class="{ 'text-blue-600 dark:text-blue-400 font-bold': sortKey === 'game_duration_minutes' }"
                title="點擊切換比賽時間排序"
              >
                <div class="flex items-center gap-1.5">
                  <span>比賽時間</span>
                  <span class="text-[10px] font-mono" :class="sortKey === 'game_duration_minutes' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                    {{ sortKey === 'game_duration_minutes' ? (sortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                  </span>
                </div>
              </th>
              <th
                @click="toggleSort('hp_umpire')"
                class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                :class="{ 'text-blue-600 dark:text-blue-400 font-bold': sortKey === 'hp_umpire' }"
                title="點擊切換主審排序"
              >
                <div class="flex items-center gap-1.5">
                  <span>主審</span>
                  <span class="text-[10px] font-mono" :class="sortKey === 'hp_umpire' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                    {{ sortKey === 'hp_umpire' ? (sortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                  </span>
                </div>
              </th>
              <th
                @click="toggleSort('missed_count')"
                class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                :class="{ 'text-blue-600 dark:text-blue-400 font-bold': sortKey === 'missed_count' }"
                title="點擊切換誤判數排序"
              >
                <div class="flex items-center gap-1.5">
                  <span>誤判數</span>
                  <span class="text-[10px] font-mono" :class="sortKey === 'missed_count' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                    {{ sortKey === 'missed_count' ? (sortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                  </span>
                </div>
              </th>
              <th
                @click="toggleSort('overall_acc')"
                class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                :class="{ 'text-blue-600 dark:text-blue-400 font-bold': sortKey === 'overall_acc' }"
                title="點擊切換整體準確率排序"
              >
                <div class="flex items-center gap-1.5">
                  <span>整體準確率</span>
                  <span class="text-[10px] font-mono" :class="sortKey === 'overall_acc' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                    {{ sortKey === 'overall_acc' ? (sortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                  </span>
                </div>
              </th>
              <th
                @click="toggleSort('ball_acc')"
                class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                :class="{ 'text-blue-600 dark:text-blue-400 font-bold': sortKey === 'ball_acc' }"
                title="點擊切換壞球準確率排序"
              >
                <div class="flex items-center gap-1.5">
                  <span>壞球準確率</span>
                  <span class="text-[10px] font-mono" :class="sortKey === 'ball_acc' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                    {{ sortKey === 'ball_acc' ? (sortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                  </span>
                </div>
              </th>
              <th
                @click="toggleSort('strike_acc')"
                class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                :class="{ 'text-blue-600 dark:text-blue-400 font-bold': sortKey === 'strike_acc' }"
                title="點擊切換好球準確率排序"
              >
                <div class="flex items-center gap-1.5">
                  <span>好球準確率</span>
                  <span class="text-[10px] font-mono" :class="sortKey === 'strike_acc' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                    {{ sortKey === 'strike_acc' ? (sortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                  </span>
                </div>
              </th>
              <th
                @click="toggleSort('consistency')"
                class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                :class="{ 'text-blue-600 dark:text-blue-400 font-bold': sortKey === 'consistency' }"
                title="點擊切換判決一致性排序"
              >
                <div class="flex items-center gap-1.5">
                  <span>判決一致性</span>
                  <span class="text-[10px] font-mono" :class="sortKey === 'consistency' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                    {{ sortKey === 'consistency' ? (sortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                  </span>
                </div>
              </th>
              <th class="p-3 text-right whitespace-nowrap">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200 dark:divide-slate-800/80">
            <tr 
              v-for="g in sortedGames" 
              :key="g.game_id"
              class="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-all font-medium"
            >
              <td class="p-3 font-mono font-bold text-blue-600 dark:text-blue-400">{{ g.game_sno }}</td>
              <td class="p-3 font-mono text-slate-600 dark:text-slate-300">{{ g.game_date }}</td>
              <td class="p-3 text-slate-600 dark:text-slate-300">{{ g.field }}</td>
              <td class="p-3 text-slate-900 dark:text-white font-bold">{{ g.visiting_team }} vs {{ g.home_team }}</td>
              <td class="p-3 font-mono font-bold text-slate-800 dark:text-slate-100">{{ g.visiting_score }} : {{ g.home_score }}</td>
              <td class="p-3 font-mono text-slate-600 dark:text-slate-300">
                {{ formatGameDuration(g.game_duration_minutes) }}
              </td>
              <td class="p-3 text-amber-600 dark:text-amber-300 font-bold">{{ g.hp_umpire }}</td>
              <td class="p-3 font-mono text-amber-600 dark:text-amber-400 font-bold">{{ g.missed_count }}</td>
              <td class="p-3 font-mono font-bold text-emerald-600 dark:text-emerald-400">{{ g.overall_acc }}%</td>
              <td class="p-3 font-mono text-slate-600 dark:text-slate-300">{{ g.ball_acc }}%</td>
              <td class="p-3 font-mono text-slate-600 dark:text-slate-300">{{ g.strike_acc }}%</td>
              <td class="p-3 font-mono font-bold text-indigo-600 dark:text-indigo-400">
                {{ (g.overall_consistency != null ? g.overall_consistency : g.consistency_rate) != null ? `${g.overall_consistency ?? g.consistency_rate}%` : '-' }}
              </td>
              <td class="p-3 text-right">
                <button 
                  @click="$emit('load-game', g.game_id)"
                  class="px-2.5 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white text-[11px] font-bold transition-all shadow-sm cursor-pointer"
                >
                  載入分析
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchGameList, fetchManifest, runBatchCollect, isStaticMode } from '../services/dataService'

defineEmits(['load-game', 'view-season-stats'])

const batchDate = ref(new Date().toISOString().slice(0, 10))
const isCollecting = ref(false)
const cachedGames = ref([])
const errorMessage = ref('')
const generatedAtStr = ref('')
const isStatic = ref(isStaticMode())
const selectedYearFilter = ref('2026')

// 排序狀態：預設場次降冪排序 (game_sno desc)
const sortKey = ref('game_sno')
const sortOrder = ref('desc')

function toggleSort(key) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    if (key === 'game_date' || key === 'field' || key === 'hp_umpire') {
      sortOrder.value = 'asc'
    } else {
      sortOrder.value = 'desc'
    }
  }
}

const yearFilterOptions = computed(() => {
  const years = Array.from(
    new Set(
      cachedGames.value
        .map(g => (g.game_date ? g.game_date.slice(0, 4) : ''))
        .filter(Boolean)
    )
  ).sort((a, b) => b - a)

  const opts = years.map(y => ({ label: `${y} 年度`, value: String(y) }))
  opts.push({ label: '全部年度', value: 'all' })
  return opts
})

const filteredGames = computed(() => {
  if (selectedYearFilter.value === 'all') {
    return cachedGames.value
  }
  return cachedGames.value.filter(g => g.game_date && g.game_date.startsWith(selectedYearFilter.value))
})

const sortedGames = computed(() => {
  const list = [...filteredGames.value]
  const key = sortKey.value
  const order = sortOrder.value === 'asc' ? 1 : -1

  return list.sort((a, b) => {
    let res
    if (key === 'game_sno') {
      res = (Number(a.game_sno) || 0) - (Number(b.game_sno) || 0)
    } else if (key === 'game_date') {
      res = (a.game_date || '').localeCompare(b.game_date || '')
    } else if (key === 'field') {
      res = (a.field || '').localeCompare(b.field || '', 'zh-Hant')
    } else if (key === 'hp_umpire') {
      res = (a.hp_umpire || '').localeCompare(b.hp_umpire || '', 'zh-Hant')
    } else if (key === 'consistency') {
      const valA = Number(a.overall_consistency ?? a.consistency_rate) || 0
      const valB = Number(b.overall_consistency ?? b.consistency_rate) || 0
      res = valA - valB
    } else if (key === 'game_duration_minutes') {
      res = (Number(a.game_duration_minutes) || 0) - (Number(b.game_duration_minutes) || 0)
    } else {
      const valA = Number(a[key]) || 0
      const valB = Number(b[key]) || 0
      res = valA - valB
    }

    if (res !== 0) {
      return res * order
    }
    return (Number(b.game_sno) || 0) - (Number(a.game_sno) || 0)
  })
})

const quickStats = computed(() => {
  const list = filteredGames.value
  if (!list || list.length === 0) {
    return { avgDuration: '無資料', avgMargin: '0.0', avgWinnerScore: '0.0', avgAcc: '0.0' }
  }

  const durs = list.map(g => g.game_duration_minutes).filter(d => d && d > 0)
  let avgDurStr = '無資料'
  if (durs.length > 0) {
    const avgM = Math.round(durs.reduce((a, b) => a + b, 0) / durs.length)
    const h = Math.floor(avgM / 60)
    const m = avgM % 60
    avgDurStr = h > 0 ? `${h}時${m}分` : `${m}分`
  }

  let totalMargin = 0
  let totalWinner = 0
  let totalAcc = 0
  list.forEach(g => {
    const hs = Number(g.home_score) || 0
    const vs = Number(g.visiting_score) || 0
    totalMargin += Math.abs(hs - vs)
    totalWinner += Math.max(hs, vs)
    totalAcc += Number(g.overall_acc) || 0
  })

  return {
    avgDuration: avgDurStr,
    avgMargin: (totalMargin / list.length).toFixed(2),
    avgWinnerScore: (totalWinner / list.length).toFixed(2),
    avgAcc: (totalAcc / list.length).toFixed(1)
  }
})

function formatGameDuration(minutes) {
  if (!minutes || minutes <= 0) return '-'
  const h = Math.floor(minutes / 60)
  const m = Math.round(minutes % 60)
  return h > 0 ? `${h}時 ${m}分` : `${m}分`
}

async function loadCachedGames() {
  errorMessage.value = ''
  try {
    if (isStatic.value) {
      const manifest = await fetchManifest()
      cachedGames.value = manifest.games || []
      if (manifest.generated_at) {
        const d = new Date(manifest.generated_at)
        generatedAtStr.value = d.toLocaleString('zh-TW', { timeZone: 'Asia/Taipei', hour12: false })
      }
    } else {
      cachedGames.value = await fetchGameList()
    }

    if (cachedGames.value.length > 0) {
      const latestDate = cachedGames.value
        .map(g => g.game_date)
        .filter(Boolean)
        .reduce((max, cur) => (cur > max ? cur : max), '')
      if (latestDate) {
        batchDate.value = latestDate
      }
    }
  } catch (e) {
    errorMessage.value = e.message || '無法取得賽事清單'
  }
}

async function handleBatchCollect() {
  if (!batchDate.value || isStatic.value) return
  isCollecting.value = true
  errorMessage.value = ''
  try {
    await runBatchCollect(batchDate.value)
    await loadCachedGames()
  } catch (e) {
    errorMessage.value = e.message || '批次抓取發生錯誤'
  } finally {
    isCollecting.value = false
  }
}

function exportFilteredJSON() {
  const blob = new Blob([JSON.stringify(sortedGames.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `cpbl_scorecard_${selectedYearFilter.value}_${new Date().toISOString().slice(0, 10)}.json`
  a.click()
}

function exportFilteredCSV() {
  const headers = ['game_id', 'game_sno', 'game_date', 'field', 'visiting_team', 'visiting_score', 'home_team', 'home_score', 'game_duration_minutes', 'hp_umpire', 'missed_count', 'overall_acc', 'ball_acc', 'strike_acc', 'overall_consistency']
  const csvRows = [headers.join(',')]
  sortedGames.value.forEach(g => {
    csvRows.push([
      g.game_id, g.game_sno, g.game_date, g.field,
      g.visiting_team, g.visiting_score, g.home_team, g.home_score,
      g.game_duration_minutes || '',
      g.hp_umpire, g.missed_count, g.overall_acc, g.ball_acc, g.strike_acc,
      (g.overall_consistency ?? g.consistency_rate ?? '')
    ].join(','))
  })
  const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `cpbl_scorecard_${selectedYearFilter.value}_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
}

onMounted(() => {
  loadCachedGames()
})
</script>

