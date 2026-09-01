<template>
  <div class="flex flex-col gap-6">
    <!-- Header Control Bar -->
    <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm dark:shadow-xl flex flex-col md:flex-row items-center justify-between gap-4 transition-colors">
      <div class="flex flex-wrap items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-blue-600/10 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 flex items-center justify-center font-black text-lg border border-blue-200 dark:border-blue-500/30">
          📊
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h2 class="text-base sm:text-lg font-black text-slate-900 dark:text-white">
              {{ selectedYear === 'all' ? '跨年度賽事統計總覽' : `${selectedYear} 年度賽事統計分析` }}
            </h2>
            <span class="text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-700/50">
              例行賽一軍
            </span>
          </div>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            共收錄 <strong class="text-slate-800 dark:text-slate-200 font-mono">{{ statsData?.total_games || 0 }}</strong> 場賽事數據，提供時間、分差、勝隊得分與主審執法表現綜合分析。
          </p>
        </div>
      </div>

      <!-- Year Selector Controls -->
      <div class="flex items-center gap-3 shrink-0">
        <div class="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl border border-slate-200 dark:border-slate-700 text-xs">
          <button
            v-for="yr in availableYearsList"
            :key="yr.value"
            @click="changeYear(yr.value)"
            :class="[
              'px-3 py-1.5 rounded-lg font-bold transition-all whitespace-nowrap cursor-pointer',
              selectedYear === yr.value
                ? 'bg-blue-600 text-white shadow-xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            ]"
          >
            {{ yr.label }}
          </button>
        </div>

        <button
          @click="loadStats"
          :disabled="isLoading"
          class="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 transition-all cursor-pointer disabled:opacity-50"
          title="重新整理數據"
        >
          <span :class="['inline-block', isLoading ? 'animate-spin' : '']">🔄</span>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex flex-col items-center justify-center py-20 gap-3">
      <div class="w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      <span class="text-sm font-medium text-slate-500 dark:text-slate-400">正在計算年度賽事統計數據...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="errorMessage" class="p-4 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500/50 text-red-700 dark:text-red-300 text-sm flex items-center justify-between gap-4">
      <span>{{ errorMessage }}</span>
      <button @click="loadStats" class="underline font-bold shrink-0 hover:text-red-900 dark:hover:text-red-200 cursor-pointer">
        重新嘗試
      </button>
    </div>

    <!-- Stats Content -->
    <template v-else-if="statsData">
      <!-- 6 Key Metrics Cards -->
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <!-- 1. 平均比賽時間 -->
        <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm flex flex-col justify-between transition-colors">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-slate-500 dark:text-slate-400">平均比賽時間</span>
            <span class="text-base">⏱️</span>
          </div>
          <div class="my-2">
            <div class="text-xl sm:text-2xl font-black font-mono text-slate-900 dark:text-white tracking-tight">
              {{ statsData.duration.formatted_avg }}
            </div>
            <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
              平均 {{ statsData.duration.avg_minutes }} 分鐘 ({{ statsData.duration.valid_games_count }} 場)
            </div>
          </div>
          <div class="text-[10px] text-blue-600 dark:text-blue-400 font-medium truncate" v-if="statsData.duration.shortest_game">
            最短: {{ statsData.duration.shortest_game.formatted }}
          </div>
        </div>

        <!-- 2. 平均分差 -->
        <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm flex flex-col justify-between transition-colors">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-slate-500 dark:text-slate-400">平均分差</span>
            <span class="text-base">⚖️</span>
          </div>
          <div class="my-2">
            <div class="text-xl sm:text-2xl font-black font-mono text-slate-900 dark:text-white tracking-tight">
              {{ statsData.scores.avg_margin }} <span class="text-xs font-normal text-slate-500">分</span>
            </div>
            <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
              1分差比賽: {{ statsData.scores.one_run_games_count }} 場 ({{ statsData.scores.one_run_games_pct }}%)
            </div>
          </div>
          <div class="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">
            和局: {{ statsData.scores.tie_games_count }} 場
          </div>
        </div>

        <!-- 3. 勝隊平均得分 -->
        <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm flex flex-col justify-between transition-colors">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-slate-500 dark:text-slate-400">勝隊平均得分</span>
            <span class="text-base">🏆</span>
          </div>
          <div class="my-2">
            <div class="text-xl sm:text-2xl font-black font-mono text-emerald-600 dark:text-emerald-400 tracking-tight">
              {{ statsData.scores.avg_winner_score }} <span class="text-xs font-normal text-slate-500">分</span>
            </div>
            <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
              敗隊平均: {{ statsData.scores.avg_loser_score }} 分
            </div>
          </div>
          <div class="text-[10px] text-slate-500 dark:text-slate-400">
            大比分(≥5分): {{ statsData.scores.blowout_games_count }} 場
          </div>
        </div>

        <!-- 4. 場均總得分 -->
        <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm flex flex-col justify-between transition-colors">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-slate-500 dark:text-slate-400">場均總得分</span>
            <span class="text-base">⚾</span>
          </div>
          <div class="my-2">
            <div class="text-xl sm:text-2xl font-black font-mono text-blue-600 dark:text-blue-400 tracking-tight">
              {{ statsData.scores.avg_total_runs }} <span class="text-xs font-normal text-slate-500">分</span>
            </div>
            <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
              總得分: {{ statsData.scores.total_runs.toLocaleString() }} 分
            </div>
          </div>
          <div class="text-[10px] text-slate-500 dark:text-slate-400">
            主勝率: {{ statsData.home_away.home_win_pct }}%
          </div>
        </div>

        <!-- 5. 好球帶整體準確率 -->
        <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm flex flex-col justify-between transition-colors">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-slate-500 dark:text-slate-400">好球帶總準確率</span>
            <span class="text-base">🎯</span>
          </div>
          <div class="my-2">
            <div class="text-xl sm:text-2xl font-black font-mono text-emerald-600 dark:text-emerald-400 tracking-tight">
              {{ statsData.umpire_summary.avg_overall_acc }}%
            </div>
            <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
              好球: {{ statsData.umpire_summary.avg_strike_acc }}% | 壞球: {{ statsData.umpire_summary.avg_ball_acc }}%
            </div>
          </div>
          <div class="text-[10px] text-slate-500 dark:text-slate-400">
            執法主審數: {{ statsData.umpire_leaderboard.length }} 位
          </div>
        </div>

        <!-- 6. 場均誤判數 -->
        <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm flex flex-col justify-between transition-colors">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-slate-500 dark:text-slate-400">場均誤判數</span>
            <span class="text-base">❌</span>
          </div>
          <div class="my-2">
            <div class="text-xl sm:text-2xl font-black font-mono text-amber-600 dark:text-amber-400 tracking-tight">
              {{ statsData.umpire_summary.avg_missed_calls }} <span class="text-xs font-normal text-slate-500">次</span>
            </div>
            <div class="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
              累計誤判: {{ statsData.umpire_summary.total_missed_calls.toLocaleString() }} 次
            </div>
          </div>
          <div class="text-[10px] text-slate-500 dark:text-slate-400" v-if="statsData.umpire_summary.highest_acc_game">
            單場最佳: {{ statsData.umpire_summary.highest_acc_game.overall_acc }}%
          </div>
        </div>
      </div>

      <!-- Sub Navigation Tabs -->
      <div class="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2 overflow-x-auto">
        <button
          v-for="tab in subTabs"
          :key="tab.id"
          @click="activeSubTab = tab.id"
          :class="[
            'px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap cursor-pointer',
            activeSubTab === tab.id
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800'
          ]"
        >
          <span>{{ tab.icon }}</span>
          <span>{{ tab.name }}</span>
        </button>
      </div>

      <!-- SubTab 1: 賽事比分與時間深度分析 -->
      <div v-show="activeSubTab === 'scores'" class="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <!-- Margin Distribution Breakdown -->
        <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors flex flex-col gap-4">
          <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
            <h3 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span>📈</span>
              <span>分差區間分布與比賽張力</span>
            </h3>
            <span class="text-xs font-mono text-slate-500">平均 {{ statsData.scores.avg_margin }} 分差</span>
          </div>

          <div class="flex flex-col gap-3.5">
            <!-- 1 Run Margin -->
            <div>
              <div class="flex justify-between text-xs mb-1">
                <span class="font-bold text-slate-800 dark:text-slate-200">1 分差 (緊繃戰局)</span>
                <span class="font-mono text-slate-600 dark:text-slate-400">{{ statsData.scores.margin_distribution['1'] }} 場 ({{ getPct(statsData.scores.margin_distribution['1']) }}%)</span>
              </div>
              <div class="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-3 overflow-hidden">
                <div class="bg-amber-500 h-full rounded-full transition-all duration-500" :style="{ width: `${getPct(statsData.scores.margin_distribution['1'])}%` }"></div>
              </div>
            </div>

            <!-- 2 Run Margin -->
            <div>
              <div class="flex justify-between text-xs mb-1">
                <span class="font-bold text-slate-800 dark:text-slate-200">2 分差</span>
                <span class="font-mono text-slate-600 dark:text-slate-400">{{ statsData.scores.margin_distribution['2'] }} 場 ({{ getPct(statsData.scores.margin_distribution['2']) }}%)</span>
              </div>
              <div class="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-3 overflow-hidden">
                <div class="bg-blue-500 h-full rounded-full transition-all duration-500" :style="{ width: `${getPct(statsData.scores.margin_distribution['2'])}%` }"></div>
              </div>
            </div>

            <!-- 3-4 Run Margin -->
            <div>
              <div class="flex justify-between text-xs mb-1">
                <span class="font-bold text-slate-800 dark:text-slate-200">3 ~ 4 分差 (中度差距)</span>
                <span class="font-mono text-slate-600 dark:text-slate-400">{{ statsData.scores.margin_distribution['3-4'] }} 場 ({{ getPct(statsData.scores.margin_distribution['3-4']) }}%)</span>
              </div>
              <div class="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-3 overflow-hidden">
                <div class="bg-indigo-500 h-full rounded-full transition-all duration-500" :style="{ width: `${getPct(statsData.scores.margin_distribution['3-4'])}%` }"></div>
              </div>
            </div>

            <!-- 5+ Run Margin -->
            <div>
              <div class="flex justify-between text-xs mb-1">
                <span class="font-bold text-slate-800 dark:text-slate-200">5 分以上 (大比分差)</span>
                <span class="font-mono text-slate-600 dark:text-slate-400">{{ statsData.scores.margin_distribution['5+'] }} 場 ({{ getPct(statsData.scores.margin_distribution['5+']) }}%)</span>
              </div>
              <div class="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-3 overflow-hidden">
                <div class="bg-purple-500 h-full rounded-full transition-all duration-500" :style="{ width: `${getPct(statsData.scores.margin_distribution['5+'])}%` }"></div>
              </div>
            </div>
          </div>

          <!-- Home vs Away Comparison -->
          <div class="mt-2 pt-3 border-t border-slate-200 dark:border-slate-800 grid grid-cols-2 gap-3 text-center">
            <div class="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800/80">
              <div class="text-[11px] text-slate-500">主場球隊勝率</div>
              <div class="text-base font-black font-mono text-blue-600 dark:text-blue-400 mt-0.5">
                {{ statsData.home_away.home_win_pct }}%
              </div>
              <div class="text-[10px] text-slate-400">{{ statsData.home_away.home_wins }} 勝</div>
            </div>
            <div class="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800/80">
              <div class="text-[11px] text-slate-500">客場球隊勝率</div>
              <div class="text-base font-black font-mono text-slate-700 dark:text-slate-300 mt-0.5">
                {{ statsData.home_away.visiting_win_pct }}%
              </div>
              <div class="text-[10px] text-slate-400">{{ statsData.home_away.visiting_wins }} 勝</div>
            </div>
          </div>
        </div>

        <!-- Duration & Extremes Cards -->
        <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors flex flex-col gap-4">
          <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
            <h3 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span>⏱️</span>
              <span>比賽時間與指標賽事紀錄</span>
            </h3>
            <span class="text-xs font-mono text-slate-500">平均 {{ statsData.duration.formatted_avg }}</span>
          </div>

          <div class="flex flex-col gap-3">
            <!-- Shortest Game Card -->
            <div v-if="statsData.duration.shortest_game" class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 flex items-center justify-between gap-3">
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 font-bold">最短比賽</span>
                  <span class="text-xs font-bold text-slate-900 dark:text-white">{{ statsData.duration.shortest_game.matchup }}</span>
                </div>
                <div class="text-[11px] text-slate-500 dark:text-slate-400 mt-1 font-mono">
                  第 {{ statsData.duration.shortest_game.game_sno }} 場 | {{ statsData.duration.shortest_game.date }}
                </div>
              </div>
              <div class="text-right shrink-0">
                <div class="text-sm font-black font-mono text-emerald-600 dark:text-emerald-400">{{ statsData.duration.shortest_game.formatted }}</div>
                <button
                  @click="$emit('load-game', statsData.duration.shortest_game.game_id)"
                  class="mt-1 px-2 py-0.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold transition-all shadow-xs cursor-pointer"
                >
                  載入分析
                </button>
              </div>
            </div>

            <!-- Longest Game Card -->
            <div v-if="statsData.duration.longest_game" class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 flex items-center justify-between gap-3">
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300 font-bold">最長比賽</span>
                  <span class="text-xs font-bold text-slate-900 dark:text-white">{{ statsData.duration.longest_game.matchup }}</span>
                </div>
                <div class="text-[11px] text-slate-500 dark:text-slate-400 mt-1 font-mono">
                  第 {{ statsData.duration.longest_game.game_sno }} 場 | {{ statsData.duration.longest_game.date }}
                </div>
              </div>
              <div class="text-right shrink-0">
                <div class="text-sm font-black font-mono text-amber-600 dark:text-amber-400">{{ statsData.duration.longest_game.formatted }}</div>
                <button
                  @click="$emit('load-game', statsData.duration.longest_game.game_id)"
                  class="mt-1 px-2 py-0.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold transition-all shadow-xs cursor-pointer"
                >
                  載入分析
                </button>
              </div>
            </div>

            <!-- Highest Accuracy Game -->
            <div v-if="statsData.umpire_summary.highest_acc_game" class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 flex items-center justify-between gap-3">
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 font-bold">最高準確率場次</span>
                  <span class="text-xs font-bold text-slate-900 dark:text-white">{{ statsData.umpire_summary.highest_acc_game.matchup }}</span>
                </div>
                <div class="text-[11px] text-slate-500 dark:text-slate-400 mt-1 font-mono">
                  主審: {{ statsData.umpire_summary.highest_acc_game.hp_umpire }} | 誤判 {{ statsData.umpire_summary.highest_acc_game.missed_count }} 球
                </div>
              </div>
              <div class="text-right shrink-0">
                <div class="text-sm font-black font-mono text-emerald-600 dark:text-emerald-400">{{ statsData.umpire_summary.highest_acc_game.overall_acc }}%</div>
                <button
                  @click="$emit('load-game', statsData.umpire_summary.highest_acc_game.game_id)"
                  class="mt-1 px-2 py-0.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold transition-all shadow-xs cursor-pointer"
                >
                  載入分析
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- SubTab 2: 主審執法表現排行榜 -->
      <div v-show="activeSubTab === 'umpires'" class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors flex flex-col gap-4">
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
          <div>
            <h3 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span>🎯</span>
              <span>主審執法好球帶表現排行榜 (共 {{ statsData.umpire_leaderboard.length }} 位)</span>
            </h3>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              依本年度主審執法場次與各球判決準確度統計分析。
            </p>
          </div>
          <div class="text-xs font-mono text-slate-500">
            年度平均: <strong class="text-emerald-600 dark:text-emerald-400 font-bold">{{ statsData.umpire_summary.avg_overall_acc }}%</strong>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-950/60 uppercase font-mono border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th class="p-3 whitespace-nowrap">排名</th>
                <th
                  @click="toggleUmpireSort('hp_umpire')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': umpireSortKey === 'hp_umpire' }"
                  title="點擊切換主審排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>主審</span>
                    <span class="text-[10px] font-mono" :class="umpireSortKey === 'hp_umpire' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ umpireSortKey === 'hp_umpire' ? (umpireSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleUmpireSort('games')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': umpireSortKey === 'games' }"
                  title="點擊切換執法場次排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>執法場次</span>
                    <span class="text-[10px] font-mono" :class="umpireSortKey === 'games' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ umpireSortKey === 'games' ? (umpireSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleUmpireSort('overall_acc')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': umpireSortKey === 'overall_acc' }"
                  title="點擊切換整體準確率排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>整體準確率</span>
                    <span class="text-[10px] font-mono" :class="umpireSortKey === 'overall_acc' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ umpireSortKey === 'overall_acc' ? (umpireSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleUmpireSort('strike_acc')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': umpireSortKey === 'strike_acc' }"
                  title="點擊切換好球準確率排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>好球準確率</span>
                    <span class="text-[10px] font-mono" :class="umpireSortKey === 'strike_acc' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ umpireSortKey === 'strike_acc' ? (umpireSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleUmpireSort('ball_acc')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': umpireSortKey === 'ball_acc' }"
                  title="點擊切換壞球準確率排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>壞球準確率</span>
                    <span class="text-[10px] font-mono" :class="umpireSortKey === 'ball_acc' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ umpireSortKey === 'ball_acc' ? (umpireSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleUmpireSort('total_missed')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': umpireSortKey === 'total_missed' }"
                  title="點擊切換總誤判數排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>總誤判數</span>
                    <span class="text-[10px] font-mono" :class="umpireSortKey === 'total_missed' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ umpireSortKey === 'total_missed' ? (umpireSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleUmpireSort('missed_per_game')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': umpireSortKey === 'missed_per_game' }"
                  title="點擊切換場均誤判排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>場均誤判</span>
                    <span class="text-[10px] font-mono" :class="umpireSortKey === 'missed_per_game' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ umpireSortKey === 'missed_per_game' ? (umpireSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleUmpireSort('overall_acc')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': umpireSortKey === 'overall_acc' }"
                  title="點擊切換評比狀態排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>評比狀態</span>
                    <span class="text-[10px] font-mono" :class="umpireSortKey === 'overall_acc' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ umpireSortKey === 'overall_acc' ? (umpireSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200 dark:divide-slate-800/80 font-medium">
              <tr
                v-for="(u, idx) in sortedUmpireLeaderboard"
                :key="u.hp_umpire"
                class="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-all"
              >
                <td class="p-3 font-mono font-bold text-slate-500">#{{ idx + 1 }}</td>
                <td class="p-3 font-bold text-amber-600 dark:text-amber-400">{{ u.hp_umpire }}</td>
                <td class="p-3 font-mono text-slate-700 dark:text-slate-300 font-bold">{{ u.games }} 場</td>
                <td class="p-3 font-mono font-black text-sm" :class="getAccColor(u.overall_acc)">
                  {{ u.overall_acc }}%
                </td>
                <td class="p-3 font-mono text-slate-600 dark:text-slate-300">{{ u.strike_acc }}%</td>
                <td class="p-3 font-mono text-slate-600 dark:text-slate-300">{{ u.ball_acc }}%</td>
                <td class="p-3 font-mono text-slate-600 dark:text-slate-400">{{ u.total_missed }} 球</td>
                <td class="p-3 font-mono font-bold text-amber-600 dark:text-amber-400">{{ u.missed_per_game }} 次</td>
                <td class="p-3">
                  <span
                    :class="[
                      'text-[10px] px-2 py-0.5 rounded-full font-bold',
                      u.overall_acc >= statsData.umpire_summary.avg_overall_acc
                        ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-700/50'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700'
                    ]"
                  >
                    {{ u.overall_acc >= statsData.umpire_summary.avg_overall_acc ? '高於平均' : '低於平均' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- SubTab 3: 球隊戰績與得失分表現 -->
      <div v-show="activeSubTab === 'teams'" class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors flex flex-col gap-4">
        <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
          <div>
            <h3 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span>🛡️</span>
              <span>各球隊年度戰績與攻守表現</span>
            </h3>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              統計各隊出賽、勝率、總得失分、淨勝分差與一分差戰績。
            </p>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-950/60 uppercase font-mono border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th
                  @click="toggleTeamSort('team')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': teamSortKey === 'team' }"
                  title="點擊切換球隊排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>球隊</span>
                    <span class="text-[10px] font-mono" :class="teamSortKey === 'team' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ teamSortKey === 'team' ? (teamSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleTeamSort('games')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': teamSortKey === 'games' }"
                  title="點擊切換出賽場次排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>出賽</span>
                    <span class="text-[10px] font-mono" :class="teamSortKey === 'games' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ teamSortKey === 'games' ? (teamSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleTeamSort('wins')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': teamSortKey === 'wins' }"
                  title="點擊切換勝場排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>勝 - 敗 - 和</span>
                    <span class="text-[10px] font-mono" :class="teamSortKey === 'wins' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ teamSortKey === 'wins' ? (teamSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleTeamSort('win_rate')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': teamSortKey === 'win_rate' }"
                  title="點擊切換勝率排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>勝率</span>
                    <span class="text-[10px] font-mono" :class="teamSortKey === 'win_rate' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ teamSortKey === 'win_rate' ? (teamSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleTeamSort('runs_scored')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': teamSortKey === 'runs_scored' }"
                  title="點擊切換總得分排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>總得分</span>
                    <span class="text-[10px] font-mono" :class="teamSortKey === 'runs_scored' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ teamSortKey === 'runs_scored' ? (teamSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleTeamSort('runs_allowed')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': teamSortKey === 'runs_allowed' }"
                  title="點擊切換總失分排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>總失分</span>
                    <span class="text-[10px] font-mono" :class="teamSortKey === 'runs_allowed' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ teamSortKey === 'runs_allowed' ? (teamSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleTeamSort('run_diff')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': teamSortKey === 'run_diff' }"
                  title="點擊切換淨勝分排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>淨勝分</span>
                    <span class="text-[10px] font-mono" :class="teamSortKey === 'run_diff' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ teamSortKey === 'run_diff' ? (teamSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleTeamSort('avg_runs_scored')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': teamSortKey === 'avg_runs_scored' }"
                  title="點擊切換場均得分排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>場均得分</span>
                    <span class="text-[10px] font-mono" :class="teamSortKey === 'avg_runs_scored' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ teamSortKey === 'avg_runs_scored' ? (teamSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleTeamSort('avg_runs_allowed')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': teamSortKey === 'avg_runs_allowed' }"
                  title="點擊切換場均失分排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>場均失分</span>
                    <span class="text-[10px] font-mono" :class="teamSortKey === 'avg_runs_allowed' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ teamSortKey === 'avg_runs_allowed' ? (teamSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleTeamSort('one_run_win_rate')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': teamSortKey === 'one_run_win_rate' }"
                  title="點擊切換一分差勝率排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>一分差戰績</span>
                    <span class="text-[10px] font-mono" :class="teamSortKey === 'one_run_win_rate' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ teamSortKey === 'one_run_win_rate' ? (teamSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleTeamSort('home_record')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': teamSortKey === 'home_record' }"
                  title="點擊切換主場戰績排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>主場戰績</span>
                    <span class="text-[10px] font-mono" :class="teamSortKey === 'home_record' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ teamSortKey === 'home_record' ? (teamSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleTeamSort('away_record')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': teamSortKey === 'away_record' }"
                  title="點擊切換客場戰績排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>客場戰績</span>
                    <span class="text-[10px] font-mono" :class="teamSortKey === 'away_record' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ teamSortKey === 'away_record' ? (teamSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200 dark:divide-slate-800/80 font-medium">
              <tr
                v-for="t in sortedTeamStandings"
                :key="t.team"
                class="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-all"
              >
                <td class="p-3 font-bold text-slate-900 dark:text-white text-sm">{{ t.team }}</td>
                <td class="p-3 font-mono text-slate-600 dark:text-slate-300">{{ t.games }}</td>
                <td class="p-3 font-mono font-bold text-slate-800 dark:text-slate-200">{{ t.wins }} - {{ t.losses }} - {{ t.ties }}</td>
                <td class="p-3 font-mono font-black text-sm text-blue-600 dark:text-blue-400">{{ t.win_rate_str }}</td>
                <td class="p-3 font-mono text-emerald-600 dark:text-emerald-400 font-bold">{{ t.runs_scored }}</td>
                <td class="p-3 font-mono text-red-500 dark:text-red-400 font-bold">{{ t.runs_allowed }}</td>
                <td class="p-3 font-mono font-bold" :class="t.run_diff >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500 dark:text-red-400'">
                  {{ t.run_diff > 0 ? `+${t.run_diff}` : t.run_diff }}
                </td>
                <td class="p-3 font-mono text-slate-600 dark:text-slate-300">{{ t.avg_runs_scored }}</td>
                <td class="p-3 font-mono text-slate-600 dark:text-slate-300">{{ t.avg_runs_allowed }}</td>
                <td class="p-3 font-mono text-slate-700 dark:text-slate-300">{{ t.one_run_record }}</td>
                <td class="p-3 font-mono text-slate-500">{{ t.home_record }}</td>
                <td class="p-3 font-mono text-slate-500">{{ t.away_record }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- SubTab 4: 球場賽事統計 -->
      <div v-show="activeSubTab === 'stadiums'" class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors flex flex-col gap-4">
        <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
          <div>
            <h3 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span>🏟️</span>
              <span>各球場舉辦場次與數據分析</span>
            </h3>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              分析不同球場之比賽時間、得分產量與主審好球帶判決準確率。
            </p>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-950/60 uppercase font-mono border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th
                  @click="toggleStadiumSort('field')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': stadiumSortKey === 'field' }"
                  title="點擊切換球場排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>球場名稱</span>
                    <span class="text-[10px] font-mono" :class="stadiumSortKey === 'field' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ stadiumSortKey === 'field' ? (stadiumSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleStadiumSort('games')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': stadiumSortKey === 'games' }"
                  title="點擊切換舉辦場次排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>舉辦場次</span>
                    <span class="text-[10px] font-mono" :class="stadiumSortKey === 'games' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ stadiumSortKey === 'games' ? (stadiumSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleStadiumSort('games')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': stadiumSortKey === 'games' }"
                  title="點擊切換場次佔比排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>場次佔比</span>
                    <span class="text-[10px] font-mono" :class="stadiumSortKey === 'games' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ stadiumSortKey === 'games' ? (stadiumSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleStadiumSort('avg_duration_minutes')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': stadiumSortKey === 'avg_duration_minutes' }"
                  title="點擊切換平均比賽時間排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>平均比賽時間</span>
                    <span class="text-[10px] font-mono" :class="stadiumSortKey === 'avg_duration_minutes' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ stadiumSortKey === 'avg_duration_minutes' ? (stadiumSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleStadiumSort('avg_total_runs')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': stadiumSortKey === 'avg_total_runs' }"
                  title="點擊切換場均總得分排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>場均總得分</span>
                    <span class="text-[10px] font-mono" :class="stadiumSortKey === 'avg_total_runs' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ stadiumSortKey === 'avg_total_runs' ? (stadiumSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
                <th
                  @click="toggleStadiumSort('avg_accuracy')"
                  class="p-3 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors whitespace-nowrap"
                  :class="{ 'text-blue-600 dark:text-blue-400 font-bold': stadiumSortKey === 'avg_accuracy' }"
                  title="點擊切換主審平均準確率排序"
                >
                  <div class="flex items-center gap-1.5">
                    <span>主審平均準確率</span>
                    <span class="text-[10px] font-mono" :class="stadiumSortKey === 'avg_accuracy' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-300 dark:text-slate-600'">
                      {{ stadiumSortKey === 'avg_accuracy' ? (stadiumSortOrder === 'asc' ? '▲' : '▼') : '↕' }}
                    </span>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200 dark:divide-slate-800/80 font-medium">
              <tr
                v-for="s in sortedStadiumStats"
                :key="s.field"
                class="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-all"
              >
                <td class="p-3 font-bold text-slate-900 dark:text-white text-sm">{{ s.field }}</td>
                <td class="p-3 font-mono font-bold text-blue-600 dark:text-blue-400">{{ s.games }} 場</td>
                <td class="p-3 font-mono text-slate-500">{{ getPct(s.games) }}%</td>
                <td class="p-3 font-mono text-slate-700 dark:text-slate-300 font-bold">{{ s.formatted_avg_duration }}</td>
                <td class="p-3 font-mono font-bold text-slate-800 dark:text-slate-200">{{ s.avg_total_runs }} 分</td>
                <td class="p-3 font-mono font-bold text-emerald-600 dark:text-emerald-400">{{ s.avg_accuracy }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchAvailableYears, fetchSeasonStats } from '../services/dataService'

defineEmits(['load-game'])

const selectedYear = ref('2026')
const availableYears = ref([2026])
const statsData = ref(null)
const isLoading = ref(false)
const errorMessage = ref('')
const activeSubTab = ref('scores')

// Sorting states
// 主審執法排行預設：整體準確率低到高 (overall_acc asc)
const umpireSortKey = ref('overall_acc')
const umpireSortOrder = ref('asc')

// 球隊戰績預設：勝率高到低 (win_rate desc)
const teamSortKey = ref('win_rate')
const teamSortOrder = ref('desc')

// 球場統計預設：舉辦場次高到低 (games desc)
const stadiumSortKey = ref('games')
const stadiumSortOrder = ref('desc')

const subTabs = [
  { id: 'scores', name: '賽事分差與時間走勢', icon: '📈' },
  { id: 'umpires', name: '主審執法表現排行', icon: '🎯' },
  { id: 'teams', name: '球隊戰績與得失分', icon: '🛡️' },
  { id: 'stadiums', name: '球場賽事統計', icon: '🏟️' }
]

const availableYearsList = computed(() => {
  const list = availableYears.value.map(y => ({ label: `${y} 年度`, value: String(y) }))
  list.push({ label: '全部年度', value: 'all' })
  return list
})

function toggleUmpireSort(key) {
  if (umpireSortKey.value === key) {
    umpireSortOrder.value = umpireSortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    umpireSortKey.value = key
    umpireSortOrder.value = (key === 'hp_umpire' || key === 'overall_acc') ? 'asc' : 'desc'
  }
}

function toggleTeamSort(key) {
  if (teamSortKey.value === key) {
    teamSortOrder.value = teamSortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    teamSortKey.value = key
    teamSortOrder.value = (key === 'team') ? 'asc' : 'desc'
  }
}

function toggleStadiumSort(key) {
  if (stadiumSortKey.value === key) {
    stadiumSortOrder.value = stadiumSortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    stadiumSortKey.value = key
    stadiumSortOrder.value = (key === 'field') ? 'asc' : 'desc'
  }
}

const sortedUmpireLeaderboard = computed(() => {
  if (!statsData.value?.umpire_leaderboard) return []
  const list = [...statsData.value.umpire_leaderboard]
  const key = umpireSortKey.value
  const order = umpireSortOrder.value === 'asc' ? 1 : -1

  return list.sort((a, b) => {
    let res
    if (key === 'hp_umpire') {
      res = a.hp_umpire.localeCompare(b.hp_umpire, 'zh-Hant')
    } else {
      const valA = Number(a[key]) || 0
      const valB = Number(b[key]) || 0
      res = valA - valB
    }

    if (res !== 0) {
      return res * order
    }
    return (b.games - a.games) || (a.overall_acc - b.overall_acc)
  })
})

const sortedTeamStandings = computed(() => {
  if (!statsData.value?.team_standings) return []
  const list = [...statsData.value.team_standings]
  const key = teamSortKey.value
  const order = teamSortOrder.value === 'asc' ? 1 : -1

  const parseRecordWinRate = (str) => {
    const m = String(str || '').match(/(\d+)勝-(\d+)敗/)
    if (!m) return 0
    const w = Number(m[1]), l = Number(m[2])
    return w + l > 0 ? (w / (w + l)) * 1000 + w : 0
  }

  return list.sort((a, b) => {
    let res
    if (key === 'team') {
      res = a.team.localeCompare(b.team, 'zh-Hant')
    } else if (key === 'wins') {
      res = (a.wins - b.wins) || (b.losses - a.losses)
    } else if (key === 'one_run_win_rate') {
      res = (a.one_run_win_rate - b.one_run_win_rate)
    } else if (key === 'home_record' || key === 'away_record') {
      res = parseRecordWinRate(a[key]) - parseRecordWinRate(b[key])
    } else {
      const valA = Number(a[key]) || 0
      const valB = Number(b[key]) || 0
      res = valA - valB
    }

    if (res !== 0) {
      return res * order
    }
    return (b.win_rate - a.win_rate) || (b.run_diff - a.run_diff) || (b.wins - a.wins)
  })
})

const sortedStadiumStats = computed(() => {
  if (!statsData.value?.stadium_stats) return []
  const list = [...statsData.value.stadium_stats]
  const key = stadiumSortKey.value
  const order = stadiumSortOrder.value === 'asc' ? 1 : -1

  return list.sort((a, b) => {
    let res
    if (key === 'field') {
      res = a.field.localeCompare(b.field, 'zh-Hant')
    } else {
      const valA = Number(a[key]) || 0
      const valB = Number(b[key]) || 0
      res = valA - valB
    }

    if (res !== 0) {
      return res * order
    }
    return b.games - a.games
  })
})

function getPct(count) {
  if (!statsData.value?.total_games || statsData.value.total_games === 0) return 0
  return Math.round((count / statsData.value.total_games) * 1000) / 10
}

function getAccColor(acc) {
  if (acc >= 91.5) return 'text-emerald-600 dark:text-emerald-400'
  if (acc >= 90.0) return 'text-blue-600 dark:text-blue-400'
  return 'text-amber-600 dark:text-amber-400'
}

async function loadYears() {
  try {
    const years = await fetchAvailableYears()
    if (years && years.length > 0) {
      availableYears.value = years
      if (!years.map(String).includes(selectedYear.value)) {
        selectedYear.value = String(years[0])
      }
    }
  } catch (e) {
    console.warn('Failed to load available years:', e)
  }
}

async function loadStats() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    statsData.value = await fetchSeasonStats(selectedYear.value)
  } catch (e) {
    errorMessage.value = e.message || '無法取得年度統計資料'
  } finally {
    isLoading.value = false
  }
}

function changeYear(yr) {
  if (selectedYear.value === yr) return
  selectedYear.value = yr
  loadStats()
}

onMounted(async () => {
  await loadYears()
  await loadStats()
})
</script>
