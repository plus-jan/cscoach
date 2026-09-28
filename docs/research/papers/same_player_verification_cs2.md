---
id: same_player_verification_cs2
title: 'Account Consistency from Gameplay Traces: Same-Player Verification in Counter-Strike
  2'
authors: Xuchen Zhang
year: 2026
venue: arXiv preprint (v2)
url: https://arxiv.org/abs/2608.24893
arxiv_version: 2608.24893v2
license: arXiv — not verified for redistribution
pdf_sha256: a9196750be3498bb
converted: '2026-09-28'
converter: pymupdf4llm
previous_version: 2608.24893v1 (replaced)
---

# Account Consistency from Gameplay Traces: Same-Player Verification in Counter-Strike 2

> Auto-converted from PDF. Tables, equations and figure text may be garbled — check the original PDF before quoting numbers.

<!-- cscoach-notes:start -->
## cscoach notes (hand-written — preserved on re-conversion)

**Author:** Xuchen Zhang (independent researcher). arXiv 2608.24893 **v2** (v1 was titled *Same-Player
Verification for Account Consistency in Counter-Strike 2*). This file contains the **v2 full text**; the v1
numbers are listed below for traceability. The raw demos and identity ledgers are not released; the
authors mention consent to release de-identified derived features.

- **Relevance:** high for **feature engineering** (xK mechanics, execution vs. decision) and as a
  **data-ethics warning** for CSDS. Low for tier modelling (it does not model rank).
- **Verified claims (v2):**
  - Two datasets:
    - Perfect (DPER): 3,570 demos, 35,700 demo-player observations; a university guild on Perfect World
      Arena; 12 amateur tiers from C to Diamond S+; manually confirmed identities.
    - Professional (DPRO): 539 HLTV demos, 5,390 observations, 130 pro players.
  - A stricter split: 6 folds with a person-first / demo-ownership ledger. Natural person, SteamID,
    alias, observation, demo and content overlap between train and test are all zero (§4.1).
  - Headline mean ROC AUC **0.926 (DPER)** and **0.956 (DPRO)**. Player-cluster bootstrap 95% CIs:
    [0.915, 0.950] and [0.948, 0.965] (§5.1). Excluding same-demo negatives: 0.920 / 0.944.
  - Representation ladder (Table 3):
    - outcome-only stats: 0.572 / 0.712;
    - behavioural features: 0.855 / 0.874;
    - adding explicit pairwise comparison features: **0.926 / 0.956**;
    - the sequence embedding adds little (+0.004 / +0.000).
  - Model family (Table 4): LightGBM ≥ XGBoost (−0.008 / −0.005) ≫ FastMLP (−0.067 / −0.073).
  - Features (Table 1 and §3; 252 per player-demo):
    - speed drop in the 250 ms before each shot;
    - crosshair correction switches around firing;
    - reloads per 100 shots;
    - seconds to first shot;
    - force-buy rate;
    - deaths in the first 20 s.
    Removing the aim/crosshair family costs −0.087 / −0.076 AUC (Table 5).
  - History aggregation (mean LLR): DPER AUC 0.923 (K=1) → **0.982 (K=10)**; DPRO 0.914 → 0.975 (K=5).
    It degrades as history gets contaminated.
  - Time gap: AUC 0.985 same-day → 0.885 at 31–90 days (DPER). Behaviour drifts over weeks.
  - **Cross-domain training (Table 9):** Pro-only training on the pro test reaches 0.955. Mixing in
    amateur data *lowers* it to 0.948; amateur-only reaches 0.912. On the amateur test, adding pro data
    gives +0.003. Domain-matched training matters.
  - External zero-shot test on 5E (weak SteamID labels): AUC 0.966.
- **v1 → v2 changes:** v1 reported mean AUC 0.931 on 1,330 demos / 13,300 observations (0.955 on one
  split), K=10 → 0.986, and a person-disjoint but not match-disjoint split. v2 enlarges the data,
  tightens the split and adds CIs. Cite **v2** numbers.
- **Corrections vs. synthesis:** "ROC AUC 0.955" is neither the v1 nor the v2 headline. The paper
  **does not** test correlation with rank; it verifies identity. "Perfect World Arena Consistency
  Dataset" is **not a public dataset**.
- **Use in project:**
  - xK/mechanics features derivable from CSDS (`player_inputs`, `player_vector.speed_2d`/`ang_vel`/
    `inaccuracy`/`recoil_index`, `weapon_fire`, `player_status.money`) → docs/specs/03#xk, M4.2, A-20.
  - Tree models on engineered features beat neural models at this scale → default GBDT (A-29).
  - Evidence that domain/skill-matched training matters (Table 9) → indirect support for A-01 / ADR-0002.
  - **Ethics/DSA (ADR-0005): these fingerprints can re-link players across matches. Doing that on CSDS
    would defeat its per-match anonymisation and is forbidden. Never build cross-match identity linking
    from behavioural features.**
- **Caveats:** the pairwise evaluation distribution is sampled (1:9 negatives), so precision-type
  metrics depend on that ratio. Label noise comes from undisclosed account sharing.
<!-- cscoach-notes:end -->

## Full text

# **Account Consistency from Gameplay Traces: Same-Player Verification in Counter-Strike 2** 

Xuchen Zhang Independent Researcher China 

tigerlovezj@outlook.com 

## **Abstract** 

In competitive first-person shooter (FPS) games such as CounterStrike 2 (CS2), account-integrity review often asks whether an account’s recent behavior remains consistent with its historical operator. This consistency question arises in cases such as temporary substitution, rank boosting, and high-skill players using lower-ranked accounts, where manual review requires comparing a current match against multiple historical matches. We formulate this review task as same-player verification: we encode the behavioral trajectory of a single player in a match replay (demo) as a demo-player behavioral fingerprint, and train a model to judge whether two behavioral observations come from the same real player. Using CS2-specific domain knowledge, the fingerprints cover crosshair control, movement-stop-fire coordination, economy/buy, combat/engagement, and temporal rhythm. We construct strict six-fold evaluations on the Perfect dataset (DPER; 3,570 demos and 35,700 demo-player observations) and the Professional dataset (DPRO; 539 demos and 5,390 demo-player observations). The final pairwise model reaches ROC AUCs of 0.926 and 0.956, respectively. Feature analysis shows that the strongest identity signals come from aiming/crosshair and other low-level mechanical behaviors, indicating that stable mechanics are more informative for this verification task than single-match performance outcomes. On fixed eligible query cohorts, aggregating pairwise evidence between a current demo and multiple historical demos raises account-history AUC on Perfect from 0.923 at _𝐾_ = 1 to 0.982 at _𝐾_ = 10, and on Professional from 0.914 at _𝐾_ = 1 to 0.975 at _𝐾_ = 5. These results show that CS2 demo behavior can support supervised same-player verification and account-level identity-consistency modeling through multi-demo history aggregation. 

## **Keywords** 

same-player verification, account consistency, behavioral biometrics, game telemetry, Counter-Strike 2 

## **1 Introduction** 

## **1.1 Problem Background** 

Counter-Strike 2 is one of the most active competitive FPS games [1, 2]. 

Beyond anti-cheat, operator consistency within an account history is a distinct fairness concern in competitive FPS platforms. Account sharing, rank boosting, temporary player substitution, and high-skill players using another person’s lower-ranked account can make current operator behavior inconsistent with the account’s historical behavior, undermining matchmaking fairness, player trust, and tournament credibility. To handle such cases, platforms and tournament organizers also need to judge whether the operator’s 

behavior in the current match is still consistent with the account’s past behavioral patterns. 

Existing platform mechanisms address admission, reporting, and case review, while account-history consistency requires a different comparison: current behavior against multiple historical matches. Identity verification suits account admission, tournament registration, or high-risk checkpoints, but is hard to trigger frequently across everyday matches; player reports are low-cost but noisy; and manual demo review can inspect single-match segments but cannot systematically compare the current match against multiple historical matches in shooting habits, mechanical habits, economy decisions, and round rhythm. As a result, existing workflows struggle to turn account-history consistency review into a routine workflow. 

