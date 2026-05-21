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

  function initialCandidates(coinCount) {
    const count = Number(coinCount);
    if (!Number.isInteger(count) || count < 1) return [];
    return Array.from({ length: count }, (_item, index) => index + 1);
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

  function initialUnknownDirectionCandidates(coinCount) {
    const count = Number(coinCount);
    if (!Number.isInteger(count) || count < 1) return [];
    const result = [];
    for (let coin = 1; coin <= count; coin += 1) {
      result.push({ coin, direction: 'heavier' });
      result.push({ coin, direction: 'lighter' });
    }
    return result;
  }

  function normalizeUnknownDirectionCandidates(candidates, coinCount = null) {
    const limit = Number(coinCount);
    const hasLimit = coinCount != null && Number.isInteger(limit);
    const seen = new Set();
    const result = [];
    for (const raw of candidates || []) {
      const coin = Number(raw?.coin ?? raw?.id ?? raw?.[0]);
      const direction = normalizeDirection(raw?.direction ?? raw?.weight ?? raw?.[1]);
      if (!Number.isInteger(coin) || coin < 1 || !direction) continue;
      if (hasLimit && coin > limit) continue;
      const key = `${coin}:${direction}`;
      if (seen.has(key)) continue;
      seen.add(key);
      result.push({ coin, direction });
    }
    return result;
  }

  function knownDirectionCoinStatuses(candidates, coinCount) {
    const count = Number(coinCount);
    if (!Number.isInteger(count) || count < 1) return {};
    const current = uniqueCoins(candidates?.length ? candidates : initialCandidates(count), count);
    const possible = new Set(current);
    const result = {};
    for (let coin = 1; coin <= count; coin += 1) {
      if (!possible.has(coin)) result[coin] = 'genuine';
      else result[coin] = current.length === 1 ? 'definite_fake' : 'possible_fake';
    }
    return result;
  }

  function unknownDirectionCoinStatuses(candidates, coinCount) {
    const count = Number(coinCount);
    if (!Number.isInteger(count) || count < 1) return {};
    const current = normalizeUnknownDirectionCandidates(
      candidates?.length ? candidates : initialUnknownDirectionCandidates(count),
      count
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
    const normalized = normalizeUnknownDirectionCandidates([candidate])[0];
    return normalized ? `${normalized.coin} ${normalized.direction === 'lighter' ? 'легче' : 'тяжелее'}` : '';
  }

  function outcomeForUnknownDirectionCandidate(candidate, leftCoins, rightCoins, options = {}) {
    const normalized = normalizeUnknownDirectionCandidates([candidate])[0];
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
    const delta = normalized.direction === 'heavier' ? 1 : -1;
    if (onLeft) leftWeight += delta;
    if (onRight) rightWeight += delta;
    if (leftWeight > rightWeight) return 'left_down';
    if (rightWeight > leftWeight) return 'right_down';
    return 'balance';
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

  function filterUnknownDirectionCandidates(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const currentCandidates = normalizeUnknownDirectionCandidates(
      params?.currentCandidates?.length ? params.currentCandidates : initialUnknownDirectionCandidates(coinCount),
      Number.isInteger(coinCount) ? coinCount : null
    );
    const leftCoins = uniqueCoins(params?.leftCoins);
    const rightCoins = uniqueCoins(params?.rightCoins);
    const outcome = params?.outcome;
    return currentCandidates.filter(candidate =>
      outcomeForUnknownDirectionCandidate(candidate, leftCoins, rightCoins, {
        requireEqualPanCounts: params?.requireEqualPanCounts ?? params?.require_equal_pan_counts
      }) === outcome
    );
  }

  function partitionCandidates(params) {
    const partitions = Object.fromEntries(OUTCOMES.map(outcome => [outcome, filterCandidates({ ...params, outcome })]));
    return partitions;
  }

  function knownDirectionCandidateSetKey(candidates, coinCount = null) {
    return uniqueCoins(candidates || [], coinCount).sort((a, b) => a - b).join('|');
  }

  function permutedKnownDirectionCandidateSetKey(candidates, permutation, coinCount = null) {
    return uniqueCoins(candidates || [], coinCount)
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
    const leftCoins = params?.leftCoins ?? params?.left_coins;
    const rightCoins = params?.rightCoins ?? params?.right_coins;
    const permutation = coinListIsWithinLimit(leftCoins, coinCount) && coinListIsWithinLimit(rightCoins, coinCount)
      ? mirroredPanCoinPermutation(leftCoins, rightCoins, Number.isInteger(coinCount) ? coinCount : null)
      : null;
    if (permutation) {
      markSymmetricOutcomeChildren(children, {
        candidateSetKey: branchCandidates => knownDirectionCandidateSetKey(branchCandidates, coinCount),
        transformedCandidateSetKey: branchCandidates => permutedKnownDirectionCandidateSetKey(branchCandidates, permutation, coinCount),
        reason: 'pan_mirror_coin_permutation'
      });
    }
    return { partitions, children };
  }

  function exhaustiveUnknownDirectionBranchStatus(candidates, usedWeighings, maxWeighings) {
    const coinCount = Number(maxCoinFromCandidates(candidates));
    const remaining = normalizeUnknownDirectionCandidates(candidates, Number.isInteger(coinCount) ? coinCount : null);
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
    const normalized = normalizeUnknownDirectionCandidates([candidate])[0];
    if (!normalized) return null;
    return {
      coin: normalized.coin,
      direction: normalized.direction === 'heavier' ? 'lighter' : 'heavier'
    };
  }

  function unknownDirectionCandidateSetKey(candidates) {
    return normalizeUnknownDirectionCandidates(candidates || [])
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
    const currentCandidates = normalizeUnknownDirectionCandidates(
      params?.currentCandidates?.length ? params.currentCandidates : initialUnknownDirectionCandidates(coinCount),
      Number.isInteger(coinCount) ? coinCount : null
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
          status: exhaustiveUnknownDirectionBranchStatus(candidates, usedWeighings + 1, maxWeighings, params?.objective)
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

  function finalizeCheaterUnknownDirectionAnswer(params) {
    const coinCount = Number(params?.coin_count ?? params?.coinCount);
    const candidates = normalizeUnknownDirectionCandidates(
      params?.currentCandidates?.length ? params.currentCandidates : initialUnknownDirectionCandidates(coinCount),
      Number.isInteger(coinCount) ? coinCount : null
    );
    const selected = normalizeUnknownDirectionCandidates([{
      coin: params?.selectedCoin,
      direction: params?.selectedDirection ?? params?.selectedWeight
    }], Number.isInteger(coinCount) ? coinCount : null)[0];
    const selectedKey = selected ? unknownDirectionCandidateKey(selected) : null;
    const selectedCoin = Number(params?.selectedCoin);
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
      errors.push(`Показанная пара ${finitePairLabel(shownKey, cardCount)} декодируется неоднозначно: ${hiddenKeys.map(key => finitePairLabel(key, cardCount)).join(' и ')}.`);
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

  return {
    OUTCOMES,
    OUTCOME_LABELS,
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
    finitePairCards,
    finitePairAllPairs,
    finitePairNormalizePair,
    finitePairKey,
    finitePairLabel,
    finitePairDisjoint,
    finitePairAllowedShownPairs,
    finitePairNormalizeAssignment,
    finitePairMatchingValidate
  };
});
