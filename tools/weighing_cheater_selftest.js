const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const cheater = require('../viewer/weighing_cheater.js');

function loadProblemConfig(relativePath) {
  const filePath = path.join(__dirname, '..', relativePath);
  return JSON.parse(fs.readFileSync(filePath, 'utf8')).interactive;
}

const twelveCoinConfig = loadProblemConfig('data/problems/weighings/counterfeit-12-coins-3-weighings.yaml');
const thirteenIdentifyOnlyConfig = loadProblemConfig('data/problems/classical_more/thirteen-coins-identify-only-three-weighings.yaml');
const thirteenKnownGenuineConfig = loadProblemConfig('data/problems/classical_more/thirteen-coins-known-genuine-three-weighings.yaml');

assert.deepEqual(twelveCoinConfig.type, 'single_counterfeit_unknown_direction');
assert.equal(twelveCoinConfig.modes.includes('cheater'), true);
assert.deepEqual(thirteenIdentifyOnlyConfig.type, 'single_counterfeit_unknown_direction');
assert.equal(thirteenIdentifyOnlyConfig.objective, 'identify_coin_only_unknown_direction');
assert.equal(thirteenIdentifyOnlyConfig.modes.includes('cheater'), true);
assert.deepEqual(thirteenKnownGenuineConfig.type, 'single_counterfeit_unknown_direction');
assert.equal(thirteenKnownGenuineConfig.known_genuine_count, 1);
assert.equal(thirteenKnownGenuineConfig.modes.includes('cheater'), true);

let candidates = cheater.initialCandidates(9);
let history = [];

let step = cheater.chooseCheaterOutcome({
  coin_count: 9,
  counterfeit_weight: 'light',
  currentCandidates: candidates,
  leftCoins: [1, 2],
  rightCoins: [3, 4],
  remainingWeighings: 2,
  history
});
assert.equal(step.outcome, 'balance');
assert.deepEqual(step.candidates, [5, 6, 7, 8, 9]);

candidates = step.candidates;
history.push({ outcome: step.outcome });
step = cheater.chooseCheaterOutcome({
  coin_count: 9,
  counterfeit_weight: 'light',
  currentCandidates: candidates,
  leftCoins: [5, 6],
  rightCoins: [7, 8],
  remainingWeighings: 1,
  history
});
assert.notEqual(step.outcome, 'balance');
assert.equal(step.candidates.length, 2);
assert.deepEqual(step.candidates, [7, 8]);

const answer = cheater.finalizeCheaterAnswer({
  coin_count: 9,
  currentCandidates: step.candidates,
  selectedCoin: 7
});
assert.equal(answer.win, false);
assert.equal(answer.actualCoin, 8);

const forcedWin = cheater.finalizeCheaterAnswer({
  coin_count: 9,
  currentCandidates: [4],
  selectedCoin: 4
});
assert.equal(forcedWin.win, true);
assert.equal(forcedWin.actualCoin, 4);

const scaleLabels = ['A', 'B', 'C'];
assert.equal(
  cheater.faultyScaleOutcomeForCandidate('B', 'A', ['B'], ['C']),
  'right_down'
);
assert.equal(
  cheater.faultyScaleOutcomeForCandidate('A', 'A', ['B'], ['C']),
  'arbitrary'
);

const firstScaleStep = cheater.faultyScaleChooseCheaterOutcome({
  scaleLabels,
  currentCandidates: scaleLabels,
  instrument: 'A',
  leftObjects: ['B'],
  rightObjects: ['C'],
  history: []
});
assert.equal(firstScaleStep.outcome, 'left_down');
assert.deepEqual(firstScaleStep.candidates, ['A', 'C']);

const secondScaleExpansion = cheater.faultyScaleExpandExhaustiveNode({
  scaleLabels,
  currentCandidates: firstScaleStep.candidates,
  instrument: 'B',
  leftObjects: ['A'],
  rightObjects: ['C'],
  usedWeighings: 1,
  maxWeighings: 2
});
assert.deepEqual(secondScaleExpansion.children.map(child => child.candidates), [['C'], ['A']]);
assert.deepEqual(secondScaleExpansion.children.map(child => child.status), ['solved', 'solved']);

const scaleAnswer = cheater.faultyScaleFinalizeAnswer({
  scaleLabels,
  currentCandidates: ['A', 'C'],
  selectedScale: 'A'
});
assert.equal(scaleAnswer.win, false);
assert.equal(scaleAnswer.actualScale, 'C');

const brokenScaleCoinCandidates = cheater.initialBrokenScaleCoinCandidates(9, scaleLabels);
assert.equal(brokenScaleCoinCandidates.length, 27);
assert.equal(
  cheater.brokenScaleCoinOutcomeForCandidate(
    { coin: 5, brokenScale: 'B' },
    'A',
    'lighter',
    [5],
    [1],
    { coinCount: 9, scaleLabels }
  ),
  'right_down'
);
assert.equal(
  cheater.brokenScaleCoinOutcomeForCandidate(
    { coin: 5, brokenScale: 'B' },
    'B',
    'lighter',
    [5],
    [1],
    { coinCount: 9, scaleLabels }
  ),
  'arbitrary'
);

const brokenScaleCoinFirst = cheater.brokenScaleCoinChooseCheaterOutcome({
  coin_count: 9,
  scaleLabels,
  counterfeit_weight: 'lighter',
  currentCandidates: brokenScaleCoinCandidates,
  instrument: 'A',
  leftCoins: [1, 2, 3],
  rightCoins: [4, 5, 6],
  history: []
});
assert.deepEqual(brokenScaleCoinFirst.scores, {
  left_down: 15,
  right_down: 15,
  balance: 15
});
assert.equal(brokenScaleCoinFirst.outcome, 'left_down');
assert.equal(brokenScaleCoinFirst.candidates.length, 15);

assert.equal(
  cheater.brokenScaleCoinBranchStatus(
    [{ coin: 4, brokenScale: 'A' }, { coin: 4, brokenScale: 'C' }],
    3,
    4
  ),
  'solved'
);