CS2 demos provide structured telemetry for modeling finegrained player operations and decisions across rounds. Viewed more generally, this is a longitudinal user-activity modeling problem over structured platform telemetry, with open-set consistency verification as its target. This paper uses these structured behavioral trajectories to build demo-player behavioral fingerprints and judge the consistency of player behavior across matches. 

## **1.2 Task and Approach Overview** 

We model account-history consistency review as open-set sameplayer verification. Here, open-set means that test-time players need not appear in training; the model does not identify who the current operator is, but learns a reusable comparison function that judges whether two segments of demo-player behavior come from the same real player. In account-history review, this function evaluates behavioral consistency between the current match and historical matches and forms account-level identity-consistency evidence. 

We model operation and decision patterns at a lower level than K/D (kill/death ratio), ADR (average damage per round), headshot rate, or rank, such as crosshair micro-adjustment, firing rhythm, movement-stop-fire coordination, and buying preference. Buying preference can be adjusted intentionally, while low-level operations and action-timing coordination such as crosshair control, firing rhythm, and movement-stop-fire coordination are less directly controllable and may be harder to imitate consistently across rounds. 

The per-demo-player fingerprint has two parts: aggregate behavioral fingerprint features constructed from game understanding, characterizing stable behaviors such as crosshair, movement, economy, combat, and timing; and Transformer-derived sequence embeddings used as complementary behavioral representations for action order, state switching, and low-level mechanics from round events and combat windows. The pairwise model uses both 

Xuchen Zhang 

representations, and account-history review aggregates current-vshistory scores into an account-level consistency signal. 

## **1.3 Contributions** 

This paper makes the following contributions: 

- **A supervised formulation for FPS account-history consistency.** We formulate account-history consistency review as a same-player verification task that a model can learn. 

- **Behavioral findings from CS2 fingerprints.** We find that player identity signals come mainly from aiming/crosshair and other low-level mechanical behaviors; sequence modeling captures complementary action-order information, with dataset-dependent gains. 

- **Verification and aggregation under person-disjoint evaluation.** We evaluate the formulation across persondisjoint splits and account-history aggregation settings, extending single-pair verification to multi-demo accounthistory consistency modeling. 

histories, focus on stable CS2 habits such as crosshair control, firing rhythm, movement-stop-fire coordination, state switching, buying rhythm, and risk preference, and evaluate with unseen-player splits plus current-vs-history aggregation. This moves the target from fixed-identity recognition to account-history consistency. 

Another related direction studies FPS fair-play risk and skill/rating discrepancy. GUARD uses mouse/keyboard dynamics, in-game actions, and expert knowledge to infer a player’s skill group, then compares it with the account rating to identify smurfing / rank-boosting risk [9]. FPS security research also detects passive aimbots through inconsistency between shooting performance and broader skillfulness [10]. These methods can flag cases where operator ability clearly mismatches account rank, or where shooting performance is inconsistent with broader skillfulness. Account borrowing, temporary substitution, or short-term boosting can also happen without an obvious ability jump. We therefore evaluate behavioral consistency between the current demo and accounthistory demos, directly comparing whether behavior before and after still follows the same player’s operational habits. 

## **2 Related Work** 

## **2.1 Account Identity Verification and Fairness Mechanisms on Competitive Platforms** 

Competitive platforms have already incorporated account integrity into fairness governance. Both operator inconsistency behind an account and one person using multiple accounts to bypass platform rules can undermine matchmaking fairness and tournament credibility. Existing esports research discusses boosting—“finding a stronger player to play on an account to improve its rank or results”—and the fairness risk from inconsistency between an account’s displayed skill and the real operator’s ability [3]; broader research on online-game cheating shows that platform governance often needs to combine multiple signals such as accounts, behavior, and social relations [4]. 

Mainstream platforms combine anti-cheat, identity verification, reporting, and manual review to manage account-integrity risks [5, 6]. These mechanisms support admission control, user reports, and case review, but they do not directly provide a systematic comparison between current behavior and multiple historical matches. This paper formalizes that longitudinal current-vs-history comparison as CS2 demo-based same-player verification. 

## **2.2 Counter-Strike and FPS Player Behavioral Identity Modeling** 

The closest game-domain work studies Counter-Strike / CS2 player identity and fair-play. Existing work uses behavioral features to identify known professional players or distinguish known player pairs [7], and related CoG work studies in-game behavioral biometrics for fair play [8]. These studies show that CS/CS2 demo telemetry contains identity-related signals, especially in aiming, shooting, movement state, and game context. 

Our setting is different: platform review often asks whether a current demo remains consistent with an account’s historical demos when the current operator may be unknown or unseen during training. We therefore use manually confirmed same-player 

## **2.3 Broader Game Behavior and Behavioral Biometrics** 

Beyond FPS games, replay and telemetry have also been used for player identity and style modeling. Dota 2 work takes whether two matches were completed by the same player as the target and models it with mouse, game statistics, and strategy information [11]. RTS (real-time strategy) replay identification shows that build order, unit control, resource management, and operation rhythm can identify player style or identity [12]. 

Behavioral biometrics research shows that identity signals can come from how a person acts—mouse trajectories, touchscreen habits, interaction rhythms, and motion patterns [13, 14]; VR head/hand motion, mouse dynamics in simple cognitive games, and active-user identification under shared accounts report similar findings [15–17]. These studies provide background evidence that behavioral telemetry can carry identity signal, but their settings differ from natural CS2 account-history review. This paper focuses on the CS2 account-history consistency setting, where identity evidence comes from FPS-specific motor, timing, and tactical behavior. 

## **2.4 Positioning of This Paper** 

The above lines of work are complementary to this paper. Platform mechanisms provide admission control, reporting, and manual review entry points; Counter-Strike / FPS behavior studies show that in-game behavior contains identity signal; broader behavioral biometrics shows that identity evidence can emerge from how people act. We instantiate these ideas in CS2 account-history consistency review: using manually confirmed account histories to construct pairwise labels, learning same-player verification for unseen players, and identifying crosshair control, movement-stop-fire coordination, and combat micro-operations as the behavioral signals that most strongly support this judgment. 

Account Consistency from Gameplay Traces: Same-Player Verification in Counter-Strike 2 

## **3 Method** 

## **3.1 Problem Definition** 

We call a parsable behavioral record left by one player in one CS2 match demo a **demo-player observation** ; a standard CS2 match demo usually contains 10 players and therefore produces 10 demoplayer observations. A demo records structured replay / telemetry from the game engine, including positions, view angles, weapons, events, and round states. 

We decompose the account-history consistency problem into two levels. 

**Pairwise verification primitive.** The input is a pair of demoplayer observations, where each observation represents the behavioral trajectory left by one player in one CS2 match demo. The verification model outputs an identity-consistency score, where higher scores indicate stronger evidence that the two observations come from the same real player. 

**Account-history aggregation.** Given a current observation under review and _𝐾_ historical observations from the account, we compute _𝐾_ pairwise scores and aggregate them into an accountlevel consistency signal. 

Formally, let _𝑥𝑖_<sup>beh</sup> denote the game-understanding-based aggregate behavioral fingerprint of the _𝑖_ -th demo-player observation, whose construction is described in Section 3.2; let _𝑥𝑖_<sup>seq</sup> denote the combat-window sequence representation produced by the sequence encoder in Section 3.3. We take their concatenation 

as the complete behavioral fingerprint. Let _𝑝𝑖_ denote the realplayer label to which this observation belongs. Player labels are used only to construct training and evaluation samples; at test time, the model does not need to identify who _𝑝𝑖_ is. For any pair of observations, we define the pair label: 

