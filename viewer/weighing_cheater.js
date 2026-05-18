(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.WeighingCheater = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const OUTCOMES = ['left_down', 'right_down', 'balance'];
  const OUTCOME_LABELS = {
    left_down: 'левая чаша тяжелее',
    right_down: 'правая чаша тяжелее',
    balance: 'равновесие'
  };

  function uniqueCoins(coins, coinCount = null) {
    const seen = new Set();
    const result = [];
    for (const raw of coins || []) {
      const coin = Number(raw);
      if (!Number.isInteger(coin) || coin < 1) continue;
      if (coinCount != null && coin > coinCount) continue;
      if (seen.has(coin)) continue;
      seen.add(coin);
      result.push(coin);
    }
    return result;
  }

  function initialCandidates(coinCount) {
    const count = Number(coinCount);
    if (!Number.isInteger(count) || count < 1) return [];
    return Array.from({ length: count }, (_item, index) => index + 1);
  }

  function normalizeWeight(counterfeitWeight) {
    const value = String(counterfeitWeight || '').toLowerCase();
    if (value === 'light' || value === 'lighter') return 'light';
    if (value === 'heavy' || value === 'heavier') return 'heavy';
    return null;
  }

  function outcomeForCandidate(candidate, counterfeitWeight, leftCoins, rightCoins) {
    const weight = normalizeWeight(counterfeitWeight);
    if (!weight) return null;
    const left = new Set(leftCoins || []);
    const right = new Set(rightCoins || []);
    const onLeft = left.has(candidate);
    const onRight = right.has(candidate);
    if (onLeft && onRight) return null;
    if (!onLeft && !onRight) return 'balance';
    if (weight === 'heavy') return onLeft ? 'left_down' : 'right_down';
    return onLeft ? 'right_down' : 'left_down';
  }

  function filterCandidates(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const currentCandidates = uniqueCoins(
      params?.currentCandidates?.length ? params.currentCandidates : initialCandidates(coinCount),
      Number.isInteger(coinCount) ? coinCount : null
    );
    const leftCoins = uniqueCoins(params?.leftCoins, Number.isInteger(coinCount) ? coinCount : null);
    const rightCoins = uniqueCoins(params?.rightCoins, Number.isInteger(coinCount) ? coinCount : null);
    const outcome = params?.outcome;
    return currentCandidates.filter(candidate =>
      outcomeForCandidate(candidate, params?.counterfeit_weight ?? params?.counterfeitWeight, leftCoins, rightCoins) === outcome
    );
  }

  function partitionCandidates(params) {
    const partitions = Object.fromEntries(OUTCOMES.map(outcome => [outcome, filterCandidates({ ...params, outcome })]));
    return partitions;
  }

  function exhaustiveBranchStatus(candidates, usedWeighings, maxWeighings) {
    const remaining = uniqueCoins(candidates);
    const used = Number(usedWeighings);
    const limit = Number(maxWeighings);
    if (remaining.length === 1) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function expandExhaustiveNode(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const currentCandidates = uniqueCoins(
      params?.currentCandidates?.length ? params.currentCandidates : initialCandidates(coinCount),
      Number.isInteger(coinCount) ? coinCount : null
    );
    const usedWeighings = Number(params?.usedWeighings ?? params?.used_weighings ?? 0);
    const maxWeighings = Number(params?.maxWeighings ?? params?.max_weighings);
    const partitions = partitionCandidates({
      ...params,
      currentCandidates,
      coin_count: coinCount
    });
    const children = OUTCOMES
      .map(outcome => {
        const candidates = partitions[outcome];
        return {
          outcome,
          label: OUTCOME_LABELS[outcome],
          candidates,
          usedWeighings: usedWeighings + 1,
          status: exhaustiveBranchStatus(candidates, usedWeighings + 1, maxWeighings)
        };
      })
      .filter(child => child.candidates.length > 0);
    return { partitions, children };
  }

  function chooseCheaterOutcome(params) {
    const partitions = partitionCandidates(params || {});
    const history = Array.isArray(params?.history) ? params.history : [];
    const maxSize = Math.max(...OUTCOMES.map(outcome => partitions[outcome].length));
    const tied = OUTCOMES.filter(outcome => partitions[outcome].length === maxSize);
    const frequencies = Object.fromEntries(OUTCOMES.map(outcome => [outcome, 0]));
    for (const entry of history) {
      const outcome = typeof entry === 'string' ? entry : entry?.outcome;
      if (outcome in frequencies) frequencies[outcome] += 1;
    }

    // Tie-break is deterministic: among equally large branches, prefer the least
    // used previous outcome, then left_down, right_down, balance. This avoids
    // random play and makes repeated equality harder to exploit.
    const outcome = tied.slice().sort((a, b) =>
      frequencies[a] - frequencies[b] || OUTCOMES.indexOf(a) - OUTCOMES.indexOf(b)
    )[0];

    return {
      outcome,
      label: OUTCOME_LABELS[outcome],
      candidates: partitions[outcome],
      partitions,
      scores: Object.fromEntries(OUTCOMES.map(item => [item, partitions[item].length]))
    };
  }

  function finalizeCheaterAnswer(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const candidates = uniqueCoins(
      params?.currentCandidates?.length ? params.currentCandidates : initialCandidates(coinCount),
      Number.isInteger(coinCount) ? coinCount : null
    );
    const selectedCoin = Number(params?.selectedCoin);
    if (candidates.length === 1) {
      const actualCoin = candidates[0];
      return { win: actualCoin === selectedCoin, actualCoin, candidates };
    }
    const actualCoin = candidates.find(candidate => candidate !== selectedCoin) ?? candidates[0] ?? null;
    return { win: false, actualCoin, candidates };
  }

  return {
    OUTCOMES,
    OUTCOME_LABELS,
    initialCandidates,
    uniqueCoins,
    outcomeForCandidate,
    filterCandidates,
    partitionCandidates,
    exhaustiveBranchStatus,
    expandExhaustiveNode,
    chooseCheaterOutcome,
    finalizeCheaterAnswer
  };
});
