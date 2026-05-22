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

  const THRESHOLD_BALANCE_OUTCOMES = ['left_reliable_lighter', 'right_reliable_lighter', 'no_reliable_tilt'];
  const THRESHOLD_BALANCE_LABELS = {
    left_reliable_lighter: 'левая чаша надежно легче',
    right_reliable_lighter: 'правая чаша надежно легче',
    no_reliable_tilt: 'нет надежного перекоса'
  };

  const YES_NO_OUTCOMES = ['yes', 'no'];
  const YES_NO_LABELS = {
    yes: 'yes',
    no: 'no'
  };

  const COIN_STATUS_DEFINITIONS = {
    unmarked: { label: 'не отмечена', className: 'coin-status-unmarked' },
    genuine: { label: 'точно настоящая', className: 'coin-status-genuine' },
    possible_fake: { label: 'может быть фальшивой', className: 'coin-status-possible-fake' },
    definite_fake: { label: 'точно фальшивая', className: 'coin-status-definite-fake' },
    possible_lighter: { label: 'может быть легкой фальшивой', className: 'coin-status-possible-lighter' },
    possible_heavier: { label: 'может быть тяжелой фальшивой', className: 'coin-status-possible-heavier' },
    possible_lighter_or_heavier: { label: 'может быть легкой или тяжелой', className: 'coin-status-possible-both' },
    definite_lighter: { label: 'точно легкая фальшивая', className: 'coin-status-definite-lighter' },
    definite_heavier: { label: 'точно тяжелая фальшивая', className: 'coin-status-definite-heavier' },
    definite_fake_unknown_direction: { label: 'точно фальшивая, знак не ясен', className: 'coin-status-definite-unknown' }
  };

  const KNOWN_DIRECTION_STATUS_OPTIONS = ['unmarked', 'genuine', 'possible_fake', 'definite_fake'];
  const UNKNOWN_DIRECTION_STATUS_OPTIONS = [
    'unmarked',
    'genuine',
    'possible_lighter',
    'possible_heavier',
    'possible_lighter_or_heavier',
    'definite_lighter',
    'definite_heavier',
    'definite_fake_unknown_direction'
  ];
  const LIGHT_SET_STATUS_OPTIONS = ['unmarked', 'genuine', 'possible_fake', 'definite_fake'];

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

  function initialCandidates(coinCount, allowNoCounterfeit = false) {
    const count = Number(coinCount);
    if (!Number.isInteger(count) || count < 1) return [];
    const candidates = Array.from({ length: count }, (_item, index) => index + 1);
    return allowNoCounterfeit ? [0, ...candidates] : candidates;
  }

  function normalizeKnownDirectionCandidates(candidates, coinCount = null, allowNoCounterfeit = false) {
    const limit = Number(coinCount);
    const hasLimit = coinCount != null && Number.isInteger(limit);
    const seen = new Set();
    const result = [];
    for (const raw of candidates || []) {
      const coin = Number(raw?.coin ?? raw?.id ?? raw);
      if (coin === 0 && allowNoCounterfeit) {
        if (!seen.has(0)) {
          seen.add(0);
          result.push(0);
        }
        continue;
      }
      if (!Number.isInteger(coin) || coin < 1) continue;
      if (hasLimit && coin > limit) continue;
      if (seen.has(coin)) continue;
      seen.add(coin);
      result.push(coin);
    }
    return result;
  }

  function statusDefinition(key) {
    return COIN_STATUS_DEFINITIONS[key] || COIN_STATUS_DEFINITIONS.unmarked;
  }

  function coinStatusDefinitions() {
    return { ...COIN_STATUS_DEFINITIONS };
  }

  function coinStatusOptions(model) {
    const value = String(model || '').toLowerCase();
    if (value === 'unknown_direction' || value === 'single_counterfeit_unknown_direction') return [...UNKNOWN_DIRECTION_STATUS_OPTIONS];
    if (value === 'light_set' || value === 'multiple_light' || value === 'paired_light') return [...LIGHT_SET_STATUS_OPTIONS];
    return [...KNOWN_DIRECTION_STATUS_OPTIONS];
  }

  function normalizeDirection(direction) {
    const value = String(direction || '').toLowerCase();
    if (value === 'heavy' || value === 'heavier') return 'heavier';
    if (value === 'light' || value === 'lighter') return 'lighter';
    return null;
  }

  function initialUnknownDirectionCandidates(coinCount, allowNoCounterfeit = false) {
    const count = Number(coinCount);
    if (!Number.isInteger(count) || count < 1) return [];
    const result = allowNoCounterfeit ? [{ coin: 0, direction: 'none' }] : [];
    for (let coin = 1; coin <= count; coin += 1) {
      result.push({ coin, direction: 'heavier' });
      result.push({ coin, direction: 'lighter' });
    }
    return result;
  }

  function normalizeUnknownDirectionCandidates(candidates, coinCount = null, allowNoCounterfeit = false) {
    const limit = Number(coinCount);
    const hasLimit = coinCount != null && Number.isInteger(limit);
    const seen = new Set();
    const result = [];
    for (const raw of candidates || []) {
      const rawCoin = raw === 'none' ? 0 : (raw?.coin === 'none' ? 0 : (raw?.coin ?? raw?.id ?? raw?.[0]));
      const coin = Number(rawCoin);
      const direction = normalizeDirection(raw?.direction ?? raw?.weight ?? raw?.[1]);
      if (coin === 0 && allowNoCounterfeit) {
        const key = '0:none';
        if (!seen.has(key)) {
          seen.add(key);
          result.push({ coin: 0, direction: 'none' });
        }
        continue;
      }
      if (!Number.isInteger(coin) || coin < 1 || !direction) continue;
      if (hasLimit && coin > limit) continue;
      const key = `${coin}:${direction}`;
      if (seen.has(key)) continue;
      seen.add(key);
      result.push({ coin, direction });
    }
    return result;
  }

  function knownDirectionCoinStatuses(candidates, coinCount, options = {}) {
    const count = Number(coinCount);
    if (!Number.isInteger(count) || count < 1) return {};
    const allowNoCounterfeit = options?.allowNoCounterfeit ?? options?.allow_no_counterfeit ?? false;
    const current = normalizeKnownDirectionCandidates(
      candidates?.length ? candidates : initialCandidates(count, allowNoCounterfeit),
      count,
      allowNoCounterfeit
    );
    const possible = new Set(current);
    const result = {};
    const possibleRealCoinFakes = current.filter(coin => coin > 0);
    for (let coin = 1; coin <= count; coin += 1) {
      if (!possible.has(coin)) result[coin] = 'genuine';
      else result[coin] = current.length === 1 && possibleRealCoinFakes.length === 1 ? 'definite_fake' : 'possible_fake';
    }
    return result;
  }

  function unknownDirectionCoinStatuses(candidates, coinCount) {
    const count = Number(coinCount);
    if (!Number.isInteger(count) || count < 1) return {};
    const allowNoCounterfeit = (candidates || []).some(candidate => Number(candidate?.coin ?? candidate) === 0);
    const current = normalizeUnknownDirectionCandidates(
      candidates?.length ? candidates : initialUnknownDirectionCandidates(count),
      count,
      allowNoCounterfeit
    );
    const directionsByCoin = new Map();
    for (const candidate of current) {
      if (!directionsByCoin.has(candidate.coin)) directionsByCoin.set(candidate.coin, new Set());
      directionsByCoin.get(candidate.coin).add(candidate.direction);
    }
    const result = {};
    for (let coin = 1; coin <= count; coin += 1) {
      const directions = directionsByCoin.get(coin) || new Set();
      const onlyThisCoin = current.length > 0 && current.every(candidate => candidate.coin === coin);
      const hasLighter = directions.has('lighter');
      const hasHeavier = directions.has('heavier');
      if (!directions.size) result[coin] = 'genuine';
      else if (hasLighter && hasHeavier) {
        result[coin] = onlyThisCoin ? 'definite_fake_unknown_direction' : 'possible_lighter_or_heavier';
      } else if (hasLighter) {
        result[coin] = onlyThisCoin ? 'definite_lighter' : 'possible_lighter';
      } else {
        result[coin] = onlyThisCoin ? 'definite_heavier' : 'possible_heavier';
      }
    }
    return result;
  }

  function normalizeWeight(counterfeitWeight) {
    const value = String(counterfeitWeight || '').toLowerCase();
    if (value === 'light' || value === 'lighter') return 'light';
    if (value === 'heavy' || value === 'heavier') return 'heavy';
    return null;
  }

  function outcomeForCandidate(candidate, counterfeitWeight, leftCoins, rightCoins) {
    if (Number(candidate) === 0) return 'balance';
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

  function unknownDirectionCandidateKey(candidate) {
    return `${candidate.coin}:${candidate.direction}`;
  }

  function sortedNumberSetKey(values) {
    return uniqueCoins(values).sort((a, b) => a - b).join(',');
  }

  function mirroredPanCoinPermutation(leftCoins, rightCoins, coinCount = null) {
    const left = uniqueCoins(leftCoins, coinCount).sort((a, b) => a - b);
    const right = uniqueCoins(rightCoins, coinCount).sort((a, b) => a - b);
    if (!left.length || left.length !== right.length) return null;
    const leftSet = new Set(left);
    if (right.some(coin => leftSet.has(coin))) return null;
    const permutation = new Map();
    for (let index = 0; index < left.length; index += 1) {
      permutation.set(left[index], right[index]);
      permutation.set(right[index], left[index]);
    }
    return permutation;
  }

  function permuteCoin(coin, permutation) {
    const normalized = Number(coin);
    return permutation?.get(normalized) ?? normalized;
  }

  function markSymmetricOutcomeChildren(children, options = {}) {
    const representativeOutcome = options.representativeOutcome || 'left_down';
    const coveredOutcome = options.coveredOutcome || 'right_down';
    const representative = children.find(child => child.outcome === representativeOutcome);
    const covered = children.find(child => child.outcome === coveredOutcome);
    if (!representative || !covered) return children;
    if (!representative.candidates.length || !covered.candidates.length) return children;
    const representativeKey = options.transformedCandidateSetKey
      ? options.transformedCandidateSetKey(representative.candidates)
      : null;
    const coveredKey = options.candidateSetKey?.(covered.candidates);
    if (representativeKey && coveredKey && representativeKey === coveredKey) {
      covered.status = 'covered';
      covered.coveredByOutcome = representative.outcome;
      covered.coveredByLabel = representative.label;
      covered.symmetryReason = options.reason || 'symmetry';
    }
    return children;
  }

  function unknownDirectionCandidateLabel(candidate) {
    const normalized = normalizeUnknownDirectionCandidates([candidate], null, true)[0];
    if (normalized?.coin === 0) return 'фальшивой монеты нет';
    return normalized ? `${normalized.coin} ${normalized.direction === 'lighter' ? 'легче' : 'тяжелее'}` : '';
  }

  function outcomeForUnknownDirectionCandidate(candidate, leftCoins, rightCoins, options = {}) {
    const allowNoCounterfeit = options.allowNoCounterfeit ?? options.allow_no_counterfeit ?? false;
    const normalized = normalizeUnknownDirectionCandidates([candidate], null, allowNoCounterfeit)[0];
    if (!normalized) return null;
    const leftList = uniqueCoins(leftCoins);
    const rightList = uniqueCoins(rightCoins);
    if (options.requireEqualPanCounts !== false && leftList.length !== rightList.length) return null;
    const left = new Set(leftList);
    const right = new Set(rightList);
    const onLeft = left.has(normalized.coin);
    const onRight = right.has(normalized.coin);
    if (onLeft && onRight) return null;
    let leftWeight = leftList.length;
    let rightWeight = rightList.length;
    if (normalized.coin > 0) {
      const delta = normalized.direction === 'heavier' ? 1 : -1;
      if (onLeft) leftWeight += delta;
      if (onRight) rightWeight += delta;
    }
    if (leftWeight > rightWeight) return 'left_down';
    if (rightWeight > leftWeight) return 'right_down';
    return 'balance';
  }

  function filterCandidates(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const allowNoCounterfeit = params?.allowNoCounterfeit ?? params?.allow_no_counterfeit ?? false;
    const currentCandidates = normalizeKnownDirectionCandidates(
      params?.currentCandidates?.length ? params.currentCandidates : initialCandidates(coinCount, allowNoCounterfeit),
      Number.isInteger(coinCount) ? coinCount : null,
      allowNoCounterfeit
    );
    const leftCoins = uniqueCoins(params?.leftCoins, Number.isInteger(coinCount) ? coinCount : null);
    const rightCoins = uniqueCoins(params?.rightCoins, Number.isInteger(coinCount) ? coinCount : null);
    const outcome = params?.outcome;
    return currentCandidates.filter(candidate =>
      outcomeForCandidate(candidate, params?.counterfeit_weight ?? params?.counterfeitWeight, leftCoins, rightCoins) === outcome
    );
  }

  function filterUnknownDirectionCandidates(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const allowNoCounterfeit = params?.allowNoCounterfeit ?? params?.allow_no_counterfeit ?? false;
    const currentCandidates = normalizeUnknownDirectionCandidates(
      params?.currentCandidates?.length ? params.currentCandidates : initialUnknownDirectionCandidates(coinCount, allowNoCounterfeit),
      Number.isInteger(coinCount) ? coinCount : null,
      allowNoCounterfeit
    );
    const leftCoins = uniqueCoins(params?.leftCoins);
    const rightCoins = uniqueCoins(params?.rightCoins);
    const outcome = params?.outcome;
    return currentCandidates.filter(candidate =>
      outcomeForUnknownDirectionCandidate(candidate, leftCoins, rightCoins, {
        requireEqualPanCounts: params?.requireEqualPanCounts ?? params?.require_equal_pan_counts,
        allowNoCounterfeit
      }) === outcome
    );
  }

  function partitionCandidates(params) {
    const partitions = Object.fromEntries(OUTCOMES.map(outcome => [outcome, filterCandidates({ ...params, outcome })]));
    return partitions;
  }

  function knownDirectionCandidateSetKey(candidates, coinCount = null, allowNoCounterfeit = false) {
    return normalizeKnownDirectionCandidates(candidates || [], coinCount, allowNoCounterfeit).sort((a, b) => a - b).join('|');
  }

  function permutedKnownDirectionCandidateSetKey(candidates, permutation, coinCount = null, allowNoCounterfeit = false) {
    return normalizeKnownDirectionCandidates(candidates || [], coinCount, allowNoCounterfeit)
      .map(coin => permuteCoin(coin, permutation))
      .sort((a, b) => a - b)
      .join('|');
  }

  function coinListIsWithinLimit(coins, coinCount) {
    const limit = Number(coinCount);
    if (!Number.isInteger(limit)) return false;
    return uniqueCoins(coins).every(coin => coin <= limit);
  }

  function partitionUnknownDirectionCandidates(params) {
    return Object.fromEntries(OUTCOMES.map(outcome => [outcome, filterUnknownDirectionCandidates({ ...params, outcome })]));
  }

  function sequentialCoinPairs(pairCount) {
    const count = Number(pairCount);
    if (!Number.isInteger(count) || count < 1) return [];
    return Array.from({ length: count }, (_item, index) => [index * 2 + 1, index * 2 + 2]);
  }

  function normalizeCoinPairs(pairs, pairCount = null) {
    const source = Array.isArray(pairs) && pairs.length ? pairs : sequentialCoinPairs(pairCount);
    const seen = new Set();
    const result = [];
    for (const rawPair of source || []) {
      const pair = uniqueCoins(rawPair);
      if (pair.length !== 2 || seen.has(pair[0]) || seen.has(pair[1])) return [];
      seen.add(pair[0]);
      seen.add(pair[1]);
      result.push(pair);
    }
    return result;
  }

  function initialPairedLightCandidates(pairsOrPairCount) {
    const pairs = Array.isArray(pairsOrPairCount)
      ? normalizeCoinPairs(pairsOrPairCount)
      : normalizeCoinPairs(null, pairsOrPairCount);
    if (!pairs.length) return [];
    const states = [[]];
    for (const pair of pairs) {
      const nextStates = [];
      for (const state of states) {
        nextStates.push([...state, pair[0]]);
        nextStates.push([...state, pair[1]]);
      }
      states.splice(0, states.length, ...nextStates);
    }
    return states.map(coins => ({ coins }));
  }

  function pairedLightStateKey(state) {
    return normalizePairedLightCandidates([state])[0]?.coins.join(',') || '';
  }

  function pairedLightCandidateSetKey(candidates, pairs = null) {
    return normalizePairedLightCandidates(candidates || [], pairs)
      .map(pairedLightStateKey)
      .sort()
      .join('|');
  }

  function permutedPairedLightCandidateSetKey(candidates, permutation, pairs = null) {
    return normalizePairedLightCandidates(candidates || [], pairs)
      .map(state => ({ coins: state.coins.map(coin => permuteCoin(coin, permutation)).sort((a, b) => a - b) }))
      .map(pairedLightStateKey)
      .sort()
      .join('|');
  }

  function coinPermutationPreservesPairs(permutation, pairs) {
    const normalizedPairs = normalizeCoinPairs(pairs);
    if (!normalizedPairs.length) return false;
    const pairKeys = new Set(normalizedPairs.map(pair => sortedNumberSetKey(pair)));
    const mappedKeys = new Set();
    for (const pair of normalizedPairs) {
      const mapped = pair.map(coin => permuteCoin(coin, permutation));
      const key = sortedNumberSetKey(mapped);
      if (!pairKeys.has(key) || mappedKeys.has(key)) return false;
      mappedKeys.add(key);
    }
    return mappedKeys.size === normalizedPairs.length;
  }

  function normalizePairedLightCandidates(candidates, pairs = null) {
    const normalizedPairs = pairs ? normalizeCoinPairs(pairs) : [];
    const pairByCoin = new Map();
    for (let index = 0; index < normalizedPairs.length; index += 1) {
      for (const coin of normalizedPairs[index]) pairByCoin.set(coin, index);
    }
    const seen = new Set();
    const result = [];
    for (const raw of candidates || []) {
      const coins = uniqueCoins(raw?.coins ?? raw?.state ?? raw);
      if (!coins.length) continue;
      if (normalizedPairs.length) {
        if (coins.length !== normalizedPairs.length) continue;
        const pairHits = new Set();
        let valid = true;
        for (const coin of coins) {
          const pairIndex = pairByCoin.get(coin);
          if (pairIndex == null || pairHits.has(pairIndex)) {
            valid = false;
            break;
          }
          pairHits.add(pairIndex);
        }
        if (!valid || pairHits.size !== normalizedPairs.length) continue;
      }
      const state = { coins: [...coins].sort((a, b) => a - b) };
      const key = state.coins.join(',');
      if (seen.has(key)) continue;
      seen.add(key);
      result.push(state);
    }
    return result;
  }

  function outcomeForPairedLightCandidate(candidate, leftCoins, rightCoins, options = {}) {
    const state = normalizePairedLightCandidates([candidate], options.pairs)[0];
    if (!state) return null;
    const leftList = uniqueCoins(leftCoins);
    const rightList = uniqueCoins(rightCoins);
    if (options.requireEqualPanCounts !== false && leftList.length !== rightList.length) return null;
    const left = new Set(leftList);
    const right = new Set(rightList);
    for (const coin of left) {
      if (right.has(coin)) return null;
    }
    const fakeCoins = new Set(state.coins);
    let leftFakes = 0;
    let rightFakes = 0;
    for (const coin of left) if (fakeCoins.has(coin)) leftFakes += 1;
    for (const coin of right) if (fakeCoins.has(coin)) rightFakes += 1;
    if (leftFakes > rightFakes) return 'right_down';
    if (rightFakes > leftFakes) return 'left_down';
    return 'balance';
  }

  function pairedLightCurrentCandidates(params) {
    const pairs = normalizeCoinPairs(params?.pairs ?? params?.coinPairs ?? params?.coin_pairs, params?.pairCount ?? params?.pair_count);
    const current = params?.currentCandidates ?? params?.current_candidates;
    return {
      pairs,
      candidates: current?.length
        ? normalizePairedLightCandidates(current, pairs)
        : initialPairedLightCandidates(pairs)
    };
  }

  function pairedLightFilterCandidates(params) {
    const { pairs, candidates } = pairedLightCurrentCandidates(params || {});
    const outcome = normalizeScaleOutcome(params?.outcome);
    if (!outcome) return [];
    return candidates.filter(candidate =>
      outcomeForPairedLightCandidate(
        candidate,
        params?.leftCoins ?? params?.left_coins,
        params?.rightCoins ?? params?.right_coins,
        {
          pairs,
          requireEqualPanCounts: params?.requireEqualPanCounts ?? params?.require_equal_pan_counts
        }
      ) === outcome
    );
  }

  function pairedLightPartitionCandidates(params) {
    return Object.fromEntries(OUTCOMES.map(outcome => [
      outcome,
      pairedLightFilterCandidates({ ...params, outcome })
    ]));
  }

  function pairedLightBranchStatus(candidates, usedWeighings, maxWeighings) {
    const remaining = normalizePairedLightCandidates(candidates);
    const used = Number(usedWeighings);
    const limit = Number(maxWeighings);
    if (remaining.length === 1) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function pairedLightChooseCheaterOutcome(params) {
    const partitions = pairedLightPartitionCandidates(params || {});
    const history = Array.isArray(params?.history) ? params.history : [];
    const maxSize = Math.max(...OUTCOMES.map(outcome => partitions[outcome].length));
    const tied = OUTCOMES.filter(outcome => partitions[outcome].length === maxSize);
    const frequencies = Object.fromEntries(OUTCOMES.map(outcome => [outcome, 0]));
    for (const entry of history) {
      const outcome = normalizeScaleOutcome(typeof entry === 'string' ? entry : entry?.outcome);
      if (outcome in frequencies) frequencies[outcome] += 1;
    }
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

  function pairedLightExpandExhaustiveNode(params) {
    const { pairs, candidates } = pairedLightCurrentCandidates(params || {});
    const usedWeighings = Number(params?.usedWeighings ?? params?.used_weighings ?? 0);
    const maxWeighings = Number(params?.maxWeighings ?? params?.max_weighings);
    const partitions = pairedLightPartitionCandidates({
      ...params,
      pairs,
      currentCandidates: candidates
    });
    const children = OUTCOMES
      .map(outcome => {
        const childCandidates = partitions[outcome];
        return {
          outcome,
          label: OUTCOME_LABELS[outcome],
          candidates: childCandidates,
          usedWeighings: usedWeighings + 1,
          status: pairedLightBranchStatus(childCandidates, usedWeighings + 1, maxWeighings)
        };
      })
      .filter(child => child.candidates.length > 0);
    const permutation = mirroredPanCoinPermutation(
      params?.leftCoins ?? params?.left_coins,
      params?.rightCoins ?? params?.right_coins
    );
    if (permutation && coinPermutationPreservesPairs(permutation, pairs)) {
      markSymmetricOutcomeChildren(children, {
        candidateSetKey: branchCandidates => pairedLightCandidateSetKey(branchCandidates, pairs),
        transformedCandidateSetKey: branchCandidates => permutedPairedLightCandidateSetKey(branchCandidates, permutation, pairs),
        reason: 'pan_mirror_pair_permutation'
      });
    }
    return { partitions, children };
  }

  function pairedLightFinalizeAnswer(params) {
    const { pairs, candidates } = pairedLightCurrentCandidates(params || {});
    const selectedCoins = uniqueCoins(params?.selectedCoins ?? params?.selected_coins);
    const selected = normalizePairedLightCandidates([{ coins: selectedCoins }], pairs)[0] ?? null;
    const selectedKey = selected ? pairedLightStateKey(selected) : null;
    if (candidates.length === 1) {
      const actualState = candidates[0];
      return {
        win: selectedKey === pairedLightStateKey(actualState),
        actualCoins: actualState.coins,
        actualState,
        candidates
      };
    }
    const actualState = candidates.find(candidate => pairedLightStateKey(candidate) !== selectedKey) ?? candidates[0] ?? null;
    return {
      win: false,
      actualCoins: actualState?.coins ?? [],
      actualState,
      candidates
    };
  }

  const ZERO_ONE_TWO_SIGN_ANSWERS = ['none', 'lighter', 'heavier'];

  function zeroOneTwoSignClassLabel(value) {
    const labels = {
      none: 'фальшивых нет',
      lighter: 'фальшивые есть и легче',
      heavier: 'фальшивые есть и тяжелее'
    };
    return labels[value] || String(value || '');
  }

  function zeroOneTwoSignInitialStates(coinCount) {
    const count = Number(coinCount);
    if (!Number.isInteger(count) || count < 1 || count > 24) return [];
    const states = [{ id: 'none', coins: [], sign: 'none', answer: 'none', label: zeroOneTwoSignClassLabel('none') }];
    for (const sign of ['lighter', 'heavier']) {
      for (let coin = 1; coin <= count; coin += 1) {
        states.push({
          id: `${sign}:${coin}`,
          coins: [coin],
          sign,
          answer: sign,
          label: `${coin} ${sign === 'lighter' ? 'легче' : 'тяжелее'}`
        });
      }
      for (let first = 1; first <= count; first += 1) {
        for (let second = first + 1; second <= count; second += 1) {
          states.push({
            id: `${sign}:${first},${second}`,
            coins: [first, second],
            sign,
            answer: sign,
            label: `${first}, ${second} ${sign === 'lighter' ? 'легче' : 'тяжелее'}`
          });
        }
      }
    }
    return states;
  }

  function zeroOneTwoSignStateKey(state) {
    if (state == null) return '';
    if (typeof state === 'string') return state;
    const sign = String(state.sign ?? state.answer ?? state.direction ?? '').toLowerCase();
    if (sign === 'none') return 'none';
    const normalizedSign = normalizeDirection(sign);
    if (!normalizedSign) return '';
    const coins = uniqueCoins(state.coins ?? state.fakeCoins ?? state.fake_coins ?? state.state ?? [])
      .sort((a, b) => a - b);
    if (coins.length < 1 || coins.length > 2) return '';
    return `${normalizedSign}:${coins.join(',')}`;
  }

  function zeroOneTwoSignNormalizeStates(states, coinCount) {
    const allowed = new Map(zeroOneTwoSignInitialStates(coinCount).map(state => [state.id, state]));
    const seen = new Set();
    const result = [];
    for (const raw of states || []) {
      const key = zeroOneTwoSignStateKey(raw);
      if (!allowed.has(key) || seen.has(key)) continue;
      seen.add(key);
      result.push(allowed.get(key));
    }
    return result;
  }

  function zeroOneTwoSignCurrentStates(params = {}) {
    const coinCount = Number(params.coinCount ?? params.coin_count);
    const current = params.currentStates ?? params.current_states ?? params.currentCandidates ?? params.current_candidates;
    return current?.length
      ? zeroOneTwoSignNormalizeStates(current, coinCount)
      : zeroOneTwoSignInitialStates(coinCount);
  }

  function zeroOneTwoSignAnswerClasses(states) {
    return [...new Set((states || []).map(state => state.answer || state.sign).filter(Boolean))]
      .sort((a, b) => ZERO_ONE_TWO_SIGN_ANSWERS.indexOf(a) - ZERO_ONE_TWO_SIGN_ANSWERS.indexOf(b));
  }

  function zeroOneTwoSignCoinStatuses(states, coinCount) {
    const count = Number(coinCount);
    if (!Number.isInteger(count) || count < 1) return {};
    const normalized = states?.length ? zeroOneTwoSignNormalizeStates(states, count) : zeroOneTwoSignInitialStates(count);
    const possible = Object.fromEntries(initialCandidates(count).map(coin => [coin, 0]));
    const totalFakeStates = normalized.filter(state => state.sign !== 'none').length;
    for (const state of normalized) {
      for (const coin of state.coins || []) possible[coin] += 1;
    }
    const result = {};
    for (let coin = 1; coin <= count; coin += 1) {
      if (!possible[coin]) result[coin] = 'genuine';
      else if (totalFakeStates > 0 && possible[coin] === totalFakeStates) result[coin] = 'definite_fake_unknown_direction';
      else result[coin] = 'possible_fake';
    }
    return result;
  }

  function zeroOneTwoSignOutcomeForState(state, params = {}) {
    const coinCount = Number(params.coinCount ?? params.coin_count);
    const normalized = zeroOneTwoSignNormalizeStates([state], coinCount)[0];
    if (!normalized) return null;
    const leftList = uniqueCoins(params.leftCoins ?? params.left_coins, Number.isInteger(coinCount) ? coinCount : null);
    const rightList = uniqueCoins(params.rightCoins ?? params.right_coins, Number.isInteger(coinCount) ? coinCount : null);
    if (params.requireEqualPanCounts !== false && params.require_equal_pan_counts !== false && leftList.length !== rightList.length) return null;
    const left = new Set(leftList);
    const right = new Set(rightList);
    for (const coin of left) {
      if (right.has(coin)) return null;
    }
    let leftWeight = leftList.length;
    let rightWeight = rightList.length;
    if (normalized.sign !== 'none') {
      const delta = normalized.sign === 'heavier' ? 1 : -1;
      for (const coin of normalized.coins) {
        if (left.has(coin)) leftWeight += delta;
        if (right.has(coin)) rightWeight += delta;
      }
    }
    if (leftWeight > rightWeight) return 'left_down';
    if (rightWeight > leftWeight) return 'right_down';
    return 'balance';
  }

  function zeroOneTwoSignPartitionStates(params = {}) {
    const states = zeroOneTwoSignCurrentStates(params);
    const partitions = Object.fromEntries(OUTCOMES.map(outcome => [outcome, []]));
    for (const state of states) {
      const outcome = zeroOneTwoSignOutcomeForState(state, params);
      if (outcome) partitions[outcome].push(state);
    }
    return OUTCOMES.map(outcome => ({
      outcome,
      label: OUTCOME_LABELS[outcome],
      states: partitions[outcome],
      candidates: partitions[outcome],
      answerClasses: zeroOneTwoSignAnswerClasses(partitions[outcome])
    }));
  }

  function zeroOneTwoSignFilterStates(params = {}) {
    const outcome = normalizeScaleOutcome(params.outcome);
    if (!outcome) return [];
    return zeroOneTwoSignPartitionStates(params).find(part => part.outcome === outcome)?.states || [];
  }

  function zeroOneTwoSignBranchStatus(states, usedWeighings, maxWeighings) {
    const remaining = states || [];
    const used = Number(usedWeighings);
    const limit = Number(maxWeighings);
    if (zeroOneTwoSignAnswerClasses(remaining).length === 1) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function zeroOneTwoSignChooseCheaterOutcome(params = {}) {
    const partitions = zeroOneTwoSignPartitionStates(params);
    const history = Array.isArray(params.history) ? params.history : [];
    const scores = Object.fromEntries(partitions.map(part => [part.outcome, {
      states: part.states.length,
      answerClasses: part.answerClasses.length
    }]));
    const frequencies = Object.fromEntries(OUTCOMES.map(outcome => [outcome, 0]));
    for (const entry of history) {
      const outcome = normalizeScaleOutcome(typeof entry === 'string' ? entry : entry?.outcome);
      if (outcome in frequencies) frequencies[outcome] += 1;
    }
    const chosen = partitions
      .filter(part => part.states.length > 0)
      .sort((a, b) =>
        scores[b.outcome].answerClasses - scores[a.outcome].answerClasses ||
        scores[b.outcome].states - scores[a.outcome].states ||
        frequencies[a.outcome] - frequencies[b.outcome] ||
        OUTCOMES.indexOf(a.outcome) - OUTCOMES.indexOf(b.outcome)
      )[0] || partitions.find(part => part.outcome === 'balance');
    return {
      outcome: chosen.outcome,
      label: chosen.label,
      states: chosen.states,
      candidates: chosen.states,
      answerClasses: chosen.answerClasses,
      partitions,
      scores
    };
  }

  function zeroOneTwoSignExpandExhaustiveNode(params = {}) {
    const usedWeighings = Number(params.usedWeighings ?? params.used_weighings ?? 0);
    const maxWeighings = Number(params.maxWeighings ?? params.max_weighings ?? 1);
    const partitions = zeroOneTwoSignPartitionStates(params);
    const children = partitions
      .filter(part => part.states.length > 0)
      .map(part => ({
        outcome: part.outcome,
        label: part.label,
        states: part.states,
        candidates: part.states,
        answerClasses: part.answerClasses,
        usedWeighings: usedWeighings + 1,
        status: zeroOneTwoSignBranchStatus(part.states, usedWeighings + 1, maxWeighings)
      }));
    return { partitions, children };
  }

  function zeroOneTwoSignFinalizeAnswer(params = {}) {
    const states = zeroOneTwoSignCurrentStates(params);
    const selectedClass = String(params.selectedClass ?? params.selected_class ?? params.answer ?? '').toLowerCase();
    const classes = zeroOneTwoSignAnswerClasses(states);
    const actualClass = classes.length === 1
      ? classes[0]
      : (classes.find(item => item !== selectedClass) ?? classes[0] ?? null);
    return {
      win: classes.length === 1 && selectedClass === actualClass,
      actualClass,
      answerClasses: classes,
      states,
      candidates: states
    };
  }

  function initialMultipleLightCandidates(coinCount, lightCount = 2) {
    const coins = initialCandidates(coinCount);
    const count = Number(lightCount);
    if (!Number.isInteger(count) || count < 1 || count > coins.length) return [];
    const result = [];
    function visit(start, picked) {
      if (picked.length === count) {
        result.push({ coins: [...picked] });
        return;
      }
      for (let index = start; index <= coins.length - (count - picked.length); index += 1) {
        picked.push(coins[index]);
        visit(index + 1, picked);
        picked.pop();
      }
    }
    visit(0, []);
    return result;
  }

  function normalizeGroupConstraints(rawGroups, rawCounts, coinCount = null) {
    const limit = Number(coinCount);
    const hasLimit = coinCount != null && Number.isInteger(limit);
    if (!Array.isArray(rawGroups) || !rawGroups.length) return null;
    const groups = [];
    const seen = new Set();
    for (const rawGroup of rawGroups) {
      const group = uniqueCoins(rawGroup, hasLimit ? limit : null).sort((a, b) => a - b);
      if (!group.length) return null;
      for (const coin of group) {
        if (seen.has(coin)) return null;
        seen.add(coin);
      }
      groups.push(group);
    }
    const counts = Array.isArray(rawCounts) && rawCounts.length
      ? rawCounts.map(Number)
      : groups.map(() => 1);
    if (counts.length !== groups.length) return null;
    for (let index = 0; index < counts.length; index += 1) {
      const count = counts[index];
      if (!Number.isInteger(count) || count < 0 || count > groups[index].length) return null;
    }
    return { groups, counts };
  }

  function groupConstraintsFromParams(params = {}) {
    return normalizeGroupConstraints(
      params?.groups ?? params?.stateGroups ?? params?.state_groups,
      params?.counterfeitPerGroup ?? params?.counterfeit_per_group ?? params?.groupLightCounts ?? params?.group_light_counts,
      params?.coinCount ?? params?.coin_count
    );
  }

  function stateMatchesGroupConstraints(state, constraints) {
    if (!constraints) return true;
    const fakeCoins = new Set(state?.coins || []);
    let total = 0;
    for (let index = 0; index < constraints.groups.length; index += 1) {
      const count = constraints.groups[index].filter(coin => fakeCoins.has(coin)).length;
      if (count !== constraints.counts[index]) return false;
      total += count;
    }
    return total === fakeCoins.size;
  }

  function initialGroupedMultipleLightCandidates(coinCount, groups, counterfeitPerGroup) {
    const constraints = normalizeGroupConstraints(groups, counterfeitPerGroup, coinCount);
    if (!constraints) return [];
    const result = [];
    function visitGroup(groupIndex, picked) {
      if (groupIndex === constraints.groups.length) {
        result.push({ coins: [...picked].sort((a, b) => a - b) });
        return;
      }
      const group = constraints.groups[groupIndex];
      const count = constraints.counts[groupIndex];
      function visitCoin(start, localPicked) {
        if (localPicked.length === count) {
          visitGroup(groupIndex + 1, [...picked, ...localPicked]);
          return;
        }
        for (let index = start; index <= group.length - (count - localPicked.length); index += 1) {
          localPicked.push(group[index]);
          visitCoin(index + 1, localPicked);
          localPicked.pop();
        }
      }
      visitCoin(0, []);
    }
    visitGroup(0, []);
    return result;
  }

  function normalizeMultipleLightCandidates(candidates, coinCount = null, lightCount = null) {
    const limit = Number(coinCount);
    const hasLimit = coinCount != null && Number.isInteger(limit);
    const requiredCount = Number(lightCount);
    const hasRequiredCount = lightCount != null && Number.isInteger(requiredCount);
    const seen = new Set();
    const result = [];
    for (const raw of candidates || []) {
      const coins = uniqueCoins(raw?.coins ?? raw?.state ?? raw, hasLimit ? limit : null).sort((a, b) => a - b);
      if (!coins.length || (hasRequiredCount && coins.length !== requiredCount)) continue;
      const key = coins.join(',');
      if (seen.has(key)) continue;
      seen.add(key);
      result.push({ coins });
    }
    return result;
  }

  function groupKey(group) {
    return sortedNumberSetKey(group);
  }

  function coinPermutationPreservesGroupConstraints(permutation, constraints) {
    if (!constraints) return true;
    const groups = constraints.groups || [];
    const counts = constraints.counts || [];
    if (!groups.length || groups.length !== counts.length) return false;
    const targetCountsByGroup = new Map(groups.map((group, index) => [groupKey(group), counts[index]]));
    const mappedKeys = new Set();
    for (let index = 0; index < groups.length; index += 1) {
      const mappedKey = groupKey(groups[index].map(coin => permuteCoin(coin, permutation)));
      if (mappedKeys.has(mappedKey)) return false;
      if (targetCountsByGroup.get(mappedKey) !== counts[index]) return false;
      mappedKeys.add(mappedKey);
    }
    return mappedKeys.size === groups.length;
  }

  function lightCoinSetStatuses(candidates, coinCount, options = {}) {
    const count = Number(coinCount);
    if (!Number.isInteger(count) || count < 1) return {};
    const lightCount = options.lightCount ?? options.light_count ?? null;
    const current = normalizeMultipleLightCandidates(
      candidates?.length ? candidates : initialMultipleLightCandidates(count, lightCount ?? 1),
      count,
      lightCount
    );
    const stateCount = current.length;
    const hits = Object.fromEntries(initialCandidates(count).map(coin => [coin, 0]));
    for (const state of current) {
      const fakeCoins = new Set(state.coins || []);
      for (let coin = 1; coin <= count; coin += 1) {
        if (fakeCoins.has(coin)) hits[coin] += 1;
      }
    }
    const result = {};
    for (let coin = 1; coin <= count; coin += 1) {
      if (!hits[coin]) result[coin] = 'genuine';
      else result[coin] = hits[coin] === stateCount ? 'definite_fake' : 'possible_fake';
    }
    return result;
  }

  function pairedLightCoinStatuses(candidates, pairsOrPairCount) {
    const pairs = Array.isArray(pairsOrPairCount)
      ? normalizeCoinPairs(pairsOrPairCount)
      : normalizeCoinPairs(null, pairsOrPairCount);
    const coinCount = pairs.flat().reduce((max, coin) => Math.max(max, coin), 0);
    if (!coinCount) return {};
    const current = normalizePairedLightCandidates(
      candidates?.length ? candidates : initialPairedLightCandidates(pairs),
      pairs
    );
    return lightCoinSetStatuses(current, coinCount);
  }

  function multipleLightStateKey(state) {
    return normalizeMultipleLightCandidates([state])[0]?.coins.join(',') || '';
  }

  function multipleLightCandidateSetKey(candidates, coinCount = null, lightCount = null) {
    return normalizeMultipleLightCandidates(candidates || [], coinCount, lightCount)
      .map(multipleLightStateKey)
      .sort()
      .join('|');
  }

  function permutedMultipleLightCandidateSetKey(candidates, permutation, coinCount = null, lightCount = null) {
    return normalizeMultipleLightCandidates(candidates || [], coinCount, lightCount)
      .map(state => ({ coins: state.coins.map(coin => permuteCoin(coin, permutation)).sort((a, b) => a - b) }))
      .map(multipleLightStateKey)
      .sort()
      .join('|');
  }

  function multipleLightCurrentCandidates(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const lightCount = Number(params?.light_count ?? params?.lightCount ?? params?.counterfeit_count ?? params?.counterfeitCount ?? 2);
    const current = params?.currentCandidates ?? params?.current_candidates;
    const groupConstraints = groupConstraintsFromParams({ ...params, coinCount });
    return {
      coinCount,
      lightCount,
      groupConstraints,
      candidates: current?.length
        ? normalizeMultipleLightCandidates(current, Number.isInteger(coinCount) ? coinCount : null, Number.isInteger(lightCount) ? lightCount : null)
          .filter(candidate => stateMatchesGroupConstraints(candidate, groupConstraints))
        : (groupConstraints
          ? initialGroupedMultipleLightCandidates(coinCount, groupConstraints.groups, groupConstraints.counts)
          : initialMultipleLightCandidates(coinCount, lightCount))
    };
  }

  function outcomeForMultipleLightCandidate(candidate, leftCoins, rightCoins, options = {}) {
    const state = normalizeMultipleLightCandidates([candidate], options.coinCount ?? options.coin_count, options.lightCount ?? options.light_count)[0];
    if (!state) return null;
    const leftList = uniqueCoins(leftCoins, options.coinCount ?? options.coin_count ?? null);
    const rightList = uniqueCoins(rightCoins, options.coinCount ?? options.coin_count ?? null);
    if (options.requireEqualPanCounts !== false && leftList.length !== rightList.length) return null;
    const left = new Set(leftList);
    const right = new Set(rightList);
    for (const coin of left) {
      if (right.has(coin)) return null;
    }
    const fakeCoins = new Set(state.coins);
    let leftWeight = leftList.length;
    let rightWeight = rightList.length;
    for (const coin of left) if (fakeCoins.has(coin)) leftWeight -= 1;
    for (const coin of right) if (fakeCoins.has(coin)) rightWeight -= 1;
    if (leftWeight > rightWeight) return 'left_down';
    if (rightWeight > leftWeight) return 'right_down';
    return 'balance';
  }

  function multipleLightFilterCandidates(params) {
    const { coinCount, lightCount, candidates } = multipleLightCurrentCandidates(params || {});
    const outcome = normalizeScaleOutcome(params?.outcome);
    if (!outcome) return [];
    return candidates.filter(candidate =>
      outcomeForMultipleLightCandidate(
        candidate,
        params?.leftCoins ?? params?.left_coins,
        params?.rightCoins ?? params?.right_coins,
        {
          coinCount,
          lightCount,
          requireEqualPanCounts: params?.requireEqualPanCounts ?? params?.require_equal_pan_counts
        }
      ) === outcome
    );
  }

  function multipleLightPartitionCandidates(params) {
    return Object.fromEntries(OUTCOMES.map(outcome => [
      outcome,
      multipleLightFilterCandidates({ ...params, outcome })
    ]));
  }

  function commonLightCoins(candidates) {
    const states = normalizeMultipleLightCandidates(candidates);
    if (!states.length) return [];
    let common = new Set(states[0].coins);
    for (const state of states.slice(1)) {
      const coins = new Set(state.coins);
      common = new Set([...common].filter(coin => coins.has(coin)));
    }
    return [...common].sort((a, b) => a - b);
  }

  function possibleLightCoins(candidates) {
    const result = new Set();
    for (const state of normalizeMultipleLightCandidates(candidates)) {
      for (const coin of state.coins) result.add(coin);
    }
    return [...result].sort((a, b) => a - b);
  }

  function uniqueLightState(candidates) {
    const states = normalizeMultipleLightCandidates(candidates);
    if (!states.length) return null;
    const key = multipleLightStateKey(states[0]);
    return states.every(state => multipleLightStateKey(state) === key) ? states[0] : null;
  }

  function multipleLightBranchStatus(candidates, usedWeighings, maxWeighings) {
    const remaining = normalizeMultipleLightCandidates(candidates);
    const used = Number(usedWeighings);
    const limit = Number(maxWeighings);
    const objective = typeof arguments[3] === 'string' ? arguments[3] : arguments[3]?.objective;
    if (objective === 'identify_all_counterfeits') {
      if (uniqueLightState(remaining)) return 'solved';
      if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
      return 'open';
    }
    if (commonLightCoins(remaining).length > 0) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function multipleLightChooseCheaterOutcome(params) {
    const partitions = multipleLightPartitionCandidates(params || {});
    const history = Array.isArray(params?.history) ? params.history : [];
    const objective = params?.objective;
    const scores = Object.fromEntries(OUTCOMES.map(outcome => {
      const candidates = partitions[outcome];
      return [outcome, {
        states: candidates.length,
        pairs: new Set(candidates.map(multipleLightStateKey)).size,
        possibleLightCoins: possibleLightCoins(candidates).length,
        guaranteedLightCoins: commonLightCoins(candidates).length
      }];
    }));
    const frequencies = Object.fromEntries(OUTCOMES.map(outcome => [outcome, 0]));
    for (const entry of history) {
      const outcome = normalizeScaleOutcome(typeof entry === 'string' ? entry : entry?.outcome);
      if (outcome in frequencies) frequencies[outcome] += 1;
    }
    const outcome = OUTCOMES
      .filter(item => partitions[item].length > 0)
      .sort((a, b) => {
        if (objective === 'identify_all_counterfeits') {
          return scores[b].pairs - scores[a].pairs
            || scores[b].states - scores[a].states
            || frequencies[a] - frequencies[b]
            || OUTCOMES.indexOf(a) - OUTCOMES.indexOf(b);
        }
        const aSolved = scores[a].guaranteedLightCoins > 0 ? 1 : 0;
        const bSolved = scores[b].guaranteedLightCoins > 0 ? 1 : 0;
        return aSolved - bSolved
          || scores[b].possibleLightCoins - scores[a].possibleLightCoins
          || scores[b].states - scores[a].states
          || frequencies[a] - frequencies[b]
          || OUTCOMES.indexOf(a) - OUTCOMES.indexOf(b);
      })[0] || 'balance';
    return {
      outcome,
      label: OUTCOME_LABELS[outcome],
      candidates: partitions[outcome],
      partitions,
      scores
    };
  }

  function multipleLightExpandExhaustiveNode(params) {
    const { coinCount, lightCount, groupConstraints, candidates } = multipleLightCurrentCandidates(params || {});
    const usedWeighings = Number(params?.usedWeighings ?? params?.used_weighings ?? 0);
    const maxWeighings = Number(params?.maxWeighings ?? params?.max_weighings);
    const objective = params?.objective;
    const partitions = multipleLightPartitionCandidates({
      ...params,
      coinCount,
      lightCount,
      currentCandidates: candidates
    });
    const children = OUTCOMES
      .map(outcome => {
        const childCandidates = partitions[outcome];
        return {
          outcome,
          label: OUTCOME_LABELS[outcome],
          candidates: childCandidates,
          guaranteedCoins: commonLightCoins(childCandidates),
          solvedState: uniqueLightState(childCandidates),
          possibleCoins: possibleLightCoins(childCandidates),
          usedWeighings: usedWeighings + 1,
          status: multipleLightBranchStatus(childCandidates, usedWeighings + 1, maxWeighings, objective)
        };
      })
      .filter(child => child.candidates.length > 0);
    const permutation = mirroredPanCoinPermutation(
      params?.leftCoins ?? params?.left_coins,
      params?.rightCoins ?? params?.right_coins,
      Number.isInteger(coinCount) ? coinCount : null
    );
    if (permutation && coinPermutationPreservesGroupConstraints(permutation, groupConstraints)) {
      markSymmetricOutcomeChildren(children, {
        candidateSetKey: branchCandidates => multipleLightCandidateSetKey(branchCandidates, coinCount, lightCount),
        transformedCandidateSetKey: branchCandidates => permutedMultipleLightCandidateSetKey(branchCandidates, permutation, coinCount, lightCount),
        reason: groupConstraints ? 'pan_mirror_group_permutation' : 'pan_mirror_coin_permutation'
      });
    }
    return { partitions, children };
  }

  function multipleLightFinalizeAnswer(params) {
    const { candidates } = multipleLightCurrentCandidates(params || {});
    const objective = params?.objective;
    if (objective === 'identify_all_counterfeits') {
      const selected = normalizeMultipleLightCandidates([params?.selectedCoins ?? params?.selected_coins], null, null)[0] ?? null;
      const selectedKey = selected ? multipleLightStateKey(selected) : null;
      const solvedState = uniqueLightState(candidates);
      if (solvedState) {
        return {
          win: selectedKey === multipleLightStateKey(solvedState),
          actualCoins: solvedState.coins,
          actualState: solvedState,
          candidates,
          solvedState
        };
      }
      const actualState = candidates.find(candidate => multipleLightStateKey(candidate) !== selectedKey) ?? candidates[0] ?? null;
      return { win: false, actualCoins: actualState?.coins ?? [], actualState, candidates, solvedState: null };
    }
    const selectedCoin = Number(params?.selectedCoin ?? params?.selected_coin);
    const guaranteedCoins = commonLightCoins(candidates);
    if (guaranteedCoins.includes(selectedCoin)) {
      const actualState = candidates.find(state => state.coins.includes(selectedCoin)) ?? candidates[0] ?? null;
      return { win: true, actualCoins: actualState?.coins ?? [], actualState, candidates, guaranteedCoins };
    }
    const actualState = candidates.find(state => !state.coins.includes(selectedCoin)) ?? candidates[0] ?? null;
    return { win: false, actualCoins: actualState?.coins ?? [], actualState, candidates, guaranteedCoins };
  }

  function thresholdBalanceInitialStates(coinCount, counterfeitCount) {
    return initialMultipleLightCandidates(coinCount, counterfeitCount);
  }

  function thresholdBalanceCurrentStates(params = {}) {
    const coinCount = Number(params.coin_count ?? params.coinCount);
    const counterfeitCount = Number(params.counterfeit_count ?? params.counterfeitCount ?? params.light_count ?? params.lightCount);
    const current = params.currentStates ?? params.current_states ?? params.currentCandidates ?? params.current_candidates;
    return {
      coinCount,
      counterfeitCount,
      states: current?.length
        ? normalizeMultipleLightCandidates(
            current,
            Number.isInteger(coinCount) ? coinCount : null,
            Number.isInteger(counterfeitCount) ? counterfeitCount : null
          )
        : thresholdBalanceInitialStates(coinCount, counterfeitCount)
    };
  }

  function thresholdBalanceStateKey(state) {
    return multipleLightStateKey(state);
  }

  function thresholdBalanceStateLabel(state) {
    const key = thresholdBalanceStateKey(state);
    return key ? `{${key}}` : '?';
  }

  function normalizeThresholdBalanceOutcome(outcome) {
    const value = String(outcome || '').toLowerCase();
    if (value === 'left_light' || value === 'left_lighter' || value === 'left_reliably_lighter') return 'left_reliable_lighter';
    if (value === 'right_light' || value === 'right_lighter' || value === 'right_reliably_lighter') return 'right_reliable_lighter';
    if (value === 'no_tilt' || value === 'uncertain' || value === 'balance' || value === 'balanced') return 'no_reliable_tilt';
    return THRESHOLD_BALANCE_OUTCOMES.includes(value) ? value : null;
  }

  function thresholdBalanceWeights(params = {}) {
    const genuineWeight = Number(params.genuine_weight ?? params.genuineWeight ?? 10);
    const counterfeitDelta = Number(params.counterfeit_delta ?? params.counterfeitDelta ?? 1);
    const reliableDifference = Number(params.reliable_difference ?? params.reliableDifference ?? params.tilt_threshold ?? params.tiltThreshold ?? 2);
    const counterfeitWeight = normalizeWeight(params.counterfeit_weight ?? params.counterfeitWeight ?? 'lighter') || 'light';
    const fakeWeight = counterfeitWeight === 'heavy'
      ? genuineWeight + counterfeitDelta
      : genuineWeight - counterfeitDelta;
    return { genuineWeight, fakeWeight, reliableDifference };
  }

  function outcomeForThresholdBalanceState(state, leftCoins, rightCoins, options = {}) {
    const coinCount = options.coinCount ?? options.coin_count ?? null;
    const normalized = normalizeMultipleLightCandidates(
      [state],
      coinCount,
      options.counterfeitCount ?? options.counterfeit_count
    )[0];
    if (!normalized) return null;
    const leftList = uniqueCoins(leftCoins, coinCount);
    const rightList = uniqueCoins(rightCoins, coinCount);
    if (options.requireEqualPanCounts !== false && leftList.length !== rightList.length) return null;
    const right = new Set(rightList);
    for (const coin of leftList) if (right.has(coin)) return null;
    const fakeCoins = new Set(normalized.coins);
    const { genuineWeight, fakeWeight, reliableDifference } = thresholdBalanceWeights(options);
    const sideWeight = coins => coins.reduce((sum, coin) => sum + (fakeCoins.has(coin) ? fakeWeight : genuineWeight), 0);
    const difference = sideWeight(leftList) - sideWeight(rightList);
    if (difference <= -reliableDifference) return 'left_reliable_lighter';
    if (difference >= reliableDifference) return 'right_reliable_lighter';
    return 'no_reliable_tilt';
  }

  function thresholdBalanceFilterStates(params = {}) {
    const outcome = normalizeThresholdBalanceOutcome(params.outcome);
    if (!outcome) return [];
    const { coinCount, counterfeitCount, states } = thresholdBalanceCurrentStates(params);
    return states.filter(state =>
      outcomeForThresholdBalanceState(
        state,
        params.leftCoins ?? params.left_coins,
        params.rightCoins ?? params.right_coins,
        {
          coinCount,
          counterfeitCount,
          genuineWeight: params.genuineWeight ?? params.genuine_weight,
          counterfeitDelta: params.counterfeitDelta ?? params.counterfeit_delta,
          reliableDifference: params.reliableDifference ?? params.reliable_difference,
          counterfeitWeight: params.counterfeitWeight ?? params.counterfeit_weight,
          requireEqualPanCounts: params.requireEqualPanCounts ?? params.require_equal_pan_counts
        }
      ) === outcome
    );
  }

  function thresholdBalancePartitionStates(params = {}) {
    return Object.fromEntries(THRESHOLD_BALANCE_OUTCOMES.map(outcome => [
      outcome,
      thresholdBalanceFilterStates({ ...params, outcome })
    ]));
  }

  function thresholdBalanceUniqueState(states) {
    return uniqueLightState(states);
  }

  function thresholdBalanceObjectiveSolved(states, objective = 'identify_all_counterfeits') {
    const current = normalizeMultipleLightCandidates(states);
    if (!current.length) return false;
    if (objective === 'identify_all_counterfeits' || objective === 'identify_fake_coin_set') {
      return Boolean(thresholdBalanceUniqueState(current));
    }
    return false;
  }

  function thresholdBalanceAnswerOptionsForStates(states, objective = 'identify_all_counterfeits') {
    const current = normalizeMultipleLightCandidates(states);
    if (objective !== 'identify_all_counterfeits' && objective !== 'identify_fake_coin_set') return [];
    return current.map(state => ({
      kind: 'state',
      value: thresholdBalanceStateKey(state),
      label: thresholdBalanceStateLabel(state),
      coins: [...state.coins]
    }));
  }

  function thresholdBalanceBranchStatus(states, usedWeighings, maxWeighings, objective = 'identify_all_counterfeits') {
    const current = normalizeMultipleLightCandidates(states);
    const used = Number(usedWeighings);
    const limit = Number(maxWeighings);
    if (thresholdBalanceObjectiveSolved(current, objective)) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function thresholdBalanceChooseCheaterOutcome(params = {}) {
    const objective = params.objective || 'identify_all_counterfeits';
    const partitions = thresholdBalancePartitionStates(params);
    const history = Array.isArray(params.history) ? params.history : [];
    const frequencies = Object.fromEntries(THRESHOLD_BALANCE_OUTCOMES.map(outcome => [outcome, 0]));
    for (const entry of history) {
      const outcome = normalizeThresholdBalanceOutcome(typeof entry === 'string' ? entry : entry?.outcome);
      if (outcome in frequencies) frequencies[outcome] += 1;
    }
    const scores = Object.fromEntries(THRESHOLD_BALANCE_OUTCOMES.map(outcome => {
      const states = partitions[outcome];
      return [outcome, {
        states: states.length,
        solved: thresholdBalanceObjectiveSolved(states, objective) ? 1 : 0,
        answerOptions: thresholdBalanceAnswerOptionsForStates(states, objective).length
      }];
    }));
    const outcome = THRESHOLD_BALANCE_OUTCOMES
      .filter(item => partitions[item].length > 0)
      .sort((a, b) =>
        scores[b].states - scores[a].states
        || scores[a].solved - scores[b].solved
        || scores[b].answerOptions - scores[a].answerOptions
        || frequencies[a] - frequencies[b]
        || THRESHOLD_BALANCE_OUTCOMES.indexOf(a) - THRESHOLD_BALANCE_OUTCOMES.indexOf(b)
      )[0] || 'no_reliable_tilt';
    return {
      outcome,
      label: THRESHOLD_BALANCE_LABELS[outcome],
      states: partitions[outcome],
      candidates: partitions[outcome],
      partitions,
      scores
    };
  }

  function thresholdBalanceExpandExhaustiveNode(params = {}) {
    const usedWeighings = Number(params.usedWeighings ?? params.used_weighings ?? 0);
    const maxWeighings = Number(params.maxWeighings ?? params.max_weighings);
    const objective = params.objective || 'identify_all_counterfeits';
    const partitions = thresholdBalancePartitionStates(params);
    const children = THRESHOLD_BALANCE_OUTCOMES
      .map(outcome => {
        const states = partitions[outcome];
        return {
          outcome,
          label: THRESHOLD_BALANCE_LABELS[outcome],
          states,
          candidates: states,
          usedWeighings: usedWeighings + 1,
          status: thresholdBalanceBranchStatus(states, usedWeighings + 1, maxWeighings, objective),
          answerOptions: thresholdBalanceAnswerOptionsForStates(states, objective)
        };
      })
      .filter(child => child.states.length > 0);
    return { partitions, children };
  }

  function thresholdBalanceFinalizeAnswer(params = {}) {
    const { states } = thresholdBalanceCurrentStates(params);
    const selectedCoins = uniqueCoins(params.selectedCoins ?? params.selected_coins, params.coin_count ?? params.coinCount ?? null);
    const selectedKey = selectedCoins.join(',');
    const solvedState = thresholdBalanceUniqueState(states);
    if (solvedState) {
      return {
        win: selectedKey === thresholdBalanceStateKey(solvedState),
        actualState: solvedState,
        actualCoins: solvedState.coins,
        states,
        candidates: states,
        solvedState
      };
    }
    const actualState = states.find(state => thresholdBalanceStateKey(state) !== selectedKey) ?? states[0] ?? null;
    return { win: false, actualState, actualCoins: actualState?.coins ?? [], states, candidates: states, solvedState: null };
  }

  function constrainedLightNormalizeState(raw, coinCount = null, index = 0) {
    const count = Number(coinCount);
    const hasLimit = Number.isInteger(count) && count > 0;
    const coins = uniqueCoins(
      Array.isArray(raw) ? raw : (raw?.coins ?? raw?.fakeCoins ?? raw?.fake_coins ?? []),
      hasLimit ? count : null
    );
    if (!coins.length) return null;
    const id = String(raw?.id ?? raw?.key ?? raw?.name ?? raw?.label ?? `s${index + 1}`);
    const label = String(raw?.label ?? raw?.name ?? id);
    return { id, label, coins };
  }

  function constrainedLightInitialStates(params = {}) {
    const coinCount = Number(params.coin_count ?? params.coinCount);
    const rawStates = params.hidden_states ?? params.hiddenStates ?? params.states ?? [];
    const states = [];
    const seen = new Set();
    if (!Array.isArray(rawStates)) return states;
    rawStates.forEach((raw, index) => {
      const state = constrainedLightNormalizeState(raw, coinCount, index);
      if (!state) return;
      const key = constrainedLightStateKey(state);
      if (seen.has(key)) return;
      seen.add(key);
      states.push(state);
    });
    return states;
  }

  function constrainedLightNormalizeStates(states, params = {}) {
    const coinCount = Number(params.coin_count ?? params.coinCount);
    const allowed = new Map(constrainedLightInitialStates(params).map(state => [constrainedLightStateKey(state), state]));
    const source = Array.isArray(states) && states.length ? states : [...allowed.values()];
    const result = [];
    const seen = new Set();
    source.forEach((raw, index) => {
      const state = constrainedLightNormalizeState(raw, coinCount, index);
      if (!state) return;
      const key = constrainedLightStateKey(state);
      const normalized = allowed.get(key) || state;
      const normalizedKey = constrainedLightStateKey(normalized);
      if (seen.has(normalizedKey)) return;
      seen.add(normalizedKey);
      result.push(normalized);
    });
    return result;
  }

  function constrainedLightStateKey(state) {
    const normalized = constrainedLightNormalizeState(state, null, 0);
    if (!normalized) return '';
    return normalized.id || normalized.coins.join(',');
  }

  function constrainedLightCoinSetKey(state) {
    const normalized = constrainedLightNormalizeState(state, null, 0);
    return normalized ? normalized.coins.join(',') : '';
  }

  function constrainedLightStateLabel(state) {
    const normalized = constrainedLightNormalizeState(state, null, 0);
    return normalized?.label || normalized?.id || constrainedLightCoinSetKey(state) || '?';
  }

  function constrainedLightCurrentStates(params = {}) {
    const states = params.currentStates ?? params.current_states ?? params.currentCandidates ?? params.current_candidates;
    return constrainedLightNormalizeStates(states, params);
  }

  function outcomeForConstrainedLightState(state, leftCoins, rightCoins, options = {}) {
    const normalized = constrainedLightNormalizeState(state, options.coinCount ?? options.coin_count ?? null, 0);
    if (!normalized) return null;
    const leftList = uniqueCoins(leftCoins, options.coinCount ?? options.coin_count ?? null);
    const rightList = uniqueCoins(rightCoins, options.coinCount ?? options.coin_count ?? null);
    if (options.requireEqualPanCounts !== false && leftList.length !== rightList.length) return null;
    const left = new Set(leftList);
    const right = new Set(rightList);
    for (const coin of left) if (right.has(coin)) return null;
    const fakeCoins = new Set(normalized.coins);
    const sideWeight = coins => coins.reduce((sum, coin) => sum + (fakeCoins.has(coin) ? 0 : 1), 0);
    const leftWeight = sideWeight(leftList);
    const rightWeight = sideWeight(rightList);
    if (leftWeight > rightWeight) return 'left_down';
    if (rightWeight > leftWeight) return 'right_down';
    return 'balance';
  }

  function constrainedLightFilterStates(params = {}) {
    const outcome = normalizeScaleOutcome(params.outcome);
    if (!outcome) return [];
    const coinCount = Number(params.coin_count ?? params.coinCount);
    return constrainedLightCurrentStates(params).filter(state =>
      outcomeForConstrainedLightState(
        state,
        params.leftCoins ?? params.left_coins,
        params.rightCoins ?? params.right_coins,
        {
          coinCount,
          requireEqualPanCounts: params.requireEqualPanCounts ?? params.require_equal_pan_counts
        }
      ) === outcome
    );
  }

  function constrainedLightPartitionStates(params = {}) {
    return Object.fromEntries(OUTCOMES.map(outcome => [
      outcome,
      constrainedLightFilterStates({ ...params, outcome })
    ]));
  }

  function constrainedLightPossibleCounts(states) {
    return [...new Set(constrainedLightNormalizeStates(states).map(state => state.coins.length))].sort((a, b) => a - b);
  }

  function constrainedLightUniqueCoinSet(states) {
    const normalized = constrainedLightNormalizeStates(states);
    if (!normalized.length) return null;
    const key = constrainedLightCoinSetKey(normalized[0]);
    return normalized.every(state => constrainedLightCoinSetKey(state) === key) ? normalized[0].coins : null;
  }

  function constrainedLightUniqueState(states) {
    const normalized = constrainedLightNormalizeStates(states);
    if (!normalized.length) return null;
    const key = constrainedLightStateKey(normalized[0]);
    return normalized.every(state => constrainedLightStateKey(state) === key) ? normalized[0] : null;
  }

  function constrainedLightObjectiveSolved(states, objective) {
    const current = constrainedLightNormalizeStates(states);
    if (!current.length) return false;
    if (objective === 'identify_one_light_coin' || objective === 'identify_one_counterfeit_coin') {
      return commonLightCoins(current).length > 0;
    }
    if (objective === 'identify_counterfeit_count') {
      return constrainedLightPossibleCounts(current).length === 1;
    }
    if (objective === 'identify_line_or_all_counterfeits' || objective === 'identify_all_counterfeits' || objective === 'identify_fake_coin_set') {
      return Boolean(constrainedLightUniqueState(current) || constrainedLightUniqueCoinSet(current));
    }
    return Boolean(constrainedLightUniqueState(current));
  }

  function constrainedLightAnswerOptionsForStates(states, objective) {
    const current = constrainedLightNormalizeStates(states);
    if (objective === 'identify_one_light_coin' || objective === 'identify_one_counterfeit_coin') {
      return possibleLightCoins(current).map(coin => ({ kind: 'coin', value: coin, label: String(coin) }));
    }
    if (objective === 'identify_counterfeit_count') {
      return constrainedLightPossibleCounts(current).map(count => ({ kind: 'count', value: count, label: String(count) }));
    }
    return current.map(state => ({ kind: 'state', value: constrainedLightStateKey(state), label: constrainedLightStateLabel(state), coins: [...state.coins] }));
  }

  function constrainedLightBranchStatus(states, usedWeighings, maxWeighings, objective = '') {
    const current = constrainedLightNormalizeStates(states);
    const used = Number(usedWeighings);
    const limit = Number(maxWeighings);
    if (constrainedLightObjectiveSolved(current, objective)) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function constrainedLightChooseCheaterOutcome(params = {}) {
    const objective = params.objective || '';
    const partitions = constrainedLightPartitionStates(params);
    const history = Array.isArray(params.history) ? params.history : [];
    const frequencies = Object.fromEntries(OUTCOMES.map(outcome => [outcome, 0]));
    for (const entry of history) {
      const outcome = normalizeScaleOutcome(typeof entry === 'string' ? entry : entry?.outcome);
      if (outcome in frequencies) frequencies[outcome] += 1;
    }
    const scores = Object.fromEntries(OUTCOMES.map(outcome => {
      const states = partitions[outcome];
      return [outcome, {
        states: states.length,
        solved: constrainedLightObjectiveSolved(states, objective) ? 1 : 0,
        answerOptions: constrainedLightAnswerOptionsForStates(states, objective).length,
        commonCoins: commonLightCoins(states).length,
        possibleCoins: possibleLightCoins(states).length,
        counts: constrainedLightPossibleCounts(states).length
      }];
    }));
    const outcome = OUTCOMES
      .filter(item => partitions[item].length > 0)
      .sort((a, b) =>
        scores[b].states - scores[a].states
        || scores[a].solved - scores[b].solved
        || scores[b].answerOptions - scores[a].answerOptions
        || scores[b].possibleCoins - scores[a].possibleCoins
        || scores[a].commonCoins - scores[b].commonCoins
        || frequencies[a] - frequencies[b]
        || OUTCOMES.indexOf(a) - OUTCOMES.indexOf(b)
      )[0] || 'balance';
    return {
      outcome,
      label: OUTCOME_LABELS[outcome],
      states: partitions[outcome],
      candidates: partitions[outcome],
      partitions,
      scores
    };
  }

  function constrainedLightExpandExhaustiveNode(params = {}) {
    const usedWeighings = Number(params.usedWeighings ?? params.used_weighings ?? 0);
    const maxWeighings = Number(params.maxWeighings ?? params.max_weighings);
    const objective = params.objective || '';
    const partitions = constrainedLightPartitionStates(params);
    const children = OUTCOMES
      .map(outcome => {
        const states = partitions[outcome];
        return {
          outcome,
          label: OUTCOME_LABELS[outcome],
          states,
          candidates: states,
          usedWeighings: usedWeighings + 1,
          status: constrainedLightBranchStatus(states, usedWeighings + 1, maxWeighings, objective),
          answerOptions: constrainedLightAnswerOptionsForStates(states, objective)
        };
      })
      .filter(child => child.states.length > 0);
    return { partitions, children };
  }

  function constrainedLightFinalizeAnswer(params = {}) {
    const objective = params.objective || '';
    const states = constrainedLightCurrentStates(params);
    const selectedCoin = Number(params.selectedCoin ?? params.selected_coin);
    const selectedCount = Number(params.selectedCount ?? params.selected_count);
    const selectedStateKey = String(params.selectedStateKey ?? params.selected_state_key ?? params.selectedState ?? params.selected_state ?? '');
    const selectedCoins = uniqueCoins(params.selectedCoins ?? params.selected_coins, params.coin_count ?? params.coinCount ?? null);
    if (objective === 'identify_one_light_coin' || objective === 'identify_one_counterfeit_coin') {
      const guaranteedCoins = commonLightCoins(states);
      if (guaranteedCoins.includes(selectedCoin)) {
        const actualState = states.find(state => state.coins.includes(selectedCoin)) ?? states[0] ?? null;
        return { win: true, actualState, actualCoins: actualState?.coins ?? [], guaranteedCoins, states, candidates: states };
      }
      const actualState = states.find(state => !state.coins.includes(selectedCoin)) ?? states[0] ?? null;
      return { win: false, actualState, actualCoins: actualState?.coins ?? [], guaranteedCoins, states, candidates: states };
    }
    if (objective === 'identify_counterfeit_count') {
      const counts = constrainedLightPossibleCounts(states);
      const win = counts.length === 1 && counts[0] === selectedCount;
      const actualState = (win ? states[0] : states.find(state => state.coins.length !== selectedCount)) ?? states[0] ?? null;
      return { win, actualState, actualCoins: actualState?.coins ?? [], actualCount: actualState?.coins.length ?? null, counts, states, candidates: states };
    }
    const uniqueState = constrainedLightUniqueState(states);
    const uniqueCoinSet = constrainedLightUniqueCoinSet(states);
    const selectedCoinKey = selectedCoins.join(',');
    const win = Boolean(
      (uniqueState && selectedStateKey && constrainedLightStateKey(uniqueState) === selectedStateKey)
      || (uniqueCoinSet && selectedCoinKey && uniqueCoinSet.join(',') === selectedCoinKey)
    );
    const actualState = win
      ? (uniqueState || states.find(state => constrainedLightCoinSetKey(state) === uniqueCoinSet.join(',')) || states[0] || null)
      : (states.find(state => constrainedLightStateKey(state) !== selectedStateKey && constrainedLightCoinSetKey(state) !== selectedCoinKey) ?? states[0] ?? null);
    return { win, actualState, actualCoins: actualState?.coins ?? [], uniqueState, uniqueCoinSet, states, candidates: states };
  }

  function zoltarMaskFromCoins(coins, coinCount = null) {
    const limit = Number(coinCount);
    const hasLimit = coinCount != null && Number.isInteger(limit);
    let mask = 0;
    for (const coin of uniqueCoins(coins, hasLimit ? limit : null)) mask |= (1 << (coin - 1));
    return mask;
  }

  function zoltarCoinsFromMask(mask, coinCount = 14) {
    const count = Number(coinCount);
    if (!Number.isInteger(count) || count < 1 || count > 30) return [];
    const rawMask = Number(mask) || 0;
    const coins = [];
    for (let index = 0; index < count; index += 1) {
      if (rawMask & (1 << index)) coins.push(index + 1);
    }
    return coins;
  }

  function zoltarBitCount(mask) {
    let value = Number(mask) || 0;
    let count = 0;
    while (value) {
      value &= value - 1;
      count += 1;
    }
    return count;
  }

  function zoltarInitialStates(coinCount = 14, realCount = 7) {
    const count = Number(coinCount);
    const genuineCount = Number(realCount);
    if (!Number.isInteger(count) || count < 2 || count > 20) return [];
    if (!Number.isInteger(genuineCount) || genuineCount < 1 || genuineCount >= count) return [];
    const states = [];
    const allMask = (1 << count) - 1;
    for (let realMask = 0; realMask <= allMask; realMask += 1) {
      if (zoltarBitCount(realMask) === genuineCount) {
        states.push({
          realMask,
          removedMask: 0,
          real: zoltarCoinsFromMask(realMask, count),
          removed: []
        });
      }
    }
    return states;
  }

  function zoltarNormalizeState(state, coinCount = 14, realCount = 7) {
    const count = Number(coinCount);
    const genuineCount = Number(realCount);
    if (!Number.isInteger(count) || count < 2 || count > 20) return null;
    let realMask = Number(state?.realMask ?? state?.real_mask);
    if (!Number.isInteger(realMask)) {
      realMask = zoltarMaskFromCoins(state?.realCoins ?? state?.real_coins ?? state?.real ?? state?.genuine ?? state?.coins, count);
    }
    let removedMask = Number(state?.removedMask ?? state?.removed_mask);
    if (!Number.isInteger(removedMask)) {
      removedMask = zoltarMaskFromCoins(state?.removedCoins ?? state?.removed_coins ?? state?.removed ?? [], count);
    }
    const allMask = (1 << count) - 1;
    realMask &= allMask;
    removedMask &= allMask;
    if (Number.isInteger(genuineCount) && genuineCount > 0 && zoltarBitCount(realMask) !== genuineCount) return null;
    return {
      realMask,
      removedMask,
      real: zoltarCoinsFromMask(realMask, count),
      removed: zoltarCoinsFromMask(removedMask, count)
    };
  }

  function zoltarStateKey(state) {
    const normalized = zoltarNormalizeState(state);
    return normalized ? `${normalized.realMask}:${normalized.removedMask}` : '';
  }

  function zoltarNormalizeStates(states, coinCount = 14, realCount = 7) {
    const seen = new Set();
    const result = [];
    for (const raw of states || []) {
      const state = zoltarNormalizeState(raw, coinCount, realCount);
      if (!state) continue;
      const key = `${state.realMask}:${state.removedMask}`;
      if (seen.has(key)) continue;
      seen.add(key);
      result.push(state);
    }
    return result;
  }

  function zoltarCurrentStates(params = {}) {
    const coinCount = Number(params.coin_count ?? params.coinCount ?? 14);
    const realCount = Number(params.real_count ?? params.realCount ?? 7);
    const current = params.currentStates ?? params.current_states ?? params.currentCandidates ?? params.current_candidates;
    return {
      coinCount,
      realCount,
      states: current?.length
        ? zoltarNormalizeStates(current, coinCount, realCount)
        : zoltarInitialStates(coinCount, realCount)
    };
  }

  function zoltarBranchKey(outcome, removedCoin = null) {
    const normalized = normalizeScaleOutcome(outcome);
    if (!normalized) return '';
    if (normalized === 'balance') return 'balance';
    const coin = Number(removedCoin);
    return Number.isInteger(coin) && coin > 0 ? `${normalized}:${coin}` : '';
  }

  function zoltarParseBranchKey(key) {
    if (key === 'balance') return { outcome: 'balance', removedCoin: null };
    const [outcome, coinText] = String(key || '').split(':');
    const normalized = normalizeScaleOutcome(outcome);
    const removedCoin = Number(coinText);
    if (!normalized || normalized === 'balance' || !Number.isInteger(removedCoin)) return null;
    return { outcome: normalized, removedCoin };
  }

  function zoltarOutcomeLabel(outcome, removedCoin = null) {
    const normalized = normalizeScaleOutcome(outcome);
    const base = OUTCOME_LABELS[normalized] || normalized || '';
    return normalized === 'balance' || removedCoin == null
      ? base
      : `${base}; Золтар забрал ${removedCoin}`;
  }

  function zoltarCompareState(state, leftCoins, rightCoins, options = {}) {
    const coinCount = Number(options.coinCount ?? options.coin_count ?? 14);
    const normalized = zoltarNormalizeState(state, coinCount, options.realCount ?? options.real_count ?? 7);
    if (!normalized) return null;
    const left = uniqueCoins(leftCoins, coinCount);
    const right = uniqueCoins(rightCoins, coinCount);
    const leftSet = new Set(left);
    for (const coin of right) {
      if (leftSet.has(coin)) return null;
    }
    for (const coin of [...left, ...right]) {
      if (normalized.removedMask & (1 << (coin - 1))) return null;
    }
    function sideWeightThousand(coins) {
      let realHits = 0;
      for (const coin of coins) {
        if (normalized.realMask & (1 << (coin - 1))) realHits += 1;
      }
      return coins.length * 999 + realHits;
    }
    const leftWeight = sideWeightThousand(left);
    const rightWeight = sideWeightThousand(right);
    if (leftWeight > rightWeight) return 'left_down';
    if (rightWeight > leftWeight) return 'right_down';
    return 'balance';
  }

  function zoltarNextBranchesForState(state, leftCoins, rightCoins, options = {}) {
    const coinCount = Number(options.coinCount ?? options.coin_count ?? 14);
    const realCount = Number(options.realCount ?? options.real_count ?? 7);
    const normalized = zoltarNormalizeState(state, coinCount, realCount);
    if (!normalized) return [];
    const outcome = zoltarCompareState(normalized, leftCoins, rightCoins, { coinCount, realCount });
    if (!outcome) return [];
    if (outcome === 'balance') {
      return [{
        key: 'balance',
        outcome,
        removedCoin: null,
        state: normalized
      }];
    }
    const heavier = outcome === 'left_down' ? uniqueCoins(leftCoins, coinCount) : uniqueCoins(rightCoins, coinCount);
    return heavier
      .filter(coin => !(normalized.removedMask & (1 << (coin - 1))))
      .map(coin => {
        const removedMask = normalized.removedMask | (1 << (coin - 1));
        return {
          key: zoltarBranchKey(outcome, coin),
          outcome,
          removedCoin: coin,
          state: {
            realMask: normalized.realMask,
            removedMask,
            real: normalized.real,
            removed: zoltarCoinsFromMask(removedMask, coinCount)
          }
        };
      });
  }

  function zoltarPartitionStates(params = {}) {
    const { coinCount, realCount, states } = zoltarCurrentStates(params);
    const leftCoins = uniqueCoins(params.leftCoins ?? params.left_coins, coinCount);
    const rightCoins = uniqueCoins(params.rightCoins ?? params.right_coins, coinCount);
    const byKey = new Map();
    for (const state of states) {
      for (const branch of zoltarNextBranchesForState(state, leftCoins, rightCoins, { coinCount, realCount })) {
        if (!byKey.has(branch.key)) {
          byKey.set(branch.key, {
            key: branch.key,
            outcome: branch.outcome,
            removedCoin: branch.removedCoin,
            label: zoltarOutcomeLabel(branch.outcome, branch.removedCoin),
            states: []
          });
        }
        byKey.get(branch.key).states.push(branch.state);
      }
    }
    return [...byKey.values()]
      .map(branch => {
        const branchStates = zoltarNormalizeStates(branch.states, coinCount, realCount);
        return { ...branch, states: branchStates, candidates: branchStates };
      })
      .sort((a, b) => OUTCOMES.indexOf(a.outcome) - OUTCOMES.indexOf(b.outcome) || (a.removedCoin ?? 0) - (b.removedCoin ?? 0));
  }

  function zoltarFilterStates(params = {}) {
    const targetKey = params.branchKey ?? params.branch_key ?? zoltarBranchKey(params.outcome, params.removedCoin ?? params.removed_coin);
    const partitions = zoltarPartitionStates(params);
    return partitions.find(branch => branch.key === targetKey)?.states || [];
  }

  function zoltarGuaranteedRealCoins(states, coinCount = 14, realCount = 7) {
    const current = zoltarNormalizeStates(states, coinCount, realCount);
    if (!current.length) return [];
    const result = [];
    for (let coin = 1; coin <= coinCount; coin += 1) {
      const bit = 1 << (coin - 1);
      if (current.every(state => (state.realMask & bit) && !(state.removedMask & bit))) result.push(coin);
    }
    return result;
  }

  function zoltarPossibleRemainingRealCoins(states, coinCount = 14, realCount = 7) {
    const result = new Set();
    for (const state of zoltarNormalizeStates(states, coinCount, realCount)) {
      for (let coin = 1; coin <= coinCount; coin += 1) {
        const bit = 1 << (coin - 1);
        if ((state.realMask & bit) && !(state.removedMask & bit)) result.add(coin);
      }
    }
    return [...result].sort((a, b) => a - b);
  }

  function zoltarRemovedCoinsInAllStates(states, coinCount = 14, realCount = 7) {
    const current = zoltarNormalizeStates(states, coinCount, realCount);
    if (!current.length) return [];
    const result = [];
    for (let coin = 1; coin <= coinCount; coin += 1) {
      const bit = 1 << (coin - 1);
      if (current.every(state => state.removedMask & bit)) result.push(coin);
    }
    return result;
  }

  function zoltarCoinStatuses(states, coinCount = 14, realCount = 7) {
    const current = zoltarNormalizeStates(states, coinCount, realCount);
    const guaranteed = new Set(zoltarGuaranteedRealCoins(current, coinCount, realCount));
    const removedAll = new Set(zoltarRemovedCoinsInAllStates(current, coinCount, realCount));
    const result = {};
    for (let coin = 1; coin <= coinCount; coin += 1) {
      if (removedAll.has(coin)) result[coin] = 'definite_fake_unknown_direction';
      else if (guaranteed.has(coin)) result[coin] = 'genuine';
      else result[coin] = 'possible_fake';
    }
    return result;
  }

  function zoltarBranchStatus(states, usedWeighings = 0, maxWeighings = null, options = {}) {
    const coinCount = Number(options.coinCount ?? options.coin_count ?? 14);
    const realCount = Number(options.realCount ?? options.real_count ?? 7);
    const current = zoltarNormalizeStates(states, coinCount, realCount);
    const used = Number(usedWeighings);
    const limit = Number(maxWeighings);
    if (zoltarGuaranteedRealCoins(current, coinCount, realCount).length > 0) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function zoltarChooseCheaterBranch(params = {}) {
    const { coinCount, realCount } = zoltarCurrentStates(params);
    const partitions = zoltarPartitionStates(params);
    const history = Array.isArray(params.history) ? params.history : [];
    const scores = Object.fromEntries(partitions.map(branch => {
      const guaranteed = zoltarGuaranteedRealCoins(branch.states, coinCount, realCount);
      return [branch.key, {
        states: branch.states.length,
        possibleRealCoins: zoltarPossibleRemainingRealCoins(branch.states, coinCount, realCount).length,
        guaranteedRealCoins: guaranteed.length
      }];
    }));
    const frequencies = Object.fromEntries(partitions.map(branch => [branch.key, 0]));
    for (const entry of history) {
      const key = entry?.branchKey ?? entry?.branch_key ?? zoltarBranchKey(entry?.outcome, entry?.removedCoin ?? entry?.removed_coin);
      if (key in frequencies) frequencies[key] += 1;
    }
    const chosen = partitions.slice().sort((a, b) => {
      const aSolved = scores[a.key].guaranteedRealCoins > 0 ? 1 : 0;
      const bSolved = scores[b.key].guaranteedRealCoins > 0 ? 1 : 0;
      return aSolved - bSolved
        || scores[b.key].states - scores[a.key].states
        || scores[b.key].possibleRealCoins - scores[a.key].possibleRealCoins
        || scores[a.key].guaranteedRealCoins - scores[b.key].guaranteedRealCoins
        || frequencies[a.key] - frequencies[b.key]
        || OUTCOMES.indexOf(a.outcome) - OUTCOMES.indexOf(b.outcome)
        || (a.removedCoin ?? 0) - (b.removedCoin ?? 0);
    })[0] || { key: '', outcome: 'balance', removedCoin: null, states: [] };
    return {
      ...chosen,
      candidates: chosen.states,
      partitions,
      scores
    };
  }

  function zoltarExpandExhaustiveNode(params = {}) {
    const { coinCount, realCount, states } = zoltarCurrentStates(params);
    const usedWeighings = Number(params.usedWeighings ?? params.used_weighings ?? 0);
    const maxWeighings = Number(params.maxWeighings ?? params.max_weighings);
    const partitions = zoltarPartitionStates({ ...params, currentStates: states });
    const children = partitions.map(branch => ({
      ...branch,
      candidates: branch.states,
      usedWeighings: usedWeighings + 1,
      status: zoltarBranchStatus(branch.states, usedWeighings + 1, maxWeighings, { coinCount, realCount })
    }));
    return { partitions, children };
  }

  function zoltarFinalizeAnswer(params = {}) {
    const { coinCount, realCount, states } = zoltarCurrentStates(params);
    const selectedCoin = Number(params.selectedCoin ?? params.selected_coin);
    const guaranteedCoins = zoltarGuaranteedRealCoins(states, coinCount, realCount);
    if (guaranteedCoins.includes(selectedCoin)) {
      const actualState = states[0] || null;
      return { win: true, selectedCoin, actualState, candidates: states, states, guaranteedCoins };
    }
    const bit = Number.isInteger(selectedCoin) ? (1 << (selectedCoin - 1)) : 0;
    const actualState = states.find(state => !bit || !(state.realMask & bit) || (state.removedMask & bit)) || states[0] || null;
    return { win: false, selectedCoin, actualState, candidates: states, states, guaranteedCoins };
  }

  function exhaustiveBranchStatus(candidates, usedWeighings, maxWeighings) {
    const remaining = normalizeKnownDirectionCandidates(candidates, null, true);
    const used = Number(usedWeighings);
    const limit = Number(maxWeighings);
    if (remaining.length === 1) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function expandExhaustiveNode(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const allowNoCounterfeit = params?.allowNoCounterfeit ?? params?.allow_no_counterfeit ?? false;
    const currentCandidates = normalizeKnownDirectionCandidates(
      params?.currentCandidates?.length ? params.currentCandidates : initialCandidates(coinCount, allowNoCounterfeit),
      Number.isInteger(coinCount) ? coinCount : null,
      allowNoCounterfeit
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
    const leftCoins = params?.leftCoins ?? params?.left_coins;
    const rightCoins = params?.rightCoins ?? params?.right_coins;
    const permutation = coinListIsWithinLimit(leftCoins, coinCount) && coinListIsWithinLimit(rightCoins, coinCount)
      ? mirroredPanCoinPermutation(leftCoins, rightCoins, Number.isInteger(coinCount) ? coinCount : null)
      : null;
    if (permutation) {
      markSymmetricOutcomeChildren(children, {
        candidateSetKey: branchCandidates => knownDirectionCandidateSetKey(branchCandidates, coinCount, allowNoCounterfeit),
        transformedCandidateSetKey: branchCandidates => permutedKnownDirectionCandidateSetKey(branchCandidates, permutation, coinCount, allowNoCounterfeit),
        reason: 'pan_mirror_coin_permutation'
      });
    }
    return { partitions, children };
  }

  function exhaustiveUnknownDirectionBranchStatus(candidates, usedWeighings, maxWeighings) {
    const coinCount = Number(maxCoinFromCandidates(candidates));
    const options = typeof arguments[3] === 'object' ? arguments[3] : {};
    const allowNoCounterfeit = options.allowNoCounterfeit ?? options.allow_no_counterfeit ?? (candidates || []).some(candidate => Number(candidate?.coin ?? candidate) === 0);
    const remaining = normalizeUnknownDirectionCandidates(candidates, Number.isInteger(coinCount) && coinCount > 0 ? coinCount : null, allowNoCounterfeit);
    const used = Number(usedWeighings);
    const limit = Number(maxWeighings);
    const objective = typeof arguments[3] === 'string' ? arguments[3] : arguments[3]?.objective;
    if (isUnknownDirectionCoinOnlyObjective(objective) && uniqueCandidateCoins(remaining).length === 1) return 'solved';
    if (remaining.length === 1) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function isUnknownDirectionCoinOnlyObjective(objective) {
    return ['identify_coin', 'identify_coin_only', 'identify_coin_only_unknown_direction'].includes(String(objective || ''));
  }

  function maxCoinFromCandidates(candidates) {
    return Math.max(0, ...((candidates || []).map(candidate => Number(candidate?.coin ?? 0)).filter(Number.isInteger)));
  }

  function flippedUnknownDirectionCandidate(candidate) {
    const normalized = normalizeUnknownDirectionCandidates([candidate], null, true)[0];
    if (!normalized) return null;
    if (normalized.coin === 0) return { coin: 0, direction: 'none' };
    return {
      coin: normalized.coin,
      direction: normalized.direction === 'heavier' ? 'lighter' : 'heavier'
    };
  }

  function unknownDirectionCandidateSetKey(candidates) {
    const allowNoCounterfeit = (candidates || []).some(candidate => Number(candidate?.coin ?? candidate) === 0);
    return normalizeUnknownDirectionCandidates(candidates || [], null, allowNoCounterfeit)
      .map(unknownDirectionCandidateKey)
      .sort()
      .join('|');
  }

  function flippedUnknownDirectionCandidateSetKey(candidates) {
    return (candidates || [])
      .map(flippedUnknownDirectionCandidate)
      .filter(Boolean)
      .map(unknownDirectionCandidateKey)
      .sort()
      .join('|');
  }

  function markUnknownDirectionSymmetricChildren(children) {
    return markSymmetricOutcomeChildren(children, {
      candidateSetKey: unknownDirectionCandidateSetKey,
      transformedCandidateSetKey: flippedUnknownDirectionCandidateSetKey,
      reason: 'direction_flip'
    });
  }

  function expandUnknownDirectionExhaustiveNode(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const allowNoCounterfeit = params?.allowNoCounterfeit ?? params?.allow_no_counterfeit ?? false;
    const currentCandidates = normalizeUnknownDirectionCandidates(
      params?.currentCandidates?.length ? params.currentCandidates : initialUnknownDirectionCandidates(coinCount, allowNoCounterfeit),
      Number.isInteger(coinCount) ? coinCount : null,
      allowNoCounterfeit
    );
    const usedWeighings = Number(params?.usedWeighings ?? params?.used_weighings ?? 0);
    const maxWeighings = Number(params?.maxWeighings ?? params?.max_weighings);
    const partitions = partitionUnknownDirectionCandidates({
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
          status: exhaustiveUnknownDirectionBranchStatus(candidates, usedWeighings + 1, maxWeighings, {
            objective: params?.objective,
            allowNoCounterfeit
          })
        };
      })
      .filter(child => child.candidates.length > 0);
    markUnknownDirectionSymmetricChildren(children);
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

  function chooseCheaterUnknownDirectionOutcome(params) {
    const partitions = partitionUnknownDirectionCandidates(params || {});
    const history = Array.isArray(params?.history) ? params.history : [];
    const maxSize = Math.max(...OUTCOMES.map(outcome => partitions[outcome].length));
    const tied = OUTCOMES.filter(outcome => partitions[outcome].length === maxSize);
    const frequencies = Object.fromEntries(OUTCOMES.map(outcome => [outcome, 0]));
    for (const entry of history) {
      const outcome = typeof entry === 'string' ? entry : entry?.outcome;
      if (outcome in frequencies) frequencies[outcome] += 1;
    }

    // Same deterministic tie-break as the known-direction mode: least used
    // previous outcome, then left_down, right_down, balance.
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

  function normalizeUnknownDirectionWeighingPlan(weighings, coinCount = null, maxWeighings = null) {
    const limit = Number(coinCount);
    const hasLimit = Number.isInteger(limit) && limit > 0;
    const rows = Array.isArray(weighings) ? weighings : [];
    const normalized = rows.map(row => ({
      leftCoins: uniqueCoins(row?.leftCoins ?? row?.left_coins ?? row?.left ?? [], hasLimit ? limit : null),
      rightCoins: uniqueCoins(row?.rightCoins ?? row?.right_coins ?? row?.right ?? [], hasLimit ? limit : null)
    }));
    const max = Number(maxWeighings);
    return maxWeighings != null && Number.isInteger(max) && max >= 0 ? normalized.slice(0, max) : normalized;
  }

  function unknownDirectionSignatureForCandidate(candidate, weighings, options = {}) {
    const coinCount = Number(options.coinCount ?? options.coin_count);
    const normalized = normalizeUnknownDirectionCandidates(
      [candidate],
      Number.isInteger(coinCount) ? coinCount : null
    )[0];
    if (!normalized) return null;
    const rows = normalizeUnknownDirectionWeighingPlan(weighings, coinCount);
    const signature = [];
    for (const row of rows) {
      const outcome = outcomeForUnknownDirectionCandidate(normalized, row.leftCoins, row.rightCoins, {
        requireEqualPanCounts: options.requireEqualPanCounts ?? options.require_equal_pan_counts
      });
      if (!outcome) return null;
      signature.push(outcome);
    }
    return signature;
  }

  function unknownDirectionSignatureKey(signature) {
    return (signature || []).join('|');
  }

  function oppositeUnknownDirectionOutcome(outcome) {
    if (outcome === 'left_down') return 'right_down';
    if (outcome === 'right_down') return 'left_down';
    return outcome;
  }

  function oppositeUnknownDirectionSignature(signature) {
    return (signature || []).map(oppositeUnknownDirectionOutcome);
  }

  function canonicalCoinOnlyUnknownDirectionSignatureKey(signature) {
    const key = unknownDirectionSignatureKey(signature);
    const oppositeKey = unknownDirectionSignatureKey(oppositeUnknownDirectionSignature(signature));
    return key <= oppositeKey ? key : oppositeKey;
  }

  function isCoinOnlyUnknownDirectionObjective(objective) {
    return ['identify_coin', 'identify_coin_only', 'identify_coin_only_unknown_direction'].includes(objective);
  }

  function knownDirectionSignatureForCandidate(candidate, counterfeitWeight, weighings, options = {}) {
    const coinCount = Number(options.coinCount ?? options.coin_count);
    const coin = Number(candidate?.coin ?? candidate?.id ?? candidate);
    if (!Number.isInteger(coin) || coin < 1 || (Number.isInteger(coinCount) && coin > coinCount)) return null;
    const rows = normalizeUnknownDirectionWeighingPlan(weighings, coinCount);
    const signature = [];
    for (const row of rows) {
      if (options.requireEqualPanCounts !== false && options.require_equal_pan_counts !== false && row.leftCoins.length !== row.rightCoins.length) return null;
      const outcome = outcomeForCandidate(coin, counterfeitWeight, row.leftCoins, row.rightCoins);
      if (!outcome) return null;
      signature.push(outcome);
    }
    return signature;
  }

  function checkKnownDirectionNonadaptiveStrategy(params = {}) {
    const coinCount = Number(params.coin_count ?? params.coinCount);
    const maxWeighings = Number(params.max_weighings ?? params.maxWeighings ?? params.weighing_count ?? params.weighingCount);
    const counterfeitWeight = params.counterfeit_weight ?? params.counterfeitWeight ?? params.weight ?? 'lighter';
    const requireEqualPanCounts = params.requireEqualPanCounts ?? params.require_equal_pan_counts;
    const weighings = normalizeUnknownDirectionWeighingPlan(
      params.weighings ?? params.plan ?? params.tests,
      coinCount,
      Number.isInteger(maxWeighings) ? maxWeighings : null
    );
    const errors = [];
    if (!Number.isInteger(coinCount) || coinCount < 2) {
      errors.push('coin_count must be an integer >= 2');
    }
    if (!Number.isInteger(maxWeighings) || maxWeighings < 1) {
      errors.push('max_weighings must be an integer >= 1');
    }
    if (!normalizeWeight(counterfeitWeight)) {
      errors.push('counterfeit_weight must be lighter or heavier');
    }
    if (Number.isInteger(maxWeighings) && weighings.length !== maxWeighings) {
      errors.push(`Нужно задать ровно ${maxWeighings} взвешивания.`);
    }
    for (let index = 0; index < weighings.length; index += 1) {
      const row = weighings[index];
      const left = row.leftCoins;
      const right = row.rightCoins;
      const leftSet = new Set(left);
      if (!left.length && !right.length) {
        errors.push(`Взвешивание ${index + 1}: обе чаши пусты.`);
      }
      if (right.some(coin => leftSet.has(coin))) {
        errors.push(`Взвешивание ${index + 1}: одна и та же монета есть на обеих чашах.`);
      }
      if (requireEqualPanCounts !== false && left.length !== right.length) {
        errors.push(`Взвешивание ${index + 1}: на чашах должно быть поровну монет.`);
      }
    }
    const states = Number.isInteger(coinCount) ? initialCandidates(coinCount) : [];
    const partitionsByKey = new Map();
    for (const state of states) {
      const signature = knownDirectionSignatureForCandidate(state, counterfeitWeight, weighings, {
        coinCount,
        requireEqualPanCounts
      });
      if (!signature || (Number.isInteger(maxWeighings) && signature.length !== maxWeighings)) continue;
      const key = unknownDirectionSignatureKey(signature);
      if (!partitionsByKey.has(key)) partitionsByKey.set(key, { key, signature, states: [] });
      partitionsByKey.get(key).states.push(state);
    }
    if (states.length && [...partitionsByKey.values()].reduce((sum, part) => sum + part.states.length, 0) !== states.length) {
      errors.push('Не для всех скрытых состояний удалось посчитать результаты.');
    }
    const partitions = [...partitionsByKey.values()].sort((a, b) =>
      a.key.localeCompare(b.key, undefined, { numeric: true })
    ).map(part => ({ ...part, solved: part.states.length === 1 }));
    const conflicts = partitions.filter(part => !part.solved);
    return {
      success: errors.length === 0 && states.length > 0 && conflicts.length === 0,
      ok: errors.length === 0 && states.length > 0 && conflicts.length === 0,
      complete: Number.isInteger(maxWeighings) && weighings.length === maxWeighings,
      coinCount,
      maxWeighings,
      counterfeitWeight: normalizeWeight(counterfeitWeight),
      weighings,
      states,
      partitions,
      conflicts,
      conflict: conflicts[0] || null,
      errors
    };
  }

  function checkUnknownDirectionNonadaptiveStrategy(params = {}) {
    const coinCount = Number(params.coin_count ?? params.coinCount);
    const maxWeighings = Number(params.max_weighings ?? params.maxWeighings ?? params.weighing_count ?? params.weighingCount);
    const requireEqualPanCounts = params.requireEqualPanCounts ?? params.require_equal_pan_counts;
    const objective = params.objective || params.goal || 'identify_coin_and_sign';
    const coinOnly = isCoinOnlyUnknownDirectionObjective(objective);
    const weighings = normalizeUnknownDirectionWeighingPlan(
      params.weighings ?? params.plan ?? params.tests,
      coinCount,
      Number.isInteger(maxWeighings) ? maxWeighings : null
    );
    const errors = [];
    if (!Number.isInteger(coinCount) || coinCount < 2) {
      errors.push('coin_count must be an integer >= 2');
    }
    if (!Number.isInteger(maxWeighings) || maxWeighings < 1) {
      errors.push('max_weighings must be an integer >= 1');
    }
    if (Number.isInteger(maxWeighings) && weighings.length !== maxWeighings) {
      errors.push(`Нужно задать ровно ${maxWeighings} взвешивания.`);
    }
    for (let index = 0; index < weighings.length; index += 1) {
      const row = weighings[index];
      const left = row.leftCoins;
      const right = row.rightCoins;
      const leftSet = new Set(left);
      if (!left.length && !right.length) {
        errors.push(`Взвешивание ${index + 1}: обе чаши пусты.`);
      }
      if (right.some(coin => leftSet.has(coin))) {
        errors.push(`Взвешивание ${index + 1}: одна и та же монета есть на обеих чашах.`);
      }
      if (requireEqualPanCounts !== false && left.length !== right.length) {
        errors.push(`Взвешивание ${index + 1}: на чашах должно быть поровну монет.`);
      }
    }
    const states = Number.isInteger(coinCount) ? initialUnknownDirectionCandidates(coinCount) : [];
    const partitionsByKey = new Map();
    for (const state of states) {
      const signature = unknownDirectionSignatureForCandidate(state, weighings, {
        coinCount,
        requireEqualPanCounts
      });
      if (!signature || (Number.isInteger(maxWeighings) && signature.length !== maxWeighings)) continue;
      const signatureKey = unknownDirectionSignatureKey(signature);
      const key = coinOnly ? canonicalCoinOnlyUnknownDirectionSignatureKey(signature) : signatureKey;
      if (!partitionsByKey.has(key)) partitionsByKey.set(key, { key, signature, signatures: [], states: [] });
      const part = partitionsByKey.get(key);
      if (!part.signatures.some(item => unknownDirectionSignatureKey(item) === signatureKey)) {
        part.signatures.push(signature);
      }
      part.states.push(state);
    }
    if (states.length && [...partitionsByKey.values()].reduce((sum, part) => sum + part.states.length, 0) !== states.length) {
      errors.push('Не для всех скрытых состояний удалось посчитать результаты.');
    }
    const partitions = [...partitionsByKey.values()].sort((a, b) =>
      a.key.localeCompare(b.key, undefined, { numeric: true })
    ).map(part => {
      const possibleCoins = [...new Set(part.states.map(state => state.coin))].sort((a, b) => a - b);
      const solved = coinOnly ? possibleCoins.length === 1 : part.states.length === 1;
      return { ...part, possibleCoins, solved };
    });
    const conflicts = partitions.filter(part => !part.solved);
    return {
      success: errors.length === 0 && states.length > 0 && conflicts.length === 0,
      ok: errors.length === 0 && states.length > 0 && conflicts.length === 0,
      complete: Number.isInteger(maxWeighings) && weighings.length === maxWeighings,
      coinCount,
      maxWeighings,
      objective,
      coinOnly,
      weighings,
      states,
      partitions,
      conflicts,
      conflict: conflicts[0] || null,
      errors
    };
  }

  function finalizeCheaterAnswer(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const allowNoCounterfeit = params?.allowNoCounterfeit ?? params?.allow_no_counterfeit ?? false;
    const candidates = normalizeKnownDirectionCandidates(
      params?.currentCandidates?.length ? params.currentCandidates : initialCandidates(coinCount, allowNoCounterfeit),
      Number.isInteger(coinCount) ? coinCount : null,
      allowNoCounterfeit
    );
    const selectedCoin = params?.selectedCoin === 'none' ? 0 : Number(params?.selectedCoin);
    if (candidates.length === 1) {
      const actualCoin = candidates[0];
      return { win: actualCoin === selectedCoin, actualCoin, candidates };
    }
    const actualCoin = candidates.find(candidate => candidate !== selectedCoin) ?? candidates[0] ?? null;
    return { win: false, actualCoin, candidates };
  }

  function finalizeCheaterUnknownDirectionAnswer(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const allowNoCounterfeit = params?.allowNoCounterfeit ?? params?.allow_no_counterfeit ?? false;
    const candidates = normalizeUnknownDirectionCandidates(
      params?.currentCandidates?.length ? params.currentCandidates : initialUnknownDirectionCandidates(coinCount, allowNoCounterfeit),
      Number.isInteger(coinCount) ? coinCount : null,
      allowNoCounterfeit
    );
    const selected = normalizeUnknownDirectionCandidates([{
      coin: params?.selectedCoin,
      direction: params?.selectedDirection ?? params?.selectedWeight
    }], Number.isInteger(coinCount) ? coinCount : null, allowNoCounterfeit)[0];
    const selectedKey = selected ? unknownDirectionCandidateKey(selected) : null;
    const selectedCoin = params?.selectedCoin === 'none' ? 0 : Number(params?.selectedCoin);
    const coinOnly = isUnknownDirectionCoinOnlyObjective(params?.objective);
    const possibleCoins = uniqueCandidateCoins(candidates);
    if (coinOnly && possibleCoins.length === 1) {
      const actualCandidate = candidates[0] ?? null;
      return {
        win: possibleCoins[0] === selectedCoin,
        actualCoin: possibleCoins[0] ?? null,
        actualDirection: actualCandidate?.direction ?? null,
        actualCandidate,
        candidates,
        possibleCoins
      };
    }
    if (candidates.length === 1) {
      const actualCandidate = candidates[0];
      return {
        win: selectedKey === unknownDirectionCandidateKey(actualCandidate),
        actualCoin: actualCandidate.coin,
        actualDirection: actualCandidate.direction,
        actualCandidate,
        candidates,
        possibleCoins
      };
    }
    const actualCandidate = coinOnly
      ? (candidates.find(candidate => candidate.coin !== selectedCoin) ?? candidates[0] ?? null)
      : (candidates.find(candidate => unknownDirectionCandidateKey(candidate) !== selectedKey) ?? candidates[0] ?? null);
    return {
      win: false,
      actualCoin: actualCandidate?.coin ?? null,
      actualDirection: actualCandidate?.direction ?? null,
      actualCandidate,
      candidates,
      possibleCoins
    };
  }

  function safePileNormalizePiles(params = {}) {
    const explicit = Array.isArray(params.piles) ? params.piles : [];
    const sizes = Array.isArray(params.pile_sizes ?? params.pileSizes)
      ? (params.pile_sizes ?? params.pileSizes).map(Number)
      : [];
    const source = explicit.length
      ? explicit
      : sizes.map((size, index) => ({ id: String.fromCharCode(65 + index), label: `Кучка ${String.fromCharCode(65 + index)}`, size }));
    const piles = [];
    const usedDiamonds = new Set();
    let nextDiamond = 1;
    for (let index = 0; index < source.length; index += 1) {
      const raw = source[index] || {};
      const id = String(raw.id ?? raw.key ?? String.fromCharCode(65 + index));
      const label = String(raw.label ?? raw.name ?? `Кучка ${id}`);
      const diamonds = Array.isArray(raw.diamonds ?? raw.coins)
        ? uniqueCoins(raw.diamonds ?? raw.coins)
        : [];
      const size = Number(raw.size ?? raw.count ?? diamonds.length);
      const pileDiamonds = diamonds.length
        ? diamonds
        : (Number.isInteger(size) && size > 0
          ? Array.from({ length: size }, (_item, offset) => nextDiamond + offset)
          : []);
      if (!id || !pileDiamonds.length) return [];
      for (const diamond of pileDiamonds) {
        if (usedDiamonds.has(diamond)) return [];
        usedDiamonds.add(diamond);
      }
      nextDiamond = Math.max(nextDiamond, ...pileDiamonds) + 1;
      piles.push({ id, label, diamonds: pileDiamonds, size: pileDiamonds.length });
    }
    return piles;
  }

  function safePileDiamondToPile(piles) {
    const map = new Map();
    for (const pile of safePileNormalizePiles({ piles })) {
      for (const diamond of pile.diamonds) map.set(diamond, pile.id);
    }
    return map;
  }

  function safePileInitialStates(params = {}) {
    const piles = safePileNormalizePiles(params);
    const result = [];
    for (const pile of piles) {
      for (const diamond of pile.diamonds) {
        result.push({ diamond, coin: diamond, pile: pile.id, direction: 'heavier' });
        result.push({ diamond, coin: diamond, pile: pile.id, direction: 'lighter' });
      }
    }
    return result;
  }

  function safePileNormalizeStates(states, params = {}) {
    const piles = safePileNormalizePiles(params);
    const diamondToPile = safePileDiamondToPile(piles);
    const seen = new Set();
    const result = [];
    for (const raw of states || []) {
      const diamond = Number(raw?.diamond ?? raw?.coin ?? raw?.id ?? raw?.[0]);
      const direction = normalizeDirection(raw?.direction ?? raw?.weight ?? raw?.[1]);
      const pile = String(raw?.pile ?? raw?.pileId ?? diamondToPile.get(diamond) ?? '');
      if (!Number.isInteger(diamond) || !direction || !pile || !diamondToPile.has(diamond)) continue;
      const key = `${diamond}:${direction}`;
      if (seen.has(key)) continue;
      seen.add(key);
      result.push({ diamond, coin: diamond, pile, direction });
    }
    return result;
  }

  function safePileCurrentStates(params = {}) {
    const current = params.currentStates ?? params.current_states ?? params.currentCandidates ?? params.current_candidates;
    return current?.length ? safePileNormalizeStates(current, params) : safePileInitialStates(params);
  }

  function safePileOutcomeForState(state, leftDiamonds, rightDiamonds, options = {}) {
    const normalized = safePileNormalizeStates([state], options)[0];
    if (!normalized) return null;
    return outcomeForUnknownDirectionCandidate(
      { coin: normalized.diamond, direction: normalized.direction },
      leftDiamonds,
      rightDiamonds,
      { requireEqualPanCounts: options.requireEqualPanCounts ?? options.require_equal_pan_counts }
    );
  }

  function safePileFilterStates(params = {}) {
    const states = safePileCurrentStates(params);
    const outcome = normalizeScaleOutcome(params.outcome ?? params.result);
    if (!outcome) return [];
    const piles = safePileNormalizePiles(params);
    const leftDiamonds = uniqueCoins(params.leftDiamonds ?? params.left_diamonds ?? params.leftCoins ?? params.left ?? []);
    const rightDiamonds = uniqueCoins(params.rightDiamonds ?? params.right_diamonds ?? params.rightCoins ?? params.right ?? []);
    return states.filter(state => safePileOutcomeForState(state, leftDiamonds, rightDiamonds, {
      piles,
      requireEqualPanCounts: params.requireEqualPanCounts ?? params.require_equal_pan_counts
    }) === outcome);
  }

  function safePilePartitionStates(params = {}) {
    return Object.fromEntries(OUTCOMES.map(outcome => [
      outcome,
      safePileFilterStates({ ...params, outcome })
    ]));
  }

  function safePileSafePileIds(states, params = {}) {
    const piles = safePileNormalizePiles(params);
    const possibleFakePiles = new Set(safePileNormalizeStates(states || [], { piles }).map(state => state.pile));
    return piles.map(pile => pile.id).filter(id => !possibleFakePiles.has(id));
  }

  function safePileStateCounts(states, params = {}) {
    const piles = safePileNormalizePiles(params);
    const counts = Object.fromEntries(piles.map(pile => [pile.id, { total: 0, heavier: 0, lighter: 0 }]));
    for (const state of safePileNormalizeStates(states || [], { piles })) {
      if (!counts[state.pile]) counts[state.pile] = { total: 0, heavier: 0, lighter: 0 };
      counts[state.pile].total += 1;
      counts[state.pile][state.direction] += 1;
    }
    return counts;
  }

  function safePileBranchStatus(states, usedWeighings, maxWeighings, params = {}) {
    const current = safePileNormalizeStates(states || [], params);
    const used = Number(usedWeighings);
    const limit = Number(maxWeighings ?? params.max_weighings ?? params.maxWeighings);
    if (safePileSafePileIds(current, params).length > 0) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function safePileChooseCheaterOutcome(params = {}) {
    const partitions = safePilePartitionStates(params);
    const history = Array.isArray(params.history) ? params.history : [];
    const frequencies = Object.fromEntries(OUTCOMES.map(outcome => [outcome, 0]));
    for (const entry of history) {
      const outcome = typeof entry === 'string' ? entry : entry?.outcome;
      if (outcome in frequencies) frequencies[outcome] += 1;
    }
    const scored = OUTCOMES.map(outcome => {
      const states = partitions[outcome] || [];
      return {
        outcome,
        states,
        safePiles: safePileSafePileIds(states, params),
        status: safePileBranchStatus(states, (params.usedWeighings ?? params.used_weighings ?? 0) + 1, params.maxWeighings ?? params.max_weighings, params)
      };
    }).filter(item => item.states.length > 0);
    const chosen = scored.sort((a, b) =>
      b.states.length - a.states.length
      || a.safePiles.length - b.safePiles.length
      || frequencies[a.outcome] - frequencies[b.outcome]
      || OUTCOMES.indexOf(a.outcome) - OUTCOMES.indexOf(b.outcome)
    )[0] || { outcome: 'balance', states: [], safePiles: [], status: 'failed' };
    return {
      outcome: chosen.outcome,
      label: OUTCOME_LABELS[chosen.outcome],
      states: chosen.states,
      candidates: chosen.states,
      safePiles: chosen.safePiles,
      partitions,
      scores: Object.fromEntries(OUTCOMES.map(outcome => {
        const states = partitions[outcome] || [];
        return [outcome, {
          states: states.length,
          safePiles: safePileSafePileIds(states, params)
        }];
      }))
    };
  }

  function safePileExpandExhaustiveNode(params = {}) {
    const states = safePileCurrentStates(params);
    const usedWeighings = Number(params.usedWeighings ?? params.used_weighings ?? 0);
    const maxWeighings = Number(params.maxWeighings ?? params.max_weighings ?? 1);
    const partitions = safePilePartitionStates({ ...params, currentStates: states });
    const children = OUTCOMES.map(outcome => {
      const childStates = partitions[outcome] || [];
      return {
        outcome,
        label: OUTCOME_LABELS[outcome],
        states: childStates,
        candidates: childStates,
        safePiles: safePileSafePileIds(childStates, params),
        usedWeighings: usedWeighings + 1,
        status: safePileBranchStatus(childStates, usedWeighings + 1, maxWeighings, params)
      };
    }).filter(child => child.states.length > 0);
    return { partitions, children };
  }

  function safePileFinalizeAnswer(params = {}) {
    const states = safePileCurrentStates(params);
    const selectedPile = String(params.selectedPile ?? params.selected_pile ?? params.answer ?? '');
    const safePiles = safePileSafePileIds(states, params);
    const actualState = states.find(state => state.pile === selectedPile) || states[0] || null;
    return {
      win: safePiles.includes(selectedPile),
      selectedPile,
      actualState,
      states,
      candidates: states,
      safePiles
    };
  }

  function xorSingleFlipPositionCount(params = {}) {
    const count = Number(params.position_count ?? params.positionCount ?? params.object_count ?? 8);
    if (!Number.isInteger(count) || count < 2 || count > 16) return 0;
    return (count & (count - 1)) === 0 ? count : 0;
  }

  function xorSingleFlipBitsFromMask(mask, positionCount) {
    const count = xorSingleFlipPositionCount({ position_count: positionCount });
    const value = Number(mask);
    if (!count || !Number.isInteger(value) || value < 0 || value >= 2 ** count) return [];
    return Array.from({ length: count }, (_item, index) => (value >> index) & 1);
  }

  function xorSingleFlipMaskFromBits(bits, positionCount = null) {
    const count = xorSingleFlipPositionCount({ position_count: positionCount ?? bits?.length ?? 0 });
    if (!count) return null;
    let mask = 0;
    for (let index = 0; index < count; index += 1) {
      if (Number(bits?.[index]) ? 1 : 0) mask |= (1 << index);
    }
    return mask;
  }

  function xorSingleFlipChecksum(bits) {
    let result = 0;
    for (let index = 0; index < (bits || []).length; index += 1) {
      if (Number(bits[index]) ? 1 : 0) result ^= index;
    }
    return result;
  }

  function xorSingleFlipApplyFlip(bits, flip) {
    const result = (bits || []).map(bit => Number(bit) ? 1 : 0);
    const index = Number(flip);
    if (!Number.isInteger(index) || index < 0 || index >= result.length) return result;
    result[index] = result[index] ? 0 : 1;
    return result;
  }

  function xorSingleFlipRecommendedFlip(bits, keyPosition) {
    const key = Number(keyPosition);
    if (!Number.isInteger(key) || key < 0 || key >= (bits || []).length) return null;
    return xorSingleFlipChecksum(bits) ^ key;
  }

  function xorSingleFlipFinalGuess(finalBits) {
    return xorSingleFlipChecksum(finalBits);
  }

  function xorSingleFlipInitialStates(params = {}) {
    const count = xorSingleFlipPositionCount(params);
    if (!count) return [];
    const result = [];
    for (let mask = 0; mask < 2 ** count; mask += 1) {
      const bits = xorSingleFlipBitsFromMask(mask, count);
      for (let key = 0; key < count; key += 1) {
        result.push({ mask, bits, key });
      }
    }
    return result;
  }

  function xorSingleFlipStateKey(state) {
    const bits = Array.isArray(state?.bits)
      ? state.bits.map(bit => Number(bit) ? 1 : 0)
      : xorSingleFlipBitsFromMask(state?.mask ?? 0, state?.position_count ?? state?.positionCount ?? 8);
    return `${bits.join('')}:${Number(state?.key ?? state?.keyPosition ?? state?.key_position ?? 0)}`;
  }

  function xorSingleFlipEvaluate(params = {}) {
    const count = xorSingleFlipPositionCount(params);
    const bits = Array.isArray(params.bits)
      ? params.bits.slice(0, count).map(bit => Number(bit) ? 1 : 0)
      : xorSingleFlipBitsFromMask(params.mask ?? 0, count);
    const key = Number(params.key ?? params.keyPosition ?? params.key_position);
    const flip = Number(params.flip);
    const guess = Number(params.guess);
    const initialChecksum = xorSingleFlipChecksum(bits);
    const recommendedFlip = xorSingleFlipRecommendedFlip(bits, key);
    const finalBits = xorSingleFlipApplyFlip(bits, flip);
    const finalChecksum = xorSingleFlipFinalGuess(finalBits);
    const firstOk = Number.isInteger(flip) && flip === recommendedFlip;
    const secondOk = Number.isInteger(guess) && guess === finalChecksum && guess === key;
    return {
      bits,
      key,
      flip,
      guess,
      initialChecksum,
      recommendedFlip,
      finalBits,
      finalChecksum,
      firstOk,
      secondOk,
      win: firstOk && secondOk
    };
  }

  function xorSingleFlipCheckStrategy(params = {}) {
    const count = xorSingleFlipPositionCount(params);
    const states = xorSingleFlipInitialStates({ position_count: count });
    const failures = [];
    for (const state of states) {
      const flip = xorSingleFlipRecommendedFlip(state.bits, state.key);
      const finalBits = xorSingleFlipApplyFlip(state.bits, flip);
      const guess = xorSingleFlipFinalGuess(finalBits);
      if (guess !== state.key || flip < 0 || flip >= count) {
        failures.push({ ...state, flip, guess, finalBits });
      }
    }
    return {
      success: failures.length === 0,
      checked: states.length,
      positionCount: count,
      failures
    };
  }

  function wiseMenParityPersonCount(params = {}) {
    const count = Number(params.person_count ?? params.personCount ?? params.word_length ?? 6);
    if (!Number.isInteger(count) || count < 2 || count > 10) return 0;
    return count;
  }

  function wiseMenParityColorCount(params = {}) {
    const personCount = wiseMenParityPersonCount(params);
    const count = Number(params.color_count ?? params.colorCount ?? params.message_count ?? 2 ** Math.max(0, personCount - 1));
    if (!personCount || !Number.isInteger(count) || count < 2 || count > 2 ** (personCount - 1)) return 0;
    return count;
  }

  function wiseMenParityCodeword(color, params = {}) {
    const personCount = wiseMenParityPersonCount(params);
    const colorCount = wiseMenParityColorCount(params);
    const normalized = Number(color);
    if (!personCount || !colorCount || !Number.isInteger(normalized) || normalized < 1 || normalized > colorCount) return [];
    const index = normalized - 1;
    const bits = [];
    let parity = 0;
    for (let bit = 0; bit < personCount - 1; bit += 1) {
      const value = (index >> bit) & 1;
      bits.push(value);
      parity ^= value;
    }
    bits.push(parity);
    return bits;
  }

  function wiseMenParityWordKey(word) {
    return (word || []).map(bit => Number(bit) ? 1 : 0).join('');
  }

  function wiseMenParityCodebook(params = {}) {
    const colorCount = wiseMenParityColorCount(params);
    if (!colorCount) return [];
    return Array.from({ length: colorCount }, (_item, index) => ({
      color: index + 1,
      word: wiseMenParityCodeword(index + 1, params)
    }));
  }

  function wiseMenParityValidateCodebook(params = {}) {
    const personCount = wiseMenParityPersonCount(params);
    const colorCount = wiseMenParityColorCount(params);
    const codebook = wiseMenParityCodebook(params);
    const errors = [];
    const seen = new Set();
    if (!personCount) errors.push('Нужно хотя бы два мудреца.');
    if (!colorCount) errors.push('Цветов должно быть не больше числа четных двоичных слов.');
    for (const entry of codebook) {
      if (entry.word.length !== personCount) errors.push(`У цвета ${entry.color} неверная длина слова.`);
      const key = wiseMenParityWordKey(entry.word);
      if (seen.has(key)) errors.push(`Код ${key} повторяется.`);
      seen.add(key);
      const parity = entry.word.reduce((acc, bit) => acc ^ (Number(bit) ? 1 : 0), 0);
      if (parity !== 0) errors.push(`Код цвета ${entry.color} нечетный.`);
    }
    return {
      ok: errors.length === 0,
      personCount,
      colorCount,
      capacity: personCount ? 2 ** (personCount - 1) : 0,
      codebook,
      errors
    };
  }

  function wiseMenParityNormalizeColors(colors, params = {}) {
    const personCount = wiseMenParityPersonCount(params);
    const colorCount = wiseMenParityColorCount(params);
    const result = [];
    for (let index = 0; index < personCount; index += 1) {
      const raw = Number(colors?.[index]);
      result.push(Number.isInteger(raw) && raw >= 1 && raw <= colorCount ? raw : 1);
    }
    return result;
  }

  function wiseMenParityMessages(colors, params = {}) {
    const personCount = wiseMenParityPersonCount(params);
    const normalizedColors = wiseMenParityNormalizeColors(colors, params);
    const words = normalizedColors.map(color => wiseMenParityCodeword(color, params));
    const messages = [];
    for (let speaker = 0; speaker < personCount; speaker += 1) {
      let bit = 0;
      for (let person = 0; person < personCount; person += 1) {
        if (person !== speaker) bit ^= words[person][speaker];
      }
      messages.push(bit);
    }
    return messages;
  }

  function wiseMenParityDecodePerson(params = {}) {
    const personCount = wiseMenParityPersonCount(params);
    const colorCount = wiseMenParityColorCount(params);
    const target = Number(params.person ?? params.target ?? params.targetPerson ?? 0);
    const colors = wiseMenParityNormalizeColors(params.colors, params);
    const messages = Array.isArray(params.messages)
      ? params.messages.slice(0, personCount).map(bit => Number(bit) ? 1 : 0)
      : wiseMenParityMessages(colors, params);
    if (!personCount || !colorCount || !Number.isInteger(target) || target < 0 || target >= personCount) {
      return { ok: false, target, decodedColor: null, bits: [], messages, steps: [] };
    }
    const words = colors.map(color => wiseMenParityCodeword(color, params));
    const bits = Array.from({ length: personCount }, () => 0);
    const steps = [];
    for (let bitIndex = 0; bitIndex < personCount; bitIndex += 1) {
      if (bitIndex === target) continue;
      let visibleParity = 0;
      for (let person = 0; person < personCount; person += 1) {
        if (person !== target && person !== bitIndex) visibleParity ^= words[person][bitIndex];
      }
      bits[bitIndex] = messages[bitIndex] ^ visibleParity;
      steps.push({
        bit: bitIndex,
        speaker: bitIndex,
        message: messages[bitIndex],
        visibleParity,
        value: bits[bitIndex]
      });
    }
    bits[target] = bits.reduce((acc, bit, index) => index === target ? acc : (acc ^ bit), 0);
    steps.push({
      bit: target,
      speaker: target,
      message: messages[target],
      visibleParity: null,
      value: bits[target],
      fromEvenParity: true
    });
    const key = wiseMenParityWordKey(bits);
    const decoded = wiseMenParityCodebook(params).find(entry => wiseMenParityWordKey(entry.word) === key);
    return {
      ok: Boolean(decoded),
      target,
      actualColor: colors[target],
      decodedColor: decoded?.color ?? null,
      bits,
      messages,
      steps,
      win: decoded?.color === colors[target]
    };
  }

  function wiseMenParityEvaluate(params = {}) {
    const personCount = wiseMenParityPersonCount(params);
    const colors = wiseMenParityNormalizeColors(params.colors, params);
    const messages = Array.isArray(params.messages)
      ? params.messages.slice(0, personCount).map(bit => Number(bit) ? 1 : 0)
      : wiseMenParityMessages(colors, params);
    const decoded = [];
    const failures = [];
    for (let person = 0; person < personCount; person += 1) {
      const result = wiseMenParityDecodePerson({ ...params, colors, messages, person });
      decoded.push(result);
      if (!result.win) failures.push(result);
    }
    return {
      colors,
      messages,
      decoded,
      success: failures.length === 0,
      failures
    };
  }

  function wiseMenParityExhaustiveCheck(params = {}) {
    const validation = wiseMenParityValidateCodebook(params);
    const personCount = validation.personCount;
    const colorCount = validation.colorCount;
    const failures = [];
    if (!validation.ok) {
      return { success: false, checked: 0, validation, failures };
    }
    for (let person = 0; person < personCount; person += 1) {
      for (let color = 1; color <= colorCount; color += 1) {
        const colors = Array.from({ length: personCount }, (_item, index) => ((color + index + person - 1) % colorCount) + 1);
        colors[person] = color;
        const result = wiseMenParityEvaluate({ ...params, colors });
        if (!result.decoded[person]?.win || !result.success) failures.push({ person, color, result });
      }
    }
    return {
      success: failures.length === 0,
      checked: personCount * colorCount,
      validation,
      failures
    };
  }

  function wiseMenParityRandomColors(params = {}) {
    const personCount = wiseMenParityPersonCount(params);
    const colorCount = wiseMenParityColorCount(params);
    return Array.from({ length: personCount }, () => Math.floor(Math.random() * colorCount) + 1);
  }

  function wiseMenColorCountSageCount(params = {}) {
    const count = Number(params.sage_count ?? params.sageCount ?? params.person_count ?? params.personCount ?? 6);
    if (!Number.isInteger(count) || count < 2 || count > 10) return 0;
    return count;
  }

  function wiseMenColorCountColorCount(params = {}) {
    const count = Number(params.color_count ?? params.colorCount ?? 4);
    if (!Number.isInteger(count) || count < 2 || count > 8) return 0;
    return count;
  }

  function wiseMenColorCountValues(params = {}) {
    const colorCount = wiseMenColorCountColorCount(params);
    const raw = Array.isArray(params.count_values) ? params.count_values : params.countValues;
    const values = (Array.isArray(raw) ? raw : Array.from({ length: colorCount }, (_item, index) => index))
      .map(value => Number(value));
    if (
      !colorCount ||
      values.length !== colorCount ||
      values.some(value => !Number.isInteger(value) || value < 0) ||
      new Set(values).size !== values.length
    ) {
      return [];
    }
    return values;
  }

  function wiseMenColorCountTargetCorrectMin(params = {}) {
    const sageCount = wiseMenColorCountSageCount(params);
    const target = Number(params.target_correct_min ?? params.targetCorrectMin ?? Math.floor(sageCount / 2));
    if (!sageCount || !Number.isInteger(target) || target < 1 || target > sageCount) return 0;
    return target;
  }

  function wiseMenColorCountValidateConfig(params = {}) {
    const sageCount = wiseMenColorCountSageCount(params);
    const colorCount = wiseMenColorCountColorCount(params);
    const countValues = wiseMenColorCountValues(params);
    const targetCorrectMin = wiseMenColorCountTargetCorrectMin(params);
    const errors = [];
    if (!sageCount) errors.push('Нужно от 2 до 10 мудрецов.');
    if (!colorCount) errors.push('Нужно от 2 до 8 цветов.');
    if (!countValues.length) errors.push('Список количеств должен содержать разные неотрицательные числа по одному на цвет.');
    if (countValues.length && countValues.reduce((sum, value) => sum + value, 0) !== sageCount) {
      errors.push('Сумма количеств должна равняться числу мудрецов.');
    }
    if (!targetCorrectMin) errors.push('Цель должна быть от 1 до числа мудрецов.');
    if (sageCount && targetCorrectMin && targetCorrectMin > Math.floor(sageCount / 2)) {
      errors.push('Этот протокол делит мудрецов на две равные группы, поэтому цель не должна быть больше половины.');
    }
    return {
      ok: errors.length === 0,
      sageCount,
      colorCount,
      countValues,
      targetCorrectMin,
      errors
    };
  }

  function wiseMenColorCountCountsFromColors(colors, params = {}) {
    const colorCount = wiseMenColorCountColorCount(params);
    const counts = Array.from({ length: colorCount }, () => 0);
    for (const color of colors || []) {
      const normalized = Number(color);
      if (Number.isInteger(normalized) && normalized >= 1 && normalized <= colorCount) {
        counts[normalized - 1] += 1;
      }
    }
    return counts;
  }

  function wiseMenColorCountNormalizeColors(colors, params = {}) {
    const sageCount = wiseMenColorCountSageCount(params);
    const colorCount = wiseMenColorCountColorCount(params);
    return Array.from({ length: sageCount }, (_item, index) => {
      const color = Number(colors?.[index]);
      return Number.isInteger(color) && color >= 1 && color <= colorCount ? color : 1;
    });
  }

  function wiseMenColorCountValidateState(colors, params = {}) {
    const validation = wiseMenColorCountValidateConfig(params);
    const normalized = wiseMenColorCountNormalizeColors(colors, params);
    const counts = wiseMenColorCountCountsFromColors(normalized, params);
    const errors = [...validation.errors];
    if (validation.ok) {
      const expected = [...validation.countValues].sort((a, b) => a - b).join(',');
      const actual = [...counts].sort((a, b) => a - b).join(',');
      if (actual !== expected) {
        errors.push(`Количества цветов должны быть ${expected}, сейчас ${actual}.`);
      }
    }
    return {
      ok: errors.length === 0,
      colors: normalized,
      counts,
      errors
    };
  }

  function wiseMenColorCountPermutationParity(counts, params = {}) {
    const countValues = wiseMenColorCountValues(params);
    if (!Array.isArray(counts) || counts.length !== countValues.length) return null;
    const order = new Map(countValues.map((value, index) => [value, index]));
    const sequence = counts.map(value => order.get(Number(value)));
    if (sequence.some(value => !Number.isInteger(value))) return null;
    let parity = 0;
    for (let left = 0; left < sequence.length; left += 1) {
      for (let right = left + 1; right < sequence.length; right += 1) {
        if (sequence[left] > sequence[right]) parity ^= 1;
      }
    }
    return parity;
  }

  function wiseMenColorCountTargetParityForSage(sageIndex, params = {}) {
    const sageCount = wiseMenColorCountSageCount(params);
    const split = Math.floor(sageCount / 2);
    return Number(sageIndex) < split ? 0 : 1;
  }

  function wiseMenColorCountCandidateOptions(colors, sageIndex, params = {}) {
    const state = wiseMenColorCountValidateState(colors, params);
    const sage = Number(sageIndex);
    if (!state.ok || !Number.isInteger(sage) || sage < 0 || sage >= state.colors.length) return [];
    const visibleCounts = [...state.counts];
    visibleCounts[state.colors[sage] - 1] -= 1;
    return state.counts.map((_count, colorIndex) => {
      const candidateCounts = [...visibleCounts];
      candidateCounts[colorIndex] += 1;
      const candidateState = wiseMenColorCountValidateState(
        state.colors.map((color, index) => index === sage ? colorIndex + 1 : color),
        params
      );
      return candidateState.ok
        ? {
            color: colorIndex + 1,
            counts: candidateCounts,
            parity: wiseMenColorCountPermutationParity(candidateCounts, params)
          }
        : null;
    }).filter(Boolean);
  }

  function wiseMenColorCountEvaluate(params = {}) {
    const state = wiseMenColorCountValidateState(params.colors ?? params.state?.colors ?? params.state, params);
    const targetCorrectMin = wiseMenColorCountTargetCorrectMin(params);
    const parity = state.ok ? wiseMenColorCountPermutationParity(state.counts, params) : null;
    if (!state.ok) {
      return {
        ok: false,
        success: false,
        colors: state.colors,
        counts: state.counts,
        parity,
        rows: [],
        correctCount: 0,
        targetCorrectMin,
        errors: state.errors
      };
    }
    const rows = state.colors.map((actualColor, sageIndex) => {
      const targetParity = wiseMenColorCountTargetParityForSage(sageIndex, params);
      const options = wiseMenColorCountCandidateOptions(state.colors, sageIndex, params);
      const selected = options.find(option => option.parity === targetParity) || options[0] || null;
      const visibleCounts = [...state.counts];
      visibleCounts[actualColor - 1] -= 1;
      return {
        sage: sageIndex + 1,
        sageIndex,
        actualColor,
        visibleCounts,
        options,
        targetParity,
        guess: selected?.color ?? null,
        guessedCounts: selected?.counts ?? [],
        correct: selected?.color === actualColor
      };
    });
    const correctCount = rows.filter(row => row.correct).length;
    return {
      ok: true,
      success: correctCount >= targetCorrectMin,
      colors: state.colors,
      counts: state.counts,
      parity,
      rows,
      correctCount,
      targetCorrectMin,
      errors: []
    };
  }

  function wiseMenColorCountInitialStates(params = {}) {
    const validation = wiseMenColorCountValidateConfig(params);
    if (!validation.ok) return [];
    const states = [];

    function uniqueArrangements(items) {
      const result = [];
      const used = Array.from({ length: items.length }, () => false);
      const sorted = [...items].sort((a, b) => a - b);
      function visit(current) {
        if (current.length === sorted.length) {
          result.push(current.slice());
          return;
        }
        for (let index = 0; index < sorted.length; index += 1) {
          if (used[index]) continue;
          if (index > 0 && sorted[index] === sorted[index - 1] && !used[index - 1]) continue;
          used[index] = true;
          current.push(sorted[index]);
          visit(current);
          current.pop();
          used[index] = false;
        }
      }
      visit([]);
      return result;
    }

    for (const counts of permutations(validation.countValues)) {
      const colorBlocks = counts.flatMap((count, colorIndex) =>
        Array.from({ length: count }, () => colorIndex + 1)
      );
      for (const colors of uniqueArrangements(colorBlocks)) {
        states.push({
          colors,
          counts: counts.slice(),
          parity: wiseMenColorCountPermutationParity(counts, params)
        });
      }
    }
    return states;
  }

  function wiseMenColorCountRandomState(params = {}, random = Math.random) {
    const states = wiseMenColorCountInitialStates(params);
    if (!states.length) return { colors: [], counts: [], parity: null };
    return states[Math.floor(random() * states.length) % states.length];
  }

  function wiseMenColorCountCheaterState(params = {}) {
    const states = wiseMenColorCountInitialStates(params);
    return states.find(state => state.parity === 1) || states[states.length - 1] || { colors: [], counts: [], parity: null };
  }

  function wiseMenColorCountExhaustiveCheck(params = {}) {
    const states = wiseMenColorCountInitialStates(params);
    const targetCorrectMin = wiseMenColorCountTargetCorrectMin(params);
    const failures = [];
    let minCorrect = Infinity;
    let maxCorrect = -Infinity;
    const parityCounts = { even: 0, odd: 0 };
    for (const state of states) {
      const result = wiseMenColorCountEvaluate({ ...params, colors: state.colors });
      minCorrect = Math.min(minCorrect, result.correctCount);
      maxCorrect = Math.max(maxCorrect, result.correctCount);
      if (result.parity === 0) parityCounts.even += 1;
      if (result.parity === 1) parityCounts.odd += 1;
      if (!result.success) failures.push({ state, result });
    }
    return {
      success: failures.length === 0 && states.length > 0,
      checked: states.length,
      targetCorrectMin,
      minCorrect: Number.isFinite(minCorrect) ? minCorrect : 0,
      maxCorrect: Number.isFinite(maxCorrect) ? maxCorrect : 0,
      parityCounts,
      failures
    };
  }

  const THREE_LETTER_DEFAULT_ALPHABET = ['А', 'Б', 'В'];

  function threeLetterErasureAlphabet(params = {}) {
    const raw = Array.isArray(params.alphabet) && params.alphabet.length === 3 ? params.alphabet : THREE_LETTER_DEFAULT_ALPHABET;
    const alphabet = raw.map(letter => String(letter || '').trim()).filter(letter => [...letter].length === 1);
    return alphabet.length === 3 && new Set(alphabet).size === 3 ? alphabet : [...THREE_LETTER_DEFAULT_ALPHABET];
  }

  function threeLetterErasureNormalizeCodeword(word, params = {}) {
    const alphabet = threeLetterErasureAlphabet(params);
    const map = new Map([
      ['A', alphabet[0]], ['a', alphabet[0]], ['А', alphabet[0]], ['а', alphabet[0]],
      ['B', alphabet[1]], ['b', alphabet[1]], ['Б', alphabet[1]], ['б', alphabet[1]],
      ['C', alphabet[2]], ['c', alphabet[2]], ['V', alphabet[2]], ['v', alphabet[2]],
      ['В', alphabet[2]], ['в', alphabet[2]]
    ]);
    return [...String(word ?? '')]
      .filter(char => !/\s|[,;:|]/.test(char))
      .map(char => map.get(char) || char)
      .join('');
  }

  function threeLetterErasureNormalizeCodewords(params = {}) {
    const wordLength = Number(params.word_length ?? params.wordLength ?? 8);
    const messageCount = Number(params.message_count ?? params.messageCount ?? 16);
    const words = Array.isArray(params.codewords) ? params.codewords : [];
    return words.slice(0, Number.isInteger(messageCount) ? messageCount : words.length)
      .map(word => threeLetterErasureNormalizeCodeword(word, params))
      .filter(word => !Number.isInteger(wordLength) || word.length <= Math.max(wordLength, word.length));
  }

  function threeLetterErasureErase(word, letter) {
    return [...String(word ?? '')].filter(char => char !== letter).join('');
  }

  function threeLetterErasureObservationRows(params = {}) {
    const alphabet = threeLetterErasureAlphabet(params);
    const codewords = threeLetterErasureNormalizeCodewords(params);
    const rows = [];
    for (let message = 0; message < codewords.length; message += 1) {
      for (const erased of alphabet) {
        rows.push({
          message,
          codeword: codewords[message],
          erased,
          observed: threeLetterErasureErase(codewords[message], erased)
        });
      }
    }
    return rows;
  }

  function threeLetterErasureDecode(params = {}) {
    const observed = threeLetterErasureNormalizeCodeword(params.observed ?? params.observation ?? params.remaining ?? '', params);
    const matches = [];
    for (const row of threeLetterErasureObservationRows(params)) {
      if (row.observed === observed) matches.push(row);
    }
    return {
      observed,
      matches,
      messages: [...new Set(matches.map(row => row.message))]
    };
  }

  function threeLetterErasureCheckTable(params = {}) {
    const alphabet = threeLetterErasureAlphabet(params);
    const messageCount = Number(params.message_count ?? params.messageCount ?? 16);
    const wordLength = Number(params.word_length ?? params.wordLength ?? 8);
    const codewords = threeLetterErasureNormalizeCodewords(params);
    const errors = [];
    const conflicts = [];
    if (!Number.isInteger(messageCount) || messageCount < 1) errors.push('message_count must be a positive integer');
    if (!Number.isInteger(wordLength) || wordLength < 1) errors.push('word_length must be a positive integer');
    if (codewords.length !== messageCount) errors.push(`expected ${messageCount} codewords, got ${codewords.length}`);
    const allowed = new Set(alphabet);
    const seenWords = new Set();
    for (let index = 0; index < codewords.length; index += 1) {
      const word = codewords[index];
      if (word.length !== wordLength) errors.push(`message ${index}: word length is ${word.length}, expected ${wordLength}`);
      const bad = [...new Set([...word].filter(char => !allowed.has(char)))];
      if (bad.length) errors.push(`message ${index}: unexpected letters ${bad.join('')}`);
      if (seenWords.has(word)) errors.push(`duplicate codeword ${word}`);
      seenWords.add(word);
    }
    const byObserved = new Map();
    for (const row of threeLetterErasureObservationRows({ ...params, codewords })) {
      if (!byObserved.has(row.observed)) byObserved.set(row.observed, []);
      byObserved.get(row.observed).push(row);
    }
    for (const [observed, rows] of byObserved.entries()) {
      const messages = [...new Set(rows.map(row => row.message))];
      if (messages.length > 1) conflicts.push({ observed, rows, messages });
    }
    return {
      ok: errors.length === 0 && conflicts.length === 0,
      success: errors.length === 0 && conflicts.length === 0,
      alphabet,
      messageCount,
      wordLength,
      codewords,
      rows: threeLetterErasureObservationRows({ ...params, codewords }),
      observationCount: byObserved.size,
      checked: codewords.length * alphabet.length,
      errors,
      conflicts,
      decodedByObserved: Object.fromEntries([...byObserved.entries()].map(([observed, rows]) => [observed, [...new Set(rows.map(row => row.message))]]))
    };
  }

  function threeLetterErasureEvaluate(params = {}) {
    const alphabet = threeLetterErasureAlphabet(params);
    const codewords = threeLetterErasureNormalizeCodewords(params);
    const message = Number(params.message ?? params.hiddenMessage ?? params.hidden_message ?? 0);
    const erased = params.erased ?? params.erasedLetter ?? params.erased_letter ?? alphabet[0];
    const guess = Number(params.guess ?? params.answer);
    const codeword = codewords[message] || '';
    const observed = threeLetterErasureErase(codeword, erased);
    const decoded = threeLetterErasureDecode({ ...params, codewords, observed });
    return {
      message,
      codeword,
      erased,
      observed,
      guess,
      decoded,
      candidates: decoded.messages,
      win: Number.isInteger(guess) && guess === message && decoded.messages.length === 1
    };
  }

  function permutationMessageItemCount(params = {}) {
    const count = Number(params.item_count ?? params.itemCount ?? 3);
    return Number.isInteger(count) && count >= 1 && count <= 6 ? count : 3;
  }

  function permutationMessageLabels(params = {}) {
    const count = permutationMessageItemCount(params);
    const fallback = ['A', 'B', 'C', 'D', 'E', 'F'].slice(0, count);
    const labels = Array.isArray(params.object_labels ?? params.objectLabels)
      ? (params.object_labels ?? params.objectLabels).map(label => String(label || '').trim()).filter(Boolean).slice(0, count)
      : [];
    return labels.length === count && new Set(labels).size === count ? labels : fallback;
  }

  function permutationMessagePermutations(params = {}) {
    const count = permutationMessageItemCount(params);
    const source = Array.from({ length: count }, (_item, index) => index);
    const result = [];
    function visit(prefix, remaining) {
      if (!remaining.length) {
        result.push(prefix);
        return;
      }
      for (let index = 0; index < remaining.length; index += 1) {
        visit([...prefix, remaining[index]], remaining.filter((_item, itemIndex) => itemIndex !== index));
      }
    }
    visit([], source);
    return result;
  }

  function permutationMessageTable(params = {}) {
    const labels = permutationMessageLabels(params);
    const messageCount = Number(params.message_count ?? params.messageCount ?? 6);
    return permutationMessagePermutations(params)
      .slice(0, Number.isInteger(messageCount) && messageCount > 0 ? messageCount : 6)
      .map((order, message) => ({
        message,
        order,
        labels: order.map(index => labels[index]),
        key: order.join(',')
      }));
  }

  function permutationMessageNormalizeOrder(order, params = {}) {
    const labels = permutationMessageLabels(params);
    let raw = [];
    if (Array.isArray(order)) {
      raw = order;
    } else if (typeof order === 'string') {
      const trimmed = order.trim();
      const compactLabels = labels.every(label => [...label].length === 1);
      raw = /[,;\s|>-]/.test(trimmed)
        ? trimmed.split(/[,;\s|>-]+/).filter(Boolean)
        : (compactLabels ? [...trimmed].filter(Boolean) : [trimmed]);
    }
    const used = new Set();
    const normalized = [];
    for (const value of raw) {
      let index = null;
      if (typeof value === 'number' && Number.isInteger(value) && value >= 0 && value < labels.length) {
        index = value;
      } else {
        const numeric = Number(value);
        if (Number.isInteger(numeric) && numeric >= 1 && numeric <= labels.length) index = numeric - 1;
        else index = labels.indexOf(String(value));
      }
      if (!Number.isInteger(index) || index < 0 || index >= labels.length || used.has(index)) return [];
      used.add(index);
      normalized.push(index);
    }
    return normalized.length === labels.length ? normalized : [];
  }

  function permutationMessageEncode(message, params = {}) {
    const table = permutationMessageTable(params);
    const index = Number(message);
    return Number.isInteger(index) && table[index] ? table[index] : null;
  }

  function permutationMessageDecode(order, params = {}) {
    const normalized = permutationMessageNormalizeOrder(order, params);
    if (!normalized.length) return { message: null, order: normalized, row: null };
    const key = normalized.join(',');
    const row = permutationMessageTable(params).find(item => item.key === key) || null;
    return { message: row ? row.message : null, order: normalized, row };
  }

  function permutationMessageEvaluate(params = {}) {
    const direction = params.direction === 'decode' ? 'decode' : 'encode';
    const message = Number(params.message ?? params.hiddenMessage ?? params.hidden_message ?? 0);
    const order = permutationMessageNormalizeOrder(params.order ?? params.permutation ?? [], params);
    const guess = Number(params.guess ?? params.answer);
    const encoded = permutationMessageEncode(message, params);
    const decoded = permutationMessageDecode(order, params);
    const expectedKey = encoded ? encoded.key : '';
    const orderKey = order.join(',');
    return {
      direction,
      message,
      order,
      orderLabels: order.map(index => permutationMessageLabels(params)[index]),
      expected: encoded,
      decoded,
      guess,
      win: direction === 'decode'
        ? Number.isInteger(guess) && guess === decoded.message
        : !!encoded && orderKey === expectedKey
    };
  }

  function permutationMessageExhaustiveCheck(params = {}) {
    const labels = permutationMessageLabels(params);
    const table = permutationMessageTable(params);
    const messageCount = Number(params.message_count ?? params.messageCount ?? 6);
    const errors = [];
    const failures = [];
    if (labels.length !== 3) errors.push('item_count must be 3');
    if (messageCount !== 6) errors.push('message_count must be 6');
    const seen = new Map();
    for (const row of table) {
      if (seen.has(row.key)) failures.push({ message: row.message, duplicateOf: seen.get(row.key), order: row.labels });
      seen.set(row.key, row.message);
      const decoded = permutationMessageDecode(row.order, params);
      if (decoded.message !== row.message) failures.push({ message: row.message, decoded: decoded.message, order: row.labels });
    }
    return {
      ok: errors.length === 0 && failures.length === 0 && table.length === 6 && seen.size === 6,
      success: errors.length === 0 && failures.length === 0 && table.length === 6 && seen.size === 6,
      checked: table.length,
      labels,
      table,
      errors,
      failures
    };
  }

  function permutationCycleCount(params = {}) {
    const count = Number(params.prisoner_count ?? params.prisonerCount ?? params.box_count ?? params.boxCount ?? 10);
    if (!Number.isInteger(count) || count < 2 || count > 12) return 0;
    return count;
  }

  function permutationCycleMaxOpenings(params = {}) {
    const count = permutationCycleCount(params);
    const maxOpenings = Number(params.max_openings ?? params.maxOpenings ?? Math.floor(count / 2));
    if (!Number.isInteger(maxOpenings) || maxOpenings < 1 || maxOpenings > count) return 0;
    return maxOpenings;
  }

  function permutationCycleNormalizePermutation(permutation, count = null) {
    const size = count ?? permutationCycleCount({ prisoner_count: Array.isArray(permutation) ? permutation.length : 0 });
    if (!Number.isInteger(size) || size < 2) return [];
    if (!Array.isArray(permutation) || permutation.length !== size) return [];
    const seen = new Set();
    const result = [];
    for (const raw of permutation) {
      const value = Number(raw);
      if (!Number.isInteger(value) || value < 1 || value > size || seen.has(value)) return [];
      seen.add(value);
      result.push(value);
    }
    return result;
  }

  function permutationCycleRandomPermutation(count) {
    const size = Number(count);
    if (!Number.isInteger(size) || size < 2) return [];
    const result = Array.from({ length: size }, (_item, index) => index + 1);
    for (let index = result.length - 1; index > 0; index -= 1) {
      const swapIndex = Math.floor(Math.random() * (index + 1));
      [result[index], result[swapIndex]] = [result[swapIndex], result[index]];
    }
    return result;
  }

  function permutationCycleCheaterPermutation(count, maxOpenings) {
    const size = Number(count);
    const limit = Number(maxOpenings);
    if (!Number.isInteger(size) || !Number.isInteger(limit) || size < 2 || limit < 1 || limit >= size) {
      return permutationCycleRandomPermutation(size);
    }
    const longCycleLength = Math.min(size, limit + 1);
    const result = Array.from({ length: size }, (_item, index) => index + 1);
    for (let value = 1; value <= longCycleLength; value += 1) {
      result[value - 1] = value === longCycleLength ? 1 : value + 1;
    }
    return result;
  }

  function permutationCycleDecomposition(permutation) {
    const perm = permutationCycleNormalizePermutation(permutation);
    const count = perm.length;
    const visited = Array(count + 1).fill(false);
    const cycles = [];
    for (let start = 1; start <= count; start += 1) {
      if (visited[start]) continue;
      const cycle = [];
      let current = start;
      while (!visited[current]) {
        visited[current] = true;
        cycle.push(current);
        current = perm[current - 1];
      }
      cycles.push(cycle);
    }
    cycles.sort((first, second) => second.length - first.length || first[0] - second[0]);
    return cycles;
  }

  function permutationCycleTrace(permutation, prisoner, maxOpenings) {
    const perm = permutationCycleNormalizePermutation(permutation);
    const count = perm.length;
    const target = Number(prisoner);
    const limit = Number(maxOpenings);
    if (!count || !Number.isInteger(target) || target < 1 || target > count || !Number.isInteger(limit) || limit < 1) {
      return { prisoner: target, openings: [], found: false, stoppedByLimit: true };
    }
    const openings = [];
    let box = target;
    for (let step = 1; step <= Math.min(limit, count); step += 1) {
      const value = perm[box - 1];
      openings.push({ step, box, value, found: value === target });
      if (value === target) return { prisoner: target, openings, found: true, stoppedByLimit: false };
      box = value;
    }
    return { prisoner: target, openings, found: false, stoppedByLimit: true };
  }

  function permutationCycleRunAll(permutation, maxOpenings) {
    const perm = permutationCycleNormalizePermutation(permutation);
    const traces = Array.from({ length: perm.length }, (_item, index) =>
      permutationCycleTrace(perm, index + 1, maxOpenings)
    );
    const cycles = permutationCycleDecomposition(perm);
    const maxCycleLength = cycles.reduce((max, cycle) => Math.max(max, cycle.length), 0);
    return {
      permutation: perm,
      traces,
      cycles,
      maxCycleLength,
      success: traces.every(trace => trace.found),
      failingPrisoners: traces.filter(trace => !trace.found).map(trace => trace.prisoner)
    };
  }

  function permutationCycleFactorials(count) {
    const factorials = [1];
    for (let index = 1; index <= count; index += 1) factorials[index] = factorials[index - 1] * index;
    return factorials;
  }

  function permutationCycleTypeStatistics(count, maxOpenings) {
    const size = Number(count);
    const limit = Number(maxOpenings);
    if (!Number.isInteger(size) || size < 2 || !Number.isInteger(limit) || limit < 1) {
      return { total: 0, successCount: 0, failureCount: 0, rows: [] };
    }
    const factorials = permutationCycleFactorials(size);
    const rows = [];
    function visit(remaining, maxPart, parts) {
      if (remaining === 0) {
        const multiplicities = {};
        for (const part of parts) multiplicities[part] = (multiplicities[part] || 0) + 1;
        let denominator = 1;
        for (const [partText, amount] of Object.entries(multiplicities)) {
          const part = Number(partText);
          denominator *= (part ** amount) * factorials[amount];
        }
        const maxCycle = Math.max(...parts);
        const countForType = factorials[size] / denominator;
        rows.push({
          parts: parts.slice(),
          type: parts.join('+'),
          maxCycle,
          count: countForType,
          success: maxCycle <= limit
        });
        return;
      }
      for (let part = Math.min(remaining, maxPart); part >= 1; part -= 1) {
        parts.push(part);
        visit(remaining - part, part, parts);
        parts.pop();
      }
    }
    visit(size, size, []);
    rows.sort((first, second) => first.maxCycle - second.maxCycle || first.type.localeCompare(second.type));
    const total = rows.reduce((sum, row) => sum + row.count, 0);
    const successCount = rows.filter(row => row.success).reduce((sum, row) => sum + row.count, 0);
    return {
      total,
      successCount,
      failureCount: total - successCount,
      probability: total ? successCount / total : 0,
      rows
    };
  }

  function prisonerHatsParityPersonCount(params = {}) {
    const count = Number(params.person_count ?? params.personCount ?? params.prisoner_count ?? params.prisonerCount ?? 6);
    return Number.isInteger(count) && count >= 2 && count <= 10 ? count : 0;
  }

  function prisonerHatsParityColorCount(params = {}) {
    const count = Number(params.color_count ?? params.colorCount ?? 2);
    return count === 2 ? 2 : 0;
  }

  function prisonerHatsParityNormalizeBit(value) {
    if (value === true) return 1;
    if (value === false) return 0;
    const text = String(value ?? '').trim().toLowerCase();
    if (text === 'black' || text === 'b' || text === '1') return 1;
    if (text === 'white' || text === 'w' || text === '0') return 0;
    const number = Number(value);
    return Number.isInteger(number) && (number === 0 || number === 1) ? number : null;
  }

  function prisonerHatsParityNormalizeBits(values, expectedLength = null) {
    const source = Array.isArray(values) ? values : [];
    const result = source.map(prisonerHatsParityNormalizeBit).filter(value => value != null);
    return expectedLength == null ? result : result.slice(0, expectedLength);
  }

  function prisonerHatsParityStateKey(state) {
    return (state?.hats || []).join('');
  }

  function prisonerHatsParityInitialStates(params = {}) {
    const count = prisonerHatsParityPersonCount(params);
    if (!count || !prisonerHatsParityColorCount(params)) return [];
    const total = 2 ** count;
    const states = [];
    for (let mask = 0; mask < total; mask += 1) {
      const hats = Array.from({ length: count }, (_item, index) => (mask >> (count - index - 1)) & 1);
      states.push({
        id: hats.join(''),
        hats,
        blackCount: hats.reduce((sum, bit) => sum + bit, 0)
      });
    }
    return states;
  }

  function prisonerHatsParityNormalizeState(raw, params = {}) {
    const count = prisonerHatsParityPersonCount(params);
    if (!count || !prisonerHatsParityColorCount(params)) return null;
    const rawHats = raw?.hats ?? raw?.colors ?? raw;
    const hats = prisonerHatsParityNormalizeBits(rawHats, count);
    if (hats.length !== count) return null;
    return {
      id: hats.join(''),
      hats,
      blackCount: hats.reduce((sum, bit) => sum + bit, 0)
    };
  }

  function prisonerHatsParityRandomState(params = {}, random = Math.random) {
    const states = prisonerHatsParityInitialStates(params);
    return states[Math.floor(random() * states.length)] || null;
  }

  function prisonerHatsParityVisibleAhead(state, prisonerIndex) {
    const hats = Array.isArray(state?.hats) ? state.hats : [];
    return hats.slice(Number(prisonerIndex) + 1);
  }

  function prisonerHatsParityBitSum(bits) {
    return (bits || []).reduce((sum, bit) => sum + (bit ? 1 : 0), 0);
  }

  function prisonerHatsParityExpectedAnswer(params = {}) {
    const count = prisonerHatsParityPersonCount(params);
    const prisonerIndex = Number(params.prisonerIndex ?? params.prisoner_index ?? params.sageIndex ?? params.sage_index ?? 0);
    const state = prisonerHatsParityNormalizeState(params.state ?? params.hiddenState ?? params.hidden_state, params);
    const visibleAhead = state
      ? prisonerHatsParityVisibleAhead(state, prisonerIndex)
      : prisonerHatsParityNormalizeBits(params.visibleAhead ?? params.visible_ahead);
    const previousAnswers = prisonerHatsParityNormalizeBits(params.previousAnswers ?? params.previous_answers ?? []);
    if (!count || !Number.isInteger(prisonerIndex) || prisonerIndex < 0 || prisonerIndex >= count) return null;
    if (visibleAhead.length !== count - prisonerIndex - 1 || previousAnswers.length !== prisonerIndex) return null;
    const visibleParity = prisonerHatsParityBitSum(visibleAhead) % 2;
    if (prisonerIndex === 0) {
      return {
        prisonerIndex,
        prisoner: prisonerIndex + 1,
        answer: visibleParity,
        signal: visibleParity,
        visibleAhead,
        visibleParity,
        previousParity: 0
      };
    }
    const signal = previousAnswers[0];
    const previousParity = prisonerHatsParityBitSum(previousAnswers.slice(1)) % 2;
    return {
      prisonerIndex,
      prisoner: prisonerIndex + 1,
      answer: signal ^ previousParity ^ visibleParity,
      signal,
      visibleAhead,
      visibleParity,
      previousParity
    };
  }

  function prisonerHatsParityProtocolTranscript(state, params = {}) {
    const normalized = prisonerHatsParityNormalizeState(state, params);
    const count = prisonerHatsParityPersonCount(params);
    if (!normalized || !count) return [];
    const answers = [];
    for (let prisonerIndex = 0; prisonerIndex < count; prisonerIndex += 1) {
      const step = prisonerHatsParityExpectedAnswer({
        ...params,
        state: normalized,
        prisonerIndex,
        previousAnswers: answers
      });
      if (!step) return [];
      answers.push(step.answer);
    }
    return answers;
  }

  function prisonerHatsParityEvaluateTranscript(params = {}) {
    const state = prisonerHatsParityNormalizeState(params.state ?? params.hiddenState ?? params.hidden_state, params);
    const count = prisonerHatsParityPersonCount(params);
    const answers = prisonerHatsParityNormalizeBits(params.answers ?? params.transcript ?? [], count);
    const rows = [];
    const previous = [];
    if (!state || !count) {
      return { success: false, rows, correctCount: 0, protocolOk: false, allButFirstCorrect: false };
    }
    for (let prisonerIndex = 0; prisonerIndex < Math.min(count, answers.length); prisonerIndex += 1) {
      const step = prisonerHatsParityExpectedAnswer({
        ...params,
        state,
        prisonerIndex,
        previousAnswers: previous
      });
      const answer = answers[prisonerIndex];
      const actualHat = state.hats[prisonerIndex];
      rows.push({
        prisonerIndex,
        prisoner: prisonerIndex + 1,
        answer,
        expected: step?.answer ?? null,
        actualHat,
        visibleAhead: prisonerHatsParityVisibleAhead(state, prisonerIndex),
        signal: step?.signal ?? null,
        visibleParity: step?.visibleParity ?? null,
        previousParity: step?.previousParity ?? null,
        protocolOk: !!step && answer === step.answer,
        correctHat: answer === actualHat
      });
      previous.push(answer);
    }
    const complete = rows.length === count;
    const protocolOk = complete && rows.every(row => row.protocolOk);
    const correctCount = rows.filter(row => row.correctHat).length;
    const allButFirstCorrect = complete && rows.slice(1).every(row => row.correctHat);
    return {
      success: complete && allButFirstCorrect,
      protocolOk,
      allButFirstCorrect,
      correctCount,
      rows,
      state,
      answers
    };
  }

  function prisonerHatsParityExhaustiveCheck(params = {}) {
    const states = prisonerHatsParityInitialStates(params);
    const rows = states.map(state => {
      const answers = prisonerHatsParityProtocolTranscript(state, params);
      const evaluation = prisonerHatsParityEvaluateTranscript({ ...params, state, answers });
      return {
        state,
        answers,
        correctCount: evaluation.correctCount,
        success: evaluation.success,
        protocolOk: evaluation.protocolOk,
        firstCorrect: evaluation.rows[0]?.correctHat === true
      };
    });
    const failures = rows.filter(row => !row.success || !row.protocolOk);
    return {
      success: failures.length === 0 && rows.length > 0,
      checked: rows.length,
      minCorrect: rows.length ? Math.min(...rows.map(row => row.correctCount)) : 0,
      maxCorrect: rows.length ? Math.max(...rows.map(row => row.correctCount)) : 0,
      firstCorrectCount: rows.filter(row => row.firstCorrect).length,
      failures,
      rows
    };
  }

  function hiddenHatParitySageCount(params = {}) {
    const count = Number(params.sage_count ?? params.sageCount ?? params.agent_count ?? params.agentCount ?? 6);
    return Number.isInteger(count) && count >= 2 && count <= 8 ? count : 0;
  }

  function hiddenHatParityNumbers(params = {}) {
    const count = hiddenHatParitySageCount(params);
    const min = Number(params.number_min ?? params.numberMin ?? 1);
    const max = Number(params.number_max ?? params.numberMax ?? (Number.isInteger(min) ? min + count : 7));
    if (!count || !Number.isInteger(min) || !Number.isInteger(max) || max - min + 1 !== count + 1) return [];
    return Array.from({ length: count + 1 }, (_item, index) => min + index);
  }

  function hiddenHatParityTarget(params = {}) {
    return String(params.target_parity ?? params.targetParity ?? 'even').toLowerCase() === 'odd' ? 1 : 0;
  }

  function hiddenHatParityPermutationParity(values) {
    let inversions = 0;
    for (let i = 0; i < values.length; i += 1) {
      for (let j = i + 1; j < values.length; j += 1) {
        if (values[i] > values[j]) inversions += 1;
      }
    }
    return inversions % 2;
  }

  function hiddenHatParityStateKey(state) {
    return `${state?.hidden}|${(state?.hats || []).join(',')}`;
  }

  function hiddenHatParityInitialStates(params = {}) {
    const numbers = hiddenHatParityNumbers(params);
    if (!numbers.length) return [];
    return permutations(numbers).map(order => ({
      id: `${order[0]}|${order.slice(1).join(',')}`,
      hidden: order[0],
      hats: order.slice(1),
      parity: hiddenHatParityPermutationParity(order)
    }));
  }

  function hiddenHatParityNormalizeState(raw, params = {}) {
    const count = hiddenHatParitySageCount(params);
    const allowed = new Set(hiddenHatParityNumbers(params));
    const hidden = Number(raw?.hidden ?? raw?.hiddenNumber ?? raw?.hidden_number);
    const hats = (raw?.hats ?? raw?.hatNumbers ?? raw?.hat_numbers ?? [])
      .map(Number)
      .filter(Number.isInteger);
    if (!count || hats.length !== count || !allowed.has(hidden)) return null;
    const seen = new Set([hidden]);
    for (const hat of hats) {
      if (!allowed.has(hat) || seen.has(hat)) return null;
      seen.add(hat);
    }
    const order = [hidden, ...hats];
    return {
      id: `${hidden}|${hats.join(',')}`,
      hidden,
      hats,
      parity: hiddenHatParityPermutationParity(order)
    };
  }

  function hiddenHatParityRandomState(params = {}, random = Math.random) {
    const states = hiddenHatParityInitialStates(params);
    return states[Math.floor(random() * states.length)] || null;
  }

  function hiddenHatParityExpectedAnswer(params = {}) {
    const count = hiddenHatParitySageCount(params);
    const numbers = hiddenHatParityNumbers(params);
    const sageIndex = Number(params.sageIndex ?? params.sage_index ?? 0);
    const previousAnswers = (params.previousAnswers ?? params.previous_answers ?? [])
      .map(Number)
      .filter(Number.isInteger);
    const visibleAhead = (params.visibleAhead ?? params.visible_ahead ?? [])
      .map(Number)
      .filter(Number.isInteger);
    if (!count || !Number.isInteger(sageIndex) || sageIndex < 0 || sageIndex >= count) return null;
    if (previousAnswers.length !== sageIndex || visibleAhead.length !== count - sageIndex - 1) return null;
    const used = [...previousAnswers, ...visibleAhead];
    if (new Set(used).size !== used.length) return null;
    const remaining = numbers.filter(number => !used.includes(number));
    if (remaining.length !== 2) return null;
    const target = hiddenHatParityTarget(params);
    const options = [
      { own: remaining[0], hidden: remaining[1] },
      { own: remaining[1], hidden: remaining[0] }
    ].map(option => {
      const order = [option.hidden, ...previousAnswers, option.own, ...visibleAhead];
      return {
        ...option,
        order,
        parity: hiddenHatParityPermutationParity(order)
      };
    });
    const selected = options.find(option => option.parity === target) || null;
    return selected ? {
      sageIndex,
      answer: selected.own,
      hidden: selected.hidden,
      remaining,
      parity: selected.parity,
      order: selected.order,
      alternatives: options
    } : null;
  }

  function hiddenHatParityVisibleAhead(state, sageIndex) {
    const hats = Array.isArray(state?.hats) ? state.hats : [];
    return hats.slice(Number(sageIndex) + 1);
  }

  function hiddenHatParityProtocolTranscript(state, params = {}) {
    const normalized = hiddenHatParityNormalizeState(state, params);
    const count = hiddenHatParitySageCount(params);
    if (!normalized || !count) return [];
    const answers = [];
    for (let sageIndex = 0; sageIndex < count; sageIndex += 1) {
      const step = hiddenHatParityExpectedAnswer({
        ...params,
        sageIndex,
        previousAnswers: answers,
        visibleAhead: hiddenHatParityVisibleAhead(normalized, sageIndex)
      });
      if (!step) return [];
      answers.push(step.answer);
    }
    return answers;
  }

  function hiddenHatParityEvaluateTranscript(params = {}) {
    const state = hiddenHatParityNormalizeState(params.state ?? params.hiddenState ?? params.hidden_state, params);
    const count = hiddenHatParitySageCount(params);
    const answers = (params.answers ?? params.transcript ?? [])
      .map(Number)
      .filter(Number.isInteger)
      .slice(0, count);
    const rows = [];
    const previous = [];
    const spoken = new Set();
    if (!state || !count) {
      return { success: false, rows, correctCount: 0, protocolOk: false, allButFirstCorrect: false };
    }
    for (let sageIndex = 0; sageIndex < Math.min(count, answers.length); sageIndex += 1) {
      const step = hiddenHatParityExpectedAnswer({
        ...params,
        sageIndex,
        previousAnswers: previous,
        visibleAhead: hiddenHatParityVisibleAhead(state, sageIndex)
      });
      const answer = answers[sageIndex];
      const repeated = spoken.has(answer);
      const actualHat = state.hats[sageIndex];
      rows.push({
        sageIndex,
        sage: sageIndex + 1,
        answer,
        expected: step?.answer ?? null,
        actualHat,
        visibleAhead: hiddenHatParityVisibleAhead(state, sageIndex),
        repeated,
        protocolOk: !!step && answer === step.answer && !repeated,
        correctHat: answer === actualHat
      });
      previous.push(answer);
      spoken.add(answer);
    }
    const protocolOk = rows.length === count && rows.every(row => row.protocolOk);
    const correctCount = rows.filter(row => row.correctHat).length;
    const allButFirstCorrect = rows.length === count && rows.slice(1).every(row => row.correctHat);
    return {
      success: protocolOk && allButFirstCorrect,
      protocolOk,
      allButFirstCorrect,
      correctCount,
      rows,
      state,
      answers
    };
  }

  function hiddenHatParityExhaustiveCheck(params = {}) {
    const states = hiddenHatParityInitialStates(params);
    const rows = states.map(state => {
      const answers = hiddenHatParityProtocolTranscript(state, params);
      const evaluation = hiddenHatParityEvaluateTranscript({ ...params, state, answers });
      return {
        state,
        answers,
        correctCount: evaluation.correctCount,
        success: evaluation.success,
        firstCorrect: evaluation.rows[0]?.correctHat === true
      };
    });
    const failures = rows.filter(row => !row.success);
    return {
      success: failures.length === 0 && rows.length > 0,
      checked: rows.length,
      minCorrect: rows.length ? Math.min(...rows.map(row => row.correctCount)) : 0,
      maxCorrect: rows.length ? Math.max(...rows.map(row => row.correctCount)) : 0,
      firstCorrectCount: rows.filter(row => row.firstCorrect).length,
      failures,
      rows
    };
  }

  function initialScaleCandidates(labels) {
    return Array.isArray(labels) ? labels.map(String).filter(Boolean) : [];
  }

  function normalizeScaleOutcome(outcome) {
    const value = String(outcome || '');
    if (value === 'left_heavy') return 'left_down';
    if (value === 'right_heavy') return 'right_down';
    if (value === 'balanced') return 'balance';
    return OUTCOMES.includes(value) ? value : null;
  }

  function uniqueScaleLabels(labels, allowedLabels = null) {
    const allowed = allowedLabels ? new Set(allowedLabels.map(String)) : null;
    const seen = new Set();
    const result = [];
    for (const raw of labels || []) {
      const label = String(raw || '');
      if (!label || seen.has(label)) continue;
      if (allowed && !allowed.has(label)) continue;
      seen.add(label);
      result.push(label);
    }
    return result;
  }

  function faultyScaleOutcomeForCandidate(candidate, instrument, leftObjects, rightObjects) {
    const faulty = String(candidate || '');
    const device = String(instrument || '');
    if (!faulty || !device) return null;
    if (device === faulty) return 'arbitrary';
    const left = uniqueScaleLabels(leftObjects);
    const right = uniqueScaleLabels(rightObjects);
    const leftWeight = left.reduce((sum, label) => sum + (label === faulty ? 0 : 1), 0);
    const rightWeight = right.reduce((sum, label) => sum + (label === faulty ? 0 : 1), 0);
    if (leftWeight > rightWeight) return 'left_down';
    if (rightWeight > leftWeight) return 'right_down';
    return 'balance';
  }

  function faultyScaleFilterCandidates(params) {
    const scaleLabels = initialScaleCandidates(params?.scaleLabels ?? params?.scale_labels);
    const currentCandidates = uniqueScaleLabels(
      params?.currentCandidates?.length ? params.currentCandidates : scaleLabels,
      scaleLabels
    );
    const instrument = String(params?.instrument || '');
    const outcome = normalizeScaleOutcome(params?.outcome);
    if (!outcome) return [];
    return currentCandidates.filter(candidate => {
      const candidateOutcome = faultyScaleOutcomeForCandidate(
        candidate,
        instrument,
        params?.leftObjects ?? params?.left_objects,
        params?.rightObjects ?? params?.right_objects
      );
      return candidateOutcome === 'arbitrary' || candidateOutcome === outcome;
    });
  }

  function faultyScalePartitionCandidates(params) {
    return Object.fromEntries(OUTCOMES.map(outcome => [
      outcome,
      faultyScaleFilterCandidates({ ...params, outcome })
    ]));
  }

  function faultyScaleBranchStatus(candidates, usedWeighings, maxWeighings) {
    const remaining = uniqueScaleLabels(candidates);
    const used = Number(usedWeighings);
    const limit = Number(maxWeighings);
    if (remaining.length === 1) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function faultyScaleChooseCheaterOutcome(params) {
    const partitions = faultyScalePartitionCandidates(params || {});
    const history = Array.isArray(params?.history) ? params.history : [];
    const maxSize = Math.max(...OUTCOMES.map(outcome => partitions[outcome].length));
    const tied = OUTCOMES.filter(outcome => partitions[outcome].length === maxSize);
    const frequencies = Object.fromEntries(OUTCOMES.map(outcome => [outcome, 0]));
    for (const entry of history) {
      const outcome = normalizeScaleOutcome(typeof entry === 'string' ? entry : entry?.outcome);
      if (outcome in frequencies) frequencies[outcome] += 1;
    }
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

  function faultyScaleExpandExhaustiveNode(params) {
    const scaleLabels = initialScaleCandidates(params?.scaleLabels ?? params?.scale_labels);
    const currentCandidates = uniqueScaleLabels(
      params?.currentCandidates?.length ? params.currentCandidates : scaleLabels,
      scaleLabels
    );
    const usedWeighings = Number(params?.usedWeighings ?? params?.used_weighings ?? 0);
    const maxWeighings = Number(params?.maxWeighings ?? params?.max_weighings);
    const partitions = faultyScalePartitionCandidates({
      ...params,
      currentCandidates,
      scaleLabels
    });
    const children = OUTCOMES
      .map(outcome => {
        const candidates = partitions[outcome];
        return {
          outcome,
          label: OUTCOME_LABELS[outcome],
          candidates,
          usedWeighings: usedWeighings + 1,
          status: faultyScaleBranchStatus(candidates, usedWeighings + 1, maxWeighings)
        };
      })
      .filter(child => child.candidates.length > 0);
    return { partitions, children };
  }

  function faultyScaleFinalizeAnswer(params) {
    const scaleLabels = initialScaleCandidates(params?.scaleLabels ?? params?.scale_labels);
    const candidates = uniqueScaleLabels(
      params?.currentCandidates?.length ? params.currentCandidates : scaleLabels,
      scaleLabels
    );
    const selectedScale = String(params?.selectedScale || '');
    if (candidates.length === 1) {
      const actualScale = candidates[0];
      return { win: actualScale === selectedScale, actualScale, candidates };
    }
    const actualScale = candidates.find(candidate => candidate !== selectedScale) ?? candidates[0] ?? null;
    return { win: false, actualScale, candidates };
  }

  function initialBrokenScaleCoinCandidates(coinCount, labels) {
    const count = Number(coinCount);
    const scaleLabels = initialScaleCandidates(labels);
    if (!Number.isInteger(count) || count < 1 || !scaleLabels.length) return [];
    const result = [];
    for (let coin = 1; coin <= count; coin += 1) {
      for (const brokenScale of scaleLabels) result.push({ coin, brokenScale });
    }
    return result;
  }

  function brokenScaleCoinCandidateKey(candidate) {
    return `${candidate.coin}:${candidate.brokenScale}`;
  }

  function normalizeBrokenScaleCoinCandidates(candidates, coinCount, labels) {
    const count = Number(coinCount);
    const scaleLabels = initialScaleCandidates(labels);
    const allowedScales = new Set(scaleLabels);
    const seen = new Set();
    const result = [];
    for (const raw of candidates || []) {
      const coin = Number(raw?.coin ?? raw?.id ?? raw?.[0]);
      const brokenScale = String(raw?.brokenScale ?? raw?.broken_scale ?? raw?.scale ?? raw?.[1] ?? '');
      if (!Number.isInteger(coin) || coin < 1 || coin > count || !allowedScales.has(brokenScale)) continue;
      const key = `${coin}:${brokenScale}`;
      if (seen.has(key)) continue;
      seen.add(key);
      result.push({ coin, brokenScale });
    }
    return result;
  }

  function outcomeForKnownCounterfeitWithCounts(candidate, counterfeitWeight, leftCoins, rightCoins, options = {}) {
    const weight = normalizeWeight(counterfeitWeight);
    if (!weight) return null;
    const leftList = uniqueCoins(leftCoins);
    const rightList = uniqueCoins(rightCoins);
    if (options.requireEqualPanCounts !== false && leftList.length !== rightList.length) return null;
    const left = new Set(leftList);
    const right = new Set(rightList);
    if (left.has(candidate) && right.has(candidate)) return null;
    let leftWeight = leftList.length;
    let rightWeight = rightList.length;
    const delta = weight === 'heavy' ? 1 : -1;
    if (left.has(candidate)) leftWeight += delta;
    if (right.has(candidate)) rightWeight += delta;
    if (leftWeight > rightWeight) return 'left_down';
    if (rightWeight > leftWeight) return 'right_down';
    return 'balance';
  }

  function brokenScaleCoinOutcomeForCandidate(candidate, instrument, counterfeitWeight, leftCoins, rightCoins, options = {}) {
    const state = normalizeBrokenScaleCoinCandidates([candidate], options.coinCount ?? options.coin_count, options.scaleLabels ?? options.scale_labels)[0];
    const device = String(instrument || '');
    if (!state || !device) return null;
    if (device === state.brokenScale) return 'arbitrary';
    return outcomeForKnownCounterfeitWithCounts(state.coin, counterfeitWeight, leftCoins, rightCoins, options);
  }

  function brokenScaleCoinFilterCandidates(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const scaleLabels = initialScaleCandidates(params?.scaleLabels ?? params?.scale_labels);
    const currentCandidates = normalizeBrokenScaleCoinCandidates(
      params?.currentCandidates?.length
        ? params.currentCandidates
        : initialBrokenScaleCoinCandidates(coinCount, scaleLabels),
      coinCount,
      scaleLabels
    );
    const instrument = String(params?.instrument || '');
    const outcome = normalizeScaleOutcome(params?.outcome);
    if (!outcome) return [];
    return currentCandidates.filter(candidate => {
      const candidateOutcome = brokenScaleCoinOutcomeForCandidate(
        candidate,
        instrument,
        params?.counterfeit_weight ?? params?.counterfeitWeight,
        params?.leftCoins ?? params?.left_coins,
        params?.rightCoins ?? params?.right_coins,
        {
          coinCount,
          scaleLabels,
          requireEqualPanCounts: params?.requireEqualPanCounts ?? params?.require_equal_pan_counts
        }
      );
      return candidateOutcome === 'arbitrary' || candidateOutcome === outcome;
    });
  }

  function brokenScaleCoinPartitionCandidates(params) {
    return Object.fromEntries(OUTCOMES.map(outcome => [
      outcome,
      brokenScaleCoinFilterCandidates({ ...params, outcome })
    ]));
  }

  function uniqueCandidateCoins(candidates) {
    return [...new Set((candidates || []).map(candidate => Number(candidate?.coin)).filter(Number.isInteger))];
  }

  function brokenScaleCoinBranchStatus(candidates, usedWeighings, maxWeighings) {
    const remainingCoins = uniqueCandidateCoins(candidates);
    const used = Number(usedWeighings);
    const limit = Number(maxWeighings);
    if (remainingCoins.length === 1) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function brokenScaleCoinChooseCheaterOutcome(params) {
    const partitions = brokenScaleCoinPartitionCandidates(params || {});
    const history = Array.isArray(params?.history) ? params.history : [];
    const maxSize = Math.max(...OUTCOMES.map(outcome => partitions[outcome].length));
    const tied = OUTCOMES.filter(outcome => partitions[outcome].length === maxSize);
    const frequencies = Object.fromEntries(OUTCOMES.map(outcome => [outcome, 0]));
    for (const entry of history) {
      const outcome = normalizeScaleOutcome(typeof entry === 'string' ? entry : entry?.outcome);
      if (outcome in frequencies) frequencies[outcome] += 1;
    }
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

  function brokenScaleCoinExpandExhaustiveNode(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const scaleLabels = initialScaleCandidates(params?.scaleLabels ?? params?.scale_labels);
    const currentCandidates = normalizeBrokenScaleCoinCandidates(
      params?.currentCandidates?.length
        ? params.currentCandidates
        : initialBrokenScaleCoinCandidates(coinCount, scaleLabels),
      coinCount,
      scaleLabels
    );
    const usedWeighings = Number(params?.usedWeighings ?? params?.used_weighings ?? 0);
    const maxWeighings = Number(params?.maxWeighings ?? params?.max_weighings);
    const partitions = brokenScaleCoinPartitionCandidates({
      ...params,
      currentCandidates,
      coin_count: coinCount,
      scaleLabels
    });
    const children = OUTCOMES
      .map(outcome => {
        const candidates = partitions[outcome];
        return {
          outcome,
          label: OUTCOME_LABELS[outcome],
          candidates,
          usedWeighings: usedWeighings + 1,
          status: brokenScaleCoinBranchStatus(candidates, usedWeighings + 1, maxWeighings)
        };
      })
      .filter(child => child.candidates.length > 0);
    return { partitions, children };
  }

  function brokenScaleCoinFinalizeAnswer(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const scaleLabels = initialScaleCandidates(params?.scaleLabels ?? params?.scale_labels);
    const candidates = normalizeBrokenScaleCoinCandidates(
      params?.currentCandidates?.length
        ? params.currentCandidates
        : initialBrokenScaleCoinCandidates(coinCount, scaleLabels),
      coinCount,
      scaleLabels
    );
    const selectedCoin = Number(params?.selectedCoin);
    const possibleCoins = uniqueCandidateCoins(candidates);
    let actualCandidate = null;
    if (possibleCoins.length === 1) {
      actualCandidate = candidates[0] ?? null;
      return {
        win: possibleCoins[0] === selectedCoin,
        actualCoin: possibleCoins[0] ?? null,
        actualBrokenScale: actualCandidate?.brokenScale ?? null,
        brokenScalesForActualCoin: uniqueScaleLabels(candidates.filter(candidate => candidate.coin === possibleCoins[0]).map(candidate => candidate.brokenScale)),
        candidates,
        possibleCoins
      };
    }
    actualCandidate = candidates.find(candidate => candidate.coin !== selectedCoin) ?? candidates[0] ?? null;
    return {
      win: false,
      actualCoin: actualCandidate?.coin ?? null,
      actualBrokenScale: actualCandidate?.brokenScale ?? null,
      brokenScalesForActualCoin: actualCandidate
        ? uniqueScaleLabels(candidates.filter(candidate => candidate.coin === actualCandidate.coin).map(candidate => candidate.brokenScale))
        : [],
      candidates,
      possibleCoins
    };
  }

  function initialBrokenDetectorCoinCandidates(coinCount, labels) {
    const count = Number(coinCount);
    const detectorLabels = initialScaleCandidates(labels);
    if (!Number.isInteger(count) || count < 1 || !detectorLabels.length) return [];
    const result = [];
    for (let coin = 1; coin <= count; coin += 1) {
      for (const brokenDetector of detectorLabels) result.push({ coin, brokenDetector });
    }
    return result;
  }

  function brokenDetectorCoinCandidateKey(candidate) {
    return `${candidate.coin}:${candidate.brokenDetector}`;
  }

  function normalizeBrokenDetectorCoinCandidates(candidates, coinCount, labels) {
    const count = Number(coinCount);
    const detectorLabels = initialScaleCandidates(labels);
    const allowedDetectors = new Set(detectorLabels);
    const seen = new Set();
    const result = [];
    for (const raw of candidates || []) {
      const coin = Number(raw?.coin ?? raw?.id ?? raw?.[0]);
      const brokenDetector = String(raw?.brokenDetector ?? raw?.broken_detector ?? raw?.detector ?? raw?.[1] ?? '');
      if (!Number.isInteger(coin) || coin < 1 || coin > count || !allowedDetectors.has(brokenDetector)) continue;
      const key = `${coin}:${brokenDetector}`;
      if (seen.has(key)) continue;
      seen.add(key);
      result.push({ coin, brokenDetector });
    }
    return result;
  }

  function normalizeDetectorAnswer(answer) {
    const value = String(answer || '').toLowerCase();
    if (['yes', 'y', 'true', '1', 'да'].includes(value)) return 'yes';
    if (['no', 'n', 'false', '0', 'нет'].includes(value)) return 'no';
    return YES_NO_OUTCOMES.includes(value) ? value : null;
  }

  function brokenDetectorCoinOutcomeForCandidate(candidate, detector, subsetCoins, options = {}) {
    const state = normalizeBrokenDetectorCoinCandidates(
      [candidate],
      options.coinCount ?? options.coin_count,
      options.detectorLabels ?? options.detector_labels
    )[0];
    const device = String(detector || '');
    if (!state || !device) return null;
    if (device === state.brokenDetector) return 'arbitrary';
    const subset = new Set(uniqueCoins(subsetCoins, options.coinCount ?? options.coin_count));
    return subset.has(state.coin) ? 'yes' : 'no';
  }

  function brokenDetectorCoinTestValidation(subsetCoins, options = {}) {
    const coinCount = options.coinCount ?? options.coin_count ?? null;
    const subset = uniqueCoins(subsetCoins, coinCount);
    if (!subset.length) {
      return {
        valid: false,
        error: 'Выберите хотя бы одну монету для проверки детектором.',
        subset
      };
    }
    return { valid: true, error: '', subset };
  }

  function brokenDetectorCoinFilterCandidates(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const detectorLabels = initialScaleCandidates(params?.detectorLabels ?? params?.detector_labels);
    const currentCandidates = normalizeBrokenDetectorCoinCandidates(
      params?.currentCandidates?.length
        ? params.currentCandidates
        : initialBrokenDetectorCoinCandidates(coinCount, detectorLabels),
      coinCount,
      detectorLabels
    );
    const detector = String(params?.detector || params?.instrument || '');
    const outcome = normalizeDetectorAnswer(params?.outcome ?? params?.answer);
    if (!outcome) return [];
    return currentCandidates.filter(candidate => {
      const candidateOutcome = brokenDetectorCoinOutcomeForCandidate(
        candidate,
        detector,
        params?.subsetCoins ?? params?.subset_coins ?? params?.coins,
        { coinCount, detectorLabels }
      );
      return candidateOutcome === 'arbitrary' || candidateOutcome === outcome;
    });
  }

  function brokenDetectorCoinPartitionCandidates(params) {
    return Object.fromEntries(YES_NO_OUTCOMES.map(outcome => [
      outcome,
      brokenDetectorCoinFilterCandidates({ ...params, outcome })
    ]));
  }

  function brokenDetectorCoinBranchStatus(candidates, usedTests, maxTests) {
    const remainingCoins = uniqueCandidateCoins(candidates);
    const used = Number(usedTests);
    const limit = Number(maxTests);
    if (remainingCoins.length === 1) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function brokenDetectorCoinChooseCheaterOutcome(params) {
    const partitions = brokenDetectorCoinPartitionCandidates(params || {});
    const history = Array.isArray(params?.history) ? params.history : [];
    const scores = Object.fromEntries(YES_NO_OUTCOMES.map(outcome => {
      const candidates = partitions[outcome];
      return [outcome, {
        states: candidates.length,
        coins: uniqueCandidateCoins(candidates).length
      }];
    }));
    const maxStateCount = Math.max(...YES_NO_OUTCOMES.map(outcome => scores[outcome].states));
    const stateTied = YES_NO_OUTCOMES.filter(outcome => scores[outcome].states === maxStateCount);
    const maxCoinCount = Math.max(...stateTied.map(outcome => scores[outcome].coins));
    const tied = stateTied.filter(outcome => scores[outcome].coins === maxCoinCount);
    const frequencies = Object.fromEntries(YES_NO_OUTCOMES.map(outcome => [outcome, 0]));
    for (const entry of history) {
      const outcome = normalizeDetectorAnswer(typeof entry === 'string' ? entry : entry?.outcome ?? entry?.answer);
      if (outcome in frequencies) frequencies[outcome] += 1;
    }
    const outcome = tied.slice().sort((a, b) =>
      frequencies[a] - frequencies[b] || YES_NO_OUTCOMES.indexOf(a) - YES_NO_OUTCOMES.indexOf(b)
    )[0];
    return {
      outcome,
      label: YES_NO_LABELS[outcome],
      candidates: partitions[outcome],
      partitions,
      scores
    };
  }

  function brokenDetectorCoinExpandExhaustiveNode(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const detectorLabels = initialScaleCandidates(params?.detectorLabels ?? params?.detector_labels);
    const currentCandidates = normalizeBrokenDetectorCoinCandidates(
      params?.currentCandidates?.length
        ? params.currentCandidates
        : initialBrokenDetectorCoinCandidates(coinCount, detectorLabels),
      coinCount,
      detectorLabels
    );
    const usedTests = Number(params?.usedTests ?? params?.used_tests ?? 0);
    const maxTests = Number(params?.maxTests ?? params?.max_tests ?? params?.maxWeighings ?? params?.max_weighings);
    const partitions = brokenDetectorCoinPartitionCandidates({
      ...params,
      currentCandidates,
      coin_count: coinCount,
      detectorLabels
    });
    const children = YES_NO_OUTCOMES
      .map(outcome => {
        const candidates = partitions[outcome];
        return {
          outcome,
          label: YES_NO_LABELS[outcome],
          candidates,
          usedTests: usedTests + 1,
          usedWeighings: usedTests + 1,
          status: brokenDetectorCoinBranchStatus(candidates, usedTests + 1, maxTests)
        };
      })
      .filter(child => child.candidates.length > 0);
    return { partitions, children };
  }

  function brokenDetectorCoinFinalizeAnswer(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const detectorLabels = initialScaleCandidates(params?.detectorLabels ?? params?.detector_labels);
    const candidates = normalizeBrokenDetectorCoinCandidates(
      params?.currentCandidates?.length
        ? params.currentCandidates
        : initialBrokenDetectorCoinCandidates(coinCount, detectorLabels),
      coinCount,
      detectorLabels
    );
    const selectedCoin = Number(params?.selectedCoin ?? params?.selected_coin);
    const possibleCoins = uniqueCandidateCoins(candidates);
    let actualCandidate = null;
    if (possibleCoins.length === 1) {
      actualCandidate = candidates[0] ?? null;
      return {
        win: possibleCoins[0] === selectedCoin,
        actualCoin: possibleCoins[0] ?? null,
        actualBrokenDetector: actualCandidate?.brokenDetector ?? null,
        brokenDetectorsForActualCoin: uniqueScaleLabels(candidates.filter(candidate => candidate.coin === possibleCoins[0]).map(candidate => candidate.brokenDetector)),
        candidates,
        possibleCoins
      };
    }
    actualCandidate = candidates.find(candidate => candidate.coin !== selectedCoin) ?? candidates[0] ?? null;
    return {
      win: false,
      actualCoin: actualCandidate?.coin ?? null,
      actualBrokenDetector: actualCandidate?.brokenDetector ?? null,
      brokenDetectorsForActualCoin: actualCandidate
        ? uniqueScaleLabels(candidates.filter(candidate => candidate.coin === actualCandidate.coin).map(candidate => candidate.brokenDetector))
        : [],
      candidates,
      possibleCoins
    };
  }

  function permutations(items) {
    const values = [...items];
    const result = [];
    function visit(index) {
      if (index === values.length) {
        result.push([...values]);
        return;
      }
      for (let cursor = index; cursor < values.length; cursor += 1) {
        [values[index], values[cursor]] = [values[cursor], values[index]];
        visit(index + 1);
        [values[index], values[cursor]] = [values[cursor], values[index]];
      }
    }
    visit(0);
    return result;
  }

  function heaviestBrokenScaleStateKey(state) {
    return `${state.brokenScale}|${state.order.join(',')}`;
  }

  function normalizeHeaviestBrokenScaleStates(states, coinCount = null, scaleLabels = null) {
    const count = Number(coinCount);
    const hasCount = Number.isInteger(count);
    const allowedScales = scaleLabels?.length ? new Set(scaleLabels.map(String)) : null;
    const seen = new Set();
    const result = [];
    for (const raw of states || []) {
      const order = uniqueCoins(raw?.order, hasCount ? count : null);
      const brokenScale = String(raw?.brokenScale ?? raw?.broken_scale ?? raw?.scale ?? '');
      if (!brokenScale || (allowedScales && !allowedScales.has(brokenScale))) continue;
      if (hasCount && order.length !== count) continue;
      const state = { order, brokenScale };
      const key = heaviestBrokenScaleStateKey(state);
      if (seen.has(key)) continue;
      seen.add(key);
      result.push(state);
    }
    return result;
  }

  function initialHeaviestBrokenScaleStates(coinCount, labels) {
    const coins = initialCandidates(coinCount);
    const scaleLabels = initialScaleCandidates(labels);
    if (!coins.length || !scaleLabels.length) return [];
    const orders = permutations(coins);
    const states = [];
    for (const brokenScale of scaleLabels) {
      for (const order of orders) states.push({ order: [...order], brokenScale });
    }
    return states;
  }

  function heaviestCoinFromState(state) {
    const order = Array.isArray(state?.order) ? state.order : [];
    return order[order.length - 1] ?? null;
  }

  function possibleHeaviestCoins(states) {
    return uniqueCoins((states || []).map(heaviestCoinFromState)).sort((a, b) => a - b);
  }

  function heaviestBrokenScaleOutcomeForState(state, instrument, leftCoin, rightCoin) {
    const device = String(instrument || '');
    const left = Number(leftCoin);
    const right = Number(rightCoin);
    if (!device || !Number.isInteger(left) || !Number.isInteger(right) || left === right) return null;
    if (device === String(state?.brokenScale || '')) return 'arbitrary';
    const order = Array.isArray(state?.order) ? state.order : [];
    const leftRank = order.indexOf(left);
    const rightRank = order.indexOf(right);
    if (leftRank < 0 || rightRank < 0) return null;
    return leftRank > rightRank ? 'left_down' : 'right_down';
  }

  function heaviestBrokenScaleCurrentStates(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const scaleLabels = initialScaleCandidates(params?.scaleLabels ?? params?.scale_labels);
    const current = params?.currentStates ?? params?.current_states;
    return current?.length
      ? normalizeHeaviestBrokenScaleStates(current, Number.isInteger(coinCount) ? coinCount : null, scaleLabels)
      : initialHeaviestBrokenScaleStates(coinCount, scaleLabels);
  }

  function heaviestBrokenScaleFilterStates(params) {
    const states = heaviestBrokenScaleCurrentStates(params || {});
    const outcome = normalizeScaleOutcome(params?.outcome);
    if (!outcome) return [];
    return states.filter(state => {
      const stateOutcome = heaviestBrokenScaleOutcomeForState(
        state,
        params?.instrument,
        params?.leftCoin ?? params?.left_coin,
        params?.rightCoin ?? params?.right_coin
      );
      return stateOutcome === 'arbitrary' || stateOutcome === outcome;
    });
  }

  function heaviestBrokenScalePartitionStates(params) {
    return Object.fromEntries(OUTCOMES.map(outcome => [
      outcome,
      heaviestBrokenScaleFilterStates({ ...params, outcome })
    ]));
  }

  function heaviestBrokenScaleChooseCheaterOutcome(params) {
    const partitions = heaviestBrokenScalePartitionStates(params || {});
    const history = Array.isArray(params?.history) ? params.history : [];
    const scores = Object.fromEntries(OUTCOMES.map(outcome => {
      const states = partitions[outcome];
      return [outcome, {
        states: states.length,
        heaviestCoins: possibleHeaviestCoins(states).length
      }];
    }));
    const maxAnswerCount = Math.max(...OUTCOMES.map(outcome => scores[outcome].heaviestCoins));
    const answerTied = OUTCOMES.filter(outcome => scores[outcome].heaviestCoins === maxAnswerCount);
    const maxStateCount = Math.max(...answerTied.map(outcome => scores[outcome].states));
    const tied = answerTied.filter(outcome => scores[outcome].states === maxStateCount);
    const frequencies = Object.fromEntries(OUTCOMES.map(outcome => [outcome, 0]));
    for (const entry of history) {
      const outcome = normalizeScaleOutcome(typeof entry === 'string' ? entry : entry?.outcome);
      if (outcome in frequencies) frequencies[outcome] += 1;
    }
    const outcome = tied.slice().sort((a, b) =>
      frequencies[a] - frequencies[b] || OUTCOMES.indexOf(a) - OUTCOMES.indexOf(b)
    )[0];
    const states = partitions[outcome];
    return {
      outcome,
      label: OUTCOME_LABELS[outcome],
      states,
      candidates: possibleHeaviestCoins(states),
      partitions,
      scores
    };
  }

  function heaviestBrokenScaleFinalizeAnswer(params) {
    const states = heaviestBrokenScaleCurrentStates(params || {});
    const selectedCoin = Number(params?.selectedCoin ?? params?.selected_coin);
    const candidates = possibleHeaviestCoins(states);
    if (candidates.length === 1) {
      const actualCoin = candidates[0];
      return { win: actualCoin === selectedCoin, actualCoin, candidates, states };
    }
    const actualCoin = candidates.find(candidate => candidate !== selectedCoin) ?? candidates[0] ?? null;
    return { win: false, actualCoin, candidates, states };
  }

  const BALANCED_WEIGHT_OUTCOMES = ['left_light', 'right_light', 'balance'];
  const BALANCED_WEIGHT_OUTCOME_LABELS = {
    left_light: 'левая чаша легче',
    right_light: 'правая чаша легче',
    balance: 'равновесие'
  };

  function balancedWeightBagWeights(params = {}) {
    const bagCount = Number(params.bagCount ?? params.bag_count ?? params.objectCount ?? params.object_count);
    const rawWeights = params.bagWeights ?? params.bag_weights ?? params.nominalWeights ?? params.nominal_weights;
    const weights = Array.isArray(rawWeights)
      ? rawWeights.map(value => Number(value)).filter(value => Number.isFinite(value) && value > 0)
      : [];
    if (Number.isInteger(bagCount) && bagCount > 0) {
      return Array.from({ length: bagCount }, (_item, index) => weights[index] || index + 1);
    }
    return weights;
  }

  function balancedWeightInitialStates(params = {}) {
    const weights = balancedWeightBagWeights(params);
    if (!weights.length || weights.length > 20) return [];
    return [
      { id: 'none', bag: null, label: 'нет недостачи' },
      ...weights.map((_weight, index) => ({
        id: `bag_${index + 1}`,
        bag: index + 1,
        label: `мешок ${index + 1}`
      }))
    ];
  }

  function balancedWeightStateKey(state) {
    if (state == null) return 'none';
    if (typeof state === 'string') return state === 'none' ? 'none' : String(state);
    const bag = Number(state.bag ?? state.deficientBag ?? state.deficient_bag);
    return Number.isInteger(bag) && bag >= 1 ? `bag_${bag}` : 'none';
  }

  function balancedWeightNormalizeStates(states, params = {}) {
    const allowed = new Map(balancedWeightInitialStates(params).map(state => [state.id, state]));
    const seen = new Set();
    const result = [];
    for (const raw of states || []) {
      const key = balancedWeightStateKey(raw);
      if (!allowed.has(key) || seen.has(key)) continue;
      seen.add(key);
      result.push(allowed.get(key));
    }
    return result;
  }

  function balancedWeightSideVector(values, bagCount) {
    const count = Number(bagCount);
    if (!Number.isInteger(count) || count < 1) return [];
    const result = Array.from({ length: count }, () => 0);
    if (Array.isArray(values)) {
      const looksLikeVector = values.length === count && values.every(value => Number.isInteger(Number(value)));
      if (looksLikeVector) {
        values.forEach((value, index) => {
          const amount = Number(value);
          result[index] = amount > 0 ? amount : 0;
        });
        return result;
      }
      for (const item of values) {
        const bag = Number(item);
        if (Number.isInteger(bag) && bag >= 1 && bag <= count) result[bag - 1] = 1;
      }
    }
    return result;
  }

  function balancedWeightNormalizeWeighing(params = {}) {
    const weights = balancedWeightBagWeights(params);
    const bagCount = weights.length;
    const left = balancedWeightSideVector(params.left ?? params.leftBags ?? params.left_bags, bagCount);
    const right = balancedWeightSideVector(params.right ?? params.rightBags ?? params.right_bags, bagCount);
    return { left, right, weights };
  }

  function balancedWeightNominalTotal(vector, weights) {
    return (vector || []).reduce((sum, amount, index) => sum + Math.max(0, Number(amount) || 0) * (Number(weights?.[index]) || 0), 0);
  }

  function balancedWeightValidateWeighing(params = {}) {
    const { left, right, weights } = balancedWeightNormalizeWeighing(params);
    if (!weights.length) return { valid: false, error: 'Нужно задать мешки и их номинальные веса.', left, right, weights };
    let hasAny = false;
    for (let index = 0; index < weights.length; index += 1) {
      const leftAmount = Number(left[index]) || 0;
      const rightAmount = Number(right[index]) || 0;
      if (leftAmount > 0 || rightAmount > 0) hasAny = true;
      if (!Number.isInteger(leftAmount) || !Number.isInteger(rightAmount) || leftAmount < 0 || rightAmount < 0) {
        return { valid: false, error: 'Коэффициенты должны быть неотрицательными целыми числами.', left, right, weights };
      }
      if (leftAmount > 0 && rightAmount > 0) {
        return { valid: false, error: `Мешок ${index + 1} нельзя положить на обе чаши одновременно.`, left, right, weights };
      }
    }
    if (!hasAny) return { valid: false, empty: true, error: 'Положите хотя бы один мешок на чаши.', left, right, weights };
    const leftTotal = balancedWeightNominalTotal(left, weights);
    const rightTotal = balancedWeightNominalTotal(right, weights);
    if (leftTotal !== rightTotal) {
      return { valid: false, error: `Номинальные веса должны совпадать: слева ${leftTotal}, справа ${rightTotal}.`, left, right, weights, leftTotal, rightTotal };
    }
    return { valid: true, error: '', left, right, weights, leftTotal, rightTotal };
  }

  function balancedWeightOutcomeForState(state, params = {}) {
    const normalizedState = balancedWeightInitialStates(params)
      .find(item => item.id === balancedWeightStateKey(state)) || { bag: null };
    const weighing = balancedWeightValidateWeighing(params);
    if (!weighing.valid) return null;
    if (normalizedState.bag == null) return 'balance';
    const index = normalizedState.bag - 1;
    if ((weighing.left[index] || 0) > 0) return 'left_light';
    if ((weighing.right[index] || 0) > 0) return 'right_light';
    return 'balance';
  }

  function balancedWeightPartitionStates(params = {}) {
    const states = params.currentStates?.length
      ? balancedWeightNormalizeStates(params.currentStates, params)
      : balancedWeightInitialStates(params);
    const validation = balancedWeightValidateWeighing(params);
    if (!validation.valid) return [];
    const partitions = Object.fromEntries(BALANCED_WEIGHT_OUTCOMES.map(outcome => [outcome, []]));
    for (const state of states) {
      const outcome = balancedWeightOutcomeForState(state, params);
      if (outcome) partitions[outcome].push(state);
    }
    return BALANCED_WEIGHT_OUTCOMES
      .filter(outcome => partitions[outcome].length)
      .map(outcome => ({
        outcome,
        label: BALANCED_WEIGHT_OUTCOME_LABELS[outcome],
        states: partitions[outcome],
        candidates: partitions[outcome],
        leftTotal: validation.leftTotal,
        rightTotal: validation.rightTotal
      }));
  }

  function balancedWeightFilterStates(params = {}) {
    const outcome = String(params.outcome || '').toLowerCase();
    const part = balancedWeightPartitionStates(params).find(item => item.outcome === outcome);
    return part ? part.states : [];
  }

  function balancedWeightChooseCheaterOutcome(params = {}) {
    const partitions = balancedWeightPartitionStates(params);
    const order = Object.fromEntries(BALANCED_WEIGHT_OUTCOMES.map((outcome, index) => [outcome, index]));
    const chosen = partitions.slice().sort((a, b) =>
      b.states.length - a.states.length || order[a.outcome] - order[b.outcome]
    )[0] || { outcome: 'balance', label: BALANCED_WEIGHT_OUTCOME_LABELS.balance, states: [], candidates: [] };
    return {
      outcome: chosen.outcome,
      label: chosen.label,
      states: chosen.states,
      candidates: chosen.states,
      partitions,
      scores: Object.fromEntries(partitions.map(part => [part.outcome, part.states.length]))
    };
  }

  function balancedWeightBranchStatus(states, usedWeighings, maxWeighings) {
    const remaining = states || [];
    const used = Number(usedWeighings);
    const limit = Number(maxWeighings);
    if (remaining.length === 1) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function balancedWeightExpandExhaustiveNode(params = {}) {
    const usedWeighings = Number(params.usedWeighings ?? params.used_weighings ?? 0);
    const maxWeighings = Number(params.maxWeighings ?? params.max_weighings ?? 1);
    const partitions = balancedWeightPartitionStates(params);
    const children = partitions.map(part => ({
      outcome: part.outcome,
      label: part.label,
      states: part.states,
      candidates: part.states,
      usedWeighings: usedWeighings + 1,
      status: balancedWeightBranchStatus(part.states, usedWeighings + 1, maxWeighings)
    }));
    return { partitions, children };
  }

  function balancedWeightFinalizeAnswer(params = {}) {
    const candidates = params.currentStates?.length
      ? balancedWeightNormalizeStates(params.currentStates, params)
      : balancedWeightInitialStates(params);
    const selectedKey = balancedWeightStateKey(
      params.selectedState ?? { bag: params.selectedBag ?? params.selected_bag }
    );
    if (candidates.length === 1) {
      const actualState = candidates[0];
      return { win: balancedWeightStateKey(actualState) === selectedKey, actualState, candidates };
    }
    const actualState = candidates.find(state => balancedWeightStateKey(state) !== selectedKey) ?? candidates[0] ?? null;
    return { win: false, actualState, candidates };
  }

  function expertJudgeObjectCount(params = {}) {
    const count = Number(params.objectCount ?? params.object_count ?? params.weightCount ?? params.weight_count);
    return Number.isInteger(count) && count >= 2 && count <= 30 ? count : 0;
  }

  function expertJudgeWeightValues(params = {}) {
    const explicit = params.weightValues ?? params.weight_values;
    if (Array.isArray(explicit)) {
      const values = explicit.map(value => Number(value));
      if (values.length >= 2 && values.every(value => Number.isInteger(value) && value > 0) && new Set(values).size === values.length) {
        return values.slice().sort((a, b) => a - b);
      }
    }
    const count = expertJudgeObjectCount(params);
    return count ? Array.from({ length: count }, (_item, index) => index + 1) : [];
  }

  function expertJudgeNormalizeAssignment(assignment, params = {}) {
    const values = expertJudgeWeightValues(params);
    const count = values.length;
    const allowed = new Set(values);
    const raw = Array.isArray(assignment)
      ? assignment
      : (assignment?.weights ?? assignment?.assignment ?? params.assignment ?? params.weights ?? []);
    const normalized = Array.isArray(raw)
      ? raw.map(value => Number(value))
      : [];
    if (normalized.length === count && normalized.every(value => allowed.has(value)) && new Set(normalized).size === count) {
      return normalized;
    }
    return [...values];
  }

  function expertJudgeRandomAssignment(params = {}) {
    const values = expertJudgeWeightValues(params);
    const result = [...values];
    for (let index = result.length - 1; index > 0; index -= 1) {
      const swapIndex = Math.floor(Math.random() * (index + 1));
      [result[index], result[swapIndex]] = [result[swapIndex], result[index]];
    }
    return result;
  }

  function expertJudgeNormalizeWeighing(params = {}) {
    const count = expertJudgeObjectCount(params);
    const left = uniqueCoins(params.left ?? params.leftObjects ?? params.left_objects, count);
    const right = uniqueCoins(params.right ?? params.rightObjects ?? params.right_objects, count);
    const leftSet = new Set(left);
    const overlap = right.filter(item => leftSet.has(item));
    const outside = Array.from({ length: count }, (_item, index) => index + 1)
      .filter(item => !leftSet.has(item) && !right.includes(item));
    return {
      valid: count >= 2 && overlap.length === 0 && (left.length > 0 || right.length > 0),
      objectCount: count,
      left,
      right,
      outside,
      overlap
    };
  }

  function expertJudgeOutcomeFromSums(leftSum, rightSum) {
    if (leftSum > rightSum) return 'left_down';
    if (rightSum > leftSum) return 'right_down';
    return 'balance';
  }

  function expertJudgeOutcomeForAssignment(assignment, params = {}) {
    const weighing = expertJudgeNormalizeWeighing(params);
    if (!weighing.valid) return null;
    const normalized = expertJudgeNormalizeAssignment(assignment, { ...params, object_count: weighing.objectCount });
    const leftSum = weighing.left.reduce((sum, item) => sum + (normalized[item - 1] || 0), 0);
    const rightSum = weighing.right.reduce((sum, item) => sum + (normalized[item - 1] || 0), 0);
    return {
      outcome: expertJudgeOutcomeFromSums(leftSum, rightSum),
      label: OUTCOME_LABELS[expertJudgeOutcomeFromSums(leftSum, rightSum)],
      leftSum,
      rightSum
    };
  }

  function expertJudgeCompareMatches(leftSum, rightSum, outcome) {
    if (outcome === 'left_down') return leftSum > rightSum;
    if (outcome === 'right_down') return rightSum > leftSum;
    if (outcome === 'balance') return leftSum === rightSum;
    return false;
  }

  function expertJudgeSubsetSums(values, size) {
    const targetSize = Number(size);
    if (!Number.isInteger(targetSize) || targetSize < 0 || targetSize > values.length) return new Set();
    const dp = Array.from({ length: targetSize + 1 }, () => new Set());
    dp[0].add(0);
    for (const value of values) {
      for (let count = targetSize - 1; count >= 0; count -= 1) {
        for (const sum of dp[count]) dp[count + 1].add(sum + value);
      }
    }
    return dp[targetSize];
  }

  function expertJudgePossibleWeightsForSingleton(role, params = {}) {
    const values = expertJudgeWeightValues(params);
    const weighing = expertJudgeNormalizeWeighing(params);
    const outcome = String(params.outcome || '').toLowerCase();
    if (!values.length || !weighing.valid || !OUTCOMES.includes(outcome)) return [];
    if (role === 'left' && weighing.left.length === 1) {
      return values.filter(value => {
        const rightSums = expertJudgeSubsetSums(values.filter(candidate => candidate !== value), weighing.right.length);
        return [...rightSums].some(rightSum => expertJudgeCompareMatches(value, rightSum, outcome));
      });
    }
    if (role === 'right' && weighing.right.length === 1) {
      return values.filter(value => {
        const leftSums = expertJudgeSubsetSums(values.filter(candidate => candidate !== value), weighing.left.length);
        return [...leftSums].some(leftSum => expertJudgeCompareMatches(leftSum, value, outcome));
      });
    }
    if (role === 'outside' && weighing.outside.length === 1) {
      return values.filter(value => {
        const remaining = values.filter(candidate => candidate !== value);
        const total = remaining.reduce((sum, item) => sum + item, 0);
        const leftSums = expertJudgeSubsetSums(remaining, weighing.left.length);
        return [...leftSums].some(leftSum => expertJudgeCompareMatches(leftSum, total - leftSum, outcome));
      });
    }
    return [];
  }

  function expertJudgeForcedWeights(params = {}) {
    const weighing = expertJudgeNormalizeWeighing(params);
    const roles = [
      { role: 'left', items: weighing.left },
      { role: 'right', items: weighing.right },
      { role: 'outside', items: weighing.outside }
    ];
    return roles
      .filter(entry => entry.items.length === 1)
      .map(entry => {
        const possibleWeights = expertJudgePossibleWeightsForSingleton(entry.role, params);
        return {
          role: entry.role,
          object: entry.items[0],
          possibleWeights,
          forcedWeight: possibleWeights.length === 1 ? possibleWeights[0] : null
        };
      });
  }

  function expertJudgeEvaluateCertificate(params = {}) {
    const assignment = expertJudgeNormalizeAssignment(params.assignment ?? params.weights, params);
    const observed = params.outcome
      ? { outcome: String(params.outcome).toLowerCase(), label: OUTCOME_LABELS[String(params.outcome).toLowerCase()] }
      : expertJudgeOutcomeForAssignment(assignment, params);
    const forced = expertJudgeForcedWeights({ ...params, outcome: observed?.outcome });
    return {
      valid: !!observed && OUTCOMES.includes(observed.outcome),
      assignment,
      outcome: observed?.outcome || null,
      label: observed?.label || '',
      leftSum: observed?.leftSum ?? null,
      rightSum: observed?.rightSum ?? null,
      forced,
      learned: forced.filter(item => item.forcedWeight != null),
      success: forced.some(item => item.forcedWeight != null)
    };
  }

  function numericSignatureInitialStates(bagCount, options = {}) {
    const count = Number(bagCount);
    if (!Number.isInteger(count) || count < 1 || count > 20) return [];
    const stateModel = String(options.stateModel ?? options.state_model ?? '').toLowerCase();
    const objective = String(options.objective || '').toLowerCase();
    const fakeBagCount = Number(options.fakeBagCount ?? options.fake_bag_count);
    const singleFake = stateModel === 'single_fake_bag' || objective === 'identify_fake_bag' || fakeBagCount === 1;
    if (singleFake) {
      const direction = normalizeDirection(options.counterfeitWeight ?? options.counterfeit_weight) || 'lighter';
      const delta = Math.max(0, Number(options.counterfeitDelta ?? options.counterfeit_delta ?? 1) || 1);
      return Array.from({ length: count }, (_item, index) => ({
        mask: 1 << index,
        bags: [index + 1],
        fakeBag: index + 1,
        direction,
        delta
      }));
    }
    const fixedFakeCount = stateModel === 'fixed_fake_count' || objective === 'identify_fake_coin_set'
      ? fakeBagCount
      : NaN;
    if (Number.isInteger(fixedFakeCount) && fixedFakeCount >= 1 && fixedFakeCount <= count) {
      const states = [];
      function addCombinations(start, remaining, mask, bags) {
        if (remaining === 0) {
          states.push({ mask, bags: [...bags] });
          return;
        }
        for (let index = start; index <= count - remaining; index += 1) {
          bags.push(index + 1);
          addCombinations(index + 1, remaining - 1, mask | (1 << index), bags);
          bags.pop();
        }
      }
      addCombinations(0, fixedFakeCount, 0, []);
      return states;
    }
    const allowEmpty = options.allowEmptySubset ?? options.allow_empty_subset ?? true;
    const excludeAll = options.excludeAllFake ?? options.exclude_all_fake ?? true;
    const allMask = (1 << count) - 1;
    const states = [];
    for (let mask = 0; mask <= allMask; mask += 1) {
      if (!allowEmpty && mask === 0) continue;
      if (excludeAll && mask === allMask) continue;
      const bags = [];
      for (let index = 0; index < count; index += 1) {
        if (mask & (1 << index)) bags.push(index + 1);
      }
      states.push({ mask, bags });
    }
    return states;
  }

  function numericSignatureStateKey(state) {
    const normalized = numericSignatureNormalizeState(state);
    const mask = Number(normalized?.mask);
    if (Number.isInteger(mask) && mask >= 0) return String(mask);
    return normalized.bags.join(',');
  }

  function numericSignatureNormalizeState(state) {
    const rawMask = Number(state?.mask);
    if (Number.isInteger(rawMask) && rawMask >= 0) {
      const bags = [];
      for (let index = 0; index < 20; index += 1) {
        if (rawMask & (1 << index)) bags.push(index + 1);
      }
      const fakeBag = bags.length === 1 ? bags[0] : undefined;
      return { mask: rawMask, bags, ...(fakeBag ? { fakeBag } : {}) };
    }
    const bags = uniqueCoins(state?.bags ?? state?.fakeBags ?? state?.fake_bags ?? state);
    let mask = 0;
    for (const bag of bags) mask |= (1 << (bag - 1));
    const fakeBag = bags.length === 1 ? bags[0] : undefined;
    return { mask, bags, ...(fakeBag ? { fakeBag } : {}) };
  }

  function numericSignatureNormalizeStates(states, bagCount, options = {}) {
    const allowed = new Set(numericSignatureInitialStates(bagCount, options).map(state => state.mask));
    const seen = new Set();
    const result = [];
    for (const raw of states || []) {
      const state = numericSignatureNormalizeState(raw);
      if (!allowed.has(state.mask) || seen.has(state.mask)) continue;
      seen.add(state.mask);
      result.push(state);
    }
    return result;
  }

  function numericSignatureAmounts(amounts, bagCount) {
    const count = Number(bagCount);
    if (!Number.isInteger(count) || count < 1) return [];
    return Array.from({ length: count }, (_item, index) => {
      const value = Number(amounts?.[index] ?? 0);
      return Number.isInteger(value) && value > 0 ? value : 0;
    });
  }

  function numericSignatureAmountsValidation(rawAmounts, bagCount) {
    const count = Number(bagCount);
    if (!Number.isInteger(count) || count < 1) {
      return { valid: false, error: 'Invalid object count.', amounts: [] };
    }
    const amounts = [];
    for (let index = 0; index < count; index += 1) {
      const raw = rawAmounts?.[index];
      if (raw == null || raw === '') {
        amounts.push(0);
        continue;
      }
      const value = typeof raw === 'string' ? raw.trim() : raw;
      if (value === '') {
        amounts.push(0);
        continue;
      }
      const number = Number(value);
      if (!Number.isInteger(number) || number < 0) {
        return {
          valid: false,
          error: `Quantity for item ${index + 1} must be a non-negative integer.`,
          amounts
        };
      }
      amounts.push(number);
    }
    return { valid: true, error: '', amounts };
  }

  function numericSignatureTotal(amounts) {
    return (amounts || []).reduce((sum, value) => sum + Math.max(0, Number(value) || 0), 0);
  }

  function numericSignatureDeficit(state, amounts) {
    const normalized = numericSignatureNormalizeState(state);
    return normalized.bags.reduce((sum, bag) => sum + (Number(amounts?.[bag - 1]) || 0), 0);
  }

  function numericSignatureObservationModel(options = {}) {
    const explicit = String(options.observationModel ?? options.observation_model ?? '').toLowerCase();
    if (explicit === 'actual_weight' || explicit === 'deficit_residue') return explicit;
    const stateModel = String(options.stateModel ?? options.state_model ?? '').toLowerCase();
    const objective = String(options.objective || '').toLowerCase();
    const fakeBagCount = Number(options.fakeBagCount ?? options.fake_bag_count);
    return stateModel === 'single_fake_bag' || objective === 'identify_fake_bag' || fakeBagCount === 1
      ? 'actual_weight'
      : 'deficit_residue';
  }

  function numericSignatureSignedDeviation(state, amounts, options = {}) {
    const normalized = numericSignatureNormalizeState(state);
    const direction = normalizeDirection(
      state?.direction ?? options.counterfeitWeight ?? options.counterfeit_weight
    ) || 'lighter';
    const delta = Math.max(0, Number(state?.delta ?? options.counterfeitDelta ?? options.counterfeit_delta ?? 1) || 1);
    const magnitude = normalized.bags.reduce((sum, bag) => sum + (Number(amounts?.[bag - 1]) || 0), 0) * delta;
    return direction === 'heavier' ? magnitude : -magnitude;
  }

  function numericSignatureResidueForDeficit(deficit, total) {
    const modulus = Number(total);
    if (!Number.isInteger(modulus) || modulus <= 0) return 0;
    const value = Number(deficit) || 0;
    return ((value % modulus) + modulus) % modulus;
  }

  function numericSignatureObservationForState(state, amounts, options = {}) {
    const values = numericSignatureAmounts(amounts, amounts?.length ?? options.bagCount ?? options.bag_count);
    const total = numericSignatureTotal(values);
    const deficit = numericSignatureDeficit(state, values);
    const deficitResidue = numericSignatureResidueForDeficit(deficit, total);
    const maxDeficit = numericSignatureTotal(values);
    const baseWeight = Math.max(Number(options.genuineWeight ?? options.genuine_weight ?? 10) || 10, Math.ceil(maxDeficit / Math.max(1, total)) + 2);
    const observationModel = numericSignatureObservationModel(options);
    const signedDeviation = numericSignatureSignedDeviation(state, values, options);
    const expectedWeight = total * baseWeight;
    const weight = observationModel === 'actual_weight'
      ? expectedWeight + signedDeviation
      : (total > 0 ? expectedWeight - deficitResidue : 0);
    return { total, deficit, deficitResidue, signedDeviation, observedDeviation: signedDeviation, expectedWeight, weight, genuineWeight: baseWeight, observationModel };
  }

  function numericSignatureObservationKeyForState(state, amounts, options = {}) {
    const observationModel = numericSignatureObservationModel(options);
    if (observationModel === 'actual_weight') {
      return numericSignatureSignedDeviation(state, amounts, options);
    }
    const total = numericSignatureTotal(amounts);
    return numericSignatureResidueForDeficit(numericSignatureDeficit(state, amounts), total);
  }

  function numericSignatureFilterStates(params) {
    const bagCount = Number(params?.bag_count ?? params?.bagCount);
    const amounts = numericSignatureAmounts(params?.amounts, bagCount);
    const total = numericSignatureTotal(amounts);
    const currentStates = params?.currentStates?.length
      ? numericSignatureNormalizeStates(params.currentStates, bagCount, params)
      : numericSignatureInitialStates(bagCount, params);
    if (numericSignatureObservationModel(params) === 'actual_weight') {
      const baseWeight = Math.max(Number(params?.genuineWeight ?? params?.genuine_weight ?? 10) || 10, 1);
      const observedDeviation = params?.observedDeviation ?? params?.observed_deviation ?? (
        params?.weight != null ? Number(params.weight) - total * baseWeight : null
      );
      const target = Number(observedDeviation);
      return currentStates.filter(state => numericSignatureSignedDeviation(state, amounts, params) === target);
    }
    const residue = numericSignatureResidueForDeficit(params?.deficitResidue ?? params?.deficit_residue ?? params?.residue, total);
    return currentStates.filter(state =>
      numericSignatureResidueForDeficit(numericSignatureDeficit(state, amounts), total) === residue
    );
  }

  function numericSignaturePartitionStates(params) {
    const bagCount = Number(params?.bag_count ?? params?.bagCount);
    const amounts = numericSignatureAmounts(params?.amounts, bagCount);
    const total = numericSignatureTotal(amounts);
    const currentStates = params?.currentStates?.length
      ? numericSignatureNormalizeStates(params.currentStates, bagCount, params)
      : numericSignatureInitialStates(bagCount, params);
    const byObservation = new Map();
    for (const state of currentStates) {
      const key = numericSignatureObservationKeyForState(state, amounts, params);
      if (!byObservation.has(key)) byObservation.set(key, []);
      byObservation.get(key).push(state);
    }
    return [...byObservation.entries()]
      .sort((a, b) => a[0] - b[0])
      .map(([key, states]) => {
        const observation = numericSignatureObservationForState(states[0] || { bags: [] }, amounts, params);
        return {
          key,
          residue: observation.deficitResidue,
          deficitResidue: observation.deficitResidue,
          observedDeviation: observation.observedDeviation,
          weight: observation.weight,
          observation,
          states,
          total
        };
      });
  }

  function numericSignatureChooseCheaterOutcome(params) {
    const partitions = numericSignaturePartitionStates(params || {});
    const chosen = partitions.slice().sort((a, b) => b.states.length - a.states.length || a.residue - b.residue)[0] || { residue: 0, states: [], total: 0 };
    return {
      key: chosen.key,
      residue: chosen.residue,
      deficitResidue: chosen.residue,
      observedDeviation: chosen.observedDeviation,
      weight: chosen.weight,
      observation: chosen.observation,
      states: chosen.states,
      candidates: chosen.states,
      partitions,
      scores: Object.fromEntries(partitions.map(part => [part.key, part.states.length]))
    };
  }

  function numericSignatureBranchStatus(states, usedWeighings, maxWeighings) {
    const remaining = states || [];
    const used = Number(usedWeighings);
    const limit = Number(maxWeighings);
    if (remaining.length === 1) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function numericSignatureExpandExhaustiveNode(params) {
    const usedWeighings = Number(params?.usedWeighings ?? params?.used_weighings ?? 0);
    const maxWeighings = Number(params?.maxWeighings ?? params?.max_weighings ?? 1);
    const partitions = numericSignaturePartitionStates(params || {});
    const children = partitions.map(part => ({
      key: part.key,
      residue: part.residue,
      deficitResidue: part.residue,
      observedDeviation: part.observedDeviation,
      weight: part.weight,
      observation: part.observation,
      states: part.states,
      candidates: part.states,
      usedWeighings: usedWeighings + 1,
      status: numericSignatureBranchStatus(part.states, usedWeighings + 1, maxWeighings)
    }));
    return { partitions, children };
  }

  function numericSignatureFinalizeAnswer(params) {
    const bagCount = Number(params?.bag_count ?? params?.bagCount);
    const candidates = params?.currentStates?.length
      ? numericSignatureNormalizeStates(params.currentStates, bagCount, params)
      : numericSignatureInitialStates(bagCount, params);
    const selected = numericSignatureNormalizeState(params?.selectedBags ?? params?.selected_bags ?? []);
    const selectedKey = numericSignatureStateKey(selected);
    if (candidates.length === 1) {
      const actualState = candidates[0];
      return { win: numericSignatureStateKey(actualState) === selectedKey, actualState, candidates };
    }
    const actualState = candidates.find(state => numericSignatureStateKey(state) !== selectedKey) ?? candidates[0] ?? null;
    return { win: false, actualState, candidates };
  }

  const SELECTED_BAG_WEIGHT_OUTCOMES = ['left_down', 'balance', 'right_down'];
  const SELECTED_BAG_WEIGHT_LABELS = {
    left_down: 'левая чаша тяжелее',
    balance: 'равновесие',
    right_down: 'правая чаша тяжелее'
  };

  function selectedBagWeightValues(params = {}) {
    const rawValues = params.weightValues ?? params.weight_values ?? params.possibleWeights ?? params.possible_weights;
    const values = Array.isArray(rawValues)
      ? rawValues.map(value => Number(value)).filter(value => Number.isInteger(value) && value > 0)
      : [];
    const unique = [...new Set(values)].sort((a, b) => a - b);
    if (unique.length) return unique;
    const bagCount = Number(params.bagCount ?? params.bag_count ?? params.objectCount ?? params.object_count ?? 7);
    const start = Number(params.weightMin ?? params.weight_min ?? 1);
    if (!Number.isInteger(bagCount) || bagCount < 1 || bagCount > 20) return [];
    return Array.from({ length: bagCount }, (_item, index) => start + index);
  }

  function selectedBagWeightReferenceTotal(params = {}) {
    const explicit = Number(params.referenceTotal ?? params.reference_total);
    if (Number.isFinite(explicit) && explicit > 0) return explicit;
    return selectedBagWeightValues(params).reduce((sum, value) => sum + value, 0);
  }

  function selectedBagWeightInitialStates(params = {}) {
    return selectedBagWeightValues(params).map(weight => ({
      id: `weight_${weight}`,
      weight,
      label: `${weight} г`
    }));
  }

  function selectedBagWeightStateKey(state) {
    const weight = Number(state?.weight ?? state?.value ?? state);
    return Number.isInteger(weight) && weight > 0 ? String(weight) : '';
  }

  function selectedBagWeightNormalizeStates(states, params = {}) {
    const allowed = new Set(selectedBagWeightValues(params));
    const seen = new Set();
    const result = [];
    for (const raw of states || []) {
      const weight = Number(raw?.weight ?? raw?.value ?? raw);
      if (!allowed.has(weight) || seen.has(weight)) continue;
      seen.add(weight);
      result.push({ id: `weight_${weight}`, weight, label: `${weight} г` });
    }
    return result;
  }

  function selectedBagWeightCurrentStates(params = {}) {
    const current = params.currentStates ?? params.current_states ?? params.currentCandidates ?? params.current_candidates;
    return current?.length
      ? selectedBagWeightNormalizeStates(current, params)
      : selectedBagWeightInitialStates(params);
  }

  function selectedBagWeightComparison(params = {}) {
    const selectedCoins = Number(params.selectedCoins ?? params.selected_coins ?? params.leftCoins ?? params.left_coins);
    const kitCount = Number(params.kitCount ?? params.kit_count ?? params.referenceKits ?? params.reference_kits ?? params.rightKits ?? params.right_kits);
    const maxCoins = Number(params.maxCoinsPerBag ?? params.max_coins_per_bag ?? 100);
    const referenceTotal = selectedBagWeightReferenceTotal(params);
    if (!Number.isInteger(selectedCoins) || selectedCoins < 0) {
      return { valid: false, empty: true, error: 'Введите целое число монет из указанного мешка.', selectedCoins: 0, kitCount: 0, referenceTotal };
    }
    if (!Number.isInteger(kitCount) || kitCount < 0) {
      return { valid: false, empty: true, error: 'Введите целое число полных комплектов.', selectedCoins, kitCount: 0, referenceTotal };
    }
    if (selectedCoins === 0 && kitCount === 0) {
      return { valid: false, empty: true, error: 'Положите что-нибудь на весы.', selectedCoins, kitCount, referenceTotal };
    }
    if (Number.isInteger(maxCoins) && maxCoins > 0 && selectedCoins > maxCoins) {
      return { valid: false, error: `В указанном мешке только ${maxCoins} монет.`, selectedCoins, kitCount, referenceTotal };
    }
    if (Number.isInteger(maxCoins) && maxCoins > 0 && kitCount > maxCoins) {
      return { valid: false, error: `Полных комплектов можно взять не больше ${maxCoins}: в каждом мешке по ${maxCoins} монет.`, selectedCoins, kitCount, referenceTotal };
    }
    if (!Number.isFinite(referenceTotal) || referenceTotal <= 0) {
      return { valid: false, error: 'Не задана сумма весов одного полного комплекта.', selectedCoins, kitCount, referenceTotal };
    }
    return {
      valid: true,
      error: '',
      selectedCoins,
      kitCount,
      referenceTotal,
      leftNominalAtMiddle: selectedCoins * (referenceTotal / Math.max(1, selectedBagWeightValues(params).length)),
      rightWeight: kitCount * referenceTotal
    };
  }

  function selectedBagWeightOutcomeForState(state, params = {}) {
    const comparison = selectedBagWeightComparison(params);
    if (!comparison.valid) return null;
    const weight = Number(state?.weight ?? state?.value ?? state);
    const leftWeight = comparison.selectedCoins * weight;
    const rightWeight = comparison.rightWeight;
    if (leftWeight > rightWeight) return 'left_down';
    if (rightWeight > leftWeight) return 'right_down';
    return 'balance';
  }

  function selectedBagWeightPartitionStates(params = {}) {
    const states = selectedBagWeightCurrentStates(params);
    const comparison = selectedBagWeightComparison(params);
    if (!comparison.valid) return [];
    const partitions = Object.fromEntries(SELECTED_BAG_WEIGHT_OUTCOMES.map(outcome => [outcome, []]));
    for (const state of states) {
      const outcome = selectedBagWeightOutcomeForState(state, params);
      if (outcome) partitions[outcome].push(state);
    }
    return SELECTED_BAG_WEIGHT_OUTCOMES
      .filter(outcome => partitions[outcome].length)
      .map(outcome => ({
        outcome,
        label: SELECTED_BAG_WEIGHT_LABELS[outcome],
        states: partitions[outcome],
        candidates: partitions[outcome],
        comparison
      }));
  }

  function selectedBagWeightFilterStates(params = {}) {
    const outcome = String(params.outcome || '').toLowerCase();
    const part = selectedBagWeightPartitionStates(params).find(item => item.outcome === outcome);
    return part ? part.states : [];
  }

  function selectedBagWeightChooseCheaterOutcome(params = {}) {
    const partitions = selectedBagWeightPartitionStates(params);
    const order = Object.fromEntries(SELECTED_BAG_WEIGHT_OUTCOMES.map((outcome, index) => [outcome, index]));
    const chosen = partitions.slice().sort((a, b) =>
      b.states.length - a.states.length || order[a.outcome] - order[b.outcome]
    )[0] || { outcome: 'balance', label: SELECTED_BAG_WEIGHT_LABELS.balance, states: [], candidates: [] };
    return {
      outcome: chosen.outcome,
      label: chosen.label,
      states: chosen.states,
      candidates: chosen.states,
      partitions,
      scores: Object.fromEntries(partitions.map(part => [part.outcome, part.states.length])),
      comparison: chosen.comparison
    };
  }

  function selectedBagWeightBranchStatus(states, usedWeighings, maxWeighings) {
    const remaining = states || [];
    const used = Number(usedWeighings);
    const limit = Number(maxWeighings);
    if (remaining.length === 1) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function selectedBagWeightExpandExhaustiveNode(params = {}) {
    const usedWeighings = Number(params.usedWeighings ?? params.used_weighings ?? 0);
    const maxWeighings = Number(params.maxWeighings ?? params.max_weighings ?? 1);
    const partitions = selectedBagWeightPartitionStates(params);
    const children = partitions.map(part => ({
      outcome: part.outcome,
      label: part.label,
      states: part.states,
      candidates: part.states,
      comparison: part.comparison,
      usedWeighings: usedWeighings + 1,
      status: selectedBagWeightBranchStatus(part.states, usedWeighings + 1, maxWeighings)
    }));
    return { partitions, children };
  }

  function selectedBagWeightFinalizeAnswer(params = {}) {
    const candidates = selectedBagWeightCurrentStates(params);
    const selectedWeight = Number(params.selectedWeight ?? params.selected_weight ?? params.answer ?? params.weight);
    if (candidates.length === 1) {
      const actualState = candidates[0];
      return { win: actualState.weight === selectedWeight, actualState, candidates };
    }
    const actualState = candidates.find(state => state.weight !== selectedWeight) ?? candidates[0] ?? null;
    return { win: false, actualState, candidates };
  }

  function subsetSignatureInitialStates(objectCount) {
    const count = Number(objectCount);
    if (!Number.isInteger(count) || count < 1 || count > 20) return [];
    const states = [];
    const allMask = (1 << count) - 1;
    for (let mask = 0; mask <= allMask; mask += 1) {
      const objects = [];
      for (let index = 0; index < count; index += 1) {
        if (mask & (1 << index)) objects.push(index + 1);
      }
      states.push({ mask, objects });
    }
    return states;
  }

  function subsetSignatureNormalizeState(state) {
    const rawMask = Number(state?.mask);
    if (Number.isInteger(rawMask) && rawMask >= 0) {
      const objects = [];
      for (let index = 0; index < 20; index += 1) {
        if (rawMask & (1 << index)) objects.push(index + 1);
      }
      return { mask: rawMask, objects };
    }
    const objects = uniqueCoins(state?.objects ?? state?.balls ?? state);
    let mask = 0;
    for (const object of objects) mask |= (1 << (object - 1));
    return { mask, objects };
  }

  function subsetSignatureNormalizeTests(tests, objectCount, maxTests = null) {
    const limit = Number(objectCount);
    if (!Number.isInteger(limit) || limit < 1) return [];
    const rows = Array.isArray(tests) ? tests : [];
    const normalized = rows.map(row => uniqueCoins(row, limit));
    const target = Number(maxTests);
    if (maxTests != null && Number.isInteger(target) && target >= 0) {
      while (normalized.length < target) normalized.push([]);
      return normalized.slice(0, target);
    }
    return normalized;
  }

  function subsetSignatureForState(state, tests) {
    const normalized = subsetSignatureNormalizeState(state);
    return (tests || []).map(test =>
      (test || []).reduce((sum, object) => sum + ((normalized.mask & (1 << (object - 1))) ? 1 : 0), 0)
    );
  }

  function subsetSignatureKey(signature) {
    return (signature || []).join(',');
  }

  function subsetSignatureStateKey(state) {
    return String(subsetSignatureNormalizeState(state).mask);
  }

  function subsetSignaturePartitionStates(params = {}) {
    const objectCount = Number(params.object_count ?? params.objectCount);
    const maxTests = Number(params.max_tests ?? params.maxTests ?? params.test_count ?? params.testCount);
    const tests = subsetSignatureNormalizeTests(params.tests, objectCount, Number.isInteger(maxTests) ? maxTests : null);
    const currentStates = params.currentStates?.length
      ? params.currentStates.map(subsetSignatureNormalizeState)
      : subsetSignatureInitialStates(objectCount);
    const bySignature = new Map();
    for (const state of currentStates) {
      const signature = subsetSignatureForState(state, tests);
      const key = subsetSignatureKey(signature);
      if (!bySignature.has(key)) bySignature.set(key, { key, signature, states: [] });
      bySignature.get(key).states.push(state);
    }
    return [...bySignature.values()].sort((a, b) =>
      a.signature.length - b.signature.length || a.key.localeCompare(b.key, undefined, { numeric: true })
    );
  }

  function subsetSignatureCheckStrategy(params = {}) {
    const objectCount = Number(params.object_count ?? params.objectCount);
    const maxTests = Number(params.max_tests ?? params.maxTests ?? params.test_count ?? params.testCount);
    const tests = subsetSignatureNormalizeTests(params.tests, objectCount, Number.isInteger(maxTests) ? maxTests : null);
    const states = subsetSignatureInitialStates(objectCount);
    const partitions = subsetSignaturePartitionStates({ object_count: objectCount, tests, currentStates: states });
    const conflicts = partitions.filter(part => part.states.length > 1);
    return {
      success: states.length > 0 && conflicts.length === 0,
      tests,
      states,
      partitions,
      conflicts,
      conflict: conflicts[0] || null
    };
  }

  function subsetSignatureChooseCheaterOutcome(params = {}) {
    const check = subsetSignatureCheckStrategy(params);
    const chosen = check.partitions.slice().sort((a, b) =>
      b.states.length - a.states.length || a.key.localeCompare(b.key, undefined, { numeric: true })
    )[0] || { key: '', signature: [], states: [] };
    return {
      ...chosen,
      candidates: chosen.states,
      partitions: check.partitions,
      scores: Object.fromEntries(check.partitions.map(part => [part.key, part.states.length])),
      success: check.success
    };
  }

  function subsetSignatureFilterStates(params = {}) {
    const objectCount = Number(params.object_count ?? params.objectCount);
    const maxTests = Number(params.max_tests ?? params.maxTests ?? params.test_count ?? params.testCount);
    const tests = subsetSignatureNormalizeTests(params.tests, objectCount, Number.isInteger(maxTests) ? maxTests : null);
    const signature = params.signature ?? params.counts ?? [];
    const key = subsetSignatureKey(signature);
    const currentStates = params.currentStates?.length ? params.currentStates : subsetSignatureInitialStates(objectCount);
    return currentStates
      .map(subsetSignatureNormalizeState)
      .filter(state => subsetSignatureKey(subsetSignatureForState(state, tests)) === key);
  }

  function subsetSignatureFinalizeAnswer(params = {}) {
    const objectCount = Number(params.object_count ?? params.objectCount);
    const candidates = params.currentStates?.length
      ? params.currentStates.map(subsetSignatureNormalizeState)
      : subsetSignatureInitialStates(objectCount);
    const selected = subsetSignatureNormalizeState(params.selectedObjects ?? params.selected_objects ?? []);
    const selectedKey = subsetSignatureStateKey(selected);
    if (candidates.length === 1) {
      const actualState = candidates[0];
      return { win: subsetSignatureStateKey(actualState) === selectedKey, actualState, candidates };
    }
    const actualState = candidates.find(state => subsetSignatureStateKey(state) !== selectedKey) ?? candidates[0] ?? null;
    return { win: false, actualState, candidates };
  }

  function balancedSubsetInitialStates(objectCount) {
    const count = Number(objectCount);
    if (!Number.isInteger(count) || count < 1 || count > 32) return [];
    return Array.from({ length: count }, (_item, index) => ({ number: index + 1 }));
  }

  function balancedSubsetNormalizeQuestions(questions, objectCount, maxTests = null) {
    const limit = Number(objectCount);
    if (!Number.isInteger(limit) || limit < 1) return [];
    const rows = Array.isArray(questions) ? questions : [];
    const normalized = rows.map(row => uniqueCoins(row, limit));
    const target = Number(maxTests);
    if (maxTests != null && Number.isInteger(target) && target >= 0) {
      while (normalized.length < target) normalized.push([]);
      return normalized.slice(0, target);
    }
    return normalized;
  }

  function balancedSubsetQuestionSum(question) {
    return (question || []).reduce((sum, number) => sum + Number(number || 0), 0);
  }

  function balancedSubsetSignatureForState(state, questions) {
    const number = Number(state?.number ?? state);
    return (questions || []).map(question => (question || []).includes(number) ? 1 : 0);
  }

  function balancedSubsetSignatureKey(signature) {
    return (signature || []).join('');
  }

  function balancedSubsetStateKey(state) {
    return String(Number(state?.number ?? state));
  }

  function balancedSubsetValidateQuestions(params = {}) {
    const objectCount = Number(params.object_count ?? params.objectCount);
    const maxTests = Number(params.max_tests ?? params.maxTests ?? params.test_count ?? params.testCount);
    const targetSumRaw = params.target_sum ?? params.targetSum;
    const targetSum = targetSumRaw == null ? null : Number(targetSumRaw);
    const questions = balancedSubsetNormalizeQuestions(params.questions ?? params.tests, objectCount, Number.isInteger(maxTests) ? maxTests : null);
    const sums = questions.map(balancedSubsetQuestionSum);
    const filled = questions.filter(question => question.length > 0).length;
    const errors = [];
    if (!Number.isInteger(objectCount) || objectCount < 1) errors.push('Некорректное число вариантов.');
    if (!Number.isInteger(maxTests) || maxTests < 1) errors.push('Некорректное число вопросов.');
    if (filled !== questions.length) errors.push('Каждый вопрос должен содержать хотя бы одно число.');
    if (Number.isInteger(targetSum)) {
      sums.forEach((sum, index) => {
        if (sum !== targetSum) errors.push(`Сумма в вопросе ${index + 1} равна ${sum}, а нужна ${targetSum}.`);
      });
    } else {
      const nonEmptySums = sums.filter((_sum, index) => questions[index]?.length);
      const first = nonEmptySums[0];
      nonEmptySums.forEach((sum, index) => {
        if (sum !== first) errors.push(`Сумма в вопросе ${index + 1} отличается от остальных.`);
      });
    }
    return {
      ok: errors.length === 0,
      questions,
      sums,
      targetSum: Number.isInteger(targetSum) ? targetSum : null,
      errors,
      filled
    };
  }

  function balancedSubsetPartitionStates(params = {}) {
    const objectCount = Number(params.object_count ?? params.objectCount);
    const maxTests = Number(params.max_tests ?? params.maxTests ?? params.test_count ?? params.testCount);
    const questions = balancedSubsetNormalizeQuestions(params.questions ?? params.tests, objectCount, Number.isInteger(maxTests) ? maxTests : null);
    const currentStates = params.currentStates?.length ? params.currentStates : balancedSubsetInitialStates(objectCount);
    const bySignature = new Map();
    for (const state of currentStates) {
      const signature = balancedSubsetSignatureForState(state, questions);
      const key = balancedSubsetSignatureKey(signature);
      if (!bySignature.has(key)) bySignature.set(key, { key, signature, states: [] });
      bySignature.get(key).states.push({ number: Number(state?.number ?? state) });
    }
    return [...bySignature.values()].sort((a, b) =>
      a.key.localeCompare(b.key, undefined, { numeric: true })
    );
  }

  function balancedSubsetCheckStrategy(params = {}) {
    const objectCount = Number(params.object_count ?? params.objectCount);
    const validation = balancedSubsetValidateQuestions(params);
    const states = balancedSubsetInitialStates(objectCount);
    const partitions = balancedSubsetPartitionStates({ ...params, questions: validation.questions, currentStates: states });
    const conflicts = partitions.filter(part => part.states.length > 1);
    return {
      success: validation.ok && states.length > 0 && conflicts.length === 0,
      questions: validation.questions,
      sums: validation.sums,
      targetSum: validation.targetSum,
      validation,
      states,
      partitions,
      conflicts,
      conflict: conflicts[0] || null
    };
  }

  function balancedSubsetFilterStates(params = {}) {
    const objectCount = Number(params.object_count ?? params.objectCount);
    const maxTests = Number(params.max_tests ?? params.maxTests ?? params.test_count ?? params.testCount);
    const questions = balancedSubsetNormalizeQuestions(params.questions ?? params.tests, objectCount, Number.isInteger(maxTests) ? maxTests : null);
    const signature = params.signature ?? [];
    const key = balancedSubsetSignatureKey(signature);
    const currentStates = params.currentStates?.length ? params.currentStates : balancedSubsetInitialStates(objectCount);
    return currentStates
      .map(state => ({ number: Number(state?.number ?? state) }))
      .filter(state => balancedSubsetSignatureKey(balancedSubsetSignatureForState(state, questions)) === key);
  }

  function balancedSubsetChooseRandom(params = {}) {
    const states = balancedSubsetInitialStates(params.object_count ?? params.objectCount);
    return states[Math.floor(Math.random() * states.length)] || null;
  }

  function binaryCardsNumberRange(params = {}) {
    const min = Number(params.number_min ?? params.numberMin ?? params.min_number ?? params.minNumber ?? 1);
    const max = Number(params.number_max ?? params.numberMax ?? params.max_number ?? params.maxNumber ?? params.object_count ?? params.objectCount ?? 31);
    return {
      min: Number.isInteger(min) && min >= 0 ? min : 1,
      max: Number.isInteger(max) && max >= min ? max : 31
    };
  }

  function binaryCardsWeights(params = {}) {
    const rawWeights = Array.isArray(params.card_weights ?? params.cardWeights)
      ? params.card_weights ?? params.cardWeights
      : [];
    const cardCount = Number(params.card_count ?? params.cardCount ?? rawWeights.length ?? 5);
    const limit = Number.isInteger(cardCount) && cardCount >= 1 && cardCount <= 10 ? cardCount : 5;
    const weights = rawWeights
      .map(Number)
      .filter(weight => Number.isInteger(weight) && weight > 0)
      .slice(0, limit);
    while (weights.length < limit) weights.push(2 ** weights.length);
    return [...new Set(weights)].slice(0, limit);
  }

  function binaryCardsAllNumbers(params = {}) {
    const range = binaryCardsNumberRange(params);
    if (range.max < range.min) return [];
    return Array.from({ length: range.max - range.min + 1 }, (_item, index) => range.min + index);
  }

  function binaryCardsCards(params = {}) {
    const weights = binaryCardsWeights(params);
    const numbers = binaryCardsAllNumbers(params);
    return weights.map((weight, index) => ({
      index,
      weight,
      numbers: numbers.filter(number => (number & weight) !== 0)
    }));
  }

  function binaryCardsNormalizeSelection(selection, params = {}) {
    const weights = binaryCardsWeights(params);
    const allowed = new Set(weights);
    const raw = selection ?? params.selection ?? params.selected_weights ?? params.selectedWeights ?? params.cards ?? [];
    const seen = new Set();
    const result = [];
    for (const item of raw || []) {
      const weight = Number(item?.weight ?? item?.value ?? item);
      if (!Number.isInteger(weight) || !allowed.has(weight) || seen.has(weight)) continue;
      seen.add(weight);
      result.push(weight);
    }
    return result.sort((a, b) => a - b);
  }

  function binaryCardsSelectionForNumber(number, params = {}) {
    const hidden = Number(number?.number ?? number);
    if (!Number.isInteger(hidden)) return [];
    return binaryCardsWeights(params).filter(weight => (hidden & weight) !== 0);
  }

  function binaryCardsDecodeSelection(selection, params = {}) {
    return binaryCardsNormalizeSelection(selection, params).reduce((sum, weight) => sum + weight, 0);
  }

  function binaryCardsEvaluate(params = {}) {
    const hidden = Number(params.number ?? params.hiddenNumber ?? params.hidden_number);
    const selection = binaryCardsNormalizeSelection(params.selection ?? params.selected_weights ?? params.selectedWeights, params);
    const decoded = binaryCardsDecodeSelection(selection, params);
    const expectedSelection = binaryCardsSelectionForNumber(hidden, params);
    const expectedDecoded = binaryCardsDecodeSelection(expectedSelection, params);
    const range = binaryCardsNumberRange(params);
    return {
      hidden,
      selection,
      decoded,
      expectedSelection,
      expectedDecoded,
      validHidden: Number.isInteger(hidden) && hidden >= range.min && hidden <= range.max,
      correctSelection: selection.join('|') === expectedSelection.join('|'),
      win: Number.isInteger(hidden) && decoded === hidden && hidden >= range.min && hidden <= range.max
    };
  }

  function binaryCardsExhaustiveCheck(params = {}) {
    const numbers = binaryCardsAllNumbers(params);
    const rows = numbers.map(number => {
      const selection = binaryCardsSelectionForNumber(number, params);
      const decoded = binaryCardsDecodeSelection(selection, params);
      return {
        number,
        selection,
        decoded,
        ok: decoded === number
      };
    });
    const byCode = new Map();
    for (const row of rows) {
      const key = row.selection.join('|');
      if (!byCode.has(key)) byCode.set(key, []);
      byCode.get(key).push(row.number);
    }
    const collisions = [...byCode.entries()]
      .filter(([_key, values]) => values.length > 1)
      .map(([key, values]) => ({ key, numbers: values }));
    return {
      success: rows.every(row => row.ok) && collisions.length === 0,
      checked: rows.length,
      rows,
      collisions,
      cards: binaryCardsCards(params)
    };
  }

  function binaryCardsChooseRandom(params = {}) {
    const numbers = binaryCardsAllNumbers(params);
    return numbers[Math.floor(Math.random() * numbers.length)] ?? null;
  }

  function fixedFeedbackAlphabet(params = {}) {
    const rawAlphabet = Array.isArray(params.alphabet)
      ? params.alphabet
      : ['A', 'B', 'C', 'D', 'E'];
    const seen = new Set();
    const result = [];
    for (const item of rawAlphabet) {
      const letter = String(item || '').trim().toUpperCase();
      if (!letter || seen.has(letter)) continue;
      seen.add(letter);
      result.push(letter);
    }
    return result.length ? result : ['A', 'B', 'C', 'D', 'E'];
  }

  function fixedFeedbackPasswordLength(params = {}) {
    const length = Number(params.password_length ?? params.passwordLength ?? params.word_length ?? params.wordLength ?? 10);
    return Number.isInteger(length) && length >= 1 && length <= 20 ? length : 10;
  }

  function fixedFeedbackMaxTests(params = {}) {
    const alphabet = fixedFeedbackAlphabet(params);
    const tests = Number(params.max_tests ?? params.maxTests ?? params.feedback_attempts ?? params.feedbackAttempts ?? alphabet.length - 1);
    return Number.isInteger(tests) && tests >= 0 && tests <= 20 ? tests : Math.max(0, alphabet.length - 1);
  }

  function fixedFeedbackStateCount(params = {}) {
    return fixedFeedbackAlphabet(params).length ** fixedFeedbackPasswordLength(params);
  }

  function fixedFeedbackNormalizeWord(word, params = {}) {
    const alphabet = fixedFeedbackAlphabet(params);
    const allowed = new Set(alphabet);
    const raw = String(word || '').trim().toUpperCase().replace(/\s+/g, '');
    const letters = Array.from(raw);
    const length = fixedFeedbackPasswordLength(params);
    return {
      word: letters.join(''),
      letters,
      valid: letters.length === length && letters.every(letter => allowed.has(letter)),
      length,
      alphabet
    };
  }

  function fixedFeedbackRandomPassword(params = {}) {
    const alphabet = fixedFeedbackAlphabet(params);
    const length = fixedFeedbackPasswordLength(params);
    let word = '';
    for (let index = 0; index < length; index += 1) {
      word += alphabet[Math.floor(Math.random() * alphabet.length)];
    }
    return word;
  }

  function fixedFeedbackFeedback(secret, guess, params = {}) {
    const normalizedSecret = fixedFeedbackNormalizeWord(secret, params);
    const normalizedGuess = fixedFeedbackNormalizeWord(guess, params);
    if (!normalizedSecret.valid || !normalizedGuess.valid) return [];
    const positions = [];
    for (let index = 0; index < normalizedSecret.length; index += 1) {
      if (normalizedSecret.letters[index] === normalizedGuess.letters[index]) positions.push(index + 1);
    }
    return positions;
  }

  function fixedFeedbackNormalizePositions(positions, params = {}) {
    const length = fixedFeedbackPasswordLength(params);
    const seen = new Set();
    const result = [];
    for (const item of positions || []) {
      const position = Number(item);
      if (!Number.isInteger(position) || position < 1 || position > length || seen.has(position)) continue;
      seen.add(position);
      result.push(position);
    }
    return result.sort((a, b) => a - b);
  }

  function fixedFeedbackInitialKnowledge(params = {}) {
    const alphabet = fixedFeedbackAlphabet(params);
    return Array.from({ length: fixedFeedbackPasswordLength(params) }, () => alphabet.slice());
  }

  function fixedFeedbackKnowledgeFromHistory(history = [], params = {}) {
    const knowledge = fixedFeedbackInitialKnowledge(params);
    for (const step of history || []) {
      const guess = fixedFeedbackNormalizeWord(step.guess ?? step.attempt ?? step.word, params);
      if (!guess.valid) continue;
      const matches = new Set(fixedFeedbackNormalizePositions(step.matches ?? step.positions ?? step.feedback, params));
      for (let index = 0; index < knowledge.length; index += 1) {
        const letter = guess.letters[index];
        if (matches.has(index + 1)) {
          knowledge[index] = knowledge[index].includes(letter) ? [letter] : [];
        } else {
          knowledge[index] = knowledge[index].filter(item => item !== letter);
        }
      }
    }
    return knowledge;
  }

  function fixedFeedbackCandidateCount(knowledgeOrHistory = [], params = {}) {
    const knowledge = Array.isArray(knowledgeOrHistory?.[0])
      ? knowledgeOrHistory
      : fixedFeedbackKnowledgeFromHistory(knowledgeOrHistory, params);
    return knowledge.reduce((product, letters) => product * Math.max(0, letters.length), 1);
  }

  function fixedFeedbackKnownPassword(knowledgeOrHistory = [], params = {}) {
    const knowledge = Array.isArray(knowledgeOrHistory?.[0])
      ? knowledgeOrHistory
      : fixedFeedbackKnowledgeFromHistory(knowledgeOrHistory, params);
    return knowledge.every(letters => letters.length === 1)
      ? knowledge.map(letters => letters[0]).join('')
      : null;
  }

  function fixedFeedbackUniformGuess(letterIndex, params = {}) {
    const alphabet = fixedFeedbackAlphabet(params);
    const index = Number(letterIndex);
    const letter = Number.isInteger(index) && index >= 0 && index < alphabet.length
      ? alphabet[index]
      : alphabet[0];
    return letter.repeat(fixedFeedbackPasswordLength(params));
  }

  function fixedFeedbackStrategyHistory(secret, params = {}) {
    const maxTests = fixedFeedbackMaxTests(params);
    const alphabet = fixedFeedbackAlphabet(params);
    const testCount = Math.min(maxTests, Math.max(0, alphabet.length - 1));
    return Array.from({ length: testCount }, (_item, index) => {
      const guess = fixedFeedbackUniformGuess(index, params);
      return {
        guess,
        matches: fixedFeedbackFeedback(secret, guess, params)
      };
    });
  }

  function fixedFeedbackFinalizeAnswer(params = {}) {
    const history = params.history ?? params.transcript ?? [];
    const answer = fixedFeedbackNormalizeWord(params.answer ?? params.guess ?? params.password, params);
    const secret = fixedFeedbackNormalizeWord(params.secret ?? params.hidden ?? params.hiddenPassword, params);
    const knowledge = fixedFeedbackKnowledgeFromHistory(history, params);
    const knownPassword = fixedFeedbackKnownPassword(knowledge, params);
    const candidateCount = fixedFeedbackCandidateCount(knowledge, params);
    return {
      answer: answer.word,
      validAnswer: answer.valid,
      secret: secret.valid ? secret.word : null,
      knownPassword,
      candidateCount,
      win: answer.valid && secret.valid && answer.word === secret.word,
      followsFeedback: answer.valid && answer.letters.every((letter, index) => knowledge[index].includes(letter))
    };
  }

  function fixedFeedbackExhaustiveCheck(params = {}) {
    const alphabet = fixedFeedbackAlphabet(params);
    const length = fixedFeedbackPasswordLength(params);
    const maxTests = fixedFeedbackMaxTests(params);
    const requiredTests = Math.max(0, alphabet.length - 1);
    const checked = alphabet.length ** length;
    const success = maxTests >= requiredTests;
    return {
      success,
      checked,
      alphabet,
      length,
      maxTests,
      requiredTests,
      candidateCountAfterStrategy: success ? 1 : alphabet.length ** Math.max(0, length),
      rows: alphabet.slice(0, requiredTests).map((letter, index) => ({
        test: index + 1,
        letter,
        guess: fixedFeedbackUniformGuess(index, params)
      }))
    };
  }

  function ternaryQuestionObjectCount(params = {}) {
    const count = Number(params.object_count ?? params.objectCount ?? params.number_max ?? params.numberMax ?? 27);
    return Number.isInteger(count) && count >= 1 && count <= 729 ? count : 27;
  }

  function ternaryQuestionMaxTests(params = {}) {
    const tests = Number(params.max_tests ?? params.maxTests ?? params.question_count ?? params.questionCount ?? 3);
    return Number.isInteger(tests) && tests >= 1 && tests <= 6 ? tests : 3;
  }

  function ternaryQuestionAlphabet(params = {}) {
    const raw = params.alphabet ?? params.answer_alphabet ?? params.answerAlphabet ?? params.outcome_labels ?? params.outcomeLabels;
    const labels = Array.isArray(raw) ? raw.map(String).filter(Boolean).slice(0, 3) : [];
    while (labels.length < 3) labels.push(String(labels.length));
    return labels;
  }

  function ternaryQuestionInitialStates(params = {}) {
    const count = ternaryQuestionObjectCount(params);
    return Array.from({ length: count }, (_item, index) => ({ number: index + 1 }));
  }

  function ternaryQuestionNormalizeOutcomes(outcomes, params = {}) {
    const alphabet = ternaryQuestionAlphabet(params);
    const maxTests = ternaryQuestionMaxTests(params);
    const raw = Array.isArray(outcomes) ? outcomes : [];
    const result = raw.slice(0, maxTests).map(item => {
      const numeric = Number(item);
      if (Number.isInteger(numeric) && numeric >= 0 && numeric <= 2) return numeric;
      const labelIndex = alphabet.indexOf(String(item));
      return labelIndex >= 0 ? labelIndex : 0;
    });
    while (result.length < maxTests) result.push(0);
    return result;
  }

  function ternaryQuestionCodeForState(state, params = {}) {
    const maxTests = ternaryQuestionMaxTests(params);
    const number = Number(state?.number ?? state);
    if (!Number.isInteger(number) || number < 1) return Array.from({ length: maxTests }, () => 0);
    let value = number - 1;
    const digits = Array.from({ length: maxTests }, () => 0);
    for (let index = maxTests - 1; index >= 0; index -= 1) {
      digits[index] = value % 3;
      value = Math.floor(value / 3);
    }
    return digits;
  }

  function ternaryQuestionCodeKey(outcomes, params = {}) {
    return ternaryQuestionNormalizeOutcomes(outcomes, params).join('');
  }

  function ternaryQuestionDecodeOutcomes(outcomes, params = {}) {
    const digits = ternaryQuestionNormalizeOutcomes(outcomes, params);
    const value = digits.reduce((total, digit) => total * 3 + digit, 0);
    const number = value + 1;
    const objectCount = ternaryQuestionObjectCount(params);
    return {
      number,
      value,
      digits,
      inRange: number >= 1 && number <= objectCount
    };
  }

  function ternaryQuestionChooseRandom(params = {}) {
    const states = ternaryQuestionInitialStates(params);
    return states[Math.floor(Math.random() * states.length)]?.number ?? null;
  }

  function ternaryQuestionEvaluate(params = {}) {
    const hidden = Number(params.number ?? params.hidden ?? params.hidden_number ?? params.hiddenNumber);
    const outcomes = ternaryQuestionNormalizeOutcomes(params.outcomes ?? params.answers ?? params.code, params);
    const decoded = ternaryQuestionDecodeOutcomes(outcomes, params);
    const expectedOutcomes = ternaryQuestionCodeForState(hidden, params);
    const range = ternaryQuestionObjectCount(params);
    return {
      hidden,
      outcomes,
      decoded: decoded.number,
      decodedState: decoded,
      expectedOutcomes,
      validHidden: Number.isInteger(hidden) && hidden >= 1 && hidden <= range,
      correctOutcomes: outcomes.join('') === expectedOutcomes.join(''),
      win: Number.isInteger(hidden) && hidden >= 1 && hidden <= range && decoded.number === hidden
    };
  }

  function ternaryQuestionExhaustiveCheck(params = {}) {
    const states = ternaryQuestionInitialStates(params);
    const rows = states.map(state => {
      const outcomes = ternaryQuestionCodeForState(state, params);
      const decodedState = ternaryQuestionDecodeOutcomes(outcomes, params);
      return {
        number: state.number,
        outcomes,
        decoded: decodedState.number,
        ok: decodedState.number === state.number && decodedState.inRange
      };
    });
    const byCode = new Map();
    for (const row of rows) {
      const key = ternaryQuestionCodeKey(row.outcomes, params);
      if (!byCode.has(key)) byCode.set(key, []);
      byCode.get(key).push(row.number);
    }
    const collisions = [...byCode.entries()]
      .filter(([_key, values]) => values.length > 1)
      .map(([key, values]) => ({ key, numbers: values }));
    return {
      success: rows.every(row => row.ok) && collisions.length === 0 && rows.length <= 3 ** ternaryQuestionMaxTests(params),
      checked: rows.length,
      rows,
      collisions
    };
  }

  function repetitionCodeBitCount(params = {}) {
    const bitCount = Number(params.bit_count ?? params.bitCount ?? 3);
    return Number.isInteger(bitCount) && bitCount >= 1 && bitCount <= 10 ? bitCount : 3;
  }

  function repetitionCodeRepetitions(params = {}) {
    const repetitions = Number(params.repetitions_per_bit ?? params.repetitionsPerBit ?? 3);
    return Number.isInteger(repetitions) && repetitions >= 1 && repetitions <= 9 ? repetitions : 3;
  }

  function repetitionCodeMaxLies(params = {}) {
    const maxLies = Number(params.max_lies ?? params.maxLies ?? 1);
    return Number.isInteger(maxLies) && maxLies >= 0 ? maxLies : 1;
  }

  function repetitionCodeNumberRange(params = {}) {
    const bitCount = repetitionCodeBitCount(params);
    const min = Number(params.number_min ?? params.numberMin ?? 0);
    const max = Number(params.number_max ?? params.numberMax ?? (2 ** bitCount - 1));
    const safeMin = Number.isInteger(min) && min >= 0 ? min : 0;
    const safeMax = Number.isInteger(max) && max >= safeMin && max < 2 ** bitCount ? max : 2 ** bitCount - 1;
    return { min: safeMin, max: safeMax };
  }

  function repetitionCodeAllNumbers(params = {}) {
    const range = repetitionCodeNumberRange(params);
    return Array.from({ length: range.max - range.min + 1 }, (_item, index) => range.min + index);
  }

  function repetitionCodeQuestionCount(params = {}) {
    return repetitionCodeBitCount(params) * repetitionCodeRepetitions(params);
  }

  function repetitionCodeQuestionRows(params = {}) {
    const bitCount = repetitionCodeBitCount(params);
    const repetitions = repetitionCodeRepetitions(params);
    const rows = [];
    for (let bit = 0; bit < bitCount; bit += 1) {
      for (let repeat = 0; repeat < repetitions; repeat += 1) {
        rows.push({
          index: rows.length,
          bit,
          repeat,
          weight: 2 ** bit
        });
      }
    }
    return rows;
  }

  function repetitionCodeTruthAnswers(number, params = {}) {
    const hidden = Number(number?.number ?? number);
    return repetitionCodeQuestionRows(params).map(row => ((hidden >> row.bit) & 1) === 1);
  }

  function repetitionCodeNormalizeLieIndex(lieIndex, params = {}) {
    if (lieIndex == null || lieIndex === '' || lieIndex === 'none') return -1;
    const index = Number(lieIndex);
    return Number.isInteger(index) && index >= 0 && index < repetitionCodeQuestionCount(params) ? index : -1;
  }

  function repetitionCodeAnswersForCase(params = {}) {
    const hidden = Number(params.number ?? params.hidden ?? params.hiddenNumber ?? params.hidden_number);
    const lieIndex = repetitionCodeNormalizeLieIndex(params.lieIndex ?? params.lie_index, params);
    const answers = repetitionCodeTruthAnswers(hidden, params);
    if (lieIndex >= 0) answers[lieIndex] = !answers[lieIndex];
    return answers;
  }

  function repetitionCodeNormalizeAnswers(answers, params = {}) {
    const expectedLength = repetitionCodeQuestionCount(params);
    const raw = Array.isArray(answers ?? params.answers) ? answers ?? params.answers : [];
    return Array.from({ length: expectedLength }, (_item, index) => {
      const value = raw[index];
      return value === true || value === 1 || value === '1' || value === 'yes' || value === 'true';
    });
  }

  function repetitionCodeDecodeAnswers(answers, params = {}) {
    const normalized = repetitionCodeNormalizeAnswers(answers, params);
    const bitCount = repetitionCodeBitCount(params);
    const repetitions = repetitionCodeRepetitions(params);
    const groups = [];
    let decoded = 0;
    for (let bit = 0; bit < bitCount; bit += 1) {
      const groupAnswers = normalized.slice(bit * repetitions, (bit + 1) * repetitions);
      const yesCount = groupAnswers.filter(Boolean).length;
      const noCount = groupAnswers.length - yesCount;
      const bitValue = yesCount > noCount ? 1 : 0;
      if (bitValue) decoded += 2 ** bit;
      groups.push({
        bit,
        weight: 2 ** bit,
        answers: groupAnswers,
        yesCount,
        noCount,
        bitValue
      });
    }
    return { answers: normalized, groups, decoded };
  }

  function repetitionCodeEvaluate(params = {}) {
    const hidden = Number(params.number ?? params.hidden ?? params.hiddenNumber ?? params.hidden_number);
    const answers = params.answers ? repetitionCodeNormalizeAnswers(params.answers, params) : repetitionCodeAnswersForCase(params);
    const decoded = repetitionCodeDecodeAnswers(answers, params);
    const truth = Number.isInteger(hidden) ? repetitionCodeTruthAnswers(hidden, params) : [];
    const liePositions = truth.length
      ? answers.map((answer, index) => answer !== truth[index] ? index : null).filter(index => index != null)
      : [];
    const range = repetitionCodeNumberRange(params);
    const validHidden = Number.isInteger(hidden) && hidden >= range.min && hidden <= range.max;
    return {
      hidden,
      lieIndex: repetitionCodeNormalizeLieIndex(params.lieIndex ?? params.lie_index, params),
      answers,
      truth,
      groups: decoded.groups,
      decoded: decoded.decoded,
      liePositions,
      lieCount: liePositions.length,
      validHidden,
      win: validHidden && decoded.decoded === hidden && liePositions.length <= repetitionCodeMaxLies(params)
    };
  }

  function repetitionCodeChooseRandom(params = {}, random = Math.random) {
    const numbers = repetitionCodeAllNumbers(params);
    const questionCount = repetitionCodeQuestionCount(params);
    const number = numbers[Math.floor(random() * numbers.length)] ?? null;
    const lieIndex = Math.floor(random() * (questionCount + 1)) - 1;
    return {
      number,
      lieIndex,
      answers: repetitionCodeAnswersForCase({ ...params, number, lieIndex })
    };
  }

  function repetitionCodeExhaustiveCheck(params = {}) {
    const rows = [];
    const questionCount = repetitionCodeQuestionCount(params);
    for (const number of repetitionCodeAllNumbers(params)) {
      for (let lieIndex = -1; lieIndex < questionCount; lieIndex += 1) {
        const check = repetitionCodeEvaluate({ ...params, number, lieIndex });
        rows.push({
          number,
          lieIndex,
          answers: check.answers,
          decoded: check.decoded,
          lieCount: check.lieCount,
          ok: check.win
        });
      }
    }
    return {
      success: rows.every(row => row.ok),
      checked: rows.length,
      rows,
      failures: rows.filter(row => !row.ok)
    };
  }

  function finiteBinaryProtocol(params = {}) {
    return String(params.protocol ?? params.model ?? params.state_model ?? '').toLowerCase();
  }

  function finiteBinaryStateKey(state) {
    return String(state?.id ?? state?.key ?? '');
  }

  function finiteBinaryActionKey(action) {
    return String(action?.id ?? action?.key ?? '');
  }

  function finiteBinaryOtherPerson(person, people) {
    return (people || []).find(item => item !== person) || '';
  }

  function finiteBinaryNormalizePeople(people) {
    const labels = (Array.isArray(people) && people.length ? people : ['Вася', 'Петя'])
      .map(item => String(item || '').trim())
      .filter(Boolean);
    return [...new Set(labels)];
  }

  function finiteBinaryGridSize(params = {}) {
    const rows = Number(params.grid_rows ?? params.gridRows ?? params.rows ?? 10);
    const cols = Number(params.grid_cols ?? params.gridCols ?? params.columns ?? params.cols ?? 10);
    return {
      rows: Number.isInteger(rows) && rows >= 2 && rows <= 30 ? rows : 0,
      cols: Number.isInteger(cols) && cols >= 2 && cols <= 30 ? cols : 0
    };
  }

  function finiteBinaryGridCellKey(row, col) {
    return `r${row}c${col}`;
  }

  function finiteBinaryGridCellLabel(row, col) {
    return `${row}:${col}`;
  }

  function finiteBinaryNormalizeCell(raw) {
    if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
      const row = Number(raw.row ?? raw.r);
      const col = Number(raw.col ?? raw.column ?? raw.c);
      if (Number.isInteger(row) && Number.isInteger(col)) {
        return { row, col, key: finiteBinaryGridCellKey(row, col) };
      }
    }
    const text = String(raw ?? '').trim();
    const match = text.match(/(\d+)\D+(\d+)/);
    if (match) {
      const row = Number(match[1]);
      const col = Number(match[2]);
      if (Number.isInteger(row) && Number.isInteger(col)) {
        return { row, col, key: finiteBinaryGridCellKey(row, col) };
      }
    }
    return null;
  }

  function finiteBinaryAdjacentGridStates(params = {}) {
    const { rows, cols } = finiteBinaryGridSize(params);
    if (!rows || !cols) return [];
    const states = [];
    function pushPair(first, second) {
      const firstKey = finiteBinaryGridCellKey(first.row, first.col);
      const secondKey = finiteBinaryGridCellKey(second.row, second.col);
      states.push({
        id: `${firstKey}_${secondKey}`,
        label: `${finiteBinaryGridCellLabel(first.row, first.col)} и ${finiteBinaryGridCellLabel(second.row, second.col)}`,
        cells: [firstKey, secondKey],
        pair: [firstKey, secondKey],
        coordinates: [first, second],
        data: { cells: [firstKey, secondKey], coordinates: [first, second] }
      });
    }
    for (let row = 1; row <= rows; row += 1) {
      for (let col = 1; col <= cols; col += 1) {
        if (col < cols) pushPair({ row, col }, { row, col: col + 1 });
        if (row < rows) pushPair({ row, col }, { row: row + 1, col });
      }
    }
    return states;
  }

  function finiteBinaryAdjacentGridActions(params = {}) {
    const { rows, cols } = finiteBinaryGridSize(params);
    if (!rows || !cols) return [];
    const actions = [];
    for (let row = 1; row <= rows; row += 1) {
      for (let col = 1; col <= cols; col += 1) {
        const cell = finiteBinaryGridCellKey(row, col);
        actions.push({
          id: `ask_${cell}`,
          label: finiteBinaryGridCellLabel(row, col),
          cell,
          row,
          col,
          data: { cell, row, col }
        });
      }
    }
    return actions;
  }

  function finiteBinaryAdjacentGridStateCells(state) {
    const rawCells = state?.cells ?? state?.pair ?? state?.data?.cells ?? state?.data?.pair;
    if (Array.isArray(rawCells) && rawCells.length) {
      return rawCells.map(cell => {
        const normalized = finiteBinaryNormalizeCell(cell);
        return normalized?.key || String(cell);
      });
    }
    const coordinates = state?.coordinates ?? state?.data?.coordinates;
    if (Array.isArray(coordinates) && coordinates.length) {
      return coordinates.map(cell => finiteBinaryNormalizeCell(cell)?.key).filter(Boolean);
    }
    return [];
  }

  function finiteBinaryAdjacentGridActionCell(action) {
    const direct = action?.cell ?? action?.data?.cell;
    const normalizedDirect = finiteBinaryNormalizeCell(direct);
    if (normalizedDirect) return normalizedDirect.key;
    const row = Number(action?.row ?? action?.data?.row);
    const col = Number(action?.col ?? action?.data?.col);
    if (Number.isInteger(row) && Number.isInteger(col)) return finiteBinaryGridCellKey(row, col);
    return '';
  }

  function finiteBinaryNormalizeGridPair(raw, params = {}) {
    const { rows, cols } = finiteBinaryGridSize(params);
    const source = raw?.cells ?? raw?.pair ?? raw?.selectedCells ?? raw?.selected_cells ?? raw;
    const values = typeof source === 'string'
      ? (source.match(/r\d+c\d+|\d+\D+\d+/gi) || source.split(/[|_;]+/))
      : source;
    if (!Array.isArray(values) || values.length !== 2) return null;
    const cells = values.map(finiteBinaryNormalizeCell);
    if (cells.some(cell => !cell)) return null;
    if (cells.some(cell => cell.row < 1 || cell.row > rows || cell.col < 1 || cell.col > cols)) return null;
    const adjacent = Math.abs(cells[0].row - cells[1].row) + Math.abs(cells[0].col - cells[1].col) === 1;
    if (!adjacent) return null;
    return cells
      .slice()
      .sort((a, b) => a.row - b.row || a.col - b.col)
      .map(cell => cell.key);
  }

  function finiteBinaryInitialStates(params = {}) {
    const protocol = finiteBinaryProtocol(params);
    if (Array.isArray(params.states) && params.states.length) {
      return params.states
        .map((state, index) => ({
          ...state,
          id: String(state.id ?? state.key ?? `state_${index + 1}`),
          label: String(state.label ?? state.title ?? state.id ?? state.key ?? `состояние ${index + 1}`),
          data: state.data && typeof state.data === 'object' ? state.data : { ...state }
        }))
        .filter(state => state.id);
    }
    if (protocol === 'one_liar_line_neighborhood') {
      const count = Number(params.person_count ?? params.personCount ?? params.object_count ?? params.objectCount);
      if (!Number.isInteger(count) || count < 2 || count > 60) return [];
      return Array.from({ length: count }, (_item, index) => {
        const liar = index + 1;
        return {
          id: `liar_${liar}`,
          label: `лжец ${liar}`,
          liar,
          data: { liar }
        };
      });
    }
    if (protocol === 'knight_liar_fake_coin_subset') {
      const coinCount = Number(params.coin_count ?? params.coinCount);
      const people = finiteBinaryNormalizePeople(params.people ?? params.person_labels ?? params.personLabels);
      if (!Number.isInteger(coinCount) || coinCount < 2 || coinCount > 12 || people.length !== 2) return [];
      const states = [];
      for (let fakeCoin = 1; fakeCoin <= coinCount; fakeCoin += 1) {
        for (const knight of people) {
          const liar = finiteBinaryOtherPerson(knight, people);
          states.push({
            id: `fake_${fakeCoin}_knight_${knight}`,
            label: `фальшивая ${fakeCoin}, рыцарь ${knight}`,
            fakeCoin,
            knight,
            liar,
            data: { fake_coin: fakeCoin, fakeCoin, knight, liar }
          });
        }
      }
      return states;
    }
    if (protocol === 'adjacent_pair_grid_search') {
      return finiteBinaryAdjacentGridStates(params);
    }
    return [];
  }

  function finiteBinaryInitialActions(params = {}) {
    const protocol = finiteBinaryProtocol(params);
    if (Array.isArray(params.actions) && params.actions.length) {
      return params.actions
        .map((action, index) => ({
          ...action,
          id: String(action.id ?? action.key ?? `action_${index + 1}`),
          label: String(action.label ?? action.title ?? action.id ?? action.key ?? `действие ${index + 1}`),
          data: action.data && typeof action.data === 'object' ? action.data : { ...action }
        }))
        .filter(action => action.id);
    }
    if (protocol === 'one_liar_line_neighborhood') {
      const count = Number(params.person_count ?? params.personCount ?? params.object_count ?? params.objectCount);
      if (!Number.isInteger(count) || count < 2 || count > 60) return [];
      return Array.from({ length: count }, (_item, index) => {
        const person = index + 1;
        const window = [person - 1, person, person + 1].filter(item => item >= 1 && item <= count);
        return {
          id: `ask_${person}`,
          label: `спросить ${person}`,
          person,
          window,
          data: { person, window }
        };
      });
    }
    if (protocol === 'knight_liar_fake_coin_subset') {
      const coinCount = Number(params.coin_count ?? params.coinCount);
      const people = finiteBinaryNormalizePeople(params.people ?? params.person_labels ?? params.personLabels);
      const sizes = (Array.isArray(params.action_subset_sizes) && params.action_subset_sizes.length
        ? params.action_subset_sizes
        : [1, 2]).map(Number).filter(size => Number.isInteger(size) && size > 0 && size <= coinCount);
      if (!Number.isInteger(coinCount) || coinCount < 2 || coinCount > 12 || people.length !== 2) return [];
      const actions = [];
      function visit(start, size, subset) {
        if (subset.length === size) {
          for (const person of people) {
            actions.push({
              id: `ask_${person}_${subset.join('_')}`,
              label: `${person}: ${subset.join(', ')}`,
              person,
              subset: [...subset],
              data: { person, subset: [...subset] }
            });
          }
          return;
        }
        for (let coin = start; coin <= coinCount; coin += 1) {
          subset.push(coin);
          visit(coin + 1, size, subset);
          subset.pop();
        }
      }
      for (const size of [...new Set(sizes)]) visit(1, size, []);
      return actions;
    }
    if (protocol === 'adjacent_pair_grid_search') {
      return finiteBinaryAdjacentGridActions(params);
    }
    return [];
  }

  function finiteBinaryNormalizeStates(states, params = {}) {
    const allowed = new Set(finiteBinaryInitialStates(params).map(finiteBinaryStateKey));
    const seen = new Set();
    const result = [];
    for (const state of states || []) {
      const key = finiteBinaryStateKey(state);
      if (!key || seen.has(key)) continue;
      if (allowed.size && !allowed.has(key)) continue;
      seen.add(key);
      result.push(state);
    }
    return result;
  }

  function finiteBinaryNormalizeAnswer(value) {
    const text = String(value ?? '').trim().toLowerCase();
    if (['yes', 'y', 'true', '1', 'да'].includes(text)) return 'yes';
    if (['no', 'n', 'false', '0', 'нет'].includes(text)) return 'no';
    return null;
  }

  function finiteBinaryResponseFromTable(state, action, params = {}) {
    const table = params.response_table ?? params.responses;
    if (!table) return null;
    const stateKey = finiteBinaryStateKey(state);
    const actionKey = finiteBinaryActionKey(action);
    if (Array.isArray(table)) {
      const row = table.find(item =>
        String(item?.state ?? item?.state_id ?? item?.stateId) === stateKey
        && String(item?.action ?? item?.action_id ?? item?.actionId) === actionKey
      );
      return row ? finiteBinaryNormalizeAnswer(row.response ?? row.answer ?? row.outcome) : null;
    }
    if (typeof table === 'object') {
      const value = table?.[stateKey]?.[actionKey] ?? table?.[`${stateKey}:${actionKey}`];
      return finiteBinaryNormalizeAnswer(value);
    }
    return null;
  }

  function finiteBinaryResponseForState(state, action, params = {}) {
    const tableResponse = finiteBinaryResponseFromTable(state, action, params);
    if (tableResponse) return tableResponse;
    const protocol = finiteBinaryProtocol(params);
    if (protocol === 'one_liar_line_neighborhood') {
      const liar = Number(state?.liar ?? state?.data?.liar);
      const person = Number(action?.person ?? action?.data?.person);
      if (!Number.isInteger(liar) || !Number.isInteger(person)) return null;
      const includesSelf = params.query_includes_self === true || params.queryIncludesSelf === true;
      const trueAnswer = includesSelf
        ? Math.abs(liar - person) <= 1
        : Math.abs(liar - person) === 1;
      const spoken = liar === person ? !trueAnswer : trueAnswer;
      return spoken ? 'yes' : 'no';
    }
    if (protocol === 'knight_liar_fake_coin_subset') {
      const fakeCoin = Number(state?.fakeCoin ?? state?.fake_coin ?? state?.data?.fakeCoin ?? state?.data?.fake_coin);
      const knight = String(state?.knight ?? state?.data?.knight ?? '');
      const person = String(action?.person ?? action?.data?.person ?? '');
      const subset = uniqueCoins(action?.subset ?? action?.coins ?? action?.data?.subset ?? action?.data?.coins);
      if (!Number.isInteger(fakeCoin) || !person || !subset.length) return null;
      const trueAnswer = subset.includes(fakeCoin);
      const truthful = knight === person;
      return (truthful ? trueAnswer : !trueAnswer) ? 'yes' : 'no';
    }
    if (protocol === 'adjacent_pair_grid_search') {
      const cell = finiteBinaryAdjacentGridActionCell(action);
      if (!cell) return null;
      return finiteBinaryAdjacentGridStateCells(state).includes(cell) ? 'yes' : 'no';
    }
    return null;
  }

  function finiteBinaryCurrentStates(params = {}) {
    const current = params.currentStates ?? params.current_states ?? params.currentCandidates ?? params.current_candidates;
    const states = current?.length
      ? finiteBinaryNormalizeStates(current, params)
      : finiteBinaryInitialStates(params);
    return { states, actions: finiteBinaryInitialActions(params) };
  }

  function finiteBinaryFilterStates(params = {}) {
    const { states, actions } = finiteBinaryCurrentStates(params);
    const actionId = String(params.actionId ?? params.action_id ?? params.action ?? '');
    const action = params.action && typeof params.action === 'object'
      ? params.action
      : actions.find(item => finiteBinaryActionKey(item) === actionId);
    const response = finiteBinaryNormalizeAnswer(params.response ?? params.answer ?? params.outcome);
    if (!action || !response) return [];
    return states.filter(state => finiteBinaryResponseForState(state, action, params) === response);
  }

  function finiteBinaryPartitionStates(params = {}) {
    return Object.fromEntries(YES_NO_OUTCOMES.map(response => [
      response,
      finiteBinaryFilterStates({ ...params, response })
    ]));
  }

  function finiteBinaryGuaranteedAnswers(states, params = {}) {
    const objective = String(params.objective || '').toLowerCase();
    const current = states || [];
    if (objective === 'identify_state' || objective === 'identify_liar' || objective === 'identify_hidden_pair') {
      return current.length === 1 ? [finiteBinaryStateKey(current[0])] : [];
    }
    if (objective === 'identify_one_genuine_coin') {
      const coinCount = Number(params.coin_count ?? params.coinCount);
      if (!Number.isInteger(coinCount) || coinCount < 1) return [];
      const fakeCoins = new Set(current.map(state => Number(state?.fakeCoin ?? state?.fake_coin ?? state?.data?.fakeCoin ?? state?.data?.fake_coin)));
      const result = [];
      for (let coin = 1; coin <= coinCount; coin += 1) {
        if (!fakeCoins.has(coin)) result.push(coin);
      }
      return result;
    }
    return current.length === 1 ? [finiteBinaryStateKey(current[0])] : [];
  }

  function finiteBinaryBranchStatus(states, usedTests, maxTests, params = {}) {
    const current = finiteBinaryNormalizeStates(states || [], params);
    const used = Number(usedTests);
    const limit = Number(maxTests);
    if (finiteBinaryGuaranteedAnswers(current, params).length > 0) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function finiteBinaryChooseCheaterResponse(params = {}) {
    const partitions = finiteBinaryPartitionStates(params);
    const scored = YES_NO_OUTCOMES.map(response => {
      const states = partitions[response] || [];
      const solved = finiteBinaryGuaranteedAnswers(states, params).length > 0;
      return { response, states, solved };
    }).filter(item => item.states.length > 0);
    const chosen = scored.sort((a, b) =>
      b.states.length - a.states.length
      || Number(a.solved) - Number(b.solved)
      || YES_NO_OUTCOMES.indexOf(a.response) - YES_NO_OUTCOMES.indexOf(b.response)
    )[0] || { response: 'no', states: [], solved: false };
    return {
      response: chosen.response,
      outcome: chosen.response,
      label: YES_NO_LABELS[chosen.response],
      states: chosen.states,
      candidates: chosen.states,
      partitions,
      scores: Object.fromEntries(YES_NO_OUTCOMES.map(response => {
        const states = partitions[response] || [];
        return [response, {
          states: states.length,
          solved: finiteBinaryGuaranteedAnswers(states, params).length > 0,
          answers: finiteBinaryGuaranteedAnswers(states, params)
        }];
      }))
    };
  }

  function finiteBinaryExpandExhaustiveNode(params = {}) {
    const usedTests = Number(params.usedTests ?? params.used_tests ?? params.usedWeighings ?? params.used_weighings ?? 0);
    const maxTests = Number(params.maxTests ?? params.max_tests ?? 1);
    const partitions = finiteBinaryPartitionStates(params);
    const children = YES_NO_OUTCOMES
      .map(response => {
        const states = partitions[response] || [];
        return {
          response,
          outcome: response,
          label: YES_NO_LABELS[response],
          states,
          candidates: states,
          guaranteedAnswers: finiteBinaryGuaranteedAnswers(states, params),
          usedTests: usedTests + 1,
          usedWeighings: usedTests + 1,
          status: finiteBinaryBranchStatus(states, usedTests + 1, maxTests, params)
        };
      })
      .filter(child => child.states.length > 0);
    return { partitions, children };
  }

  function finiteBinaryFinalizeAnswer(params = {}) {
    const { states } = finiteBinaryCurrentStates(params);
    const objective = String(params.objective || '').toLowerCase();
    if (objective === 'identify_one_genuine_coin') {
      const selectedCoin = Number(params.selectedCoin ?? params.selected_coin ?? params.answer);
      const guaranteedAnswers = finiteBinaryGuaranteedAnswers(states, params);
      const actualState = states.find(state => Number(state?.fakeCoin ?? state?.fake_coin ?? state?.data?.fakeCoin ?? state?.data?.fake_coin) === selectedCoin) || states[0] || null;
      return {
        win: guaranteedAnswers.includes(selectedCoin),
        selectedCoin,
        actualState,
        states,
        candidates: states,
        guaranteedAnswers
      };
    }
    if (objective === 'identify_hidden_pair') {
      const selectedPair = finiteBinaryNormalizeGridPair(
        params.selectedPair ?? params.selected_pair ?? params.selectedCells ?? params.selected_cells ?? params.answer,
        params
      );
      const selectedKey = selectedPair?.join('_');
      const guaranteedAnswers = finiteBinaryGuaranteedAnswers(states, params).map(String);
      const actualState = states.find(state => finiteBinaryStateKey(state) !== selectedKey) || states[0] || null;
      return {
        win: Boolean(selectedKey && guaranteedAnswers.includes(selectedKey)),
        selectedPair,
        selectedStateId: selectedKey,
        actualState,
        states,
        candidates: states,
        guaranteedAnswers
      };
    }
    const selectedStateId = String(params.selectedStateId ?? params.selected_state_id ?? params.answer ?? '');
    const guaranteedAnswers = finiteBinaryGuaranteedAnswers(states, params).map(String);
    const actualState = states.find(state => finiteBinaryStateKey(state) !== selectedStateId) || states[0] || null;
    return {
      win: guaranteedAnswers.includes(selectedStateId),
      selectedStateId,
      actualState,
      states,
      candidates: states,
      guaranteedAnswers
    };
  }

  function finitePairCards(cardCount) {
    const count = Number(cardCount);
    if (!Number.isInteger(count) || count < 2) return [];
    return Array.from({ length: count }, (_item, index) => index + 1);
  }

  function finitePairAllPairs(cardCount) {
    const cards = finitePairCards(cardCount);
    const pairs = [];
    for (let first = 0; first < cards.length; first += 1) {
      for (let second = first + 1; second < cards.length; second += 1) {
        pairs.push([cards[first], cards[second]]);
      }
    }
    return pairs;
  }

  function finitePairNormalizePair(pair, cardCount = null) {
    let values = [];
    if (Array.isArray(pair)) {
      values = pair;
    } else if (typeof pair === 'string') {
      values = pair.split(/[^0-9]+/).filter(Boolean);
    } else if (pair && typeof pair === 'object') {
      values = [pair.first ?? pair.a ?? pair[0], pair.second ?? pair.b ?? pair[1]];
    }
    const limit = cardCount == null ? null : Number(cardCount);
    const result = uniqueCoins(values, Number.isInteger(limit) ? limit : null).sort((a, b) => a - b);
    return result.length === 2 ? result : null;
  }

  function finitePairKey(pair, cardCount = null) {
    const normalized = finitePairNormalizePair(pair, cardCount);
    return normalized ? normalized.join(',') : '';
  }

  function finitePairLabel(pair, cardCount = null) {
    const normalized = finitePairNormalizePair(pair, cardCount);
    return normalized ? normalized.join('-') : '';
  }

  function finitePairDisjoint(firstPair, secondPair, cardCount = null) {
    const first = finitePairNormalizePair(firstPair, cardCount);
    const second = finitePairNormalizePair(secondPair, cardCount);
    if (!first || !second) return false;
    const firstSet = new Set(first);
    return second.every(card => !firstSet.has(card));
  }

  function finitePairAllowedShownPairs(hiddenPair, cardCount) {
    return finitePairAllPairs(cardCount).filter(pair => finitePairDisjoint(hiddenPair, pair, cardCount));
  }

  function finitePairNormalizeAssignment(assignments, cardCount) {
    const result = {};
    if (!assignments) return result;
    if (Array.isArray(assignments)) {
      for (const entry of assignments) {
        const hiddenKey = finitePairKey(entry?.hiddenPair ?? entry?.hidden_pair ?? entry?.hidden, cardCount);
        const shownKey = finitePairKey(entry?.shownPair ?? entry?.shown_pair ?? entry?.shown, cardCount);
        if (hiddenKey) result[hiddenKey] = shownKey;
      }
      return result;
    }
    if (typeof assignments === 'object') {
      for (const [rawHidden, rawShown] of Object.entries(assignments)) {
        const hiddenKey = finitePairKey(rawHidden, cardCount);
        if (!hiddenKey) continue;
        const shownKey = finitePairKey(rawShown, cardCount);
        result[hiddenKey] = shownKey;
      }
    }
    return result;
  }

  function finitePairMatchingValidate(params = {}) {
    const cardCount = Number(params.card_count ?? params.cardCount ?? 5);
    const hiddenPairs = finitePairAllPairs(cardCount);
    const assignments = finitePairNormalizeAssignment(params.assignments ?? params.mapping ?? params.rows, cardCount);
    const requireComplete = params.requireComplete !== false && params.require_complete !== false;
    const errors = [];
    const rows = [];
    const shownToHidden = new Map();
    if (!Number.isInteger(cardCount) || cardCount < 4 || cardCount > 9) {
      return { ok: false, errors: ['Нужно от 4 до 9 карточек.'], rows: [], conflicts: [] };
    }
    for (const hiddenPair of hiddenPairs) {
      const hiddenKey = finitePairKey(hiddenPair, cardCount);
      const shownKey = assignments[hiddenKey] || '';
      const shownPair = shownKey ? finitePairNormalizePair(shownKey, cardCount) : null;
      const rowErrors = [];
      if (!shownKey) {
        if (requireComplete) rowErrors.push(`Для спрятанной пары ${finitePairLabel(hiddenPair)} не выбрана показываемая пара.`);
      } else if (!shownPair) {
        rowErrors.push(`Показываемая пара для ${finitePairLabel(hiddenPair)} записана неверно.`);
      } else if (!finitePairDisjoint(hiddenPair, shownPair, cardCount)) {
        rowErrors.push(`Пара ${finitePairLabel(shownPair)} пересекается со спрятанной парой ${finitePairLabel(hiddenPair)}.`);
      } else {
        if (!shownToHidden.has(shownKey)) shownToHidden.set(shownKey, []);
        shownToHidden.get(shownKey).push(hiddenKey);
      }
      rows.push({
        hiddenPair,
        hiddenKey,
        shownPair,
        shownKey,
        valid: rowErrors.length === 0 && Boolean(shownKey),
        errors: rowErrors
      });
      errors.push(...rowErrors);
    }
    const conflicts = [];
    for (const [shownKey, hiddenKeys] of shownToHidden.entries()) {
      if (hiddenKeys.length <= 1) continue;
      const conflict = {
        shownKey,
        shownPair: finitePairNormalizePair(shownKey, cardCount),
        hiddenKeys,
        hiddenPairs: hiddenKeys.map(key => finitePairNormalizePair(key, cardCount))
      };
      conflicts.push(conflict);
      errors.push(`Показанная пара ${finitePairLabel(shownKey, cardCount)} читается неоднозначно: ${hiddenKeys.map(key => finitePairLabel(key, cardCount)).join(' и ')}.`);
    }
    const complete = rows.every(row => Boolean(row.shownKey));
    return {
      ok: errors.length === 0 && (!requireComplete || complete),
      complete,
      cardCount,
      hiddenPairs,
      assignments,
      rows,
      conflicts,
      errors,
      decodedByShown: Object.fromEntries([...shownToHidden.entries()])
    };
  }

  function petyaVasyaCardCount(params = {}) {
    const count = Number(params.card_count ?? params.cardCount ?? 5);
    return Number.isInteger(count) && count === 5 ? count : 5;
  }

  function petyaVasyaCards(params = {}) {
    return Array.from({ length: petyaVasyaCardCount(params) }, (_item, index) => index + 1);
  }

  function petyaVasyaNextCard(card, offset = 1, params = {}) {
    const count = petyaVasyaCardCount(params);
    const value = Number(card);
    if (!Number.isInteger(value) || value < 1 || value > count) return null;
    return ((value - 1 + offset + count * 10) % count) + 1;
  }

  function petyaVasyaNormalizeDistribution(raw, params = {}) {
    const count = petyaVasyaCardCount(params);
    const cards = petyaVasyaCards(params);
    const petyaCount = Number(params.petya_count ?? params.petyaCount ?? 2);
    const vasyaCount = Number(params.vasya_count ?? params.vasyaCount ?? 1);
    const spectatorCount = Number(params.spectator_count ?? params.spectatorCount ?? 2);
    const source = raw && typeof raw === 'object' ? raw : {};
    const ownerMap = source.owners ?? source.ownerMap ?? null;
    let petya = [];
    let vasya = [];
    let spectators = [];
    if (ownerMap && typeof ownerMap === 'object' && !Array.isArray(ownerMap)) {
      for (const card of cards) {
        const owner = String(ownerMap[card] ?? ownerMap[String(card)] ?? '').toLowerCase();
        if (owner === 'petya' || owner === 'петя') petya.push(card);
        else if (owner === 'vasya' || owner === 'вася') vasya.push(card);
        else if (owner === 'spectator' || owner === 'spectators' || owner === 'viewer' || owner === 'зрители') spectators.push(card);
      }
    } else {
      petya = uniqueCoins(source.petya ?? source.petyaCards ?? source.petya_cards, count);
      vasya = uniqueCoins(source.vasya ?? source.vasyaCards ?? source.vasya_cards, count);
      spectators = uniqueCoins(source.spectators ?? source.spectatorCards ?? source.spectator_cards, count);
    }
    if (!spectators.length) {
      const used = new Set([...petya, ...vasya]);
      spectators = cards.filter(card => !used.has(card));
    }
    const all = [...petya, ...vasya, ...spectators];
    const valid = petya.length === petyaCount
      && vasya.length === vasyaCount
      && spectators.length === spectatorCount
      && all.length === count
      && new Set(all).size === count
      && all.every(card => cards.includes(card));
    return {
      valid,
      petya: petya.slice().sort((a, b) => a - b),
      vasya: vasya.slice().sort((a, b) => a - b),
      vasyaCard: vasya[0] || null,
      spectators: spectators.slice().sort((a, b) => a - b),
      owners: Object.fromEntries(cards.map(card => [
        card,
        petya.includes(card) ? 'petya' : (vasya.includes(card) ? 'vasya' : (spectators.includes(card) ? 'spectators' : ''))
      ]))
    };
  }

  function petyaVasyaAllDistributions(params = {}) {
    const cards = petyaVasyaCards(params);
    const states = [];
    for (let first = 0; first < cards.length; first += 1) {
      for (let second = first + 1; second < cards.length; second += 1) {
        const petya = [cards[first], cards[second]];
        const remaining = cards.filter(card => !petya.includes(card));
        for (const vasyaCard of remaining) {
          const spectators = remaining.filter(card => card !== vasyaCard);
          states.push(petyaVasyaNormalizeDistribution({ petya, vasya: [vasyaCard], spectators }, params));
        }
      }
    }
    return states;
  }

  function petyaVasyaRandomDistribution(params = {}, random = Math.random) {
    const states = petyaVasyaAllDistributions(params);
    return states[Math.floor(random() * states.length)] || petyaVasyaNormalizeDistribution({ petya: [1, 2], vasya: [3], spectators: [4, 5] }, params);
  }

  function petyaVasyaStrategyMove(rawDistribution, params = {}) {
    const distribution = petyaVasyaNormalizeDistribution(rawDistribution, params);
    if (!distribution.valid) return { ok: false, error: 'Распределите 2 карточки Пете, 1 Васе и 2 зрителям.', distribution };
    const count = petyaVasyaCardCount(params);
    const [first, second] = distribution.petya;
    const forward = (second - first + count) % count;
    const backward = (first - second + count) % count;
    const namedCard = forward >= 1 && forward <= 2 ? second : first;
    const otherPetyaCard = namedCard === second ? first : second;
    const vasyaCard = distribution.vasyaCard;
    const nextCards = [petyaVasyaNextCard(namedCard, 1, params), petyaVasyaNextCard(namedCard, 2, params)];
    const answerOptions = nextCards.filter(card => card !== vasyaCard);
    const answerCard = answerOptions[0] || null;
    return {
      ok: Boolean(namedCard && answerCard),
      distribution,
      namedCard,
      otherPetyaCard,
      vasyaCard,
      nextCards,
      answerOptions,
      answerCard,
      shortArcLength: namedCard === second ? forward : backward
    };
  }

  function petyaVasyaEvaluate(params = {}) {
    const distribution = petyaVasyaNormalizeDistribution(params.distribution ?? params, params);
    const namedCard = Number(params.namedCard ?? params.named_card ?? params.petyaNamed ?? params.petya_named);
    const answerCard = Number(params.answerCard ?? params.answer_card ?? params.vasyaAnswer ?? params.vasya_answer);
    const move = petyaVasyaStrategyMove(distribution, params);
    const petyaNamedOwn = distribution.petya.includes(namedCard);
    const petyaFollowsStrategy = move.ok && namedCard === move.namedCard;
    const vasyaAnswerSpectator = distribution.spectators.includes(answerCard);
    const vasyaAnswerByRule = move.ok && move.answerOptions.includes(answerCard);
    return {
      valid: distribution.valid && Number.isInteger(namedCard) && Number.isInteger(answerCard),
      distribution,
      namedCard,
      answerCard,
      move,
      petyaNamedOwn,
      petyaFollowsStrategy,
      vasyaAnswerSpectator,
      vasyaAnswerByRule,
      win: distribution.valid && petyaNamedOwn && vasyaAnswerSpectator,
      strategyWin: distribution.valid && petyaFollowsStrategy && vasyaAnswerByRule && vasyaAnswerSpectator
    };
  }

  function petyaVasyaExhaustiveCheck(params = {}) {
    const rows = petyaVasyaAllDistributions(params).map(distribution => {
      const move = petyaVasyaStrategyMove(distribution, params);
      const evaluation = petyaVasyaEvaluate({
        ...params,
        distribution,
        namedCard: move.namedCard,
        answerCard: move.answerCard
      });
      return {
        distribution,
        move,
        ok: move.ok && evaluation.strategyWin,
        petya: distribution.petya,
        vasya: distribution.vasyaCard,
        spectators: distribution.spectators,
        namedCard: move.namedCard,
        answerCard: move.answerCard
      };
    });
    return {
      ok: rows.length > 0 && rows.every(row => row.ok),
      checked: rows.length,
      rows,
      failures: rows.filter(row => !row.ok)
    };
  }

  const FITCH_CHENEY_RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'];
  const FITCH_CHENEY_SUITS = [
    { id: 'C', label: '♣', name: 'трефы', color: 'black' },
    { id: 'D', label: '♦', name: 'бубны', color: 'red' },
    { id: 'H', label: '♥', name: 'червы', color: 'red' },
    { id: 'S', label: '♠', name: 'пики', color: 'black' }
  ];
  const FITCH_CHENEY_PERMUTATIONS = [
    [0, 1, 2],
    [0, 2, 1],
    [1, 0, 2],
    [1, 2, 0],
    [2, 0, 1],
    [2, 1, 0]
  ];

  function fitchCheneyRanks(params = {}) {
    const ranks = Array.isArray(params.ranks) && params.ranks.length ? params.ranks.map(String) : FITCH_CHENEY_RANKS;
    return ranks.slice(0, 13);
  }

  function fitchCheneySuits(params = {}) {
    const suits = Array.isArray(params.suits) && params.suits.length
      ? params.suits.map((raw, index) => ({
        id: String(raw?.id ?? raw?.key ?? index),
        label: String(raw?.label ?? raw?.symbol ?? raw?.id ?? index),
        name: String(raw?.name ?? raw?.title ?? raw?.label ?? raw?.id ?? index),
        color: String(raw?.color ?? '')
      }))
      : FITCH_CHENEY_SUITS;
    return suits.slice(0, 4);
  }

  function fitchCheneyDeck(params = {}) {
    const ranks = fitchCheneyRanks(params);
    const suits = fitchCheneySuits(params);
    const deck = [];
    for (let suitIndex = 0; suitIndex < suits.length; suitIndex += 1) {
      for (let rankIndex = 0; rankIndex < ranks.length; rankIndex += 1) {
        const suit = suits[suitIndex];
        const rank = ranks[rankIndex];
        deck.push({
          id: `${suit.id}${rankIndex}`,
          suit: suit.id,
          suitLabel: suit.label,
          suitName: suit.name,
          color: suit.color || (suit.id === 'D' || suit.id === 'H' ? 'red' : 'black'),
          rank,
          rankIndex,
          suitIndex,
          sortIndex: suitIndex * ranks.length + rankIndex,
          label: `${rank}${suit.label}`
        });
      }
    }
    return deck;
  }

  function fitchCheneyCardMap(params = {}) {
    return new Map(fitchCheneyDeck(params).map(card => [card.id, card]));
  }

  function fitchCheneyNormalizeCards(cards, params = {}) {
    let byId = null;
    const seen = new Set();
    const result = [];
    for (const raw of cards || []) {
      let card = null;
      if (raw && typeof raw === 'object' && raw.id && Number.isInteger(raw.rankIndex) && Number.isInteger(raw.suitIndex)) {
        card = raw;
      } else {
        if (!byId) byId = fitchCheneyCardMap(params);
        const id = String(raw?.id ?? raw ?? '');
        card = byId.get(id);
      }
      if (!card || seen.has(card.id)) continue;
      seen.add(card.id);
      result.push(card);
    }
    return result;
  }

  function fitchCheneyCardLabel(cardOrId, params = {}) {
    const card = typeof cardOrId === 'string'
      ? fitchCheneyCardMap(params).get(cardOrId)
      : fitchCheneyNormalizeCards([cardOrId], params)[0];
    return card?.label || '';
  }

  function fitchCheneyDistance(fromCard, toCard, rankCount = FITCH_CHENEY_RANKS.length) {
    return (toCard.rankIndex - fromCard.rankIndex + rankCount) % rankCount;
  }

  function fitchCheneySorted(cards) {
    return [...cards].sort((a, b) => a.sortIndex - b.sortIndex);
  }

  function fitchCheneyOrderForOffset(restCards, offset) {
    const base = fitchCheneySorted(restCards);
    const permutation = FITCH_CHENEY_PERMUTATIONS[offset - 1];
    if (!permutation || base.length !== 3) return [];
    return permutation.map(index => base[index]);
  }

  function fitchCheneyPermutationOffset(orderedRest) {
    if (!Array.isArray(orderedRest) || orderedRest.length !== 3) return null;
    const base = fitchCheneySorted(orderedRest);
    const positionById = new Map(base.map((card, index) => [card.id, index]));
    const key = orderedRest.map(card => positionById.get(card.id)).join(',');
    const index = FITCH_CHENEY_PERMUTATIONS.findIndex(permutation => permutation.join(',') === key);
    return index >= 0 ? index + 1 : null;
  }

  function fitchCheneyChooseAssistantMove(handCards, params = {}) {
    const hand = fitchCheneySorted(fitchCheneyNormalizeCards(handCards, params));
    const rankCount = fitchCheneyRanks(params).length;
    const maxOffset = Math.min(FITCH_CHENEY_PERMUTATIONS.length, Math.floor(rankCount / 2));
    if (hand.length !== 5) {
      return { ok: false, error: 'Нужны ровно 5 разных карт.', hand };
    }
    for (let first = 0; first < hand.length; first += 1) {
      for (let second = first + 1; second < hand.length; second += 1) {
        const a = hand[first];
        const b = hand[second];
        if (a.suit !== b.suit) continue;
        const forward = fitchCheneyDistance(a, b, rankCount);
        const backward = fitchCheneyDistance(b, a, rankCount);
        let keyCard = null;
        let hiddenCard = null;
        let offset = null;
        if (forward >= 1 && forward <= maxOffset) {
          keyCard = a;
          hiddenCard = b;
          offset = forward;
        } else if (backward >= 1 && backward <= maxOffset) {
          keyCard = b;
          hiddenCard = a;
          offset = backward;
        }
        if (!keyCard || !hiddenCard) continue;
        const rest = hand.filter(card => card.id !== keyCard.id && card.id !== hiddenCard.id);
        const shownCards = [keyCard, ...fitchCheneyOrderForOffset(rest, offset)];
        return {
          ok: true,
          hand,
          hiddenCard,
          shownCards,
          keyCard,
          offset
        };
      }
    }
    return { ok: false, error: 'В руке не найдена подходящая пара одной масти.', hand };
  }

  function fitchCheneyDecodeShown(shownCards, params = {}) {
    const shown = fitchCheneyNormalizeCards(shownCards, params);
    const ranks = fitchCheneyRanks(params);
    const rankCount = ranks.length;
    if (shown.length !== 4) return { ok: false, error: 'Нужны ровно 4 разные показанные карты.', shownCards: shown };
    const keyCard = shown[0];
    const orderedRest = shown.slice(1);
    const offset = fitchCheneyPermutationOffset(orderedRest);
    if (offset == null) return { ok: false, error: 'Порядок трех карт не распознан.', shownCards: shown };
    const hiddenRankIndex = (keyCard.rankIndex + offset) % rankCount;
    const hiddenCard = {
      ...keyCard,
      id: `${keyCard.suit}${hiddenRankIndex}`,
      rank: ranks[hiddenRankIndex],
      rankIndex: hiddenRankIndex,
      sortIndex: keyCard.suitIndex * rankCount + hiddenRankIndex,
      label: `${ranks[hiddenRankIndex]}${keyCard.suitLabel}`
    };
    const shownIds = new Set(shown.map(card => card.id));
    return {
      ok: Boolean(hiddenCard) && !shownIds.has(hiddenCard.id),
      error: shownIds.has(hiddenCard?.id) ? 'Декодированная карта уже лежит среди показанных.' : '',
      shownCards: shown,
      keyCard,
      offset,
      hiddenCard
    };
  }

  function fitchCheneyEvaluate(params = {}) {
    const hand = fitchCheneyNormalizeCards(params.hand ?? params.handCards ?? params.cards, params);
    const shownCards = fitchCheneyNormalizeCards(params.shownCards ?? params.shown ?? [], params);
    const hiddenCard = fitchCheneyNormalizeCards([params.hiddenCard ?? params.hidden ?? ''], params)[0] || null;
    const decoded = fitchCheneyDecodeShown(shownCards, params);
    const handIds = new Set(hand.map(card => card.id));
    const shownIds = new Set(shownCards.map(card => card.id));
    const validHand = hand.length === 5 && shownCards.length === 4 && hiddenCard && handIds.has(hiddenCard.id)
      && shownCards.every(card => handIds.has(card.id))
      && !shownIds.has(hiddenCard.id);
    return {
      ok: validHand && decoded.ok,
      win: validHand && decoded.ok && decoded.hiddenCard?.id === hiddenCard.id,
      hand,
      hiddenCard,
      shownCards,
      decodedCard: decoded.hiddenCard || null,
      decoded,
      error: validHand ? (decoded.error || '') : 'Проверьте: нужна рука из 5 карт, одна скрытая карта и 4 показанные из этой руки.'
    };
  }

  function fitchCheneyRandomHand(params = {}) {
    const deck = fitchCheneyDeck(params);
    const shuffled = [...deck];
    for (let index = shuffled.length - 1; index > 0; index -= 1) {
      const swapIndex = Math.floor(Math.random() * (index + 1));
      [shuffled[index], shuffled[swapIndex]] = [shuffled[swapIndex], shuffled[index]];
    }
    return fitchCheneySorted(shuffled.slice(0, 5));
  }

  function fitchCheneyExhaustiveCheck(params = {}) {
    const deck = fitchCheneyDeck(params);
    const failures = [];
    let checked = 0;
    for (let a = 0; a < deck.length - 4; a += 1) {
      for (let b = a + 1; b < deck.length - 3; b += 1) {
        for (let c = b + 1; c < deck.length - 2; c += 1) {
          for (let d = c + 1; d < deck.length - 1; d += 1) {
            for (let e = d + 1; e < deck.length; e += 1) {
              const hand = [deck[a], deck[b], deck[c], deck[d], deck[e]];
              const move = fitchCheneyChooseAssistantMove(hand, params);
              const decoded = move.ok ? fitchCheneyDecodeShown(move.shownCards, params) : null;
              checked += 1;
              if (!move.ok || !decoded?.ok || decoded.hiddenCard?.id !== move.hiddenCard.id) {
                failures.push({
                  hand: hand.map(card => card.id),
                  hidden: move.hiddenCard?.id || '',
                  shown: (move.shownCards || []).map(card => card.id),
                  decoded: decoded?.hiddenCard?.id || '',
                  error: move.error || decoded?.error || 'decode mismatch'
                });
                if (failures.length >= 10) {
                  return { ok: false, checked, total: checked, failures, stoppedEarly: true };
                }
              }
            }
          }
        }
      }
    }
    return { ok: failures.length === 0, checked, total: checked, failures, stoppedEarly: false };
  }

  function twentyOneCardDeckSize(params = {}) {
    const size = Number(params.deck_size ?? params.deckSize ?? params.card_count ?? params.cardCount ?? 21);
    return Number.isInteger(size) && size > 0 ? size : 21;
  }

  function twentyOneCardColumnCount(params = {}) {
    const count = Number(params.column_count ?? params.columnCount ?? 3);
    return Number.isInteger(count) && count > 0 ? count : 3;
  }

  function twentyOneCardRowCount(params = {}) {
    const rows = Number(params.row_count ?? params.rowCount ?? 7);
    return Number.isInteger(rows) && rows > 0 ? rows : 7;
  }

  function twentyOneCardRoundCount(params = {}) {
    const rounds = Number(params.round_count ?? params.roundCount ?? 3);
    return Number.isInteger(rounds) && rounds > 0 ? rounds : 3;
  }

  function twentyOneCardCards(params = {}) {
    const size = twentyOneCardDeckSize(params);
    const labels = Array.isArray(params.card_labels ?? params.cardLabels) ? (params.card_labels ?? params.cardLabels) : [];
    return Array.from({ length: size }, (_item, index) => ({
      id: index + 1,
      label: String(labels[index] ?? index + 1)
    }));
  }

  function twentyOneCardInitialDeck(params = {}) {
    const size = twentyOneCardDeckSize(params);
    const rawDeck = Array.isArray(params.deck) ? params.deck : null;
    const deck = rawDeck
      ? rawDeck.map(Number).filter(card => Number.isInteger(card) && card >= 1 && card <= size)
      : [];
    if (deck.length === size && new Set(deck).size === size) return deck;
    return Array.from({ length: size }, (_item, index) => index + 1);
  }

  function twentyOneCardDeal(deck, params = {}) {
    const columnCount = twentyOneCardColumnCount(params);
    const columns = Array.from({ length: columnCount }, () => []);
    for (let index = 0; index < (deck || []).length; index += 1) {
      columns[index % columnCount].push(deck[index]);
    }
    return columns;
  }

  function twentyOneCardNormalizeColumn(column, params = {}) {
    const count = twentyOneCardColumnCount(params);
    const raw = Number(column);
    if (!Number.isInteger(raw)) return null;
    if (raw >= 0 && raw < count) return raw;
    if (raw >= 1 && raw <= count) return raw - 1;
    return null;
  }

  function twentyOneCardFindColumn(layout, card) {
    const target = Number(card);
    for (let column = 0; column < (layout || []).length; column += 1) {
      if ((layout[column] || []).includes(target)) return column;
    }
    return null;
  }

  function twentyOneCardCollectionOrder(selectedColumn, params = {}) {
    const columnCount = twentyOneCardColumnCount(params);
    const middle = Math.floor(columnCount / 2);
    const selected = twentyOneCardNormalizeColumn(selectedColumn, params);
    if (selected == null || columnCount < 1) return [];
    const others = Array.from({ length: columnCount }, (_item, index) => index).filter(index => index !== selected);
    const order = [];
    for (let index = 0; index < middle; index += 1) order.push(others[index]);
    order.push(selected);
    for (let index = middle; index < others.length; index += 1) order.push(others[index]);
    return order;
  }

  function twentyOneCardCollect(layout, selectedColumn, params = {}) {
    const order = twentyOneCardCollectionOrder(selectedColumn, params);
    return order.flatMap(column => [...(layout?.[column] || [])]);
  }

  function twentyOneCardStep(params = {}) {
    const deck = Array.isArray(params.deck) ? params.deck.map(Number) : twentyOneCardInitialDeck(params);
    const selectedCard = Number(params.selectedCard ?? params.selected_card ?? params.hiddenCard ?? params.hidden_card);
    const layout = twentyOneCardDeal(deck, params);
    const actualColumn = twentyOneCardFindColumn(layout, selectedCard);
    const reportedColumn = twentyOneCardNormalizeColumn(
      params.reportedColumn ?? params.reported_column ?? params.column ?? actualColumn,
      params
    );
    const collectionOrder = twentyOneCardCollectionOrder(reportedColumn, params);
    const collectedDeck = twentyOneCardCollect(layout, reportedColumn, params);
    return {
      deck,
      layout,
      selectedCard,
      actualColumn,
      reportedColumn,
      truthful: actualColumn != null && actualColumn === reportedColumn,
      collectionOrder,
      collectedDeck,
      positionBefore: selectedCard ? deck.indexOf(selectedCard) + 1 : null,
      positionAfter: selectedCard ? collectedDeck.indexOf(selectedCard) + 1 : null
    };
  }

  function twentyOneCardTrace(params = {}) {
    const roundCount = twentyOneCardRoundCount(params);
    const deckSize = twentyOneCardDeckSize(params);
    const selectedCard = Number(params.selectedCard ?? params.selected_card ?? params.hiddenCard ?? params.hidden_card ?? 1);
    const answers = Array.isArray(params.answers ?? params.reported_columns ?? params.columns)
      ? (params.answers ?? params.reported_columns ?? params.columns)
      : [];
    let deck = twentyOneCardInitialDeck(params);
    const rounds = [];
    for (let index = 0; index < roundCount; index += 1) {
      const step = twentyOneCardStep({
        ...params,
        deck,
        selectedCard,
        reportedColumn: answers[index]
      });
      rounds.push({
        round: index + 1,
        deck: step.deck,
        layout: step.layout,
        actualColumn: step.actualColumn,
        reportedColumn: step.reportedColumn,
        truthful: step.truthful,
        collectionOrder: step.collectionOrder,
        collectedDeck: step.collectedDeck,
        positionBefore: step.positionBefore,
        positionAfter: step.positionAfter
      });
      deck = step.collectedDeck;
    }
    const finalPosition = Math.ceil(deckSize / 2);
    const finalCard = deck[finalPosition - 1] ?? null;
    return {
      deckSize,
      columnCount: twentyOneCardColumnCount(params),
      rowCount: twentyOneCardRowCount(params),
      roundCount,
      selectedCard,
      initialDeck: twentyOneCardInitialDeck(params),
      rounds,
      finalDeck: deck,
      finalPosition,
      finalCard,
      success: finalCard === selectedCard && rounds.every(round => round.truthful)
    };
  }

  function twentyOneCardExhaustive(params = {}) {
    const cards = twentyOneCardInitialDeck(params);
    const rows = cards.map(card => {
      const trace = twentyOneCardTrace({ ...params, selectedCard: card });
      return {
        card,
        answers: trace.rounds.map(round => round.actualColumn),
        finalCard: trace.finalCard,
        finalPosition: trace.finalPosition,
        success: trace.finalCard === card,
        trace
      };
    });
    return {
      checked: rows.length,
      success: rows.every(row => row.success),
      rows,
      failures: rows.filter(row => !row.success)
    };
  }

  function twentyOneCardRandomState(params = {}, random = Math.random) {
    const deck = twentyOneCardInitialDeck(params);
    const index = Math.floor(Math.max(0, Math.min(0.999999, Number(random()) || 0)) * deck.length);
    return {
      selectedCard: deck[index],
      deck
    };
  }

  function higherLowerGcd(a, b) {
    let x = a < 0n ? -a : a;
    let y = b < 0n ? -b : b;
    while (y !== 0n) {
      const next = x % y;
      x = y;
      y = next;
    }
    return x || 1n;
  }

  function higherLowerFraction(num, den = 1n) {
    let n = BigInt(num);
    let d = BigInt(den);
    if (d === 0n) throw new Error('Zero denominator');
    if (d < 0n) {
      n = -n;
      d = -d;
    }
    const divisor = higherLowerGcd(n, d);
    return { num: n / divisor, den: d / divisor };
  }

  function higherLowerAdd(first, second) {
    return higherLowerFraction(first.num * second.den + second.num * first.den, first.den * second.den);
  }

  function higherLowerMulInt(value, factor) {
    return higherLowerFraction(value.num * BigInt(factor), value.den);
  }

  function higherLowerDivInt(value, divisor) {
    return higherLowerFraction(value.num, value.den * BigInt(divisor));
  }

  function higherLowerCompare(first, second) {
    const left = first.num * second.den;
    const right = second.num * first.den;
    if (left < right) return -1;
    if (left > right) return 1;
    return 0;
  }

  function higherLowerFractionLabel(value) {
    const normalized = higherLowerFraction(value.num, value.den);
    if (normalized.den === 1n) return String(normalized.num);
    return `${normalized.num}/${normalized.den}`;
  }

  function higherLowerFractionNumber(value) {
    return Number(value.num) / Number(value.den);
  }

  function higherLowerPublicFraction(value) {
    return {
      numerator: String(value.num),
      denominator: String(value.den),
      label: higherLowerFractionLabel(value),
      value: higherLowerFractionNumber(value),
      percent: 100 * higherLowerFractionNumber(value)
    };
  }

  function higherLowerBoxCount(params = {}) {
    const count = Number(params.box_count ?? params.boxCount ?? params.number_count ?? params.numberCount ?? 9);
    if (!Number.isInteger(count) || count < 1) return 0;
    return count;
  }

  function higherLowerComparisonCounts(params = {}) {
    const main = higherLowerBoxCount(params);
    const raw = params.compare_box_counts ?? params.compareBoxCounts ?? params.sample_box_counts ?? params.sampleBoxCounts ?? [3, 4, main];
    const seen = new Set();
    const result = [];
    for (const value of Array.isArray(raw) ? raw : [raw]) {
      const count = Number(value);
      if (!Number.isInteger(count) || count < 1 || seen.has(count)) continue;
      seen.add(count);
      result.push(count);
    }
    if (main && !seen.has(main)) result.push(main);
    return result.length ? result : [main || 1];
  }

  function higherLowerMoveScore(table, boxCount, guess, turn) {
    const count = Number(boxCount);
    const pivot = Number(guess);
    if (!Number.isInteger(count) || count < 1 || !Number.isInteger(pivot) || pivot < 1 || pivot > count) return null;
    const lowerSize = pivot - 1;
    const higherSize = count - pivot;
    if (turn === 'second') {
      const lower = higherLowerMulInt(table.first[lowerSize].value, lowerSize);
      const higher = higherLowerMulInt(table.first[higherSize].value, higherSize);
      return higherLowerDivInt(higherLowerAdd(lower, higher), count);
    }
    const hit = higherLowerFraction(1n, BigInt(count));
    const lower = higherLowerMulInt(table.second[lowerSize].value, lowerSize);
    const higher = higherLowerMulInt(table.second[higherSize].value, higherSize);
    return higherLowerAdd(hit, higherLowerDivInt(higherLowerAdd(lower, higher), count));
  }

  function higherLowerBuildTable(maxBoxes) {
    const max = Number(maxBoxes);
    if (!Number.isInteger(max) || max < 1) return { first: [], second: [] };
    const first = [{ boxCount: 0, value: higherLowerFraction(0), moves: [] }];
    const second = [{ boxCount: 0, value: higherLowerFraction(0), moves: [] }];
    const table = { first, second };
    for (let count = 1; count <= max; count += 1) {
      const firstMoves = [];
      for (let guess = 1; guess <= count; guess += 1) {
        firstMoves.push({
          guess,
          lowerSize: guess - 1,
          higherSize: count - guess,
          value: higherLowerMoveScore(table, count, guess, 'first')
        });
      }
      let bestFirst = firstMoves[0].value;
      for (const move of firstMoves) {
        if (higherLowerCompare(move.value, bestFirst) > 0) bestFirst = move.value;
      }
      first.push({
        boxCount: count,
        value: bestFirst,
        moves: firstMoves.map(move => ({ ...move, optimal: higherLowerCompare(move.value, bestFirst) === 0 }))
      });

      const secondMoves = [];
      for (let guess = 1; guess <= count; guess += 1) {
        secondMoves.push({
          guess,
          lowerSize: guess - 1,
          higherSize: count - guess,
          value: higherLowerMoveScore(table, count, guess, 'second')
        });
      }
      let bestSecond = secondMoves[0].value;
      for (const move of secondMoves) {
        if (higherLowerCompare(move.value, bestSecond) < 0) bestSecond = move.value;
      }
      second.push({
        boxCount: count,
        value: bestSecond,
        moves: secondMoves.map(move => ({ ...move, optimal: higherLowerCompare(move.value, bestSecond) === 0 }))
      });
    }
    return table;
  }

  function higherLowerPublicPosition(position) {
    return {
      boxCount: position.boxCount,
      value: higherLowerPublicFraction(position.value),
      moves: position.moves.map(move => ({
        guess: move.guess,
        lowerSize: move.lowerSize,
        higherSize: move.higherSize,
        optimal: Boolean(move.optimal),
        value: higherLowerPublicFraction(move.value)
      }))
    };
  }

  function higherLowerSolve(params = {}) {
    const boxCount = higherLowerBoxCount(params);
    const counts = higherLowerComparisonCounts(params);
    const max = Math.max(boxCount, ...counts);
    const table = higherLowerBuildTable(max);
    return {
      boxCount,
      counts,
      first: higherLowerPublicPosition(table.first[boxCount]),
      second: higherLowerPublicPosition(table.second[boxCount]),
      comparisons: counts.map(count => ({
        boxCount: count,
        first: higherLowerPublicPosition(table.first[count]),
        second: higherLowerPublicPosition(table.second[count])
      }))
    };
  }

  function higherLowerActionScores(params = {}) {
    const boxCount = higherLowerBoxCount(params);
    const turn = params.turn === 'second' ? 'second' : 'first';
    const table = higherLowerBuildTable(boxCount);
    return higherLowerPublicPosition(table[turn][boxCount]).moves;
  }

  function higherLowerBestGuesses(params = {}) {
    return higherLowerActionScores(params).filter(move => move.optimal).map(move => move.guess);
  }

  function higherLowerInitialState(params = {}) {
    const boxCount = higherLowerBoxCount(params);
    return { low: 1, high: boxCount, turn: 'first', finished: false, winner: null };
  }

  function higherLowerStateSize(state) {
    const low = Number(state?.low);
    const high = Number(state?.high);
    if (!Number.isInteger(low) || !Number.isInteger(high) || high < low) return 0;
    return high - low + 1;
  }

  function higherLowerStateValue(state, params = {}) {
    const size = higherLowerStateSize(state);
    const table = higherLowerBuildTable(Math.max(size, higherLowerBoxCount(params)));
    const turn = state?.turn === 'second' ? 'second' : 'first';
    return higherLowerPublicFraction(table[turn][size]?.value || higherLowerFraction(0));
  }

  function higherLowerGuessBranches(state, guess, params = {}) {
    const low = Number(state?.low);
    const high = Number(state?.high);
    const turn = state?.turn === 'second' ? 'second' : 'first';
    const selected = Number(guess);
    if (!Number.isInteger(low) || !Number.isInteger(high) || !Number.isInteger(selected) || selected < low || selected > high) return [];
    const nextTurn = turn === 'first' ? 'second' : 'first';
    const table = higherLowerBuildTable(Math.max(higherLowerBoxCount(params), high - low + 1));
    const total = high - low + 1;
    const branches = [{
      answer: 'hit',
      label: 'угадано',
      size: 1,
      probability: higherLowerPublicFraction(higherLowerFraction(1n, BigInt(total))),
      nextState: { low: selected, high: selected, turn, finished: true, winner: turn },
      firstWinChance: turn === 'first' ? higherLowerPublicFraction(higherLowerFraction(1)) : higherLowerPublicFraction(higherLowerFraction(0))
    }];
    if (selected > low) {
      const size = selected - low;
      const nextState = { low, high: selected - 1, turn: nextTurn, finished: false, winner: null };
      branches.push({
        answer: 'lower',
        label: 'ниже',
        size,
        probability: higherLowerPublicFraction(higherLowerFraction(BigInt(size), BigInt(total))),
        nextState,
        firstWinChance: higherLowerPublicFraction(table[nextTurn][size].value)
      });
    }
    if (selected < high) {
      const size = high - selected;
      const nextState = { low: selected + 1, high, turn: nextTurn, finished: false, winner: null };
      branches.push({
        answer: 'higher',
        label: 'выше',
        size,
        probability: higherLowerPublicFraction(higherLowerFraction(BigInt(size), BigInt(total))),
        nextState,
        firstWinChance: higherLowerPublicFraction(table[nextTurn][size].value)
      });
    }
    return branches;
  }

  function higherLowerApplyAnswer(state, guess, answer, params = {}) {
    const branches = higherLowerGuessBranches(state, guess, params);
    return branches.find(branch => branch.answer === answer)?.nextState || null;
  }

  function movingTargetDefaultCube() {
    return {
      vertices: [
        { id: 'A', label: 'A', color: 'light', x: 24, y: 72 },
        { id: 'B', label: 'B', color: 'dark', x: 24, y: 28 },
        { id: 'C', label: 'C', color: 'light', x: 58, y: 20 },
        { id: 'D', label: 'D', color: 'dark', x: 58, y: 64 },
        { id: 'E', label: 'E', color: 'dark', x: 42, y: 86 },
        { id: 'F', label: 'F', color: 'light', x: 42, y: 42 },
        { id: 'G', label: 'G', color: 'dark', x: 76, y: 34 },
        { id: 'H', label: 'H', color: 'light', x: 76, y: 78 }
      ],
      edges: [
        ['A', 'B'], ['B', 'C'], ['C', 'D'], ['D', 'A'],
        ['E', 'F'], ['F', 'G'], ['G', 'H'], ['H', 'E'],
        ['A', 'E'], ['B', 'F'], ['C', 'G'], ['D', 'H']
      ]
    };
  }

  function movingTargetNormalizeGraph(params = {}) {
    const fallback = movingTargetDefaultCube();
    const rawVertices = Array.isArray(params.vertices) && params.vertices.length ? params.vertices : fallback.vertices;
    const vertices = [];
    const seen = new Set();
    for (const raw of rawVertices) {
      const id = String(raw?.id ?? raw?.key ?? raw ?? '').trim();
      if (!id || seen.has(id)) continue;
      seen.add(id);
      vertices.push({
        id,
        label: String(raw?.label ?? id),
        color: String(raw?.color ?? ''),
        x: Number.isFinite(Number(raw?.x)) ? Number(raw.x) : null,
        y: Number.isFinite(Number(raw?.y)) ? Number(raw.y) : null
      });
    }
    const vertexIds = new Set(vertices.map(vertex => vertex.id));
    const rawEdges = Array.isArray(params.edges) && params.edges.length ? params.edges : fallback.edges;
    const edgeSeen = new Set();
    const edges = [];
    for (const raw of rawEdges) {
      const first = String(raw?.[0] ?? raw?.from ?? raw?.a ?? '').trim();
      const second = String(raw?.[1] ?? raw?.to ?? raw?.b ?? '').trim();
      if (!first || !second || first === second || !vertexIds.has(first) || !vertexIds.has(second)) continue;
      const key = [first, second].sort().join('|');
      if (edgeSeen.has(key)) continue;
      edgeSeen.add(key);
      edges.push([first, second]);
    }
    const neighbors = Object.fromEntries(vertices.map(vertex => [vertex.id, []]));
    for (const [first, second] of edges) {
      neighbors[first].push(second);
      neighbors[second].push(first);
    }
    for (const list of Object.values(neighbors)) list.sort();
    return { vertices, edges, neighbors };
  }

  function movingTargetVertexKey(vertex) {
    return String(vertex?.id ?? vertex?.key ?? vertex ?? '').trim();
  }

  function movingTargetNormalizeVertices(vertices, params = {}) {
    const graph = movingTargetNormalizeGraph(params);
    const allowed = new Set(graph.vertices.map(vertex => vertex.id));
    const seen = new Set();
    const result = [];
    for (const raw of vertices || []) {
      const key = movingTargetVertexKey(raw);
      if (!allowed.has(key) || seen.has(key)) continue;
      seen.add(key);
      result.push(key);
    }
    return result;
  }

  function movingTargetInitialStates(params = {}) {
    return movingTargetNormalizeGraph(params).vertices.map(vertex => vertex.id);
  }

  function movingTargetCurrentStates(params = {}) {
    const current = params.currentStates ?? params.current_states ?? params.currentCandidates ?? params.current_candidates;
    return current?.length
      ? movingTargetNormalizeVertices(current, params)
      : movingTargetInitialStates(params);
  }

  function movingTargetValidation(checkedVertices, params = {}) {
    const checkSize = Number(params.checkSize ?? params.check_size ?? params.action_size ?? 1);
    const checked = movingTargetNormalizeVertices(checkedVertices, params);
    const validSize = Number.isInteger(checkSize) && checkSize >= 1;
    if (!validSize) return { valid: false, error: 'Invalid check size.', checked };
    const allowFewer = params.allowFewer === true || params.allow_fewer === true || params.allowUpTo === true || params.allow_up_to === true;
    if (allowFewer ? checked.length < 1 || checked.length > checkSize : checked.length !== checkSize) {
      return {
        valid: false,
        error: allowFewer
          ? `Select from 1 to ${checkSize} vertices.`
          : `Select exactly ${checkSize} vertices.`,
        checked
      };
    }
    return { valid: true, error: '', checked };
  }

  function movingTargetTransitionStates(params = {}) {
    const graph = movingTargetNormalizeGraph(params);
    const current = movingTargetCurrentStates(params);
    const checked = new Set(movingTargetNormalizeVertices(params.checkedVertices ?? params.checked_vertices ?? params.checked ?? params.verticesToCheck, params));
    const escapedBeforeMove = current.filter(vertex => !checked.has(vertex));
    const next = new Set();
    for (const vertex of escapedBeforeMove) {
      for (const neighbor of graph.neighbors[vertex] || []) next.add(neighbor);
    }
    return [...next].sort();
  }

  function movingTargetCaughtStates(params = {}) {
    const current = movingTargetCurrentStates(params);
    const checked = new Set(movingTargetNormalizeVertices(params.checkedVertices ?? params.checked_vertices ?? params.checked ?? params.verticesToCheck, params));
    return current.filter(vertex => checked.has(vertex)).sort();
  }

  function movingTargetBranchStatus(states, usedTests, maxTests) {
    const remaining = states || [];
    const used = Number(usedTests);
    const limit = Number(maxTests);
    if (!remaining.length) return 'solved';
    if (Number.isInteger(used) && Number.isInteger(limit) && used >= limit) return 'failed';
    return 'open';
  }

  function movingTargetChooseCheaterOutcome(params = {}) {
    const maxTests = Number(params.maxTests ?? params.max_tests ?? params.maxMoves ?? params.max_moves ?? 1);
    const usedTests = Number(params.usedTests ?? params.used_tests ?? params.usedMoves ?? params.used_moves ?? 0);
    const current = movingTargetCurrentStates(params);
    const caughtStates = movingTargetCaughtStates(params);
    const states = movingTargetTransitionStates(params);
    const caught = states.length === 0;
    return {
      outcome: caught ? 'caught' : 'not_found',
      caught,
      found: caught,
      caughtStates,
      states,
      candidates: states,
      usedTests: usedTests + 1,
      status: caught ? 'solved' : movingTargetBranchStatus(states, usedTests + 1, maxTests),
      scores: {
        caughtStates: caughtStates.length,
        escapedStates: current.length - caughtStates.length,
        nextStates: states.length
      }
    };
  }

  function movingTargetExpandExhaustiveNode(params = {}) {
    const maxTests = Number(params.maxTests ?? params.max_tests ?? params.maxMoves ?? params.max_moves ?? 1);
    const usedTests = Number(params.usedTests ?? params.used_tests ?? params.usedMoves ?? params.used_moves ?? 0);
    const caughtStates = movingTargetCaughtStates(params);
    const escapedStates = movingTargetTransitionStates(params);
    const children = [];
    if (caughtStates.length) {
      children.push({
        outcome: 'caught',
        label: 'поймано',
        states: [],
        candidates: [],
        caughtStates,
        usedTests: usedTests + 1,
        status: 'solved'
      });
    }
    if (escapedStates.length) {
      children.push({
        outcome: 'not_found',
        label: 'не найдено',
        states: escapedStates,
        candidates: escapedStates,
        caughtStates: [],
        usedTests: usedTests + 1,
        status: movingTargetBranchStatus(escapedStates, usedTests + 1, maxTests)
      });
    }
    return { caughtStates, escapedStates, children };
  }

  return {
    OUTCOMES,
    OUTCOME_LABELS,
    THRESHOLD_BALANCE_OUTCOMES,
    THRESHOLD_BALANCE_LABELS,
    YES_NO_OUTCOMES,
    YES_NO_LABELS,
    coinStatusDefinitions,
    statusDefinition,
    coinStatusOptions,
    knownDirectionCoinStatuses,
    unknownDirectionCoinStatuses,
    lightCoinSetStatuses,
    pairedLightCoinStatuses,
    initialCandidates,
    initialUnknownDirectionCandidates,
    uniqueCoins,
    normalizeDirection,
    normalizeKnownDirectionCandidates,
    normalizeUnknownDirectionCandidates,
    isUnknownDirectionCoinOnlyObjective,
    unknownDirectionCandidateKey,
    unknownDirectionCandidateLabel,
    flippedUnknownDirectionCandidate,
    unknownDirectionCandidateSetKey,
    flippedUnknownDirectionCandidateSetKey,
    mirroredPanCoinPermutation,
    knownDirectionCandidateSetKey,
    permutedKnownDirectionCandidateSetKey,
    markUnknownDirectionSymmetricChildren,
    markSymmetricOutcomeChildren,
    outcomeForCandidate,
    outcomeForUnknownDirectionCandidate,
    filterCandidates,
    filterUnknownDirectionCandidates,
    partitionCandidates,
    partitionUnknownDirectionCandidates,
    sequentialCoinPairs,
    normalizeCoinPairs,
    initialPairedLightCandidates,
    normalizePairedLightCandidates,
    pairedLightStateKey,
    pairedLightCandidateSetKey,
    permutedPairedLightCandidateSetKey,
    coinPermutationPreservesPairs,
    outcomeForPairedLightCandidate,
    pairedLightFilterCandidates,
    pairedLightPartitionCandidates,
    pairedLightBranchStatus,
    pairedLightChooseCheaterOutcome,
    pairedLightExpandExhaustiveNode,
    pairedLightFinalizeAnswer,
    zeroOneTwoSignClassLabel,
    zeroOneTwoSignInitialStates,
    zeroOneTwoSignStateKey,
    zeroOneTwoSignNormalizeStates,
    zeroOneTwoSignAnswerClasses,
    zeroOneTwoSignCoinStatuses,
    zeroOneTwoSignOutcomeForState,
    zeroOneTwoSignPartitionStates,
    zeroOneTwoSignFilterStates,
    zeroOneTwoSignBranchStatus,
    zeroOneTwoSignChooseCheaterOutcome,
    zeroOneTwoSignExpandExhaustiveNode,
    zeroOneTwoSignFinalizeAnswer,
    initialMultipleLightCandidates,
    normalizeGroupConstraints,
    initialGroupedMultipleLightCandidates,
    normalizeMultipleLightCandidates,
    multipleLightStateKey,
    multipleLightCandidateSetKey,
    permutedMultipleLightCandidateSetKey,
    coinPermutationPreservesGroupConstraints,
    outcomeForMultipleLightCandidate,
    multipleLightFilterCandidates,
    multipleLightPartitionCandidates,
    commonLightCoins,
    possibleLightCoins,
    uniqueLightState,
    multipleLightBranchStatus,
    multipleLightChooseCheaterOutcome,
    multipleLightExpandExhaustiveNode,
    multipleLightFinalizeAnswer,
    thresholdBalanceInitialStates,
    thresholdBalanceStateKey,
    thresholdBalanceStateLabel,
    normalizeThresholdBalanceOutcome,
    outcomeForThresholdBalanceState,
    thresholdBalanceFilterStates,
    thresholdBalancePartitionStates,
    thresholdBalanceUniqueState,
    thresholdBalanceObjectiveSolved,
    thresholdBalanceAnswerOptionsForStates,
    thresholdBalanceBranchStatus,
    thresholdBalanceChooseCheaterOutcome,
    thresholdBalanceExpandExhaustiveNode,
    thresholdBalanceFinalizeAnswer,
    constrainedLightInitialStates,
    constrainedLightNormalizeStates,
    constrainedLightStateKey,
    constrainedLightCoinSetKey,
    constrainedLightStateLabel,
    outcomeForConstrainedLightState,
    constrainedLightFilterStates,
    constrainedLightPartitionStates,
    constrainedLightPossibleCounts,
    constrainedLightUniqueCoinSet,
    constrainedLightUniqueState,
    constrainedLightObjectiveSolved,
    constrainedLightAnswerOptionsForStates,
    constrainedLightBranchStatus,
    constrainedLightChooseCheaterOutcome,
    constrainedLightExpandExhaustiveNode,
    constrainedLightFinalizeAnswer,
    zoltarMaskFromCoins,
    zoltarCoinsFromMask,
    zoltarInitialStates,
    zoltarNormalizeState,
    zoltarNormalizeStates,
    zoltarStateKey,
    zoltarBranchKey,
    zoltarParseBranchKey,
    zoltarOutcomeLabel,
    zoltarCompareState,
    zoltarNextBranchesForState,
    zoltarPartitionStates,
    zoltarFilterStates,
    zoltarGuaranteedRealCoins,
    zoltarPossibleRemainingRealCoins,
    zoltarRemovedCoinsInAllStates,
    zoltarCoinStatuses,
    zoltarBranchStatus,
    zoltarChooseCheaterBranch,
    zoltarExpandExhaustiveNode,
    zoltarFinalizeAnswer,
    exhaustiveBranchStatus,
    exhaustiveUnknownDirectionBranchStatus,
    expandExhaustiveNode,
    expandUnknownDirectionExhaustiveNode,
    chooseCheaterOutcome,
    chooseCheaterUnknownDirectionOutcome,
    normalizeUnknownDirectionWeighingPlan,
    unknownDirectionSignatureForCandidate,
    unknownDirectionSignatureKey,
    oppositeUnknownDirectionSignature,
    canonicalCoinOnlyUnknownDirectionSignatureKey,
    knownDirectionSignatureForCandidate,
    checkKnownDirectionNonadaptiveStrategy,
    checkUnknownDirectionNonadaptiveStrategy,
    finalizeCheaterAnswer,
    finalizeCheaterUnknownDirectionAnswer,
    initialScaleCandidates,
    faultyScaleOutcomeForCandidate,
    faultyScaleFilterCandidates,
    faultyScalePartitionCandidates,
    faultyScaleBranchStatus,
    faultyScaleChooseCheaterOutcome,
    faultyScaleExpandExhaustiveNode,
    faultyScaleFinalizeAnswer,
    initialBrokenScaleCoinCandidates,
    normalizeBrokenScaleCoinCandidates,
    brokenScaleCoinCandidateKey,
    outcomeForKnownCounterfeitWithCounts,
    brokenScaleCoinOutcomeForCandidate,
    brokenScaleCoinFilterCandidates,
    brokenScaleCoinPartitionCandidates,
    brokenScaleCoinBranchStatus,
    brokenScaleCoinChooseCheaterOutcome,
    brokenScaleCoinExpandExhaustiveNode,
    brokenScaleCoinFinalizeAnswer,
    initialBrokenDetectorCoinCandidates,
    normalizeBrokenDetectorCoinCandidates,
    brokenDetectorCoinCandidateKey,
    normalizeDetectorAnswer,
    brokenDetectorCoinOutcomeForCandidate,
    brokenDetectorCoinTestValidation,
    brokenDetectorCoinFilterCandidates,
    brokenDetectorCoinPartitionCandidates,
    brokenDetectorCoinBranchStatus,
    brokenDetectorCoinChooseCheaterOutcome,
    brokenDetectorCoinExpandExhaustiveNode,
    brokenDetectorCoinFinalizeAnswer,
    initialHeaviestBrokenScaleStates,
    normalizeHeaviestBrokenScaleStates,
    heaviestBrokenScaleOutcomeForState,
    heaviestBrokenScaleFilterStates,
    heaviestBrokenScalePartitionStates,
    heaviestBrokenScaleChooseCheaterOutcome,
    heaviestBrokenScaleFinalizeAnswer,
    possibleHeaviestCoins,
    balancedWeightInitialStates,
    balancedWeightStateKey,
    balancedWeightNormalizeStates,
    balancedWeightNormalizeWeighing,
    balancedWeightValidateWeighing,
    balancedWeightOutcomeForState,
    balancedWeightPartitionStates,
    balancedWeightFilterStates,
    balancedWeightChooseCheaterOutcome,
    balancedWeightBranchStatus,
    balancedWeightExpandExhaustiveNode,
    balancedWeightFinalizeAnswer,
    expertJudgeObjectCount,
    expertJudgeWeightValues,
    expertJudgeNormalizeAssignment,
    expertJudgeRandomAssignment,
    expertJudgeNormalizeWeighing,
    expertJudgeOutcomeForAssignment,
    expertJudgePossibleWeightsForSingleton,
    expertJudgeForcedWeights,
    expertJudgeEvaluateCertificate,
    numericSignatureInitialStates,
    numericSignatureNormalizeStates,
    numericSignatureStateKey,
    numericSignatureAmounts,
    numericSignatureAmountsValidation,
    numericSignatureTotal,
    numericSignatureDeficit,
    numericSignatureResidueForDeficit,
    numericSignatureObservationForState,
    numericSignatureFilterStates,
    numericSignaturePartitionStates,
    numericSignatureChooseCheaterOutcome,
    numericSignatureBranchStatus,
    numericSignatureExpandExhaustiveNode,
    numericSignatureFinalizeAnswer,
    selectedBagWeightValues,
    selectedBagWeightReferenceTotal,
    selectedBagWeightInitialStates,
    selectedBagWeightStateKey,
    selectedBagWeightNormalizeStates,
    selectedBagWeightComparison,
    selectedBagWeightOutcomeForState,
    selectedBagWeightPartitionStates,
    selectedBagWeightFilterStates,
    selectedBagWeightChooseCheaterOutcome,
    selectedBagWeightBranchStatus,
    selectedBagWeightExpandExhaustiveNode,
    selectedBagWeightFinalizeAnswer,
    subsetSignatureInitialStates,
    subsetSignatureNormalizeState,
    subsetSignatureNormalizeTests,
    subsetSignatureForState,
    subsetSignatureKey,
    subsetSignatureStateKey,
    subsetSignaturePartitionStates,
    subsetSignatureCheckStrategy,
    subsetSignatureChooseCheaterOutcome,
    subsetSignatureFilterStates,
    subsetSignatureFinalizeAnswer,
    balancedSubsetInitialStates,
    balancedSubsetNormalizeQuestions,
    balancedSubsetQuestionSum,
    balancedSubsetSignatureForState,
    balancedSubsetSignatureKey,
    balancedSubsetStateKey,
    balancedSubsetValidateQuestions,
    balancedSubsetPartitionStates,
    balancedSubsetCheckStrategy,
    balancedSubsetFilterStates,
    balancedSubsetChooseRandom,
    binaryCardsNumberRange,
    binaryCardsWeights,
    binaryCardsAllNumbers,
    binaryCardsCards,
    binaryCardsNormalizeSelection,
    binaryCardsSelectionForNumber,
    binaryCardsDecodeSelection,
    binaryCardsEvaluate,
    binaryCardsExhaustiveCheck,
    binaryCardsChooseRandom,
    fixedFeedbackAlphabet,
    fixedFeedbackPasswordLength,
    fixedFeedbackMaxTests,
    fixedFeedbackStateCount,
    fixedFeedbackNormalizeWord,
    fixedFeedbackRandomPassword,
    fixedFeedbackFeedback,
    fixedFeedbackNormalizePositions,
    fixedFeedbackInitialKnowledge,
    fixedFeedbackKnowledgeFromHistory,
    fixedFeedbackCandidateCount,
    fixedFeedbackKnownPassword,
    fixedFeedbackUniformGuess,
    fixedFeedbackStrategyHistory,
    fixedFeedbackFinalizeAnswer,
    fixedFeedbackExhaustiveCheck,
    ternaryQuestionObjectCount,
    ternaryQuestionMaxTests,
    ternaryQuestionAlphabet,
    ternaryQuestionInitialStates,
    ternaryQuestionNormalizeOutcomes,
    ternaryQuestionCodeForState,
    ternaryQuestionCodeKey,
    ternaryQuestionDecodeOutcomes,
    ternaryQuestionChooseRandom,
    ternaryQuestionEvaluate,
    ternaryQuestionExhaustiveCheck,
    repetitionCodeBitCount,
    repetitionCodeRepetitions,
    repetitionCodeMaxLies,
    repetitionCodeNumberRange,
    repetitionCodeAllNumbers,
    repetitionCodeQuestionCount,
    repetitionCodeQuestionRows,
    repetitionCodeTruthAnswers,
    repetitionCodeNormalizeLieIndex,
    repetitionCodeAnswersForCase,
    repetitionCodeNormalizeAnswers,
    repetitionCodeDecodeAnswers,
    repetitionCodeEvaluate,
    repetitionCodeChooseRandom,
    repetitionCodeExhaustiveCheck,
    finiteBinaryGridSize,
    finiteBinaryAdjacentGridStates,
    finiteBinaryAdjacentGridActions,
    finiteBinaryNormalizeGridPair,
    finiteBinaryInitialStates,
    finiteBinaryInitialActions,
    finiteBinaryStateKey,
    finiteBinaryActionKey,
    finiteBinaryResponseForState,
    finiteBinaryFilterStates,
    finiteBinaryPartitionStates,
    finiteBinaryGuaranteedAnswers,
    finiteBinaryBranchStatus,
    finiteBinaryChooseCheaterResponse,
    finiteBinaryExpandExhaustiveNode,
    finiteBinaryFinalizeAnswer,
    safePileNormalizePiles,
    safePileInitialStates,
    safePileNormalizeStates,
    safePileOutcomeForState,
    safePileFilterStates,
    safePilePartitionStates,
    safePileSafePileIds,
    safePileStateCounts,
    safePileBranchStatus,
    safePileChooseCheaterOutcome,
    safePileExpandExhaustiveNode,
    safePileFinalizeAnswer,
    xorSingleFlipPositionCount,
    xorSingleFlipBitsFromMask,
    xorSingleFlipMaskFromBits,
    xorSingleFlipChecksum,
    xorSingleFlipApplyFlip,
    xorSingleFlipRecommendedFlip,
    xorSingleFlipFinalGuess,
    xorSingleFlipInitialStates,
    xorSingleFlipStateKey,
    xorSingleFlipEvaluate,
    xorSingleFlipCheckStrategy,
    wiseMenParityPersonCount,
    wiseMenParityColorCount,
    wiseMenParityCodeword,
    wiseMenParityWordKey,
    wiseMenParityCodebook,
    wiseMenParityValidateCodebook,
    wiseMenParityNormalizeColors,
    wiseMenParityMessages,
    wiseMenParityDecodePerson,
    wiseMenParityEvaluate,
    wiseMenParityExhaustiveCheck,
    wiseMenParityRandomColors,
    wiseMenColorCountSageCount,
    wiseMenColorCountColorCount,
    wiseMenColorCountValues,
    wiseMenColorCountTargetCorrectMin,
    wiseMenColorCountValidateConfig,
    wiseMenColorCountCountsFromColors,
    wiseMenColorCountNormalizeColors,
    wiseMenColorCountValidateState,
    wiseMenColorCountPermutationParity,
    wiseMenColorCountTargetParityForSage,
    wiseMenColorCountCandidateOptions,
    wiseMenColorCountEvaluate,
    wiseMenColorCountInitialStates,
    wiseMenColorCountRandomState,
    wiseMenColorCountCheaterState,
    wiseMenColorCountExhaustiveCheck,
    threeLetterErasureAlphabet,
    threeLetterErasureNormalizeCodeword,
    threeLetterErasureNormalizeCodewords,
    threeLetterErasureErase,
    threeLetterErasureObservationRows,
    threeLetterErasureDecode,
    threeLetterErasureCheckTable,
    threeLetterErasureEvaluate,
    permutationMessageItemCount,
    permutationMessageLabels,
    permutationMessagePermutations,
    permutationMessageTable,
    permutationMessageNormalizeOrder,
    permutationMessageEncode,
    permutationMessageDecode,
    permutationMessageEvaluate,
    permutationMessageExhaustiveCheck,
    permutationCycleCount,
    permutationCycleMaxOpenings,
    permutationCycleNormalizePermutation,
    permutationCycleRandomPermutation,
    permutationCycleCheaterPermutation,
    permutationCycleDecomposition,
    permutationCycleTrace,
    permutationCycleRunAll,
    permutationCycleTypeStatistics,
    prisonerHatsParityPersonCount,
    prisonerHatsParityColorCount,
    prisonerHatsParityNormalizeBit,
    prisonerHatsParityNormalizeBits,
    prisonerHatsParityStateKey,
    prisonerHatsParityInitialStates,
    prisonerHatsParityNormalizeState,
    prisonerHatsParityRandomState,
    prisonerHatsParityVisibleAhead,
    prisonerHatsParityExpectedAnswer,
    prisonerHatsParityProtocolTranscript,
    prisonerHatsParityEvaluateTranscript,
    prisonerHatsParityExhaustiveCheck,
    hiddenHatParitySageCount,
    hiddenHatParityNumbers,
    hiddenHatParityTarget,
    hiddenHatParityPermutationParity,
    hiddenHatParityStateKey,
    hiddenHatParityInitialStates,
    hiddenHatParityNormalizeState,
    hiddenHatParityRandomState,
    hiddenHatParityExpectedAnswer,
    hiddenHatParityVisibleAhead,
    hiddenHatParityProtocolTranscript,
    hiddenHatParityEvaluateTranscript,
    hiddenHatParityExhaustiveCheck,
    finitePairCards,
    finitePairAllPairs,
    finitePairNormalizePair,
    finitePairKey,
    finitePairLabel,
    finitePairDisjoint,
    finitePairAllowedShownPairs,
    finitePairNormalizeAssignment,
    finitePairMatchingValidate,
    petyaVasyaCardCount,
    petyaVasyaCards,
    petyaVasyaNextCard,
    petyaVasyaNormalizeDistribution,
    petyaVasyaAllDistributions,
    petyaVasyaRandomDistribution,
    petyaVasyaStrategyMove,
    petyaVasyaEvaluate,
    petyaVasyaExhaustiveCheck,
    fitchCheneyRanks,
    fitchCheneySuits,
    fitchCheneyDeck,
    fitchCheneyNormalizeCards,
    fitchCheneyCardLabel,
    fitchCheneyDistance,
    fitchCheneyChooseAssistantMove,
    fitchCheneyDecodeShown,
    fitchCheneyEvaluate,
    fitchCheneyRandomHand,
    fitchCheneyExhaustiveCheck,
    twentyOneCardDeckSize,
    twentyOneCardColumnCount,
    twentyOneCardRowCount,
    twentyOneCardRoundCount,
    twentyOneCardCards,
    twentyOneCardInitialDeck,
    twentyOneCardDeal,
    twentyOneCardNormalizeColumn,
    twentyOneCardFindColumn,
    twentyOneCardCollectionOrder,
    twentyOneCardCollect,
    twentyOneCardStep,
    twentyOneCardTrace,
    twentyOneCardExhaustive,
    twentyOneCardRandomState,
    higherLowerBoxCount,
    higherLowerComparisonCounts,
    higherLowerBuildTable,
    higherLowerSolve,
    higherLowerActionScores,
    higherLowerBestGuesses,
    higherLowerInitialState,
    higherLowerStateSize,
    higherLowerStateValue,
    higherLowerGuessBranches,
    higherLowerApplyAnswer,
    movingTargetDefaultCube,
    movingTargetNormalizeGraph,
    movingTargetNormalizeVertices,
    movingTargetInitialStates,
    movingTargetCurrentStates,
    movingTargetValidation,
    movingTargetCaughtStates,
    movingTargetTransitionStates,
    movingTargetBranchStatus,
    movingTargetChooseCheaterOutcome,
    movingTargetExpandExhaustiveNode
  };
});
