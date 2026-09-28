---
id: same_player_verification_cs2
title: Same-Player Verification for Account Consistency in Counter-Strike 2
authors: null
year: 2026
venue: arXiv preprint (submitted to IEEE)
url: https://arxiv.org/abs/2608.24893
arxiv_version: 2608.24893v1
license: unknown — check before redistributing
pdf_sha256: b9b41a1e68f6ac6e
converted: '2026-09-28'
converter: pymupdf4llm
---

# Same-Player Verification for Account Consistency in Counter-Strike 2

> Auto-converted from PDF. Tables, equations and figure text may be garbled — check the original PDF before quoting numbers.

<!-- cscoach-notes:start -->
## cscoach notes (hand-written — preserved on re-conversion)

**Author:** Xuchen Zhang (independent researcher). arXiv preprint, submitted to IEEE. Dataset/code **not** released.
Equations were lost in PDF conversion (Eq. 1–10); read the PDF for formulas.

- **Relevance:** high for *feature engineering* (M4.2 xK, execution-vs-decision split, player fingerprints),
  low for tier modelling (it does not model rank).
- **Verified claims:**
  - 1,330 CS2 demos, 13,300 demo-player observations, Perfect World Arena university guild, **12 amateur
    tiers C … Diamond S+**; 2,380 manually confirmed observations from 64 people; 663,590 pairs (1:9 neg).
  - Headline: **mean ROC AUC 0.931** over 6 person-disjoint splits; recall 0.722 @95% precision.
    **0.955 is the single analysis split** (Table IV), LightGBM > XGBoost (0.951) ≫ MLP (0.854).
  - History aggregation: AUC 0.971 (K=3), 0.980 (K=5), **0.986 (K=10)** (Table VI).
  - Outcome stats only (K/D, ADR, HS%, first kill/death): **AUC 0.599** vs behavioural features 0.831 (Table III).
  - Removing aim/crosshair family: −0.074 AUC; low-level (aim+mechanics+combat) alone ≈ full model.
  - Adding HLTV pro demos did **not** help (distribution shift pro ↔ amateur, §IV-E3).
- **Corrections vs. synthesis:**
  - "ROC AUC 0.955" → headline is **0.931** (0.955 = best split).
  - "These mechanical differences correlate strongly with rank" — **not tested in the paper**. It verifies
    identity, not skill tier. Do not cite it for tier separation.
  - "12 tiers" and dataset name "Perfect World Arena Consistency Dataset" — the paper gives no dataset name
    and releases no data (synthesis §4 lists it as a public dataset: **wrong**).