const brokenScaleCoinAnswer = cheater.brokenScaleCoinFinalizeAnswer({
  coin_count: 9,
  scaleLabels,
  currentCandidates: [{ coin: 4, brokenScale: 'A' }, { coin: 4, brokenScale: 'C' }],
  selectedCoin: 4
});
assert.equal(brokenScaleCoinAnswer.win, true);
assert.equal(brokenScaleCoinAnswer.actualCoin, 4);
assert.deepEqual(brokenScaleCoinAnswer.brokenScalesForActualCoin, ['A', 'C']);

const brokenScaleCoinAmbiguousAnswer = cheater.brokenScaleCoinFinalizeAnswer({
  coin_count: 9,
  scaleLabels,
  currentCandidates: [{ coin: 4, brokenScale: 'A' }, { coin: 5, brokenScale: 'A' }],
  selectedCoin: 4
});
assert.equal(brokenScaleCoinAmbiguousAnswer.win, false);
assert.equal(brokenScaleCoinAmbiguousAnswer.actualCoin, 5);

const detectorLabels = ['A', 'B', 'C'];
const brokenDetectorCandidates = cheater.initialBrokenDetectorCoinCandidates(8, detectorLabels);
assert.equal(brokenDetectorCandidates.length, 24);
assert.equal(
  cheater.brokenDetectorCoinTestValidation([], { coinCount: 8 }).valid,
  false
);
assert.deepEqual(
  cheater.brokenDetectorCoinTestValidation([1, 1, 9], { coinCount: 8 }).subset,
  [1]
);
assert.equal(
  cheater.brokenDetectorCoinOutcomeForCandidate(
    { coin: 5, brokenDetector: 'B' },
    'A',
    [1, 2, 5],
    { coinCount: 8, detectorLabels }
  ),
  'yes'
);
assert.equal(
  cheater.brokenDetectorCoinOutcomeForCandidate(
    { coin: 5, brokenDetector: 'B' },
    'B',
    [1, 2, 5],
    { coinCount: 8, detectorLabels }
  ),
  'arbitrary'
);
const brokenDetectorFirst = cheater.brokenDetectorCoinChooseCheaterOutcome({
  coin_count: 8,
  detectorLabels,
  currentCandidates: brokenDetectorCandidates,
  detector: 'A',
  subsetCoins: [1, 2, 3, 4],
  history: []
});
assert.equal(brokenDetectorFirst.outcome, 'yes');
assert.deepEqual(brokenDetectorFirst.scores, {
  yes: { states: 16, coins: 8 },
  no: { states: 16, coins: 8 }
});
assert.equal(brokenDetectorFirst.candidates.length, 16);
assert.equal(
  cheater.brokenDetectorCoinBranchStatus(
    [{ coin: 4, brokenDetector: 'A' }, { coin: 4, brokenDetector: 'C' }],
    5,
    6
  ),
  'solved'
);
const brokenDetectorExpansion = cheater.brokenDetectorCoinExpandExhaustiveNode({
  coin_count: 8,
  detectorLabels,
  currentCandidates: [{ coin: 1, brokenDetector: 'A' }, { coin: 2, brokenDetector: 'B' }],
  detector: 'C',
  subsetCoins: [1],
  usedTests: 2,
  maxTests: 6
});
assert.deepEqual(brokenDetectorExpansion.children.map(child => child.outcome), ['yes', 'no']);
assert.deepEqual(brokenDetectorExpansion.children.map(child => child.candidates), [
  [{ coin: 1, brokenDetector: 'A' }],
  [{ coin: 2, brokenDetector: 'B' }]
]);
assert.deepEqual(brokenDetectorExpansion.children.map(child => child.status), ['solved', 'solved']);
const brokenDetectorAnswer = cheater.brokenDetectorCoinFinalizeAnswer({
  coin_count: 8,
  detectorLabels,
  currentCandidates: [{ coin: 4, brokenDetector: 'A' }, { coin: 4, brokenDetector: 'C' }],
  selectedCoin: 4
});
assert.equal(brokenDetectorAnswer.win, true);
assert.equal(brokenDetectorAnswer.actualCoin, 4);
assert.deepEqual(brokenDetectorAnswer.brokenDetectorsForActualCoin, ['A', 'C']);

const heaviestStates = cheater.initialHeaviestBrokenScaleStates(3, scaleLabels);
assert.equal(heaviestStates.length, 18);
assert.deepEqual(cheater.possibleHeaviestCoins(heaviestStates), [1, 2, 3]);
assert.equal(
  cheater.heaviestBrokenScaleOutcomeForState(
    { order: [2, 3, 1], brokenScale: 'B' },
    'A',
    1,
    2
  ),
  'left_down'
);
assert.equal(
  cheater.heaviestBrokenScaleOutcomeForState(
    { order: [2, 3, 1], brokenScale: 'A' },
    'A',
    1,
    2
  ),
  'arbitrary'
);

const heaviestBalance = cheater.heaviestBrokenScaleFilterStates({
  coin_count: 3,
  scaleLabels,
  currentStates: heaviestStates,
  instrument: 'A',
  leftCoin: 1,
  rightCoin: 2,
  outcome: 'balance'
});
assert.equal(heaviestBalance.length, 6);
assert.deepEqual([...new Set(heaviestBalance.map(state => state.brokenScale))], ['A']);

const heaviestCheaterFirst = cheater.heaviestBrokenScaleChooseCheaterOutcome({
  coin_count: 3,
  scaleLabels,
  currentStates: heaviestStates,
  instrument: 'A',
  leftCoin: 1,
  rightCoin: 2,
  history: []
});
assert.equal(heaviestCheaterFirst.outcome, 'left_down');
assert.deepEqual(heaviestCheaterFirst.candidates, [1, 2, 3]);
assert.deepEqual(heaviestCheaterFirst.scores, {
  left_down: { states: 12, heaviestCoins: 3 },
  right_down: { states: 12, heaviestCoins: 3 },
  balance: { states: 6, heaviestCoins: 3 }
});

const heaviestAfterTwo = cheater.heaviestBrokenScaleFilterStates({
  coin_count: 3,
  scaleLabels,
  currentStates: heaviestBalance,
  instrument: 'B',
  leftCoin: 1,
  rightCoin: 2,
  outcome: 'left_down'
});
assert.deepEqual(cheater.possibleHeaviestCoins(heaviestAfterTwo), [1, 3]);

