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
          已發布：<strong class="text-slate-900 dark:text-white">{{ cachedGames.length }}</strong> 場
        </span>
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
        <h3 class="text-sm font-bold text-slate-900 dark:text-white">已儲存賽事清單 ({{ cachedGames.length }} 場)</h3>
        <div class="flex items-center gap-2">
          <button 
            @click="exportAllJSON"
            class="px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-all border border-slate-200 dark:border-slate-700 cursor-pointer"
          >
            匯出全場次 JSON
          </button>
          <button 
            @click="exportAllCSV"
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
import { ref, onMounted } from 'vue'
import { fetchGameList, fetchManifest, runBatchCollect, isStaticMode } from '../services/dataService'

defineEmits(['load-game'])

const batchDate = ref(new Date().toISOString().slice(0, 10))
const isCollecting = ref(false)
const cachedGames = ref([])
const errorMessage = ref('')
const generatedAtStr = ref('')
const isStatic = ref(isStaticMode())

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
  loadCachedGames()
})
</script>
