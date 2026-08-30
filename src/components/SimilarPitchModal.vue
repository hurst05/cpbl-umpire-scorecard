<template>
  <div 
    v-if="isOpen" 
    class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 md:p-6 bg-slate-950/70 backdrop-blur-sm transition-all"
    @click.self="close"
  >
    <div 
      class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150"
    >
      <!-- Modal Header -->
      <div class="px-5 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-950/40">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-600 dark:text-amber-400 flex items-center justify-center font-bold text-base border border-amber-500/30">
            📍
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-base sm:text-lg font-black text-slate-900 dark:text-white">
                類似進壘點判決分析
              </h2>
              <span class="px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-mono font-bold">
                同場比對
              </span>
            </div>
            <p class="text-xs text-slate-500 dark:text-slate-400">
              找出該場比賽進壘位置在附近的全部判決，比對主審執法一致性與好球帶傾向
            </p>
          </div>
        </div>

        <button 
          @click="close"
          class="w-8 h-8 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center transition-colors font-bold text-lg cursor-pointer"
          title="關閉 (ESC)"
        >
          ✕
        </button>
      </div>

      <!-- Modal Body (Scrollable) -->
      <div class="flex-1 overflow-y-auto p-4 sm:p-5 flex flex-col gap-4">
        <!-- Target Pitch Banner (Yellow/Amber Theme) -->
        <div 
          v-if="targetPitch"
          class="p-4 rounded-xl bg-gradient-to-r from-amber-50/90 via-amber-50/40 to-slate-50/60 dark:from-amber-950/30 dark:via-slate-900 dark:to-slate-950 border border-amber-300/80 dark:border-amber-500/30 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs"
        >
          <div class="flex items-start sm:items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-amber-500 text-white flex items-center justify-center font-black text-lg shrink-0 shadow-sm shadow-amber-500/30">
              🎯
            </div>
            <div class="flex flex-col">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-black text-slate-900 dark:text-white text-sm sm:text-base">
                  {{ targetPitch.inning_num }}局{{ targetPitch.inning_half }} 
                  {{ targetPitch.pitcher }} (投) vs {{ targetPitch.batter }} (打)
                  <span v-if="targetPitch.batter_height" class="text-xs font-normal text-slate-500">({{ targetPitch.batter_height }} cm)</span>
                </span>
                <span :class="['px-2 py-0.5 rounded text-[11px] font-mono font-bold', targetPitch.is_correct ? 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-800 dark:text-amber-300 border border-amber-500/40']">
                  {{ targetPitch.is_correct ? '🎯 基準球 (判決正確)' : '🎯 基準誤判球' }}
                </span>
                <span :class="['px-2 py-0.5 rounded text-[11px] font-mono font-bold', targetPitch.is_correct ? 'bg-slate-500/10 text-slate-700 dark:text-slate-300 border border-slate-500/20' : 'bg-red-500/10 text-red-700 dark:text-red-300 border border-red-500/20']">
                  {{ targetPitch.is_correct ? `距好球帶邊界 ${targetPitch.dist_cm} cm (${targetPitch.true_call === 'STRIKE' ? '帶內' : '帶外'})` : `誤差 ${targetPitch.dist_cm} cm` }}
                </span>
              </div>
              <span class="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                球數: {{ targetPitch.count_b }}-{{ targetPitch.count_s }} | {{ targetPitch.pitch_type || '快速球' }} {{ targetPitch.speed_kmh ? targetPitch.speed_kmh + ' km/h' : '' }} | {{ targetPitch.content }}
              </span>
            </div>
          </div>

          <!-- Target Calls Badge -->
          <div class="flex items-center gap-3 self-end md:self-center shrink-0">
            <div class="flex flex-col items-end">
              <div class="text-xs text-slate-500 dark:text-slate-400">原判呼叫</div>
              <span :class="['font-mono font-black text-sm px-2 py-0.5 rounded', targetPitch.called === 'STRIKE' ? 'bg-red-500/10 text-red-600 dark:text-red-400' : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400']">
                {{ targetPitch.called === 'STRIKE' ? '好球 (STRIKE)' : '壞球 (BALL)' }}
              </span>
            </div>
            <span class="text-slate-400 dark:text-slate-600 font-bold">➔</span>
            <div class="flex flex-col items-start">
              <div class="text-xs text-slate-500 dark:text-slate-400">系統真值</div>
              <span :class="['font-mono font-black text-sm px-2 py-0.5 rounded', targetPitch.true_call === 'STRIKE' ? 'bg-red-500/10 text-red-600 dark:text-red-400' : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400']">
                {{ targetPitch.true_call === 'STRIKE' ? '好球 (STRIKE)' : '壞球 (BALL)' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Search Radius Toolbar -->
        <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
          <!-- Radius Slider -->
          <div class="flex items-center gap-3 w-full sm:w-auto">
            <label class="font-bold text-slate-700 dark:text-slate-300 whitespace-nowrap flex items-center gap-1.5">
              <span>搜尋半徑範圍:</span>
              <span class="font-mono text-blue-600 dark:text-blue-400 font-black text-sm">{{ searchRadiusCm.toFixed(1) }} cm</span>
            </label>
            <input 
              type="range" 
              min="3" 
              max="20" 
              step="0.5" 
              v-model.number="searchRadiusCm"
              class="w-36 sm:w-44 accent-blue-600 cursor-pointer"
            />
          </div>

          <!-- Radius Presets -->
          <div class="flex items-center gap-1.5 w-full sm:w-auto justify-end">
            <span class="text-slate-400 dark:text-slate-500 text-[11px]">快捷預設:</span>
            <button 
              v-for="r in presetRadii" 
              :key="r.val"
              @click="searchRadiusCm = r.val"
              :class="[
                'px-2.5 py-1 rounded-md text-[11px] font-bold transition-all border',
                Math.abs(searchRadiusCm - r.val) < 0.1
                  ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                  : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:text-slate-900 dark:hover:text-white'
              ]"
            >
              {{ r.label }} ({{ r.val }}cm)
            </button>
          </div>
        </div>

        <!-- Umpire Consistency Diagnostic Card -->
        <div class="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col gap-3 shadow-xs">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800/80 pb-2.5">
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                主審在此進壘區域的執法診斷
              </span>
              <span 
                :class="[
                  'px-2 py-0.5 rounded-full text-[11px] font-bold border',
                  consistency.diagnosisType === 'conflict' ? 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/30' :
                  consistency.diagnosisType === 'generous' ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30' :
                  consistency.diagnosisType === 'strict' ? 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/30' :
                  consistency.diagnosisType === 'consistent' ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30' :
                  'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700'
                ]"
              >
                {{ consistency.diagnosisType === 'conflict' ? '⚠️ 判決標準矛盾' : 
                   consistency.diagnosisType === 'generous' ? '📐 好球帶擴張' : 
                   consistency.diagnosisType === 'strict' ? '📐 好球帶偏窄' : 
                   consistency.diagnosisType === 'consistent' ? '✓ 判決高度一致' : '📍 孤立進壘點' }}
              </span>
            </div>

            <div class="text-xs font-mono text-slate-600 dark:text-slate-300">
              鄰近判決總計：<strong class="text-blue-600 dark:text-blue-400 text-sm">{{ similarPitches.length }}</strong> 顆
            </div>
          </div>

          <!-- Diagnosis Description -->
          <div class="text-xs sm:text-sm font-medium text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <span>{{ consistency.diagnosis }}</span>
          </div>

          <!-- Ratio Bars (if any similar pitches) -->
          <div v-if="similarPitches.length > 0" class="flex flex-col gap-1.5 pt-1">
            <div class="flex items-center justify-between text-xs font-mono">
              <span class="text-red-600 dark:text-red-400 font-bold">
                好球 {{ consistency.strikeCount }} 顆 ({{ consistency.strikeRate }}%)
              </span>
              <span class="text-emerald-600 dark:text-emerald-400 font-bold">
                壞球 {{ consistency.ballCount }} 顆 ({{ consistency.ballRate }}%)
              </span>
            </div>
            <!-- Dual Colored Progress Bar -->
            <div class="w-full h-2.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden flex">
              <div 
                class="h-full bg-red-500 transition-all duration-300"
                :style="{ width: consistency.strikeRate + '%' }"
              ></div>
              <div 
                class="h-full bg-emerald-500 transition-all duration-300"
                :style="{ width: consistency.ballRate + '%' }"
              ></div>
            </div>
          </div>
        </div>

        <!-- Main Visual & List Comparison Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
          <!-- Left: Strike Zone Visualizer (lg:col-span-5) -->
          <div class="lg:col-span-5 flex flex-col items-center">
            <!-- View Mode Switcher Header Banner -->
            <div 
              v-if="isInspectingPA" 
              class="w-full mb-2 p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/50 border border-amber-300 dark:border-amber-700/70 flex items-center justify-between gap-2 text-xs shadow-xs animate-in fade-in duration-200"
            >
              <div class="flex items-center gap-1.5 min-w-0">
                <span class="w-2 h-2 rounded-full bg-amber-500 shrink-0"></span>
                <span class="font-bold text-amber-800 dark:text-amber-200 truncate">
                  該球原打席九宮格：{{ activeInspectedPitch.inning_num }}局{{ activeInspectedPitch.inning_half }} {{ activeInspectedPitch.pitcher }} vs {{ activeInspectedPitch.batter }} (第 {{ activeInspectedPitch.pitch_num ?? activeInspectedPitch.pitch_index }} 球)
                </span>
              </div>
              <button 
                @click="activeInspectedPitch = null"
                class="px-2 py-1 rounded-md bg-amber-200 hover:bg-amber-300 dark:bg-amber-800 dark:hover:bg-amber-700 text-amber-900 dark:text-amber-100 font-bold transition-all text-[11px] shrink-0 cursor-pointer shadow-2xs"
              >
                ↩ 還原比對
              </button>
            </div>
            <div 
              v-else 
              class="w-full mb-2 px-1 text-xs text-slate-500 dark:text-slate-400 flex items-center justify-between font-medium"
            >
              <span>🎯 類似進壘點比對視角 (半徑 {{ searchRadiusCm }} cm)</span>
              <span class="text-[11px] text-blue-600 dark:text-blue-400 font-semibold">點擊清單可切換原打席九宮格</span>
            </div>

            <StrikeZoneSVG 
              :pitches="displayPitchesForSVG"
              :sz-top="currentSzTop"
              :sz-bottom="currentSzBottom"
              :target-pitch="isInspectingPA ? null : targetPitch"
              :similar-pitches="isInspectingPA ? [] : similarPitches"
              :search-radius-cm="isInspectingPA ? null : searchRadiusCm"
              :highlighted-pitch="activeInspectedPitch"
              :highlighted-index="currentHighlightedIndex"
              @select-pitch="(n, p) => onSVGSelectPitch(p)"
            />
          </div>

          <!-- Right: Detailed Similar Pitches Table (lg:col-span-7) -->
          <div class="lg:col-span-7 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 flex flex-col gap-3 shadow-xs min-h-[420px]">
            <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
              <div class="flex items-center gap-2">
                <h3 class="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                  半徑 {{ searchRadiusCm }} cm 內的判決明細 (由近至遠排序)
                </h3>
                <span class="text-[11px] text-slate-400">(點擊任一筆切換該球九宮格視角)</span>
              </div>
              <span class="text-xs text-slate-500 font-mono">共 {{ listPitches.length }} 顆 (含基準球)</span>
            </div>

            <!-- Pitches List (Includes Target Pitch at top) -->
            <div class="flex flex-col gap-2 max-h-[380px] overflow-y-auto pr-1">
              <div 
                v-for="(p, idx) in listPitches" 
                :key="'sim-' + idx"
                @mouseenter="hoveredListPitchNum = p.pitch_num ?? p.pitch_index"
                @mouseleave="hoveredListPitchNum = null"
                @click="toggleInspectPitch(p)"
                :class="[
                  'p-3 rounded-lg border transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 text-xs select-none',
                  isPitchActiveInPA(p)
                    ? 'bg-amber-50/90 dark:bg-amber-950/40 border-amber-500 shadow-sm ring-1 ring-amber-500/40'
                    : p.is_target_pitch
                      ? 'bg-amber-50/50 dark:bg-amber-950/20 border-amber-300/80 dark:border-amber-600/40 hover:border-amber-400'
                      : 'bg-slate-50/80 dark:bg-slate-950/60 border-slate-200 dark:border-slate-800 hover:border-blue-400 dark:hover:border-blue-500'
                ]"
              >
                <!-- Left Details -->
                <div class="flex items-start gap-2.5">
                  <!-- Primary Strike Zone Distance Badge -->
                  <div 
                    :class="[
                      'flex flex-col items-center justify-center px-2.5 py-1 rounded shrink-0 font-mono border min-w-[72px]',
                      !p.is_correct
                        ? 'bg-red-50 dark:bg-red-950/60 border-red-200 dark:border-red-800 text-red-700 dark:text-red-300'
                        : p.true_call === 'STRIKE'
                          ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300'
                          : 'bg-slate-100 dark:bg-slate-800/80 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300'
                    ]"
                  >
                    <span class="text-[10px] whitespace-nowrap">
                      {{ !p.is_correct ? '! 誤差' : (p.true_call === 'STRIKE' ? '好球帶內' : '好球帶外') }}
                    </span>
                    <span class="font-bold text-xs">{{ p.dist_cm != null ? p.dist_cm + ' cm' : '-' }}</span>
                  </div>

                  <div class="flex flex-col gap-0.5 min-w-0">
                    <div class="flex items-center gap-1.5 flex-wrap">
                      <span class="font-bold text-slate-900 dark:text-white">
                        {{ p.inning_num }}局{{ p.inning_half }}
                      </span>
                      <span class="text-slate-600 dark:text-slate-300">
                        {{ p.pitcher }} (投) vs {{ p.batter }} (打)
                      </span>
                      <span v-if="p.is_target_pitch" class="px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-400/20 text-amber-700 dark:text-amber-300 border border-amber-400/40">
                        🎯 基準球
                      </span>
                    </div>
                    <span class="text-slate-500 dark:text-slate-400 text-[11px]">
                      球數: {{ p.count_b }}-{{ p.count_s }} | {{ p.speed_kmh ? p.speed_kmh + ' km/h' : '' }} {{ p.pitch_type || '快速球' }} | {{ p.content }}
                    </span>
                    <span class="text-slate-400 dark:text-slate-500 text-[10px] flex items-center gap-2 mt-0.5 font-mono flex-wrap">
                      <span>進壘高度: {{ (p.z * 100).toFixed(1) }} cm</span>
                      <span class="text-sky-600 dark:text-sky-400 font-semibold">
                        距基準球: {{ p.is_target_pitch ? '0.0 cm (基準球)' : p.distance_to_target_cm + ' cm' }}
                      </span>
                    </span>
                  </div>
                </div>

                <!-- Right Call Badges & Toggle Button -->
                <div class="flex items-center sm:flex-col sm:items-end gap-1.5 shrink-0 self-end sm:self-center">
                  <!-- Call Result -->
                  <div class="flex items-center gap-1.5 font-mono font-bold">
                    <span :class="['px-2 py-0.5 rounded text-xs', p.called === 'STRIKE' ? 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20' : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20']">
                      原判: {{ p.called === 'STRIKE' ? '好球' : '壞球' }}
                    </span>
                    <span :class="['text-[11px] font-normal px-1.5 py-0.5 rounded', p.is_correct ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10' : 'text-amber-600 dark:text-amber-400 bg-amber-500/10']">
                      {{ p.is_correct ? '判決正確' : '誤判' }}
                    </span>
                  </div>

                  <!-- Toggle Button -->
                  <div class="flex items-center gap-1.5">
                    <button 
                      @click.stop="toggleInspectPitch(p)"
                      :class="[
                        'px-2 py-0.5 rounded text-[11px] font-bold transition-all border flex items-center gap-1 cursor-pointer',
                        isPitchActiveInPA(p)
                          ? 'bg-amber-500 text-white border-amber-500 shadow-2xs'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-300 dark:border-slate-700 hover:bg-blue-600 hover:text-white'
                      ]"
                    >
                      <span>{{ isPitchActiveInPA(p) ? '✓ 檢視中 (點擊還原)' : '👁️ 原打席九宮格' }}</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="px-5 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/40 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
        <span class="text-slate-500 dark:text-slate-400">
          以基準球進壘點為核心：左右邊界採<strong>本壘板絕對物理公分距</strong>，上下邊界採<strong>打者好球帶相對比例距</strong>進行同場篩選。
        </span>
        <button 
          @click="close"
          class="px-4 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-bold transition-all cursor-pointer self-end sm:self-center"
        >
          關閉
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import StrikeZoneSVG from './StrikeZoneSVG.vue'
import { findSimilarPitches, analyzeConsistency, isSamePitch } from '../utils/pitchGeometry.js'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  targetPitch: {
    type: Object,
    default: null
  },
  allPitches: {
    type: Array,
    default: () => []
  },
  plateAppearances: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close'])