where _𝑦𝑖𝑗_ = 1 denotes a same-player pair and _𝑦𝑖𝑗_ = 0 denotes a different-player pair. The model receives the endpoint fingerprints, the explicit comparison features compare( _𝑥𝑖,𝑥 𝑗_ ) defined in Section 3.4, and the pair-level context _𝑐𝑖𝑗_ , and outputs a consistency score: 

where _𝑔𝜃_ is the pairwise comparator to be learned and _𝜃_ denotes model parameters; _𝑠𝑖𝑗_ is the identity-consistency score. During training, _𝑦𝑖𝑗_ supervises _𝑔𝜃_ . A higher score indicates stronger sameplayer consistency, and different-player retrieval uses the low-score side. 

In this paper, _𝑐𝑖𝑗_ only encodes map relation, such as same-map versus cross-map; it does not include demo IDs, match IDs, teammate/opponent identities, or other shared match identifiers. 

## **3.2 Game-Understanding-Based Behavioral Fingerprint Features** 

This section describes the construction of _𝑥𝑖_<sup>beh</sup> : from each demoplayer observation we extract behavioral fingerprints based on CS2 game understanding to summarize the player’s operation and decision habits in one match. 

From the demo record we recover the player’s within-round position, view angle, movement state, weapon state, firing, damage, utility, and buy events, and express these behaviors at demoplayer granularity as _𝑥𝑖_<sup>beh</sup> : a summary of behavioral frequency, time intervals, distribution shapes, and conditional relations that characterizes how a player moves, aims, fires, switches states, buys equipment, and uses utility across maps and round phases. In implementation, we extract 245 per-demo-player behavioral fingerprint features and organize them into eight sub-representations: 

Taking mechanics/state as an example, this feature type records not “how many duels were won” but how the player’s body state changes before firing. In CS2, stable shooting usually requires counter-strafing; some players fire only after completely stopping, while others fire early while moving. Aggregating such microtransition habits over the full demo-player observation expresses a player’s long-term mechanical style. 

## **3.3 Sequential Behavioral Representation** 

The behavioral fingerprint features in Section 3.2 efficiently summarize behavioral distributions that repeatedly appear in one match. However, similar firing counts, movement speeds, or utility counts can come from completely different round developments. For example, around the same combat, counter-strafing first and then microadjusting and firing, versus firing early while moving and then counter-strafing and micro-adjusting, reflect different movementstop-fire coordination but may look almost identical in the features above; likewise, after throwing a utility item, immediately pushing, waiting for a teammate to trade, or only delaying tempo represent different utility-combat coordination. 

We therefore encode action sequences, but not all ticks of the entire demo. A CS2 demo contains many rounds, and large portions of a demo may contain weak identity signal; player identity is more concentrated in short operations around firing, taking damage, dealing damage, kills, and the moments before death. We thus extract local windows centered on combat events from each demo-player observation: around firing, dealing/taking damage, kills, and death events, we crop fixed-length tick sequences, with death-related evidence concentrated before the event. Each window is a 32 × 16 continuous numerical tensor whose channels are relative time, yaw/pitch velocities, yaw/pitch deltas, speed, horizontal velocity in two axes, displacement, tick interval, health, duck amount, walking and scoped indicators, shots fired, and a center-band indicator. The final sequence encoder retains valid tokens with shots_fired _>_ 0; if an otherwise available observation has no selected firing token, it falls back to the base valid-token mask. 

Let _𝑤𝑖𝑚_ denote the _𝑚_ -th combat window in observation _𝑖_ . The sequence encoder _𝐸𝜓_ maps each window to a window embedding _ℎ𝑖𝑚_ , and an aggregation function aggregate _𝜔_ summarizes them into a demo-player-level sequence embedding: 

Xuchen Zhang 

**Table 1: Game-understanding-based behavioral fingerprint feature families and quantification examples.** 

|behavioral layer|symbol|feature family|behavior captured|concrete quantification example|
|---|---|---|---|---|
|low-level<br>low-level<br>low-level|_𝑥_<sup>beh-aim</sup><br>_𝑖_<br>_𝑥_<sup>beh-mech</sup><br>_𝑖_<br>_𝑥_<sup>beh-combat</sup><br>_𝑖_<br>|aiming/crosshair<br>mechanics/state<br>combat/engagement|view control, correction, recoil, aiming stability<br>counter-strafe, walk/crouch/scope, state switch<br>shooting discipline, reload rhythm, fire output|left-right crosshair correction switches around firing<br>speed drop in the 250ms before each shot<br>reloads per 100 weapon fires|
|rhythm-space<br>rhythm-space<br>rhythm-space|_𝑥_<sup>beh-move</sup><br>_𝑖_<br>_𝑥_<sup>beh-util</sup><br>_𝑖_<br>_𝑥_<sup>beh-time</sup><br>_𝑖_<br>|movement/positioning<br>utility usage<br>timing/rhythm|opening route, position, map-space preference<br>utility timing, type choice, follow-up<br>first contact, firing interval, push/wait rhythm|concentration of frequent opening positions<br>damage within 5 seconds after utility release<br>seconds from round start to first weapon fire|
|tactical|_𝑥_<sup>beh-econ</sup><br>_𝑖_<br>|economy/buy|buy choice and risk under economic pressure|force-buy rate under insufficient economy|
|tactical|_𝑥_<sup>beh-ctx</sup><br>_𝑖_|context|early risk, man advantage/disadvantage, role<br>context|deaths in the first 20 seconds of a round|

where _𝑀𝑖_ is the number of available combat windows. We use a two-layer, four-head Transformer with hidden size 96 and dropout 0.15. Learned attention pooling, masked mean, and masked standard deviation are concatenated and projected to a 192-dimensional observation embedding. The encoder minimizes identity crossentropy plus 0.35 supervised contrastive loss (temperature 0.12), using at most 24 windows during training and 64 during evaluation. 

## **3.4 Pairwise Comparison Representation** 

After obtaining _𝑥𝑖_<sup>beh</sup> and _𝑥𝑖_<sup>seq</sup> , we concatenate them into the complete fingerprint _𝑥𝑖_ = [ _𝑥𝑖_<sup>beh</sup> _,𝑥𝑖_<sup>seq</sup> ]. If two raw fingerprints are simply concatenated and fed to the model, the model must infer both feature differences and endpoint levels from limited samples. We therefore add a set of symmetric comparison features that explicitly express relations such as absolute and relative differences between two demo-players on the same behavioral dimensions. 

Specifically, given two raw fingerprints _𝑥𝑖_ and _𝑥 𝑗_ , we construct explicit comparison features compare( _𝑥𝑖,𝑥 𝑗_ ) by concatenating behavior and sequence comparison blocks. For each scalar behavioral feature _𝑘_ , the behavioral comparison block contains: 

where _𝜖_ ensures numerical stability and 1[·] is the indicator function (1 when the bracketed condition holds, 0 otherwise); ⊕ denotes exclusive OR. For the sequence embeddings, the comparison block contains the elementwise absolute difference, elementwise product, Euclidean distance, and cosine similarity: 

## **3.5 Account-History Aggregation** 

Actual account-consistency checks usually compare not just two demos, but one current demo under review against multiple historical demos of the account. Based on the _𝑠𝑖𝑗_ defined in Section 

3.1, we compare the current observation _𝑥𝑞_ with each of the account’s _𝐾_ historical observations _𝐻_ = { _𝑥ℎ_ 1 _, . . . ,𝑥ℎ𝐾_ }, obtaining _𝐾_ scores that describe the consistency between current behavior and account-history behavior: 

Multi-demo aggregation converts _𝐾_ pairwise scores into an account-level consistency score. The most direct approach aggregates raw scores, such as the raw-score mean: 

We also evaluate an empirical LLR-style score transformation as an interpretable evidence scale for adding multiple pairwise scores. Based on the same / different score distributions on the training side, each pair score _𝑠_ is mapped to an evidence value _ℓ_ ( _𝑠_ ): 