- **Use in project:**
  - Feature ideas (Table I): speed drop in the 250 ms before each shot (counter-strafe), crosshair correction
    switches around firing, reloads per 100 shots, seconds to first shot, force-buy rate, deaths in first 20 s.
    → xK features (docs/specs/03#xk, M4.2; in CSDS: `player_inputs`, `player_vector.speed_2d`/`ang_vel`/`inaccuracy`, `weapon_fire`), player-habit metrics (M8/M9).
  - Supports design choice: tree models (LightGBM) on engineered features beat MLPs at this data scale.
  - Evidence that pro data does not transfer to amateurs (supports ADR-0002, M3.5).
- **Caveats:** split is person-disjoint but **not match-disjoint** (§V-A); pairwise CIs too narrow, they
  report player-clustered bootstrap only as a diagnostic — same issue our ADR-0001 addresses.
<!-- cscoach-notes:end -->

## Full text

# Same-Player Verification for Account Consistency in Counter-Strike 2 

Xuchen Zhang 

Independent Researcher Email: tigerlovezj@outlook.com 

**_Abstract_ —In competitive first-person shooter (FPS) games such as Counter-Strike 2 (CS2), account-integrity review often asks whether an account’s recent behavior remains consistent with its historical operator. This consistency question arises in cases such as temporary substitution, rank boosting, and high-skill players using lower-ranked accounts, where manual review requires comparing a current match against multiple historical matches. We formulate this review task as same-player verification: we encode the behavioral trajectory of a single player in a match replay (demo) as a demo-player behavioral fingerprint, and train a model to judge whether two behavioral observations come from the same real player. Grounded in CS2 game understanding, the fingerprints cover crosshair control, movement-stop-fire coordination, economy/buy, combat/engagement, and temporal rhythm. From 1,330 CS2 demos we extract 13,300 demo-player observations, and sample 663,590 same/different pairs from an 88.4M candidate-pair space for supervised training and evaluation. The final pairwise model reaches an average ROC AUC of 0.931 and achieves 0.722 different-player recall at 95% precision. Feature analysis shows that the strongest identity signals come from lowlevel operations, especially crosshair control, firing rhythm, and movement-stop-fire coordination, indicating that stable low-level mechanical habits are more informative for this verification task than single-match performance outcomes. In the account-history aggregation evaluation, increasing history depth raises AUC from the K=1 single-pair baseline of 0.931 to 0.986 at K=10. These results show that CS2 demo behavior can support supervised same-player verification and account-level identity-consistency modeling through multi-demo history aggregation.** 

## I. INTRODUCTION 

## _A. Problem Background_ 

Counter-Strike 2 is one of the most active competitive FPS games [1], [2]. 

Beyond anti-cheat, operator consistency within an account history is a distinct fairness concern in competitive FPS platforms. Account sharing, rank boosting, temporary player substitution, and high-skill players using another person’s lower-ranked account can make current operator behavior inconsistent with the account’s historical behavior, undermining matchmaking fairness, player trust, and tournament credibility. To handle such cases, platforms and tournament organizers also need to judge whether the operator’s behavior in the current match is still consistent with the account’s past behavioral patterns. 

This work has been submitted to the IEEE for possible publication. Copyright may be transferred without notice, after which this version may no longer be accessible. 

Existing platform mechanisms address admission, reporting, and case review, while account-history consistency requires a different comparison: current behavior against multiple historical matches. Identity verification suits account admission, tournament registration, or high-risk checkpoints, but is hard to trigger frequently across everyday matches; player reports are low-cost but noisy; and manual demo review can inspect single-match segments but cannot systematically compare the current match against multiple historical matches in shooting habits, mechanics habits, economy decisions, and round rhythm. As a result, existing workflows struggle to turn account-history consistency review into a routine workflow. 

CS2 demos provide structured telemetry for modeling finegrained player operations and decisions across rounds. This paper uses these structured behavioral trajectories to build demo-player behavioral fingerprints and judge the consistency of player behavior across matches. 

## _B. Paper Idea_ 

We model account-history consistency review as open-set same-player verification. Here, open-set means that test-time players need not appear in training; the model does not identify who the current operator is, but learns a reusable comparison function that judges whether two segments of demo-player behavior come from the same real player. In account-history review, this function evaluates behavioral consistency between the current match and historical matches and forms accountlevel identity-consistency evidence. 

We model operation and decision patterns at a lower level than K/D (kill/death ratio), ADR (average damage per round), headshot rate, or rank, such as crosshair micro-adjustment, firing rhythm, movement-stop-fire coordination, and buying preference. Buying preference can be adjusted intentionally, while low-level operations and action-timing coordination such as crosshair control, firing rhythm, and movement-stopfire coordination are less directly controllable and may be harder to imitate consistently across rounds. 

The per-demo-player fingerprint has two parts: aggregate behavioral fingerprint features constructed from game understanding, characterizing stable behaviors such as crosshair, movement, economy, combat, and timing; and Transformerderived sequence embeddings used as complementary behavioral representations for action order, state switching, and lowlevel mechanics from round events and combat windows. The 

pairwise model uses both representations, and account-history review aggregates current-vs-history scores into an accountlevel consistency signal. 

## _C. Results Overview_ 

On the main evaluation set of 1,330 CS2 demos and 13,300 demo-player observations, we sample 663,590 same/different pairs from an 88.4M candidate-pair space for supervised training and evaluation. The final pairwise model reaches ROC AUC 0.931 and achieves 0.722 different-player recall at 95% precision. Feature analysis shows that the identity signal is strongest in crosshair control and combat micro-operations, including view/crosshair micro-adjustment, firing rhythm, and movement-stop-fire coordination. Account-history aggregation raises AUC from the K=1 single-pair baseline of 0.931 to 0.986 at K=10. 

## _D. Contributions_ 

This paper makes the following contributions: 

- **A supervised formulation for FPS account-history consistency.** We formulate account-history consistency review as a same-player verification task that a model can learn. 

- **Behavioral findings from CS2 fingerprints.** We find that player identity signals come mainly from lowlevel operations such as crosshair control, firing rhythm, and movement-stop-fire coordination; sequence modeling adds complementary evidence about action order. 

- **A verification-and-aggregation model with practical account-integrity value.** We evaluate the formulation across person-disjoint splits and account-history aggregation settings, showing that the method scales from singlepair verification to multi-demo account-history consistency modeling. 

## II. RELATED WORK 

## _A. Account Identity Verification and Fairness Mechanisms on Competitive Platforms_ 

Competitive platforms have already incorporated account integrity into fairness governance. Both operator inconsistency behind an account and one person using multiple accounts to bypass platform rules can undermine matchmaking fairness and tournament credibility. Existing esports research discusses boosting—“finding a stronger player to play on an account to improve its rank or results”—and the fairness risk from inconsistency between an account’s displayed skill and the real operator’s ability [3]; broader research on online-game cheating shows that platform governance often needs to combine multiple signals such as accounts, behavior, and social relations [4]. 

Mainstream platforms combine anti-cheat, identity verification, reporting, and manual review to manage account-integrity risks [5], [6]. These mechanisms support admission control, user reports, and case review, but they do not directly provide a systematic comparison between current behavior and multiple historical matches. This paper formalizes that horizontal comparison as CS2 demo-based same-player verification. 

_B. Counter-Strike and FPS Player Behavioral Identity Modeling_ 

The closest game-domain work studies Counter-Strike / CS2 player identity and fair-play. Existing work uses behavioral features to identify known professional players or distinguish known player pairs [7], and related CoG work studies ingame behavioral biometrics for fair play [8]. These studies show that CS/CS2 demo telemetry contains identity-related signals, especially in aiming, shooting, movement state, and game context. 

Our setting is different: platform review often asks whether a current demo remains consistent with an account’s historical demos when the current operator may be unknown or unseen during training. We therefore use manually confirmed sameplayer histories, focus on stable CS2 habits such as crosshair control, firing rhythm, movement-stop-fire coordination, state switching, buying rhythm, and risk preference, and evaluate with unseen-player splits plus current-vs-history aggregation. This moves the target from fixed-identity recognition to account-history consistency. 

Another related direction studies FPS fair-play risk and skill/rating discrepancy. GUARD uses mouse/keyboard dynamics, in-game actions, and expert knowledge to infer a player’s skill group, then compares it with the account rating to identify smurfing / rank-boosting risk [9]. FPS security research also detects passive aimbots through inconsistency between shooting performance and broader skillfulness [10]. These methods can flag cases where operator ability clearly mismatches account rank, or where shooting performance is inconsistent with broader skillfulness. Account borrowing, temporary substitution, or short-term boosting can also happen without an obvious ability jump. We therefore evaluate behavioral consistency between the current demo and accounthistory demos, directly comparing whether behavior before and after still follows the same player’s operational habits. 

## _C. Broader Game Behavior and Behavioral Biometrics_ 

Beyond FPS games, replay and telemetry have also been used for player identity and style modeling. Dota 2 work takes whether two matches were completed by the same player as the target and models it with mouse, game statistics, and strategy information [11]. RTS (real-time strategy) replay identification shows that build order, unit control, resource management, and operation rhythm can identify player style or identity [12]. 

Behavioral biometrics research shows that identity signals can come from how a person acts—mouse trajectories, touchscreen habits, interaction rhythms, and motion patterns [13], [14]; VR head/hand motion, mouse dynamics in simple cognitive games, and active-user identification under shared accounts report similar findings [15]–[17]. These studies provide background evidence that behavioral telemetry can carry identity signal, but their settings differ from natural CS2 account-history review. This paper focuses on the CS2 account-history consistency setting, where identity evidence comes from FPS-specific motor, timing, and tactical behavior. 

## _D. Positioning of This Paper_ 

The above lines of work are complementary to this paper. Platform mechanisms provide admission control, reporting, and manual review entry points; Counter-Strike / FPS behavior studies show that in-game behavior contains identity signal; broader behavioral biometrics shows that identity evidence can emerge from how people act. We instantiate these ideas in CS2 account-history consistency review: using manually confirmed account histories to construct pairwise labels, learning sameplayer verification for unseen players, and identifying crosshair control, movement-stop-fire coordination, and combat microoperations as the behavioral signals that most strongly support this judgment. 

## III. METHOD 

## _A. Problem Definition_ 

We call a parsable behavioral record left by one player in one CS2 match demo a **demo-player observation** ; a standard CS2 match demo usually contains 10 players and therefore produces 10 demo-player observations. A demo records structured replay / telemetry from the game engine, including positions, view angles, weapons, events, and round states. 

We decompose the account-history consistency problem into two levels. 

**Pairwise verification primitive.** The input is a pair of demo-player observations, where each observation represents the behavioral trajectory left by one player in one CS2 match demo. The verification model outputs an identity-consistency score, where higher scores indicate stronger evidence that the two observations come from the same real player. 

**Account-history aggregation.** Given a current observation under review and _K_ historical observations from the account, we compute _K_ pairwise scores and aggregate them into an account-level consistency signal. 

Formally, let _xi_<sup>beh</sup> denote the game-understanding-based aggregate behavioral fingerprint of the _i_ -th demo-player observation, whose construction is described in Section III-B; let _xi_<sup>seq</sup> denote the combat-window sequence representation produced by the sequence encoder in Section III-C. We take their concatenation 

where _gθ_ is the pairwise comparator to be learned and _θ_ denotes model parameters; _sij_ is the identity-consistency score. During training, _yij_ supervises _gθ_ . A higher score indicates stronger same-player consistency, and different-player retrieval uses the low-score side. 

In this paper, _cij_ only encodes map relation, such as samemap versus cross-map; it does not include demo IDs, match IDs, teammate/opponent identities, or other shared match identifiers. 

_B. Game-Understanding-Based Behavioral Fingerprint Features_ 

This section describes the construction of _xi_<sup>beh</sup> : from each demo-player observation we extract behavioral fingerprints based on CS2 game understanding to summarize the player’s operation and decision habits in one match. 

From the demo record we recover the player’s within-round position, view angle, movement state, weapon state, firing, damage, utility, and buy events, and express these behaviors at demo-player granularity as _xi_<sup>beh</sup> : a summary of behavioral frequency, time intervals, distribution shapes, and conditional relations that characterizes how a player moves, aims, fires, switches states, buys equipment, and uses utility across maps and round phases. In implementation, we extract 252 perdemo-player behavioral fingerprint features and organize them into eight sub-representations: 

Taking mechanics/state as an example, this feature type records not “how many duels were won” but how the player’s body state changes before firing. In CS2, stable shooting usually requires counter-strafing; some players fire only after completely stopping, while others fire early while moving. Aggregating such micro-transition habits over the full demoplayer observation expresses a player’s long-formed operation style. 

## _C. Sequential Behavioral Representation_ 

as the complete behavioral fingerprint. Let _pi_ denote the real-player label to which this observation belongs. Player labels are used only to construct training and evaluation samples; at test time, the model does not need to identify who _pi_ is. For any pair of observations, we define the pair label: 

where _yij_ = 1 denotes a same-player pair and _yij_ = 0 denotes a different-player pair. The model receives the endpoint fingerprints, the explicit comparison features compare( _xi, x j_ ) defined in Section III-D, and the pair-level context _cij_ , and outputs a consistency score: 

The behavioral fingerprint features in Section III-B efficiently summarize behavioral distributions that repeatedly appear in one match. However, similar firing counts, movement speeds, or utility counts can come from completely different round developments. For example, around the same combat, counter-strafing first and then micro-adjusting and firing, versus firing early while moving and then counterstrafing and micro-adjusting, reflect different movement-stopfire coordination but may look almost identical in the features above; likewise, after throwing a utility item, immediately pushing, waiting for a teammate to trade, or only delaying tempo represent different utility-combat coordination. 

We therefore encode action sequences, but not all ticks of the entire demo. A CS2 demo contains many rounds, and 

TABLE I 

GAME-UNDERSTANDING-BASED BEHAVIORAL FINGERPRINT FEATURE FAMILIES AND QUANTIFICATION EXAMPLES. 

|behavioral<br>layer|symbol|feature family|behavior captured|concrete quantification example|
|---|---|---|---|---|
|low-level|_x_<sup>beh-aim</sup><br>_i_|aiming/crosshair|view control, correction, recoil, aiming<br>stability|left-right crosshair correction switches around firing|
|low-level|_x_<sup>beh-mech</sup><br>_i_|mechanics/state|counter-strafe, walk/crouch/scope, state<br>switch|speed drop in the 250ms before each shot|
|low-level|_x_<sup>beh-combat</sup><br>_i_<br>|combat/engagement|shooting discipline, reload rhythm, fire output|reloads per 100 weapon fires|
|rhythm-space|_x_<sup>beh-move</sup><br>_i_|movement/positioning|opening route, position, map-space<br>preference|concentration of frequent opening positions|
|rhythm-space|_x_<sup>beh-util</sup><br>_i_<br>|utility usage|utility timing, type choice, follow-up|damage within 5 seconds after utility release|
|rhythm-space|_x_<sup>beh-time</sup><br>_i_|timing/rhythm|first contact, firing interval, push/wait rhythm|seconds from round start to first weapon fire|
|tactical|_x_<sup>beh-econ</sup><br>_i_|economy/buy|buy choice and risk under economic pressure|force-buy rate under insufficient economy|
|tactical|_x_<sup>beh-ctx</sup><br>_i_|context|early risk, man advantage/disadvantage, role<br>context|deaths in the first 20 seconds of a round|

large portions of a demo may contain weak identity signal; player identity is more concentrated in short operations around firing, taking damage, dealing damage, kills, and the moments before death. We thus extract local windows centered on combat events from each demo-player observation: around firing, dealing/taking damage, kills, and death events, we crop fixed-length tick sequences, with death-related evidence concentrated before the event. Each window is a 32 _×_ 16 continuous numerical tensor, where the 16 states include relative time, horizontal/vertical view-angle changes, aiming-change magnitude, movement speed and speed change, weapon speed modifier, crouch/walk/scope states, firing change, health, and before/during/after event position markers. 

Let _wim_ denote the _m_ -th combat window in observation _i_ . The sequence encoder _Eψ_ maps each window to a window embedding _him_ , and an aggregation function aggregate _ω_ summarizes them into a demo-player-level sequence embedding: 

where _Mi_ is the number of available combat windows in this observation; during training, each observation samples at most 24 windows. In our experiments, _Eψ_ is implemented as a Transformer encoder. 

## _D. Pairwise Comparison Representation_ 

After obtaining _xi_<sup>beh</sup> and _xi_<sup>seq</sup> , we concatenate them into the complete fingerprint _xi_ = [ _xi_<sup>beh</sup> _, xi_<sup>seq</sup> ]. If two raw fingerprints are simply concatenated and fed to the model, the model must infer both feature differences and endpoint levels from limited samples. We therefore add a set of symmetric comparison features that explicitly express relations such as absolute and relative differences between two demo-players on the same behavioral dimensions. 

Specifically, given two raw fingerprints _xi_ and _x j_ , we construct explicit comparison features compare( _xi, x j_ ). For each scalar feature _k_ , the comparison block contains: 

where _ε_ ensures numerical stability and **1** [ _·_ ] is the indicator function (1 when the bracketed condition holds, 0 otherwise); _⊕_ denotes exclusive OR. 

## _E. Account-History Aggregation_ 

Actual account-consistency checks usually compare not just two demos, but one current demo under review against multiple historical demos of the account. Based on the _sij_ defined in Section III-A, we compare the current observation _xq_ with each of the account’s _K_ historical observations _H_ = _{xh_ 1 _,..., xhK }_ , obtaining _K_ scores that describe the consistency between current behavior and account-history behavior: 

Multi-demo aggregation converts _K_ pairwise scores into an account-level consistency score. The most direct approach aggregates raw scores, such as the raw-score mean: 

We also evaluate an empirical LLR-style score transformation as an interpretable evidence scale for adding multiple pairwise scores. Based on the same / different score distributions on the training side, each pair score _s_ is mapped to an evidence value _ℓ_ ( _s_ ): 

where _b_ ( _s_ ) denotes the discrete bin to which the score belongs and _α_ is a smoothing term. Intuitively, _ℓ_ ( _s_ ) measures 

Fig. 1. Method overview: per-demo-player fingerprinting, pairwise scoring, and current-vs-history aggregation. 

how common a score bin is in the training-side same-player distribution relative to the different-player distribution: _ℓ_ ( _s_ ) _>_ 0 if the interval appears more often in same-player pairs, and _ℓ_ ( _s_ ) _<_ 0 if it appears more often in different-player pairs. We then average the evidence over the _K_ historical observations to obtain the account-level score: 

## _F. Overall Workflow_ 

Fig. 1 shows the main data flow at inference time: each demo-player observation is first encoded as a fingerprint, two fingerprints are compared to obtain _si j_ , and multiple currentvs-history scores are then aggregated into an account-level consistency score. Training mainly supervises the pairwise comparator _gθ_ . 

## IV. EXPERIMENTS 

## _A. Dataset and Evaluation Setup_ 

**Main data source and manual confirmation.** The main dataset uses active users from a university CS player guild on Perfect World Arena as the collection entry point. We downloaded their available CS2 match demos within a specified time window, forming 1,330 demos and 13,300 demo-player observations. The guild players cover 12 amateur competitive tiers from C to Diamond S and above. To obtain credible sameplayer positives, we contacted almost all active users in the guild and asked them to confirm whether the account was used only by themselves within the window, whether multiple accounts existed, and whether those accounts were all operated by the same real player. Observations with clear account borrowing, non-self play, uncertainty, or account-sharing risk do not enter same-player positives. 

**Supplemental professional identity source.** In addition to the main dataset, we downloaded public professional match demos from HLTV match/demo pages and built an extension 

dataset for professional players. This set contains 227 professional match demos and 2,270 professional match demoplayer observations, among which 631 target professional player observations correspond to 50 professional players. Professional identities come from public tournament records, providing externally verifiable high-level identity sequences and higher skill coverage; Section IV-E3 separately reports the expansion experiment after adding professional player demos to the training side. 

**Positive construction.** The 2,380 manually confirmed demo-player observations come from 64 confirmed persons and are used to construct same-player positives. For each confirmed person with _np_ available observations, we enumerate � _n_ 2 _p_ � same-player combinations; in total, 66,359 same-player pairs are formed. 

**Negative sampling.** Different-player pairs are sampled between observations with different person ids; observations manually confirmed to belong to the same real player or the same account group are first assigned to the same person id so they are not sampled as negatives. The 13,300 observations theoretically form �133002 � = 88 _._ 4M possible pairs, the vast majority different-player. We keep all 66,359 same-player pairs and randomly sample different-player pairs at 1:9, obtaining 663,590 pairwise samples. Precision, AP, and recall at fixed precision are therefore reported on this sampled evaluation distribution; deployment thresholds should be recalibrated on platform-specific data. 

**Split protocol.** To prevent the same real player from appearing on both training and test sides and causing identity leakage, we split train/test by person id; pairs crossing the training and test sides are discarded. 

**Map factor.** CS2 competitive matches concentrate on a small active-duty competitive map pool of roughly seven maps, including Dust2 and Mirage. Maps affect default routes, combat distances, and utility combinations; still, the same player is likely to retain stable habits such as crosshair control, firing rhythm, movement-stop-fire coordination, and risk preference across maps. We therefore verify both same-map and cross- 

TABLE II 

EVALUATION SETS AND METRICS USED IN THE EXPERIMENTS. 

|symbol|purpose|construction|size|metrics|
|---|---|---|---|---|
|_T_ <sup>(1:6)</sup><br>_pair_<br>|main pairwise verification<br>and high-precision<br>inconsistency retrieval|6 person-disjoint test splits, train/test<br>person overlap is 0<br>|each split<br>_N_=25_,_510–58_,_088 pairs|mean AUC, same-AP, F1, @95P recall|
|_T_ <sup>(1)</sup><br>_pair_|model family, PR curve,<br>and feature-sensitivity<br>analysis|the first test split in _T_ <sup>(1:6)</sup><br>_pair_|_N_=36_,_594 pairs = 14,028<br>same + 22,566 different|AUC / AP / F1 / @95P, PR curve,<br>sensitivity AUC|
|_Tpro_<br>|impact of<br>professional-player demo<br>expansion training set|construct professional same/different<br>training pairs from HLTV public<br>professional match demos<br>|_N_=29_,_060 pairs = 2,906<br>same + 26,154 different|∆AUC, ∆@95P recall|
|_T_ <sup>(1:6)</sup><br>_hist_<br>(_K_)<br>|account-level aggregation<br>of current demo against<br>multiple historical demos|for each split in _T_ <sup>(1:6)</sup><br>_pair_ <sup>, construct</sup><br>groups of one current observation and<br>_K_ history observations<br>|6-split mean: K=3<br>_N_=2_,_668, K=5 _N_=2_,_652,<br>K=10 _N_=2_,_354 groups|account AUC, @95P recall|
|_T_ <sup>(1)</sup><br>_time_<br>|recent-vs-history<br>cross-time comparison|retain pairs in _T_ <sup>(1)</sup><br>_pair_ <sup>with archive</sup><br>timestamp gap > 15 days<br>|_N_=6_,_857 pairs = 2,546<br>same + 4,311 different|AUC, AP, F1, @95P recall|
|_T_ <sup>(1)</sup><br>_map_|same-map and cross-map<br>robustness|split _T_ <sup>(1)</sup><br>_pair_ <sup>by map relation</sup>|same-map _N_=9_,_798 pairs;<br>cross-map _N_=26_,_796 pairs|AUC, AP, @95P recall|

TABLE III 

REPRESENTATION LADDER ON _T_<sup>(1:6)</sup> _pair_<sup>.</sup> 

|experiment|input representation|mean AUC|mean AP|mean F1|mean recall @95%P|
|---|---|---|---|---|---|
|E1|_x_<sup>out</sup><br>_i_<br>_,x_<sup>out</sup><br>_j _<sup>_,cij_</sup>|0.599|0.447|0.543|0.002|
|E2|_x_<sup>beh</sup><br>_i_<br>_,x_<sup>beh</sup><br>_j_<br>_,cij_|0.831|0.727|0.689|0.358|
|E3|_x_<sup>seq</sup><br>_i_<br>_,x_<sup>seq</sup><br>_j _<sup>_,cij_</sup>|0.723|0.575|0.605|0.110|
|E4|_x_<sup>beh</sup><br>_i_<br>_,x_<sup>seq</sup><br>_i_<br>_,x_<sup>beh</sup><br>_j_<br>_,x_<sup>seq</sup><br>_j _<sup>_,cij_</sup>|0.842|0.738|0.699|0.411|
|E5|_x_<sup>beh</sup><br>_i_<br>_,x_<sup>seq</sup><br>_i_<br>_,x_<sup>beh</sup><br>_j_<br>_,x_<sup>seq</sup><br>_j _<sup>_,_compare(</sup><sup>_xi,x j_)</sup><sup>_,cij_</sup>|**0.931**|**0.894**|**0.806**|**0.722**|

## map pairs. 

**Evaluation sets.** Table II gives the evaluation views used in this paper. The main pairwise conclusions use the six-split average of _Tpair_<sup>(1:6);</sup><sup>_T_</sup> _pair_<sup>(1),astheanalysissplit,carriesmodel-</sup> family, curve, and feature-sensitivity analysis. _Tpro_ tests the impact of adding professional-player demos to the training side; _Thist_<sup>(1:6)</sup> ( _K_ ) tests whether aggregating the current demo with _K_ historical demos forms more stable account-level evidence; _Ttime_<sup>(1)detectseffectdecayoverlongertimespans;</sup> _Tmap_<sup>(1)examinesrobustnessincross-mapcomparison.</sup> 

AP (Average Precision) summarizes the discrete area under the precision-recall curve; recall at 95% precision indicates how many true inconsistent pairs or account-history groups can be recovered under a high-confidence threshold. 

## _B. Behavioral Representations and Model Selection_ 

_1) Representation Levels: Which Information Brings Gains:_ Table III uses the average over _Tpair_<sup>(1:6)</sup> as the main pairwise result. On each split, the same LightGBM pairwise model [18] compares how much same-player consistency signal different input representations provide. E1 uses _x_<sup>out</sup> , i.e., outcome/performance-only features, including result-based statistics such as K/D (kill/death ratio), damage, score (game scoreboard score), headshot rate, and first kill / first death. E5 corresponds to the full pairwise input in Eq. (3) in Section III-A. 

