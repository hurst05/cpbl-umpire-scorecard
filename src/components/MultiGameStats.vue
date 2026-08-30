<template>
  <div class="flex flex-col gap-6">
    <!-- Batch Collector Controls -->
    <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm dark:shadow-xl flex flex-col md:flex-row items-center justify-between gap-4 transition-colors">
      <div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">批次賽事抓取與主審數據庫</h3>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
          從 CPBL 官方進階數據網抓取指定日期的全部完賽比賽，並寫入本機 SQLite 資料庫以供跨場次分析。
        </p>
      </div>

      <div class="flex items-center gap-3">
        <input 
          type="date" 
          v-model="batchDate"
          class="px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white text-xs focus:ring-1 focus:ring-blue-500 outline-none"
        />
        <button 
          @click="runBatchCollect"
          :disabled="isCollecting"
          class="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs transition-all disabled:opacity-50 flex items-center gap-1.5 shadow-sm"
        >
          <span v-if="isCollecting" class="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>
          {{ isCollecting ? '抓取與分析中...' : '批次抓取此日賽事' }}
        </button>
      </div>
    </div>

    <!-- Cached Games Table -->
    <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm dark:shadow-xl flex flex-col gap-4 transition-colors">
      <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
        <h3 class="text-sm font-bold text-slate-900 dark:text-white">已儲存賽事清單 ({{ cachedGames.length }} 場)</h3>
        <div class="flex items-center gap-2">
          <button 
            @click="exportAllJSON"
            class="px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-all border border-slate-200 dark:border-slate-700"
          >
            匯出全場次 JSON
          </button>
          <button 
            @click="exportAllCSV"
            class="px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-all border border-slate-200 dark:border-slate-700"
          >
            匯出 CSV 統計表
          </button>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-950/60 uppercase font-mono border-b border-slate-200 dark:border-slate-800">
            <tr>
              <th class="p-3">場次</th>
              <th class="p-3">日期</th>
              <th class="p-3">球場</th>
              <th class="p-3">對戰隊伍</th>
              <th class="p-3">比分</th>
              <th class="p-3">主審</th>
              <th class="p-3">整體準確率</th>
              <th class="p-3">壞球準確率</th>
              <th class="p-3">好球準確率</th>
              <th class="p-3">誤判數</th>
              <th class="p-3 text-right">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200 dark:divide-slate-800/80">
            <tr 
              v-for="g in cachedGames" 
              :key="g.game_id"
              class="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-all font-medium"
            >
              <td class="p-3 font-mono font-bold text-blue-600 dark:text-blue-400">{{ g.game_sno }}</td>
              <td class="p-3 font-mono text-slate-600 dark:text-slate-300">{{ g.game_date }}</td>
              <td class="p-3 text-slate-600 dark:text-slate-300">{{ g.field }}</td>
              <td class="p-3 text-slate-900 dark:text-white font-bold">{{ g.visiting_team }} vs {{ g.home_team }}</td>
              <td class="p-3 font-mono font-bold text-slate-800 dark:text-slate-100">{{ g.visiting_score }} : {{ g.home_score }}</td>
              <td class="p-3 text-amber-600 dark:text-amber-300 font-bold">{{ g.hp_umpire }}</td>
              <td class="p-3 font-mono font-bold text-emerald-600 dark:text-emerald-400">{{ g.overall_acc }}%</td>
              <td class="p-3 font-mono text-slate-600 dark:text-slate-300">{{ g.ball_acc }}%</td>
              <td class="p-3 font-mono text-slate-600 dark:text-slate-300">{{ g.strike_acc }}%</td>
              <td class="p-3 font-mono text-amber-600 dark:text-amber-400 font-bold">{{ g.missed_count }}</td>
              <td class="p-3 text-right">
                <button 
                  @click="$emit('load-game', g.game_id)"
                  class="px-2.5 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white text-[11px] font-bold transition-all shadow-sm"
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
import { ref, onMounted } from 'vue'

defineEmits(['load-game'])

const batchDate = ref('2026-08-29')
const isCollecting = ref(false)
const cachedGames = ref([])

async function fetchCachedGames() {
  try {
    const res = await fetch('/api/games/cached')
    if (res.ok) {
      cachedGames.value = await res.json()
    }
  } catch (e) {
    console.error('Error fetching cached games:', e)
  }
}

async function runBatchCollect() {
  if (!batchDate.value) return
  isCollecting.value = true
  try {
    const res = await fetch(`/api/batch-collect?date=${batchDate.value}`, { method: 'POST' })
    if (res.ok) {
      await fetchCachedGames()
    }
  } catch (e) {
    console.error('Error in batch collection:', e)
  } finally {
    isCollecting.value = false
  }
}

function exportAllJSON() {
  const blob = new Blob([JSON.stringify(cachedGames.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `cpbl_scorecard_games_${new Date().toISOString().slice(0, 10)}.json`
  a.click()
}

function exportAllCSV() {
  const headers = ['game_id', 'game_sno', 'game_date', 'field', 'visiting_team', 'visiting_score', 'home_team', 'home_score', 'hp_umpire', 'overall_acc', 'ball_acc', 'strike_acc', 'missed_count']
  const csvRows = [headers.join(',')]
  cachedGames.value.forEach(g => {
    csvRows.push([
      g.game_id, g.game_sno, g.game_date, g.field,
      g.visiting_team, g.visiting_score, g.home_team, g.home_score,
      g.hp_umpire, g.overall_acc, g.ball_acc, g.strike_acc, g.missed_count
    ].join(','))
  })
  const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `cpbl_scorecard_summary_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
}

onMounted(() => {
  fetchCachedGames()
})
</script>
