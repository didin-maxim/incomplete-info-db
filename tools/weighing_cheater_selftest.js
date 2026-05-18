const assert = require('node:assert/strict');
const cheater = require('../viewer/weighing_cheater.js');

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

console.log('weighing_cheater_selftest: ok');