E1, using only result-based statistics, is a weak baseline at AUC 0.599. Switching to _x_<sup>beh</sup> in E2 raises AUC to 0.831, showing that behavioral dimensions such as crosshair control, movement-stop-fire coordination, combat rhythm, economy/buy, and round timing are closer to player identity than performance outcomes. E3, using the sequence representation _x_<sup>seq</sup> alone, reaches AUC 0.723, indicating that action order in combat windows carries identity information; but its information density is lower than E2 and it cannot alone cover the operation and decision habits that recur across rounds. 

Compared with E2, E4 combines _x_<sup>beh</sup> and _x_<sup>seq</sup> , improving AUC by 0.011 on average (+0.018/0.004/+0.014/+0.005/+0.035/-0.005) and @95% precision recall by 0.053 on average (+0.071/0.008/+0.090/+0.039/+0.140/-0.013). The two are complementary: behavioral fingerprints summarize operation and decision distributions that recur across rounds, while sequence embeddings preserve action order in combat windows. 

The final jump comes from explicit pairwise comparison. Compared with E4, E5 improves AUC by 0.089 on average (+0.102/+0.097/+0.069/+0.104/+0.078/+0.085) and @95% precision recall by 0.310 on average (+0.389/+0.372/+0.224/+0.359/+0.248/+0.271). With explicit comparison features, the model directly uses absolute and relative differences on the same behavioral dimensions. 

