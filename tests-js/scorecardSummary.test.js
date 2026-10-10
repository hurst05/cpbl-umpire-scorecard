import assert from 'node:assert/strict'
import { after, before, test } from 'node:test'
import { createRenderer, nextTick, reactive, ssrContextKey } from 'vue'
import { createServer } from 'vite'

let server
let ScorecardSummary
const { createApp } = createRenderer({
  createComment: () => ({}),
  insert() {},
  remove() {},
  parentNode: () => null,
  nextSibling: () => null
})

before(async () => {
  server = await createServer({ server: { middlewareMode: true, hmr: false, watch: null } })
  ScorecardSummary = (await server.ssrLoadModule('/src/components/ScorecardSummary.vue')).default
})

after(async () => { await server?.close() })

function createScorecard(t, overrides = {}) {
  const allPitches = [
    { inning_num: 1, inning_half: '上', x: -0.3, called: 'BALL', true_call: 'BALL', dist_cm: 4 },
    { inning_num: 1, inning_half: '下', x: 0.1, called: 'BALL', true_call: 'STRIKE', dist_cm: 4, favored_team: '主隊' },
    { inning_num: 2, inning_half: '上', x: 0.1, called: 'STRIKE', true_call: 'STRIKE', dist_cm: 4 },
    { inning_num: 2, inning_half: '下', x: 0.28, called: 'STRIKE', true_call: 'BALL', dist_cm: 1, favored_team: '客隊' },
    { inning_num: 10, inning_half: '上', x: 0.3, called: 'STRIKE', true_call: 'BALL', dist_cm: 5, favored_team: '主隊' },
    { inning_num: 10, inning_half: '下', x: -0.05, called: 'STRIKE', true_call: 'STRIKE', dist_cm: 3 }
  ].map((p, index) => ({
    ...p, pa_index: index + 1, pitch_index: 1, z: 0.7, sz_top: 0.963, sz_bottom: 0.486,
    is_correct: p.called === p.true_call
  }))
  const props = reactive({
    allPitches,
    metrics: {
      total_called_pitches: allPitches.length,
      missed_calls: allPitches.filter(p => !p.is_correct).sort((a, b) => b.dist_cm - a.dist_cm)
    },
    plateAppearances: [{ inning: '1局上' }, { inning: '10局下' }],
    gameInfo: { game_id: 'first-game', visiting_team: '客隊', home_team: '主隊' },
    ...overrides
  })
  let state
  const app = createApp({
    setup(_, context) {
      state = ScorecardSummary.setup(props, context)
      return () => null
    }
  })
  app.provide(ssrContextKey, {})
  app.mount({})
  t.after(() => app.unmount())
  return { state, props }
}

test('defaults to the end of an extra-inning game, including innings without tracked calls', t => {
  const { state } = createScorecard(t, { plateAppearances: [{ inning: '11局上' }] })
  assert.equal(state.finalInning.value, 11)
  assert.equal(state.selectedInning.value, 11)
  assert.equal(state.inningRangeLabel.value, '全場')
  assert.equal(state.inningPitches.value.length, 6)
  assert.equal(state.effectiveCorrectCount.value, 3)
  assert.equal(state.effectiveOverallAcc.value, '50.0')
  assert.deepEqual(state.effectiveMissedCalls.value.map(p => p.dist_cm), [5, 4, 1])
})

test('inning and tolerance sliders update decisions, accuracy, favor, and nearby consistency together', t => {
  const { state } = createScorecard(t)
  state.selectedInning.value = 1
  assert.equal(state.inningRangeLabel.value, '第一局')
  assert.deepEqual(state.inningPitches.value.map(p => p.inning_half), ['上', '下'])
  assert.equal(state.effectiveMissedCalls.value.length, 1)
  assert.equal(state.effectiveCorrectCount.value, 1)
  assert.equal(state.effectiveOverallAcc.value, '50.0')
  assert.equal(state.effectiveBallAcc.value, '100.0')
  assert.equal(state.effectiveStrikeAcc.value, '0.0')
  assert.equal(state.correctBalls.value.length, 1)
  assert.equal(state.trueBalls.value.length, 1)
  assert.equal(state.correctStrikes.value.length, 0)
  assert.equal(state.trueStrikes.value.length, 1)
  assert.equal(state.effectiveAvgMissDist.value, '4.0')
  assert.equal(state.effectiveHomeCount.value, 1)
  assert.equal(state.effectiveHomeDist.value, 4)
  assert.equal(state.effectiveVisitingCount.value, 0)
  assert.equal(state.netCountDiff.value, 1)
  assert.equal(state.netDistDiff.value, '4.0')
  assert.equal(state.effectiveGameConsistency.value.ratioStr, '0/0')
  assert.equal(state.getNearbyCount(state.inningPitches.value[1]), 0)

  state.showOnlyMissed.value = false
  assert.equal(state.displayPitches.value.length, 2)
  state.selectedInning.value = 2
  assert.equal(state.displayPitches.value.length, 4)
  assert.equal(state.effectiveGameConsistency.value.ratioStr, '0/1')
  assert.equal(state.getNearbyCount(state.inningPitches.value[1]), 1)
  assert.equal(state.effectiveVisitingCount.value, 1)

  state.toleranceCm.value = 1
  assert.equal(state.effectiveMissedCalls.value.length, 2)
  assert.equal(state.correctBalls.value.length, 1)
  state.toleranceCm.value = 2
  assert.equal(state.effectiveMissedCalls.value.length, 1)
  assert.equal(state.effectiveCorrectCount.value, 3)
  assert.equal(state.effectiveOverallAcc.value, '75.0')
  assert.equal(state.effectiveBallAcc.value, '100.0')
  assert.equal(state.correctBalls.value.length, 2)
  assert.equal(state.trueBalls.value.length, 2)
  assert.equal(state.effectiveVisitingCount.value, 0)
  assert.equal(state.effectiveGameConsistency.value.ratioStr, '0/1')

  state.selectedInning.value = 10
  assert.equal(state.displayPitches.value.length, 6)
  assert.equal(state.effectiveMissedCalls.value.length, 2)
  assert.equal(state.effectiveHomeCount.value, 2)
})

test('clears a pitch excluded by the inning range and resets to game end when switching games', async t => {
  const { state, props } = createScorecard(t)
  state.selectedPitchObject.value = props.allPitches[4]
  state.selectedInning.value = 1
  await nextTick()
  assert.equal(state.selectedPitchObject.value, null)

  props.allPitches = props.allPitches.slice(0, 4)
  props.plateAppearances = [{ inning: '2局下' }]
  props.gameInfo = { ...props.gameInfo, game_id: 'second-game' }
  await nextTick()
  assert.equal(state.selectedInning.value, 2)
  assert.equal(state.inningPitches.value.length, 4)
})

test('handles a game with no tracked calls without invalid slider bounds or percentages', t => {
  const { state } = createScorecard(t, { allPitches: [], metrics: {}, plateAppearances: [] })
  assert.equal(state.finalInning.value, 1)
  assert.equal(state.selectedInning.value, 1)
  assert.equal(state.displayPitches.value.length, 0)
  assert.equal(state.effectiveCorrectCount.value, 0)
  assert.equal(state.effectiveOverallAcc.value, 100)
  assert.equal(state.effectiveGameConsistency.value.ratioStr, '0/0')
})