const searchRadiusCm = ref(8.0)
const hoveredListPitchNum = ref(null)
const activeInspectedPitch = ref(null)

const presetRadii = [
  { label: '極近', val: 5.0 },
  { label: '標準球徑', val: 8.0 },
  { label: '邊角帶', val: 12.0 },
  { label: '廣域', val: 16.0 }
]

const similarPitches = computed(() => {
  if (!props.targetPitch || !props.allPitches.length) return []
  return findSimilarPitches(props.targetPitch, props.allPitches, searchRadiusCm.value)
})

const listPitches = computed(() => {
  if (!props.targetPitch) return []
  const targetItem = {
    ...props.targetPitch,
    distance_to_target_cm: 0.0,
    is_target_pitch: true
  }
  return [targetItem, ...similarPitches.value]
})

const consistency = computed(() => {
  return analyzeConsistency(props.targetPitch, similarPitches.value)
})

const activeInspectedPA = computed(() => {
  if (!activeInspectedPitch.value || !props.plateAppearances.length) return null
  const targetPaNum = activeInspectedPitch.value.pa_index ?? activeInspectedPitch.value.pa_num
  return props.plateAppearances.find(pa => pa.pa_num === targetPaNum) || null
})

const isInspectingPA = computed(() => {
  return !!activeInspectedPA.value
})

