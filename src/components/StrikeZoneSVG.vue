<template>
  <div class="relative flex flex-col items-center bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm dark:shadow-xl select-none transition-colors">
    <!-- View Switcher Toolbar -->
    <div class="w-full flex items-center justify-between mb-3 text-xs">
      <!-- Missed Mode Legend with Team Colors -->
      <div v-if="isMissedMode" class="flex items-center gap-2 font-bold text-slate-700 dark:text-slate-300 flex-wrap">
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-3 h-3 rounded-full shadow-xs" :style="{ backgroundColor: visitingTeamColor }"></span>
          <span>{{ visitingTeam || '客隊' }} 得利</span>
        </span>
        <span class="flex items-center gap-1.5 ml-2">
          <span class="inline-block w-3 h-3 rounded-full shadow-xs" :style="{ backgroundColor: homeTeamColor }"></span>
          <span>{{ homeTeam || '主隊' }} 得利</span>
        </span>
        <span v-if="targetPitch" class="inline-block px-1.5 py-0.5 rounded text-[10px] bg-amber-400/20 text-amber-700 dark:text-amber-300 border border-amber-400/40 ml-1.5 font-bold">🎯 基準球</span>
      </div>
      <!-- Normal Mode Legend -->
      <div v-else class="flex items-center gap-1.5 font-medium text-slate-700 dark:text-slate-300 flex-wrap">
        <span class="inline-block w-2.5 h-2.5 rounded-full bg-red-500"></span> 好球
        <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500 ml-1.5"></span> 壞球
        <span class="inline-block px-1.5 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-600 dark:text-amber-300 border border-amber-500/30 dark:border-amber-500/40 ml-1.5 font-bold">! 誤判</span>
        <span v-if="targetPitch" class="inline-block px-1.5 py-0.5 rounded text-[10px] bg-amber-400/20 text-amber-700 dark:text-amber-300 border border-amber-400/40 ml-1.5 font-bold">🎯 基準球 (黃色)</span>
      </div>

      <div class="flex items-center gap-2">
        <label class="flex items-center gap-1.5 cursor-pointer text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white">
          <input type="checkbox" v-model="showTrajectory" class="rounded bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-blue-600 focus:ring-0">
          <span>軌跡</span>
        </label>
        <label class="flex items-center gap-1.5 cursor-pointer text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white ml-2">
          <input type="checkbox" v-model="showNumbers" class="rounded bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-blue-600 focus:ring-0">
          <span>編號</span>
        </label>
      </div>
    </div>

    <!-- SVG Container -->
    <div class="relative flex justify-center items-center w-[360px] h-[400px] bg-slate-100/70 dark:bg-gradient-to-b dark:from-slate-950 dark:to-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden shadow-inner transition-colors">
      <svg 
        class="w-full h-full"
        viewBox="0 0 400 450"
        @mousemove="onMouseMove"
        @mouseleave="hoveredPitch = null"
      >
        <!-- Background Strike Zone Plate Visual (Home Plate) -->
        <polygon 
          points="200,430 260,390 260,370 140,370 140,390" 
          class="fill-slate-200 dark:fill-slate-800 stroke-slate-300 dark:stroke-slate-700" 
          stroke-width="2"
          opacity="0.9"
        />

        <!-- Strike Zone (九宮格) outer box and 3x3 grids -->
        <g id="strike-zone-grid">
          <!-- Main Outer Rectangle -->
          <rect 
            :x="szBox.x" 
            :y="szBox.y" 
            :width="szBox.width" 
            :height="szBox.height" 
            class="fill-white/60 dark:fill-slate-900/40 stroke-slate-800 dark:stroke-slate-300" 
            stroke-width="2.5"
            rx="2"
          />

          <!-- 3x3 Grid Lines -->
          <line 
            :x1="szBox.x + szBox.width / 3" 
            :y1="szBox.y" 
            :x2="szBox.x + szBox.width / 3" 
            :y2="szBox.y + szBox.height" 
            class="stroke-slate-300 dark:stroke-slate-700" 
            stroke-width="1.2" 
            stroke-dasharray="3,3"
          />
          <line 
            :x1="szBox.x + (szBox.width * 2) / 3" 
            :y1="szBox.y" 
            :x2="szBox.x + (szBox.width * 2) / 3" 
            :y2="szBox.y + szBox.height" 
            class="stroke-slate-300 dark:stroke-slate-700" 
            stroke-width="1.2" 
            stroke-dasharray="3,3"
          />

          <line 
            :x1="szBox.x" 
            :y1="szBox.y + szBox.height / 3" 
            :x2="szBox.x + szBox.width" 
            :y2="szBox.y + szBox.height / 3" 
            class="stroke-slate-300 dark:stroke-slate-700" 
            stroke-width="1.2" 
            stroke-dasharray="3,3"
          />
          <line 
            :x1="szBox.x" 
            :y1="szBox.y + (szBox.height * 2) / 3" 
            :x2="szBox.x + szBox.width" 
            :y2="szBox.y + (szBox.height * 2) / 3" 
            class="stroke-slate-300 dark:stroke-slate-700" 
            stroke-width="1.2" 
            stroke-dasharray="3,3"
          />
        </g>

        <!-- Radar Search Radius Circle around Target Pitch -->
        <g v-if="targetCenter && searchRadiusCm > 0" class="pointer-events-none">
          <!-- Background Radius Fill and Perimeter -->
          <ellipse 
            :cx="targetCenter.x" 
            :cy="targetCenter.y" 
            :rx="radarRadiusPx.x" 
            :ry="radarRadiusPx.y" 
            fill="rgba(56, 189, 248, 0.12)"
            stroke="#0284c7"
            stroke-width="1.8"
            stroke-dasharray="5,4"
          />
          <!-- Crosshair Center Indicator -->
          <line 
            :x1="targetCenter.x - 6" 
            :y1="targetCenter.y" 
            :x2="targetCenter.x + 6" 
            :y2="targetCenter.y" 
            stroke="#0284c7" 
            stroke-width="1.5" 
          />
          <line 
            :x1="targetCenter.x" 
            :y1="targetCenter.y - 6" 
            :x2="targetCenter.x" 
            :y2="targetCenter.y + 6" 
            stroke="#0284c7" 
            stroke-width="1.5" 
          />
          <!-- Radius Tag Text -->
          <text 
            :x="targetCenter.x" 
            :y="Math.max(15, targetCenter.y - radarRadiusPx.y - 4)" 
            text-anchor="middle" 
            font-size="10" 
            font-weight="bold" 
            fill="#0284c7"
            class="select-none"
          >
            半徑 {{ searchRadiusCm }} cm ({{ similarPitches.length }} 顆)
          </text>
        </g>

        <!-- Trajectory Arcs (if enabled) -->
        <g v-if="showTrajectory">
          <path 
            v-for="(p, idx) in visiblePitches" 
            :key="'traj-' + idx"
            :d="calculateTrajectoryPath(p)"
            fill="none"
            :stroke="getTrajectoryStroke(p)"
            stroke-width="2.5"
            stroke-linecap="round"
            :opacity="getPitchOpacity(p)"
          />
        </g>

        <!-- Pitches Circles -->
        <g v-for="(p, idx) in visiblePitches" :key="'pitch-' + idx">
          <!-- Outer Halo for Missed Calls -->
          <circle 
            v-if="p.is_called_pitch && !p.is_correct && !isTarget(p)"
            :cx="mapX(p.x)"
            :cy="mapZ(p.z, p.sz_top, p.sz_bottom)"
            r="19"
            fill="rgba(245, 158, 11, 0.3)"
            stroke="#f59e0b"
            stroke-width="2.2"
            class="animate-pulse"
            :opacity="getPitchOpacity(p)"
          />

          <!-- Target Pitch Special Halo / Ring (Yellow/Amber) -->
          <circle 
            v-if="isTarget(p)"
            :cx="mapX(p.x)"
            :cy="mapZ(p.z, p.sz_top, p.sz_bottom)"
            r="20"
            fill="rgba(234, 179, 8, 0.25)"
            stroke="#eab308"
            stroke-width="2.5"
          />

          <!-- Similar Pitch Ring -->
          <circle 
            v-if="isSimilar(p)"
            :cx="mapX(p.x)"
            :cy="mapZ(p.z, p.sz_top, p.sz_bottom)"
            r="17.5"
            fill="none"
            stroke="#38bdf8"
            stroke-width="2"
          />

          <!-- Selected / Highlighted ring -->
          <circle 
            v-if="highlightedIndex === (p.pitch_num ?? p.pitch_index)"
            :cx="mapX(p.x)"
            :cy="mapZ(p.z, p.sz_top, p.sz_bottom)"
            r="18"
            fill="none"
            stroke="#6366f1"
            stroke-width="3"
          />

          <!-- Main Pitch Dot -->
          <circle 
            :cx="mapX(p.x)"
            :cy="mapZ(p.z, p.sz_top, p.sz_bottom)"
            :r="isTarget(p) ? 15.5 : 14"
            :fill="getPitchColor(p)"
            :stroke="isTarget(p) ? '#ca8a04' : (p.is_called_pitch ? '#ffffff' : '#94a3b8')"
            :stroke-width="isTarget(p) ? 2.5 : 1.8"
            :opacity="getPitchOpacity(p)"
            class="cursor-pointer transition-all duration-150 hover:opacity-100 shadow-sm"
            @mouseenter="hoveredPitch = p"
            @click="$emit('select-pitch', p.pitch_num ?? p.pitch_index, p)"
          />

          <!-- Pitch Number / Target Icon Text -->
          <text 
            v-if="isTarget(p)"
            :x="mapX(p.x)"
            :y="mapZ(p.z, p.sz_top, p.sz_bottom) + 4.5"
            text-anchor="middle"
            font-size="12"
            font-weight="bold"
            fill="#ffffff"
            class="pointer-events-none select-none drop-shadow"
          >
            🎯
          </text>
          <text 
            v-else-if="showNumbers"
            :x="mapX(p.x)"
            :y="mapZ(p.z, p.sz_top, p.sz_bottom) + 4.5"
            text-anchor="middle"
            font-size="11"
            font-weight="bold"
            fill="#ffffff"
            :opacity="getPitchOpacity(p)"
            class="pointer-events-none select-none drop-shadow"
          >
            {{ p.pitch_num ?? p.pitch_index ?? (idx + 1) }}
          </text>
        </g>
      </svg>

      <!-- Floating Tooltip on Hover -->
      <div 
        v-if="hoveredPitch" 
        class="absolute z-30 pointer-events-none bg-white/95 dark:bg-slate-950/95 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg p-2.5 shadow-2xl backdrop-blur-sm text-xs min-w-[190px]"
        :style="{ left: tooltipPos.x + 'px', top: tooltipPos.y + 'px' }"
      >
        <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-1 mb-1.5 font-bold">
          <span class="text-blue-600 dark:text-blue-400">
            {{ isTarget(hoveredPitch) ? '🎯 基準誤判球' : `第 ${hoveredPitch.pitch_num ?? hoveredPitch.pitch_index ?? ''} 球` }}
            <span v-if="hoveredPitch.inning_num" class="text-slate-500 text-[10px]">({{ hoveredPitch.inning_num }}局{{ hoveredPitch.inning_half }})</span>
          </span>
          <span class="text-slate-500 dark:text-slate-400 font-mono">{{ hoveredPitch.speed_kmh ? hoveredPitch.speed_kmh + ' km/h' : '' }}</span>
        </div>

        <div v-if="hoveredPitch.pitcher || hoveredPitch.batter" class="text-slate-600 dark:text-slate-300 text-[11px] mb-1">
          對戰：<span class="text-slate-900 dark:text-white font-medium">{{ hoveredPitch.pitcher }} vs {{ hoveredPitch.batter }}</span>
        </div>

        <div class="text-slate-600 dark:text-slate-300 text-[11px] mb-1">
          球種：<span class="text-slate-900 dark:text-white font-medium">{{ hoveredPitch.pitch_type || '快速球' }}</span>
        </div>

        <div v-if="hoveredPitch.content" class="text-slate-600 dark:text-slate-300 text-[11px] mb-1">
          事件：<span class="text-slate-800 dark:text-slate-200">{{ hoveredPitch.content }}</span>
        </div>

        <div v-if="hoveredPitch.is_called_pitch ?? (hoveredPitch.called != null)" class="mt-1.5 pt-1.5 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div>
            原判：<span :class="hoveredPitch.called === 'STRIKE' ? 'text-red-500 font-bold' : 'text-emerald-500 font-bold'">{{ hoveredPitch.called === 'STRIKE' ? '好球' : '壞球' }}</span>
          </div>
          <div>
            真值：<span class="text-amber-500 font-bold">{{ hoveredPitch.true_call === 'STRIKE' ? '好球' : '壞球' }}</span>
          </div>
        </div>

        <div v-if="hoveredPitch.dist_cm != null && !hoveredPitch.is_correct" class="mt-1 flex items-center justify-between text-[11px] font-bold">
          <span class="text-amber-600 dark:text-amber-400">誤差距離：{{ hoveredPitch.dist_cm }} cm</span>
          <span v-if="hoveredPitch.favored_team" class="text-blue-600 dark:text-blue-400 font-bold">
            {{ hoveredPitch.favored_team }}得利
          </span>
        </div>

        <div v-if="hoveredPitch.distance_to_target_cm != null" class="mt-1 text-sky-600 dark:text-sky-400 text-[11px] font-bold border-t border-slate-200 dark:border-slate-800/80 pt-1">
          📍 距基準球：{{ hoveredPitch.distance_to_target_cm }} cm
        </div>
      </div>
    </div>

    <!-- Catcher View Label -->
    <div class="mt-2 text-center text-xs font-medium text-slate-500 dark:text-slate-400">
      捕手視角 (Catcher View)
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { getTeamColorInfo } from '../utils/teamColors.js'

