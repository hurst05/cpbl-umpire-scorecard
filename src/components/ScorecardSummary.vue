<template>
  <div class="flex flex-col gap-6">
    <!-- Top Scorecard Overview Banner -->
    <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm dark:shadow-xl flex flex-col md:flex-row items-center justify-between gap-6 transition-colors">
      <div>
        <span class="text-xs text-blue-600 dark:text-blue-400 font-bold tracking-wider uppercase">主審執法表現評分卡</span>
        <h2 class="text-2xl font-black text-slate-900 dark:text-white mt-1 flex items-center gap-2">
          主審裁判：{{ metrics.hp_umpire }}
        </h2>
        <div class="text-xs text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-3 flex-wrap">
          <!-- Total called pitches -->
          <div class="group/sumtip relative cursor-help flex items-center gap-1">
            <span class="border-b border-dashed border-slate-400/60 dark:border-slate-500/60">
              本場總判決數：<strong class="font-mono text-slate-800 dark:text-slate-200">{{ metrics.total_called_pitches }}</strong> 顆
            </span>
            <div class="absolute bottom-full left-0 mb-2 hidden group-hover/sumtip:flex flex-col w-56 p-2.5 bg-slate-900 dark:bg-slate-800 text-white text-xs rounded-lg shadow-xl z-50 pointer-events-none border border-slate-700">
              <span class="font-bold text-blue-400 mb-0.5">本場總判決數</span>
              <p class="text-[11px] text-slate-300 leading-relaxed">全場所有打者未出棒（Called Strike / Ball）且具有完整 Trackman 座標的判決球總數。</p>
            </div>
          </div>
          <span>|</span>
          <!-- Effective missed calls -->
          <div class="group/sumtip relative cursor-help flex items-center gap-1">
            <span class="border-b border-dashed border-slate-400/60 dark:border-slate-500/60">
              實質誤判：<strong class="font-mono text-red-600 dark:text-red-400">{{ effectiveMissedCalls.length }}</strong> 顆
            </span>
            <div class="absolute bottom-full left-0 mb-2 hidden group-hover/sumtip:flex flex-col w-60 p-2.5 bg-slate-900 dark:bg-slate-800 text-white text-xs rounded-lg shadow-xl z-50 pointer-events-none border border-slate-700">
              <span class="font-bold text-red-400 mb-0.5">實質誤判數 (Effective Missed)</span>
              <p class="text-[11px] text-slate-300 leading-relaxed">判決與官方好球帶不符，且誤差距離超出當前設定容錯範圍（{{ toleranceCm.toFixed(1) }} cm）的球數。</p>
            </div>
          </div>
          <span>|</span>
          <!-- Avg miss dist -->
          <div class="group/sumtip relative cursor-help flex items-center gap-1">
            <span class="border-b border-dashed border-slate-400/60 dark:border-slate-500/60">
              平均誤差：<strong class="font-mono text-slate-800 dark:text-slate-200">{{ effectiveAvgMissDist }}</strong> cm
            </span>
            <div class="absolute bottom-full left-0 mb-2 hidden group-hover/sumtip:flex flex-col w-60 p-2.5 bg-slate-900 dark:bg-slate-800 text-white text-xs rounded-lg shadow-xl z-50 pointer-events-none border border-slate-700">
              <span class="font-bold text-amber-400 mb-0.5">平均誤判距離 (Avg Miss Distance)</span>
              <p class="text-[11px] text-slate-300 leading-relaxed">所有實質誤判球距離好球帶有效判定邊界的平均物理距離。</p>
              <div class="mt-1 pt-1 border-t border-slate-700 text-[10px] text-slate-400 font-mono">計算：Σ(實質誤判距離) / 實質誤判球數</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Accuracy & Consistency Ring Metrics -->
      <div class="flex items-center gap-4 sm:gap-6 flex-wrap justify-center">
        <!-- Overall Accuracy -->
        <div class="flex flex-col items-center group/ring relative cursor-help">
          <div class="relative w-20 h-20 flex items-center justify-center">
            <svg class="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path class="text-slate-100 dark:text-slate-800 stroke-current" stroke-width="3.5" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              <path class="text-blue-600 dark:text-blue-500 stroke-current transition-all duration-500" :stroke-dasharray="`${effectiveOverallAcc}, 100`" stroke-width="3.5" stroke-linecap="round" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
            </svg>
            <span class="absolute font-bold text-sm text-slate-900 dark:text-white font-mono">{{ effectiveOverallAcc }}%</span>
          </div>
          <span class="text-xs font-bold text-slate-700 dark:text-slate-300 mt-1 border-b border-dotted border-slate-400 dark:border-slate-500">整體準確率</span>
          <span class="text-[11px] text-slate-500 dark:text-slate-400 font-mono">{{ effectiveCorrectCount }}/{{ metrics.total_called_pitches }}</span>

          <!-- Tooltip -->
          <div class="absolute top-full left-1/2 -translate-x-1/2 mt-2 hidden group-hover/ring:flex flex-col w-64 p-3 bg-slate-900 dark:bg-slate-800 text-white rounded-xl shadow-2xl border border-slate-700 z-50 pointer-events-none text-left">
            <div class="flex items-center justify-between pb-1 border-b border-slate-700">
              <span class="font-bold text-blue-400 text-xs">整體準確率 (Accuracy)</span>
              <span class="font-mono text-[10px] text-slate-400">{{ effectiveCorrectCount }}/{{ metrics.total_called_pitches }}</span>
            </div>
            <p class="text-[11px] text-slate-300 mt-1.5 leading-relaxed">
              衡量全場判決符合官方規則好球帶（計入當前容錯範圍）之比率。
            </p>
            <div class="mt-2 pt-1.5 border-t border-slate-700/80 text-[10px] text-blue-300 font-mono bg-blue-950/40 p-1.5 rounded">
              計算：(有效正確數 / 總判決數) × 100%
            </div>
          </div>
        </div>

        <!-- Ball Accuracy -->
        <div class="flex flex-col items-center group/ring relative cursor-help">
          <div class="relative w-20 h-20 flex items-center justify-center">
            <svg class="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path class="text-slate-100 dark:text-slate-800 stroke-current" stroke-width="3.5" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              <path class="text-emerald-500 stroke-current transition-all duration-500" :stroke-dasharray="`${effectiveBallAcc}, 100`" stroke-width="3.5" stroke-linecap="round" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
            </svg>
            <span class="absolute font-bold text-sm text-slate-900 dark:text-white font-mono">{{ effectiveBallAcc }}%</span>
          </div>
          <span class="text-xs font-bold text-slate-700 dark:text-slate-300 mt-1 border-b border-dotted border-slate-400 dark:border-slate-500">壞球準確率</span>
          <span class="text-[11px] text-slate-500 dark:text-slate-400 font-mono">{{ metrics.ball_ratio_str }}</span>

          <!-- Tooltip -->
          <div class="absolute top-full left-1/2 -translate-x-1/2 mt-2 hidden group-hover/ring:flex flex-col w-64 p-3 bg-slate-900 dark:bg-slate-800 text-white rounded-xl shadow-2xl border border-slate-700 z-50 pointer-events-none text-left">
            <div class="flex items-center justify-between pb-1 border-b border-slate-700">
              <span class="font-bold text-emerald-400 text-xs">壞球準確率 (Ball Accuracy)</span>
              <span class="font-mono text-[10px] text-slate-400">{{ metrics.ball_ratio_str }}</span>
            </div>
            <p class="text-[11px] text-slate-300 mt-1.5 leading-relaxed">
              實際落在官方好球帶外的球中，主審正確判定為壞球之比率。
            </p>
            <div class="mt-2 pt-1.5 border-t border-slate-700/80 text-[10px] text-emerald-300 font-mono bg-emerald-950/40 p-1.5 rounded">
              計算：(正確壞球數 / 規則好球帶外總數) × 100%
            </div>
          </div>
        </div>

        <!-- Strike Accuracy -->
        <div class="flex flex-col items-center group/ring relative cursor-help">
          <div class="relative w-20 h-20 flex items-center justify-center">
            <svg class="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path class="text-slate-100 dark:text-slate-800 stroke-current" stroke-width="3.5" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              <path class="text-red-500 stroke-current transition-all duration-500" :stroke-dasharray="`${effectiveStrikeAcc}, 100`" stroke-width="3.5" stroke-linecap="round" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
            </svg>
            <span class="absolute font-bold text-sm text-slate-900 dark:text-white font-mono">{{ effectiveStrikeAcc }}%</span>
          </div>
          <span class="text-xs font-bold text-slate-700 dark:text-slate-300 mt-1 border-b border-dotted border-slate-400 dark:border-slate-500">好球準確率</span>
          <span class="text-[11px] text-slate-500 dark:text-slate-400 font-mono">{{ metrics.strike_ratio_str }}</span>

          <!-- Tooltip -->
          <div class="absolute top-full left-1/2 -translate-x-1/2 mt-2 hidden group-hover/ring:flex flex-col w-64 p-3 bg-slate-900 dark:bg-slate-800 text-white rounded-xl shadow-2xl border border-slate-700 z-50 pointer-events-none text-left">
            <div class="flex items-center justify-between pb-1 border-b border-slate-700">
              <span class="font-bold text-red-400 text-xs">好球準確率 (Strike Accuracy)</span>
              <span class="font-mono text-[10px] text-slate-400">{{ metrics.strike_ratio_str }}</span>
            </div>
            <p class="text-[11px] text-slate-300 mt-1.5 leading-relaxed">
              實際落在官方好球帶內的球中，主審正確判定為好球之比率。
            </p>
            <div class="mt-2 pt-1.5 border-t border-slate-700/80 text-[10px] text-red-300 font-mono bg-red-950/40 p-1.5 rounded">
              計算：(正確好球數 / 規則好球帶內總數) × 100%
            </div>
          </div>
        </div>

        <!-- Consistency (Method A) -->
        <div class="flex flex-col items-center group/ring relative cursor-help">
          <div class="relative w-20 h-20 flex items-center justify-center">
            <svg class="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path class="text-slate-100 dark:text-slate-800 stroke-current" stroke-width="3.5" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              <path class="text-indigo-600 dark:text-indigo-400 stroke-current transition-all duration-500" :stroke-dasharray="`${effectiveGameConsistency.consistencyRate}, 100`" stroke-width="3.5" stroke-linecap="round" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
            </svg>
            <span class="absolute font-bold text-sm text-slate-900 dark:text-white font-mono">{{ effectiveGameConsistency.consistencyRate }}%</span>
          </div>
          <span class="text-xs font-bold text-slate-700 dark:text-slate-300 mt-1 border-b border-dotted border-slate-400 dark:border-slate-500">判決一致性</span>
          <span class="text-[11px] text-slate-500 dark:text-slate-400 font-mono">{{ effectiveGameConsistency.ratioStr }}</span>

          <!-- Tooltip -->
          <div class="absolute top-full right-0 sm:left-1/2 sm:-translate-x-1/2 mt-2 hidden group-hover/ring:flex flex-col w-80 p-3 bg-slate-900 dark:bg-slate-800 text-white rounded-xl shadow-2xl border border-slate-700 z-50 pointer-events-none text-left">
            <div class="flex items-center justify-between pb-1 border-b border-slate-700">
              <span class="font-bold text-indigo-400 text-xs">判決一致性 (Consistency)</span>
              <span class="font-mono text-[10px] text-slate-400">{{ effectiveGameConsistency.ratioStr }} 球對</span>
            </div>
            <p class="text-[11px] text-slate-300 mt-1.5 leading-relaxed">
              採身高校正幾何混合距離，比對 8cm 內相近進壘點是否維持同判好或同判壞（衡量是否雙標）。
            </p>
            <div class="mt-1.5 p-1.5 rounded bg-indigo-950/60 border border-indigo-500/30 text-[10px] text-indigo-200 leading-normal">
              💡 <strong>重要說明</strong>：本指標衡量「球與球之間」的相對矛盾，<strong>不受官方好球帶邊界容錯範圍影響</strong>（其判定基準為 8cm 進壘點鄰域半徑，而非好球帶邊界距離）。
            </div>
            <div class="mt-2 pt-1.5 border-t border-slate-700/80 text-[10px] text-indigo-300 font-mono bg-indigo-950/40 p-1.5 rounded">
              計算：(8cm 內判決相同球對數 / 總鄰近球對數) × 100%
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Team Advantage / Favor Metrics Summary Cards (容錯範圍後統計，依各隊代表色呈現) -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <!-- Visiting Team Favor Card -->
      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm flex flex-col justify-between gap-3 transition-colors relative overflow-hidden group/fcard">
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
            <div class="group/tip relative cursor-help">
              <span class="text-xs text-slate-400 dark:text-slate-500 font-medium border-b border-dotted border-slate-400">容錯過濾後 ⓘ</span>
              <div class="absolute top-full right-0 mt-1.5 hidden group-hover/tip:flex flex-col w-56 p-2 bg-slate-900 dark:bg-slate-800 text-white rounded-lg shadow-xl border border-slate-700 z-40 pointer-events-none text-[11px]">
                客隊打擊時好球判壞球（保送得利）+ 客隊投球時壞球判好球（出局得利）且超出當前容錯之總誤判。
              </div>
            </div>
          </div>
          <div class="mt-4 flex items-baseline gap-2">
            <span class="text-3xl font-black font-mono transition-colors" :style="{ color: visitingColorInfo.primary }">
              {{ effectiveVisitingCount }}
            </span>
            <span class="text-xs text-slate-500 dark:text-slate-400 font-bold">顆球</span>
          </div>
        </div>
        <div class="pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-2 gap-2 text-xs">
          <div class="group/tip relative cursor-help">
            <span class="text-slate-500 dark:text-slate-400 block text-[11px] border-b border-dotted border-slate-300 dark:border-slate-700 inline-block">得利總距離</span>
            <strong class="font-mono text-slate-900 dark:text-white text-sm font-bold block">{{ effectiveVisitingDist }} cm</strong>
            <div class="absolute bottom-full left-0 mb-1.5 hidden group-hover/tip:flex flex-col w-48 p-2 bg-slate-900 dark:bg-slate-800 text-white rounded-lg shadow-xl border border-slate-700 z-40 pointer-events-none text-[10px]">
              客隊所有得利誤判球之誤差物理距離累計總和。
            </div>
          </div>
          <div class="group/tip relative cursor-help">
            <span class="text-slate-500 dark:text-slate-400 block text-[11px] border-b border-dotted border-slate-300 dark:border-slate-700 inline-block">平均每球得利</span>
            <strong class="font-mono text-slate-900 dark:text-white text-sm font-bold block">{{ effectiveVisitingAvg }} cm</strong>
            <div class="absolute bottom-full right-0 mb-1.5 hidden group-hover/tip:flex flex-col w-52 p-2 bg-slate-900 dark:bg-slate-800 text-white rounded-lg shadow-xl border border-slate-700 z-40 pointer-events-none text-[10px]">
              客隊得利總距離 / 客隊得利球數，反映平均每球得利之偏差幅度。
            </div>
          </div>
        </div>
      </div>

      <!-- Home Team Favor Card -->
      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm flex flex-col justify-between gap-3 transition-colors relative overflow-hidden group/fcard">
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
            <div class="group/tip relative cursor-help">
              <span class="text-xs text-slate-400 dark:text-slate-500 font-medium border-b border-dotted border-slate-400">容錯過濾後 ⓘ</span>
              <div class="absolute top-full right-0 mt-1.5 hidden group-hover/tip:flex flex-col w-56 p-2 bg-slate-900 dark:bg-slate-800 text-white rounded-lg shadow-xl border border-slate-700 z-40 pointer-events-none text-[11px]">
                主隊打擊時好球判壞球（保送得利）+ 主隊投球時壞球判好球（出局得利）且超出當前容錯之總誤判。
              </div>
            </div>
          </div>
          <div class="mt-4 flex items-baseline gap-2">
            <span class="text-3xl font-black font-mono transition-colors" :style="{ color: homeColorInfo.primary }">
              {{ effectiveHomeCount }}
            </span>
            <span class="text-xs text-slate-500 dark:text-slate-400 font-bold">顆球</span>
          </div>
        </div>
        <div class="pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-2 gap-2 text-xs">
          <div class="group/tip relative cursor-help">
            <span class="text-slate-500 dark:text-slate-400 block text-[11px] border-b border-dotted border-slate-300 dark:border-slate-700 inline-block">得利總距離</span>
            <strong class="font-mono text-slate-900 dark:text-white text-sm font-bold block">{{ effectiveHomeDist }} cm</strong>
            <div class="absolute bottom-full left-0 mb-1.5 hidden group-hover/tip:flex flex-col w-48 p-2 bg-slate-900 dark:bg-slate-800 text-white rounded-lg shadow-xl border border-slate-700 z-40 pointer-events-none text-[10px]">
              主隊所有得利誤判球之誤差物理距離累計總和。
            </div>
          </div>
          <div class="group/tip relative cursor-help">
            <span class="text-slate-500 dark:text-slate-400 block text-[11px] border-b border-dotted border-slate-300 dark:border-slate-700 inline-block">平均每球得利</span>
            <strong class="font-mono text-slate-900 dark:text-white text-sm font-bold block">{{ effectiveHomeAvg }} cm</strong>
            <div class="absolute bottom-full right-0 mb-1.5 hidden group-hover/tip:flex flex-col w-52 p-2 bg-slate-900 dark:bg-slate-800 text-white rounded-lg shadow-xl border border-slate-700 z-40 pointer-events-none text-[10px]">
              主隊得利總距離 / 主隊得利球數，反映平均每球得利之偏差幅度。
            </div>
          </div>
        </div>
      </div>

      <!-- Net Advantage Differential Card -->
      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm flex flex-col justify-between gap-3 transition-colors relative overflow-hidden md:col-span-2 lg:col-span-1 group/fcard">
        <div class="absolute top-0 left-0 right-0 h-1.5" :style="{ backgroundColor: netFavoredColor }"></div>
        <div>
          <div class="flex items-center justify-between">
            <div class="group/tip relative cursor-help flex items-center gap-1">
              <span class="text-xs font-bold text-slate-700 dark:text-slate-300 border-b border-dotted border-slate-400">⚖️ 全場裁決偏向 (Net Favor)</span>
              <div class="absolute top-full left-0 mt-1.5 hidden group-hover/tip:flex flex-col w-60 p-2.5 bg-slate-900 dark:bg-slate-800 text-white rounded-lg shadow-xl border border-slate-700 z-40 pointer-events-none text-[11px]">
                <span class="font-bold text-blue-400 mb-0.5">全場裁決偏向</span>
                <p class="text-slate-300 leading-relaxed">比對兩隊在實質誤判中的得利球數與累積距離淨差額，判定全場裁判尺度對哪隊實質有利。</p>
              </div>
            </div>
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
          <div class="group/tip relative cursor-help">
            <span class="text-slate-500 dark:text-slate-400 block text-[11px] border-b border-dotted border-slate-300 dark:border-slate-700 inline-block">淨得利球數差</span>
            <strong class="font-mono text-slate-900 dark:text-white text-sm font-bold block">{{ netCountDiff }} 顆</strong>
            <div class="absolute bottom-full left-0 mb-1.5 hidden group-hover/tip:flex flex-col w-48 p-2 bg-slate-900 dark:bg-slate-800 text-white rounded-lg shadow-xl border border-slate-700 z-40 pointer-events-none text-[10px]">
              計算：| 主隊得利球數 - 客隊得利球數 |
            </div>
          </div>
          <div class="group/tip relative cursor-help">
            <span class="text-slate-500 dark:text-slate-400 block text-[11px] border-b border-dotted border-slate-300 dark:border-slate-700 inline-block">淨得利距離差</span>
            <strong class="font-mono text-slate-900 dark:text-white text-sm font-bold block">{{ netDistDiff }} cm</strong>
            <div class="absolute bottom-full right-0 mb-1.5 hidden group-hover/tip:flex flex-col w-52 p-2 bg-slate-900 dark:bg-slate-800 text-white rounded-lg shadow-xl border border-slate-700 z-40 pointer-events-none text-[10px]">
              計算：| 主隊得利總距離 - 客隊得利總距離 | (cm)
            </div>
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
      <div class="flex items-center gap-3 group/toltip relative cursor-help">
        <label class="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-2 border-b border-dotted border-slate-400">
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
        <div class="absolute bottom-full right-0 mb-2 hidden group-hover/toltip:flex flex-col w-72 p-2.5 bg-slate-900 dark:bg-slate-800 text-white text-xs rounded-lg shadow-xl z-50 pointer-events-none border border-slate-700 text-left">
          <span class="font-bold text-amber-400 mb-0.5">邊界容錯範圍 (Tolerance)</span>
          <p class="text-[11px] text-slate-300 leading-relaxed">進壘點距離官方好球帶邊界在此設定值（cm）以內的判決將視為主審視覺極限容許值，不計為實質誤判。</p>
          <div class="mt-1.5 p-1.5 rounded bg-amber-950/50 border border-amber-500/30 text-[10px] text-amber-200 leading-normal">
            💡 <strong>影響範圍</strong>：僅影響「準確率」與「球隊得利」計算；<strong>不影響「判決一致性」</strong>（一致性衡量球與球之間的相對雙標，無關官方邊界）。
          </div>
        </div>
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
          :highlighted-pitch="selectedPitchObject"
          :is-missed-mode="showOnlyMissed"
          :home-team="teamNames.home"
          :visiting-team="teamNames.visiting"
          @select-pitch="onSelectPitchFromSVG"
        />
      </div>

      <!-- Missed Calls Leaderboard (lg:col-span-6) -->
      <div class="lg:col-span-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm dark:shadow-none flex flex-col gap-3">
        <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2">
          <h3 class="text-sm font-bold text-slate-900 dark:text-white">誤判距離排行 (Top Missed Calls)</h3>
          <span class="text-xs text-slate-500 dark:text-slate-400 font-mono">共 {{ effectiveMissedCalls.length }} 顆</span>
        </div>

        <div class="flex flex-col gap-2 max-h-[460px] overflow-y-auto pr-1">
          <div 
            v-for="(mc, idx) in effectiveMissedCalls" 
            :key="'mc-' + idx"
            :id="'mc-card-' + idx"
            @click="onSelectMissedCall(mc)"
            :class="[
              'p-3 rounded-lg border transition-all flex flex-col gap-2.5 text-xs cursor-pointer',
              isSamePitch(mc, selectedPitchObject)
                ? 'bg-blue-50/90 dark:bg-slate-800/90 border-blue-500 shadow-sm ring-2 ring-blue-400/40'
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
                <div class="group/errtip relative cursor-help">
                  <span class="px-2 py-0.5 rounded bg-red-500/10 dark:bg-red-500/20 text-red-600 dark:text-red-400 border border-red-500/20 dark:border-red-500/30 font-bold font-mono inline-block">
                    誤差 {{ mc.dist_cm }} cm
                  </span>
                  <div class="absolute bottom-full right-0 mb-1 hidden group-hover/errtip:flex flex-col w-52 p-2 bg-slate-900 dark:bg-slate-800 text-white rounded-lg shadow-xl border border-slate-700 z-50 pointer-events-none text-[10px]">
                    球心距離好球帶有效邊界（含球體半徑 3.69 cm）之物理距離。
                  </div>
                </div>
                <span class="text-[10px] text-slate-500 dark:text-slate-400">
                  原判 {{ mc.called === 'STRIKE' ? '好球' : '壞球' }} → 實判 {{ mc.true_call === 'STRIKE' ? '好球' : '壞球' }}
                </span>
              </div>
            </div>

            <!-- Bottom Action Toolbar: Similar Pitch Analysis Trigger -->
            <div class="flex items-center justify-between pt-2 border-t border-slate-200/70 dark:border-slate-800/80 text-[11px]">
              <div class="group/neartip relative cursor-help">
                <span class="text-slate-500 dark:text-slate-400 border-b border-dotted border-slate-300 dark:border-slate-700">
                  附近判決：<strong class="text-blue-600 dark:text-blue-400 font-mono font-bold">{{ getNearbyCount(mc) }}</strong> 顆 (8cm半徑)
                </span>
                <div class="absolute bottom-full left-0 mb-1 hidden group-hover/neartip:flex flex-col w-56 p-2 bg-slate-900 dark:bg-slate-800 text-white rounded-lg shadow-xl border border-slate-700 z-50 pointer-events-none text-[10px]">
                  經打者身高校正後，在 8.0 cm 混合幾何距離內的同場判決球數。
                </div>
              </div>
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
import { ref, computed, watch } from 'vue'
import StrikeZoneSVG from './StrikeZoneSVG.vue'
import SimilarPitchModal from './SimilarPitchModal.vue'
import { findSimilarPitches, isSamePitch, calculateGameConsistency } from '../utils/pitchGeometry.js'
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
const selectedPitchObject = ref(null)

const isSimilarModalOpen = ref(false)
const activeTargetPitch = ref(null)

function onSelectMissedCall(mc) {
  if (isSamePitch(selectedPitchObject.value, mc)) {
    selectedPitchObject.value = null
  } else {
    selectedPitchObject.value = mc
  }
}

function onSelectPitchFromSVG(rankNum, pitch) {
  if (isSamePitch(selectedPitchObject.value, pitch)) {
    selectedPitchObject.value = null
  } else {
    selectedPitchObject.value = pitch
    // 排行榜對應卡片自動滾動至視圖
    const idx = effectiveMissedCalls.value.findIndex(mc => isSamePitch(mc, pitch))
    if (idx !== -1) {
      const el = document.getElementById('mc-card-' + idx)
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      }
    }
  }
}

watch([toleranceCm, showOnlyMissed], () => {
  if (selectedPitchObject.value) {
    const stillExists = displayPitches.value.some(p => isSamePitch(p, selectedPitchObject.value))
    if (!stillExists) {
      selectedPitchObject.value = null
    }
  }
})

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

// --- 全場判決一致性（Method A 鄰域球對比對法） ---
const effectiveGameConsistency = computed(() => {
  return calculateGameConsistency(props.allPitches, 8.0)
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