TABLE IV 

MODEL-FAMILY CHECK FOR THE INPUT IN EQ. (3) ON _Tpair_<sup>(1).</sup> 

|input representation|model|training note|ROC AUC|same-player AP|best F1|different recall @95%P|
|---|---|---|---|---|---|---|
|_x_<sup>beh </sup>+_x_<sup>seq </sup>+compare(_xi,x j_)+_cij_|LightGBM|final representation|**0.955**|**0.936**|**0.855**|**0.816**|
|same as above|XGBoost|model-family check|0.951|0.930|0.845|0.795|
|same as above|fast MLP|controlled diagnostic|0.854|0.787|0.727|0.270|
|same as above|rank-avg ensemble|rank-score average|0.944|0.918|0.832|0.762|

When sample size is limited and behavioral features are heterogeneous, explicit comparison features spare the model from learning symmetric difference relations on its own. 

_2) Model Selection and High-Precision Inconsistency Retrieval:_ **Sequence feature model selection.** The _x_<sup>seq</sup> in Eq. (5) in Section III-C is produced by a separately trained Transformer sequence encoder. We compared discrete token sequences, continuous numerical combat-window sequences, and different window-aggregation and pair-readout methods; on the current data, the continuous numerical combat-window Transformer is the most stable, and other routes do not exceed it. This encoder is trained with player identity labels, models action order around combat windows, and aggregates multiple windows into a demo-player-level sequence representation, which then enters the final pairwise input together with the game-understanding-based _x_<sup>beh</sup> . 