const displayPitchesForSVG = computed(() => {
  if (isInspectingPA.value && activeInspectedPitch.value) {
    // 僅帶入該打席九宮格和該球而已，該打席的其他球數和基準球都不出現
    return [activeInspectedPitch.value]
  }
  // 預設類似進壘點集群模式：顯示基準球與半徑內候選球
  if (!props.targetPitch) return []
  return [props.targetPitch, ...similarPitches.value]
})

const currentSzTop = computed(() => {
  if (isInspectingPA.value && activeInspectedPitch.value) {
    return activeInspectedPitch.value.sz_top || activeInspectedPA.value?.pitches?.[0]?.sz_top || 0.963
  }
  return props.targetPitch?.sz_top || 0.963
})

const currentSzBottom = computed(() => {
  if (isInspectingPA.value && activeInspectedPitch.value) {
    return activeInspectedPitch.value.sz_bottom || activeInspectedPA.value?.pitches?.[0]?.sz_bottom || 0.486
  }
  return props.targetPitch?.sz_bottom || 0.486
})

const currentHighlightedIndex = computed(() => {
  if (isInspectingPA.value && activeInspectedPitch.value) {
    return activeInspectedPitch.value.pitch_num ?? activeInspectedPitch.value.pitch_index
  }
  return hoveredListPitchNum.value
})

function isPitchActiveInPA(p) {
  if (!activeInspectedPitch.value || !p) return false
  return isSamePitch(activeInspectedPitch.value, p)
}

function toggleInspectPitch(pitch) {
  if (isPitchActiveInPA(pitch)) {
    activeInspectedPitch.value = null
  } else {
    activeInspectedPitch.value = pitch
  }
}

function onSVGSelectPitch(pitch) {
  if (!pitch) return
  toggleInspectPitch(pitch)
}

watch(() => props.targetPitch, () => {
  activeInspectedPitch.value = null
  hoveredListPitchNum.value = null
})

function close() {
  activeInspectedPitch.value = null
  emit('close')
}

function handleKeydown(e) {
  if (e.key === 'Escape' && props.isOpen) {
    close()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>