const heaviestAmbiguousAnswer = cheater.heaviestBrokenScaleFinalizeAnswer({
  coin_count: 3,
  scaleLabels,
  currentStates: heaviestAfterTwo,
  selectedCoin: 1
});
assert.equal(heaviestAmbiguousAnswer.win, false);
assert.equal(heaviestAmbiguousAnswer.actualCoin, 3);

const heaviestForcedAnswer = cheater.heaviestBrokenScaleFinalizeAnswer({
  coin_count: 3,
  scaleLabels,
  currentStates: heaviestAfterTwo.filter(state => state.order.at(-1) === 1),
  selectedCoin: 1
});
assert.equal(heaviestForcedAnswer.win, true);
assert.equal(heaviestForcedAnswer.actualCoin, 1);

const firstExhaustive = cheater.expandExhaustiveNode({
  coin_count: 9,
  counterfeit_weight: 'heavy',
  currentCandidates: cheater.initialCandidates(9),
  leftCoins: [1, 2, 3],
  rightCoins: [4, 5, 6],
  usedWeighings: 0,
  maxWeighings: 2
});
assert.equal(firstExhaustive.children.length, 3);
assert.deepEqual(firstExhaustive.children.map(child => child.candidates), [
  [1, 2, 3],
  [4, 5, 6],
  [7, 8, 9]
]);
assert.deepEqual(firstExhaustive.children.map(child => child.status), ['open', 'open', 'open']);

const secondWeighings = [
  { node: firstExhaustive.children[0], leftCoins: [1], rightCoins: [2], expected: [[1], [2], [3]] },
  { node: firstExhaustive.children[1], leftCoins: [4], rightCoins: [5], expected: [[4], [5], [6]] },
  { node: firstExhaustive.children[2], leftCoins: [7], rightCoins: [8], expected: [[7], [8], [9]] }
];
for (const item of secondWeighings) {
  const expanded = cheater.expandExhaustiveNode({
    coin_count: 9,
    counterfeit_weight: 'heavy',
    currentCandidates: item.node.candidates,
    leftCoins: item.leftCoins,
    rightCoins: item.rightCoins,
    usedWeighings: item.node.usedWeighings,
    maxWeighings: 2
  });
  assert.deepEqual(expanded.children.map(child => child.candidates), item.expected);
  assert.deepEqual(expanded.children.map(child => child.status), ['solved', 'solved', 'solved']);
}

const impossibleOneWeighing = cheater.expandExhaustiveNode({
  coin_count: 4,
  counterfeit_weight: 'heavy',
  currentCandidates: cheater.initialCandidates(4),
  leftCoins: [1],
  rightCoins: [2],
  usedWeighings: 0,
  maxWeighings: 1
});
assert.deepEqual(impossibleOneWeighing.children.map(child => child.candidates), [[1], [2], [3, 4]]);
assert.deepEqual(impossibleOneWeighing.children.map(child => child.status), ['solved', 'solved', 'failed']);

const unknownFirst = cheater.expandUnknownDirectionExhaustiveNode({
  coin_count: 12,
  currentCandidates: cheater.initialUnknownDirectionCandidates(12),
  leftCoins: [1, 2, 3, 4],
  rightCoins: [5, 6, 7, 8],
  usedWeighings: 0,
  maxWeighings: 3
});
assert.equal(unknownFirst.children.length, 3);
assert.deepEqual(unknownFirst.children.map(child => child.candidates.length), [8, 8, 8]);
assert.deepEqual(unknownFirst.children.map(child => child.status), ['open', 'open', 'open']);
assert.deepEqual(unknownFirst.children[0].candidates, [
  { coin: 1, direction: 'heavier' },
  { coin: 2, direction: 'heavier' },
  { coin: 3, direction: 'heavier' },
  { coin: 4, direction: 'heavier' },
  { coin: 5, direction: 'lighter' },
  { coin: 6, direction: 'lighter' },
  { coin: 7, direction: 'lighter' },
  { coin: 8, direction: 'lighter' }
]);

const unknownCheaterFirst = cheater.chooseCheaterUnknownDirectionOutcome({
  coin_count: 12,
  currentCandidates: cheater.initialUnknownDirectionCandidates(12),
  leftCoins: [1, 2, 3, 4],
  rightCoins: [5, 6, 7, 8],
  remainingWeighings: 3,
  history: []
});
assert.equal(unknownCheaterFirst.outcome, 'left_down');
assert.deepEqual(unknownCheaterFirst.scores, {
  left_down: 8,
  right_down: 8,
  balance: 8
});
assert.deepEqual(
  unknownCheaterFirst.candidates,
  cheater.filterUnknownDirectionCandidates({
    coin_count: 12,
    currentCandidates: cheater.initialUnknownDirectionCandidates(12),
    leftCoins: [1, 2, 3, 4],
    rightCoins: [5, 6, 7, 8],
    outcome: unknownCheaterFirst.outcome,
    require_equal_pan_counts: true
  })
);

const unknownTwelveInefficientFirstMoves = [
  { leftCoins: [1], rightCoins: [2], expected: 'balance', scores: { left_down: 2, right_down: 2, balance: 20 } },
  { leftCoins: [1, 2], rightCoins: [3, 4], expected: 'balance', scores: { left_down: 4, right_down: 4, balance: 16 } },
  { leftCoins: [1, 2, 3], rightCoins: [4, 5, 6], expected: 'balance', scores: { left_down: 6, right_down: 6, balance: 12 } },
  { leftCoins: [1, 2, 3, 4], rightCoins: [5, 6, 7, 8], expected: 'left_down', scores: { left_down: 8, right_down: 8, balance: 8 } },
  { leftCoins: [1, 2, 3, 4, 5], rightCoins: [6, 7, 8, 9, 10], expected: 'left_down', scores: { left_down: 10, right_down: 10, balance: 4 } },
  { leftCoins: [1, 2, 3, 4, 5, 6], rightCoins: [7, 8, 9, 10, 11, 12], expected: 'left_down', scores: { left_down: 12, right_down: 12, balance: 0 } }
];
for (const item of unknownTwelveInefficientFirstMoves) {
  const decision = cheater.chooseCheaterUnknownDirectionOutcome({
    coin_count: twelveCoinConfig.coin_count,
    currentCandidates: cheater.initialUnknownDirectionCandidates(twelveCoinConfig.coin_count),
    leftCoins: item.leftCoins,
    rightCoins: item.rightCoins,
    history: [],
    require_equal_pan_counts: twelveCoinConfig.require_equal_pan_counts
  });
  assert.equal(decision.outcome, item.expected);
  assert.deepEqual(decision.scores, item.scores);
  assert.equal(decision.candidates.length, Math.max(...Object.values(item.scores)));
}

