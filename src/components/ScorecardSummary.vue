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
          本場總判決數：{{ metrics.total_called_pitches }} 顆 | 實質誤判：{{ effectiveMissedCalls.length }} 顆 | 平均誤差：{{ effectiveAvgMissDist }} cm
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

    <!-- Team Advantage / Favor Metrics Summary Cards (容錯範圍後統計，依各隊代表色呈現) -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <!-- Visiting Team Favor Card -->
      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm flex flex-col justify-between gap-3 transition-colors relative overflow-hidden">
        <div class="absolute top-0 left-0 right-0 h-1.5" :style="{ backgroundColor: visitingColorInfo.primary }"></div>
        <div>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span 
                class="text-xs px-2 py-0.5 rounded font-bold border transition-colors"
                :style="{ backgroundColor: visitingColorInfo.badgeBg, color: visitingColorInfo.primary, borderColor: visitingColorInfo.badgeBorder }"
              >
                客隊
              </span>
              <h3 class="text-base font-black text-slate-900 dark:text-white">{{ teamNames.visiting }} 得利</h3>
            </div>
            <span class="text-xs text-slate-400 dark:text-slate-500 font-medium">容錯過濾後</span>
          </div>
          <div class="mt-4 flex items-baseline gap-2">
            <span class="text-3xl font-black font-mono transition-colors" :style="{ color: visitingColorInfo.primary }">
              {{ effectiveVisitingCount }}
            </span>
            <span class="text-xs text-slate-500 dark:text-slate-400 font-bold">顆球</span>
          </div>
        </div>
        <div class="pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-2 gap-2 text-xs">
          <div>
            <span class="text-slate-500 dark:text-slate-400 block text-[11px]">得利總距離</span>
            <strong class="font-mono text-slate-900 dark:text-white text-sm font-bold">{{ effectiveVisitingDist }} cm</strong>
          </div>
          <div>
            <span class="text-slate-500 dark:text-slate-400 block text-[11px]">平均每球得利</span>
            <strong class="font-mono text-slate-900 dark:text-white text-sm font-bold">{{ effectiveVisitingAvg }} cm</strong>
          </div>
        </div>
      </div>

      <!-- Home Team Favor Card -->
      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm flex flex-col justify-between gap-3 transition-colors relative overflow-hidden">
        <div class="absolute top-0 left-0 right-0 h-1.5" :style="{ backgroundColor: homeColorInfo.primary }"></div>
        <div>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span 
                class="text-xs px-2 py-0.5 rounded font-bold border transition-colors"
                :style="{ backgroundColor: homeColorInfo.badgeBg, color: homeColorInfo.primary, borderColor: homeColorInfo.badgeBorder }"
              >
                主隊
              </span>
              <h3 class="text-base font-black text-slate-900 dark:text-white">{{ teamNames.home }} 得利</h3>
            </div>
            <span class="text-xs text-slate-400 dark:text-slate-500 font-medium">容錯過濾後</span>
          </div>
          <div class="mt-4 flex items-baseline gap-2">
            <span class="text-3xl font-black font-mono transition-colors" :style="{ color: homeColorInfo.primary }">
              {{ effectiveHomeCount }}
            </span>
            <span class="text-xs text-slate-500 dark:text-slate-400 font-bold">顆球</span>
          </div>
        </div>
        <div class="pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-2 gap-2 text-xs">
          <div>
            <span class="text-slate-500 dark:text-slate-400 block text-[11px]">得利總距離</span>
            <strong class="font-mono text-slate-900 dark:text-white text-sm font-bold">{{ effectiveHomeDist }} cm</strong>
          </div>
          <div>
            <span class="text-slate-500 dark:text-slate-400 block text-[11px]">平均每球得利</span>
            <strong class="font-mono text-slate-900 dark:text-white text-sm font-bold">{{ effectiveHomeAvg }} cm</strong>
          </div>
        </div>
      </div>

      <!-- Net Advantage Differential Card -->
      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm flex flex-col justify-between gap-3 transition-colors relative overflow-hidden md:col-span-2 lg:col-span-1">
        <div class="absolute top-0 left-0 right-0 h-1.5" :style="{ backgroundColor: netFavoredColor }"></div>
        <div>
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-700 dark:text-slate-300">⚖️ 全場裁決偏向 (Net Favor)</span>
            <span 
              class="text-[10px] px-2 py-0.5 rounded font-mono font-bold border"
              :style="{ backgroundColor: netFavorBadgeStyle.bg, color: netFavorBadgeStyle.color, borderColor: netFavorBadgeStyle.border }"
            >
              {{ netFavorStatusText }}
            </span>
          </div>
          <div class="mt-3">
            <div class="text-[11px] text-slate-500 dark:text-slate-400">總體得利優勢隊伍：</div>
            <div class="text-base font-black mt-0.5 truncate transition-colors" :style="{ color: netFavoredColor }">
              {{ netFavorHeadline }}
            </div>
          </div>
        </div>
        <div class="pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-2 gap-2 text-xs">
          <div>
            <span class="text-slate-500 dark:text-slate-400 block text-[11px]">淨得利球數差</span>
            <strong class="font-mono text-slate-900 dark:text-white text-sm font-bold">{{ netCountDiff }} 顆</strong>
          </div>
          <div>
            <span class="text-slate-500 dark:text-slate-400 block text-[11px]">淨得利距離差</span>
            <strong class="font-mono text-slate-900 dark:text-white text-sm font-bold">{{ netDistDiff }} cm</strong>
          </div>
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
          {{ showOnlyMissed ? '全場誤判球點分佈 (依得利隊伍配色)' : '全場所有判決球點分佈' }}
        </h3>
        <StrikeZoneSVG 
          :pitches="displayPitches"
          :sz-top="0.963"
          :sz-bottom="0.486"
          :highlighted-index="selectedPitchIndex"
          :is-missed-mode="showOnlyMissed"
          :home-team="teamNames.home"
          :visiting-team="teamNames.visiting"
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
            @click="onSelectMissedCall(mc)"
            :class="[
              'p-3 rounded-lg border transition-all flex flex-col gap-2.5 text-xs cursor-pointer',
              selectedPitchObject === mc
                ? 'bg-blue-50/90 dark:bg-slate-800/90 border-blue-500 shadow-xs'
                : 'bg-slate-50 dark:bg-slate-950/80 border-slate-200 dark:border-slate-800 hover:border-blue-400 dark:hover:border-slate-700'
            ]"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="flex items-start gap-2.5">
                <span class="w-5 h-5 rounded bg-amber-500/10 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 font-mono font-bold flex items-center justify-center text-xs shrink-0 border border-amber-500/20">
                  {{ idx + 1 }}
                </span>
                <div class="flex flex-col gap-0.5">
                  <div class="flex items-center gap-2">
                    <span class="font-bold text-slate-900 dark:text-white">
                      {{ mc.inning_num }}局{{ mc.inning_half }} 投手: {{ mc.pitcher }} vs 打者: {{ mc.batter }}
                    </span>
                    <!-- Favored Team badge with Team representative color -->
                    <span 
                      v-if="getPitchFavoredTeam(mc)" 
                      class="px-2 py-0.5 rounded border text-[10px] font-bold shrink-0 transition-colors"
                      :style="getTeamBadgeStyle(getPitchFavoredTeam(mc))"
                    >
                      {{ getPitchFavoredTeam(mc) }}得利
                    </span>
                  </div>
                  <span class="text-slate-500 dark:text-slate-400 text-[11px]">
                    球數: {{ mc.count_b }}-{{ mc.count_s }} | {{ mc.speed_kmh ? mc.speed_kmh + ' km/h' : '' }} {{ mc.pitch_type || '' }} | {{ mc.content }}
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

            <!-- Bottom Action Toolbar: Similar Pitch Analysis Trigger -->
            <div class="flex items-center justify-between pt-2 border-t border-slate-200/70 dark:border-slate-800/80 text-[11px]">
              <span class="text-slate-500 dark:text-slate-400">
                附近判決：<strong class="text-blue-600 dark:text-blue-400 font-mono font-bold">{{ getNearbyCount(mc) }}</strong> 顆 (8cm半徑)
              </span>
              <button 
                @click.stop="openSimilarPitchModal(mc)"
                class="px-2.5 py-1 rounded bg-blue-600/10 hover:bg-blue-600 text-blue-700 hover:text-white dark:bg-blue-500/20 dark:hover:bg-blue-600 dark:text-blue-300 dark:hover:text-white font-bold transition-all border border-blue-200 dark:border-blue-500/30 flex items-center gap-1 cursor-pointer"
              >
                <span>📍 類似進壘點分析</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Similar Pitch Analysis Modal -->
    <SimilarPitchModal 
      :is-open="isSimilarModalOpen"
      :target-pitch="activeTargetPitch"
      :all-pitches="allPitches"
      :plate-appearances="plateAppearances"
      @close="isSimilarModalOpen = false"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import StrikeZoneSVG from './StrikeZoneSVG.vue'
