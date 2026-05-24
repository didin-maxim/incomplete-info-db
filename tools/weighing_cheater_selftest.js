const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const cheater = require('../viewer/weighing_cheater.js');

function loadProblemConfig(relativePath) {
  const filePath = path.join(__dirname, '..', relativePath);
  return JSON.parse(fs.readFileSync(filePath, 'utf8')).interactive;
}

const twelveCoinConfig = loadProblemConfig('data/problems/weighings/counterfeit-12-coins-3-weighings.yaml');
const twelveCoinPreassignedConfig = loadProblemConfig('data/problems/weighings/counterfeit-12-coins-3-preassigned-weighings.yaml');
const limitedTwoUsesPreassignedConfig = loadProblemConfig('data/problems/generalizations/light-coin-limited-two-uses-preassigned-weighings.yaml');
const knopKnownLightPreassignedConfig = loadProblemConfig('data/problems/knop_2011_part5/knop-2011-known-light-coin-preassigned-ternary-code.yaml');
const knopOneErasureReserveConfig = loadProblemConfig('data/problems/knop_2011_part5/knop-2011-nine-light-coins-one-erasure-reserve-plan.yaml');
const knopTwoErasureReserveConfig = loadProblemConfig('data/problems/knop_2011_part5/knop-2011-nine-light-coins-two-erasure-reserve-plan.yaml');
const knopSaladinSpareConfig = loadProblemConfig('data/problems/knop_2011_part6/knop-saladin-four-weighings-one-spare.yaml');
const thirteenIdentifyOnlyConfig = loadProblemConfig('data/problems/classical_more/thirteen-coins-identify-only-three-weighings.yaml');
const thirteenPreassignedIdentifyOnlyConfig = loadProblemConfig('data/problems/classical_more/thirteen-coins-preassigned-identify-only-three-weighings.yaml');
const thirteenKnownGenuineConfig = loadProblemConfig('data/problems/classical_more/thirteen-coins-known-genuine-three-weighings.yaml');
const optionalLightEightConfig = loadProblemConfig('data/problems/knop_2011_part2/lighter-8-coins-optional-2-weighings.yaml');
const sixteenZeroOneTwoSignConfig = loadProblemConfig('data/problems/classical_more/sixteen-coins-zero-one-two-fakes-sign.yaml');
const matprazdnikSevenBagsConfig = loadProblemConfig('data/problems/extended_sources/matprazdnik-2023-seven-bags-two-weighings.yaml');
const knopSevenBagsSubsetConfig = loadProblemConfig('data/problems/knop_2011_part4/knop-2011-seven-bags-subset-one-weighing.yaml');
const apsimonThreeBagsConfig = loadProblemConfig('data/problems/knop_2011_part4/apsimon-knop-2011-three-bags-four-coins-two-weighings.yaml');
const mmoFourCoinsAllFakesConfig = loadProblemConfig('data/problems/knop_2011_part4/mmo-1988-four-coins-all-fakes-numeric-scale.yaml');
const knopOnePanTwoFakesConfig = loadProblemConfig('data/problems/knop_2011_part6/knop-2011-one-pan-9g-12g-two-fakes-family.yaml');
const problemsRuElevenBagsConfig = loadProblemConfig('data/problems/problems_ru_deep/problems-ru-78572-eleven-bags-two-numeric-balance-weighings.yaml');
const rmoThreeConsecutiveWeightsConfig = loadProblemConfig('data/problems/knop_2011_part4/rmo-2002-three-consecutive-light-weights.yaml');
const tenAdjacentSwappedLabelsConfig = loadProblemConfig('data/problems/knop_2011_part3/ten-weights-adjacent-labels-swapped-two-weighings.yaml');
const fourLabeledWeightsDefectiveConfig = loadProblemConfig('data/problems/knop_2011_part3/four-labeled-weights-one-defective-two-weighings.yaml');
const thirteenLabeledWeightsDefectiveConfig = loadProblemConfig('data/problems/knop_2011_part3/thirteen-labeled-weights-one-defective-three-weighings.yaml');
const lindstromTwoTriplesConfig = loadProblemConfig('data/problems/knop_2011_part4/lindstrom-1969-two-triples-one-fake-each.yaml');
const problemsRuSignOnlyConfig = loadProblemConfig('data/problems/problems_ru/problems-ru-32820-sign-only-two-weighings.yaml');
const matprazdnikRotatedTrayConfig = loadProblemConfig('data/problems/matprazdnik_savin/matprazdnik-2025-eighteen-coins-rotated-tray.yaml');
const moebiusLineConfig = loadProblemConfig('data/problems/moebius_tour/moebius-2023-ten-line-one-liar-four-questions.yaml');
const moebiusCoinsConfig = loadProblemConfig('data/problems/moebius_tour/moebius-2018-three-coins-knight-liar-genuine.yaml');
const treasureGridConfig = loadProblemConfig('data/problems/serbia/jsmo-2016-adjacent-treasure-10x10.yaml');
const moebiusSixCircleConfig = loadProblemConfig('data/problems/moebius_tour/moebius-2021-six-circle-adjacent-light-fakes-one-weighing.yaml');
const moebiusFiveCircleConfig = loadProblemConfig('data/problems/moebius_tour/moebius-2019-five-circle-light-fakes-count.yaml');
const moebiusGridLineConfig = loadProblemConfig('data/problems/moebius_tour/moebius-2022-3x3-line-of-three-light-fakes.yaml');
const kvantEightCircleHeavyConfig = loadProblemConfig('data/problems/kvant/kvant-2002-05-eight-circle-three-heavy.yaml');
const tenRowFakesRightConfig = loadProblemConfig('data/problems/knop_2011_part3/ten-row-fakes-on-right-two-weighings.yaml');
const knopNineCirclePairConfig = loadProblemConfig('data/problems/knop_2011_part3/nine-circle-two-adjacent-light-two-weighings.yaml');
const knopNineCircleTripleConfig = loadProblemConfig('data/problems/knop_2011_part3/nine-circle-three-consecutive-light-two-weighings.yaml');
const fiveCoinsTwoEqualFakesConfig = loadProblemConfig('data/problems/knop_2011_part3/five-coins-two-equal-fakes-find-genuine.yaml');
const rusanivskyiRustyConfig = loadProblemConfig('data/problems/rusanivskyi/rusanivskyi-2025-rusty-scales-eight-coins.yaml');
const bilboSafePileConfig = loadProblemConfig('data/problems/israelmath/israelmath-5781-bilbo-three-diamond-piles-safe-pile.yaml');
const mccmeSafePileConfig = loadProblemConfig('data/problems/web_weighings/mccme-2016-three-piles-one-genuine-pile.yaml');
const israelCandyBagsConfig = loadProblemConfig('data/problems/israelmath/israelmath-5783-six-candy-bags-two-weighings.yaml');
const spiderFlyCubeConfig = loadProblemConfig('data/problems/rusanivskyi/rusanivskyi-2025-spider-fly-cube-search.yaml');
const xorEightCoinsConfig = loadProblemConfig('data/problems/classical_more/xor-8-coins-one-flip.yaml');
const wiseMenSixColorsConfig = loadProblemConfig('data/problems/web_wise_prisoners/wise-men-6-32-colors-one-bit.yaml');
const wiseMenFourColorCountsConfig = loadProblemConfig('data/problems/web_wise_prisoners/wise-men-6-four-colors-permutation-parity.yaml');
const prisonersHatsLineConfig = loadProblemConfig('data/problems/classical/prisoners-hats-parity-line.yaml');
const wiseMenSixHiddenHatConfig = loadProblemConfig('data/problems/classical_more/wise-men-6-hidden-hat-number-parity.yaml');
const prisonersTenBoxesConfig = loadProblemConfig('data/problems/classical_more/prisoners-10-boxes-cycle-strategy.yaml');
const balancedSubsetEightConfig = loadProblemConfig('data/problems/bulgaria_bas/balanced-subset-8-three-questions.yaml');
const fixedBinaryQuestionsConfig = loadProblemConfig('data/problems/coding_games/fixed-questions-as-binary-code.yaml');
const fitchCheneyConfig = loadProblemConfig('data/problems/card_tricks/fitch-cheney-five-card-trick.yaml');
const binaryCardsConfig = loadProblemConfig('data/problems/classical/calendar-card-binary-trick.yaml');
const passwordFeedbackConfig = loadProblemConfig('data/problems/extracted_archives/calgary-jmc-2021-b3-password-feedback.yaml');
const passwordPermutationConfig = loadProblemConfig('data/problems/coding_games/password-feedback-permutation-variant.yaml');
const ternaryQuestionConfig = loadProblemConfig('data/problems/coding_games/one-counterfeit-among-27-three-ternary-questions.yaml');
const repetitionCodeConfig = loadProblemConfig('data/problems/coding_games/number-guessing-one-lie-by-repetition.yaml');
const permutationMessageConfig = loadProblemConfig('data/problems/coding_games/permutation-encodes-six-messages.yaml');
const twentyOneCardConfig = loadProblemConfig('data/problems/classical/twenty-one-card-trick.yaml');
const petyaVasyaConfig = loadProblemConfig('data/problems/matprazdnik_deep/matprazdnik-2026-five-cards-petya-vasya.yaml');
const higherLowerConfig = loadProblemConfig('data/problems/australia/mcya-2018-intermediate-higher-or-lower.yaml');
const expertJudgeOneWeightConfig = loadProblemConfig('data/problems/knop_2011_part6/knop-expert-judge-one-weighing-one-weight.yaml');
const expertJudgeEightCoinsConfig = loadProblemConfig('data/problems/knop_2011_part6/knop-expert-judge-eight-coins-3-4g-one-weighing.yaml');
const uniformityConfig = loadProblemConfig('data/problems/knop_2011_part6/knop-coin-uniformity-verification.yaml');
const knopPairDifferentWeightsConfig = loadProblemConfig('data/problems/knop_2011_part6/knop-2011-pair-light-different-weights-4-6-8.yaml');
const utyumParityConfig = loadProblemConfig('data/problems/russian_young/utyum-2010-seventeen-coins-parity-test.yaml');
const moebiusCupscalesConfig = loadProblemConfig('data/problems/moebius_tour/moebius-cupscales-2-silver-copper-counterfeit.yaml');
const rotatedTrayHelperFixtureConfig = {
  type: 'rotated_tray_balance_protocol',
  objective: 'identify_all_weights_after_rotation',
  position_count: 6,
  base_weights: [1, 2, 3, 1, 2, 3],
  max_weighings: 2
};