const unknownTieWithHistory = cheater.chooseCheaterUnknownDirectionOutcome({
  coin_count: twelveCoinConfig.coin_count,
  currentCandidates: cheater.initialUnknownDirectionCandidates(twelveCoinConfig.coin_count),
  leftCoins: [1, 2, 3, 4],
  rightCoins: [5, 6, 7, 8],
  history: [{ outcome: 'left_down' }],
  require_equal_pan_counts: true
});
assert.equal(unknownTieWithHistory.outcome, 'right_down');

const unknownAmbiguousAnswer = cheater.finalizeCheaterUnknownDirectionAnswer({
  coin_count: 12,
  currentCandidates: unknownFirst.children.find(child => child.outcome === 'balance').candidates,
  selectedCoin: 9,
  selectedDirection: 'heavier'
});
assert.equal(unknownAmbiguousAnswer.win, false);
assert.deepEqual(unknownAmbiguousAnswer.actualCandidate, { coin: 9, direction: 'lighter' });

const unknownCoinOnlyRejectedForSignObjective = cheater.finalizeCheaterUnknownDirectionAnswer({
  coin_count: 12,
  currentCandidates: [{ coin: 4, direction: 'heavier' }],
  selectedCoin: 4,
  objective: 'identify_coin_and_sign'
});
assert.equal(unknownCoinOnlyRejectedForSignObjective.win, false);
assert.deepEqual(unknownCoinOnlyRejectedForSignObjective.actualCandidate, { coin: 4, direction: 'heavier' });

const unknownForcedWin = cheater.finalizeCheaterUnknownDirectionAnswer({
  coin_count: 12,
  currentCandidates: [{ coin: 4, direction: 'heavier' }],
  selectedCoin: 4,
  selectedDirection: 'heavier'
});
assert.equal(unknownForcedWin.win, true);
assert.deepEqual(unknownForcedWin.actualCandidate, { coin: 4, direction: 'heavier' });

assert.equal(
  cheater.exhaustiveUnknownDirectionBranchStatus(
    [{ coin: 4, direction: 'heavier' }, { coin: 4, direction: 'lighter' }],
    3,
    3,
    'identify_coin_only_unknown_direction'
  ),
  'solved'
);
assert.equal(
  cheater.exhaustiveUnknownDirectionBranchStatus(
    [{ coin: 4, direction: 'heavier' }, { coin: 4, direction: 'lighter' }],
    3,
    3
  ),
  'failed'
);

const unknownCoinOnlyWin = cheater.finalizeCheaterUnknownDirectionAnswer({
  coin_count: 13,
  currentCandidates: [{ coin: 7, direction: 'heavier' }, { coin: 7, direction: 'lighter' }],
  selectedCoin: 7,
  objective: 'identify_coin_only_unknown_direction'
});
assert.equal(unknownCoinOnlyWin.win, true);
assert.equal(unknownCoinOnlyWin.actualCoin, 7);
assert.deepEqual(unknownCoinOnlyWin.possibleCoins, [7]);

const unknownCoinOnlyAmbiguous = cheater.finalizeCheaterUnknownDirectionAnswer({
  coin_count: 13,
  currentCandidates: [{ coin: 7, direction: 'heavier' }, { coin: 8, direction: 'lighter' }],
  selectedCoin: 7,
  objective: 'identify_coin_only_unknown_direction'
});
assert.equal(unknownCoinOnlyAmbiguous.win, false);
assert.equal(unknownCoinOnlyAmbiguous.actualCoin, 8);

const thirteenIdentifyOnlyFirst = cheater.chooseCheaterUnknownDirectionOutcome({
  coin_count: thirteenIdentifyOnlyConfig.coin_count,
  currentCandidates: cheater.initialUnknownDirectionCandidates(thirteenIdentifyOnlyConfig.coin_count),
  leftCoins: [1, 2, 3, 4],
  rightCoins: [5, 6, 7, 8],
  history: [],
  require_equal_pan_counts: thirteenIdentifyOnlyConfig.require_equal_pan_counts
});
assert.equal(thirteenIdentifyOnlyFirst.outcome, 'balance');
assert.deepEqual(thirteenIdentifyOnlyFirst.scores, {
  left_down: 8,
  right_down: 8,
  balance: 10
});
assert.deepEqual(thirteenIdentifyOnlyFirst.candidates, [
  { coin: 9, direction: 'heavier' },
  { coin: 9, direction: 'lighter' },
  { coin: 10, direction: 'heavier' },
  { coin: 10, direction: 'lighter' },
  { coin: 11, direction: 'heavier' },
  { coin: 11, direction: 'lighter' },
  { coin: 12, direction: 'heavier' },
  { coin: 12, direction: 'lighter' },
  { coin: 13, direction: 'heavier' },
  { coin: 13, direction: 'lighter' }
]);

const thirteenIdentifyOnlySecond = cheater.chooseCheaterUnknownDirectionOutcome({
  coin_count: thirteenIdentifyOnlyConfig.coin_count,
  currentCandidates: thirteenIdentifyOnlyFirst.candidates,
  leftCoins: [10, 11, 12],
  rightCoins: [1, 2, 3],
  history: [{ outcome: thirteenIdentifyOnlyFirst.outcome }],
  require_equal_pan_counts: thirteenIdentifyOnlyConfig.require_equal_pan_counts
});
assert.equal(thirteenIdentifyOnlySecond.outcome, 'balance');
assert.deepEqual(thirteenIdentifyOnlySecond.scores, {
  left_down: 3,
  right_down: 3,
  balance: 4
});
assert.equal(
  cheater.exhaustiveUnknownDirectionBranchStatus(
    [{ coin: 9, direction: 'heavier' }, { coin: 9, direction: 'lighter' }],
    thirteenIdentifyOnlyConfig.max_weighings,
    thirteenIdentifyOnlyConfig.max_weighings,
    thirteenIdentifyOnlyConfig.objective
  ),
  'solved'
);