import SimilarPitchModal from './SimilarPitchModal.vue'
import { findSimilarPitches } from '../utils/pitchGeometry.js'
import { getTeamColorInfo } from '../utils/teamColors.js'

const props = defineProps({
  metrics: {
    type: Object,
    default: () => ({})
  },
  allPitches: {
    type: Array,
    default: () => []
  },
  plateAppearances: {
    type: Array,
    default: () => []
  },
  gameInfo: {
    type: Object,
    default: () => ({})
  }
})

const toleranceCm = ref(0)
const showOnlyMissed = ref(true)
const selectedPitchIndex = ref(null)
const selectedPitchObject = ref(null)

const isSimilarModalOpen = ref(false)
const activeTargetPitch = ref(null)

function onSelectMissedCall(mc) {
  selectedPitchIndex.value = mc.pitch_index
  selectedPitchObject.value = mc
}

function openSimilarPitchModal(pitch) {
  activeTargetPitch.value = pitch
  isSimilarModalOpen.value = true
}

function getNearbyCount(pitch) {
  if (!pitch || !props.allPitches.length) return 0
  return findSimilarPitches(pitch, props.allPitches, 8.0).length
}

const teamNames = computed(() => {
  return {
    visiting: props.gameInfo?.visiting_team || props.plateAppearances[0]?.batting_team || '客隊',
    home: props.gameInfo?.home_team || props.plateAppearances[0]?.fielding_team || '主隊'
  }
})