where _𝑏_ ( _𝑠_ ) is one of 20 fixed equal-width bins on [0 _,_ 1] and _𝛼_ = 1. The bin distributions are estimated only from frozen foldlocal validation predictions. Intuitively, _ℓ_ ( _𝑠_ ) is positive when a score bin is more common among same-player pairs and negative when it is more common among different-player pairs. We then average the evidence over the _𝐾_ historical observations: 

## **3.6 Overall Workflow** 

Fig. 1 shows the main data flow at inference time: each demo-player observation is first encoded as a fingerprint, two fingerprints are compared to obtain _𝑠𝑖𝑗_ , and multiple current-vs-history scores are then aggregated into an account-level consistency score. Training mainly supervises the pairwise comparator _𝑔𝜃_ . 

## **4 Experiments** 

## **4.1 Dataset and Evaluation Setup** 

**Perfect dataset and manual confirmation.** The Perfect dataset, DPER, uses active users from a university CS player guild on Perfect World Arena [20] as the collection entry point. We downloaded 

Account Consistency from Gameplay Traces: Same-Player Verification in Counter-Strike 2 

**Figure 1: Method overview: per-demo-player fingerprinting, pairwise scoring, and current-vs-history aggregation.** 

their available CS2 match demos within a specified time window, forming 3,570 demos and 35,700 demo-player observations. The guild players cover 12 amateur competitive tiers from C to Diamond S and above. To obtain credible same-player positives, we contacted active users in the guild and asked them to confirm whether the account was used only by themselves within the window, whether multiple accounts existed, and whether those accounts were all operated by the same real player. Observations with clear account borrowing, non-self play, uncertainty, or account-sharing risk do not enter same-player positives. 

**Positive construction.** The 4,495 manually confirmed demoplayer observations come from 107 confirmed persons and are used to construct same-player positives. For each confirmed person with _𝑛𝑝_ available observations, we enumerate<sup>�</sup><sup>_𝑛_</sup> 2<sup>_𝑝_</sup> � same-player combinations; across the six test folds, 171,713 same-player pairs are formed. 

**Negative sampling.** Different-player pairs are sampled between observations with different person ids; observations manually confirmed to belong to the same real player or the same account group are first assigned to the same person id so they are not sampled as negatives. To cover negatives of different difficulty, the initial candidate quota assigns 25% to same-demo pairs, 25% to same-rank pairs, and 50% to other randomly sampled different-player pairs; if a stratum lacks sufficient legal capacity, its shortfall is deterministically reassigned to the random stratum. The 35,700 observations theoretically form<sup>�35700</sup> 2 � = 637 _._ 2M possible pairs, the vast majority different-player. We keep all 171,713 same-player pairs in the six test folds and sample different-player pairs at an overall 1:9 ratio, obtaining 1,717,130 pairwise samples. 

**Professional dataset.** In addition to DPER, we downloaded public professional match demos from HLTV match/demo pages [21] and built the Professional dataset, DPRO. This set contains 539 professional match demos and 5,390 demo-player observations, among which 1,330 target professional-player observations correspond to 130 professional players. Professional identities come from public tournament records, providing externally verifiable longitudinal player records and coverage of elite play. 

**Positive and negative construction.** In DPRO, the 1,330 target observations used for positive construction come from 130 professional players; for each player _𝑝_ with _𝑛𝑝_ available observations, we likewise enumerate<sup>�</sup><sup>_𝑛_</sup> 2<sup>_𝑝_</sup> � same-player combinations, yielding 10,769 same-player pairs across the six test folds. The 5,390 observations theoretically form<sup>�5390</sup> 2 � = 14 _._ 5M possible pairs, the vast majority different-player. Different-player pairs use the same initial stratification targets and capacity-shortfall reassignment rule. We retain all 10,769 same-player pairs in the six test folds and sample different-player pairs at an overall 1:9 ratio, yielding 107,690 pairwise samples. Across both datasets, only confirmed/target observations generate same-player positives; remaining roster observations enter only as different-player candidates under the frozen SteamID/alias mapping. Unlinked SteamIDs are treated as distinct identity units, so undisclosed cross-account ownership can create false-negative labels. For both datasets, AP is reported on the sampled evaluation distribution; deployment thresholds should be recalibrated on platform-specific data. 

**Dataset use.** We evaluate representation levels, model comparison, feature sensitivity, history aggregation, and cross-time and cross-map robustness on both DPER and DPRO, and further examine cross-dataset training. We additionally collect 513 demos and 5,130 demo-player observations from an independent player guild on the 5E platform [22], forming the 5E dataset D5E. We use D5E as a cross-platform external test set with weak account labels to evaluate zero-shot generalization of models trained on Perfect. 

**Split protocol.** Both datasets first form six folds by the known real-player identity ledger and then assign each demo to one side. Under this ledger, natural-person, SteamID, alias, observation, demo, and content overlaps between training and test are zero; undisclosed cross-account ownership remains possible label noise. Pairs crossing the two sides are discarded. Training and validation pairs follow the same legal constraints and 1:9 same-to-different ratio as the test pairs. Within each outer fold, sequence encoders and pairwise scorers fit only training-side identities; validation selects checkpoints and iteration counts, and the test fold is used only for final scoring. Pair endpoints use ascending frozen endpoint index as the canonical order. 

Xuchen Zhang 

**Map factor.** CS2 competitive matches concentrate on a small active-duty competitive map pool, including Dust2 and Mirage. Maps affect default routes, combat distances, and utility combinations; still, the same player is likely to retain stable habits such as crosshair control, firing rhythm, movement-stop-fire coordination, and risk preference across maps. We therefore verify both same-map and cross-map pairs. 

**Evaluation sets.** Table 2 gives the evaluation views used in this paper. The E1–E5 representation ladder and headline finalmodel results use the sequence-common surfaces TPER<sup>(1:6</sup> _,𝑝𝑎𝑖𝑟,𝑠𝑒𝑞_<sup>)and</sup> TPRO<sup>(1:6</sup> _,𝑝𝑎𝑖𝑟,𝑠𝑒𝑞_<sup>),whereallrepresentationlevelsshareidenticalpair</sup> IDs, labels, and order. The full pair surfaces TPER<sup>(1:6</sup> _,𝑝𝑎𝑖𝑟_<sup>)and T</sup> PRO<sup>(1:6</sup> _,𝑝𝑎𝑖𝑟_<sup>)</sup> are used for non-sequence analyses; TPER<sup>(1)</sup> _,𝑝𝑎𝑖𝑟_<sup>is used only as the</sup> Perfect grouped-feature analysis split, whereas the corresponding Professional analysis uses all six folds. TPER<sup>(1:6</sup> _,ℎ𝑖𝑠𝑡_<sup>)(</sup><sup>_𝐾_) and T</sup> PRO<sup>(1:6</sup> _,ℎ𝑖𝑠𝑡_<sup>)(</sup><sup>_𝐾_)</sup> test whether aggregating the current demo with _𝐾_ historical demos forms more stable account-level evidence; TPER<sup>(1:6</sup> _,𝑡𝑖𝑚𝑒_<sup>)and T</sup> PRO<sup>(1:6</sup> _,𝑡𝑖𝑚𝑒_<sup>)</sup> measure degradation over longer time spans; and TPER<sup>(1:6</sup> _,𝑚𝑎𝑝_<sup>)and</sup> TPRO<sup>(1:6</sup> _,𝑚𝑎𝑝_<sup>)examine robustness in cross-map comparison.</sup> 