const thirteenKnownGenuineFirst = cheater.chooseCheaterUnknownDirectionOutcome({
  coin_count: thirteenKnownGenuineConfig.coin_count,
  currentCandidates: cheater.initialUnknownDirectionCandidates(thirteenKnownGenuineConfig.coin_count),
  leftCoins: [1, 2, 3, 14],
  rightCoins: [4, 5, 6, 7],
  history: [],
  require_equal_pan_counts: thirteenKnownGenuineConfig.require_equal_pan_counts
});
assert.equal(thirteenKnownGenuineFirst.outcome, 'balance');
assert.deepEqual(thirteenKnownGenuineFirst.scores, {
  left_down: 7,
  right_down: 7,
  balance: 12
});

assert.equal(cheater.initialUnknownDirectionCandidates(thirteenKnownGenuineConfig.coin_count).length, 26);
assert.equal(cheater.initialUnknownDirectionCandidates(thirteenKnownGenuineConfig.coin_count).some(candidate => candidate.coin === 14), false);

assert.equal(
  cheater.outcomeForUnknownDirectionCandidate(
    { coin: 1, direction: 'heavier' },
    [1, 14],
    [2, 3],
    { requireEqualPanCounts: thirteenKnownGenuineConfig.require_equal_pan_counts }
  ),
  'left_down'
);
assert.equal(
  cheater.outcomeForUnknownDirectionCandidate(
    { coin: 4, direction: 'lighter' },
    [1, 14],
    [2, 3],
    { requireEqualPanCounts: thirteenKnownGenuineConfig.require_equal_pan_counts }
  ),
  'balance'
);

const thirteenKnownGenuineStrategy = [
  { leftCoins: [1, 3, 4, 5, 14], rightCoins: [2, 6, 7, 8, 9] },
  { leftCoins: [1, 3, 7, 8, 9], rightCoins: [2, 10, 11, 12, 14] },
  { leftCoins: [1, 4, 6, 9, 12], rightCoins: [3, 7, 10, 13, 14] }
];
let thirteenKnownGenuineCandidates = cheater.initialUnknownDirectionCandidates(thirteenKnownGenuineConfig.coin_count);
let thirteenKnownGenuineHistory = [];
for (const [index, weighing] of thirteenKnownGenuineStrategy.entries()) {
  const decision = cheater.chooseCheaterUnknownDirectionOutcome({
    coin_count: thirteenKnownGenuineConfig.coin_count,
    currentCandidates: thirteenKnownGenuineCandidates,
    leftCoins: weighing.leftCoins,
    rightCoins: weighing.rightCoins,
    history: thirteenKnownGenuineHistory,
    require_equal_pan_counts: thirteenKnownGenuineConfig.require_equal_pan_counts
  });
  assert.equal(Object.values(decision.scores).reduce((sum, count) => sum + count, 0), thirteenKnownGenuineCandidates.length);
  assert.equal(decision.candidates.some(candidate => candidate.coin === 14), false);
  thirteenKnownGenuineCandidates = decision.candidates;
  thirteenKnownGenuineHistory.push({ outcome: decision.outcome });
  if (index < thirteenKnownGenuineStrategy.length - 1) assert.equal(thirteenKnownGenuineCandidates.length > 1, true);
}
assert.equal(thirteenKnownGenuineCandidates.length, 1);

const thirteenKnownGenuineSolved = thirteenKnownGenuineCandidates[0];
const thirteenKnownGenuineMissingSign = cheater.finalizeCheaterUnknownDirectionAnswer({
  coin_count: thirteenKnownGenuineConfig.coin_count,
  currentCandidates: thirteenKnownGenuineCandidates,
  selectedCoin: thirteenKnownGenuineSolved.coin,
  objective: thirteenKnownGenuineConfig.objective
});
assert.equal(thirteenKnownGenuineMissingSign.win, false);

const thirteenKnownGenuineForcedWin = cheater.finalizeCheaterUnknownDirectionAnswer({
  coin_count: thirteenKnownGenuineConfig.coin_count,
  currentCandidates: thirteenKnownGenuineCandidates,
  selectedCoin: thirteenKnownGenuineSolved.coin,
  selectedDirection: thirteenKnownGenuineSolved.direction,
  objective: thirteenKnownGenuineConfig.objective
});
assert.equal(thirteenKnownGenuineForcedWin.win, true);
assert.deepEqual(thirteenKnownGenuineForcedWin.actualCandidate, thirteenKnownGenuineSolved);

assert.equal(
  cheater.outcomeForUnknownDirectionCandidate(
    { coin: 1, direction: 'heavier' },
    [1, 2],
    [3],
  ),
  null
);

const pairedPairs = [[1, 2], [3, 4], [5, 6]];
const pairedStates = cheater.initialPairedLightCandidates(pairedPairs);
assert.equal(pairedStates.length, 8);
assert.deepEqual(pairedStates[0], { coins: [1, 3, 5] });
assert.equal(
  cheater.outcomeForPairedLightCandidate(
    { coins: [1, 3, 5] },
    [1, 3],
    [2, 5],
    { pairs: pairedPairs }
  ),
  'right_down'
);

const cardStrategy = [
  { leftCoins: [1, 3], rightCoins: [2, 5] },
  { leftCoins: [2, 3], rightCoins: [4, 5] }
];
const signatures = new Map();
for (const state of pairedStates) {
  const signature = cardStrategy
    .map(weighing => cheater.outcomeForPairedLightCandidate(state, weighing.leftCoins, weighing.rightCoins, { pairs: pairedPairs }))
    .join('|');
  assert.equal(signatures.has(signature), false, `duplicate paired signature ${signature}`);
  signatures.set(signature, state);
}
assert.equal(signatures.size, 8);

const pairedFirst = cheater.pairedLightExpandExhaustiveNode({
  pairs: pairedPairs,
  currentCandidates: pairedStates,
  leftCoins: cardStrategy[0].leftCoins,
  rightCoins: cardStrategy[0].rightCoins,
  usedWeighings: 0,
  maxWeighings: 2
});
assert.equal(pairedFirst.children.length, 3);
for (const child of pairedFirst.children) {
  const expanded = cheater.pairedLightExpandExhaustiveNode({
    pairs: pairedPairs,
    currentCandidates: child.candidates,
    leftCoins: cardStrategy[1].leftCoins,
    rightCoins: cardStrategy[1].rightCoins,
    usedWeighings: child.usedWeighings,
    maxWeighings: 2
  });
  assert.deepEqual(expanded.children.map(branch => branch.status), expanded.children.map(() => 'solved'));
}