const props = defineProps({
  pitches: {
    type: Array,
    default: () => []
  },
  szTop: {
    type: Number,
    default: 0.963
  },
  szBottom: {
    type: Number,
    default: 0.486
  },
  highlightedIndex: {
    type: Number,
    default: null
  },
  targetPitch: {
    type: Object,
    default: null
  },
  similarPitches: {
    type: Array,
    default: () => []
  },
  searchRadiusCm: {
    type: Number,
    default: null
  },
  isMissedMode: {
    type: Boolean,
    default: false
  },
  homeTeam: {
    type: String,
    default: '主隊'
  },
  visitingTeam: {
    type: String,
    default: '客隊'
  }
})

defineEmits(['select-pitch'])

const showTrajectory = ref(true)
const showNumbers = ref(true)
const hoveredPitch = ref(null)
const tooltipPos = ref({ x: 0, y: 0 })

const svgW = 400
const svgH = 450
const xMin = -0.5
const xMax = 0.5
const zMin = 0.15
const zMax = 1.25

const visitingTeamColor = computed(() => getTeamColorInfo(props.visitingTeam).pitchColor)
const homeTeamColor = computed(() => getTeamColorInfo(props.homeTeam).pitchColor)

const szBox = computed(() => {
  const leftX = mapX(0.22)
  const rightX = mapX(-0.22)
  const topY = mapZ(props.szTop, props.szTop, props.szBottom)
  const bottomY = mapZ(props.szBottom, props.szTop, props.szBottom)
  return {
    x: leftX,
    y: topY,
    width: rightX - leftX,
    height: bottomY - topY
  }
})