Compared with E2, E4 combines _𝑥_<sup>beh</sup> and _𝑥_<sup>seq</sup> : on DPER, AUC improves by 0.004 on average (+0.005/+0.002/+0.006/0.011/+0.004/+0.018); on DPRO, AUC changes by 0.000 on average (-0.017/+0.005/-0.005/-0.002/+0.007/+0.014). Overall, the two representations provide complementary information: behavioral fingerprints summarize operation and decision distributions that recur across rounds, while sequence embeddings preserve action order in combat windows. This complementarity yields a small improvement on DPER but no consistent gain on DPRO. This may reflect the smaller Professional training set and redundancy between the transferred sequence representation and existing behavioral statistics. 

The largest gain comes from explicit pairwise comparison. After adding explicit pairwise comparison features, E5 improves over E4 on DPER by 0.066 AUC on average (+0.049/+0.096/+0.079/+0.045/+0.036/+0.093); on DPRO, the gain is 0.082 AUC (+0.089/+0.077/+0.068/+0.078/+0.055/+0.123). With explicit comparison features, the model directly uses absolute and relative differences on the same behavioral dimensions, reducing the need to learn symmetric difference relations from limited samples. 

In pairwise tables, AP (Average Precision) uses same-player as the positive class. On the 5E weak-label surface, AP analogously uses same-account as the positive class. 

Reported means and deltas are calculated from unrounded fold scores. 

## **4.2 Behavioral Representations and Model Comparison** 

_4.2.1 Representation Levels: Which Information Brings Gains._ Table 3 uses the averages over TPER<sup>(1:6</sup> _,𝑝𝑎𝑖𝑟,𝑠𝑒𝑞_<sup>)andT</sup> PRO<sup>(1:6</sup> _,𝑝𝑎𝑖𝑟,𝑠𝑒𝑞_<sup>)asthe</sup> main pairwise results for the two datasets. The main DPRO results use a sequence encoder trained and frozen on the larger DPER, avoiding a sequence representation determined only by the smaller Professional training set. On each split, the same LightGBM pairwise model [18] compares how much same-player consistency signal different input representations provide. E1 uses _𝑥_<sup>out</sup> , i.e., outcome/performance-only features, including result-based statistics such as K/D (kill/death ratio), damage, score (game scoreboard score), headshot rate, and first kill / first death. E5 corresponds to the full pairwise input in Eq. (3) in Section 3.1. 

E1, using only result-based statistics, is a weak baseline, with AUCs of 0.572 and 0.712 on DPER and DPRO, respectively. Using the CS2-understanding-based _𝑥_<sup>beh</sup> in E2 yields AUCs of 0.855 and 0.874 on TPER<sup>(1:6</sup> _,𝑝𝑎𝑖𝑟,𝑠𝑒𝑞_<sup>)and T</sup> PRO<sup>(1:6</sup> _,𝑝𝑎𝑖𝑟,𝑠𝑒𝑞_<sup>), respectively, showing that crosshair</sup> control, movement-stop-fire coordination, combat rhythm, economy/buy, and round timing contain strong player-identity signals. E3, using the sequence representation _𝑥_<sup>seq</sup> alone, reaches AUCs of 0.719 and 0.749 on the two surfaces, indicating that action order in combat windows carries identity information but does not alone cover behaviors that recur across rounds. The main DPRO configuration uses the encoder pretrained and frozen on DPER; an alternative trained only on DPRO training data yields a nearly identical E3 AUC of 0.747 versus 0.749. 

_4.2.2 Model Comparison._ **Sequence feature comparison.** The _𝑥_<sup>seq</sup> in Eq. (5) in Section 3.3 is produced by a separately trained Transformer sequence encoder. The reported configuration uses continuous numerical combat-window sequences focused on shooting interactions. This encoder is trained with player identity labels, models action order around combat windows, and aggregates multiple windows into a demo-player-level sequence representation, which then enters the final pairwise input together with the gameunderstanding-based _𝑥_<sup>beh</sup> . 

**Pairwise model comparison.** Table 4 compares final-layer pairwise models on frozen outer-test predictions from TPER<sup>(1:6</sup> _,𝑝𝑎𝑖𝑟,𝑠𝑒𝑞_<sup>)</sup> and TPRO<sup>(1:6</sup> _,𝑝𝑎𝑖𝑟,𝑠𝑒𝑞_<sup>); no tuning follows these comparisons. Within each</sup> dataset, all models use exactly the same frozen E5 input representation, _𝑥_<sup>beh</sup> + _𝑥_<sup>seq</sup> + compare( _𝑥𝑖,𝑥 𝑗_ ) + _𝑐𝑖𝑗_ . We compare LightGBM [18], XGBoost [19], FastMLP, and a rank-average ensemble. LightGBM is used as the final pairwise scorer and obtains the highest six-fold mean AUC on both datasets. XGBoost and rank averaging remain close, while FastMLP is consistently weaker. Our final implementation therefore uses game-understandingbased behavioral fingerprints, Transformer-derived sequence representations, explicit comparison features, and a LightGBM pairwise scorer. 

**Implementation details.** The sequence encoder is trained for 12 epochs with AdamW (learning rate 2 × 10<sup>−4</sup> , weight decay 0.02) and gradient-norm clipping at 1.0. The LightGBM scorer uses 63 leaves, learning rate 0.04, feature fraction 0.78, bagging fraction 0.85, and minimum child size 160; it trains for at most 450 rounds with validation-side early stopping after 40 rounds. ChatGPT/Codex assisted code drafting, figure preparation, and language editing; all outputs were reviewed and verified by the author. A de-identified research code package is planned for public release. 

Account Consistency from Gameplay Traces: Same-Player Verification in Counter-Strike 2 

**Table 2: Evaluation sets and metrics used in the experiments.** 

|symbol||purpose|construction|size|metrics|
|---|---|---|---|---|---|
|T <sup>(1:6)</sup><br>PER_,𝑝𝑎𝑖𝑟_<br>||full Perfect pair surface|six person-first/demo-ownership folds;<br>known-identity, SteamID, alias, observation, demo,<br>and content overlap is zero|total_𝑁_=1_,_717_,_130= 171,713 same +<br>1,545,417 different|mean AUC, same-AP|
|T <sup>(1:6)</sup><br>PRO_,𝑝𝑎𝑖𝑟_<br>||full Professional pair surface|the same strict six-fold protocol<br>|total_𝑁_=107_,_690= 10,769 same + 96,921<br>different|mean AUC, same-AP|
|T <sup>(1)</sup><br>PER_,𝑝𝑎𝑖𝑟_<br><br>||Perfect grouped feature sensitivity|first test fold of T <sup>(1:6)</sup><br>PER_,𝑝𝑎𝑖𝑟_|_𝑁_=286_,_170= 28,617 same + 257,553<br>different|sensitivity AUC|
|T <sup>(1:6)</sup><br>PER_,𝑝𝑎𝑖𝑟,𝑠_<br><br>|_𝑒𝑞_<sup>/ T (1:6)</sup><br>PRO_,𝑝𝑎𝑖𝑟,𝑠𝑒𝑞_<br>|E1–E5 ladder and headline final<br>model|identical sequence-common pair IDs, labels, and<br>order within each dataset|Perfect: 1,518,330 pairs; Professional:<br>107,690 pairs|E1–E5 mean AUC / same-AP|
|T <sup>(1:6)</sup><br>PER_,ℎ𝑖𝑠𝑡_<sup>(</sup><br><br>|<sup>_𝐾_) / T (1:6)</sup><br>PRO_,ℎ𝑖𝑠𝑡_<sup>(</sup><sup>_𝐾_)</sup><br>|strict-prior history aggregation|current observation with_𝐾_earlier history<br>observations|Perfect:_𝐾_=1_,_3_,_5_,_10; Professional:<br>_𝐾_=1_,_3_,_5|account mean-LLR AUC|
|T <sup>(1:6)</sup><br>PER_,𝑡𝑖𝑚𝑒_<br><br>|<sup>/ T (1:6)</sup><br>PRO_,𝑡𝑖𝑚𝑒_<br>|cross-time comparison|same day, 1–7, 8–30, 31–90, and_>_ 90days|available buckets in frozen six-fold<br>predictions|AUC|
|T <sup>(1:6)</sup><br>PER_,𝑚𝑎𝑝_<sup>/</sup>|<sup>T (1:6)</sup><br>PRO_,𝑚𝑎𝑝_|map robustness|split frozen predictions by map relation|Perfect: 462,043 same-map + 1,056,287<br>cross-map; Professional: 38,295 + 69,395|AUC, same-AP|
|T5E<br>||cross-platform weak-account test|exact SteamID as weak same-account label|_𝑁_=55_,_840= 5,584 same + 50,256<br>different|AUC|
|T<sup>disjoint</sup><br>5E||exact-SteamID-disjoint sensitivity|exclude one SteamID overlapping the source|_𝑁_=55_,_676= 5,583 same + 50,093<br>different|AUC|