assert.deepEqual(twelveCoinConfig.type, 'single_counterfeit_unknown_direction');
assert.equal(twelveCoinConfig.modes.includes('cheater'), true);
assert.deepEqual(twelveCoinPreassignedConfig.type, 'single_counterfeit_unknown_direction');
assert.equal(twelveCoinPreassignedConfig.adaptive, false);
assert.equal(twelveCoinPreassignedConfig.modes.includes('exhaustive'), true);
assert.deepEqual(limitedTwoUsesPreassignedConfig.type, 'single_counterfeit_weighing');
assert.equal(limitedTwoUsesPreassignedConfig.adaptive, false);
assert.equal(limitedTwoUsesPreassignedConfig.counterfeit_weight, 'lighter');
assert.deepEqual(knopKnownLightPreassignedConfig.type, 'single_counterfeit_weighing');
assert.equal(knopKnownLightPreassignedConfig.adaptive, false);
assert.equal(knopKnownLightPreassignedConfig.coin_count, 27);
assert.equal(knopKnownLightPreassignedConfig.counterfeit_weight, 'lighter');
assert.deepEqual(knopOneErasureReserveConfig.type, 'single_counterfeit_weighing');
assert.equal(knopOneErasureReserveConfig.adaptive, false);
assert.equal(knopOneErasureReserveConfig.erasure_count, 1);
assert.deepEqual(knopTwoErasureReserveConfig.type, 'single_counterfeit_weighing');
assert.equal(knopTwoErasureReserveConfig.adaptive, false);
assert.equal(knopTwoErasureReserveConfig.erasure_count, 2);
assert.deepEqual(knopSaladinSpareConfig.type, 'single_counterfeit_unknown_direction');
assert.equal(knopSaladinSpareConfig.adaptive, false);
assert.equal(knopSaladinSpareConfig.erasure_count, 1);
assert.equal(knopSaladinSpareConfig.objective, 'identify_coin_and_sign');
assert.deepEqual(thirteenIdentifyOnlyConfig.type, 'single_counterfeit_unknown_direction');
assert.equal(thirteenIdentifyOnlyConfig.objective, 'identify_coin_only_unknown_direction');
assert.equal(thirteenIdentifyOnlyConfig.modes.includes('cheater'), true);
assert.deepEqual(thirteenPreassignedIdentifyOnlyConfig.type, 'single_counterfeit_unknown_direction');
assert.equal(thirteenPreassignedIdentifyOnlyConfig.adaptive, false);
assert.equal(thirteenPreassignedIdentifyOnlyConfig.objective, 'identify_coin_only_unknown_direction');
assert.equal(thirteenPreassignedIdentifyOnlyConfig.modes.includes('exhaustive'), true);
assert.deepEqual(thirteenKnownGenuineConfig.type, 'single_counterfeit_unknown_direction');
assert.equal(thirteenKnownGenuineConfig.known_genuine_count, 1);
assert.equal(thirteenKnownGenuineConfig.modes.includes('cheater'), true);
assert.deepEqual(optionalLightEightConfig.type, 'single_counterfeit_weighing');
assert.equal(optionalLightEightConfig.allow_no_counterfeit, true);
assert.equal(optionalLightEightConfig.objective, 'identify_coin_or_none');
assert.deepEqual(sixteenZeroOneTwoSignConfig.type, 'zero_one_two_counterfeit_sign');
assert.equal(sixteenZeroOneTwoSignConfig.objective, 'detect_presence_and_sign');
assert.equal(sixteenZeroOneTwoSignConfig.modes.includes('exhaustive'), true);
assert.deepEqual(matprazdnikSevenBagsConfig.type, 'numeric_linear_signature');
assert.equal(matprazdnikSevenBagsConfig.objective, 'identify_selected_bag_weight');
assert.equal(matprazdnikSevenBagsConfig.state_model, 'selected_bag_weight');
assert.deepEqual(knopSevenBagsSubsetConfig.type, 'numeric_linear_signature');
assert.equal(knopSevenBagsSubsetConfig.objective, 'identify_fake_bag_subset');
assert.equal(knopSevenBagsSubsetConfig.presentation, 'exercise');
assert.equal(knopSevenBagsSubsetConfig.observation_model, 'actual_weight');
assert.equal(knopSevenBagsSubsetConfig.allow_empty_subset, true);
assert.equal(knopSevenBagsSubsetConfig.exclude_all_fake, false);
assert.deepEqual(apsimonThreeBagsConfig.type, 'numeric_linear_signature');
assert.equal(apsimonThreeBagsConfig.presentation, 'exercise');
assert.equal(apsimonThreeBagsConfig.objective, 'identify_fake_bag_subset');
assert.equal(apsimonThreeBagsConfig.observation_model, 'actual_weight');
assert.equal(apsimonThreeBagsConfig.max_sampled_coins, 4);
assert.equal(cheater.numericSignatureSampledCoinCount([[2, 1, 0], [0, 1, 1]], apsimonThreeBagsConfig.bag_count), 4);
assert.equal(cheater.numericSignatureSampledCoinCount([[2, 1, 0], [0, 2, 1]], apsimonThreeBagsConfig.bag_count), 5);
{
  const options = {
    bag_count: apsimonThreeBagsConfig.bag_count,
    state_model: apsimonThreeBagsConfig.state_model,
    objective: apsimonThreeBagsConfig.objective,
    observation_model: apsimonThreeBagsConfig.observation_model,
    counterfeit_weight: apsimonThreeBagsConfig.counterfeit_weight,
    counterfeit_delta: apsimonThreeBagsConfig.counterfeit_delta,
    genuine_weight: apsimonThreeBagsConfig.genuine_weight,
    allow_empty_subset: apsimonThreeBagsConfig.allow_empty_subset,
    exclude_all_fake: apsimonThreeBagsConfig.exclude_all_fake
  };
  const first = cheater.numericSignatureExpandExhaustiveNode({
    ...options,
    amounts: [2, 1, 0],
    maxWeighings: 2,
    usedWeighings: 0
  }).children;
  const second = first.flatMap(node => cheater.numericSignatureExpandExhaustiveNode({
    ...options,
    amounts: [0, 1, 1],
    currentStates: node.states,
    maxWeighings: 2,
    usedWeighings: 1
  }).children);
  assert.equal(second.every(node => node.status === 'solved'), true);
}
assert.deepEqual(mmoFourCoinsAllFakesConfig.type, 'numeric_linear_signature');
assert.equal(mmoFourCoinsAllFakesConfig.presentation, 'exercise');
assert.equal(mmoFourCoinsAllFakesConfig.objective, 'identify_fake_bag_subset');
assert.equal(mmoFourCoinsAllFakesConfig.state_model, 'fake_bag_subset');
assert.equal(mmoFourCoinsAllFakesConfig.object_kind, 'coin');
assert.equal(mmoFourCoinsAllFakesConfig.selection_model, 'subset');
assert.equal(mmoFourCoinsAllFakesConfig.observation_model, 'actual_weight');
assert.equal(mmoFourCoinsAllFakesConfig.allow_empty_subset, true);
assert.equal(mmoFourCoinsAllFakesConfig.exclude_all_fake, false);
assert.deepEqual(knopOnePanTwoFakesConfig.type, 'numeric_linear_signature');
assert.equal(knopOnePanTwoFakesConfig.presentation, 'exercise');
assert.equal(knopOnePanTwoFakesConfig.objective, 'identify_light_and_heavy_counterfeit_coins');
assert.equal(knopOnePanTwoFakesConfig.state_model, 'signed_delta_states');
assert.equal(knopOnePanTwoFakesConfig.object_kind, 'coin');
assert.equal(knopOnePanTwoFakesConfig.selection_model, 'subset');
assert.equal(knopOnePanTwoFakesConfig.observation_model, 'actual_weight');
assert.equal(knopOnePanTwoFakesConfig.hidden_states.length, 12);
{
  const options = {
    bag_count: knopOnePanTwoFakesConfig.bag_count,
    state_model: knopOnePanTwoFakesConfig.state_model,
    hidden_states: knopOnePanTwoFakesConfig.hidden_states,
    objective: knopOnePanTwoFakesConfig.objective,
    observation_model: knopOnePanTwoFakesConfig.observation_model,
    genuine_weight: knopOnePanTwoFakesConfig.genuine_weight
  };
  const states = cheater.numericSignatureInitialStates(knopOnePanTwoFakesConfig.bag_count, options);
  assert.equal(states.length, 12);
  const light1Heavy2 = states.find(state => state.id === 'L1-H2');
  assert.equal(cheater.numericSignatureObservationForState(light1Heavy2, [1, 1, 0, 0], options).weight, 21);
  assert.equal(cheater.numericSignatureObservationForState(light1Heavy2, [1, 0, 0, 0], options).weight, 9);
  const firstBranches = cheater.numericSignatureExpandExhaustiveNode({
    ...options,
    amounts: [1, 1, 0, 0],
    maxWeighings: 2,
    usedWeighings: 0
  }).children;
  assert.deepEqual(firstBranches.map(branch => branch.states.length).sort((a, b) => a - b), [2, 2, 4, 4]);
  const secondBranches = firstBranches.flatMap(branch => cheater.numericSignatureExpandExhaustiveNode({
    ...options,
    amounts: [1, 0, 1, 0],
    currentStates: branch.states,
    maxWeighings: 2,
    usedWeighings: 1
  }).children);
  assert.equal(secondBranches.length, 12);
  assert.equal(secondBranches.every(branch => branch.status === 'solved'), true);
  assert.equal(cheater.numericSignatureFinalizeAnswer({
    ...options,
    currentStates: [light1Heavy2],
    selectedStateKey: cheater.numericSignatureStateKey(light1Heavy2)
  }).win, true);
}
assert.deepEqual(rmoThreeConsecutiveWeightsConfig.type, 'numeric_linear_signature');
assert.equal(rmoThreeConsecutiveWeightsConfig.presentation, 'exercise');
assert.equal(rmoThreeConsecutiveWeightsConfig.state_model, 'explicit_fake_sets');
assert.equal(rmoThreeConsecutiveWeightsConfig.object_kind, 'coin');
assert.equal(rmoThreeConsecutiveWeightsConfig.selection_model, 'subset');
assert.equal(rmoThreeConsecutiveWeightsConfig.hidden_states.length, 16);
{
  const options = {
    bag_count: rmoThreeConsecutiveWeightsConfig.bag_count,
    state_model: rmoThreeConsecutiveWeightsConfig.state_model,
    hidden_states: rmoThreeConsecutiveWeightsConfig.hidden_states,
    objective: rmoThreeConsecutiveWeightsConfig.objective,
    observation_model: rmoThreeConsecutiveWeightsConfig.observation_model,
    counterfeit_weight: rmoThreeConsecutiveWeightsConfig.counterfeit_weight,
    counterfeit_delta: rmoThreeConsecutiveWeightsConfig.counterfeit_delta,
    genuine_weight: rmoThreeConsecutiveWeightsConfig.genuine_weight
  };
  const states = cheater.numericSignatureInitialStates(rmoThreeConsecutiveWeightsConfig.bag_count, options);
  assert.equal(states.length, 16);
  const first = [0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0];
  const second = [0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0];
  const firstBranches = cheater.numericSignatureExpandExhaustiveNode({
    ...options,
    amounts: first,
    maxWeighings: 2,
    usedWeighings: 0
  }).children;
  assert.deepEqual(firstBranches.map(branch => branch.states.length).sort((a, b) => a - b), [4, 4, 4, 4]);
  const secondBranches = firstBranches.flatMap(branch => cheater.numericSignatureExpandExhaustiveNode({
    ...options,
    amounts: second,
    currentStates: branch.states,
    maxWeighings: 2,
    usedWeighings: 1
  }).children);
  assert.equal(secondBranches.length, 16);
  assert.equal(secondBranches.every(branch => branch.status === 'solved'), true);
}
assert.deepEqual(tenAdjacentSwappedLabelsConfig.type, 'numeric_linear_signature');
assert.equal(tenAdjacentSwappedLabelsConfig.presentation, 'exercise');
assert.equal(tenAdjacentSwappedLabelsConfig.objective, 'identify_swapped_adjacent_labels');
assert.equal(tenAdjacentSwappedLabelsConfig.state_model, 'signed_delta_states');
assert.equal(tenAdjacentSwappedLabelsConfig.observation_model, 'signed_tilt_pattern');
assert.equal(tenAdjacentSwappedLabelsConfig.selection_model, 'signed_quantities');
{
  const options = {
    bag_count: tenAdjacentSwappedLabelsConfig.bag_count,
    state_model: tenAdjacentSwappedLabelsConfig.state_model,
    hidden_states: tenAdjacentSwappedLabelsConfig.hidden_states,
    objective: tenAdjacentSwappedLabelsConfig.objective,
    observation_model: tenAdjacentSwappedLabelsConfig.observation_model,
    selection_model: tenAdjacentSwappedLabelsConfig.selection_model,
    nominal_weights: tenAdjacentSwappedLabelsConfig.nominal_weights,
    balance_constraint: tenAdjacentSwappedLabelsConfig.balance_constraint
  };
  const states = cheater.numericSignatureInitialStates(tenAdjacentSwappedLabelsConfig.bag_count, options);
  assert.equal(states.length, 9);
  const first = [0, 0, 1, 0, 1, 0, 0, -1, 0, 0];
  const second = [0, 1, 0, 0, 1, 0, -1, 0, 0, 0];
  assert.equal(cheater.numericSignatureAmountsValidation(first, 10, options).valid, true);
  assert.equal(cheater.numericSignatureAmountsValidation(second, 10, options).valid, true);
  assert.equal(cheater.numericSignatureAmountsValidation([1, 0, 0, 0, 0, 0, 0, 0, 0, 0], 10, options).valid, false);
  const signatures = new Set(states.map(state =>
    [first, second].map(row => cheater.numericSignatureTiltKeyForState(state, [row], options)).join('|')
  ));
  assert.equal(signatures.size, 9);
  const firstBranches = cheater.numericSignatureExpandExhaustiveNode({
    ...options,
    amounts: first,
    maxWeighings: 2,
    usedWeighings: 0
  }).children;
  assert.deepEqual(firstBranches.map(branch => branch.states.length).sort((a, b) => a - b), [3, 3, 3]);
  const secondBranches = firstBranches.flatMap(branch => cheater.numericSignatureExpandExhaustiveNode({
    ...options,
    amounts: second,
    amountRows: [first, second],
    currentStates: branch.states,
    maxWeighings: 2,
    usedWeighings: 1
  }).children);
  assert.equal(secondBranches.length, 9);
  assert.equal(secondBranches.every(branch => branch.status === 'solved'), true);
  const solvedSwap12 = states.find(state => state.id === 'swap-1-2');
  assert.equal(cheater.numericSignatureFinalizeAnswer({
    ...options,
    currentStates: [solvedSwap12],
    selectedBags: [1, 2]
  }).win, true);
  assert.equal(cheater.numericSignatureFinalizeAnswer({
    ...options,
    currentStates: [solvedSwap12],
    selectedBags: [2, 3]
  }).win, false);
}
assert.deepEqual(fourLabeledWeightsDefectiveConfig.type, 'numeric_linear_signature');
assert.equal(fourLabeledWeightsDefectiveConfig.presentation, 'exercise');
assert.equal(fourLabeledWeightsDefectiveConfig.objective, 'identify_defective_weight_and_sign');
assert.equal(fourLabeledWeightsDefectiveConfig.state_model, 'signed_delta_states');
assert.equal(fourLabeledWeightsDefectiveConfig.observation_model, 'signed_tilt_pattern');
assert.equal(fourLabeledWeightsDefectiveConfig.selection_model, 'signed_quantities');
{
  const options = {
    bag_count: fourLabeledWeightsDefectiveConfig.bag_count,
    state_model: fourLabeledWeightsDefectiveConfig.state_model,
    hidden_states: fourLabeledWeightsDefectiveConfig.hidden_states,
    objective: fourLabeledWeightsDefectiveConfig.objective,
    observation_model: fourLabeledWeightsDefectiveConfig.observation_model,
    selection_model: fourLabeledWeightsDefectiveConfig.selection_model,
    nominal_weights: fourLabeledWeightsDefectiveConfig.nominal_weights,
    balance_constraint: fourLabeledWeightsDefectiveConfig.balance_constraint
  };
  const states = cheater.numericSignatureInitialStates(fourLabeledWeightsDefectiveConfig.bag_count, options);
  assert.equal(states.length, 8);
  const first = [1, 1, -1, 0];
  const second = [1, 0, 1, -1];
  assert.equal(cheater.numericSignatureAmountsValidation(first, 4, options).valid, true);
  assert.equal(cheater.numericSignatureAmountsValidation(second, 4, options).valid, true);
  assert.equal(cheater.numericSignatureAmountsValidation([1, 0, -1, 0], 4, options).valid, false);
  const signatures = new Set(states.map(state =>
    cheater.numericSignatureTiltKeyForState(state, [first, second], options)
  ));
  assert.equal(signatures.size, 8);
  const firstBranches = cheater.numericSignatureExpandExhaustiveNode({
    ...options,
    amounts: first,
    maxWeighings: 2,
    usedWeighings: 0
  }).children;
  assert.deepEqual(firstBranches.map(branch => branch.states.length).sort((a, b) => a - b), [2, 3, 3]);
  const secondBranches = firstBranches.flatMap(branch => cheater.numericSignatureExpandExhaustiveNode({
    ...options,
    amounts: second,
    amountRows: [first, second],
    currentStates: branch.states,
    maxWeighings: 2,
    usedWeighings: 1
  }).children);
  assert.equal(secondBranches.length, 8);
  assert.equal(secondBranches.every(branch => branch.status === 'solved'), true);
  const hidden = states.find(state => state.id === 'W3H');
  const observed = [first, second].map(amounts =>
    cheater.numericSignatureObservationForState(hidden, amounts, options).observedDeviation
  );
  assert.deepEqual(observed, [-1, 1]);
  assert.deepEqual(
    cheater.numericSignatureFilterStates({
      ...options,
      bag_count: 4,
      amountRows: [first, second],
      observedDeviations: observed,
      currentStates: states
    }).map(state => state.id),
    ['W3H']
  );
  assert.equal(cheater.numericSignatureFinalizeAnswer({
    ...options,
    bag_count: 4,
    currentStates: [hidden],
    selectedStateKey: cheater.numericSignatureStateKey(hidden)
  }).win, true);
}
assert.deepEqual(thirteenLabeledWeightsDefectiveConfig.type, 'numeric_linear_signature');
assert.equal(thirteenLabeledWeightsDefectiveConfig.presentation, 'exercise');
assert.equal(thirteenLabeledWeightsDefectiveConfig.objective, 'identify_defective_weight_and_sign');
assert.equal(thirteenLabeledWeightsDefectiveConfig.state_model, 'signed_delta_states');
assert.equal(thirteenLabeledWeightsDefectiveConfig.observation_model, 'signed_tilt_pattern');
assert.equal(thirteenLabeledWeightsDefectiveConfig.selection_model, 'signed_quantities');
{
  const options = {
    bag_count: thirteenLabeledWeightsDefectiveConfig.bag_count,
    state_model: thirteenLabeledWeightsDefectiveConfig.state_model,
    hidden_states: thirteenLabeledWeightsDefectiveConfig.hidden_states,
    objective: thirteenLabeledWeightsDefectiveConfig.objective,
    observation_model: thirteenLabeledWeightsDefectiveConfig.observation_model,
    selection_model: thirteenLabeledWeightsDefectiveConfig.selection_model,
    nominal_weights: thirteenLabeledWeightsDefectiveConfig.nominal_weights,
    balance_constraint: thirteenLabeledWeightsDefectiveConfig.balance_constraint
  };
  const states = cheater.numericSignatureInitialStates(thirteenLabeledWeightsDefectiveConfig.bag_count, options);
  assert.equal(states.length, 26);
  const plan = [
    [1, 1, 1, 1, 1, -1, -1, 1, 0, -1, 0, 0, 0],
    [1, 1, 1, 0, 0, 1, 0, -1, 1, 1, -1, -1, 0],
    [1, 0, -1, 0, 1, 0, 1, -1, 1, -1, 0, 1, -1]
  ];
  assert.equal(plan.every(row => cheater.numericSignatureAmountsValidation(row, 13, options).valid), true);
  assert.equal(cheater.numericSignatureAmountsValidation([1, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 13, options).valid, false);
  const signatures = new Set(states.map(state =>
    cheater.numericSignatureTiltKeyForState(state, plan, options)
  ));
  assert.equal(signatures.size, 26);
  let frontier = [{ states, usedWeighings: 0, status: 'open' }];
  for (let step = 0; step < plan.length; step += 1) {
    const rows = plan.slice(0, step + 1);
    frontier = frontier.flatMap(node => {
      if (node.status !== 'open') return [node];
      return cheater.numericSignatureExpandExhaustiveNode({
        ...options,
        amounts: plan[step],
        amountRows: rows,
        currentStates: node.states,
        maxWeighings: 3,
        usedWeighings: step
      }).children;
    });
  }
  assert.equal(frontier.length, 26);
  assert.equal(frontier.every(branch => branch.status === 'solved'), true);
  assert.equal(frontier.every(branch => branch.states.length === 1), true);
  const hidden = states.find(state => state.id === 'W13L');
  const observed = plan.map(amounts =>
    cheater.numericSignatureObservationForState(hidden, amounts, options).observedDeviation
  );
  assert.deepEqual(observed, [0, 0, 1]);
  assert.deepEqual(
    cheater.numericSignatureFilterStates({
      ...options,
      bag_count: 13,
      amountRows: plan,
      observedDeviations: observed,
      currentStates: states
    }).map(state => state.id),
    ['W13L']
  );
}
assert.deepEqual(lindstromTwoTriplesConfig.type, 'numeric_linear_signature');
assert.equal(lindstromTwoTriplesConfig.presentation, 'exercise');
assert.equal(lindstromTwoTriplesConfig.objective, 'identify_fake_coin_set');
assert.equal(lindstromTwoTriplesConfig.state_model, 'explicit_fake_sets');
assert.equal(lindstromTwoTriplesConfig.object_kind, 'coin');
assert.equal(lindstromTwoTriplesConfig.selection_model, 'subset');
assert.equal(lindstromTwoTriplesConfig.answer_count, 2);
assert.equal(lindstromTwoTriplesConfig.observation_model, 'actual_weight');
assert.equal(lindstromTwoTriplesConfig.hidden_states.length, 9);
{
  const states = cheater.numericSignatureInitialStates(lindstromTwoTriplesConfig.bag_count, lindstromTwoTriplesConfig);
  assert.equal(states.length, 9);
  assert.deepEqual(states.map(state => state.bags), [
    [1, 4], [1, 5], [1, 6],
    [2, 4], [2, 5], [2, 6],
    [3, 4], [3, 5], [3, 6]
  ]);
  assert.equal(
    cheater.numericSignatureObservationForState({ bags: [1, 4] }, [1, 0, 0, 1, 0, 0], lindstromTwoTriplesConfig).weight,
    18
  );
  let frontier = [{ states, usedWeighings: 0, status: 'open' }];
  for (const amounts of [[1, 0, 0, 1, 0, 0], [0, 1, 0, 0, 1, 0]]) {
    frontier = frontier.flatMap(node => cheater.numericSignatureExpandExhaustiveNode({
      ...lindstromTwoTriplesConfig,
      bag_count: 6,
      amounts,
      currentStates: node.states,
      usedWeighings: node.usedWeighings,
      maxWeighings: 3
    }).children);
  }
  assert.equal(frontier.every(node => node.states.length <= 2), true);
  const finalFrontier = frontier.flatMap(node => {
    if (node.status === 'solved') return [node];
    const options = new Set(node.states.flatMap(state => state.bags));
    const shared = node.states[0].bags.filter(coin => node.states[1].bags.includes(coin));
    for (const coin of shared) options.delete(coin);
    const distinguishingCoin = [...options][0];
    const amounts = Array.from({ length: 6 }, (_item, index) => index + 1 === distinguishingCoin ? 1 : 0);
    return cheater.numericSignatureExpandExhaustiveNode({
      ...lindstromTwoTriplesConfig,
      bag_count: 6,
      amounts,
      currentStates: node.states,
      usedWeighings: 2,
      maxWeighings: 3
    }).children;
  });
  assert.equal(finalFrontier.length, 9);
  assert.equal(finalFrontier.every(branch => branch.status === 'solved'), true);
  assert.equal(finalFrontier.every(branch => branch.states.length === 1), true);
}
assert.deepEqual(problemsRuSignOnlyConfig.type, 'single_counterfeit_unknown_direction');
assert.equal(problemsRuSignOnlyConfig.presentation, 'exercise');
assert.equal(problemsRuSignOnlyConfig.objective, 'identify_sign_only_unknown_direction');
assert.equal(problemsRuSignOnlyConfig.coin_count, 100);
{
  const first = cheater.expandUnknownDirectionExhaustiveNode({
    coin_count: problemsRuSignOnlyConfig.coin_count,
    leftCoins: Array.from({ length: 50 }, (_item, index) => index + 1),
    rightCoins: Array.from({ length: 50 }, (_item, index) => index + 51),
    usedWeighings: 0,
    maxWeighings: 2,
    objective: problemsRuSignOnlyConfig.objective
  });
  const leftDown = first.children.find(child => child.outcome === 'left_down');
  assert.equal(leftDown.status, 'open');
  const second = cheater.expandUnknownDirectionExhaustiveNode({
    coin_count: problemsRuSignOnlyConfig.coin_count,
    currentCandidates: leftDown.candidates,
    leftCoins: Array.from({ length: 25 }, (_item, index) => index + 1),
    rightCoins: Array.from({ length: 25 }, (_item, index) => index + 26),
    usedWeighings: 1,
    maxWeighings: 2,
    objective: problemsRuSignOnlyConfig.objective
  });
  assert.equal(second.children.every(child => child.status === 'solved'), true);
  assert.deepEqual(second.children.map(child => child.candidates[0].direction).sort(), ['heavier', 'heavier', 'lighter']);
  const cheaterFinish = cheater.finalizeCheaterUnknownDirectionAnswer({
    coin_count: problemsRuSignOnlyConfig.coin_count,
    currentCandidates: leftDown.candidates,
    selectedDirection: 'heavier',
    objective: problemsRuSignOnlyConfig.objective
  });
  assert.equal(cheaterFinish.win, false);
  assert.equal(cheaterFinish.actualDirection, 'lighter');
}
assert.equal(matprazdnikRotatedTrayConfig, undefined, 'rotated-tray card is blocked until the official diagram/layout is restored');
assert.deepEqual(rotatedTrayHelperFixtureConfig.type, 'rotated_tray_balance_protocol');
assert.equal(rotatedTrayHelperFixtureConfig.objective, 'identify_all_weights_after_rotation');
const rotatedTrayStates = cheater.rotatedTrayInitialStates(rotatedTrayHelperFixtureConfig);
assert.equal(rotatedTrayStates.length, 3);
assert.deepEqual(cheater.rotatedTrayWeightsForRotation(rotatedTrayHelperFixtureConfig.base_weights, 1), [3, 1, 2, 3, 1, 2]);
assert.deepEqual(cheater.rotatedTrayNormalizeWeighing({
  ...rotatedTrayHelperFixtureConfig,
  left: [1, 4],
  right: [2, 5]
}).left, [1, 4]);
assert.equal(cheater.rotatedTrayNormalizeWeighing({
  ...rotatedTrayHelperFixtureConfig,
  left: [1],
  right: [1]
}).valid, false);
const rotatedFirst = cheater.rotatedTrayPartitionStates({
  ...rotatedTrayHelperFixtureConfig,
  left: [1],
  right: [2]
});
assert.deepEqual(rotatedFirst.map(part => [part.outcome, part.states.length]), [['left_down', 1], ['right_down', 2]]);
assert.deepEqual(
  cheater.rotatedTrayFilterStates({
    ...rotatedTrayHelperFixtureConfig,
    left: [1],
    right: [2],
    outcome: 'left_down'
  }).map(state => state.rotation),
  [1]
);
assert.deepEqual(
  cheater.rotatedTrayForcedWeights(rotatedTrayStates.slice(0, 1), rotatedTrayHelperFixtureConfig),
  [1, 2, 3, 1, 2, 3]
);
assert.equal(cheater.rotatedTrayBranchStatus(rotatedTrayStates, 0, 2), 'open');
assert.equal(cheater.rotatedTrayBranchStatus(rotatedTrayStates, 2, 2), 'failed');
assert.equal(cheater.rotatedTrayFinalizeAnswer({
  ...rotatedTrayHelperFixtureConfig,
  currentStates: [rotatedTrayStates[0]],
  answer: rotatedTrayStates[0].weights
}).win, true);
assert.deepEqual(moebiusLineConfig.type, 'finite_binary_state_protocol');
assert.equal(moebiusLineConfig.protocol, 'one_liar_line_neighborhood');
assert.equal(moebiusLineConfig.max_tests, 4);
assert.deepEqual(moebiusCoinsConfig.type, 'finite_binary_state_protocol');
assert.equal(moebiusCoinsConfig.protocol, 'knight_liar_fake_coin_subset');
assert.equal(moebiusCoinsConfig.max_tests, 2);
assert.deepEqual(israelCandyBagsConfig.type, 'balanced_weight_signature_protocol');
assert.equal(israelCandyBagsConfig.max_weighings, 2);
assert.deepEqual(treasureGridConfig.type, 'finite_binary_state_protocol');
assert.equal(treasureGridConfig.protocol, 'adjacent_pair_grid_search');
assert.equal(treasureGridConfig.max_tests, 50);
assert.deepEqual(spiderFlyCubeConfig.type, 'moving_target_graph_search');
assert.equal(spiderFlyCubeConfig.objective, 'capture_hidden_moving_target');
assert.equal(spiderFlyCubeConfig.max_tests, 4);
assert.deepEqual(xorEightCoinsConfig.type, 'xor_single_flip_protocol');
assert.equal(xorEightCoinsConfig.position_count, 8);
assert.equal(xorEightCoinsConfig.objective, 'identify_key_position');
assert.deepEqual(wiseMenSixColorsConfig.type, 'wise_men_even_parity_code');
assert.equal(wiseMenSixColorsConfig.person_count, 6);
assert.equal(wiseMenSixColorsConfig.color_count, 32);
assert.deepEqual(wiseMenFourColorCountsConfig.type, 'wise_men_color_count_parity_protocol');
assert.equal(wiseMenFourColorCountsConfig.sage_count, 6);
assert.equal(wiseMenFourColorCountsConfig.color_count, 4);
assert.deepEqual(wiseMenFourColorCountsConfig.count_values, [0, 1, 2, 3]);
assert.equal(wiseMenFourColorCountsConfig.target_correct_min, 3);
assert.deepEqual(prisonersHatsLineConfig.type, 'prisoners_hats_parity_line');
assert.equal(prisonersHatsLineConfig.person_count, 6);
assert.equal(prisonersHatsLineConfig.color_count, 2);
assert.equal(prisonersHatsLineConfig.objective, 'guarantee_all_but_first_correct');
assert.deepEqual(prisonersHatsLineConfig.modes, ['random', 'guided', 'exhaustive']);
assert.deepEqual(wiseMenSixHiddenHatConfig.type, 'hidden_hat_number_parity_protocol');
assert.equal(wiseMenSixHiddenHatConfig.sage_count, 6);
assert.equal(wiseMenSixHiddenHatConfig.number_max, 7);
assert.equal(wiseMenSixHiddenHatConfig.objective, 'guarantee_all_but_first_correct');
assert.deepEqual(prisonersTenBoxesConfig.type, 'permutation_cycle_protocol');
assert.equal(prisonersTenBoxesConfig.prisoner_count, 10);
assert.equal(prisonersTenBoxesConfig.max_openings, 5);
assert.equal(prisonersTenBoxesConfig.objective, 'all_agents_find_own_state');
assert.deepEqual(balancedSubsetEightConfig.type, 'balanced_subset_question_code');
assert.equal(balancedSubsetEightConfig.object_count, 8);
assert.equal(balancedSubsetEightConfig.target_sum, 18);
assert.deepEqual(fixedBinaryQuestionsConfig.type, 'binary_question_code');
assert.equal(fixedBinaryQuestionsConfig.object_count, 8);
assert.equal(fixedBinaryQuestionsConfig.max_tests, 3);
assert.deepEqual(fitchCheneyConfig.type, 'fitch_cheney_card_trick');
assert.equal(fitchCheneyConfig.deck_size, 52);
assert.equal(fitchCheneyConfig.objective, 'identify_hidden_card');
assert.deepEqual(binaryCardsConfig.type, 'binary_cards_number_trick');
assert.equal(binaryCardsConfig.card_count, 5);
assert.equal(binaryCardsConfig.number_max, 31);
assert.deepEqual(passwordFeedbackConfig.type, 'fixed_feedback_code');
assert.equal(passwordFeedbackConfig.password_length, 10);
assert.equal(passwordFeedbackConfig.max_tests, 4);
assert.deepEqual(passwordPermutationConfig.type, 'fixed_feedback_code');
assert.equal(passwordPermutationConfig.password_model, 'permutation');
assert.equal(passwordPermutationConfig.password_length, 4);
assert.deepEqual(ternaryQuestionConfig.type, 'ternary_question_code');
assert.equal(ternaryQuestionConfig.object_count, 27);
assert.equal(ternaryQuestionConfig.max_tests, 3);
assert.deepEqual(repetitionCodeConfig.type, 'repetition_code_one_lie_questions');
assert.equal(repetitionCodeConfig.bit_count, 3);
assert.equal(repetitionCodeConfig.repetitions_per_bit, 3);
assert.deepEqual(permutationMessageConfig.type, 'permutation_message_order_code');
assert.equal(permutationMessageConfig.item_count, 3);
assert.equal(permutationMessageConfig.message_count, 6);
assert.deepEqual(twentyOneCardConfig.type, 'twenty_one_card_trick');
assert.equal(twentyOneCardConfig.deck_size, 21);
assert.equal(twentyOneCardConfig.round_count, 3);
assert.deepEqual(petyaVasyaConfig.type, 'petya_vasya_five_cards_protocol');
assert.equal(petyaVasyaConfig.card_count, 5);
assert.equal(petyaVasyaConfig.objective, 'identify_spectator_card');
assert.deepEqual(higherLowerConfig.type, 'higher_lower_strategy_game');
assert.equal(higherLowerConfig.box_count, 9);
assert.equal(higherLowerConfig.objective, 'maximize_win_probability');
assert.deepEqual(expertJudgeOneWeightConfig.type, 'expert_judge_certificate');
assert.equal(expertJudgeOneWeightConfig.objective, 'identify_one_weight');
assert.deepEqual(expertJudgeEightCoinsConfig.type, 'expert_judge_certificate');
assert.equal(expertJudgeEightCoinsConfig.objective, 'identify_all_weights');
assert.equal(expertJudgeEightCoinsConfig.weight_model, 'equal_halves_binary');
assert.deepEqual(uniformityConfig.type, 'uniformity_verification');
assert.equal(uniformityConfig.objective, 'verify_all_weights_equal');
assert.deepEqual(uniformityConfig.modes, ['exhaustive', 'sandbox']);
assert.deepEqual(utyumParityConfig.type, 'selected_coin_parity_detector');
assert.equal(utyumParityConfig.objective, 'identify_selected_coin_type');
assert.deepEqual(moebiusCupscalesConfig.type, 'single_counterfeit_weighing');
assert.deepEqual(moebiusCupscalesConfig.counterfeit_weight_options, ['lighter', 'heavier']);
assert.equal(moebiusCupscalesConfig.coin_types.filter(type => type === 'silver').length, 4);
assert.equal(moebiusCupscalesConfig.coin_types.filter(type => type === 'copper').length, 5);
assert.equal(
  cheater.outcomeForCandidate(2, 'lighter', [1], [5], moebiusCupscalesConfig),
  'right_down',
  'mixed normal masses must affect the scale even when the fake is off the pans'
);
assert.deepEqual(
  cheater.filterCandidates({
    ...moebiusCupscalesConfig,
    currentCandidates: cheater.initialCandidates(moebiusCupscalesConfig.coin_count),
    counterfeit_weight: 'lighter',
    leftCoins: [1, 5],
    rightCoins: [2, 6],
    outcome: 'right_down'
  }),
  [1, 5]
);
assert.deepEqual(
  cheater.filterCandidates({
    ...moebiusCupscalesConfig,
    currentCandidates: cheater.initialCandidates(moebiusCupscalesConfig.coin_count),
    counterfeit_weight: 'heavier',
    leftCoins: [1, 5],
    rightCoins: [2, 6],
    outcome: 'left_down'
  }),
  [1, 5]
);

const uniformityBadStates = cheater.uniformityBadStates(uniformityConfig);
assert.equal(uniformityBadStates.length, 7);
const uniformityEmpty = cheater.uniformityAnalyzePlan(uniformityConfig, []);
assert.equal(uniformityEmpty.ok, false);
assert.equal(uniformityEmpty.remaining.length, 7);
const uniformityOneWeighing = cheater.uniformityAnalyzePlan(uniformityConfig, [
  { left: [1, 2], right: [3, 4] }
]);
assert.equal(uniformityOneWeighing.ok, false);
assert.equal(uniformityOneWeighing.remaining.length > 0, true);
const uniformityGoodPlan = cheater.uniformityAnalyzePlan(uniformityConfig, [
  { left: [1, 2], right: [3, 4] },
  { left: [1], right: [2] }
]);
assert.equal(uniformityGoodPlan.ok, true);
assert.equal(uniformityGoodPlan.remaining.length, 0);
const uniformityBadPlan = cheater.uniformityAnalyzePlan(uniformityConfig, [
  { left: [1], right: [2, 3] }
]);
assert.equal(uniformityBadPlan.ok, false);
assert.equal(uniformityBadPlan.errors.length, 1);

const utyumParityStates = cheater.parityDetectorInitialStates(utyumParityConfig);
assert.equal(utyumParityStates.length, 24310);
assert.equal(cheater.parityDetectorSelectedType({ fakeMask: 1 }, utyumParityConfig), 'fake');
assert.equal(cheater.parityDetectorSelectedType({ fakeMask: 2 }, utyumParityConfig), 'genuine');
assert.equal(
  cheater.parityDetectorOutcomeForState({ fakeMask: 0b11111111 }, { left: 2, right: 3 }),
  'equal'
);
assert.equal(
  cheater.parityDetectorOutcomeForState({ fakeMask: 0b11111111 }, { left: 8, right: 9 }),
  'different'
);
const utyumPairPlan = [[2, 3], [4, 5], [6, 7], [8, 9], [10, 11], [12, 13], [14, 15], [16, 17]]
  .map(([left, right]) => ({ left, right }));
const utyumGoodPlan = cheater.parityDetectorAnalyzePlan(utyumParityConfig, utyumPairPlan);
assert.equal(utyumGoodPlan.ok, true);
assert.equal(utyumGoodPlan.conflicts.length, 0);
assert.equal(utyumGoodPlan.partitions.every(part => {
  const equalCount = part.signature.filter(outcome => outcome === 'equal').length;
  return part.forcedType === (equalCount % 2 === 0 ? 'genuine' : 'fake');
}), true);
const utyumShortPlan = cheater.parityDetectorAnalyzePlan(utyumParityConfig, utyumPairPlan.slice(0, 7));
assert.equal(utyumShortPlan.ok, false);
assert.equal(utyumShortPlan.conflicts.length > 0, true);
const utyumCheaterFirst = cheater.parityDetectorChooseCheaterOutcome({
  ...utyumParityConfig,
  currentStates: utyumParityStates,
  test: { left: 2, right: 3 }
});
assert.equal(['equal', 'different'].includes(utyumCheaterFirst.outcome), true);
assert.equal(utyumCheaterFirst.states.length > 0, true);

const petyaVasyaAll = cheater.petyaVasyaExhaustiveCheck(petyaVasyaConfig);
assert.equal(petyaVasyaAll.ok, true);
assert.equal(petyaVasyaAll.checked, 30);
const petyaVasyaSample = cheater.petyaVasyaEvaluate({
  ...petyaVasyaConfig,
  distribution: { petya: [1, 4], vasya: [5], spectators: [2, 3] },
  namedCard: 1,
  answerCard: 2
});
assert.equal(petyaVasyaSample.strategyWin, true);
assert.equal(petyaVasyaSample.petyaFollowsStrategy, true);
assert.equal(petyaVasyaSample.vasyaAnswerSpectator, true);
const petyaVasyaWrong = cheater.petyaVasyaEvaluate({
  ...petyaVasyaConfig,
  distribution: { petya: [1, 4], vasya: [5], spectators: [2, 3] },
  namedCard: 4,
  answerCard: 5
});
assert.equal(petyaVasyaWrong.strategyWin, false);
assert.equal(petyaVasyaWrong.vasyaAnswerSpectator, false);

const expertJudgeCases = [
  {
    object_count: 3,
    left: [3],
    right: [1, 2],
    assignment: [1, 2, 3],
    forced: [{ object: 3, weight: 3 }]
  },
  {
    object_count: 7,
    left: [7],
    right: [1, 2, 3],
    assignment: [1, 2, 3, 4, 5, 6, 7],
    forced: [{ object: 7, weight: 7 }]
  },
  {
    object_count: 8,
    left: [7, 8],
    right: [1, 2, 3, 4, 5],
    assignment: [1, 2, 3, 4, 5, 6, 7, 8],
    forced: [{ object: 6, weight: 6 }]
  },
  {
    object_count: 25,
    left: [19, 20, 21, 22, 23, 24, 25],
    right: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
    assignment: Array.from({ length: 25 }, (_item, index) => index + 1),
    forced: [{ object: 18, weight: 18 }]
  }
];

for (const testCase of expertJudgeCases) {
  const result = cheater.expertJudgeEvaluateCertificate(testCase);
  assert.equal(result.success, true);
  for (const expected of testCase.forced) {
    const forced = result.learned.find(item => item.object === expected.object);
    assert.ok(forced, `missing forced object ${expected.object} for N=${testCase.object_count}`);
    assert.equal(forced.forcedWeight, expected.weight);
  }
}

assert.deepEqual(
  cheater.expertJudgePossibleWeightsForSingleton('outside', {
    object_count: 8,
    left: [1, 2],
    right: [3, 4, 5, 6, 7],
    outcome: 'balance'
  }),
  [6]
);

const expertJudgeEightResult = cheater.expertJudgeEvaluateCertificate({
  ...expertJudgeEightCoinsConfig,
  object_count: 8,
  left: [1, 2, 3, 4],
  right: [5, 6, 7],
  assignment: [3, 3, 3, 3, 4, 4, 4, 4]
});
assert.equal(expertJudgeEightResult.outcome, 'balance');
assert.equal(expertJudgeEightResult.compatibleCount, 1);
assert.equal(expertJudgeEightResult.success, true);
assert.deepEqual(
  expertJudgeEightResult.learned.map(item => [item.object, item.forcedWeight]),
  [[1, 3], [2, 3], [3, 3], [4, 3], [5, 4], [6, 4], [7, 4], [8, 4]]
);
const expertJudgeEightWeak = cheater.expertJudgeEvaluateCertificate({
  ...expertJudgeEightCoinsConfig,
  object_count: 8,
  left: [1],
  right: [2],
  outcome: 'balance'
});
assert.equal(expertJudgeEightWeak.success, false);
assert.equal(expertJudgeEightWeak.compatibleCount > 1, true);

const higherLowerSolution = cheater.higherLowerSolve(higherLowerConfig);
assert.equal(higherLowerSolution.comparisons.find(row => row.boxCount === 3).first.value.label, '2/3');
assert.deepEqual(
  higherLowerSolution.comparisons.find(row => row.boxCount === 3).first.moves.filter(move => move.optimal).map(move => move.guess),
  [1, 3]
);
assert.equal(higherLowerSolution.comparisons.find(row => row.boxCount === 4).first.value.label, '1/2');
assert.equal(higherLowerSolution.first.value.label, '5/9');
assert.deepEqual(higherLowerSolution.first.moves.filter(move => move.optimal).map(move => move.guess), [1, 3, 5, 7, 9]);
assert.deepEqual(cheater.higherLowerBestGuesses({ ...higherLowerConfig, box_count: 4, turn: 'second' }), [1, 2, 3, 4]);
const higherLowerRoot = cheater.higherLowerInitialState(higherLowerConfig);
const afterMiddleLower = cheater.higherLowerApplyAnswer(higherLowerRoot, 5, 'lower', higherLowerConfig);
assert.deepEqual(afterMiddleLower, { low: 1, high: 4, turn: 'second', finished: false, winner: null });
assert.equal(cheater.higherLowerStateValue(afterMiddleLower, higherLowerConfig).label, '1/2');

assert.deepEqual(
  cheater.fixedFeedbackFeedback('ABCDEABCDE', 'AABBDDCCEE', passwordFeedbackConfig),
  [1, 8, 10]
);
const passwordStrategyHistory = cheater.fixedFeedbackStrategyHistory('ABCDEABCDE', passwordFeedbackConfig);
assert.equal(passwordStrategyHistory.length, 4);
assert.equal(cheater.fixedFeedbackCandidateCount(passwordStrategyHistory, passwordFeedbackConfig), 1);
assert.equal(cheater.fixedFeedbackKnownPassword(passwordStrategyHistory, passwordFeedbackConfig), 'ABCDEABCDE');
assert.equal(
  cheater.fixedFeedbackFinalizeAnswer({
    ...passwordFeedbackConfig,
    history: passwordStrategyHistory,
    secret: 'ABCDEABCDE',
    answer: 'ABCDEABCDE'
  }).win,
  true
);
const passwordFeedbackExhaustive = cheater.fixedFeedbackExhaustiveCheck(passwordFeedbackConfig);
assert.equal(passwordFeedbackExhaustive.success, true);
assert.equal(passwordFeedbackExhaustive.checked, 5 ** 10);
assert.equal(passwordFeedbackExhaustive.requiredTests, 4);

assert.deepEqual(cheater.ternaryQuestionCodeForState(1, ternaryQuestionConfig), [0, 0, 0]);
assert.deepEqual(cheater.ternaryQuestionCodeForState(27, ternaryQuestionConfig), [2, 2, 2]);
assert.equal(cheater.ternaryQuestionDecodeOutcomes([2, 2, 2], ternaryQuestionConfig).number, 27);
const ternaryQuestionExhaustive = cheater.ternaryQuestionExhaustiveCheck(ternaryQuestionConfig);
assert.equal(ternaryQuestionExhaustive.success, true);
assert.equal(ternaryQuestionExhaustive.checked, 27);
assert.equal(ternaryQuestionExhaustive.collisions.length, 0);

function finiteAction(config, actionId) {
  const action = cheater.finiteBinaryInitialActions(config).find(item => cheater.finiteBinaryActionKey(item) === actionId);
  assert.ok(action, `missing finite action ${actionId}`);
  return action;
}

function finiteApply(config, states, actionId, response) {
  return cheater.finiteBinaryFilterStates({
    ...config,
    currentStates: states,
    action: finiteAction(config, actionId),
    response
  });
}

assert.equal(cheater.finiteBinaryInitialStates(moebiusLineConfig).length, 10);
assert.equal(cheater.finiteBinaryInitialActions(moebiusLineConfig).length, 10);
assert.equal(
  cheater.finiteBinaryResponseForState(
    { id: 'liar_2', liar: 2 },
    finiteAction(moebiusLineConfig, 'ask_2'),
    moebiusLineConfig
  ),
  'yes'
);
assert.deepEqual(
  finiteApply(moebiusLineConfig, cheater.finiteBinaryInitialStates(moebiusLineConfig), 'ask_2', 'yes').map(state => state.liar),
  [1, 2, 3]
);
let lineBranch = cheater.finiteBinaryInitialStates(moebiusLineConfig);
lineBranch = finiteApply(moebiusLineConfig, lineBranch, 'ask_2', 'no');
lineBranch = finiteApply(moebiusLineConfig, lineBranch, 'ask_5', 'no');
lineBranch = finiteApply(moebiusLineConfig, lineBranch, 'ask_7', 'no');
lineBranch = finiteApply(moebiusLineConfig, lineBranch, 'ask_8', 'no');
assert.deepEqual(lineBranch.map(state => state.liar), [10]);
assert.equal(
  cheater.finiteBinaryBranchStatus(lineBranch, 4, moebiusLineConfig.max_tests, moebiusLineConfig),
  'solved'
);

function lineStrategyAction(history) {
  const key = history.join('');
  if (key === '') return 'ask_2';
  if (key === 'yes') return 'ask_1';
  if (key === 'yesyes') return 'ask_3';
  if (key === 'no') return 'ask_5';
  if (key === 'noyes') return 'ask_3';
  if (key === 'noyesno') return 'ask_4';
  if (key === 'nono') return 'ask_7';
  if (key === 'nonoyes') return 'ask_6';
  if (key === 'nonono') return 'ask_8';
  return null;
}

for (const hidden of cheater.finiteBinaryInitialStates(moebiusLineConfig)) {
  let states = cheater.finiteBinaryInitialStates(moebiusLineConfig);
  const history = [];
  while (!cheater.finiteBinaryGuaranteedAnswers(states, moebiusLineConfig).length) {
    const actionId = lineStrategyAction(history);
    assert.ok(actionId, `line strategy missing branch ${history.join('/')}`);
    const action = finiteAction(moebiusLineConfig, actionId);
    const response = cheater.finiteBinaryResponseForState(hidden, action, moebiusLineConfig);
    history.push(response);
    states = cheater.finiteBinaryFilterStates({ ...moebiusLineConfig, currentStates: states, action, response });
    assert.ok(history.length <= moebiusLineConfig.max_tests);
  }
  assert.deepEqual(cheater.finiteBinaryGuaranteedAnswers(states, moebiusLineConfig), [hidden.id]);
}

assert.equal(cheater.finiteBinaryInitialStates(moebiusCoinsConfig).length, 6);
assert.equal(cheater.finiteBinaryInitialActions(moebiusCoinsConfig).length, 12);
let coinBranch = cheater.finiteBinaryInitialStates(moebiusCoinsConfig);
coinBranch = finiteApply(moebiusCoinsConfig, coinBranch, 'ask_Вася_1', 'yes');
assert.deepEqual(coinBranch.map(state => [state.fakeCoin, state.knight]), [[1, 'Вася'], [2, 'Петя'], [3, 'Петя']]);
coinBranch = finiteApply(moebiusCoinsConfig, coinBranch, 'ask_Вася_2', 'no');
assert.deepEqual(cheater.finiteBinaryGuaranteedAnswers(coinBranch, moebiusCoinsConfig), [3]);
assert.equal(
  cheater.finiteBinaryFinalizeAnswer({ ...moebiusCoinsConfig, currentStates: coinBranch, selectedCoin: 3 }).win,
  true
);
for (const hidden of cheater.finiteBinaryInitialStates(moebiusCoinsConfig)) {
  let states = cheater.finiteBinaryInitialStates(moebiusCoinsConfig);
  const firstAction = finiteAction(moebiusCoinsConfig, 'ask_Вася_1');
  const firstResponse = cheater.finiteBinaryResponseForState(hidden, firstAction, moebiusCoinsConfig);
  states = cheater.finiteBinaryFilterStates({ ...moebiusCoinsConfig, currentStates: states, action: firstAction, response: firstResponse });
  const secondAction = finiteAction(moebiusCoinsConfig, 'ask_Вася_2');
  const secondResponse = cheater.finiteBinaryResponseForState(hidden, secondAction, moebiusCoinsConfig);
  states = cheater.finiteBinaryFilterStates({ ...moebiusCoinsConfig, currentStates: states, action: secondAction, response: secondResponse });
  const guaranteed = cheater.finiteBinaryGuaranteedAnswers(states, moebiusCoinsConfig);
  assert.equal(guaranteed.length > 0, true);
  assert.equal(guaranteed.includes(hidden.fakeCoin), false);
}
const coinCheater = cheater.finiteBinaryChooseCheaterResponse({
  ...moebiusCoinsConfig,
  currentStates: cheater.finiteBinaryInitialStates(moebiusCoinsConfig),
  action: finiteAction(moebiusCoinsConfig, 'ask_Вася_1')
});
assert.deepEqual(coinCheater.scores, {
  yes: { states: 3, solved: false, answers: [] },
  no: { states: 3, solved: false, answers: [] }
});

const candyStates = cheater.balancedWeightInitialStates(israelCandyBagsConfig);
assert.equal(candyStates.length, 7);
assert.equal(cheater.balancedWeightValidateWeighing({
  ...israelCandyBagsConfig,
  left: [6],
  right: [1]
}).valid, false);
const candyStrategy = [
  { left: [6], right: [1, 2, 3] },
  { left: [2, 4], right: [1, 5] }
];
for (const hidden of candyStates) {
  let states = candyStates;
  const transcript = [];
  for (const weighing of candyStrategy) {
    const outcome = cheater.balancedWeightOutcomeForState(hidden, {
      ...israelCandyBagsConfig,
      ...weighing
    });
    transcript.push(outcome);
    states = cheater.balancedWeightFilterStates({
      ...israelCandyBagsConfig,
      ...weighing,
      currentStates: states,
      outcome
    });
  }
  assert.equal(states.length, 1, `candy transcript ${transcript.join('/')} should isolate one state`);
  assert.equal(cheater.balancedWeightStateKey(states[0]), cheater.balancedWeightStateKey(hidden));
  assert.equal(
    cheater.balancedWeightFinalizeAnswer({
      ...israelCandyBagsConfig,
      currentStates: states,
      selectedBag: hidden.bag
    }).win,
    true
  );
}
assert.deepEqual(
  candyStrategy.map(weighing => cheater.balancedWeightOutcomeForState({ id: 'none', bag: null }, {
    ...israelCandyBagsConfig,
    ...weighing
  })),
  ['balance', 'balance']
);

assert.equal(cheater.finiteBinaryInitialStates(treasureGridConfig).length, 180);
assert.equal(cheater.finiteBinaryInitialActions(treasureGridConfig).length, 100);
assert.equal(
  cheater.finiteBinaryResponseForState(
    { id: 'r1c1_r1c2', cells: ['r1c1', 'r1c2'] },
    finiteAction(treasureGridConfig, 'ask_r1c1'),
    treasureGridConfig
  ),
  'yes'
);
assert.equal(
  cheater.finiteBinaryResponseForState(
    { id: 'r1c1_r1c2', cells: ['r1c1', 'r1c2'] },
    finiteAction(treasureGridConfig, 'ask_r2c2'),
    treasureGridConfig
  ),
  'no'
);
let treasureBranch = cheater.finiteBinaryInitialStates(treasureGridConfig);
treasureBranch = cheater.finiteBinaryFilterStates({
  ...treasureGridConfig,
  currentStates: treasureBranch,
  action: finiteAction(treasureGridConfig, 'ask_r1c1'),
  response: 'yes'
});
assert.deepEqual(treasureBranch.map(state => state.id), ['r1c1_r1c2', 'r1c1_r2c1']);
treasureBranch = cheater.finiteBinaryFilterStates({
  ...treasureGridConfig,
  currentStates: treasureBranch,
  action: finiteAction(treasureGridConfig, 'ask_r1c2'),
  response: 'yes'
});
assert.deepEqual(cheater.finiteBinaryGuaranteedAnswers(treasureBranch, treasureGridConfig), ['r1c1_r1c2']);
assert.equal(
  cheater.finiteBinaryFinalizeAnswer({
    ...treasureGridConfig,
    currentStates: treasureBranch,
    selectedCells: ['r1c1', 'r1c2']
  }).win,
  true
);
const treasureCheater = cheater.finiteBinaryChooseCheaterResponse({
  ...treasureGridConfig,
  currentStates: cheater.finiteBinaryInitialStates(treasureGridConfig),
  action: finiteAction(treasureGridConfig, 'ask_r1c1')
});
assert.equal(treasureCheater.response, 'no');
assert.deepEqual(treasureCheater.scores, {
  yes: { states: 2, solved: false, answers: [] },
  no: { states: 178, solved: false, answers: [] }
});
const treasureExpansion = cheater.finiteBinaryExpandExhaustiveNode({
  ...treasureGridConfig,
  currentStates: cheater.finiteBinaryInitialStates(treasureGridConfig),
  action: finiteAction(treasureGridConfig, 'ask_r1c1'),
  usedTests: 0,
  maxTests: 50
});
assert.deepEqual(treasureExpansion.children.map(child => child.response), ['yes', 'no']);
assert.deepEqual(treasureExpansion.children.map(child => child.states.length), [2, 178]);

assert.deepEqual(moebiusSixCircleConfig.type, 'constrained_light_counterfeit_sets');
assert.deepEqual(moebiusFiveCircleConfig.type, 'constrained_light_counterfeit_sets');
assert.deepEqual(moebiusGridLineConfig.type, 'constrained_light_counterfeit_sets');
assert.deepEqual(rusanivskyiRustyConfig.type, 'threshold_balance_counterfeit_sets');
assert.equal(rusanivskyiRustyConfig.reliable_difference, 2);

const rustyStates = cheater.thresholdBalanceInitialStates(
  rusanivskyiRustyConfig.coin_count,
  rusanivskyiRustyConfig.counterfeit_count
);
assert.equal(rustyStates.length, 70);
assert.equal(
  cheater.outcomeForThresholdBalanceState(
    { coins: [1, 2, 3, 4] },
    [1, 2],
    [5, 6],
    rusanivskyiRustyConfig
  ),
  'left_reliable_lighter'
);
assert.equal(
  cheater.outcomeForThresholdBalanceState(
    { coins: [1, 2, 3, 4] },
    [1],
    [5],
    rusanivskyiRustyConfig
  ),
  'no_reliable_tilt'
);
const rustyOneAgainstOne = cheater.thresholdBalancePartitionStates({
  ...rusanivskyiRustyConfig,
  currentStates: rustyStates,
  leftCoins: [1],
  rightCoins: [5]
});
assert.equal(rustyOneAgainstOne.left_reliable_lighter.length, 0);
assert.equal(rustyOneAgainstOne.right_reliable_lighter.length, 0);
assert.equal(rustyOneAgainstOne.no_reliable_tilt.length, 70);
assert.equal(
  cheater.thresholdBalanceChooseCheaterOutcome({
    ...rusanivskyiRustyConfig,
    currentStates: rustyStates,
    leftCoins: [1],
    rightCoins: [5]
  }).outcome,
  'no_reliable_tilt'
);
assert.equal(
  cheater.thresholdBalanceFilterStates({
    ...rusanivskyiRustyConfig,
    currentStates: rustyStates,
    leftCoins: [1, 2],
    rightCoins: [5, 6],
    outcome: 'left_reliable_lighter'
  }).every(state => state.coins.includes(1) && state.coins.includes(2) && !state.coins.includes(5) && !state.coins.includes(6)),
  true
);
const rustySolved = cheater.thresholdBalanceFinalizeAnswer({
  ...rusanivskyiRustyConfig,
  currentStates: [{ coins: [1, 2, 3, 4] }],
  selectedCoins: [1, 2, 3, 4]
});
assert.equal(rustySolved.win, true);
assert.equal(cheater.movingTargetInitialStates(spiderFlyCubeConfig).length, 8);
assert.deepEqual(
  cheater.movingTargetValidation(['C', 'F', 'H'], spiderFlyCubeConfig),
  { valid: true, error: '', checked: ['C', 'F', 'H'] }
);
assert.equal(cheater.movingTargetValidation(['C', 'F'], spiderFlyCubeConfig).valid, false);
let flyStates = cheater.movingTargetInitialStates(spiderFlyCubeConfig);
for (const [index, checkedVertices] of [['C', 'F', 'H'], ['B', 'D', 'E'], ['B', 'D', 'E'], ['C', 'F', 'H']].entries()) {
  const step = cheater.movingTargetChooseCheaterOutcome({
    ...spiderFlyCubeConfig,
    currentStates: flyStates,
    checkedVertices,
    usedTests: index,
    maxTests: spiderFlyCubeConfig.max_tests
  });
  flyStates = step.states;
  if (index < 3) assert.equal(step.outcome, 'not_found');
  else assert.equal(step.outcome, 'caught');
}
const movingTargetFailed = cheater.movingTargetChooseCheaterOutcome({
  ...spiderFlyCubeConfig,
  currentStates: cheater.movingTargetInitialStates(spiderFlyCubeConfig),
  checkedVertices: ['A', 'B', 'C'],
  usedTests: 3,
  maxTests: 4
});
assert.equal(movingTargetFailed.status, 'failed');
assert.equal(movingTargetFailed.states.length > 0, true);
assert.deepEqual(bilboSafePileConfig.type, 'safe_pile_balance_certificate');
assert.deepEqual(bilboSafePileConfig.pile_sizes, [17, 21, 27]);

const bilboPiles = cheater.safePileNormalizePiles(bilboSafePileConfig);
assert.deepEqual(bilboPiles.map(pile => pile.size), [17, 21, 27]);
const bilboStates = cheater.safePileInitialStates(bilboSafePileConfig);
assert.equal(bilboStates.length, 130);
const bilboSolutionLeft = bilboPiles[0].diamonds;
const bilboSolutionRight = bilboPiles[1].diamonds.slice(0, 17);
const bilboExpansion = cheater.safePileExpandExhaustiveNode({
  ...bilboSafePileConfig,
  currentStates: bilboStates,
  leftDiamonds: bilboSolutionLeft,
  rightDiamonds: bilboSolutionRight,
  usedWeighings: 0,
  maxWeighings: 1
});
assert.deepEqual(bilboExpansion.children.map(child => child.outcome), ['left_down', 'right_down', 'balance']);
assert.deepEqual(
  Object.fromEntries(bilboExpansion.children.map(child => [child.outcome, child.safePiles])),
  { left_down: ['C'], right_down: ['C'], balance: ['A'] }
);
assert.deepEqual(bilboExpansion.children.map(child => child.status), ['solved', 'solved', 'solved']);
assert.equal(
  cheater.safePileFinalizeAnswer({
    ...bilboSafePileConfig,
    currentStates: bilboExpansion.children.find(child => child.outcome === 'balance').states,
    selectedPile: 'A'
  }).win,
  true
);
assert.equal(
  cheater.safePileFinalizeAnswer({
    ...bilboSafePileConfig,
    currentStates: bilboExpansion.children.find(child => child.outcome === 'left_down').states,
    selectedPile: 'A'
  }).win,
  false
);
assert.deepEqual(mccmeSafePileConfig.type, 'safe_pile_balance_certificate');
assert.deepEqual(mccmeSafePileConfig.pile_sizes, [17, 21, 27]);
assert.equal(mccmeSafePileConfig.objective, 'identify_safe_pile');
assert.equal(mccmeSafePileConfig.object_nouns.many, 'монет');
const mccmePiles = cheater.safePileNormalizePiles(mccmeSafePileConfig);
const mccmeStates = cheater.safePileInitialStates(mccmeSafePileConfig);
assert.equal(mccmeStates.length, 130);
const mccmeExpansion = cheater.safePileExpandExhaustiveNode({
  ...mccmeSafePileConfig,
  currentStates: mccmeStates,
  leftDiamonds: mccmePiles[0].diamonds,
  rightDiamonds: mccmePiles[1].diamonds.slice(0, 17),
  usedWeighings: 0,
  maxWeighings: 1
});
assert.deepEqual(
  Object.fromEntries(mccmeExpansion.children.map(child => [child.outcome, child.safePiles])),
  { left_down: ['C'], right_down: ['C'], balance: ['A'] }
);
assert.deepEqual(mccmeExpansion.children.map(child => child.status), ['solved', 'solved', 'solved']);

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

assert.deepEqual(
  cheater.knownDirectionCoinStatuses([2, 4], 5),
  {
    1: 'genuine',
    2: 'possible_fake',
    3: 'genuine',
    4: 'possible_fake',
    5: 'genuine'
  }
);
assert.deepEqual(
  cheater.knownDirectionCoinStatuses([4], 5),
  {
    1: 'genuine',
    2: 'genuine',
    3: 'genuine',
    4: 'definite_fake',
    5: 'genuine'
  }
);

const optionalLightStates = cheater.initialCandidates(8, true);
assert.deepEqual(optionalLightStates, [0, 1, 2, 3, 4, 5, 6, 7, 8]);
const optionalFirst = cheater.partitionCandidates({
  coin_count: 8,
  counterfeit_weight: 'light',
  allow_no_counterfeit: true,
  currentCandidates: optionalLightStates,
  leftCoins: [1, 2, 3],
  rightCoins: [4, 5, 6]
});
assert.deepEqual(optionalFirst.left_down, [4, 5, 6]);
assert.deepEqual(optionalFirst.right_down, [1, 2, 3]);
assert.deepEqual(optionalFirst.balance, [0, 7, 8]);
const optionalNullBranch = cheater.expandExhaustiveNode({
  coin_count: 8,
  counterfeit_weight: 'light',
  allow_no_counterfeit: true,
  currentCandidates: optionalFirst.balance,
  leftCoins: [7],
  rightCoins: [8],
  usedWeighings: 1,
  maxWeighings: 2
});
assert.deepEqual(
  Object.fromEntries(optionalNullBranch.children.map(child => [child.outcome, child.candidates])),
  { left_down: [8], right_down: [7], balance: [0] }
);
assert.equal(
  cheater.finalizeCheaterAnswer({
    coin_count: 8,
    allow_no_counterfeit: true,
    currentCandidates: [0],
    selectedCoin: 'none'
  }).win,
  true
);
assert.deepEqual(
  cheater.knownDirectionCoinStatuses([0], 8, { allowNoCounterfeit: true }),
  { 1: 'genuine', 2: 'genuine', 3: 'genuine', 4: 'genuine', 5: 'genuine', 6: 'genuine', 7: 'genuine', 8: 'genuine' }
);

const zeroOneTwoStates = cheater.zeroOneTwoSignInitialStates(16);
assert.equal(zeroOneTwoStates.length, 273);
assert.deepEqual(cheater.zeroOneTwoSignAnswerClasses(zeroOneTwoStates), ['none', 'lighter', 'heavier']);
assert.equal(zeroOneTwoStates.some(state => state.coins.length === 2 && state.sign === 'mixed'), false);
assert.equal(
  cheater.zeroOneTwoSignOutcomeForState(
    { sign: 'heavier', coins: [1, 9] },
    { coin_count: 16, leftCoins: [1, 2], rightCoins: [9, 10], requireEqualPanCounts: true }
  ),
  'balance'
);
assert.equal(
  cheater.zeroOneTwoSignOutcomeForState(
    { sign: 'lighter', coins: [1, 2] },
    { coin_count: 16, leftCoins: [1, 3], rightCoins: [4, 5], requireEqualPanCounts: true }
  ),
  'right_down'
);
const zeroOneTwoFirstPartition = cheater.zeroOneTwoSignPartitionStates({
  coin_count: 16,
  currentStates: zeroOneTwoStates,
  leftCoins: [1, 2, 3, 4, 5, 6, 7, 8],
  rightCoins: [9, 10, 11, 12, 13, 14, 15, 16],
  requireEqualPanCounts: true
});
assert.deepEqual(zeroOneTwoFirstPartition.map(part => part.states.length), [72, 72, 129]);
assert.deepEqual(zeroOneTwoFirstPartition.map(part => part.answerClasses), [
  ['lighter', 'heavier'],
  ['lighter', 'heavier'],
  ['none', 'lighter', 'heavier']
]);

function zeroOneTwoApply(states, hidden, left, right) {
  const outcome = cheater.zeroOneTwoSignOutcomeForState(hidden, {
    coin_count: 16,
    leftCoins: left,
    rightCoins: right,
    requireEqualPanCounts: true
  });
  return {
    outcome,
    states: cheater.zeroOneTwoSignFilterStates({
      coin_count: 16,
      currentStates: states,
      leftCoins: left,
      rightCoins: right,
      outcome,
      requireEqualPanCounts: true
    })
  };
}

function zeroOneTwoKuhnPlan(hidden) {
  let states = zeroOneTwoStates;
  const first = zeroOneTwoApply(states, hidden, [1, 2, 3, 4, 5, 6, 7, 8], [9, 10, 11, 12, 13, 14, 15, 16]);
  states = first.states;
  if (first.outcome === 'balance') {
    const second = zeroOneTwoApply(states, hidden, [8, 9, 11, 13, 16], [1, 10, 12, 14, 15]);
    states = second.states;
    if (second.outcome === 'balance') {
      const third = zeroOneTwoApply(states, hidden, [1, 8, 9], [4, 5, 7]);
      const answer = third.outcome === 'balance' ? 'none' : (third.outcome === 'left_down' ? 'heavier' : 'lighter');
      return { answer, states: third.states };
    }
    const third = zeroOneTwoApply(states, hidden, [11, 16], [9, 13]);
    const answer = second.outcome === 'left_down'
      ? (third.outcome === 'balance' ? 'lighter' : 'heavier')
      : (third.outcome === 'balance' ? 'heavier' : 'lighter');
    return { answer, states: third.states };
  }

  const heavyPan = first.outcome === 'left_down'
    ? [1, 2, 3, 4, 5, 6, 7, 8]
    : [9, 10, 11, 12, 13, 14, 15, 16];
  const lightPan = first.outcome === 'left_down'
    ? [9, 10, 11, 12, 13, 14, 15, 16]
    : [1, 2, 3, 4, 5, 6, 7, 8];
  const H = index => heavyPan[index - 1];
  const L = index => lightPan[index - 1];
  const second = zeroOneTwoApply(
    states,
    hidden,
    [H(4), H(5), H(6), H(7), L(3), L(4), L(5), L(7)],
    [H(1), H(2), H(3), H(8), L(1), L(2), L(6), L(8)]
  );
  states = second.states;
  if (second.outcome === 'balance') {
    const third = zeroOneTwoApply(states, hidden, [L(1), L(2)], [L(6), L(8)]);
    return { answer: third.outcome === 'balance' ? 'heavier' : 'lighter', states: third.states };
  }
  if (second.outcome === 'left_down') {
    const third = zeroOneTwoApply(
      states,
      hidden,
      [H(4), H(5), H(6), H(7), L(1)],
      [H(1), H(2), H(3), L(4), L(7)]
    );
    return { answer: third.outcome === 'left_down' ? 'heavier' : 'lighter', states: third.states };
  }
  const third = zeroOneTwoApply(
    states,
    hidden,
    [H(4), H(5), H(7), L(2), L(6), L(8)],
    [H(1), H(2), H(3), H(8), L(3), L(7)]
  );
  return { answer: third.outcome === 'right_down' ? 'heavier' : 'lighter', states: third.states };
}

for (const hidden of zeroOneTwoStates) {
  const result = zeroOneTwoKuhnPlan(hidden);
  assert.equal(result.answer, hidden.answer);
  assert.deepEqual(cheater.zeroOneTwoSignAnswerClasses(result.states), [hidden.answer]);
}

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
assert.deepEqual(firstExhaustive.children.map(child => child.status), ['open', 'covered', 'open']);
assert.equal(firstExhaustive.children[1].coveredByOutcome, 'left_down');
assert.equal(firstExhaustive.children[1].symmetryReason, 'pan_mirror_coin_permutation');

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
  assert.deepEqual(expanded.children.map(child => child.status), ['solved', 'covered', 'solved']);
  assert.equal(expanded.children[1].coveredByOutcome, 'left_down');
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
assert.deepEqual(impossibleOneWeighing.children.map(child => child.status), ['solved', 'covered', 'failed']);

const knownDirectionAsymmetricSameSizes = cheater.expandExhaustiveNode({
  coin_count: 6,
  counterfeit_weight: 'heavy',
  currentCandidates: [1, 2, 4, 5],
  leftCoins: [1, 2],
  rightCoins: [3, 4],
  usedWeighings: 0,
  maxWeighings: 2
});
assert.deepEqual(knownDirectionAsymmetricSameSizes.children.map(child => child.candidates), [[1, 2], [4], [5]]);
assert.equal(knownDirectionAsymmetricSameSizes.children.some(child => child.status === 'covered'), false);

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
assert.deepEqual(unknownFirst.children.map(child => child.status), ['open', 'covered', 'open']);
assert.equal(unknownFirst.children[1].coveredByOutcome, 'left_down');
assert.equal(unknownFirst.children[1].symmetryReason, 'direction_flip');
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
assert.equal(
  cheater.flippedUnknownDirectionCandidateSetKey(unknownFirst.children[0].candidates),
  cheater.unknownDirectionCandidateSetKey(unknownFirst.children[1].candidates)
);

const unknownFirstEssentialBranches = unknownFirst.children.filter(child => child.status !== 'covered');
assert.deepEqual(unknownFirstEssentialBranches.map(child => child.outcome), ['left_down', 'balance']);

const unknownBalanceBranch = unknownFirst.children.find(child => child.outcome === 'balance');
const unknownDeeperSymmetry = cheater.expandUnknownDirectionExhaustiveNode({
  coin_count: 12,
  currentCandidates: unknownBalanceBranch.candidates,
  leftCoins: [9],
  rightCoins: [10],
  usedWeighings: unknownBalanceBranch.usedWeighings,
  maxWeighings: 3
});
assert.deepEqual(unknownDeeperSymmetry.children.map(child => child.candidates.length), [2, 2, 4]);
assert.deepEqual(unknownDeeperSymmetry.children.map(child => child.status), ['open', 'covered', 'open']);
assert.equal(unknownDeeperSymmetry.children[1].coveredByOutcome, 'left_down');
assert.equal(unknownDeeperSymmetry.children[1].symmetryReason, 'direction_flip');

const unknownAsymmetricSplit = cheater.expandUnknownDirectionExhaustiveNode({
  coin_count: 3,
  currentCandidates: [
    { coin: 1, direction: 'heavier' },
    { coin: 1, direction: 'lighter' },
    { coin: 2, direction: 'heavier' }
  ],
  leftCoins: [1],
  rightCoins: [2],
  usedWeighings: 0,
  maxWeighings: 2
});
assert.equal(unknownAsymmetricSplit.children.some(child => child.status === 'covered'), false);

const unknownEqualSizeNonEquivalent = cheater.expandUnknownDirectionExhaustiveNode({
  coin_count: 4,
  currentCandidates: [
    { coin: 1, direction: 'heavier' },
    { coin: 2, direction: 'lighter' },
    { coin: 3, direction: 'heavier' },
    { coin: 4, direction: 'lighter' }
  ],
  leftCoins: [1, 2],
  rightCoins: [3, 4],
  usedWeighings: 0,
  maxWeighings: 2
});
assert.deepEqual(unknownEqualSizeNonEquivalent.children.map(child => child.candidates.length), [2, 2]);
assert.equal(unknownEqualSizeNonEquivalent.children.some(child => child.status === 'covered'), false);

const fourCoinsStandardCandidates = cheater.initialUnknownDirectionCandidates(4, true);
assert.equal(fourCoinsStandardCandidates.length, 9);
assert.deepEqual(fourCoinsStandardCandidates[0], { coin: 0, direction: 'none' });

const fourCoinsStandardFirst = cheater.expandUnknownDirectionExhaustiveNode({
  coin_count: 4,
  currentCandidates: fourCoinsStandardCandidates,
  leftCoins: [1, 2],
  rightCoins: [3, 5],
  usedWeighings: 0,
  maxWeighings: 2,
  objective: 'identify_coin_and_sign',
  allow_no_counterfeit: true,
  require_equal_pan_counts: true
});
assert.deepEqual(fourCoinsStandardFirst.children.map(child => child.candidates.length), [3, 3, 3]);

const fourCoinsStandardBalance = fourCoinsStandardFirst.children.find(child => child.outcome === 'balance');
assert.deepEqual(
  fourCoinsStandardBalance.candidates,
  [{ coin: 0, direction: 'none' }, { coin: 4, direction: 'heavier' }, { coin: 4, direction: 'lighter' }]
);

const fourCoinsStandardSecond = cheater.expandUnknownDirectionExhaustiveNode({
  coin_count: 4,
  currentCandidates: fourCoinsStandardBalance.candidates,
  leftCoins: [4],
  rightCoins: [5],
  usedWeighings: fourCoinsStandardBalance.usedWeighings,
  maxWeighings: 2,
  objective: 'identify_coin_and_sign',
  allow_no_counterfeit: true,
  require_equal_pan_counts: true
});
assert.deepEqual(fourCoinsStandardSecond.children.map(child => child.status), ['solved', 'covered', 'solved']);

const fourCoinsStandardNoneAnswer = cheater.finalizeCheaterUnknownDirectionAnswer({
  coin_count: 4,
  currentCandidates: [{ coin: 0, direction: 'none' }],
  selectedCoin: 'none',
  selectedDirection: 'none',
  objective: 'identify_coin_and_sign',
  allow_no_counterfeit: true
});
assert.equal(fourCoinsStandardNoneAnswer.win, true);
assert.deepEqual(fourCoinsStandardNoneAnswer.actualCandidate, { coin: 0, direction: 'none' });

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

const twelveCoinPreassignedCheck = cheater.checkUnknownDirectionNonadaptiveStrategy({
  coin_count: twelveCoinPreassignedConfig.coin_count,
  max_weighings: twelveCoinPreassignedConfig.max_weighings,
  weighings: twelveCoinPreassignedConfig.preset_weighings,
  require_equal_pan_counts: twelveCoinPreassignedConfig.require_equal_pan_counts
});
assert.equal(twelveCoinPreassignedCheck.success, true);
assert.equal(twelveCoinPreassignedCheck.states.length, 24);
assert.equal(twelveCoinPreassignedCheck.partitions.length, 24);
assert.deepEqual(twelveCoinPreassignedCheck.conflicts, []);
assert.deepEqual(
  cheater.unknownDirectionSignatureForCandidate(
    { coin: 7, direction: 'heavier' },
    twelveCoinPreassignedConfig.preset_weighings,
    { coinCount: twelveCoinPreassignedConfig.coin_count, requireEqualPanCounts: true }
  ),
  ['left_down', 'balance', 'right_down']
);

const twelveCoinBadPreassignedCheck = cheater.checkUnknownDirectionNonadaptiveStrategy({
  coin_count: twelveCoinPreassignedConfig.coin_count,
  max_weighings: twelveCoinPreassignedConfig.max_weighings,
  weighings: [
    twelveCoinPreassignedConfig.preset_weighings[0],
    twelveCoinPreassignedConfig.preset_weighings[1],
    twelveCoinPreassignedConfig.preset_weighings[1]
  ],
  require_equal_pan_counts: true
});
assert.equal(twelveCoinBadPreassignedCheck.success, false);
assert.equal(twelveCoinBadPreassignedCheck.conflicts.length > 0, true);

const limitedTwoUsesPreassignedCheck = cheater.checkKnownDirectionNonadaptiveStrategy({
  coin_count: limitedTwoUsesPreassignedConfig.coin_count,
  max_weighings: limitedTwoUsesPreassignedConfig.max_weighings,
  counterfeit_weight: limitedTwoUsesPreassignedConfig.counterfeit_weight,
  weighings: limitedTwoUsesPreassignedConfig.preset_weighings,
  require_equal_pan_counts: limitedTwoUsesPreassignedConfig.require_equal_pan_counts
});
assert.equal(limitedTwoUsesPreassignedCheck.success, true);
assert.equal(limitedTwoUsesPreassignedCheck.states.length, 99);
assert.equal(limitedTwoUsesPreassignedCheck.partitions.length, 99);
assert.deepEqual(limitedTwoUsesPreassignedCheck.conflicts, []);
assert.deepEqual(
  cheater.knownDirectionSignatureForCandidate(
    20,
    'lighter',
    limitedTwoUsesPreassignedConfig.preset_weighings,
    { coinCount: limitedTwoUsesPreassignedConfig.coin_count, requireEqualPanCounts: true }
  ),
  ['right_down', 'balance', 'right_down', 'balance', 'balance', 'balance', 'balance']
);

const limitedTwoUsesBadPreassignedCheck = cheater.checkKnownDirectionNonadaptiveStrategy({
  coin_count: limitedTwoUsesPreassignedConfig.coin_count,
  max_weighings: limitedTwoUsesPreassignedConfig.max_weighings,
  counterfeit_weight: limitedTwoUsesPreassignedConfig.counterfeit_weight,
  weighings: [
    limitedTwoUsesPreassignedConfig.preset_weighings[0],
    limitedTwoUsesPreassignedConfig.preset_weighings[1],
    limitedTwoUsesPreassignedConfig.preset_weighings[2],
    limitedTwoUsesPreassignedConfig.preset_weighings[3],
    limitedTwoUsesPreassignedConfig.preset_weighings[4],
    limitedTwoUsesPreassignedConfig.preset_weighings[5],
    limitedTwoUsesPreassignedConfig.preset_weighings[5]
  ],
  require_equal_pan_counts: true
});
assert.equal(limitedTwoUsesBadPreassignedCheck.success, false);
assert.equal(limitedTwoUsesBadPreassignedCheck.conflicts.length > 0, true);

const knopKnownLightPreassignedCheck = cheater.checkKnownDirectionNonadaptiveStrategy({
  coin_count: knopKnownLightPreassignedConfig.coin_count,
  max_weighings: knopKnownLightPreassignedConfig.max_weighings,
  counterfeit_weight: knopKnownLightPreassignedConfig.counterfeit_weight,
  weighings: knopKnownLightPreassignedConfig.preset_weighings,
  require_equal_pan_counts: knopKnownLightPreassignedConfig.require_equal_pan_counts
});
assert.equal(knopKnownLightPreassignedCheck.success, true);
assert.equal(knopKnownLightPreassignedCheck.states.length, 27);
assert.equal(knopKnownLightPreassignedCheck.partitions.length, 27);
assert.deepEqual(knopKnownLightPreassignedCheck.conflicts, []);
assert.equal(
  knopKnownLightPreassignedConfig.preset_weighings.every(row => row.left.length === 9 && row.right.length === 9),
  true
);
assert.deepEqual(
  cheater.knownDirectionSignatureForCandidate(
    14,
    'lighter',
    knopKnownLightPreassignedConfig.preset_weighings,
    { coinCount: knopKnownLightPreassignedConfig.coin_count, requireEqualPanCounts: true }
  ),
  ['right_down', 'right_down', 'right_down']
);

const knopOneErasureReserveCheck = cheater.checkKnownDirectionNonadaptiveStrategy({
  coin_count: knopOneErasureReserveConfig.coin_count,
  max_weighings: knopOneErasureReserveConfig.max_weighings,
  counterfeit_weight: knopOneErasureReserveConfig.counterfeit_weight,
  erasure_count: knopOneErasureReserveConfig.erasure_count,
  weighings: knopOneErasureReserveConfig.preset_weighings,
  require_equal_pan_counts: knopOneErasureReserveConfig.require_equal_pan_counts
});
assert.equal(knopOneErasureReserveCheck.success, true);
assert.equal(knopOneErasureReserveCheck.states.length, 9);
assert.equal(knopOneErasureReserveCheck.erasurePatterns.length, 3);
assert.equal(knopOneErasureReserveCheck.partitions.length, 27);
assert.deepEqual(knopOneErasureReserveCheck.conflicts, []);
assert.deepEqual(
  cheater.knownDirectionSignatureForCandidate(
    5,
    'lighter',
    knopOneErasureReserveConfig.preset_weighings,
    { coinCount: knopOneErasureReserveConfig.coin_count, requireEqualPanCounts: true }
  ),
  ['right_down', 'right_down', 'left_down']
);

const knopOneErasureReserveBadCheck = cheater.checkKnownDirectionNonadaptiveStrategy({
  coin_count: knopOneErasureReserveConfig.coin_count,
  max_weighings: knopOneErasureReserveConfig.max_weighings,
  counterfeit_weight: knopOneErasureReserveConfig.counterfeit_weight,
  erasure_count: knopOneErasureReserveConfig.erasure_count,
  weighings: [
    knopOneErasureReserveConfig.preset_weighings[0],
    knopOneErasureReserveConfig.preset_weighings[1],
    knopOneErasureReserveConfig.preset_weighings[1]
  ],
  require_equal_pan_counts: true
});
assert.equal(knopOneErasureReserveBadCheck.success, false);
assert.equal(knopOneErasureReserveBadCheck.conflicts.length > 0, true);

const knopTwoErasureReserveCheck = cheater.checkKnownDirectionNonadaptiveStrategy({
  coin_count: knopTwoErasureReserveConfig.coin_count,
  max_weighings: knopTwoErasureReserveConfig.max_weighings,
  counterfeit_weight: knopTwoErasureReserveConfig.counterfeit_weight,
  erasure_count: knopTwoErasureReserveConfig.erasure_count,
  weighings: knopTwoErasureReserveConfig.preset_weighings,
  require_equal_pan_counts: knopTwoErasureReserveConfig.require_equal_pan_counts
});
assert.equal(knopTwoErasureReserveCheck.success, true);
assert.equal(knopTwoErasureReserveCheck.states.length, 9);
assert.equal(knopTwoErasureReserveCheck.erasurePatterns.length, 6);
assert.equal(knopTwoErasureReserveCheck.partitions.length, 54);
assert.deepEqual(knopTwoErasureReserveCheck.conflicts, []);
assert.deepEqual(
  cheater.knownDirectionSignatureForCandidate(
    8,
    'lighter',
    knopTwoErasureReserveConfig.preset_weighings,
    { coinCount: knopTwoErasureReserveConfig.coin_count, requireEqualPanCounts: true }
  ),
  ['left_down', 'right_down', 'balance', 'right_down']
);

const knopTwoErasureReserveBadCheck = cheater.checkKnownDirectionNonadaptiveStrategy({
  coin_count: knopTwoErasureReserveConfig.coin_count,
  max_weighings: knopTwoErasureReserveConfig.max_weighings,
  counterfeit_weight: knopTwoErasureReserveConfig.counterfeit_weight,
  erasure_count: knopTwoErasureReserveConfig.erasure_count,
  weighings: [
    knopTwoErasureReserveConfig.preset_weighings[0],
    knopTwoErasureReserveConfig.preset_weighings[1],
    knopTwoErasureReserveConfig.preset_weighings[2],
    knopTwoErasureReserveConfig.preset_weighings[2]
  ],
  require_equal_pan_counts: true
});
assert.equal(knopTwoErasureReserveBadCheck.success, false);
assert.equal(knopTwoErasureReserveBadCheck.conflicts.length > 0, true);

const knopSaladinSpareCheck = cheater.checkUnknownDirectionNonadaptiveStrategy({
  coin_count: knopSaladinSpareConfig.coin_count,
  max_weighings: knopSaladinSpareConfig.max_weighings,
  erasure_count: knopSaladinSpareConfig.erasure_count,
  weighings: knopSaladinSpareConfig.preset_weighings,
  objective: knopSaladinSpareConfig.objective,
  require_equal_pan_counts: knopSaladinSpareConfig.require_equal_pan_counts
});
assert.equal(knopSaladinSpareCheck.success, true);
assert.equal(knopSaladinSpareCheck.states.length, 24);
assert.equal(knopSaladinSpareCheck.erasurePatterns.length, 4);
assert.equal(knopSaladinSpareCheck.partitions.length, 96);
assert.deepEqual(knopSaladinSpareCheck.conflicts, []);
assert.deepEqual(
  cheater.unknownDirectionSignatureForCandidate(
    { coin: 10, direction: 'heavier' },
    knopSaladinSpareConfig.preset_weighings,
    { coinCount: knopSaladinSpareConfig.coin_count, requireEqualPanCounts: true }
  ),
  ['left_down', 'left_down', 'balance', 'balance']
);

const knopSaladinSpareBadCheck = cheater.checkUnknownDirectionNonadaptiveStrategy({
  coin_count: knopSaladinSpareConfig.coin_count,
  max_weighings: knopSaladinSpareConfig.max_weighings,
  erasure_count: knopSaladinSpareConfig.erasure_count,
  weighings: [
    knopSaladinSpareConfig.preset_weighings[0],
    knopSaladinSpareConfig.preset_weighings[1],
    knopSaladinSpareConfig.preset_weighings[2],
    knopSaladinSpareConfig.preset_weighings[2]
  ],
  objective: knopSaladinSpareConfig.objective,
  require_equal_pan_counts: true
});
assert.equal(knopSaladinSpareBadCheck.success, false);
assert.equal(knopSaladinSpareBadCheck.conflicts.length > 0, true);

const thirteenPreassignedIdentifyOnlyCheck = cheater.checkUnknownDirectionNonadaptiveStrategy({
  coin_count: thirteenPreassignedIdentifyOnlyConfig.coin_count,
  max_weighings: thirteenPreassignedIdentifyOnlyConfig.max_weighings,
  weighings: thirteenPreassignedIdentifyOnlyConfig.preset_weighings,
  objective: thirteenPreassignedIdentifyOnlyConfig.objective,
  require_equal_pan_counts: thirteenPreassignedIdentifyOnlyConfig.require_equal_pan_counts
});
assert.equal(thirteenPreassignedIdentifyOnlyCheck.success, true);
assert.equal(thirteenPreassignedIdentifyOnlyCheck.coinOnly, true);
assert.equal(thirteenPreassignedIdentifyOnlyCheck.states.length, 26);
assert.equal(thirteenPreassignedIdentifyOnlyCheck.partitions.length, 13);
assert.deepEqual(thirteenPreassignedIdentifyOnlyCheck.conflicts, []);
assert.deepEqual(
  thirteenPreassignedIdentifyOnlyCheck.partitions.find(part => part.key === 'balance|balance|balance').states,
  [
    { coin: 13, direction: 'heavier' },
    { coin: 13, direction: 'lighter' }
  ]
);
assert.equal(
  thirteenPreassignedIdentifyOnlyCheck.partitions.every(part => part.possibleCoins.length === 1),
  true
);

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

assert.deepEqual(
  cheater.unknownDirectionCoinStatuses([
    { coin: 2, direction: 'lighter' },
    { coin: 3, direction: 'heavier' },
    { coin: 3, direction: 'lighter' }
  ], 4),
  {
    1: 'genuine',
    2: 'possible_lighter',
    3: 'possible_lighter_or_heavier',
    4: 'genuine'
  }
);
assert.deepEqual(
  cheater.unknownDirectionCoinStatuses([
    { coin: 7, direction: 'heavier' },
    { coin: 7, direction: 'lighter' }
  ], 8)[7],
  'definite_fake_unknown_direction'
);
assert.equal(
  cheater.unknownDirectionCoinStatuses([{ coin: 5, direction: 'lighter' }], 8)[5],
  'definite_lighter'
);

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
assert.deepEqual(
  cheater.pairedLightCoinStatuses([{ coins: [1, 3, 5] }, { coins: [1, 3, 6] }], pairedPairs),
  {
    1: 'definite_fake',
    2: 'genuine',
    3: 'definite_fake',
    4: 'genuine',
    5: 'possible_fake',
    6: 'possible_fake'
  }
);
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

const pairedMirrorSymmetry = cheater.pairedLightExpandExhaustiveNode({
  pairs: [[1, 2], [3, 4]],
  currentCandidates: cheater.initialPairedLightCandidates([[1, 2], [3, 4]]),
  leftCoins: [1, 3],
  rightCoins: [2, 4],
  usedWeighings: 0,
  maxWeighings: 2
});
assert.deepEqual(pairedMirrorSymmetry.children.map(child => child.candidates.length), [1, 1, 2]);
assert.deepEqual(pairedMirrorSymmetry.children.map(child => child.status), ['solved', 'covered', 'open']);
assert.equal(pairedMirrorSymmetry.children[1].coveredByOutcome, 'left_down');
assert.equal(pairedMirrorSymmetry.children[1].symmetryReason, 'pan_mirror_pair_permutation');

const pairedMirrorNotPairPreserving = cheater.pairedLightExpandExhaustiveNode({
  pairs: [[1, 2], [3, 4]],
  currentCandidates: cheater.initialPairedLightCandidates([[1, 2], [3, 4]]),
  leftCoins: [1],
  rightCoins: [3],
  usedWeighings: 0,
  maxWeighings: 2
});
assert.equal(pairedMirrorNotPairPreserving.children.some(child => child.status === 'covered'), false);

const sixCircleStates = cheater.constrainedLightInitialStates({
  coin_count: moebiusSixCircleConfig.coin_count,
  hidden_states: moebiusSixCircleConfig.hidden_states
});
assert.equal(sixCircleStates.length, 6);
assert.equal(
  cheater.outcomeForConstrainedLightState(sixCircleStates[0], [1], [3], { coinCount: 6 }),
  'right_down'
);
const sixAfterBalance = cheater.constrainedLightFilterStates({
  coin_count: 6,
  hidden_states: moebiusSixCircleConfig.hidden_states,
  currentStates: sixCircleStates,
  leftCoins: [1],
  rightCoins: [3],
  outcome: 'balance'
});
assert.deepEqual(sixAfterBalance.map(state => state.coins), [[4, 5], [5, 6]]);
assert.deepEqual(cheater.commonLightCoins(sixAfterBalance), [5]);
assert.equal(cheater.constrainedLightBranchStatus(sixAfterBalance, 1, 1, 'identify_one_counterfeit_coin'), 'solved');
assert.equal(cheater.constrainedLightFinalizeAnswer({
  coin_count: 6,
  hidden_states: moebiusSixCircleConfig.hidden_states,
  objective: 'identify_one_counterfeit_coin',
  currentStates: sixAfterBalance,
  selectedCoin: 5
}).win, true);

const fiveCircleStates = cheater.constrainedLightInitialStates({
  coin_count: moebiusFiveCircleConfig.coin_count,
  hidden_states: moebiusFiveCircleConfig.hidden_states
});
assert.equal(fiveCircleStates.length, 10);
let fiveCompatible = cheater.constrainedLightFilterStates({
  coin_count: 5,
  hidden_states: moebiusFiveCircleConfig.hidden_states,
  currentStates: fiveCircleStates,
  leftCoins: [1],
  rightCoins: [2],
  outcome: 'left_down'
});
assert.deepEqual(fiveCompatible.map(state => state.coins), [[2], [2, 4], [2, 5]]);
fiveCompatible = cheater.constrainedLightFilterStates({
  coin_count: 5,
  hidden_states: moebiusFiveCircleConfig.hidden_states,
  currentStates: fiveCompatible,
  leftCoins: [4],
  rightCoins: [5],
  outcome: 'balance'
});
assert.deepEqual(cheater.constrainedLightPossibleCounts(fiveCompatible), [1]);
assert.equal(cheater.constrainedLightFinalizeAnswer({
  coin_count: 5,
  hidden_states: moebiusFiveCircleConfig.hidden_states,
  objective: 'identify_counterfeit_count',
  currentStates: fiveCompatible,
  selectedCount: 1
}).win, true);

const gridStates = cheater.constrainedLightInitialStates({
  coin_count: moebiusGridLineConfig.coin_count,
  hidden_states: moebiusGridLineConfig.hidden_states
});
assert.equal(gridStates.length, 6);
let gridCompatible = cheater.constrainedLightFilterStates({
  coin_count: 9,
  hidden_states: moebiusGridLineConfig.hidden_states,
  currentStates: gridStates,
  leftCoins: [1],
  rightCoins: [5],
  outcome: 'right_down'
});
assert.deepEqual(gridCompatible.map(state => state.id), ['R1', 'C1']);
gridCompatible = cheater.constrainedLightFilterStates({
  coin_count: 9,
  hidden_states: moebiusGridLineConfig.hidden_states,
  currentStates: gridCompatible,
  leftCoins: [1],
  rightCoins: [2],
  outcome: 'balance'
});
assert.deepEqual(gridCompatible.map(state => state.id), ['R1']);
assert.equal(cheater.constrainedLightBranchStatus(gridCompatible, 2, 2, 'identify_line_or_all_counterfeits'), 'solved');
assert.equal(cheater.constrainedLightFinalizeAnswer({
  coin_count: 9,
  hidden_states: moebiusGridLineConfig.hidden_states,
  objective: 'identify_line_or_all_counterfeits',
  currentStates: gridCompatible,
  selectedStateKey: 'R1'
}).win, true);

assert.deepEqual(kvantEightCircleHeavyConfig.type, 'constrained_light_counterfeit_sets');
assert.equal(kvantEightCircleHeavyConfig.counterfeit_weight, 'heavier');
const kvantEightCircleStates = cheater.constrainedLightInitialStates({
  coin_count: kvantEightCircleHeavyConfig.coin_count,
  hidden_states: kvantEightCircleHeavyConfig.hidden_states
});
assert.equal(kvantEightCircleStates.length, 8);
assert.equal(
  cheater.outcomeForConstrainedLightState(kvantEightCircleStates[0], [1], [4], {
    coinCount: 8,
    counterfeitWeight: 'heavier'
  }),
  'left_down'
);
let kvantEightCompatible = cheater.constrainedLightFilterStates({
  coin_count: 8,
  hidden_states: kvantEightCircleHeavyConfig.hidden_states,
  currentStates: kvantEightCircleStates,
  leftCoins: [1, 2, 3],
  rightCoins: [5, 6, 7],
  outcome: 'left_down',
  counterfeit_weight: 'heavier'
});
assert.deepEqual(kvantEightCompatible.map(state => state.id), ['H123', 'H234', 'H812']);
kvantEightCompatible = cheater.constrainedLightFilterStates({
  coin_count: 8,
  hidden_states: kvantEightCircleHeavyConfig.hidden_states,
  currentStates: kvantEightCompatible,
  leftCoins: [4],
  rightCoins: [8],
  outcome: 'right_down',
  counterfeit_weight: 'heavier'
});
assert.deepEqual(kvantEightCompatible.map(state => state.id), ['H812']);
assert.equal(cheater.constrainedLightBranchStatus(kvantEightCompatible, 2, 2, 'identify_all_counterfeits'), 'solved');
assert.equal(cheater.constrainedLightFinalizeAnswer({
  coin_count: 8,
  hidden_states: kvantEightCircleHeavyConfig.hidden_states,
  objective: 'identify_all_counterfeits',
  currentStates: kvantEightCompatible,
  selectedStateKey: 'H812'
}).win, true);

assert.deepEqual(tenRowFakesRightConfig.type, 'constrained_light_counterfeit_sets');
assert.equal(tenRowFakesRightConfig.presentation, 'exercise');
assert.equal(tenRowFakesRightConfig.require_equal_pan_counts, false);
const tenRowStates = cheater.constrainedLightInitialStates({
  coin_count: tenRowFakesRightConfig.coin_count,
  hidden_states: tenRowFakesRightConfig.hidden_states
});
assert.equal(tenRowStates.length, 9);
const tenRowFirst = cheater.constrainedLightExpandExhaustiveNode({
  coin_count: 10,
  hidden_states: tenRowFakesRightConfig.hidden_states,
  currentStates: tenRowStates,
  leftCoins: [1, 8],
  rightCoins: [4, 5],
  usedWeighings: 0,
  maxWeighings: 2,
  objective: 'identify_all_counterfeits',
  requireEqualPanCounts: false
});
assert.deepEqual(Object.fromEntries(tenRowFirst.children.map(child => [child.outcome, child.states.map(state => state.id)])), {
  left_down: ['B1', 'B2', 'B3'],
  right_down: ['B5', 'B6', 'B7'],
  balance: ['B4', 'B8', 'B9']
});
const tenRowSecondByOutcome = {
  left_down: { leftCoins: [2, 3], rightCoins: [1, 10], solved: ['B1', 'B2', 'B3'] },
  right_down: { leftCoins: [6, 7], rightCoins: [1, 10], solved: ['B5', 'B6', 'B7'] },
  balance: { leftCoins: [1, 9], rightCoins: [5, 6], solved: ['B4', 'B8', 'B9'] }
};
for (const child of tenRowFirst.children) {
  const second = tenRowSecondByOutcome[child.outcome];
  const expanded = cheater.constrainedLightExpandExhaustiveNode({
    coin_count: 10,
    hidden_states: tenRowFakesRightConfig.hidden_states,
    currentStates: child.states,
    leftCoins: second.leftCoins,
    rightCoins: second.rightCoins,
    usedWeighings: 1,
    maxWeighings: 2,
    objective: 'identify_all_counterfeits',
    requireEqualPanCounts: false
  });
  assert.deepEqual(expanded.children.map(grandchild => grandchild.status), ['solved', 'solved', 'solved']);
  assert.deepEqual(expanded.children.flatMap(grandchild => grandchild.states.map(state => state.id)).sort(), second.solved.sort());
}
assert.equal(cheater.constrainedLightFinalizeAnswer({
  coin_count: 10,
  hidden_states: tenRowFakesRightConfig.hidden_states,
  objective: 'identify_all_counterfeits',
  currentStates: [tenRowStates[0]],
  selectedStateKey: 'B1'
}).win, true);

assert.deepEqual(knopNineCirclePairConfig.type, 'constrained_light_counterfeit_sets');
assert.equal(knopNineCirclePairConfig.presentation, 'exercise');
assert.equal(knopNineCirclePairConfig.counterfeit_weight_model, 'variable_lighter');
const knopNineCirclePairStates = cheater.constrainedLightInitialStates({
  coin_count: knopNineCirclePairConfig.coin_count,
  hidden_states: knopNineCirclePairConfig.hidden_states
});
assert.equal(knopNineCirclePairStates.length, 9);
assert.deepEqual(
  cheater.outcomesForConstrainedLightState(knopNineCirclePairStates[1], [2], [3], {
    coinCount: 9,
    counterfeitWeight: 'lighter',
    counterfeitWeightModel: 'variable_lighter'
  }),
  ['left_down', 'balance', 'right_down']
);
assert.deepEqual(
  cheater.outcomesForConstrainedLightState(knopNineCirclePairStates[1], [2, 3], [5, 6], {
    coinCount: 9,
    counterfeitWeight: 'lighter',
    counterfeitWeightModel: 'variable_lighter'
  }),
  ['right_down']
);
let knopNineCirclePairCompatible = cheater.constrainedLightFilterStates({
  coin_count: 9,
  hidden_states: knopNineCirclePairConfig.hidden_states,
  currentStates: knopNineCirclePairStates,
  leftCoins: [2, 3],
  rightCoins: [5, 6],
  outcome: 'right_down',
  counterfeit_weight: 'lighter',
  counterfeit_weight_model: 'variable_lighter'
});
assert.deepEqual(knopNineCirclePairCompatible.map(state => state.id), ['L12', 'L23', 'L34']);
knopNineCirclePairCompatible = cheater.constrainedLightFilterStates({
  coin_count: 9,
  hidden_states: knopNineCirclePairConfig.hidden_states,
  currentStates: knopNineCirclePairCompatible,
  leftCoins: [1],
  rightCoins: [4],
  outcome: 'balance',
  counterfeit_weight: 'lighter',
  counterfeit_weight_model: 'variable_lighter'
});
assert.deepEqual(knopNineCirclePairCompatible.map(state => state.id), ['L23']);
assert.equal(cheater.constrainedLightBranchStatus(knopNineCirclePairCompatible, 2, 2, 'identify_all_counterfeits'), 'solved');
assert.equal(cheater.constrainedLightFinalizeAnswer({
  coin_count: 9,
  hidden_states: knopNineCirclePairConfig.hidden_states,
  objective: 'identify_all_counterfeits',
  currentStates: knopNineCirclePairCompatible,
  selectedStateKey: 'L23'
}).win, true);

assert.deepEqual(knopPairDifferentWeightsConfig.type, 'constrained_light_counterfeit_sets');
assert.equal(knopPairDifferentWeightsConfig.presentation, 'exercise');
assert.equal(knopPairDifferentWeightsConfig.case, 'D.32_six_coins');
assert.equal(knopPairDifferentWeightsConfig.counterfeit_weight_model, 'distinct_lighter');
const knopPairDifferentStates = cheater.constrainedLightInitialStates({
  coin_count: knopPairDifferentWeightsConfig.coin_count,
  hidden_states: knopPairDifferentWeightsConfig.hidden_states
});
assert.equal(knopPairDifferentStates.length, 15);
assert.deepEqual(
  cheater.outcomesForConstrainedLightState(knopPairDifferentStates[0], [1], [2], {
    coinCount: 6,
    counterfeitWeight: 'lighter',
    counterfeitWeightModel: 'distinct_lighter'
  }),
  ['left_down', 'right_down']
);
assert.deepEqual(
  cheater.outcomesForConstrainedLightState(knopPairDifferentStates[0], [1], [2], {
    coinCount: 6,
    counterfeitWeight: 'lighter',
    counterfeitWeightModel: 'variable_lighter'
  }),
  ['left_down', 'balance', 'right_down']
);
function expandKnopPairDifferent(currentStates, leftCoins, rightCoins, usedWeighings) {
  return cheater.constrainedLightExpandExhaustiveNode({
    coin_count: 6,
    hidden_states: knopPairDifferentWeightsConfig.hidden_states,
    currentStates,
    leftCoins,
    rightCoins,
    usedWeighings,
    maxWeighings: 3,
    objective: 'identify_all_counterfeits',
    counterfeit_weight: 'lighter',
    counterfeit_weight_model: 'distinct_lighter',
    requireEqualPanCounts: true
  });
}
function childByOutcome(node, outcome) {
  return node.children.find(child => child.outcome === outcome);
}
const knopPairFirst = expandKnopPairDifferent(knopPairDifferentStates, [1], [2], 0);
assert.deepEqual(Object.fromEntries(knopPairFirst.children.map(child => [child.outcome, child.states.length])), {
  left_down: 5,
  right_down: 5,
  balance: 6
});
const knopPairBalanceSecond = expandKnopPairDifferent(childByOutcome(knopPairFirst, 'balance').states, [3], [4], 1);
for (const child of knopPairBalanceSecond.children) {
  if (child.status === 'solved') continue;
  const third = expandKnopPairDifferent(child.states, [5], [6], 2);
  assert.equal(third.children.every(grandchild => grandchild.status === 'solved'), true);
}
const knopPairRightSecond = expandKnopPairDifferent(childByOutcome(knopPairFirst, 'right_down').states, [2, 3], [4, 5], 1);
assert.equal(childByOutcome(knopPairRightSecond, 'balance').status, 'solved');
assert.equal(expandKnopPairDifferent(childByOutcome(knopPairRightSecond, 'right_down').states, [2], [3], 2).children.every(child => child.status === 'solved'), true);
assert.equal(expandKnopPairDifferent(childByOutcome(knopPairRightSecond, 'left_down').states, [4], [5], 2).children.every(child => child.status === 'solved'), true);
const knopPairLeftSecond = expandKnopPairDifferent(childByOutcome(knopPairFirst, 'left_down').states, [1, 3], [4, 5], 1);
assert.equal(childByOutcome(knopPairLeftSecond, 'balance').status, 'solved');
assert.equal(expandKnopPairDifferent(childByOutcome(knopPairLeftSecond, 'right_down').states, [1], [3], 2).children.every(child => child.status === 'solved'), true);
assert.equal(expandKnopPairDifferent(childByOutcome(knopPairLeftSecond, 'left_down').states, [4], [5], 2).children.every(child => child.status === 'solved'), true);

assert.deepEqual(knopNineCircleTripleConfig.type, 'constrained_light_counterfeit_sets');
assert.equal(knopNineCircleTripleConfig.presentation, 'exercise');
assert.equal(knopNineCircleTripleConfig.counterfeit_weight, 'lighter');
const knopNineCircleTripleStates = cheater.constrainedLightInitialStates({
  coin_count: knopNineCircleTripleConfig.coin_count,
  hidden_states: knopNineCircleTripleConfig.hidden_states
});
assert.equal(knopNineCircleTripleStates.length, 9);
assert.equal(
  cheater.outcomeForConstrainedLightState(knopNineCircleTripleStates[0], [3], [6], {
    coinCount: 9,
    counterfeitWeight: 'lighter'
  }),
  'right_down'
);
let knopNineCircleCompatible = cheater.constrainedLightFilterStates({
  coin_count: 9,
  hidden_states: knopNineCircleTripleConfig.hidden_states,
  currentStates: knopNineCircleTripleStates,
  leftCoins: [3],
  rightCoins: [6],
  outcome: 'right_down',
  counterfeit_weight: 'lighter'
});
assert.deepEqual(knopNineCircleCompatible.map(state => state.id), ['H123', 'H234', 'H345']);
knopNineCircleCompatible = cheater.constrainedLightFilterStates({
  coin_count: 9,
  hidden_states: knopNineCircleTripleConfig.hidden_states,
  currentStates: knopNineCircleCompatible,
  leftCoins: [1],
  rightCoins: [5],
  outcome: 'balance',
  counterfeit_weight: 'lighter'
});
assert.deepEqual(knopNineCircleCompatible.map(state => state.id), ['H234']);
assert.equal(cheater.constrainedLightBranchStatus(knopNineCircleCompatible, 2, 2, 'identify_all_counterfeits'), 'solved');
assert.equal(cheater.constrainedLightFinalizeAnswer({
  coin_count: 9,
  hidden_states: knopNineCircleTripleConfig.hidden_states,
  objective: 'identify_all_counterfeits',
  currentStates: knopNineCircleCompatible,
  selectedStateKey: 'H234'
}).win, true);

assert.deepEqual(fiveCoinsTwoEqualFakesConfig.type, 'constrained_light_counterfeit_sets');
assert.equal(fiveCoinsTwoEqualFakesConfig.presentation, 'exercise');
assert.equal(fiveCoinsTwoEqualFakesConfig.objective, 'identify_one_genuine_coin');
assert.equal(fiveCoinsTwoEqualFakesConfig.counterfeit_weight_model, 'unknown_equal_sign');
const fiveEqualFakeStates = cheater.constrainedLightInitialStates({
  coin_count: fiveCoinsTwoEqualFakesConfig.coin_count,
  hidden_states: fiveCoinsTwoEqualFakesConfig.hidden_states
});
assert.equal(fiveEqualFakeStates.length, 20);
assert.equal(
  cheater.outcomeForConstrainedLightState(fiveEqualFakeStates.find(state => state.id === '13-light'), [1], [2], {
    coinCount: 5,
    counterfeitWeight: 'lighter'
  }),
  'right_down'
);
assert.equal(
  cheater.outcomeForConstrainedLightState(fiveEqualFakeStates.find(state => state.id === '13-heavy'), [1], [2], {
    coinCount: 5,
    counterfeitWeight: 'lighter'
  }),
  'left_down'
);
const fiveFirst = cheater.constrainedLightExpandExhaustiveNode({
  coin_count: 5,
  hidden_states: fiveCoinsTwoEqualFakesConfig.hidden_states,
  objective: 'identify_one_genuine_coin',
  currentStates: fiveEqualFakeStates,
  leftCoins: [1],
  rightCoins: [2],
  usedWeighings: 0,
  maxWeighings: 2,
  counterfeit_weight: 'lighter'
});
assert.equal(fiveFirst.children.every(child => child.status === 'open'), true);
const fiveSecondLeaves = fiveFirst.children.flatMap(child => cheater.constrainedLightExpandExhaustiveNode({
  coin_count: 5,
  hidden_states: fiveCoinsTwoEqualFakesConfig.hidden_states,
  objective: 'identify_one_genuine_coin',
  currentStates: child.states,
  leftCoins: [3],
  rightCoins: [4],
  usedWeighings: 1,
  maxWeighings: 2,
  counterfeit_weight: 'lighter'
}).children);
assert.equal(fiveSecondLeaves.length > 0, true);
assert.equal(fiveSecondLeaves.every(child => child.status === 'solved'), true);
const fiveBothTiltLeaf = fiveSecondLeaves.find(child =>
  cheater.constrainedLightAnswerOptionsForStates(child.states, 'identify_one_genuine_coin')
    .some(option => option.value === 5)
);
assert.ok(fiveBothTiltLeaf);
assert.equal(cheater.constrainedLightFinalizeAnswer({
  coin_count: 5,
  hidden_states: fiveCoinsTwoEqualFakesConfig.hidden_states,
  objective: 'identify_one_genuine_coin',
  currentStates: fiveBothTiltLeaf.states,
  selectedCoin: 5
}).win, true);

const multipleStates = cheater.initialMultipleLightCandidates(6, 2);
assert.equal(multipleStates.length, 15);
assert.deepEqual(multipleStates[0], { coins: [1, 2] });
assert.deepEqual(multipleStates.at(-1), { coins: [5, 6] });
assert.deepEqual(
  cheater.lightCoinSetStatuses([{ coins: [1, 2] }, { coins: [1, 3] }, { coins: [1, 4] }], 5, { lightCount: 2 }),
  {
    1: 'definite_fake',
    2: 'possible_fake',
    3: 'possible_fake',
    4: 'possible_fake',
    5: 'genuine'
  }
);
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

const israelSevenThreeStates = cheater.initialMultipleLightCandidates(7, 3);
assert.equal(israelSevenThreeStates.length, 35);
const israelSevenThreeFirst = cheater.multipleLightExpandExhaustiveNode({
  coin_count: 7,
  light_count: 3,
  currentCandidates: israelSevenThreeStates,
  leftCoins: [1, 2],
  rightCoins: [3, 4],
  usedWeighings: 0,
  maxWeighings: 2,
  objective: 'identify_one_light_coin'
});
assert.equal(israelSevenThreeFirst.children.length, 3);
assert.deepEqual(israelSevenThreeFirst.children.map(child => child.candidates.length), [11, 11, 13]);
for (const child of israelSevenThreeFirst.children) {
  const second = child.outcome === 'left_down'
    ? { leftCoins: [1], rightCoins: [3] }
    : { leftCoins: [1], rightCoins: [2] };
  const expanded = cheater.multipleLightExpandExhaustiveNode({
    coin_count: 7,
    light_count: 3,
    currentCandidates: child.candidates,
    leftCoins: second.leftCoins,
    rightCoins: second.rightCoins,
    usedWeighings: child.usedWeighings,
    maxWeighings: 2,
    objective: 'identify_one_light_coin'
  });
  assert.equal(expanded.children.every(branch => cheater.commonLightCoins(branch.candidates).length > 0), true);
}
const israelSevenThreeCheaterFirst = cheater.multipleLightChooseCheaterOutcome({
  coin_count: 7,
  light_count: 3,
  currentCandidates: israelSevenThreeStates,
  leftCoins: [1, 2],
  rightCoins: [3, 4],
  history: [],
  objective: 'identify_one_light_coin'
});
assert.equal(israelSevenThreeCheaterFirst.outcome, 'balance');
assert.equal(israelSevenThreeCheaterFirst.candidates.length, 13);

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

const multipleMirrorSymmetry = cheater.multipleLightExpandExhaustiveNode({
  coin_count: 4,
  light_count: 2,
  currentCandidates: cheater.initialMultipleLightCandidates(4, 2),
  leftCoins: [1, 2],
  rightCoins: [3, 4],
  usedWeighings: 0,
  maxWeighings: 2
});
assert.deepEqual(multipleMirrorSymmetry.children.map(child => child.candidates.length), [1, 1, 4]);
assert.deepEqual(multipleMirrorSymmetry.children.map(child => child.status), ['solved', 'covered', 'open']);
assert.equal(multipleMirrorSymmetry.children[1].coveredByOutcome, 'left_down');
assert.equal(multipleMirrorSymmetry.children[1].symmetryReason, 'pan_mirror_coin_permutation');

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

const groupedMirrorSymmetry = cheater.multipleLightExpandExhaustiveNode({
  coin_count: 4,
  light_count: 2,
  groups: [[1, 2], [3, 4]],
  counterfeit_per_group: [1, 1],
  objective: 'identify_all_counterfeits',
  currentCandidates: cheater.initialGroupedMultipleLightCandidates(4, [[1, 2], [3, 4]], [1, 1]),
  leftCoins: [1, 3],
  rightCoins: [2, 4],
  usedWeighings: 0,
  maxWeighings: 2
});
assert.deepEqual(groupedMirrorSymmetry.children.map(child => child.candidates.length), [1, 1, 2]);
assert.deepEqual(groupedMirrorSymmetry.children.map(child => child.status), ['solved', 'covered', 'open']);
assert.equal(groupedMirrorSymmetry.children[1].coveredByOutcome, 'left_down');
assert.equal(groupedMirrorSymmetry.children[1].symmetryReason, 'pan_mirror_group_permutation');

const groupedMirrorNotConstraintPreserving = cheater.multipleLightExpandExhaustiveNode({
  coin_count: 4,
  light_count: 2,
  groups: [[1, 2], [3, 4]],
  counterfeit_per_group: [1, 1],
  objective: 'identify_all_counterfeits',
  currentCandidates: cheater.initialGroupedMultipleLightCandidates(4, [[1, 2], [3, 4]], [1, 1]),
  leftCoins: [1],
  rightCoins: [3],
  usedWeighings: 0,
  maxWeighings: 2
});
assert.equal(groupedMirrorNotConstraintPreserving.children.some(child => child.status === 'covered'), false);

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

const zoltarStates = cheater.zoltarInitialStates(14, 7);
assert.equal(zoltarStates.length, 3432);
const zoltarInitialPartition = cheater.zoltarPartitionStates({
  coin_count: 14,
  real_count: 7,
  currentStates: zoltarStates,
  leftCoins: [1, 2],
  rightCoins: [3, 4]
});
assert.deepEqual(zoltarInitialPartition.map(branch => branch.key), [
  'left_down:1',
  'left_down:2',
  'right_down:3',
  'right_down:4',
  'balance'
]);
assert.equal(zoltarInitialPartition.reduce((sum, branch) => sum + branch.states.length, 0) > zoltarStates.length, true);
const zoltarKnownState = [{ real: [1, 2, 5, 6, 7, 8, 9], removed: [] }];
const zoltarKnownExpansion = cheater.zoltarExpandExhaustiveNode({
  coin_count: 14,
  real_count: 7,
  currentStates: zoltarKnownState,
  leftCoins: [1, 2],
  rightCoins: [3, 4],
  usedWeighings: 0,
  maxWeighings: 2
});
assert.deepEqual(zoltarKnownExpansion.children.map(child => child.key), ['left_down:1', 'left_down:2']);
assert.deepEqual(zoltarKnownExpansion.children.map(child => child.states[0].removed), [[1], [2]]);

const zoltarGuaranteed = [
  { real: [1, 2, 3, 4, 5, 6, 7], removed: [2] },
  { real: [1, 3, 4, 5, 6, 7, 8], removed: [2] }
];
assert.deepEqual(cheater.zoltarGuaranteedRealCoins(zoltarGuaranteed, 14, 7), [1, 3, 4, 5, 6, 7]);
assert.equal(cheater.zoltarFinalizeAnswer({
  coin_count: 14,
  real_count: 7,
  currentStates: zoltarGuaranteed,
  selectedCoin: 1
}).win, true);
assert.equal(cheater.zoltarFinalizeAnswer({
  coin_count: 14,
  real_count: 7,
  currentStates: zoltarGuaranteed,
  selectedCoin: 2
}).win, false);
assert.equal(cheater.zoltarFinalizeAnswer({
  coin_count: 14,
  real_count: 7,
  currentStates: zoltarGuaranteed,
  selectedCoin: 8
}).win, false);

const zoltarCheater = cheater.zoltarChooseCheaterBranch({
  coin_count: 14,
  real_count: 7,
  currentStates: zoltarStates,
  leftCoins: [1],
  rightCoins: [2],
  history: []
});
assert.equal(zoltarCheater.key, 'balance');
assert.equal(zoltarCheater.states.length, Math.max(...Object.values(zoltarCheater.scores).map(score => score.states)));

assert.equal(cheater.zoltarBranchStatus(zoltarGuaranteed, 1, 2, { coinCount: 14, realCount: 7 }), 'solved');
assert.equal(cheater.zoltarBranchStatus(zoltarStates, 25, 25, { coinCount: 14, realCount: 7 }), 'failed');
assert.equal(cheater.zoltarBranchStatus(zoltarStates, 2, 25, { coinCount: 14, realCount: 7 }), 'open');

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

const selectedBagStates = cheater.selectedBagWeightInitialStates(matprazdnikSevenBagsConfig);
assert.deepEqual(selectedBagStates.map(state => state.weight), [7, 8, 9, 10, 11, 12, 13]);
assert.equal(cheater.selectedBagWeightReferenceTotal(matprazdnikSevenBagsConfig), 70);

const selectedBagFirst = {
  ...matprazdnikSevenBagsConfig,
  selectedCoins: 70,
  kitCount: 10
};
const selectedBagFirstPartitions = cheater.selectedBagWeightPartitionStates(selectedBagFirst);
assert.deepEqual(
  Object.fromEntries(selectedBagFirstPartitions.map(part => [part.outcome, part.states.map(state => state.weight)])),
  {
    left_down: [11, 12, 13],
    balance: [10],
    right_down: [7, 8, 9]
  }
);
assert.deepEqual(
  cheater.selectedBagWeightChooseCheaterOutcome(selectedBagFirst).states.map(state => state.weight),
  [11, 12, 13]
);
assert.equal(
  cheater.selectedBagWeightComparison({
    ...matprazdnikSevenBagsConfig,
    selectedCoins: 95,
    kitCount: 10
  }).valid,
  false
);

let selectedBagBranch = selectedBagStates;
for (const step of [
  { selectedCoins: 70, kitCount: 10, hiddenWeight: 12 },
  { selectedCoins: 70, kitCount: 12, hiddenWeight: 12 }
]) {
  const outcome = cheater.selectedBagWeightOutcomeForState({ weight: step.hiddenWeight }, {
    ...matprazdnikSevenBagsConfig,
    selectedCoins: step.selectedCoins,
    kitCount: step.kitCount
  });
  selectedBagBranch = cheater.selectedBagWeightFilterStates({
    ...matprazdnikSevenBagsConfig,
    currentStates: selectedBagBranch,
    selectedCoins: step.selectedCoins,
    kitCount: step.kitCount,
    outcome
  });
}
assert.deepEqual(selectedBagBranch.map(state => state.weight), [12]);
assert.equal(cheater.selectedBagWeightFinalizeAnswer({
  ...matprazdnikSevenBagsConfig,
  currentStates: selectedBagBranch,
  selectedWeight: 12
}).win, true);

let selectedLightBranch = cheater.selectedBagWeightFilterStates({
  ...selectedBagFirst,
  currentStates: selectedBagStates,
  outcome: 'right_down'
});
selectedLightBranch = cheater.selectedBagWeightFilterStates({
  ...matprazdnikSevenBagsConfig,
  currentStates: selectedLightBranch,
  selectedCoins: 70,
  kitCount: 8,
  outcome: cheater.selectedBagWeightOutcomeForState({ weight: 7 }, {
    ...matprazdnikSevenBagsConfig,
    selectedCoins: 70,
    kitCount: 8
  })
});
assert.deepEqual(selectedLightBranch.map(state => state.weight), [7]);

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

const knopSevenSubsetStates = cheater.numericSignatureInitialStates(7, knopSevenBagsSubsetConfig);
assert.equal(knopSevenSubsetStates.length, 128);
assert.equal(knopSevenSubsetStates.some(state => state.mask === 0), true);
assert.equal(knopSevenSubsetStates.some(state => state.mask === 127), true);
const oneFromEachBag = [1, 1, 1, 1, 1, 1, 1];
assert.equal(
  cheater.numericSignatureObservationForState({ bags: [] }, oneFromEachBag, knopSevenBagsSubsetConfig).weight,
  70
);
assert.equal(
  cheater.numericSignatureObservationForState({ mask: 127 }, oneFromEachBag, knopSevenBagsSubsetConfig).weight,
  63
);
const oneEachPartitions = cheater.numericSignaturePartitionStates({
  ...knopSevenBagsSubsetConfig,
  bag_count: 7,
  amounts: oneFromEachBag,
  currentStates: knopSevenSubsetStates
});
assert.equal(oneEachPartitions.length, 8);
assert.equal(oneEachPartitions.some(part => part.states.some(state => state.mask === 0) && part.states.some(state => state.mask === 127)), false);

const apsimonStates = cheater.numericSignatureInitialStates(3, apsimonThreeBagsConfig);
assert.equal(apsimonStates.length, 8);
const apsimonFirst = cheater.numericSignatureExpandExhaustiveNode({
  ...apsimonThreeBagsConfig,
  bag_count: 3,
  amounts: [2, 1, 0],
  currentStates: apsimonStates,
  usedWeighings: 0,
  maxWeighings: 2
});
const apsimonSecondLeaves = [];
for (const child of apsimonFirst.children) {
  const expansion = cheater.numericSignatureExpandExhaustiveNode({
    ...apsimonThreeBagsConfig,
    bag_count: 3,
    amounts: [0, 1, 1],
    currentStates: child.states,
    usedWeighings: 1,
    maxWeighings: 2
  });
  apsimonSecondLeaves.push(...expansion.children);
}
assert.equal(apsimonSecondLeaves.length, 8);
assert.equal(apsimonSecondLeaves.every(child => child.status === 'solved'), true);
assert.equal(
  cheater.numericSignatureSampledCoinCount([[2, 1, 0], [0, 1, 1]], 3),
  4
);
assert.equal(
  cheater.numericSignatureSampledCoinCount([[2, 1, 0], [0, 2, 1]], 3),
  5
);

const mmoFourCoinStates = cheater.numericSignatureInitialStates(4, mmoFourCoinsAllFakesConfig);
assert.equal(mmoFourCoinStates.length, 16);
assert.equal(mmoFourCoinStates.some(state => state.mask === 0), true);
assert.equal(mmoFourCoinStates.some(state => state.mask === 15), true);
const mmoFourCoinPlan = [
  [1, 1, 0, 1],
  [1, 0, 1, 0],
  [0, 1, 1, 0]
];
const mmoFourCoinSignatures = new Map();
for (const state of mmoFourCoinStates) {
  const signature = mmoFourCoinPlan
    .map(amounts => cheater.numericSignatureObservationForState(state, amounts, mmoFourCoinsAllFakesConfig).weight)
    .join('|');
  assert.equal(mmoFourCoinSignatures.has(signature), false, `duplicate MMO four-coin signature ${signature}`);
  mmoFourCoinSignatures.set(signature, state);
}
assert.equal(mmoFourCoinSignatures.size, 16);
let mmoFourCoinFrontier = [{ states: mmoFourCoinStates, usedWeighings: 0, status: 'open' }];
for (const amounts of mmoFourCoinPlan) {
  mmoFourCoinFrontier = mmoFourCoinFrontier.flatMap(node => {
    if (node.status !== 'open') return [node];
    return cheater.numericSignatureExpandExhaustiveNode({
      ...mmoFourCoinsAllFakesConfig,
      bag_count: 4,
      amounts,
      currentStates: node.states,
      usedWeighings: node.usedWeighings,
      maxWeighings: 3
    }).children;
  });
}
assert.equal(mmoFourCoinFrontier.length, 16);
assert.equal(mmoFourCoinFrontier.every(child => child.status === 'solved'), true);
assert.equal(mmoFourCoinFrontier.every(child => child.states.length === 1), true);

assert.deepEqual(problemsRuElevenBagsConfig.type, 'numeric_linear_signature');
assert.equal(problemsRuElevenBagsConfig.objective, 'identify_fake_bag');
assert.equal(problemsRuElevenBagsConfig.observation_model, 'projective_signed_deviation');
assert.equal(problemsRuElevenBagsConfig.selection_model, 'signed_quantities');
const elevenBagStates = cheater.numericSignatureInitialStates(11, problemsRuElevenBagsConfig);
assert.equal(elevenBagStates.length, 11);
const elevenBagPlan = [
  [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -10],
  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, -55]
];
assert.equal(cheater.numericSignatureAmountsValidation(elevenBagPlan[0], 11, problemsRuElevenBagsConfig).valid, true);
assert.equal(cheater.numericSignatureAmountsValidation(elevenBagPlan[1], 11, problemsRuElevenBagsConfig).valid, true);
assert.equal(cheater.numericSignatureAmountsValidation([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 11, problemsRuElevenBagsConfig).valid, false);
assert.equal(cheater.numericSignatureSignedPanSize(elevenBagPlan[0]), 10);
assert.equal(cheater.numericSignatureSignedPanSize(elevenBagPlan[1]), 55);
const elevenBagProjectiveKeys = new Set(elevenBagStates.map(state =>
  cheater.numericSignatureProjectiveKeyForState(state, elevenBagPlan, problemsRuElevenBagsConfig)
));
assert.equal(elevenBagProjectiveKeys.size, 11);
let elevenBagFrontier = [{ states: elevenBagStates, usedWeighings: 0, status: 'open' }];
for (let step = 0; step < elevenBagPlan.length; step += 1) {
  const rows = elevenBagPlan.slice(0, step + 1);
  elevenBagFrontier = elevenBagFrontier.flatMap(node => {
    if (node.status !== 'open') return [node];
    return cheater.numericSignatureExpandExhaustiveNode({
      ...problemsRuElevenBagsConfig,
      bag_count: 11,
      amounts: elevenBagPlan[step],
      amountRows: rows,
      currentStates: node.states,
      usedWeighings: step,
      maxWeighings: 2
    }).children;
  });
}
assert.equal(elevenBagFrontier.length, 11);
assert.equal(elevenBagFrontier.every(child => child.status === 'solved'), true);
const hiddenElevenBag = { bags: [8], delta: -3 };
const observedElevenBag = elevenBagPlan.map(amounts =>
  cheater.numericSignatureObservationForState(hiddenElevenBag, amounts, problemsRuElevenBagsConfig).observedDeviation
);
assert.deepEqual(observedElevenBag, [-3, -24]);
assert.deepEqual(
  cheater.numericSignatureFilterStates({
    ...problemsRuElevenBagsConfig,
    bag_count: 11,
    amountRows: elevenBagPlan,
    observedDeviations: observedElevenBag,
    currentStates: elevenBagStates
  }).map(state => state.bags),
  [[8]]
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

const magicBallGoodTests = [[3, 4], [2, 4], [1, 2, 3]];
const magicBallGoodCheck = cheater.subsetSignatureCheckStrategy({
  object_count: 4,
  max_tests: 3,
  tests: magicBallGoodTests
});
assert.equal(magicBallGoodCheck.success, true);
assert.equal(magicBallGoodCheck.partitions.length, 16);
assert.equal(magicBallGoodCheck.partitions.every(part => part.states.length === 1), true);
assert.deepEqual(
  cheater.subsetSignatureForState({ objects: [1, 2, 3, 4] }, magicBallGoodTests),
  [2, 2, 3]
);

const magicBallMissingFourthCheck = cheater.subsetSignatureCheckStrategy({
  object_count: 4,
  max_tests: 3,
  tests: [[1], [2], [3]]
});
assert.equal(magicBallMissingFourthCheck.success, false);
assert.equal(magicBallMissingFourthCheck.conflicts.some(part => part.states.length === 2), true);

const magicBallRepeatedCheck = cheater.subsetSignatureCheckStrategy({
  object_count: 4,
  max_tests: 3,
  tests: [[1, 2], [1, 2], [1, 2]]
});
assert.equal(magicBallRepeatedCheck.success, false);
assert.equal(Math.max(...magicBallRepeatedCheck.conflicts.map(part => part.states.length)) > 2, true);

const magicBallCheater = cheater.subsetSignatureChooseCheaterOutcome({
  object_count: 4,
  max_tests: 3,
  tests: magicBallRepeatedCheck.tests
});
assert.equal(magicBallCheater.states.length > 1, true);
assert.deepEqual(
  cheater.subsetSignatureFilterStates({
    object_count: 4,
    max_tests: 3,
    tests: magicBallGoodTests,
    signature: [0, 0, 1]
  }).map(state => state.objects),
  [[1]]
);

const balancedSubsetGoodQuestions = [[1, 2, 7, 8], [1, 3, 6, 8], [1, 4, 6, 7]];
const balancedSubsetGoodCheck = cheater.balancedSubsetCheckStrategy({
  object_count: 8,
  max_tests: 3,
  target_sum: 18,
  questions: balancedSubsetGoodQuestions
});
assert.equal(balancedSubsetGoodCheck.success, true);
assert.deepEqual(balancedSubsetGoodCheck.sums, [18, 18, 18]);
assert.equal(balancedSubsetGoodCheck.partitions.length, 8);
assert.deepEqual(
  cheater.balancedSubsetSignatureForState({ number: 7 }, balancedSubsetGoodQuestions),
  [1, 0, 1]
);
assert.deepEqual(
  cheater.balancedSubsetFilterStates({
    object_count: 8,
    max_tests: 3,
    questions: balancedSubsetGoodQuestions,
    signature: [0, 0, 0]
  }).map(state => state.number),
  [5]
);

const balancedSubsetWrongSumCheck = cheater.balancedSubsetCheckStrategy({
  object_count: 8,
  max_tests: 3,
  target_sum: 18,
  questions: [[1, 2], [1, 3, 6, 8], [1, 4, 6, 7]]
});
assert.equal(balancedSubsetWrongSumCheck.success, false);
assert.equal(balancedSubsetWrongSumCheck.validation.errors.some(error => error.includes('нужна 18')), true);

const balancedSubsetCollisionCheck = cheater.balancedSubsetCheckStrategy({
  object_count: 8,
  max_tests: 3,
  target_sum: 18,
  questions: [[1, 2, 7, 8], [1, 2, 7, 8], [1, 2, 7, 8]]
});
assert.equal(balancedSubsetCollisionCheck.success, false);
assert.equal(balancedSubsetCollisionCheck.conflicts.some(part => part.states.length > 1), true);

const fixedBinaryQuestionsGood = [[2, 4, 6, 8], [3, 4, 7, 8], [5, 6, 7, 8]];
const fixedBinaryQuestionPartitions = cheater.balancedSubsetPartitionStates({
  object_count: fixedBinaryQuestionsConfig.object_count,
  max_tests: fixedBinaryQuestionsConfig.max_tests,
  questions: fixedBinaryQuestionsGood
});
assert.equal(fixedBinaryQuestionPartitions.length, 8);
assert.equal(fixedBinaryQuestionPartitions.every(part => part.states.length === 1), true);
assert.deepEqual(
  cheater.balancedSubsetFilterStates({
    object_count: fixedBinaryQuestionsConfig.object_count,
    max_tests: fixedBinaryQuestionsConfig.max_tests,
    questions: fixedBinaryQuestionsGood,
    signature: [1, 1, 1]
  }).map(state => state.number),
  [8]
);

assert.deepEqual(cheater.binaryCardsWeights(binaryCardsConfig), [1, 2, 4, 8, 16]);
assert.deepEqual(
  cheater.binaryCardsCards(binaryCardsConfig).map(card => card.numbers[0]),
  [1, 2, 4, 8, 16]
);
assert.deepEqual(cheater.binaryCardsSelectionForNumber(21, binaryCardsConfig), [1, 4, 16]);
assert.equal(cheater.binaryCardsDecodeSelection([1, 4, 16], binaryCardsConfig), 21);
assert.equal(
  cheater.binaryCardsEvaluate({
    ...binaryCardsConfig,
    number: 31,
    selection: [1, 2, 4, 8, 16]
  }).win,
  true
);
const binaryCardsExhaustive = cheater.binaryCardsExhaustiveCheck(binaryCardsConfig);
assert.equal(binaryCardsExhaustive.success, true);
assert.equal(binaryCardsExhaustive.checked, 31);
assert.equal(binaryCardsExhaustive.collisions.length, 0);

assert.equal(cheater.fixedFeedbackStateCount(passwordFeedbackConfig), 9765625);
assert.equal(cheater.fixedFeedbackExhaustiveCheck(passwordFeedbackConfig).success, true);
assert.equal(cheater.fixedFeedbackPasswordModel(passwordPermutationConfig), 'permutation');
assert.equal(cheater.fixedFeedbackStateCount(passwordPermutationConfig), 24);
const passwordPermutationExhaustive = cheater.fixedFeedbackExhaustiveCheck(passwordPermutationConfig);
assert.equal(passwordPermutationExhaustive.success, true);
assert.equal(passwordPermutationExhaustive.checked, 24);
assert.equal(passwordPermutationExhaustive.rows.length, 3);
assert.equal(cheater.fixedFeedbackCompatibleSecrets([], passwordPermutationConfig).length, 24);
const passwordPermutationHistory = passwordPermutationConfig.preset_tests.map(guess => ({
  guess,
  matches: cheater.fixedFeedbackFeedback('CADB', guess, passwordPermutationConfig)
}));
assert.deepEqual(cheater.fixedFeedbackCompatibleSecrets(passwordPermutationHistory, passwordPermutationConfig), ['CADB']);
assert.equal(cheater.fixedFeedbackKnownPassword(passwordPermutationHistory, passwordPermutationConfig), 'CADB');
assert.equal(cheater.fixedFeedbackFinalizeAnswer({
  ...passwordPermutationConfig,
  secret: 'CADB',
  history: passwordPermutationHistory,
  answer: 'CADB'
}).win, true);
assert.equal(cheater.fixedFeedbackFinalizeAnswer({
  ...passwordPermutationConfig,
  secret: 'CADB',
  history: passwordPermutationHistory,
  answer: 'CAAB'
}).validAnswer, false);

assert.equal(cheater.repetitionCodeQuestionCount(repetitionCodeConfig), 9);
assert.deepEqual(cheater.repetitionCodeAnswersForCase({ ...repetitionCodeConfig, number: 5, lieIndex: -1 }), [true, true, true, false, false, false, true, true, true]);
assert.deepEqual(cheater.repetitionCodeAnswersForCase({ ...repetitionCodeConfig, number: 5, lieIndex: 1 }), [true, false, true, false, false, false, true, true, true]);
const repetitionDecoded = cheater.repetitionCodeEvaluate({ ...repetitionCodeConfig, number: 5, lieIndex: 1 });
assert.equal(repetitionDecoded.decoded, 5);
assert.equal(repetitionDecoded.lieCount, 1);
assert.equal(repetitionDecoded.win, true);
const repetitionExhaustive = cheater.repetitionCodeExhaustiveCheck(repetitionCodeConfig);
assert.equal(repetitionExhaustive.success, true);
assert.equal(repetitionExhaustive.checked, 80);
assert.equal(repetitionExhaustive.failures.length, 0);

const twentyOneExhaustive = cheater.twentyOneCardExhaustive(twentyOneCardConfig);
assert.equal(twentyOneExhaustive.checked, 21);
assert.equal(twentyOneExhaustive.success, true);
assert.equal(twentyOneExhaustive.rows.every(row => row.finalPosition === 11), true);
assert.deepEqual(
  cheater.twentyOneCardTrace({ ...twentyOneCardConfig, selectedCard: 1 }).rounds.map(round => round.actualColumn),
  [0, 1, 0]
);
assert.equal(cheater.twentyOneCardTrace({ ...twentyOneCardConfig, selectedCard: 17 }).finalCard, 17);
const twentyOneManualTrace = cheater.twentyOneCardTrace({
  ...twentyOneCardConfig,
  selectedCard: 9,
  answers: [2, 0, 1]
});
assert.equal(twentyOneManualTrace.success, true);
assert.equal(twentyOneManualTrace.finalCard, 9);
assert.deepEqual(cheater.twentyOneCardCollectionOrder(2, twentyOneCardConfig), [0, 2, 1]);

const finitePairs = cheater.finitePairAllPairs(5);
assert.equal(finitePairs.length, 10);
assert.deepEqual(cheater.finitePairAllowedShownPairs([1, 2], 5), [[3, 4], [3, 5], [4, 5]]);

const validPairProtocol = {
  '1,2': '3,4',
  '3,4': '1,2',
  '1,3': '2,5',
  '2,5': '1,3',
  '1,4': '3,5',
  '3,5': '1,4',
  '1,5': '2,4',
  '2,4': '1,5',
  '2,3': '4,5',
  '4,5': '2,3'
};
const validPairCheck = cheater.finitePairMatchingValidate({
  card_count: 5,
  assignments: validPairProtocol
});
assert.equal(validPairCheck.ok, true);
assert.equal(Object.keys(validPairCheck.decodedByShown).length, 10);

const conflictingPairCheck = cheater.finitePairMatchingValidate({
  card_count: 5,
  assignments: {
    ...validPairProtocol,
    '1,5': '3,4'
  }
});
assert.equal(conflictingPairCheck.ok, false);
assert.equal(conflictingPairCheck.conflicts.length, 1);
assert.deepEqual(conflictingPairCheck.conflicts[0].hiddenKeys.sort(), ['1,2', '1,5']);

const intersectingPairCheck = cheater.finitePairMatchingValidate({
  card_count: 5,
  assignments: {
    ...validPairProtocol,
    '1,2': '2,3'
  }
});
assert.equal(intersectingPairCheck.ok, false);
assert.equal(intersectingPairCheck.errors.some(error => error.includes('пересекается')), true);

const xorAllStates = cheater.xorSingleFlipInitialStates(xorEightCoinsConfig);
assert.equal(xorAllStates.length, 8 * 2 ** 8);
const xorCheck = cheater.xorSingleFlipCheckStrategy(xorEightCoinsConfig);
assert.equal(xorCheck.success, true);
assert.equal(xorCheck.checked, 8 * 2 ** 8);
assert.deepEqual(
  cheater.xorSingleFlipEvaluate({
    ...xorEightCoinsConfig,
    bits: [0, 1, 1, 0, 1, 0, 0, 0],
    key: 6,
    flip: cheater.xorSingleFlipRecommendedFlip([0, 1, 1, 0, 1, 0, 0, 0], 6),
    guess: 6
  }).win,
  true
);

const wiseMenValidation = cheater.wiseMenParityValidateCodebook(wiseMenSixColorsConfig);
assert.equal(wiseMenValidation.ok, true);
assert.equal(wiseMenValidation.codebook.length, 32);
assert.deepEqual(cheater.wiseMenParityCodeword(32, wiseMenSixColorsConfig), [1, 1, 1, 1, 1, 1]);
const wiseMenColors = [1, 2, 7, 12, 25, 32];
const wiseMenMessages = cheater.wiseMenParityMessages(wiseMenColors, wiseMenSixColorsConfig);
assert.deepEqual(wiseMenMessages, [1, 1, 1, 0, 1, 0]);
const wiseMenDecodedThird = cheater.wiseMenParityDecodePerson({
  ...wiseMenSixColorsConfig,
  colors: wiseMenColors,
  messages: wiseMenMessages,
  person: 2
});
assert.equal(wiseMenDecodedThird.win, true);
assert.equal(wiseMenDecodedThird.decodedColor, 7);
assert.deepEqual(wiseMenDecodedThird.bits, cheater.wiseMenParityCodeword(7, wiseMenSixColorsConfig));
const wiseMenEval = cheater.wiseMenParityEvaluate({
  ...wiseMenSixColorsConfig,
  colors: wiseMenColors
});
assert.equal(wiseMenEval.success, true);
assert.deepEqual(wiseMenEval.decoded.map(item => item.decodedColor), wiseMenColors);
const wiseMenFullCheck = cheater.wiseMenParityExhaustiveCheck(wiseMenSixColorsConfig);
assert.equal(wiseMenFullCheck.success, true);
assert.equal(wiseMenFullCheck.checked, 6 * 32);

const wiseMenColorCountValidation = cheater.wiseMenColorCountValidateConfig(wiseMenFourColorCountsConfig);
assert.equal(wiseMenColorCountValidation.ok, true);
const wiseMenColorCountStates = cheater.wiseMenColorCountInitialStates(wiseMenFourColorCountsConfig);
assert.equal(wiseMenColorCountStates.length, 1440);
const wiseMenColorCountEval = cheater.wiseMenColorCountEvaluate({
  ...wiseMenFourColorCountsConfig,
  colors: [2, 3, 3, 4, 4, 4]
});
assert.equal(wiseMenColorCountEval.success, true);
assert.equal(wiseMenColorCountEval.correctCount, 3);
assert.deepEqual(wiseMenColorCountEval.counts, [0, 1, 2, 3]);
assert.deepEqual(wiseMenColorCountEval.rows.map(row => row.options.length), [2, 2, 2, 2, 2, 2]);
const wiseMenColorCountOddEval = cheater.wiseMenColorCountEvaluate({
  ...wiseMenFourColorCountsConfig,
  colors: [1, 3, 3, 4, 4, 4]
});
assert.equal(wiseMenColorCountOddEval.success, true);
assert.equal(wiseMenColorCountOddEval.correctCount, 3);
assert.equal(wiseMenColorCountOddEval.parity, 1);
const wiseMenColorCountFullCheck = cheater.wiseMenColorCountExhaustiveCheck(wiseMenFourColorCountsConfig);
assert.equal(wiseMenColorCountFullCheck.success, true);
assert.equal(wiseMenColorCountFullCheck.checked, 1440);
assert.equal(wiseMenColorCountFullCheck.minCorrect, 3);
assert.equal(wiseMenColorCountFullCheck.maxCorrect, 3);

const prisonerHatStates = cheater.prisonerHatsParityInitialStates(prisonersHatsLineConfig);
assert.equal(prisonerHatStates.length, 64);
const prisonerHatState = cheater.prisonerHatsParityNormalizeState(
  { hats: [1, 0, 0, 0, 0, 0] },
  prisonersHatsLineConfig
);
const prisonerHatTranscript = cheater.prisonerHatsParityProtocolTranscript(prisonerHatState, prisonersHatsLineConfig);
assert.deepEqual(prisonerHatTranscript, [0, 0, 0, 0, 0, 0]);
const prisonerHatEvaluation = cheater.prisonerHatsParityEvaluateTranscript({
  ...prisonersHatsLineConfig,
  state: prisonerHatState,
  answers: prisonerHatTranscript
});
assert.equal(prisonerHatEvaluation.success, true);
assert.equal(prisonerHatEvaluation.rows[0].correctHat, false);
assert.equal(prisonerHatEvaluation.rows.slice(1).every(row => row.correctHat), true);
assert.equal(prisonerHatEvaluation.correctCount, 5);
const prisonerHatFullCheck = cheater.prisonerHatsParityExhaustiveCheck(prisonersHatsLineConfig);
assert.equal(prisonerHatFullCheck.success, true);
assert.equal(prisonerHatFullCheck.checked, 64);
assert.equal(prisonerHatFullCheck.minCorrect, 5);
assert.equal(prisonerHatFullCheck.maxCorrect, 6);
assert.equal(prisonerHatFullCheck.firstCorrectCount, 32);

const hiddenHatStates = cheater.hiddenHatParityInitialStates(wiseMenSixHiddenHatConfig);
assert.equal(hiddenHatStates.length, 5040);
const hiddenHatState = cheater.hiddenHatParityNormalizeState(
  { hidden: 7, hats: [1, 2, 3, 4, 5, 6] },
  wiseMenSixHiddenHatConfig
);
const hiddenHatTranscript = cheater.hiddenHatParityProtocolTranscript(hiddenHatState, wiseMenSixHiddenHatConfig);
assert.equal(hiddenHatTranscript.length, 6);
assert.equal(new Set(hiddenHatTranscript).size, 6);
const hiddenHatEvaluation = cheater.hiddenHatParityEvaluateTranscript({
  ...wiseMenSixHiddenHatConfig,
  state: hiddenHatState,
  answers: hiddenHatTranscript
});
assert.equal(hiddenHatEvaluation.success, true);
assert.equal(hiddenHatEvaluation.rows.slice(1).every(row => row.correctHat), true);
const hiddenHatFullCheck = cheater.hiddenHatParityExhaustiveCheck(wiseMenSixHiddenHatConfig);
assert.equal(hiddenHatFullCheck.success, true);
assert.equal(hiddenHatFullCheck.checked, 5040);
assert.equal(hiddenHatFullCheck.minCorrect, 5);
assert.equal(hiddenHatFullCheck.maxCorrect, 6);

const tenBoxSuccessPermutation = [2, 3, 4, 5, 1, 7, 8, 9, 10, 6];
const tenBoxSuccess = cheater.permutationCycleRunAll(tenBoxSuccessPermutation, 5);
assert.equal(tenBoxSuccess.success, true);
assert.deepEqual(tenBoxSuccess.cycles.map(cycle => cycle.length), [5, 5]);
assert.deepEqual(
  cheater.permutationCycleTrace(tenBoxSuccessPermutation, 3, 5).openings.map(item => [item.box, item.value]),
  [[3, 4], [4, 5], [5, 1], [1, 2], [2, 3]]
);

const tenBoxFailurePermutation = cheater.permutationCycleCheaterPermutation(10, 5);
const tenBoxFailure = cheater.permutationCycleRunAll(tenBoxFailurePermutation, 5);
assert.equal(tenBoxFailure.success, false);
assert.equal(tenBoxFailure.maxCycleLength, 6);
assert.deepEqual(tenBoxFailure.failingPrisoners, [1, 2, 3, 4, 5, 6]);

const tenBoxCycleStats = cheater.permutationCycleTypeStatistics(10, 5);
assert.equal(tenBoxCycleStats.total, 3628800);
assert.equal(tenBoxCycleStats.rows.length, 42);
assert.equal(tenBoxCycleStats.successCount, 1285920);
assert.equal(Math.round(tenBoxCycleStats.probability * 1000000), 354365);

const fitchDeck = cheater.fitchCheneyDeck(fitchCheneyConfig);
assert.equal(fitchDeck.length, 52);
const fitchHand = ['C0', 'C5', 'D2', 'H8', 'S12'];
const fitchMove = cheater.fitchCheneyChooseAssistantMove(fitchHand, fitchCheneyConfig);
assert.equal(fitchMove.ok, true);
assert.deepEqual(fitchMove.hand.map(card => card.id), fitchHand);
assert.equal(fitchMove.hiddenCard.id, 'C5');
assert.deepEqual(fitchMove.shownCards.map(card => card.id), ['C0', 'S12', 'D2', 'H8']);
const fitchDecoded = cheater.fitchCheneyDecodeShown(fitchMove.shownCards, fitchCheneyConfig);
assert.equal(fitchDecoded.ok, true);
assert.equal(fitchDecoded.hiddenCard.id, fitchMove.hiddenCard.id);
assert.equal(
  cheater.fitchCheneyEvaluate({
    ...fitchCheneyConfig,
    hand: fitchHand,
    hiddenCard: fitchMove.hiddenCard.id,
    shownCards: fitchMove.shownCards.map(card => card.id)
  }).win,
  true
);
assert.equal(
  cheater.fitchCheneyEvaluate({
    ...fitchCheneyConfig,
    hand: fitchHand,
    hiddenCard: fitchMove.hiddenCard.id,
    shownCards: ['C0', 'D2', 'H8', 'S12']
  }).win,
  false
);
const fitchExhaustive = cheater.fitchCheneyExhaustiveCheck(fitchCheneyConfig);
assert.equal(fitchExhaustive.ok, true);
assert.equal(fitchExhaustive.checked, 2598960);

const threeLetterErasureConfig = {
  message_count: 16,
  word_length: 8,
  alphabet: ['А', 'Б', 'В'],
  codewords: [
    'АББАВВАБ',
    'АБВБВВВА',
    'АВААВББВ',
    'АВАВВБВБ',
    'АВБББВАВ',
    'АВББВВАБ',
    'АВВББАББ',
    'ББВААВАВ',
    'БВААВББВ',
    'БВВААВБВ',
    'ВААБАББВ',
    'ВАБАВВБА',
    'ВАВВАБББ',
    'ВБААВААБ',
    'ВБВБВААВ',
    'ВВБАБААА'
  ]
};
const threeLetterCheck = cheater.threeLetterErasureCheckTable(threeLetterErasureConfig);
assert.equal(threeLetterCheck.success, true);
assert.equal(threeLetterCheck.checked, 48);
assert.equal(threeLetterCheck.conflicts.length, 0);
for (let message = 0; message < threeLetterErasureConfig.message_count; message += 1) {
  for (const erased of threeLetterErasureConfig.alphabet) {
    const result = cheater.threeLetterErasureEvaluate({
      ...threeLetterErasureConfig,
      message,
      erased,
      guess: message
    });
    assert.equal(result.win, true);
    assert.deepEqual(result.candidates, [message]);
  }
}
const threeLetterBadCheck = cheater.threeLetterErasureCheckTable({
  ...threeLetterErasureConfig,
  codewords: Array.from({ length: 16 }, () => 'АБАБАБАБ')
});
assert.equal(threeLetterBadCheck.success, false);
assert.equal(threeLetterBadCheck.conflicts.length > 0, true);

const permutationMessageLabels = cheater.permutationMessageLabels(permutationMessageConfig);
assert.deepEqual(permutationMessageLabels, ['A', 'B', 'C']);
const permutationMessageTable = cheater.permutationMessageTable(permutationMessageConfig);
assert.equal(permutationMessageTable.length, 6);
assert.deepEqual(permutationMessageTable.map(row => row.labels.join('')), ['ABC', 'ACB', 'BAC', 'BCA', 'CAB', 'CBA']);
for (const row of permutationMessageTable) {
  assert.deepEqual(cheater.permutationMessageEncode(row.message, permutationMessageConfig).order, row.order);
  assert.equal(cheater.permutationMessageDecode(row.order, permutationMessageConfig).message, row.message);
  assert.equal(
    cheater.permutationMessageEvaluate({
      ...permutationMessageConfig,
      direction: 'encode',
      message: row.message,
      order: row.order
    }).win,
    true
  );
  assert.equal(
    cheater.permutationMessageEvaluate({
      ...permutationMessageConfig,
      direction: 'decode',
      order: row.order,
      guess: row.message
    }).win,
    true
  );
}
const permutationMessageExhaustive = cheater.permutationMessageExhaustiveCheck(permutationMessageConfig);
assert.equal(permutationMessageExhaustive.success, true);
assert.equal(permutationMessageExhaustive.checked, 6);
assert.equal(permutationMessageExhaustive.failures.length, 0);
assert.equal(cheater.permutationMessageDecode(['A', 'A', 'B'], permutationMessageConfig).message, null);

console.log('weighing_cheater_selftest: ok');