**Pairwise model selection.** Table IV compares the finallayer pairwise model on _Tpair_<sup>(1).Allmodelsusethesameinput</sup> representation _x_<sup>beh</sup> + _x_<sup>seq</sup> + compare( _xi, x j_ )+ _ci j_ . We compare tree-based pairwise models (LightGBM [18], XGBoost [19]), a neural pairwise model (fast MLP; we also tried several MLP variants and projection-then-distance-comparison NN schemes, but did not find stronger results), and a rank-average ensemble (averaging the ranking scores of multiple models). 

LightGBM is strongest on _Tpair_<sup>(1),withXGBoostclose</sup> behind. Fast MLP is clearly weaker, indicating that at the current data scale tree-based models more stably use continuous statistics, sparse indicators, map information, and explicit differences. Because the ranking-quality gap between NN and tree models is relatively large, the rank-average ensemble does not exceed the single strongest model. 

Here _T_<sup>(1)</sup> _pair_<sup>is the analysis split; its AUC 0.955 is higher than</sup> the six-split mean AUC 0.931 reported as the main pairwise result. 

Our final implementation therefore uses gameunderstanding-based behavioral fingerprints, Transformerderived sequence representation, and a LightGBM pairwise scorer. 

After the model-family comparison, Fig. 2 shows the different-player retrieval precision-recall curve on _Tpair_<sup>(1),il-</sup> lustrating the threshold tradeoff in the high-precision region. The LightGBM final representation reaches best F1 0.855; at 95% precision it still recalls about 0.816 of different-player pairs. In other words, under a low false-positive budget the model still discovers a large share of true behavior-inconsistent 