const visitingColorInfo = computed(() => getTeamColorInfo(teamNames.value.visiting))
const homeColorInfo = computed(() => getTeamColorInfo(teamNames.value.home))

function getPitchFavoredTeam(pitch) {
  if (!pitch) return ''
  if (pitch.favored_team) return pitch.favored_team

  const vName = teamNames.value.visiting
  const hName = teamNames.value.home

  const isInningTop = pitch.inning_half === '上' || (typeof pitch.inning === 'string' && pitch.inning.includes('上'))
  const isStrikeCalledBall = (pitch.true_call === 'STRIKE' && pitch.called === 'BALL') || pitch.advantage === 'BATTER'
  const isBallCalledStrike = (pitch.true_call === 'BALL' && pitch.called === 'STRIKE') || pitch.advantage === 'PITCHER'

  if (isInningTop) {
    // 上半局：客隊打擊 (好球判壞球 -> 客隊得利), 主隊投球 (壞球判好球 -> 主隊得利)
    if (isStrikeCalledBall) return vName
    if (isBallCalledStrike) return hName
  } else {
    // 下半局：主隊打擊 (好球判壞球 -> 主隊得利), 客隊投球 (壞球判好球 -> 客隊得利)
    if (isStrikeCalledBall) return hName
    if (isBallCalledStrike) return vName
  }
  return ''
}

function getTeamBadgeStyle(teamName) {
  const info = getTeamColorInfo(teamName)
  return {
    backgroundColor: info.badgeBg,
    borderColor: info.badgeBorder,
    color: info.primary
  }
}

// 容錯範圍後之實質誤判清單
const effectiveMissedCalls = computed(() => {
  const list = props.metrics.missed_calls || []
  return list.filter(p => p.dist_cm >= toleranceCm.value)
})

