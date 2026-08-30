<template>
  <div class="flex flex-col gap-4">
    <!-- Inning Filter Bar -->
    <div class="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs no-scrollbar">
      <button 
        v-for="inn in availableInnings" 
        :key="inn"
        @click="selectedInning = inn"
        :class="[
          'px-3 py-1.5 rounded-lg font-bold transition-all shrink-0 border',
          selectedInning === inn 
            ? 'bg-blue-600 text-white border-blue-600 shadow-sm shadow-blue-500/20' 
            : 'bg-white dark:bg-slate-800/80 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700/80 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-white'
        ]"
      >
        {{ inn }}
      </button>
    </div>

    <!-- Main Content Layout: PA List & Details & Strike Zone in 3-column layout -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
      <!-- Left Column: Plate Appearance Cards for Selected Inning (lg:col-span-4) -->
      <div class="lg:col-span-4 flex flex-col gap-2.5 max-h-[640px] overflow-y-auto pr-1">
        <div 
          v-for="pa in filteredPAs" 
          :key="pa.pa_num"
          @click="activePANum = pa.pa_num"
          :class="[
            'p-3 rounded-xl border transition-all cursor-pointer flex flex-col gap-2',
            activePANum === pa.pa_num 
              ? 'bg-blue-50/90 dark:bg-slate-800/90 border-blue-500 shadow-xs dark:shadow-lg dark:shadow-blue-500/10' 
              : 'bg-white dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
          ]"
        >
          <!-- PA Top Header -->
          <div class="flex items-center justify-between text-xs">
            <span class="font-bold text-blue-600 dark:text-blue-400">第 {{ pa.pa_num }} 打席 ({{ pa.inning }})</span>
            <!-- Base Diamond & Out Status -->
            <div class="flex items-center gap-2">
              <svg width="20" height="20" viewBox="0 0 50 50" class="inline-block">
                <polygon points="25,5 35,15 25,25 15,15" :fill="pa.game_state.bases['2B'] ? '#ef4444' : '#94a3b8'" stroke="#64748b" stroke-width="1.5"/>
                <polygon points="35,15 45,25 35,35 25,25" :fill="pa.game_state.bases['1B'] ? '#ef4444' : '#94a3b8'" stroke="#64748b" stroke-width="1.5"/>
                <polygon points="15,15 25,25 15,35 5,25" :fill="pa.game_state.bases['3B'] ? '#ef4444' : '#94a3b8'" stroke="#64748b" stroke-width="1.5"/>
              </svg>
              <!-- Out count dots -->
              <div class="flex items-center gap-1">
                <span :class="['w-2 h-2 rounded-full', pa.game_state.outs >= 1 ? 'bg-red-500' : 'bg-slate-300 dark:bg-slate-700']"></span>
                <span :class="['w-2 h-2 rounded-full', pa.game_state.outs >= 2 ? 'bg-red-500' : 'bg-slate-300 dark:bg-slate-700']"></span>
              </div>
            </div>
          </div>

          <!-- Matchup Info -->
          <div class="flex items-center gap-3">
            <img 
              :src="pa.batter.img || 'https://www.cpbl.com.tw/images/default-player.png'" 
              :alt="pa.batter.name"
              class="w-10 h-10 rounded-full object-cover border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 shrink-0"
              onerror="this.src='https://www.cpbl.com.tw/images/default-player.png'"
            />
            <div class="flex flex-col min-w-0">
              <span class="font-bold text-sm text-slate-900 dark:text-white truncate">
                #{{ pa.batter.uniform_no }} {{ pa.batter.name }}
              </span>
              <span class="text-xs text-slate-500 dark:text-slate-400 truncate">
                投手: #{{ pa.pitcher.uniform_no }} {{ pa.pitcher.name }} (用球數: {{ pa.pitches.length }})
              </span>
            </div>
          </div>

          <!-- Outcome Badge -->
          <div class="flex items-center justify-between text-xs pt-1 border-t border-slate-100 dark:border-slate-800/80">
            <span class="text-slate-700 dark:text-slate-300 font-medium truncate max-w-[200px]">{{ pa.outcome }}</span>
            <span v-if="hasMissedCall(pa)" class="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 dark:bg-amber-500/20 text-amber-600 dark:text-amber-300 border border-amber-500/30 dark:border-amber-500/40 font-bold shrink-0">
              有誤判
            </span>
          </div>
        </div>
      </div>

      <!-- Middle Column: Pitch Breakdown Table (lg:col-span-4) -->
      <div v-if="activePA" class="lg:col-span-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-xs dark:shadow-none flex flex-col gap-3">
        <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2.5">
          <div>
            <span class="text-xs text-blue-600 dark:text-blue-400 font-bold uppercase tracking-wider">{{ activePA.inning }} 打席詳情</span>
            <h3 class="text-sm font-bold text-slate-900 dark:text-white mt-0.5 truncate max-w-[200px]">
              #{{ activePA.batter.uniform_no }} {{ activePA.batter.name }} vs #{{ activePA.pitcher.uniform_no }} {{ activePA.pitcher.name }}
            </h3>
          </div>
          <span class="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 font-mono text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
            {{ activePA.batter.height }} cm
          </span>
        </div>

        <!-- Pitch by Pitch List -->
        <div class="flex flex-col gap-2 overflow-y-auto max-h-[520px] pr-1">
          <div 
            v-for="p in activePA.pitches" 
            :key="p.pitch_num"
            @click="highlightedPitchNum = p.pitch_num"
            :class="[
              'p-2.5 rounded-lg border transition-all cursor-pointer flex items-start gap-2.5 text-xs',
              highlightedPitchNum === p.pitch_num 
                ? 'bg-blue-50/80 dark:bg-blue-950/40 border-blue-400 dark:border-blue-500/60 shadow-xs' 
                : 'bg-slate-50 dark:bg-slate-950/60 border-slate-200 dark:border-slate-800/80 hover:border-slate-300 dark:hover:border-slate-700'
            ]"
          >
            <!-- Pitch Number badge -->
            <span 
              :class="[
                'w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs shrink-0 text-white shadow-xs',
                p.called === 'STRIKE' ? 'bg-red-500' : (p.called === 'BALL' ? 'bg-emerald-500' : 'bg-slate-400 dark:bg-slate-600')
              ]"
            >
              {{ p.pitch_num }}
            </span>

            <!-- Pitch content & speed -->
            <div class="flex-1 flex flex-col gap-1">
              <div class="flex items-center justify-between">
                <span class="font-bold text-slate-800 dark:text-slate-200">{{ p.content }}</span>
                <span class="text-slate-500 dark:text-slate-400 font-mono text-[11px]">{{ p.speed_kmh ? p.speed_kmh + ' km/h' : '' }} {{ p.pitch_type }}</span>
              </div>
              <div class="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
                <span>球數: {{ p.count_b }}-{{ p.count_s }}</span>
                <div v-if="p.is_called_pitch" class="flex items-center gap-1.5 flex-wrap justify-end">
                  <span :class="p.is_correct ? 'text-emerald-600 dark:text-emerald-400 font-medium' : 'text-amber-600 dark:text-amber-400 font-bold'">
                    {{ p.is_correct ? '✓ 判決正確' : '! 誤判 (' + p.dist_cm + ' cm)' }}
                  </span>
                  <span 
                    v-if="!p.is_correct && getFavoredTeamText(p, activePA)" 
                    class="px-1.5 py-0.2 rounded bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 text-[10px] font-bold"
                  >
                    {{ getFavoredTeamText(p, activePA) }}
                  </span>
                  <!-- Similar Pitch Button -->
                  <button 
                    v-if="!p.is_correct || p.is_called_pitch"
                    @click.stop="openSimilarPitchModal(p, activePA)"
                    class="px-1.5 py-0.5 rounded bg-blue-50 hover:bg-blue-600 dark:bg-blue-900/30 dark:hover:bg-blue-600 text-blue-600 hover:text-white dark:text-blue-300 dark:hover:text-white font-bold transition-all border border-blue-200 dark:border-blue-700/60 text-[10px] flex items-center gap-0.5 cursor-pointer"
                    title="比對同場相近進壘點判決"
                  >
                    <span>📍 類似點</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Interactive Strike Zone (lg:col-span-4) -->
      <div v-if="activePA" class="lg:col-span-4 flex flex-col items-center">
        <StrikeZoneSVG 
          :pitches="activePA.pitches"
          :sz-top="activePA.pitches[0]?.sz_top || 0.95"
          :sz-bottom="activePA.pitches[0]?.sz_bottom || 0.48"
          :highlighted-index="highlightedPitchNum"
          @select-pitch="(n) => highlightedPitchNum = n"
        />
      </div>
    </div>

    <!-- Similar Pitch Modal -->
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
import { ref, computed, watch } from 'vue'
import StrikeZoneSVG from './StrikeZoneSVG.vue'
import SimilarPitchModal from './SimilarPitchModal.vue'