const badPairedWeighings = [
  { leftCoins: [1], rightCoins: [2] },
  { leftCoins: [3], rightCoins: [4] }
];
const badSignatures = new Map();
for (const state of pairedStates) {
  const signature = badPairedWeighings
    .map(weighing => cheater.outcomeForPairedLightCandidate(state, weighing.leftCoins, weighing.rightCoins, { pairs: pairedPairs }))
    .join('|');
  badSignatures.set(signature, (badSignatures.get(signature) || 0) + 1);
}
assert.equal([...badSignatures.values()].some(count => count > 1), true);

const ambiguousPairedAnswer = cheater.pairedLightFinalizeAnswer({
  pairs: pairedPairs,
  currentCandidates: [{ coins: [1, 3, 5] }, { coins: [1, 3, 6] }],
  selectedCoins: [1, 3, 5]
});
assert.equal(ambiguousPairedAnswer.win, false);
assert.deepEqual(ambiguousPairedAnswer.actualCoins, [1, 3, 6]);

const forcedPairedAnswer = cheater.pairedLightFinalizeAnswer({
  pairs: pairedPairs,
  currentCandidates: [{ coins: [2, 4, 6] }],
  selectedCoins: [2, 4, 6]
});
assert.equal(forcedPairedAnswer.win, true);
assert.deepEqual(forcedPairedAnswer.actualCoins, [2, 4, 6]);

const multipleStates = cheater.initialMultipleLightCandidates(6, 2);
assert.equal(multipleStates.length, 15);
assert.deepEqual(multipleStates[0], { coins: [1, 2] });
assert.deepEqual(multipleStates.at(-1), { coins: [5, 6] });
assert.equal(
  cheater.outcomeForMultipleLightCandidate(
    { coins: [1, 2] },
    [1, 3],
    [4, 5],
    { coinCount: 6, lightCount: 2 }
  ),
  'right_down'
);
assert.deepEqual(
  cheater.commonLightCoins([{ coins: [1, 2] }, { coins: [1, 3] }, { coins: [1, 4] }]),
  [1]
);
assert.equal(
  cheater.multipleLightBranchStatus([{ coins: [1, 2] }, { coins: [1, 3] }], 2, 2),
  'solved'
);
assert.equal(
  cheater.multipleLightBranchStatus([{ coins: [1, 2] }, { coins: [3, 4] }], 2, 2),
  'failed'
);

const multipleFirst = cheater.multipleLightExpandExhaustiveNode({
  coin_count: 6,
  light_count: 2,
  currentCandidates: multipleStates,
  leftCoins: [1, 2],
  rightCoins: [3, 4],
  usedWeighings: 0,
  maxWeighings: 2
});
assert.equal(multipleFirst.children.length, 3);
assert.deepEqual(multipleFirst.children.map(child => child.candidates.length), [5, 5, 5]);
for (const child of multipleFirst.children) {
  const second = child.outcome === 'right_down'
    ? { leftCoins: [1], rightCoins: [3] }
    : (child.outcome === 'left_down'
      ? { leftCoins: [3], rightCoins: [1] }
      : { leftCoins: [1], rightCoins: [5] });
  const expanded = cheater.multipleLightExpandExhaustiveNode({
    coin_count: 6,
    light_count: 2,
    currentCandidates: child.candidates,
    leftCoins: second.leftCoins,
    rightCoins: second.rightCoins,
    usedWeighings: child.usedWeighings,
    maxWeighings: 2
  });
  assert.deepEqual(expanded.children.map(branch => branch.status), expanded.children.map(() => 'solved'));
  assert.equal(expanded.children.every(branch => cheater.commonLightCoins(branch.candidates).length > 0), true);
}

const multipleCheaterFirst = cheater.multipleLightChooseCheaterOutcome({
  coin_count: 6,
  light_count: 2,
  currentCandidates: multipleStates,
  leftCoins: [1],
  rightCoins: [2],
  history: []
});
assert.equal(multipleCheaterFirst.outcome, 'balance');
assert.deepEqual(multipleCheaterFirst.scores.balance, {
  states: 7,
  pairs: 7,
  possibleLightCoins: 6,
  guaranteedLightCoins: 0
});

const multipleAmbiguousAnswer = cheater.multipleLightFinalizeAnswer({
  coin_count: 6,
  light_count: 2,
  currentCandidates: [{ coins: [1, 2] }, { coins: [1, 3] }, { coins: [2, 3] }],
  selectedCoin: 1
});
assert.equal(multipleAmbiguousAnswer.win, false);
assert.deepEqual(multipleAmbiguousAnswer.actualCoins, [2, 3]);

const multipleForcedAnswer = cheater.multipleLightFinalizeAnswer({
  coin_count: 6,
  light_count: 2,
  currentCandidates: [{ coins: [1, 2] }, { coins: [1, 3] }],
  selectedCoin: 1
});
assert.equal(multipleForcedAnswer.win, true);
assert.deepEqual(multipleForcedAnswer.guaranteedCoins, [1]);

const groupedStates = cheater.initialGroupedMultipleLightCandidates(6, [[1, 2, 3, 4], [5, 6]], [1, 1]);
assert.equal(groupedStates.length, 8);
assert.deepEqual(groupedStates[0], { coins: [1, 5] });
assert.deepEqual(groupedStates.at(-1), { coins: [4, 6] });
assert.equal(
  cheater.outcomeForMultipleLightCandidate(
    { coins: [1, 5] },
    [1, 5],
    [2, 6],
    { coinCount: 6, lightCount: 2 }
  ),
  'right_down'
);

const savinFixedWeighings = [
  { leftCoins: [4, 6], rightCoins: [1, 2] },
  { leftCoins: [3, 5], rightCoins: [1, 4] }
];
const groupedSignatures = new Map();
for (const state of groupedStates) {
  const signature = savinFixedWeighings
    .map(weighing => cheater.outcomeForMultipleLightCandidate(state, weighing.leftCoins, weighing.rightCoins, { coinCount: 6, lightCount: 2 }))
    .join('|');
  assert.equal(groupedSignatures.has(signature), false, `duplicate grouped signature ${signature}`);
  groupedSignatures.set(signature, state);
}
assert.equal(groupedSignatures.size, 8);