const visiblePitches = computed(() => {
  return props.pitches.filter(p => p.x !== null && p.z !== null)
})

const targetCenter = computed(() => {
  if (!props.targetPitch || props.targetPitch.x == null || props.targetPitch.z == null) return null
  return {
    x: mapX(props.targetPitch.x),
    y: mapZ(props.targetPitch.z, props.targetPitch.sz_top || props.szTop, props.targetPitch.sz_bottom || props.szBottom)
  }
})

const radarRadiusPx = computed(() => {
  if (!props.searchRadiusCm) return { x: 0, y: 0 }
  // 1 meter = 400px in X; 1 meter = 450 / 1.1 = 409.09px in Z
  return {
    x: (props.searchRadiusCm / 100) * 400,
    y: (props.searchRadiusCm / 100) * (svgH / (zMax - zMin))
  }
})

function isTarget(pitch) {
  if (!props.targetPitch || !pitch) return false
  if (pitch === props.targetPitch) return true
  const targetPa = props.targetPitch.pa_index ?? props.targetPitch.pa_num
  const pPa = pitch.pa_index ?? pitch.pa_num
  const targetPitchIdx = props.targetPitch.pitch_index ?? props.targetPitch.pitch_num
  const pPitchIdx = pitch.pitch_index ?? pitch.pitch_num

  if (targetPa != null && pPa != null && targetPa === pPa && targetPitchIdx != null && pPitchIdx != null) {
    return targetPitchIdx === pPitchIdx
  }

  return (
    Math.abs(pitch.x - props.targetPitch.x) < 0.0005 &&
    Math.abs(pitch.z - props.targetPitch.z) < 0.0005 &&
    pitch.inning_num === props.targetPitch.inning_num &&
    pitch.called === props.targetPitch.called
  )
}