Fig. 2. Different-player retrieval precision-recall curves on _Tpair_<sup>(1).</sup> 

comparisons, making it useful for account-history consistency review. 

_C. Feature-Family Sensitivity: Which Behaviors Carry Identity Signal_ 

Table V reports both the eight-feature-family sensitivity on _Tpair_<sup>(1:6)</sup> and the feature-layer analysis after merging by behavioral mechanism on _T_<sup>(1)</sup> _pair_<sup>, summarizing the features that</sup> most support the behavioral findings. 

TABLE V 

KEY FEATURE-FAMILY AND LAYER SENSITIVITY. 

|setting|evaluation|ROC AUC (∆vs<br>same-setting full)|
|---|---|---|
|full _x_<sup>beh</sup>|_T_ <sup>(1:6)</sup><br>_pair_<br>|**0.929 (0)**|
|remove _{x_<sup>beh-aim</sup>_}_ aiming/crosshair|_T_ <sup>(1:6)</sup><br>_pair_<br>|**0.855 (-0.074)**|
|only _{x_<sup>beh-aim</sup>_}_ aiming/crosshair|_T_ <sup>(1:6)</sup><br>_pair_<br>|**0.883 (-0.047)**|
|remove _{x_<sup>beh-mech</sup>_}_ mechanics/state|_T_ <sup>(1:6)</sup><br>_pair_<br>|0.914 (-0.016)|
|full _x_<sup>beh</sup>|_T_ <sup>(1)</sup><br>_pair_<br>|**0.953 (0)**|
|only _{x_<sup>beh-aim</sup>_,x_<sup>beh-mech</sup>_,x_<sup>beh-combat</sup>_}_ low-level<br>|_T_ <sup>(1)</sup><br>_pair_|**0.946 (-0.007)**|
|operations<br>remove _{x_<sup>beh-aim</sup>_,x_<sup>beh-mech</sup>_,x_<sup>beh-combat</sup>_}_|_T_ <sup>(1)</sup><br>_pair_|**0.779 (-0.175)**|
|low-level operations<br>remove _{x_<sup>beh-move</sup>_,x_<sup>beh-util</sup>_,x_<sup>beh-time</sup>_}_ rhythm<br>|_T_ <sup>(1)</sup><br>_pair_|0.952 (-0.001)|
|and space<br>remove _{x_<sup>beh-econ</sup>_,x_<sup>beh-ctx</sup>_}_ tactics and context|_T_ <sup>(1)</sup><br>_pair_|0.950 (-0.004)|

Table V shows that aiming/crosshair is the strongest identity signal. The 6-split average AUC of the full _x_<sup>beh</sup> is 0.929; removing aiming/crosshair lowers AUC by 0.074 on average (-0.099/-0.059/-0.061/-0.084/-0.067/-0.073). Using only the 

TABLE VI 

ACCOUNT-HISTORY AGGREGATION AS HISTORY DEPTH _K_ CHANGES. 

|symbol|K|mean LLR AUC (∆vs K=1)|split AUCs (rounded)|different recall @95%P (∆vs K=1)|
|---|---|---|---|---|
|_T_ <sup>(1:6)</sup><br>_pair_<br>|1|**0.931 (baseline)**|0.955/0.928/0.921/0.946/0.902/0.934|**0.722 (baseline)**|
|_T_ <sup>(1:6)</sup><br>_hist_<br>(3)<br>|3|0.971 (+0.040)|0.986/0.969/0.945/0.986/0.968/0.972|0.961 (+0.239)|
|_T_ <sup>(1:6)</sup><br>_hist_<br>(5)<br>|5|0.980 (+0.049)|0.989/0.981/0.966/0.990/0.976/0.979|0.985 (+0.263)|
|_T_ <sup>(1:6)</sup><br>_hist_<br>(10)|10|**0.986 (+0.055)**|0.990/0.984/0.979/0.995/0.979/0.992|**0.988 (+0.266)**|

aiming/crosshair family still reaches AUC 0.883, only 0.047 below the full representation and clearly stronger than other single families; mechanics/state is the second tier. 

