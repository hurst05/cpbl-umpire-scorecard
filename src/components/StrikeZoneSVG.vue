<template>
  <div class="relative flex flex-col items-center bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm dark:shadow-xl select-none transition-colors">
    <!-- View Switcher Toolbar -->
    <div class="w-full flex items-center justify-between mb-3 text-xs">
      <div class="flex items-center gap-1.5 font-medium text-slate-700 dark:text-slate-300">
        <span class="inline-block w-2.5 h-2.5 rounded-full bg-red-500"></span> 好球原判
        <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500 ml-2"></span> 壞球原判
        <span class="inline-block px-1.5 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-600 dark:text-amber-300 border border-amber-500/30 dark:border-amber-500/40 ml-2 font-bold">! 誤判</span>
      </div>
      <div class="flex items-center gap-2">
        <label class="flex items-center gap-1.5 cursor-pointer text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white">
          <input type="checkbox" v-model="showTrajectory" class="rounded bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-blue-600 focus:ring-0">
          <span>投球軌跡</span>
        </label>
        <label class="flex items-center gap-1.5 cursor-pointer text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white ml-2">
          <input type="checkbox" v-model="showNumbers" class="rounded bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-blue-600 focus:ring-0">
          <span>球數編號</span>
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

        <!-- Trajectory Arcs (if enabled) -->
        <g v-if="showTrajectory">
          <path 
            v-for="(p, idx) in visiblePitches" 
            :key="'traj-' + idx"
            :d="calculateTrajectoryPath(p)"
            fill="none"
            :stroke="p.called === 'STRIKE' ? 'rgba(239, 68, 68, 0.7)' : 'rgba(16, 185, 129, 0.7)'"
            stroke-width="2.5"
            stroke-linecap="round"
          />
        </g>

        <!-- Pitches Circles -->
        <g v-for="(p, idx) in visiblePitches" :key="'pitch-' + idx">
          <!-- Outer Halo for Missed Calls -->
          <circle 
            v-if="p.is_called_pitch && !p.is_correct"
            :cx="mapX(p.x)"
            :cy="mapZ(p.z, p.sz_top, p.sz_bottom)"
            r="19"
            fill="rgba(245, 158, 11, 0.3)"
            stroke="#f59e0b"
            stroke-width="2.2"
            class="animate-pulse"
          />

          <!-- Selected / Highlighted ring -->
          <circle 
            v-if="highlightedIndex === p.pitch_num"
            :cx="mapX(p.x)"
            :cy="mapZ(p.z, p.sz_top, p.sz_bottom)"
            r="18"
            fill="none"
            stroke="#0284c7"
            stroke-width="3"
          />

          <!-- Main Pitch Dot -->
          <circle 
            :cx="mapX(p.x)"
            :cy="mapZ(p.z, p.sz_top, p.sz_bottom)"
            r="14.5"
            :fill="getPitchColor(p)"
            :stroke="p.is_called_pitch ? '#ffffff' : '#94a3b8'"
            stroke-width="1.8"
            class="cursor-pointer transition-all duration-150 hover:opacity-90 shadow-sm"
            @mouseenter="hoveredPitch = p"
            @click="$emit('select-pitch', p.pitch_num)"
          />

          <!-- Pitch Number Text -->
          <text 
            v-if="showNumbers"
            :x="mapX(p.x)"
            :y="mapZ(p.z, p.sz_top, p.sz_bottom) + 4.5"
            text-anchor="middle"
            font-size="12"
            font-weight="bold"
            fill="#ffffff"
            class="pointer-events-none select-none drop-shadow"
          >
            {{ p.pitch_num }}
          </text>
        </g>
      </svg>

      <!-- Floating Tooltip on Hover -->
      <div 
        v-if="hoveredPitch" 
        class="absolute z-30 pointer-events-none bg-white/95 dark:bg-slate-950/95 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg p-2.5 shadow-2xl backdrop-blur-sm text-xs min-w-[180px]"
        :style="{ left: tooltipPos.x + 'px', top: tooltipPos.y + 'px' }"
      >
        <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-1 mb-1.5 font-bold">
          <span class="text-blue-600 dark:text-blue-400">第 {{ hoveredPitch.pitch_num }} 球</span>
          <span class="text-slate-500 dark:text-slate-400 font-mono">{{ hoveredPitch.speed_kmh ? hoveredPitch.speed_kmh + ' km/h' : '' }}</span>
        </div>
        <div class="text-slate-600 dark:text-slate-300 text-[11px] mb-1">
          球種：<span class="text-slate-900 dark:text-white font-medium">{{ hoveredPitch.pitch_type }}</span>
        </div>
        <div class="text-slate-600 dark:text-slate-300 text-[11px] mb-1">
          事件：<span class="text-slate-800 dark:text-slate-200">{{ hoveredPitch.content }}</span>
        </div>
        <div v-if="hoveredPitch.is_called_pitch" class="mt-1.5 pt-1.5 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div>
            原判：<span :class="hoveredPitch.called === 'STRIKE' ? 'text-red-500 font-bold' : 'text-emerald-500 font-bold'">{{ hoveredPitch.called === 'STRIKE' ? '好球' : '壞球' }}</span>
          </div>
          <div>
            真值：<span class="text-amber-500 font-bold">{{ hoveredPitch.true_call === 'STRIKE' ? '好球' : '壞球' }}</span>
          </div>
        </div>
        <div v-if="hoveredPitch.is_called_pitch && !hoveredPitch.is_correct" class="mt-1 text-amber-600 dark:text-amber-400 text-[11px] font-bold">
          誤判距離：{{ hoveredPitch.dist_cm }} cm
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

function mapX(x) {
  return ((xMax - x) / (xMax - xMin)) * svgW
}

function mapZ(z, top, bot) {
  const normZ = props.szBottom + ((z - bot) * (props.szTop - props.szBottom)) / (top - bot || 1)
  return svgH - ((normZ - zMin) / (zMax - zMin)) * svgH
}

function getPitchColor(pitch) {
  if (pitch.called === 'STRIKE') {
    return '#ef4444'
  } else if (pitch.called === 'BALL') {
    return '#10b981'
  } else {
    return '#94a3b8'
  }
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