function isSimilar(pitch) {
  if (!props.similarPitches || props.similarPitches.length === 0 || !pitch) return false
  return props.similarPitches.some(sp => {
    if (sp === pitch) return true
    const spPa = sp.pa_index ?? sp.pa_num
    const pPa = pitch.pa_index ?? pitch.pa_num
    const spPitchIdx = sp.pitch_index ?? sp.pitch_num
    const pPitchIdx = pitch.pitch_index ?? pitch.pitch_num
    if (spPa != null && pPa != null && spPa === pPa && spPitchIdx != null && pPitchIdx != null) {
      return spPitchIdx === pPitchIdx
    }
    return (
      Math.abs(sp.x - pitch.x) < 0.0005 &&
      Math.abs(sp.z - pitch.z) < 0.0005 &&
      sp.inning_num === pitch.inning_num &&
      sp.called === pitch.called
    )
  })
}

function getPitchOpacity(pitch) {
  // If target pitch mode is active and pitch is neither target nor similar, dim it down
  if (props.targetPitch && props.similarPitches?.length >= 0) {
    if (isTarget(pitch) || isSimilar(pitch)) {
      return 1.0
    }
    return 0.25
  }
  return 1.0
}

function mapX(x) {
  return ((xMax - x) / (xMax - xMin)) * svgW
}