Merging the eight feature types by behavioral mechanism concentrates the conclusion: on _T_<sup>(1)</sup> _pair_<sup>,usingonlyaim-</sup> ing/crosshair, mechanics/state, and combat/engagement lowers AUC by only 0.007, while removing these three lowers AUC by 0.175. This agrees with the eight-family results: CS2 player identity signals come mainly from crosshair control, combat micro-operations, and movement-stop-fire coordination, while rhythm, space, buying, and context preferences provide supplementary information. 

_D. Account-History Aggregation: From Pairwise Scores to Multi-Demo History Comparison_ 

Account-history review compares a current demo against multiple historical demos. Table VI reports account-history aggregation on _Thist_<sup>(1:6)</sup> ( _K_ ): each group is constructed within the held-out side of a person-disjoint split, using one current observation and _K_ historical observations; the group label follows whether the current observation comes from the same person as the historical reference. The mean LLR in Eq. (10) in Section III-E then aggregates the _K_ pairwise scores into an account-level consistency score. 

The median time gap is 18.96 days, p90 is 24.68 days, and the maximum is 31.07 days. 

Table VII shows that _Ttime_<sup>(1)isharderthan</sup><sup>_T_</sup> _pair_<sup>(1),withAUC</sup> about 0.008 lower. This is consistent with intuition: over longer gaps, the same player’s state, map pool, and play style may change, yet the model retains strong cross-time recognition under the high-precision threshold. 

_2) Cross-Map Robustness:_ Same-map pairs usually have higher recognition accuracy; cross-map pairs are closer to real account-history review, because same-map samples are usually fewer in account history, and longer time spans further increase recognition difficulty. 

Table VIII shows that the map factor affects judgment difficulty: same-map AUC is about 0.020 higher than _Tpair_<sup>(1),</sup> and cross-map AUC about 0.008 lower. Same-map comparison provides relatively stronger evidence, while cross-map comparison is harder but remains usable. 

Multi-demo history comparison provides a more stable account-level signal than a single pairwise score: a particular match may shift because of map, teammates, weapons, opponents, or the player’s state that day, but multiple historical demos provide a more stable behavioral reference. Compared with K=1, mean LLR AUC rises from 0.931 to 0.971 at K=3 and 0.986 at K=10. Raw-score mean gives very similar AUC, so the main gain comes from accumulating multiple pairwise evidence rather than from a specific aggregation formula. In practical terms, under a high-confidence threshold maintaining 95% precision, K=5 and K=10 already recall about 98.5% and 98.8% of true behavior-inconsistent account-history groups, showing that multi-demo comparison can substantially reduce misses caused by single-match fluctuation. 

_E. Cross-Time, Cross-Map, and Data Expansion Experiments_ 

_1) Time Gap and Cross-Window Evaluation:_ Actual review often occurs with larger time gaps: a platform or tournament organizer obtains a recent suspicious demo and compares it with earlier historical demos of the account. This setting is harder than random pairs, because player state, map pool, version, settings, and play style may all change over time. 

TABLE VII COMPARISON BETWEEN _Ttime_<sup>(1)AND</sup><sup>_T_</sup> _pair_<sup>(1).</sup> 

|evaluation set|pairs|AUC|AP|best F1|different recall @95% precision|
|---|---|---|---|---|---|
|_T_ <sup>(1)</sup><br>_pair_<br>|36,594|**0.955**|**0.936**|**0.855**|**0.816**|
|_T_ <sup>(1)</sup><br>_time_|6,857|0.947|0.921|0.838|0.771|

TABLE VIII SAME-MAP VS CROSS-MAP SENSITIVITY ON _Tmap_<sup>(1).</sup> 

|evaluation set / map relation|pairs|same|different|AUC (∆vs all)|AP (∆vs all)|different recall @95%P<br>(∆vs all)|
|---|---|---|---|---|---|---|
|_T_ <sup>(1)</sup><br>_pair_ <sup>all pairs</sup><br>|36,594|14,028|22,566|**0.955**|**0.936**|**0.816**|
|_T_ <sup>(1)</sup><br>_map_ <sup>same-map</sup><br>|9,798|3,623|6,175|**0.975 (+0.020)**|**0.963 (+0.027)**|**0.916 (+0.100)**|
|_T_ <sup>(1)</sup><br>_map_ <sup>cross-map</sup>|26,796|10,405|16,391|0.947 (-0.008)|0.925 (-0.011)|0.773 (-0.043)|

_3) Training Expansion Experiment with Public Professional Demos:_ We test whether introducing public professional match identity sequences in _Tpro_ can improve training coverage and model performance. 

The results do not support the conclusion that adding professional demos stably improves the main model. After adding professional positives and negatives, LightGBM AUC / @95% precision recall change by -0.005 / -0.019, respectively; the corresponding changes for XGBoost are 0.000 / +0.005. When adding only professional positives, LightGBM is basically flat (-0.002 / 0.000), while XGBoost has a small improvement (+0.002 / +0.008). One likely explanation is distribution shift: team roles, tactical execution, match intensity, and player behavior stability in professional matches all differ from the current platform matches. Assessing professional-demo augmentation therefore requires larger high-skill samples closer to the target platform distribution. 

## V. DISCUSSION AND LIMITATIONS 

## _A. Evaluation Boundaries_ 

Our primary split is person-disjoint, so the test players are unseen during training. The protocol targets unseen-player consistency, but it is not match-disjoint: different players from the same demo may appear on different sides. The model input is restricted to per-player fingerprints and a same-map/cross-map flag; it excludes demo IDs, match IDs, teammate/opponent identities, and shared-match identifiers. As an additional sanity check, removing same-demo pairs within _T_<sup>(1)</sup> _pair_<sup>changesAUCfrom0.955to0.952andAPfrom0.936</sup> to 0.937. This check targets same-demo co-occurrence within the test set rather than full match-disjoint evaluation, and the reported protocol should be interpreted as person-disjoint and observation-disjoint evaluation. 

Pairwise construction makes players with more observations contribute more pairs, so pair-level uncertainty can be too narrow. We therefore report player-clustered bootstrap as a diagnostic; it gives wider intervals but does not change the core conclusions. 

## _B. Data and Label Boundaries_ 