const groupedFirst = cheater.multipleLightExpandExhaustiveNode({
  coin_count: 6,
  light_count: 2,
  groups: [[1, 2, 3, 4], [5, 6]],
  counterfeit_per_group: [1, 1],
  objective: 'identify_all_counterfeits',
  currentCandidates: groupedStates,
  leftCoins: savinFixedWeighings[0].leftCoins,
  rightCoins: savinFixedWeighings[0].rightCoins,
  usedWeighings: 0,
  maxWeighings: 2
});
assert.equal(groupedFirst.children.length, 3);
for (const child of groupedFirst.children) {
  const expanded = cheater.multipleLightExpandExhaustiveNode({
    coin_count: 6,
    light_count: 2,
    groups: [[1, 2, 3, 4], [5, 6]],
    counterfeit_per_group: [1, 1],
    objective: 'identify_all_counterfeits',
    currentCandidates: child.candidates,
    leftCoins: savinFixedWeighings[1].leftCoins,
    rightCoins: savinFixedWeighings[1].rightCoins,
    usedWeighings: child.usedWeighings,
    maxWeighings: 2
  });
  assert.deepEqual(expanded.children.map(branch => branch.status), expanded.children.map(() => 'solved'));
  assert.equal(expanded.children.every(branch => cheater.uniqueLightState(branch.candidates)), true);
}

const groupedCheaterFirst = cheater.multipleLightChooseCheaterOutcome({
  coin_count: 6,
  light_count: 2,
  groups: [[1, 2, 3, 4], [5, 6]],
  counterfeit_per_group: [1, 1],
  objective: 'identify_all_counterfeits',
  currentCandidates: groupedStates,
  leftCoins: [1],
  rightCoins: [2],
  history: []
});
assert.equal(groupedCheaterFirst.outcome, 'balance');
assert.equal(groupedCheaterFirst.scores.balance.pairs, 4);

const groupedAmbiguousAnswer = cheater.multipleLightFinalizeAnswer({
  coin_count: 6,
  light_count: 2,
  groups: [[1, 2, 3, 4], [5, 6]],
  counterfeit_per_group: [1, 1],
  objective: 'identify_all_counterfeits',
  currentCandidates: [{ coins: [1, 5] }, { coins: [1, 6] }],
  selectedCoins: [1, 5]
});
assert.equal(groupedAmbiguousAnswer.win, false);
assert.deepEqual(groupedAmbiguousAnswer.actualCoins, [1, 6]);

const groupedForcedAnswer = cheater.multipleLightFinalizeAnswer({
  coin_count: 6,
  light_count: 2,
  groups: [[1, 2, 3, 4], [5, 6]],
  counterfeit_per_group: [1, 1],
  objective: 'identify_all_counterfeits',
  currentCandidates: [{ coins: [2, 6] }],
  selectedCoins: [2, 6]
});
assert.equal(groupedForcedAnswer.win, true);
assert.deepEqual(groupedForcedAnswer.actualCoins, [2, 6]);

const numericStates = cheater.numericSignatureInitialStates(6, {
  allowEmptySubset: true,
  excludeAllFake: true
});
assert.equal(numericStates.length, 63);
assert.equal(numericStates.some(state => state.mask === 0), true);
assert.equal(numericStates.some(state => state.mask === 63), false);
assert.deepEqual(
  cheater.numericSignatureAmountsValidation(['', '2', 0, '03', null, undefined], 6),
  { valid: true, error: '', amounts: [0, 2, 0, 3, 0, 0] }
);
assert.equal(
  cheater.numericSignatureAmountsValidation(['-1', 2, 3, 4, 5, 6], 6).valid,
  false
);
assert.equal(
  cheater.numericSignatureAmountsValidation([1, '1.5', 3, 4, 5, 6], 6).valid,
  false
);

const powersOfTwoExpansion = cheater.numericSignatureExpandExhaustiveNode({
  bag_count: 6,
  amounts: [1, 2, 4, 8, 16, 32],
  currentStates: numericStates,
  usedWeighings: 0,
  maxWeighings: 1,
  allowEmptySubset: true,
  excludeAllFake: true
});
assert.equal(powersOfTwoExpansion.children.length, 63);
assert.equal(powersOfTwoExpansion.children.every(child => child.status === 'solved'), true);
assert.equal(powersOfTwoExpansion.children.every(child => child.states.length === 1), true);

const repeatedCoefficients = cheater.numericSignatureExpandExhaustiveNode({
  bag_count: 6,
  amounts: [1, 1, 1, 1, 1, 1],
  currentStates: numericStates,
  usedWeighings: 0,
  maxWeighings: 1,
  allowEmptySubset: true,
  excludeAllFake: true
});
assert.equal(repeatedCoefficients.children.some(child => child.status === 'failed'), true);
assert.equal(Math.max(...repeatedCoefficients.children.map(child => child.states.length)) > 1, true);

const observedPowers = cheater.numericSignatureObservationForState(
  { bags: [1, 3, 6] },
  [1, 2, 4, 8, 16, 32],
  { genuineWeight: 10, bagCount: 6 }
);
assert.equal(observedPowers.total, 63);
assert.equal(observedPowers.deficit, 37);
assert.equal(observedPowers.deficitResidue, 37);
assert.deepEqual(
  cheater.numericSignatureFilterStates({
    bag_count: 6,
    amounts: [1, 2, 4, 8, 16, 32],
    currentStates: numericStates,
    deficitResidue: observedPowers.deficitResidue,
    allowEmptySubset: true,
    excludeAllFake: true
  }).map(state => state.bags),
  [[1, 3, 6]]
);

const numericAmbiguousAnswer = cheater.numericSignatureFinalizeAnswer({
  bag_count: 6,
  currentStates: repeatedCoefficients.children.find(child => child.states.length > 1).states,
  selectedBags: [1],
  allowEmptySubset: true,
  excludeAllFake: true
});
assert.equal(numericAmbiguousAnswer.win, false);