function mapZ(z, top, bot) {
  const pTop = top || props.szTop
  const pBot = bot || props.szBottom
  const h = pTop - pBot > 0 ? pTop - pBot : (props.szTop - props.szBottom || 1)
  const normRatio = (z - pBot) / h
  const normZ = props.szBottom + normRatio * (props.szTop - props.szBottom)
  return svgH - ((normZ - zMin) / (zMax - zMin)) * svgH
}

function getFavoredTeamForPitch(pitch) {
  if (!pitch) return ''
  if (pitch.favored_team) return pitch.favored_team
  const vName = props.visitingTeam || '客隊'
  const hName = props.homeTeam || '主隊'
  const isInningTop = pitch.inning_half === '上' || (typeof pitch.inning === 'string' && pitch.inning.includes('上'))
  const isStrikeCalledBall = (pitch.true_call === 'STRIKE' && pitch.called === 'BALL') || pitch.advantage === 'BATTER'
  const isBallCalledStrike = (pitch.true_call === 'BALL' && pitch.called === 'STRIKE') || pitch.advantage === 'PITCHER'
  if (isInningTop) {
    if (isStrikeCalledBall) return vName
    if (isBallCalledStrike) return hName
  } else {
    if (isStrikeCalledBall) return hName
    if (isBallCalledStrike) return vName
  }
  return ''
}

function getPitchColor(pitch) {
  if (isTarget(pitch)) {
    return '#eab308'
  }
  // 在誤判顯示模式下，捕手視角的球改用得利隊伍的顏色
  if (props.isMissedMode) {
    const team = getFavoredTeamForPitch(pitch)
    if (team) {
      return getTeamColorInfo(team).pitchColor
    }
  }
  if (pitch.called === 'STRIKE') {
    return '#ef4444'
  } else if (pitch.called === 'BALL') {
    return '#10b981'
  } else {
    return '#94a3b8'
  }
}

function getTrajectoryStroke(pitch) {
  if (props.isMissedMode) {
    return getPitchColor(pitch)
  }
  return pitch.called === 'STRIKE' ? 'rgba(239, 68, 68, 0.7)' : 'rgba(16, 185, 129, 0.7)'
}

function calculateTrajectoryPath(p) {
  const targetX = mapX(p.x)
  const targetY = mapZ(p.z, p.sz_top, p.sz_bottom)
  const startX = targetX + (p.x > 0 ? -12 : 12)
  const startY = targetY - 140
  const ctrlX = (startX + targetX) / 2 + (p.x > 0 ? 8 : -8)
  const ctrlY = (startY + targetY) / 2 - 20
  return `M ${startX} ${startY} Q ${ctrlX} ${ctrlY} ${targetX} ${targetY}`
}

function onMouseMove(e) {
  const rect = e.currentTarget.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top
  tooltipPos.value = {
    x: Math.min(Math.max(10, mouseX + 15), 180),
    y: Math.min(Math.max(10, mouseY - 40), 280)
  }
}
</script>

