<template>
  <div class="flex flex-col gap-6">
    <!-- Top Scorecard Overview Banner -->
    <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm dark:shadow-xl flex flex-col md:flex-row items-center justify-between gap-6 transition-colors">
      <div>
        <span class="text-xs text-blue-600 dark:text-blue-400 font-bold tracking-wider uppercase">主審執法表現評分卡</span>
        <h2 class="text-2xl font-black text-slate-900 dark:text-white mt-1 flex items-center gap-2">
          主審裁判：{{ metrics.hp_umpire }}
        </h2>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
          本場總判決數：{{ metrics.total_called_pitches }} 顆 | 誤判數：{{ metrics.missed_count }} 顆 | 平均誤差：{{ metrics.avg_miss_distance_cm }} cm
        </p>
      </div>

      <!-- Accuracy Ring Metrics -->
      <div class="flex items-center gap-6">
        <!-- Overall Accuracy -->
        <div class="flex flex-col items-center">
          <div class="relative w-20 h-20 flex items-center justify-center">
            <svg class="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path class="text-slate-100 dark:text-slate-800 stroke-current" stroke-width="3.5" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              <path class="text-blue-600 dark:text-blue-500 stroke-current transition-all duration-500" :stroke-dasharray="`${effectiveOverallAcc}, 100`" stroke-width="3.5" stroke-linecap="round" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
            </svg>
            <span class="absolute font-bold text-sm text-slate-900 dark:text-white font-mono">{{ effectiveOverallAcc }}%</span>
          </div>
          <span class="text-xs font-bold text-slate-700 dark:text-slate-300 mt-1">整體準確率</span>
          <span class="text-[11px] text-slate-500 dark:text-slate-400 font-mono">{{ effectiveCorrectCount }}/{{ metrics.total_called_pitches }}</span>
        </div>

        <!-- Ball Accuracy -->
        <div class="flex flex-col items-center">
          <div class="relative w-20 h-20 flex items-center justify-center">
            <svg class="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path class="text-slate-100 dark:text-slate-800 stroke-current" stroke-width="3.5" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              <path class="text-emerald-500 stroke-current transition-all duration-500" :stroke-dasharray="`${effectiveBallAcc}, 100`" stroke-width="3.5" stroke-linecap="round" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
            </svg>
            <span class="absolute font-bold text-sm text-slate-900 dark:text-white font-mono">{{ effectiveBallAcc }}%</span>
          </div>
          <span class="text-xs font-bold text-slate-700 dark:text-slate-300 mt-1">壞球準確率</span>
          <span class="text-[11px] text-slate-500 dark:text-slate-400 font-mono">{{ metrics.ball_ratio_str }}</span>
        </div>

        <!-- Strike Accuracy -->
        <div class="flex flex-col items-center">
          <div class="relative w-20 h-20 flex items-center justify-center">
            <svg class="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path class="text-slate-100 dark:text-slate-800 stroke-current" stroke-width="3.5" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              <path class="text-red-500 stroke-current transition-all duration-500" :stroke-dasharray="`${effectiveStrikeAcc}, 100`" stroke-width="3.5" stroke-linecap="round" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
            </svg>
            <span class="absolute font-bold text-sm text-slate-900 dark:text-white font-mono">{{ effectiveStrikeAcc }}%</span>
          </div>
          <span class="text-xs font-bold text-slate-700 dark:text-slate-300 mt-1">好球準確率</span>
          <span class="text-[11px] text-slate-500 dark:text-slate-400 font-mono">{{ metrics.strike_ratio_str }}</span>
        </div>
      </div>
    </div>

    <!-- Interactive Tolerance Slider & Filter Bar -->
    <div class="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm dark:shadow-none flex flex-col sm:flex-row items-center justify-between gap-4 transition-colors">
      <div class="flex items-center gap-3">
        <span class="text-xs font-bold text-slate-700 dark:text-slate-300">顯示模式:</span>
        <button 
          @click="showOnlyMissed = true"
          :class="['px-3 py-1.5 rounded-lg text-xs font-bold transition-all border', showOnlyMissed ? 'bg-amber-500 text-white border-amber-500 shadow-sm' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:text-slate-900 dark:hover:text-white']"
        >
          僅顯示誤判 ({{ effectiveMissedCalls.length }})
        </button>
        <button 
          @click="showOnlyMissed = false"
          :class="['px-3 py-1.5 rounded-lg text-xs font-bold transition-all border', !showOnlyMissed ? 'bg-blue-600 text-white border-blue-600 shadow-sm' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:text-slate-900 dark:hover:text-white']"
        >
          顯示全部判決 ({{ allPitches.length }})
        </button>
      </div>

      <!-- Dynamic Tolerance Slider -->
      <div class="flex items-center gap-3">
        <label class="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-2">
          容錯範圍: <span class="font-mono text-amber-600 dark:text-amber-400 font-bold">{{ toleranceCm.toFixed(1) }} cm</span>
        </label>
        <input 
          type="range" 
          min="0" 
          max="10" 
          step="0.1" 
          v-model.number="toleranceCm"
          class="w-32 accent-blue-600 cursor-pointer"
        />
      </div>
    </div>

    <!-- Main Scorecard Content: Strike Zone Plot and Top Missed Calls List -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <!-- Strike Zone Visualizer (lg:col-span-6) -->
      <div class="lg:col-span-6 flex flex-col items-center bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm dark:shadow-none">
        <h3 class="text-sm font-bold text-slate-900 dark:text-white mb-3">
          {{ showOnlyMissed ? '全場誤判球點分佈' : '全場所有判決球點分佈' }}
        </h3>
        <StrikeZoneSVG 
          :pitches="displayPitches"
          :sz-top="0.963"
          :sz-bottom="0.486"
          :highlighted-index="selectedPitchIndex"
        />
      </div>

      <!-- Missed Calls Leaderboard (lg:col-span-6) -->
      <div class="lg:col-span-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm dark:shadow-none flex flex-col gap-3">
        <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2">
          <h3 class="text-sm font-bold text-slate-900 dark:text-white">關鍵誤判排行 (Top Missed Calls)</h3>
          <span class="text-xs text-slate-500 dark:text-slate-400 font-mono">共 {{ effectiveMissedCalls.length }} 顆</span>
        </div>

        <div class="flex flex-col gap-2 max-h-[460px] overflow-y-auto pr-1">
          <div 
            v-for="(mc, idx) in effectiveMissedCalls" 
            :key="'mc-' + idx"
            @click="selectedPitchIndex = mc.pitch_index"
            class="p-3 rounded-lg bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 hover:border-blue-400 dark:hover:border-slate-700 transition-all flex items-start justify-between gap-3 text-xs cursor-pointer"
          >
            <div class="flex items-start gap-2.5">
              <span class="w-5 h-5 rounded bg-amber-500/10 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 font-mono font-bold flex items-center justify-center text-xs shrink-0 border border-amber-500/20">
                {{ idx + 1 }}
              </span>
              <div class="flex flex-col gap-0.5">
                <span class="font-bold text-slate-900 dark:text-white">
                  {{ mc.inning_num }}局{{ mc.inning_half }} 投手: {{ mc.pitcher }} vs 打者: {{ mc.batter }}
                </span>
                <span class="text-slate-500 dark:text-slate-400 text-[11px]">
                  球數: {{ mc.count_b }}-{{ mc.count_s }} | {{ mc.content }}
                </span>
              </div>
            </div>

            <!-- Call badges -->
            <div class="flex flex-col items-end gap-1 shrink-0">
              <span class="px-2 py-0.5 rounded bg-red-500/10 dark:bg-red-500/20 text-red-600 dark:text-red-400 border border-red-500/20 dark:border-red-500/30 font-bold font-mono">
                誤差 {{ mc.dist_cm }} cm
              </span>
              <span class="text-[10px] text-slate-500 dark:text-slate-400">
                原判 {{ mc.called === 'STRIKE' ? '好球' : '壞球' }} → 實判 {{ mc.true_call === 'STRIKE' ? '好球' : '壞球' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import StrikeZoneSVG from './StrikeZoneSVG.vue'

const props = defineProps({
  metrics: {
    type: Object,
    default: () => ({})
  },
  allPitches: {
    type: Array,
    default: () => []
  }
})

const toleranceCm = ref(0)
const showOnlyMissed = ref(true)
const selectedPitchIndex = ref(null)

const effectiveMissedCalls = computed(() => {
  const list = props.metrics.missed_calls || []
  return list.filter(p => p.dist_cm >= toleranceCm.value)
})

const effectiveCorrectCount = computed(() => {
  const total = props.metrics.total_called_pitches || 0
  return total - effectiveMissedCalls.value.length
})

const effectiveOverallAcc = computed(() => {
  const total = props.metrics.total_called_pitches || 0
  if (total === 0) return 100.0
  return ((effectiveCorrectCount.value / total) * 100).toFixed(1)
})

const effectiveBallAcc = computed(() => {
  const trueBalls = props.allPitches.filter(p => p.true_call === 'BALL')
  if (trueBalls.length === 0) return 100.0
  const correct = trueBalls.filter(p => p.called === 'BALL' || p.dist_cm < toleranceCm.value)
  return ((correct.length / trueBalls.length) * 100).toFixed(1)
})

const effectiveStrikeAcc = computed(() => {
  const trueStrikes = props.allPitches.filter(p => p.true_call === 'STRIKE')
  if (trueStrikes.length === 0) return 100.0
  const correct = trueStrikes.filter(p => p.called === 'STRIKE' || p.dist_cm < toleranceCm.value)
  return ((correct.length / trueStrikes.length) * 100).toFixed(1)
})

const displayPitches = computed(() => {
  if (showOnlyMissed.value) {
    return effectiveMissedCalls.value
  }
  return props.allPitches
})
</script>