**Table 3: Representation ladder on the two sequence-common evaluation surfaces.** 

**Table 5: Behavioral feature sensitivity (explicit comparison fixed; sequence excluded).** 

|data|exp.|input|AUC|same-AP|
|---|---|---|---|---|
|DPER|E1|outcome|0.572|0.130|
|DPER|E2|behavior|0.855|0.452|
|DPER|E3|sequence|0.719|0.227|
|DPER|E4|behavior + sequence|0.859|0.454|
|DPER|E5|+ explicit compare|**0.926**|**0.703**|
|DPRO|E1|outcome|0.712|0.210|
|DPRO|E2|behavior|0.874|0.464|
|DPRO|E3|sequence|0.749|0.254|
|DPRO|E4|behavior + sequence|0.874|0.480|
|DPRO|E5|+ explicit compare|**0.956**|**0.775**|

**Table 4: Six-fold mean AUC for pairwise model families on the two frozen E5 evaluation surfaces.** 

|dataset|model|AUC|Δvs. LightGBM|
|---|---|---|---|
|DPER|LightGBM|**0.926**|–|
|DPER<br>|XGBoost|0.918|-0.008|
|DPER|FastMLP|0.858|-0.067|
|DPER<br>|rank-average|0.918|-0.008|
|DPRO|LightGBM|**0.956**|–|
|DPRO|XGBoost|0.950|-0.005|
|DPRO|FastMLP|0.883|-0.073|
|DPRO|rank-average|0.946|-0.010|

|data|setting|eval.|AUC (Δ)|
|---|---|---|---|
|DPER|full_𝑥_<sup>beh</sup>|T<sup>(1:6)</sup><br>PER_,𝑝𝑎𝑖𝑟_<br>|0.919 (0)|
|DPER|remove aiming/crosshair|T<sup>(1:6)</sup><br>PER_,𝑝𝑎𝑖𝑟_<br>|0.833 (-0.087)|
|DPER|only aiming/crosshair|T<sup>(1:6)</sup><br>PER_,𝑝𝑎𝑖𝑟_<br>|0.890 (-0.029)|
|DPER|remove mechanics/state|T<sup>(1:6)</sup><br>PER_,𝑝𝑎𝑖𝑟_<br>|0.908 (-0.012)|
|DPRO|full_𝑥_<sup>beh</sup>|T<sup>(1:6)</sup><br>PRO_,𝑝𝑎𝑖𝑟_<br>|0.955 (0)|
|DPRO|remove aiming/crosshair|T<sup>(1:6)</sup><br>PRO_,𝑝𝑎𝑖𝑟_<br>|0.880 (-0.076)|
|DPRO|only aiming/crosshair|T<sup>(1:6)</sup><br>PRO_,𝑝𝑎𝑖𝑟_<br>|0.915 (-0.041)|
|DPRO|remove mechanics/state|T<sup>(1:6)</sup><br>PRO_,𝑝𝑎𝑖𝑟_|0.950 (-0.006)|
|DPER|full_𝑥_<sup>beh</sup>|T<sup>(1)</sup><br>PER_,𝑝𝑎𝑖𝑟_<br>|0.916 (0)|
|DPER|only low-level operations|T<sup>(1)</sup><br>PER_,𝑝𝑎𝑖𝑟_<br>|0.915 (-0.001)|
|DPER|remove low-level operations|T<sup>(1)</sup><br>PER_,𝑝𝑎𝑖𝑟_<br>|0.738 (-0.179)|
|DPER|remove rhythm/space|T<sup>(1)</sup><br>PER_,𝑝𝑎𝑖𝑟_<br>|0.914 (-0.002)|
|DPER|remove tactics/context|T<sup>(1)</sup><br>PER_,𝑝𝑎𝑖𝑟_<br>|0.914 (-0.002)|
|DPRO|full_𝑥_<sup>beh</sup>|T<sup>(1:6)</sup><br>PRO_,𝑝𝑎𝑖𝑟_<br>|0.955 (0)|
|DPRO|only low-level operations|T<sup>(1:6)</sup><br>PRO_,𝑝𝑎𝑖𝑟_<br>|0.947 (-0.009)|
|DPRO|remove low-level operations|T<sup>(1:6)</sup><br>PRO_,𝑝𝑎𝑖𝑟_<br>|0.842 (-0.113)|
|DPRO|remove rhythm/space|T<sup>(1:6)</sup><br>PRO_,𝑝𝑎𝑖𝑟_<br>|0.953 (-0.003)|
|DPRO|remove tactics/context|T<sup>(1:6)</sup><br>PRO_,𝑝𝑎𝑖𝑟_|0.952 (-0.003)|

## **4.3 Feature-Family Sensitivity: Which Behaviors Carry Identity Signal** 

Table 5 reports feature-family sensitivity on TPER<sup>(1:6</sup> _,𝑝𝑎𝑖𝑟_<sup>)and T</sup> PRO<sup>(1:6</sup> _,𝑝𝑎𝑖𝑟_<sup>),</sup> together with feature-layer analysis by behavioral mechanism on TPER<sup>(1)</sup> _,𝑝𝑎𝑖𝑟_<sup>and T</sup> PRO<sup>(1:6</sup> _,𝑝𝑎𝑖𝑟_<sup>), summarizing the features that most support</sup> the behavioral findings. Every setting in Table 5 fixes the same explicit comparison input and changes only the behavioral feature families retained in _𝑥_<sup>beh</sup> . 

Table 5 shows that aiming/crosshair is the strongest identity signal. On DPER, the six-fold average AUC of the full _𝑥_<sup>beh</sup> is 0.919, and removing aiming/crosshair lowers it by 0.087 on average (-0.114/0.090/-0.098/-0.053/-0.068/-0.096); on DPRO, the corresponding AUC is 0.955 and the average decrease is 0.076 (-0.082/-0.068/-0.046/0.063/-0.062/-0.134). Using only aiming/crosshair reaches AUCs of 

0.890 and 0.915, respectively; among the reported removals, mechanics/state provides the next-largest contribution. 

Merging the eight feature types by behavioral mechanism concentrates the conclusion: on TPER<sup>(1)</sup> _,𝑝𝑎𝑖𝑟_<sup>and T</sup> PRO<sup>(1:6</sup> _,𝑝𝑎𝑖𝑟_<sup>), using only aim-</sup> ing/crosshair, mechanics/state, and combat/engagement lowers AUC by only 0.001 and 0.009, respectively, while removing these three lowers AUC by 0.179 and 0.113. The two datasets yield the same conclusion: CS2 player identity signals come mainly from crosshair control, combat micro-operations, and movement-stopfire coordination, while rhythm, space, buying, and context preferences provide supplementary information. 

Xuchen Zhang 

**Table 6: Account-history aggregation as history depth** _𝐾_ **changes.** 