const props = defineProps({
  plateAppearances: {
    type: Array,
    default: () => []
  },
  allPitches: {
    type: Array,
    default: () => []
  }
})

const availableInnings = computed(() => {
  const innings = new Set()
  props.plateAppearances.forEach(pa => {
    if (pa.inning) innings.add(pa.inning)
  })
  return Array.from(innings)
})

const selectedInning = ref(availableInnings.value[0] || '1局上')
const activePANum = ref(1)
const highlightedPitchNum = ref(null)

const isSimilarModalOpen = ref(false)
const activeTargetPitch = ref(null)

function openSimilarPitchModal(pitch, pa) {
  const fullPitch = {
    ...pitch,
    pa_index: pa.pa_num,
    pitch_index: pitch.pitch_num,
    inning_num: pa.inning?.replace(/[^0-9]/g, '') || '1',
    inning_half: pa.inning?.includes('上') ? '上' : '下',
    pitcher: pa.pitcher?.name || '',
    batter: pa.batter?.name || '',
    batter_height: pa.batter?.height || null
  }
  activeTargetPitch.value = fullPitch
  isSimilarModalOpen.value = true
}

watch(availableInnings, (newInnings) => {
  if (newInnings.length > 0 && !newInnings.includes(selectedInning.value)) {
    selectedInning.value = newInnings[0]
  }
})

watch(selectedInning, () => {
  const firstPa = filteredPAs.value[0]
  if (firstPa) {
    activePANum.value = firstPa.pa_num
    highlightedPitchNum.value = null
  }
})

const filteredPAs = computed(() => {
  return props.plateAppearances.filter(pa => pa.inning === selectedInning.value)
})

const activePA = computed(() => {
  return props.plateAppearances.find(pa => pa.pa_num === activePANum.value) || props.plateAppearances[0]
})

function hasMissedCall(pa) {
  return pa.pitches?.some(p => p.is_called_pitch && !p.is_correct)
}

function getFavoredTeamText(pitch, pa) {
  if (pitch.favored_team) return `${pitch.favored_team}得利`
  if (!pa) return ''
  const isBatter = (pitch.true_call === 'STRIKE' && pitch.called === 'BALL') || pitch.advantage === 'BATTER'
  const isPitcher = (pitch.true_call === 'BALL' && pitch.called === 'STRIKE') || pitch.advantage === 'PITCHER'
  if (isBatter && pa.batting_team) return `${pa.batting_team}得利`
  if (isPitcher && pa.fielding_team) return `${pa.fielding_team}得利`
  return ''
}
</script>