const stackStates = cheater.numericSignatureInitialStates(10, {
  objective: 'identify_fake_bag',
  stateModel: 'single_fake_bag',
  fakeBagCount: 1,
  counterfeitWeight: 'lighter',
  counterfeitDelta: 1
});
assert.equal(stackStates.length, 10);
assert.deepEqual(stackStates[9].bags, [10]);

const stackExpansion = cheater.numericSignatureExpandExhaustiveNode({
  bag_count: 10,
  amounts: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  currentStates: stackStates,
  usedWeighings: 0,
  maxWeighings: 1,
  objective: 'identify_fake_bag',
  stateModel: 'single_fake_bag',
  fakeBagCount: 1,
  counterfeitWeight: 'lighter',
  counterfeitDelta: 1,
  genuineWeight: 10,
  observationModel: 'actual_weight'
});
assert.equal(stackExpansion.children.length, 10);
assert.equal(stackExpansion.children.every(child => child.status === 'solved'), true);
assert.deepEqual(
  stackExpansion.children.map(child => child.weight).sort((a, b) => a - b),
  [540, 541, 542, 543, 544, 545, 546, 547, 548, 549]
);

const observedStack = cheater.numericSignatureObservationForState(
  { bags: [7] },
  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  {
    objective: 'identify_fake_bag',
    stateModel: 'single_fake_bag',
    fakeBagCount: 1,
    counterfeitWeight: 'lighter',
    counterfeitDelta: 1,
    genuineWeight: 10,
    observationModel: 'actual_weight'
  }
);
assert.equal(observedStack.expectedWeight, 550);
assert.equal(observedStack.weight, 543);
assert.deepEqual(
  cheater.numericSignatureFilterStates({
    bag_count: 10,
    amounts: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    currentStates: stackStates,
    observedDeviation: observedStack.observedDeviation,
    objective: 'identify_fake_bag',
    stateModel: 'single_fake_bag',
    fakeBagCount: 1,
    counterfeitWeight: 'lighter',
    counterfeitDelta: 1,
    genuineWeight: 10,
    observationModel: 'actual_weight'
  }).map(state => state.bags),
  [[7]]
);

const fiveCoinPairStates = cheater.numericSignatureInitialStates(5, {
  objective: 'identify_fake_coin_set',
  stateModel: 'fixed_fake_count',
  fakeBagCount: 2,
  counterfeitWeight: 'lighter',
  counterfeitDelta: 1,
  genuineWeight: 10,
  observationModel: 'actual_weight'
});
assert.equal(fiveCoinPairStates.length, 10);
assert.deepEqual(fiveCoinPairStates[0].bags, [1, 2]);
assert.deepEqual(fiveCoinPairStates.at(-1).bags, [4, 5]);
assert.equal(
  cheater.numericSignatureStateKey({ bags: [1, 4] }),
  cheater.numericSignatureStateKey({ mask: 9, bags: [1, 4] })
);

const fiveCoinOptions = {
  objective: 'identify_fake_coin_set',
  stateModel: 'fixed_fake_count',
  fakeBagCount: 2,
  counterfeitWeight: 'lighter',
  counterfeitDelta: 1,
  genuineWeight: 10,
  observationModel: 'actual_weight'
};
const fiveCoinSubsets = [
  [0, 1, 0, 0, 1],
  [0, 0, 1, 0, 1],
  [0, 0, 0, 1, 1]
];
const fiveCoinSignatures = new Map();
for (const state of fiveCoinPairStates) {
  const signature = fiveCoinSubsets
    .map(amounts => cheater.numericSignatureObservationForState(state, amounts, fiveCoinOptions).weight)
    .join('|');
  assert.equal(fiveCoinSignatures.has(signature), false, `duplicate five-coin digital signature ${signature}`);
  fiveCoinSignatures.set(signature, state);
}
assert.equal(fiveCoinSignatures.size, 10);

let compatibleFiveCoinStates = fiveCoinPairStates;
const hiddenFiveCoinPair = { bags: [1, 5] };
for (const amounts of fiveCoinSubsets) {
  const observation = cheater.numericSignatureObservationForState(hiddenFiveCoinPair, amounts, fiveCoinOptions);
  compatibleFiveCoinStates = cheater.numericSignatureFilterStates({
    bag_count: 5,
    amounts,
    currentStates: compatibleFiveCoinStates,
    observedDeviation: observation.observedDeviation,
    weight: observation.weight,
    ...fiveCoinOptions
  });
}
assert.deepEqual(compatibleFiveCoinStates.map(state => state.bags), [[1, 5]]);
assert.equal(
  cheater.numericSignatureFinalizeAnswer({
    bag_count: 5,
    currentStates: compatibleFiveCoinStates,
    selectedBags: [1, 5],
    ...fiveCoinOptions
  }).win,
  true
);

let compatiblePolandReportedStates = fiveCoinPairStates;
const polandReportedPair = { bags: [1, 4] };
for (const amounts of [
  [0, 1, 0, 0, 1],
  [0, 0, 1, 0, 1],
  [0, 0, 0, 1, 1]
]) {
  const observation = cheater.numericSignatureObservationForState(polandReportedPair, amounts, fiveCoinOptions);
  compatiblePolandReportedStates = cheater.numericSignatureFilterStates({
    bag_count: 5,
    amounts,
    currentStates: compatiblePolandReportedStates,
    observedDeviation: observation.observedDeviation,
    weight: observation.weight,
    ...fiveCoinOptions
  });
}
assert.deepEqual(compatiblePolandReportedStates.map(state => state.bags), [[1, 4]]);
assert.equal(
  cheater.numericSignatureFinalizeAnswer({
    bag_count: 5,
    currentStates: compatiblePolandReportedStates,
    selectedBags: [1, 4],
    ...fiveCoinOptions
  }).win,
  true
);

const firstFiveCoinExpansion = cheater.numericSignatureExpandExhaustiveNode({
  bag_count: 5,
  amounts: fiveCoinSubsets[0],
  currentStates: fiveCoinPairStates,
  usedWeighings: 0,
  maxWeighings: 3,
  ...fiveCoinOptions
});
assert.equal(firstFiveCoinExpansion.children.some(child => child.status === 'open'), true);
assert.equal(firstFiveCoinExpansion.children.every(child => child.status !== 'failed'), true);

console.log('weighing_cheater_selftest: ok');