|data|_𝐾_|mean-LLR AUC|six-fold AUCs|
|---|---|---|---|
|DPER<br>|1|0.923 (baseline)|0.935/0.918/0.878/0.940/0.949/0.918|
|DPER<br>|3|0.966 (+0.043)|0.976/0.960/0.938/0.962/0.985/0.974|
|DPER|5|0.975 (+0.052)|0.981/0.967/0.955/0.975/0.989/0.983|
|DPER|10|0.982 (+0.058)|0.986/0.975/0.966/0.982/0.992/0.987|
|DPRO<br>|1|0.914|0.893/0.941/0.922/0.919/0.906/0.905|
|DPRO<br>|3|0.966|0.970/0.969/0.962/0.967/0.968/0.959<br>|
|DPRO|5|0.975|0.974/0.983/0.969/0.980/0.978/0.968|
|DPRO|10|not estimable|no eligible_𝐾_=10queries in any fold|

**Table 7: Time-gap sensitivity on the two datasets.** 

|data|time gap|pairs|AUC|
|---|---|---|---|
|DPER|same day|187,171|0.985|
|DPER|1–7 days|321,023|0.944|
|DPER|8–30 days|345,533|0.927|
|DPER|31–90 days|220,265|0.885|
|DPER|_>_90days|444,338|0.894|
|DPRO|same day|29,626|0.989|
|DPRO|1–7 days|45,126|0.949|
|DPRO|8–30 days|32,938|0.924|
|DPRO|≥31days|0|–|

## **4.4 Account-History Aggregation: From Pairwise Scores to Multi-Demo History Comparison** 

Account-history review compares a current demo against multiple historical demos. Table 6 reports account-history aggregation on TPER<sup>(1:6</sup> _,ℎ𝑖𝑠𝑡_<sup>)(</sup><sup>_𝐾_)and T</sup> PRO<sup>(1:6</sup> _,ℎ𝑖𝑠𝑡_<sup>)(</sup><sup>_𝐾_). Each eligible query forms one posi-</sup> tive group from _𝐾_ strictly earlier observations of the same identity/account key and four negative groups, each formed from one different identity candidate; deterministic, score-blind nested prefixes are fixed by each dataset contract. The mean LLR in Eq. (10) aggregates each group’s _𝐾_ scores. 

Multi-demo history comparison provides a more stable accountlevel signal than a single pairwise score. To keep _𝐾_ comparisons paired, all Perfect rows use the same fixed _𝐾_ = 10-eligible cohort (3,782 query-fold instances), while Professional _𝐾_ = 1 _,_ 3 _,_ 5 use the same fixed _𝐾_ = 5-eligible cohort (446 query-fold instances). On DPER, mean-LLR AUC rises from 0.923 at _𝐾_ = 1 to 0.966 at _𝐾_ = 3 and 0.982 at _𝐾_ = 10; on DPRO, the corresponding _𝐾_ = 1 _,_ 3 _,_ 5 values are 0.914, 0.966, and 0.975. No Professional fold has an eligible _𝐾_ = 10 query. These fixed history-group cohorts differ from the pair surface in Table 3; on Perfect, raw-score mean gives very similar AUC, indicating that the main gain comes from accumulating multiple evidence items. 

## **4.5 Cross-Time, Cross-Map, and Data Expansion Experiments** 

_4.5.1 Time-Gap Sensitivity._ Actual review often occurs with larger time gaps: a platform or tournament organizer obtains a recent suspicious demo and compares it with earlier historical demos of the account. This setting is harder than random pairs, because player state, map pool, version, settings, and play style may all change over time. 

DPER observations span April 14 to August 19, 2026, forming same-day, 1–7-day, 8–30-day, 31–90-day, and over-90-day comparisons; the available DPRO comparisons cover same-day, 1–7-day, and 8–30-day gaps. 

**Table 8: Same-map vs cross-map sensitivity on the two datasets.** 

|data|relation|pairs|same/diff.|AUC/Δ|same-AP/Δ|
|---|---|---|---|---|---|
|DPER|all|1,518,330|153,790/1,364,540|0.926/–|0.703/–|
|DPER|same|462,043|41,862/420,181|0.951/+0.026|0.769/+0.066|
|DPER <br>|cross<br>|1,056,287|111,928/944,359|0.914/-0.012|0.676/-0.027|
|DPRO <br>|all<br>|107,690|10,769/96,921<br>|0.956/–<br>|0.775/–<br>|
|DPRO <br>|same<br>|38,295|1,823/36,472|0.980/+0.024|0.808/+0.034|
|DPRO|cross|69,395|8,946/60,449|0.942/-0.014|0.768/-0.007|

**Table 9: Cross-dataset training under a separate frozen augmentation protocol (** Δ **relative to** DPER **-only training within each test block).** 

|test|training data|AUC|Δvs. block baseline|
|---|---|---|---|
|DPER|DPER|0.911|baseline|
|DPER|DPER + DPRO|0.914|+0.003|
|DPRO|DPER|0.912|baseline|
|DPRO|DPRO|**0.955**|+0.043|
|DPRO|DPER + DPRO|0.948|+0.036|

Table 7 shows that longer time gaps are generally harder: AUC on DPER declines from 0.985 for same-day comparisons to 0.885 for 31–90 days and is 0.894 beyond 90 days; on DPRO, it declines from 0.989 for same-day comparisons to 0.924 for 8–30 days. This is consistent with intuition: over longer gaps, the same player’s state, map pool, and play style may change, yet the model retains useful cross-time recognition. 

_4.5.2 Cross-Map Robustness._ Cross-map comparisons are common in account-history review and remove some map-specific contextual similarity. 

Table 8 shows that on DPER, same-map AUC is 0.026 above the all-pair result and cross-map AUC is 0.012 below it; on DPRO, the differences are +0.024 and -0.014. Because sampled same-demo negatives are necessarily same-map, part of the same-map advantage reflects pair construction. Cross-map AUCs remain 0.914 and 0.942. 

_4.5.3 Cross-Dataset Training Between Perfect and Professional._ We examine the effect of training-data source on TPER<sup>(1:6</sup> _,𝑝𝑎𝑖𝑟_<sup>)and T</sup> PRO<sup>(1:6</sup> _,𝑝𝑎𝑖𝑟_<sup>).</sup> 

Table 9 uses a separate frozen cross-dataset augmentation protocol; its DPER-only baseline uses a different training-pair construction from the within-dataset ablation baseline in Table 5. On TPRO<sup>(1:6</sup> _,𝑝𝑎𝑖𝑟_<sup>), Professional-only training reaches AUC 0.955, 0.043</sup> above the 0.912 from Perfect-only training; mixed training reaches 0.948. On the Perfect test surface, adding Professional training data changes AUC from 0.911 to 0.914. The lower mixed-versusProfessional-only result may reflect differences between the two data domains in team roles, match intensity, and behavior distributions. 

_4.5.4 External Test on 5E._ D5E uses exact SteamID as a weak sameaccount label, so the result cannot be directly interpreted as samenatural-person verification. The behavior-and-explicit-comparison model trained on DPER reaches zero-shot AUC 0.966 on the full fixed test surface T5E (55,840 pairs), providing evidence of crossplatform transfer under weak same-account labels. After excluding one SteamID that overlaps the training source, T5E<sup>disjoint</sup> retains 55,676 pairs (99.7%) and the AUC remains 0.966. 

Account Consistency from Gameplay Traces: Same-Player Verification in Counter-Strike 2 

## **5 Discussion and Limitations** 

## **5.1 Evaluation Boundaries** 

Our primary splits are formed by the constructed identity ledger and assign each demo to one side. Under this ledger, known naturalperson, SteamID, alias, observation, demo, and content overlaps between training and test are zero. The model input is restricted to per-player fingerprints and a same-map/cross-map flag; it excludes demo IDs, match IDs, teammate/opponent identities, and sharedmatch identifiers. Undisclosed cross-account ownership may still violate true person disjointness and is treated as residual label noise. 

Using 1,000 player-cluster bootstrap replicates, the final model has 95% AUC confidence intervals of [0.915, 0.950] on DPER and [0.948, 0.965] on DPRO, indicating that the results are not driven by a few high-contribution players. 