The labels remain a source of uncertainty. Same-player labels mainly come from manually confirmed account histories and public professional identities; different-player labels come from identity mappings and negative-sampling rules. Some different-player negatives may be noisy if two accounts are operated by the same real player but not captured in the identity mapping. Account sharing, multi-account use, and temporary substitution can contaminate both types of labels, so deployment needs to retain human confirmation, label audit, and new-evidence feedback, and cannot treat a one-time dataset as permanent truth. 

## _C. Practical Deployment: Historical Reference Quality, Runtime Cost, and Responsible Use_ 

Account-history aggregation depends on a practical premise: the historical demos used for comparison should mainly come from the same real player. If the history has already mixed multiple operators, the aggregation score between the current demo and this history set will be contaminated. The deployment workflow should therefore first perform a history self-consistency audit: compute history-history pairwise scores within the same account history and judge whether this history set can serve as a reference. 

Runtime cost also determines deployment form. The current runtime benchmark shows that demo parsing and feature extraction are the main offline costs; on a small representative subset, parsing and feature extraction are at the level of seconds per demo, but the exact throughput depends on demo length, parallelism, and I/O conditions. Once fingerprints / sequence embeddings are available, pairwise scoring and account-history aggregation are lightweight: about 24k pairs per second on Apple M4. 

In deployment, a new demo can be compared with historical observations to prioritize cases where current behavior is clearly inconsistent with the account history. 

## VI. CONCLUSION AND FUTURE WORK 

This paper starts from account-history consistency review on competitive FPS platforms and formalizes “whether the current match is still behaviorally consistent with the account history” as open-set same-player verification. We use CS2 demos to design per-demo-player behavioral fingerprints and learn pairwise same-player consistency. 

Experiments show that this formulation supports accurate pairwise verification with lightweight scoring after fingerprint extraction: the game-understanding-based behavioral fingerprint + Transformer sequence model + pairwise model reaches an average ROC AUC of 0.931 and achieves 0.722 differentplayer recall at 95% precision. Feature analysis further shows that the identity signal comes mainly from low-level operations, especially crosshair control, firing rhythm, and movement-stop-fire coordination; stable play habits such as state switching, buying rhythm, and round positioning/rhythm provide supplementary information. These low-level operations are less directly controllable than outcome statistics and may be harder to imitate consistently. After aggregating multiple historical demos, mean LLR account-history aggregation raises AUC from 0.931 at K=1 to 0.986 at K=10, providing an account-history behavioral analysis method for platform and tournament review. 

Future work should expand data scale and time span, adapt the feature design to other competitive FPS games such as Valorant, PUBG / Apex Legends, and Rainbow Six Siege, extend post-match demo-level verification toward streaming partialmatch verification, and evaluate human-machine collaboration in platform or tournament review workflows. 

## AI USE DISCLOSURE 

Generative AI tools were used for language editing and formatting assistance; all technical claims, experimental results, figures, tables, citations, and final text were manually verified by the author. 

## REFERENCES 

- [1] Valve, “Counter-Strike 2,” Steam Store. [Online]. Available: https://store. steampowered.com/app/730/CounterStrike_2/ 

- [2] SteamDB, “Counter-Strike 2 Steam Charts.” [Online]. Available: https: //steamdb.info/app/730/charts/ 

- [3] E. Conroy, M. Kowal, A. J. Toth, and M. J. Campbell, “Boosting: Rank and skill deception in esports,” _Entertainment Computing_ , 2021. 

- [4] J. Blackburn, N. Kourtellis, J. Skvoretz, M. Ripeanu, and A. Iamnitchi, “Cheating in online games: A social network perspective,” _ACM Trans. Internet Technol._ , 2014. 

- [5] FACEIT, “FACEIT Banning Policy.” [Online]. Available: https://support. faceit.com/ 

- [6] FACEIT, “The Verification Process.” [Online]. Available: https://support. faceit.com/ 

- [7] F. Zimmer _et al._ , “Player behavior analysis for predicting player identity within pairs in esports tournaments: A case study of Counter-Strike using binary Random Forest classifier,” in _Proc. HICSS_ , 2025, doi: 10.24251/HICSS.2025.513. 

- [8] F. Zimmer _et al._ , “Fair Play and Identity: In-game behavioral biometrics for player identification in competitive online games,” in _Proc. IEEE Conf. Games (CoG)_ , 2025, doi: 10.1109/CoG64752.2025.11114281. 

- [9] J. Orlova, A. Stepanov, and A. Somov, “GUARD: Enabling fair gaming through the gameplay analysis using machine learning methods and expert knowledge,” _Expert Systems with Applications_ , 2026, doi: 10.1016/j.eswa.2025.130908. 

- [10] D. Liu, X. Gao, M. Zhang, H. Wang, and A. Stavrou, “Detecting passive cheats in online games via performance-skillfulness inconsistency,” in _Proc. DSN_ , 2017. 

- [11] S. Yuen, J. D. Thomson, and O. Don, “Automatic player identification in Dota 2,” arXiv, 2020. 

- [12] S. Liu, C. Ballinger, and S. J. Louis, “Player identification from RTS game replays,” in _Proc. CATA_ , 2013. 

- [13] I. Stylios, S. Kokolakis, O. Thanou, and S. Chatzis, “Behavioral biometrics and continuous user authentication on mobile devices: A survey,” _Information Fusion_ , vol. 66, pp. 76–99, 2021. 

- [14] A. Mahfouz, T. M. Mahmoud, and A. S. Eldin, “A survey on behavioral biometric authentication on smartphones,” _Journal of Information Security and Applications_ , vol. 37, pp. 28–37, 2017. 

- [15] V. Nair _et al._ , “Unique identification of 50,000+ virtual reality users from head and hand motion data,” in _Proc. USENIX Security_ , 2023. 

- [16] M. Mohamed and N. Saxena, “Gametrics: Towards attack-resilient behavioral authentication with simple cognitive games,” in _Proc. ACSAC_ , 2016, pp. 277–288. 

- [17] C. Lesaege, F. Schnitzler, A. Lambert, and J.-R. Vigouroux, “Time-aware user identification with topic models,” in _Proc. IEEE ICDM_ , 2016, pp. 997–1002. 

- [18] G. Ke _et al._ , “LightGBM: A highly efficient gradient boosting decision tree,” in _Advances in Neural Information Processing Systems_ , 2017. 

- [19] T. Chen and C. Guestrin, “XGBoost: A scalable tree boosting system,” in _Proc. ACM SIGKDD_ , 2016, pp. 785–794.