const effectiveAvgMissDist = computed(() => {
  const list = effectiveMissedCalls.value
  if (list.length === 0) return 0.0
  const sum = list.reduce((acc, p) => acc + (p.dist_cm || 0), 0)
  return (sum / list.length).toFixed(1)
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

// --- 客隊得利統計（容錯範圍後） ---
const effectiveVisitingFavoredCalls = computed(() => {
  const vName = teamNames.value.visiting
  return effectiveMissedCalls.value.filter(p => getPitchFavoredTeam(p) === vName)
})

const effectiveVisitingCount = computed(() => effectiveVisitingFavoredCalls.value.length)

const effectiveVisitingDist = computed(() => {
  const sum = effectiveVisitingFavoredCalls.value.reduce((acc, p) => acc + (p.dist_cm || 0), 0)
  return Math.round(sum * 10) / 10
})

const effectiveVisitingAvg = computed(() => {
  const count = effectiveVisitingCount.value
  if (count === 0) return 0.0
  return Math.round((effectiveVisitingDist.value / count) * 10) / 10
})

// --- 主隊得利統計（容錯範圍後） ---
const effectiveHomeFavoredCalls = computed(() => {
  const hName = teamNames.value.home
  return effectiveMissedCalls.value.filter(p => getPitchFavoredTeam(p) === hName)
})

const effectiveHomeCount = computed(() => effectiveHomeFavoredCalls.value.length)

const effectiveHomeDist = computed(() => {
  const sum = effectiveHomeFavoredCalls.value.reduce((acc, p) => acc + (p.dist_cm || 0), 0)
  return Math.round(sum * 10) / 10
})

const effectiveHomeAvg = computed(() => {
  const count = effectiveHomeCount.value
  if (count === 0) return 0.0
  return Math.round((effectiveHomeDist.value / count) * 10) / 10
})

// --- 淨得利差額與傾向 ---
const netCountDiff = computed(() => Math.abs(effectiveHomeCount.value - effectiveVisitingCount.value))

const netDistDiff = computed(() => {
  return Math.abs(Math.round((effectiveHomeDist.value - effectiveVisitingDist.value) * 10) / 10).toFixed(1)
})

const netFavorHeadline = computed(() => {
  const vCount = effectiveVisitingCount.value
  const hCount = effectiveHomeCount.value
  const vDist = effectiveVisitingDist.value
  const hDist = effectiveHomeDist.value
  const vName = teamNames.value.visiting
  const hName = teamNames.value.home

  if (vCount > hCount) {
    return `${vName} 得利 (+${vCount - hCount} 顆 / +${(vDist - hDist).toFixed(1)} cm)`
  } else if (hCount > vCount) {
    return `${hName} 得利 (+${hCount - vCount} 顆 / +${(hDist - vDist).toFixed(1)} cm)`
  } else if (vDist !== hDist) {
    return vDist > hDist ? `${vName} 距離偏多 (+${(vDist - hDist).toFixed(1)} cm)` : `${hName} 距離偏多 (+${(hDist - vDist).toFixed(1)} cm)`
  }
  return '兩隊得利完全平衡'
})

const netFavorStatusText = computed(() => {
  const vCount = effectiveVisitingCount.value
  const hCount = effectiveHomeCount.value
  if (vCount > hCount) return `${teamNames.value.visiting} 佔優`
  if (hCount > vCount) return `${teamNames.value.home} 佔優`
  return '雙方均等'
})

const netFavoredColor = computed(() => {
  const vCount = effectiveVisitingCount.value
  const hCount = effectiveHomeCount.value
  if (vCount > hCount) return visitingColorInfo.value.primary
  if (hCount > vCount) return homeColorInfo.value.primary
  return '#64748b'
})

const netFavorBadgeStyle = computed(() => {
  const vCount = effectiveVisitingCount.value
  const hCount = effectiveHomeCount.value
  if (vCount > hCount) {
    return {
      bg: visitingColorInfo.value.badgeBg,
      color: visitingColorInfo.value.primary,
      border: visitingColorInfo.value.badgeBorder
    }
  }
  if (hCount > vCount) {
    return {
      bg: homeColorInfo.value.badgeBg,
      color: homeColorInfo.value.primary,
      border: homeColorInfo.value.badgeBorder
    }
  }
  return {
    bg: 'rgba(100, 116, 139, 0.15)',
    color: '#64748b',
    border: 'rgba(100, 116, 139, 0.3)'
  }
})

const displayPitches = computed(() => {
  if (showOnlyMissed.value) {
    return effectiveMissedCalls.value
  }
  return props.allPitches
})
</script>