After excluding different-player pairs drawn from the same demo, E5 AUC remains 0.920 on Perfect and 0.944 on Professional, indicating that performance is not driven by same-match negatives. 

## **5.2 Data and Label Boundaries** 

In DPER, same-player labels come from players’ manual confirmation of account histories, account sharing, and multi-account ownership; undisclosed borrowing, temporary substitution, or account sharing may still introduce label noise. The results therefore depend on the completeness of the manual confirmations, and deployment should retain identity audits and feedback from new evidence. 

## **5.3 Practical Deployment: Runtime Cost and Responsible Use** 

Once fingerprints and embeddings are available, pairwise scoring and history aggregation process about 24k pairs/s on Apple M4; demo parsing and feature extraction remain the dominant offline cost. 

In deployment, a new demo can be compared with historical observations to prioritize cases where current behavior is clearly inconsistent with the account history. 

On DPER, retrieved account histories may include observations from another operator. On the _𝐾_ = 5 subset for which eligible third-player replacements can be constructed, 3,674/3,782 queries (97.1%) are retained. Replacing one, two, or three of the five positive histories with different-player observations lowers mean-LLR AUC from 0.975 to 0.963, 0.941, and 0.894, respectively. 

## **6 Conclusion and Future Work** 

We formulate account-history consistency review on competitive FPS platforms as open-set same-player verification, using CS2 demos to design per-demo-player behavioral fingerprints and learn pairwise consistency. 

Experiments show strong discrimination: on the sequencecommon Perfect and Professional evaluation surfaces, the full model reaches ROC AUCs of 0.926 and 0.956. Identity signal comes mainly from aiming/crosshair and other low-level mechanical behaviors. On fixed eligible query cohorts, mean-LLR account-history AUC rises from 0.923 at _𝐾_ = 1 to 0.982 at _𝐾_ = 10 on Perfect and from 0.914 at _𝐾_ = 1 to 0.975 at _𝐾_ = 5 on Professional. 

Future work will study longer-term drift, partial-match verification, and human-in-the-loop review. 

## **7 Ethical Considerations** 

This work is intended to provide identity-consistency evidence for prioritizing account-history review, rather than to determine player identity or impose automated sanctions. False positives may subject legitimate players to unwarranted suspicion, while sparse histories, hardware or setting changes, and atypical play styles may affect model scores. Any operational use should therefore combine multiple sources of evidence with human review, appeals, threshold calibration, and continuing audits, and should not treat a single model score as grounds for enforcement. 

The gameplay demos analyzed in this study were publicly accessible. For the manually confirmed Perfect subset, participating players were informed that their demos and identity confirmations would be used for model training and research, and they consented to this research use and to the release of de-identified derived features. 

Game demos contain fine-grained behavioral trajectories, and learned fingerprints could be repurposed for unwanted tracking or profiling. The model inputs exclude real names, SteamIDs, demo IDs, match IDs, and other direct identifiers; we report aggregate results, and the de-identified research artifact excludes raw demos, identity mappings, and identity ledgers. Storage, access, and subsequent sharing of manually confirmed information, public professionalmatch records, and derived representations should follow dataminimization principles and the scope of the original authorization. 

The evaluated data cover particular platforms, player communities, and professional matches, and do not establish equal performance across regions, skill levels, hardware environments, or long-term behavioral drift. Deliberate imitation or behavior modification may also evade review, and this work does not establish robustness under real adversarial conditions. Deployment should monitor error rates across populations and use cases and constrain the system’s purpose accordingly. 

## **References** 

- [1] Valve, “Counter-Strike 2,” Steam Store. [Online]. Available: https://store. steampowered.com/app/730/CounterStrike_2/ 

- [2] SteamDB, “Counter-Strike 2 Steam Charts.” [Online]. Available: https://steamdb. info/app/730/charts/ 

- [3] E. Conroy, M. Kowal, A. J. Toth, and M. J. Campbell, “Boosting: Rank and skill deception in esports,” _Entertainment Computing_ , vol. 36, Art. no. 100393, 2021, doi: 10.1016/j.entcom.2020.100393. 

- [4] J. Blackburn, N. Kourtellis, J. Skvoretz, M. Ripeanu, and A. Iamnitchi, “Cheating in online games: A social network perspective,” _ACM Trans. Internet Technol._ , vol. 13, no. 3, Art. no. 9, pp. 1–25, 2014, doi: 10.1145/2602570. 

- [5] FACEIT, “FACEIT Banning Policy.” [Online]. Available: https://support.faceit. com/ 

- [6] FACEIT, “The Verification Process.” [Online]. Available: https://support.faceit. com/ 

- [7] F. Zimmer _et al._ , “Player behavior analysis for predicting player identity within pairs in esports tournaments: A case study of Counter-Strike using binary Random Forest classifier,” in _Proc. HICSS_ , 2025, doi: 10.24251/HICSS.2025.513. 

- [8] F. Zimmer _et al._ , “Fair Play and Identity: In-game behavioral biometrics for player identification in competitive online games,” in _Proc. IEEE Conf. Games (CoG)_ , 2025, doi: 10.1109/CoG64752.2025.11114281. 

- [9] J. Orlova, A. Stepanov, and A. Somov, “GUARD: Enabling fair gaming through the gameplay analysis using machine learning methods and expert knowledge,” _Expert Systems with Applications_ , 2026, doi: 10.1016/j.eswa.2025.130908. 

- [10] D. Liu, X. Gao, M. Zhang, H. Wang, and A. Stavrou, “Detecting passive cheats in online games via performance-skillfulness inconsistency,” in _Proc. DSN_ , 2017. 

Xuchen Zhang 

- [11] S. Yuen, J. D. Thomson, and O. Don, “Automatic player identification in Dota 2,” arXiv:2008.12401 [cs.AI], 2020. 

- [12] S. Liu, C. Ballinger, and S. J. Louis, “Player identification from RTS game replays,” in _Proc. CATA_ , 2013. 

- [13] I. Stylios, S. Kokolakis, O. Thanou, and S. Chatzis, “Behavioral biometrics and continuous user authentication on mobile devices: A survey,” _Information Fusion_ , vol. 66, pp. 76–99, 2021. 

- [14] A. Mahfouz, T. M. Mahmoud, and A. S. Eldin, “A survey on behavioral biometric authentication on smartphones,” _Journal of Information Security and Applications_ , vol. 37, pp. 28–37, 2017. 

- [15] V. Nair _et al._ , “Unique identification of 50,000+ virtual reality users from head and hand motion data,” in _Proc. USENIX Security_ , 2023. 

   - [17] C. Lesaege, F. Schnitzler, A. Lambert, and J.-R. Vigouroux, “Time-aware user identification with topic models,” in _Proc. IEEE ICDM_ , 2016, pp. 997–1002. 

   - [18] G. Ke _et al._ , “LightGBM: A highly efficient gradient boosting decision tree,” in _Advances in Neural Information Processing Systems_ , 2017. 

   - [19] T. Chen and C. Guestrin, “XGBoost: A scalable tree boosting system,” in _Proc. ACM SIGKDD_ , 2016, pp. 785–794. 

   - [20] Perfect World Esports, “Perfect World Esports,” [Online]. Available: https://www. pwesports.cn/. Accessed: Aug. 25, 2026. 

   - [21] HLTV.org, “Counter-Strike matches and demos,” [Online]. Available: https:// www.hltv.org/matches. Accessed: Aug. 25, 2026. 

   - [22] 5EPlay, “5E CS2 platform,” [Online]. Available: https://csgo.5eplay.com/Home. Accessed: Aug. 25, 2026. 

- [16] M. Mohamed and N. Saxena, “Gametrics: Towards attack-resilient behavioral authentication with simple cognitive games,” in _Proc. ACSAC_ , 2016, pp. 277–288.
