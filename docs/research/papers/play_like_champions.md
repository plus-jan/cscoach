---
id: play_like_champions
title: 'Play Like Champions: Counterfactual Feedback Generation in Latent Space'
authors: Andrzej Białecki, Adam Mastalerz, Han Zhou
year: 2026
venue: arXiv preprint
url: https://arxiv.org/abs/2607.00190
arxiv_version: 2607.00190v1
license: 'arXiv — not verified for redistribution (data: SC2EGSet CC BY 4.0)'
pdf_sha256: 9cb28eaf490e4462
converted: '2026-09-28'
converter: pymupdf4llm
---

# Play Like Champions: Counterfactual Feedback Generation in Latent Space

> Auto-converted from PDF. Tables, equations and figure text may be garbled — check the original PDF before quoting numbers.

<!-- cscoach-notes:start -->
## cscoach notes (hand-written — preserved on re-conversion)
**Authors:** Białecki (Warsaw UT), Mastalerz (Silesian UT), Zhou (UBC). arXiv 2607.00190v1. Code, tensors and
checkpoint: anonymous.4open.science/r/SC2_LatentTrainer-1E5B; data: SC2EGSet (Hugging Face, CC BY 4.0).

- **Relevance:** medium, as a **design warning and pattern** for counterfactual feedback (M9.2, A-04,
  docs/specs/05). StarCraft II, not CS.
- **Verified claims:**
  - Data: SC2EGSet, **professional** tournament replays: 23,476 files, of which 23,305 were usable
    (18,780 / 2,347 / 2,178), split **randomly** 80/10/10. OOD test: 2,178 amateur replays from
    sc2replaystats (unreleased).
  - Features per player (196): economy tracker statistics averaged over the early/middle/late thirds,
    **the final economy state**, and late − early differences.
  - Model: a Guided VAE. Some latent dimensions are supervised by the **match outcome**, and an
    adversarial classifier is trained on the rest.
  - Classifier (Table 1): accuracy 98.76%, ROC-AUC 0.9991, Brier 0.0090. On amateur OOD data: 97.11%,
    AUC 0.9926.
  - Four latent paths from loss to win (Table 2, OOD success rate = the share of paths that reach
    P(win) ≥ 0.5):
    - linear interpolation: 0.715 (centroid) / 0.543 (k-NN);
    - optimal transport: 0.720, crossing earliest (α 0.14) with monotone paths;
    - neural flow matching: 0.731;
    - gradient ascent: 0.998, but it **drifts off the data manifold** (larger latent norm, lower KDE
      density, monotonicity 0.75). The authors say it "exploits classifier blind spots".
  - Feedback has three signals: full-path change, **minimum viable change** (stop at the first waypoint
    with P(win) > 0.5), and WP-weighted change (Appendix F).
  - **Limitations stated by the authors:** no human validation; game patches ignored; no race
    information; the feedback is not tied to specific in-game actions.
- **Critical reading:**
  - The classifier's near-perfect AUC comes from **outcome-proxy features** such as
    `final_mineralsKilledArmy` and final army values, measured at game end. The "advice" is then largely
    "have killed more / have a bigger army", which is descriptive, not actionable.
  - The split is random, and "counterfactual" means movement in a latent space, not a causal
    intervention.
  - The synthesis's claims (KL divergence/EMD giving the "absolutely minimal change") overstate what
    the paper shows.
- **Corrections vs. synthesis:** "23,476 amateur and pro replays" → training uses only **pro**
  replays (23,305 usable of 23,476 files); amateurs are only an OOD test set.
- **Use in project (docs/specs/05, M9.2, MV.10):**
  - **Actionability rule:** counterfactuals may only change **decision variables available before the
    decision** (buy, duel taken or not, utility timing, position), never outcome proxies (kills,
    damage dealt, round result).
  - **On-manifold rule:** counterfactual states must be supported by observed CSDS states (near-twin
    matching or density checks). Unconstrained optimisation over the model is forbidden.
  - **Minimum viable change** + ranked signals as the output pattern.
  - Validation with humans is still needed (M9.5) and effectiveness is untested (A-03, M11).
- **Caveats:** a different genre; preprint; no uncertainty on the path metrics beyond ±SD.
<!-- cscoach-notes:end -->

## Full text

# PLAY LIKE CHAMPIONS: COUNTERFACTUAL FEEDBACK GENERATION IN LATENT SPACE 

A PREPRINT 

**Andrzej Białecki**<sup>_∗_,1</sup> , **Adam Mastalerz**<sup>_∗_,2</sup> , **Han Zhou**<sup>_∗_,3</sup> 

1Warsaw University of Technology 

2Silesian University of Technology 

3University of British Columbia 

### **ABSTRACT** 

Recent advances in reinforcement learning have produced superhuman agents across a wide range of competitive games. As a byproduct, researchers have begun studying how these agents play, extracting behavioral representations, analyzing decision structure, and modeling the latent geometry of expert performance. However, this growing body of work has overwhelmingly focused on defeating human players rather than providing feedback, leaving a critical gap in creating model solutions to improve human players. Unlike chess and Go, where AI has become integral to player training, real-time strategy (RTS) games lack principled frameworks for translating expert knowledge into actionable feedback. We introduce Latent Maps of Performance, a framework for counterfactual path generation. We focus on StarCraft II data to model player improvement as an algorithmic recourse within a learned representation space. As inspiration for our work, we have looked at the championship model used in sports science. We trained a Guided Variational Autoencoder model on 23,305 professional tournament replays, with macro-economic gameplay structure conditioned on match outcome, enabling counterfactual traversal between losing and winning gameplay profiles. To fulfill our goal, we have devised and verified four traversal strategies on out-of-distribution (OOD) data randomly sampled from a dataset of amateur replays, namely linear interpolation, iterative optimal transport, density-regularized gradient ascent, and neural flow matching, each designed to generate multi-step improvement trajectories that remain grounded in observed expert behavior while moving a player’s profile toward winning configurations. Feedback is extracted at multiple granularities to support players at different stages of improvement. Finally, we conclude that there is a trade-off between the path-finding methods we employ and hope that future research will focus on developing model solutions for human improvement. 

**_Keywords_** generative artificial intelligence _·_ latent space traversal _·_ optimal transport _·_ variational autoencoder _·_ esports 

### **1 Introduction** 

Mastering real-time strategy (RTS) games such as StarCraft II has long stood as a grand challenge for artificial intelligence, one only partially addressed by recent advances in reinforcement learning (RL) [1, 2]. The difficulty stems from the cognitive demands these games place on their players: precise control of units, careful management of economies, and continuous decision-making in adversarial settings where even momentary lapses can prove decisive. Success thus hinges on the interplay of multitasking, strategic foresight, and rapid reaction [3], making RTS an especially rich testbed for studying intelligent behavior. These high-frequency interactions make RTS games especially well-suited for large-scale behavioral study through open-source replay parsers and direct game-engine access [4, 5]. A growing body of work leverages data to surface game information for player decision support, both through digital interfaces and physical prototypes [6]. In StarCraft II, community tools such as sc2replaystats [7] and replayman [8] have emerged to support replay analysis, alongside real-time dashboards that contextualize gameplay for spectators and post-match review [9]. Strategic summaries and encounter-level analysis are highly valued by players across genres [10]. Game 

> *contact (in-order): `andrzej.bialecki94@gmail.com` , `adam.mastalerz@polsl.pl` , `hzhou30@student.ubc.ca` 

Play Like Champions: Counterfactual Feedback Generation in Latent Space 

A PREPRINT 

state retrieval by similarity to estimate win probabilities on demand is a possibility [11]. In parallel, AI methods have become deeply embedded in game research and development, powering procedural content generation [12], voicedriven agents that deepen immersion [13], human-like behavior modeling [14], and automated quality assurance [15]. However, most existing analysis tools remain oriented toward broadcast and streaming audiences rather than the players themselves [16]. 

This player-facing gap is not unique to gaming. In robotics, efficient simulators have driven dramatic breakthroughs [17, 18], producing systems that now rival or exceed human performance in domains as varied as drone racing [19, 20], badminton [21, 22], and table tennis [23]. Such interdisciplinary efforts are increasingly recognized as accelerators of research progress [24]. However, despite agents and robotic systems consistently surpassing average human ability, few of these works offer mechanisms to translate the resulting expertise back to human practitioners seeking to improve. The skill translation problem is well understood in the sport sciences, where the championship model describes how athletes shorten the path to performance gains by adopting the training methods, techniques, and tactics of successful peers [25, 26]. In domains where the competitive space is naturally digitized, this dynamic increasingly extends to AI. In chess, AI has reshaped human learning by serving as a scalable training partner. Analyses show that elite human play has steadily improved across the engine era [27–29]. AlphaZero’s games further illustrate how superhuman agents can surface novel strategic ideas for human study [30]. Similar patterns have emerged in Go following the rise of superhuman agents [31, 32]. 

RTS games share the same computational substrate, but, to our knowledge, no comparable bridge exists between agent expertise, representational learning, and human improvement. In this work, we introduce a latent-space feedback system that learns compressed representations of quantitative gameplay features from StarCraft II replays and provides manifold-aware improvement guidance to players. Our contribution is a framework for training representational models that recover counterfactual improvement trajectories and reconstruct them back into the original feature space. Given a well-trained model, points sampled along an “improvement trajectory” in latent space can be decoded and compared with the player’s input vector, yielding immediate feedback on which gameplay features need to change to improve performance, as determined by the model. Our work builds directly on “SC2EGSet”, rather than asking “ _who will win_ ”, we ask “ _what the player should do differently_ ”. 

### **2 Related Work** 

Our work sits at the intersection of four research threads: StarCraft II as a machine learning domain; variational autoencoders and disentangled representation learning; latent space traversal; and counterfactual explanations as actionable feedback. We discuss each in turn and position our contribution relative to prior art. 

**StarCraft II as a Machine Learning Domain:** StarCraft II has become a canonical benchmark for sequential decisionmaking under partial observability. Vinyals et al. [33] demonstrated that a combination of imitation learning, multi-agent self-play, and a latent conditioning variable for strategy style can produce grandmaster-level play, establishing that large-scale replay data contains rich, learnable structure. However, AlphaStar is an autonomous agent; it optimizes for winning, not for explaining to human players how to improve. On the other hand, the simplistic nature of benchmarks geared primarily towards multi-agent solutions does not fit well in the context of providing feedback to players [34, 35]. Work on modeling player skill from replays predates AlphaStar. Avontuur et al. [36] showed that even simple classifiers trained on APM and economy features can predict a player’s league with meaningful accuracy. Subsequent work demonstrated that macro-level economic measures, such as the Spending Quotient introduced by Bowman et al. [37], are among the strongest predictors of both skill and match outcomes. 

**Variational Autoencoders and Disentangled Representations:** Naturally, the Variational Autoencoder (VAE) [38] acts as the backbone for our work. By learning a probabilistic encoder and decoder jointly with a Kullback-Leibler (KL) divergence regulariser, the VAE produces a smooth, continuous latent space from which new samples can be reconstructed. As an extension, Higgins et al. [39] introduced _β_ -VAE, and addressed the interpretability by up-weighting the KL term. The _β_ factor was applied to force the model to trade reconstruction fidelity for statistical independence between latent dimensions. Guided VAE addresses this in a direct manner Ding et al. [40]. It attaches a supervised classifier to designated latent dimensions, and uses an adversarial excitation-inhibition mechanism to concentrate the target factor in that dimension while preventing it from leaking into the remaining dimensions. Schrum et al. [41] presented “SAIL”, which learns persistent skill embeddings from naturalistic behavioral data using expert-novice basis blending and counterfactual subskill swaps applied to motor tasks such as driving and baseball batting. We draw inspiration and intuition from these works. 

**Latent Space Traversal:** Generating semantically meaningful paths through a learned latent space is a non-trivial problem. Naive linear interpolation between two latent codes can pass through low-density regions of the prior, leading to decoded samples that lie outside the data manifold. Korkmaz et al. [42] formalize this distribution mismatch and show that optimal transport (OT) maps can correct linear trajectories so that all intermediate points remain consistent 

2 

Play Like Champions: Counterfactual Feedback Generation in Latent Space 

A PREPRINT 

with the prior distribution while minimally deviating from a straight line. Song et al. [43] propose a more general framework that models latent structures as learned dynamic potential landscapes, deriving traversal trajectories as the gradient flow of a partial differential equation (PDE)-based potential field. Yeh et al. [44] take a related approach in the explainability domain with partial focus on StarCraft II by leveraging a fixed “SC2 Assault” scenario. They generate counterfactuals from a jointly trained generative latent space where the traversal is guided toward a target outcome during decoding. 

**Counterfactual Explanations as Actionable Feedback:** Counterfactual explanations answer the question: “ _what is the minimal change to the input that would change the model’s prediction?_ ” In a performance-improvement context, this is equivalent to algorithmic recourse. Providing a ranked list of feature changes that move a player from their current state to a more desirable one. Crupi et al. [45] proposed “CEILS”, generating counterfactuals as interventions in the latent space of a trained VAE [45]. Work beyond passive explanation towards actionable coaching was shown by Bae et al. [46], leveraging counterfactual explanations in racing scenarios with language-based guidance. Pegios et al. [47] extend latent-space counterfactual generation by equipping the VAE latent space with a Riemannian metric pulled back through both the decoder and the classifier. 

### **3 Material and Methods** 

**Replay Preprocessing and Feature Extraction:** To fulfill our goal of providing feedback based on learned representations, we have decided to use a dataset consisting of professional StarCraft II games named “SC2EGSet” [4] licensed under CC-BY 4.0. Please refer to Appendix A for a simplified game description. At the time our work was prepared, the dataset consisted of 23,476 files containing game-state information sourced from 71 “replaypacks”. Before training, each replay is converted into a tensor containing information about both players. For every player, we extract a 196-dimensional feature vector R<sup>196</sup> . Selected features primarily include economical game progression statistics that inform various aspects of the game. Additionally, for more expressive modeling insights, we split the array of player statistics into three windows, each spanning one-third of the total game duration. These features are named as “early”, “middle”, and “late game” windows (3 _·_ 39 features). Tracker statistics averaged within each window. Finally, we include the final economy state (39 features) and the economy difference features (39 features), computed as late-game economy minus early-game economy. Besides the economy, we include a scalar value, “supply capped percent”, denoting the percentage of the game duration during which the player was unable to build additional units due to insufficient in-game infrastructure. The final replay tensor has shape R<sup>2</sup><sup>_×_196</sup> , where the first dimension corresponds to the player. The label used for disentanglement is the match result from player 0’s perspective, represented as a binary outcome _y ∈_ 0 _,_ 1, where _y_ = 1 indicates that player 0 won. Prior to training, all features are standardized using per-feature z-score normalization. The normalization statistics (mean and standard deviation) are computed exclusively on the training set and subsequently applied to the validation and test sets, preventing any data leakage. A small epsilon ( _ϵ_ = 10<sup>_−_8</sup> ) is added to each standard deviation to avoid division by zero for constant features. 

The initial split between training, validation, and test sets was random (80%/10%/10%). Replays with missing player statistics, player information, or undecided/draw outcomes were skipped. Finally, to assure that the training, and validation sets were indeed (80%/10%), the missing samples were taken out of the test set without replacement. After excluding samples, the splits consisted of the following numbers of samples in the training set ( _ntraining_ = 18780), the validation set ( _nvalidation_ = 2347), and the test set ( _ntest_ = 2178). To confirm the efficacy of our method on out-of-distribution (OOD) data, we have randomly sampled an additional ( _nood_ = 2178) samples from an unreleased dataset of players who submitted their replays to the sc2replaystats [7] in 2016-2020. Access to all of the pre-processed data and code is available. For more information please see Appendix G. 

**Modelling** To ensure the possibility of transitioning between learned latent space representations and reconstruction of the player features, we have decided to use a model adapted from the original Guided VAE [40] architecture. We guide the latent space separation by the game outcome. Therefore, a part of the latent representation is encouraged to contain information about features that are significant for predicting winning or losing outcomes. The structure of our model consists of a symmetrical encoder-decoder multilayer perceptron (MLP) network with ReLU activations, with an additional supervised classifier attached to the latent space. In our modified Guided VAE [40], a selected number of dimensions are set to be supervised. An adversarial classifier is trained on the remaining latent dimensions, excluding the supervised dimensions. In training, the supervised classifier receives concatenated supervised latent dimensions of both players, [ _z_<sup>(0)</sup> 1 : _k|z_<sup>(1)</sup> 1 : _k_ ], and is trained to predict _y_ directly. At inference-time, when generating improvement paths for the player in seat 1, the input order is swapped, and the output probability is complemented, so that the score always represents the win probability of the player whose path is being improved. Please refer to Appendix B for more implementation details. We use AdamW optimizers [48, 49], implemented in PyTorch. The first updates the VAE and its guided classifier jointly. The second trains an auxiliary adversarial classifier on the non-guided (free) latent dimensions. The third updates the VAE parameters adversarially, penalising the encoder for producing free-dimension representations that are predictive of match outcome. Validation is monitored using the VAE loss, and early stopping is 

3 

Play Like Champions: Counterfactual Feedback Generation in Latent Space 

A PREPRINT 

used to avoid overfitting. We conducted a hyperparameter search to find the best-performing model, see Appendix D. All of the experiments were run on consumer hardware, see Appendix C. 

**Latent Space Traversal and Feedback Generation:** After training, a replay is encoded into a latent vector. We construct a path from the current game state to a winning region in the supervised dimensions of the latent space. Each point interpolated along the path in the latent space can be reconstructed back to the feature space, where the difference between the current feature values and the reconstructed feature values informs the player about the improvement “trajectory”. We compute feedback in three ways. First, we measure the raw change from the start of the path to the end. Second, we compute a minimum viable change that stops at the first waypoint where the predicted win probability crosses 0.5, if such a crossing exists. Third, we compute a win-probability-weighted change, where each step’s feature change is weighted by the corresponding increase in predicted win probability; steps where win probability decreases contribute zero weight. The final output is a ranked list of feature changes. These changes act as rough suggestions, and should be interpreted as model-generated hypotheses. Example generated feedback reports are available in Appendix F. 

### **4 Standardized Path Representation** 

To ensure compatibility with downstream generation and visualization tasks, the output of the path charting pipeline is strictly standardized, regardless of the specific employed strategy. The generated path _P_ is defined as an ordered sequence of _n_ discrete waypoints in the _d_ -dimensional latent space. This sequence is structured as a matrix **P** _∈_ R<sup>_n×d_</sup> , where each row **p** _j ∈_ R<sup>_d_</sup> corresponds to a specific waypoint along as seen in Equation 1. 

By definition across all strategies, the first waypoint **p** 0 corresponds exactly to the initial latent vector **z** _start_ . The final waypoint **p** _n−_ 1 corresponds to the terminal state of the strategy, denoted generally as **z** _end_ (which may represent a predefined target **z** _target_ , a successfully converged optimization state, or the integrated endpoint of a velocity field). Traversal methods have their own set of tunable parameters fully described in Appendix D. 

#### **4.1 Linear Strategy** 

The linear strategy serves as the foundational baseline for counterfactual generation. It implements a simple Linear Interpolation (LERP) to navigate the high-dimensional latent space, constructing a straight-line trajectory between the initial losing latent vector and a specified winning target. **Target Selection Strategies:** Because the "winning" state is represented by a distribution of points rather than a single vector, the algorithm first collapses the winning latents _Zwin_ = _{_ **w** 1 _, . . . ,_ **w** _M }_ into a single target vector **z** _target ∈_ R<sup>_d_</sup> using one of two selectable methods. **Centroid Strategy (** `method="centroid"` **):** The target is defined globally as the unweighted mean position (centroid) of all known winning latent vectors. This provides a robust, generalized direction toward the center of the winning class, see Equation 2. **Nearest Neighbors Strategy (** `method="nearest"` **):** To preserve local manifold structure and find the "closest" way to win, the target is derived locally. It calculates the mean of only the _k_ winning latents that are closest to the starting sample **z** _start_ (where _k_ is defined by `k_neighbours` ), see Equation 3. 

**Linear Interpolation (LERP) Formula:** Once the target **z** _target_ is established, the path is generated as a sequence of _n_ waypoints _{_ **p** 0 _,_ **p** 1 _, . . . ,_ **p** _n−_ 1 _}_ . The interpolation coefficient _αj_ is defined by an evenly spaced linear progression from 0 _._ 0 to 1 _._ 0, see Equation 4. Each intermediate point **p** _j_ along the trajectory is calculated using a convex combination of the start and target vectors, moving progressively closer to the target as _α_ increases, see Equation 5. This straight-line interpolation assumes a globally Euclidean latent space, transitioning semantic features at a constant velocity without explicit regard for the underlying data density. 

#### **4.2 Iterative Optimal Transport Strategy** 

The iterative optimal transport (OT) strategy simulates a vector field flow toward the winning distribution. Instead of interpolating toward a single static target (such as a centroid), the algorithm dynamically recalculates a local barycentric target at each step by finding the optimal mass transport plan between the current position and the target distribution. 

4 

Play Like Champions: Counterfactual Feedback Generation in Latent Space 

A PREPRINT 

**Distance Matrix and Transport Plan:** At each step _t_ , the current latent position **z**<sup>(</sup><sup>_t_)</sup> is treated as a point mass with weight **a** = 1. The set of _N_ winning latents _Zwin_ = _{_ **w** 1 _, . . . ,_ **w** _N }_ is treated as a uniform target distribution with weights **b** = _N_ <u>1</u><sup>**1**.First,the squared Euclidean distance matrix</sup><sup>**M**(</sup><sup>_t_)</sup><sup>_∈_R1</sup><sup>_×N_is computed.To prevent numerical</sup> underflow during exponentiation in the regularized transport step, the distance matrix is normalized by its maximum value as seen in Equation 6. Next, the optimal transport plan **T**<sup>(</sup><sup>_t_)</sup> is computed. If entropic regularization _λ >_ 0 ( `ot_reg` ) is provided, the mathematically stable log-domain Sinkhorn algorithm is utilized as seen in Equation 7, where _H_ ( **T** ) is the entropy of the coupling matrix. If _λ_ = 0, the exact Earth Mover’s Distance (EMD) is computed. **Local Barycentric Target:** The resulting transport plan **T**<sup>(</sup><sup>_t_)</sup> dictates the optimal distribution of mass from the current position to the winning points. These transport weights are normalized to form a localized probability distribution as seen in Equation 8. The local target **z**<sup>(</sup> _target_<sup>_t_)is then defined as the barycenter (weighted average) of the winning points,</sup> pulled specifically according to the optimal transport plan presented as Equation 9. **Euler Step (Vector Flow):** Rather than jumping directly to the target, the algorithm treats the vector ( **z**<sup>(</sup> _target_<sup>_t_)</sup><sup>_−_</sup><sup>**z**(</sup><sup>_t_)) as a local velocity field.It takes a</sup> small Euler step of size _η_ ( `step_size` ) toward the local barycenter, as seen in Equation 10. This process is repeated iteratively to trace a smooth trajectory. Because the transport plan dynamically updates at each spatial step, the resulting path closely mimics a continuous vector flow into the densest regions of the winning distribution. 

#### **4.3 Gradient Ascent Strategy** 

In the context of a Guided VAE, the gradient ascent strategy actively searches for a counterfactual path. Starting from a starting latent representation, the goal is to discover the minimal feature changes required to transition into a winning state. To ensure the generated counterfactuals remain realistic and do not exploit adversarial blind spots in the classifier, the trajectory is explicitly regularized by the data manifold. **Objective Formulation:** The optimization seeks to iteratively adjust the latent vector **z** to maximize an opponent-aware classification score _S_ ( **z** ) (e.g., the logit of winning against a specific opponent **z** _opp_ ), constrained by a manifold density penalty _D_ ( **z** ). The density is modeled using a fully differentiable Gaussian Kernel Density Estimate (KDE) evaluated over the reference dataset of known winning latents _Zwin_ = _{_ **w** 1 _, . . . ,_ **w** _N }_ with bandwidth _h_ , as seen in Equation 11. The total combined gradient at step _t_ merges the direction that increases the likelihood of winning with the direction that points toward denser, realistic regions of the latent space, as shown in Equation 12, where _λ_ represents the weighting of the density prior ( `density_weight` ). **Momentum-Based Optimization Update:** To traverse the disentangled latent space smoothly and avoid local minima, the latent vector is updated using gradient ascent with momentum. Let _α_ be the learning rate and _β_ be the momentum factor. The velocity **v** and position **z** are updated as seen in Equation 13, and Equation 14. **Convergence and Resampling:** This iterative process continues until the predicted probability of the winning class exceeds a specified `convergence_threshold` _τ_ as in Equation 15. Because the number of optimization steps _T_ required to reach this threshold is variable, the resulting sequence _{_ **z**<sup>(0)</sup> _,_ **z**<sup>(1)</sup> _, . . . ,_ **z**<sup>(</sup><sup>_T_)</sup> _}_ is evenly resampled to extract exactly _n_ waypoints. This final trajectory is then output as the standardized path matrix **P** _∈_ R<sup>_n×d_</sup> , representing a smooth, realistic counterfactual feature transition. 

#### **4.4 Neural Flow Strategy** 

The neural flow strategy utilizes continuous normalizing flows via an Optimal Transport (OT) Flow Matching framework. Rather than relying on simple geometric interpolations or local gradient steps, this approach trains a neural network to learn a global velocity field. This field models the continuous optimal transport of probability mass from the "losing" to the "winning" latent distribution. **Velocity Field Training and OT Pairing:** A Multi-Layer Perceptron (MLP) acts 

5 

Play Like Champions: Counterfactual Feedback Generation in Latent Space 

A PREPRINT 

as a time-conditioned velocity field **v** _θ_ ( **z** _, t_ ), parameterized by weights _θ_ . During training, mini-batches of losing latents **Z** 0 and winning latents **Z** 1 are extracted. To ensure the network learns the most efficient, non-crossing paths between these distributions, the samples are dynamically paired using exact Earth Mover’s Distance (EMD) based on squared Euclidean distance. For each **z** 0, an optimal **z** 1 _,_ paired is identified. At a uniformly sampled time _t ∈_ [0 _,_ 1], the intermediate state is defined by linear interpolation as shown in Equation 16. The network is then trained to predict the constant-velocity vector between paired samples by minimizing the Mean Squared Error (MSE), as shown in Equation 17. **Trajectory Integration (Euler Method):** To generate a counterfactual path during inference, a starting (losing) latent **z** _start_ is integrated through the learned velocity field from _t_ = 0 to _tmax_ = 1 _._ 0. Using a discrete number of integration steps _Nsteps_ , the time increment is ∆ _t_ = _Nsteps_ <u>1</u> _<u>.</u>_ <u>0</u><sup>.The latent position is updated iteratively using the</sup> 

Euler method seen in Equation 18, where the initial condition is **z**<sup>(0)</sup> = **z** _start_ . This produces a smooth flow along the learned data manifold. **Classifier Guidance (Optional):** To explicitly steer the trajectory toward regions with a higher probability of winning against a specific opponent, optional classifier guidance can be injected into the Euler integration. At each step, the gradient of the probability score _S_ ( **z** ) is computed. To ensure the guidance scale remains a consistent fraction of the flow step size, regardless of the raw gradient’s magnitude, the gradient is normalized to a unit vector. The position is updated as shown in Equation 19, where _γ_ ( `guidance_scale` ) dictates how strongly the path is pulled toward the classifier’s optimal regions, and _ϵ_ prevents division by zero. 

### **5 Experiments** 

**Model Performance:** To evaluate the quality of the trained Guided VAE, we assess both its reconstruction capabilities and the effectiveness of the latent space separation. The model’s performance on the held-out test set is summarized using several key metrics as seen in Table 1. 

Table 1: GuidedVAE Test-Set Evaluation 

|**Metric**|**SC2EGSet**|**OOD Data**|
|---|---|---|
|_VAE_|||
|MSE (original scale)|430095.6|519342.7|
|MSE (normalised scale)|0.5830|1.6619|
|KL Divergence|7.3601|7.6009|
|_Classifier_|||
|Accuracy (%)|98.76|97.11|
|ROC-AUC|0.9991|0.9926|
|F1 Score|0.9881|0.9714|
|Brier Score|0.0090|0.0229|

Evaluation of the GuidedVAE demonstrates strong generative and reconstruction fidelity, with the MSE and KL divergence confirming accurate game-state reconstruction from a well-regularised latent space. Furthermore, evaluation of the predictive guidance imposed on the first latent dimension—measured via test accuracy, ROC-AUC, and Brier score—indicates robust classification performance and highly calibrated win probabilities. Overall, the model successfully balances precise feature reconstruction with meaningful latent disentanglement, establishing a reliable foundation for generating counterfactual improvement trajectories. **Conterfactual Paths:** To evaluate the performance of the final model against our main goal of latent space traversal generating counterfactual “improvement trajectory”, we conduct a comparative assessment of all path generation strategies in Table 2. Where the success rate is the fraction of samples for which the path reaches _P_ (win) _≥_ 0 _._ 5 at any waypoint along the path. Crossover _α_ is the position along the path at which _P_ (win) first crosses 0.5, where _α_ = 0 is the start and _α_ = 1 is the end. Reported only for successful runs, **∆** P(win) is the absolute gain in predicted win probability from path start to path end, i.e. _P_ (win)end _− P_ (win)start., AUC is the area under the _P_ (win) curve over _α ∈_ [0 _,_ 1]. Monotonicity is the fraction of consecutive waypoint pairs for which _P_ (win) is non-decreasing. A value of 1.0 means _P_ (win) increases or stays flat at every step. Lower values indicate oscillation or regression along the path. Finally, the nearest-win distance is the Euclidean distance in the supervised latent subspace between the path endpoint and the closest winning latent vector in the training set. While Gradient Ascent achieves a nominally perfect success rate (1 _._ 000), further inspection 

6 

Play Like Champions: Counterfactual Feedback Generation in Latent Space 

A PREPRINT 

of the secondary metrics suggests this performance is largely driven by adversarial off-manifold drift. Compared to geometrically grounded strategies such as Optimal Transport, Gradient Ascent tends to explore low-density regions of the latent space. This is directly evidenced by a heavily inflated maximum latent norm (max _∥_ **z** _∥_ = 3 _._ 95 _±_ 1 _._ 74, compared to just 2 _._ 03 _±_ 0 _._ 58 for Optimal Transport) and a severely degraded path KDE density ( _−_ 4 _._ 63 _±_ 1 _._ 40 vs. _−_ 2 _._ 80 _±_ 0 _._ 50). Furthermore, its significantly reduced monotonicity (0 _._ 727 _±_ 0 _._ 227 vs. 0 _._ 998 _±_ 0 _._ 041) and higher nearest-win distance (0 _._ 15 _±_ 0 _._ 12 vs. 0 _._ 06 _±_ 0 _._ 04) indicate erratic, unconstrained traversal rather than smooth semantic interpolation. Consequently, the representations generated by this strategy are likely to exploit classifier blind spots and warrant much closer examination, see Appendix E. We hypothesize that these failure modes could be addressed in future work by imposing stricter regularization constraints to firmly anchor the trajectory to the learned data prior. 

Table 2: Cross-Dataset Comparison of Path-Charting Strategies 

|**Method**|**Metric**|**SC2EGSet**|**OOD Data**|**∆**Dataset|
|---|---|---|---|---|
|Linear (centroid)|Success rate|0.834|0.715|-0.118|
||Crossover_α_<br>|0.659_±_0.202<br>|0.704_±_0.236<br>|+0.045<br>|
||**∆**P(win)<br>|0.813_±_0.320<br>|0.681_±_0.399<br>|-0.132<br>|
||AUC|0.310_±_0.221|0.234_±_0.236|-0.076|
||Monotonicity|0.997_±_0.041|0.977_±_0.093|-0.020|
||Nearest-win dist.|0.06_±_0.04|0.05_±_0.03|-0.006|
|Linear (k-NN)|Success rate|0.845|0.543|-0.303|
||Crossover_α_|0.688_±_0.190|0.700_±_0.250|+0.012|
||**∆**P(win)|0.824_±_0.310|0.510_±_0.443|-0.314|
||AUC|0.290_±_0.206|0.182_±_0.234|-0.108|
||Monotonicity|0.998_±_0.027|0.966_±_0.128|-0.032|
||Nearest-win dist.|0.05_±_0.05|0.06_±_0.04|+0.005|
|Optimal Transport|Success rate|0.837|0.720|-0.117|
||Crossover_α_|0.120_±_0.065|0.140_±_0.084|+0.020|
||**∆**P(win)|0.819_±_0.315|0.682_±_0.397|-0.137|
||AUC|0.752_±_0.301|0.629_±_0.364|-0.123|
||Monotonicity|0.998_±_0.041|0.995_±_0.059|-0.003|
||Nearest-win dist.|0.06_±_0.04|0.05_±_0.03|-0.005|
|Neural Flow|Success rate|0.931|0.731|-0.200|
||Crossover_α_|0.524_±_0.230|0.494_±_0.279|-0.030|
||**∆**P(win)|0.915_±_0.241|0.701_±_0.427|-0.213|
||AUC|0.468_±_0.253|0.390_±_0.332|-0.078|
||Monotonicity|0.999_±_0.013|0.996_±_0.025|-0.002|
||Nearest-win dist.|0.18_±_0.16|0.20_±_0.19|+0.024|
|Gradient Ascent|Success rate|1.000|0.998|-0.002|
||Crossover_α_|0.486_±_0.367|0.513_±_0.337|+0.027|
||**∆**P(win)|0.986_±_0.076|0.969_±_0.139|-0.017|
||AUC|0.545_±_0.355|0.517_±_0.321|-0.029|
||Monotonicity|0.727_±_0.227|0.749_±_0.209|+0.021|
||Nearest-win dist.|0.15_±_0.12|0.15_±_0.14|+0.005|

The experimental results reveal several key insights regarding the trade-offs between path reliability and quality: (1) **Reliability and Success Rates:** Gradient Ascent emerges as the strategy maintaining a near-perfect success rate on both the **SC2EGSet** (1.000) and **OOD Data** (0.998). In contrast, the Linear (k-NN) baseline exhibits significant fragility under distributional shift, with success rates dropping by over 30% (∆= _−_ 0 _._ 302). (2) **Path Efficiency and Crossover:** Optimal Transport (OT) demonstrates superior efficiency in trajectory charting. As shown by the **Crossover** _α_ (0 _._ 120 _±_ 0 _._ 065), OT-generated paths transition to a winning state much earlier than Linear methods ( _α ≈_ 0 _._ 65). Furthermore, OT achieves the highest **AUC** (0 _._ 752 _±_ 0 _._ 301), suggesting it identifies more direct routes through the latent space. (3) **The Success-Monotonicity Trade-off :** A clear divergence exists between raw success and path smoothness. While Gradient Ascent is the most successful, it records the lowest **Monotonicity** (0 _._ 727 _±_ 0 _._ 227), indicating more erratic trajectories. Conversely, Neural Flow and Optimal Transport maintain near-perfect monotonicity ( _>_ 0 _._ 99) even on OOD data, providing highly stable and interpretable transitions. The substantial variance in ∆ _P_ (win) across the linear baselines further suggests that simple interpolation is insufficient to capture the model’s complex 

7 

Play Like Champions: Counterfactual Feedback Generation in Latent Space 

A PREPRINT 

decision boundaries. In contrast, neural and transport-based methods provide more consistent counterfactual evidence, with a mean _P_ (win) along the counterfactual path shown in Fig. 1, and directly showcase some of the aforementioned trade-offs on OOD data. Further model interpretability is covered in Appendix E. 

<!-- Start of picture text -->
P(win) along path   mean across samples<br>1.0 P(win)=0.5<br>Linear (centroid)<br>Linear (k-NN)<br>Optimal Transport<br>Neural Flow<br>0.8 Gradient Ascent<br>0.6<br>0.4<br>0.2<br>0.0<br>0.0 0.2 0.4 0.6 0.8 1.0<br>P(win)<br><!-- End of picture text -->

Figure 1: Mean OOD data _P_ (win) performance of generated paths progress in the latent space. 

### **6 Limitations and Future Research** 

**Limitations:** Despite the promising results, our approach has several limitations that should be acknowledged. First, we train our model on a dataset of games spanning multiple years. We do not explicitly account for the game updates. Additionally, we do not encode the players’ in-game race information in any way. By design, our model is incapable of providing feedback directed towards specific in-game actions and environment configurations. The model feedback is additionally constrained by the dataset choice; tournament gameplay samples can be seen as a very specific subset of all of the games. Our model does not directly convey a more granular approach of jumping between leagues when leveraging its feedback. Finally, the model and method parameters were not verified with human participants, and aside from expert input from known professional players, we were unable to set up a human-in-the-loop type of experiment. **Future Research:** We hope that by extending research efforts in representational learning geared towards providing feedback, we can inspire others to prepare end-to-end feedback generation. Automating ways to improve humans based on deep generative solutions and other computational means. In the future, we wish to address most of the concerns raised above. Moving towards optimizing human performance jointly with actions against an environment sounds incredibly exciting, with the potential to uncover environment configurations that promote positive training or learning outcomes. Given the recent advancements and rapid adoption of AI systems, creating models that provide data-driven, actionable feedback is crucial. 

### **7 Conclusion and Summary** 

We have demonstrated the computational feasibility and the potential for developing many practical solutions for providing feedback based on learned representations. Additionally, simplistic methods, while appealing, have drawbacks that become more evident when dealing with a more advanced nonlinear model. Finally, we have accomplished our goal of bridging the gap between representational learning and generating feedback by extracting actionable, counterfactual improvement trajectories from the latent space, effectively shifting the analytical paradigm from predicting game outcomes to providing players with tangible guidance on what they should do differently. Based on our ongoing discussions with esports professionals, our solution is proving to be a real asset for future feedback systems. 

8 

Play Like Champions: Counterfactual Feedback Generation in Latent Space 

A PREPRINT 

### **References** 

- [1] O. Vinyals, T. Ewalds, S. Bartunov, P. Georgiev, A. S. Vezhnevets, M. Yeo, A. Makhzani, H. Küttler, J. Agapiou, J. Schrittwieser, J. Quan, S. Gaffney, S. Petersen, K. Simonyan, T. Schaul, H. van Hasselt, D. Silver, T. Lillicrap, K. Calderone, P. Keet, A. Brunasso, D. Lawrence, A. Ekermo, J. Repp, and R. Tsing, “Starcraft ii: A new challenge for reinforcement learning,” 2017. [Online]. Available: https://arxiv.org/abs/1708.04782 (Cited on page: 1). 

- [2] M. Mathieu, S. Ozair, S. Srinivasan, C. Gulcehre, S. Zhang, R. Jiang, T. L. Paine, R. Powell, K. Zołna,<sup>˙</sup> J. Schrittwieser, D. Choi, P. Georgiev, D. Toyama, A. Huang, R. Ring, I. Babuschkin, T. Ewalds, M. Bordbar, S. Henderson, S. G. Colmenarejo, A. van den Oord, W. M. Czarnecki, N. de Freitas, and O. Vinyals, “Alphastar unplugged: Large-scale offline reinforcement learning,” 2023. [Online]. Available: https://arxiv.org/abs/2308.03526 (Cited on page: 1). 

- [3] J. J. Thompson, M. R. Blair, L. Chen, and A. J. Henrey, “Video game telemetry as a critical tool in the study of complex skill learning,” _PLOS ONE_ , vol. 8, no. 9, pp. 1–12, 09 2013. [Online]. Available: https://doi.org/10.1371/journal.pone.0075129 (Cited on page: 1). 

- [4] A. Białecki, N. Jakubowska, P. Dobrowolski, P. Białecki, L. Krupi´nski, A. Szczap, R. Białecki, and J. Gajewski, “Sc2egset: Starcraft ii esport replay and game-state dataset,” _Scientific Data_ , vol. 10, no. 1, p. 600, Sep 2023. [Online]. Available: https://doi.org/10.1038/s41597-023-02510-7 (Cited on pages: 1, 3). 

- [5] B. Ferenczi, R. Newbury, M. Burke, and T. Drummond, “Carefully structured compression: Efficiently managing starcraft ii data,” 2024. [Online]. Available: https://arxiv.org/abs/2410.08659 (Cited on page: 1). 

- [6] F. Rijnders, G. Wallner, and R. Bernhaupt, “Live feedback for training through real-time data visualizations: A study with league of legends,” _Proc. ACM Hum.-Comput. Interact._ , vol. 6, no. CHI PLAY, oct 2022. [Online]. Available: https://doi.org/10.1145/3549506 (Cited on page: 1). 

- [7] A. Martin, “sc2replaystats,” https://sc2replaystats.com/, 2012, acessed: 2026.04.28. (Cited on pages: 1, 3). 

- [8] B. Dibbell, “REPLAYMAN — SC2 Replay Analysis & Management – replayman.com,” https://replayman.com/, 2026, [Accessed 28-04-2026]. (Cited on page: 1). 

- [9] S. Charleer, K. Gerling, F. Gutiérrez, H. Cauwenbergh, B. Luycx, and K. Verbert, “Real-time dashboards to support esports spectating,” in _Proceedings of the 2018 Annual Symposium on Computer-Human Interaction in Play_ , ser. CHI PLAY ’18. New York, NY, USA: Association for Computing Machinery, 2018, pp. 59–71. [Online]. Available: https://doi.org/10.1145/3242671.3242680 (Cited on page: 1). 

- [10] G. Wallner and S. Kriglstein, “Visualizations for retrospective analysis of battles in team-based combat games: A user study,” in _Proceedings of the 2016 Annual Symposium on Computer-Human Interaction in Play_ , ser. CHI PLAY ’16. New York, NY, USA: Association for Computing Machinery, 2016, pp. 22–32. [Online]. Available: https://doi.org/10.1145/2967934.2968093 (Cited on page: 1). 

- [11] P. Xenopoulos, J. a. Rulff, and C. Silva, “ggviz: Accelerating large-scale esports game analysis,” _Proc. ACM Hum.-Comput. Interact._ , vol. 6, no. CHI PLAY, oct 2022. [Online]. Available: https://doi.org/10.1145/3549501 (Cited on page: 2). 

- [12] N. Shaker, J. Togelius, and M. J. Nelson, _Procedural Content Generation in Games_ . Springer International Publishing, 2016. [Online]. Available: http://dx.doi.org/10.1007/978-3-319-42716-4 (Cited on page: 2). 

- [13] W. Wei, S. Yang, Q. Zhou, R. Liu, X. Zhang, Y. Yuan, Y. Jiang, Y. Luo, H. Wang, T. Wang, P. Jin, W. Liu, Z. Zhao, X. Jin, and E. S. Liu, “F.a.c.u.l.: Language-based interaction with ai companions in gaming,” 2025. [Online]. Available: https://arxiv.org/abs/2511.13112 (Cited on page: 2). 

- [14] A. Sestini, J. Bergdahl, J.-P. Barrette-LaPierre, F. Fuchs, B. Chen, M. Jones, and L. Gisslén, “Human-like goalkeeping in a realistic football simulation: a sample-efficient reinforcement learning approach,” 2025. [Online]. Available: https://arxiv.org/abs/2510.23216 (Cited on page: 2). 

- [15] R. Tufano, S. Scalabrino, L. Pascarella, E. Aghajani, R. Oliveto, and G. Bavota, “Using reinforcement learning for load testing of video games,” in _Proceedings of the 44th International Conference on Software Engineering_ , ser. ICSE ’22. New York, NY, USA: Association for Computing Machinery, 2022, pp. 2303–2314. [Online]. Available: https://doi.org/10.1145/3510003.3510625 (Cited on page: 2). 

- [16] A. V. Kokkinakis, S. Demediuk, I. Nölle, O. Olarewaju, S. Patra, J. Robertson, P. York, A. P. Pedrassoli Chitayat, A. Coates, D. Slawson, P. Hughes, N. Hardie, B. Kirman, J. Hook, A. Drachen, M. F. Ursu, and F. Block, “Dax: Data-driven audience experiences in esports,” in _Proceedings of the 2020 ACM International Conference on Interactive Media Experiences_ , ser. IMX ’20. New York, NY, USA: Association for Computing Machinery, 2020, pp. 94–105. [Online]. Available: https://doi.org/10.1145/3391614.3393659 (Cited on page: 2). 

9 

Play Like Champions: Counterfactual Feedback Generation in Latent Space 

A PREPRINT 

- [17] The Newton Contributors, “Newton: GPU-accelerated physics simulation for robotics and simulation research,” apr 2025. [Online]. Available: https://github.com/newton-physics/newton (Cited on page: 2). 

- [18] M. Mittal, P. Roth, J. Tigue, A. Richard, O. Zhang, P. Du, A. Serrano-Muñoz, X. Yao, R. Zurbrügg, N. Rudin, L. Wawrzyniak, M. Rakhsha, A. Denzler, E. Heiden, A. Borovicka, O. Ahmed, I. Akinola, A. Anwar, M. T. Carlson, J. Y. Feng, A. Garg, R. Gasoto, L. Gulich, Y. Guo, M. Gussert, A. Hansen, M. Kulkarni, C. Li, W. Liu, V. Makoviychuk, G. Malczyk, H. Mazhar, M. Moghani, A. Murali, M. Noseworthy, A. Poddubny, N. Ratliff, W. Rehberg, C. Schwarke, R. Singh, J. L. Smith, B. Tang, R. Thaker, M. Trepte, K. Van Wyk, F. Yu, A. Millane, V. Ramasamy, R. Steiner, S. Subramanian, C. Volk, C. Chen, N. Jawale, A. V. Kuruttukulam, M. A. Lin, A. Mandlekar, K. Patzwaldt, J. Welsh, J.-F. Lafleche, N. Moënne-Loccoz, S. Park, R. Stepinski, D. Van Gelder, C. Amevor, J. Carius, J. Chang, A. He Chen, P. d. H. Ciechomski, G. Daviet, M. Mohajerani, J. von Muralt, V. Reutskyy, M. Sauter, S. Schirm, E. L. Shi, P. Terdiman, K. Vilella, T. Widmer, G. Yeoman, T. Chen, S. Grizan, C. Li, L. Li, C. Smith, R. Wiltz, K. Alexis, Y. Chang, L. J. Fan, F. Farshidian, A. Handa, S. Huang, M. Hutter, Y. Narang, S. Pouya, S. Sheng, Y. Zhu, M. Macklin, A. Moravanszky, P. Reist, Y. Guo, D. Hoeller, and G. State, “Isaac Lab - A GPU-Accelerated Simulation Framework for Multi-Modal Robot Learning,” _arXiv preprint arXiv:2511.04831_ , 2025. [Online]. Available: https://arxiv.org/abs/2511.04831 (Cited on page: 2). 

- [19] E. Kaufmann, L. Bauersfeld, A. Loquercio, M. Müller, V. Koltun, and D. Scaramuzza, “Champion-level drone racing using deep reinforcement learning,” _Nature_ , vol. 620, no. 7976, pp. 982–987, Aug 2023. [Online]. Available: https://doi.org/10.1038/s41586-023-06419-4 (Cited on page: 2). 

- [20] L. Lamberti, E. Cereda, G. Abbate, L. Bellone, V. J. K. Morinigo, M. Barci´s, A. Barci´s, A. Giusti, F. Conti, and D. Palossi, “A sim-to-real deep learning-based framework for autonomous nano-drone racing,” _IEEE Robotics and Automation Letters_ , vol. 9, no. 2, pp. 1899–1906, 2024. (Cited on page: 2). 

- [21] Y. Ma, A. Cramariuc, F. Farshidian, and M. Hutter, “Learning coordinated badminton skills for legged manipulators,” _Science Robotics_ , vol. 10, no. 102, may 2025. [Online]. Available: http://dx.doi.org/10.1126/scirobotics.adu3922 (Cited on page: 2). 

- [22] C. Liu, L. Jiang, Y. Wang, K. Yao, J. Fu, and X. Ren, “Humanoid whole-body badminton via multi-stage reinforcement learning,” 2026. [Online]. Available: https://arxiv.org/abs/2511.11218 (Cited on page: 2). 

- [23] P. Dürr, M. El Gheche, G. J. Maeda, N. Mukai, N. Takahashi, S. Heusser, H. Sahloul, Y. Saraiji, P. Adodin, Y. Bi, S. Blakeman, C. Conti, D. Fuentes Hitos, Y. Hu, F. Khadivar, R. Kreiser, L. Martinez, F. Schilling, R. Tapiador Morales, G. Torrente, M. Ynocente Castro, L. Abecassis, A. Giammarino, Y.-T. Huang, Y. Nagel, A. Scotti, A. Sigrist, T. Silva, E. Walther, J. Wong, B. Yang, A. Aydin, D. Grover, A. Saha, V. Cavinato, T. Kakinuma, T. Kunori, V. Monferrato, S. Richter, S. Charalambous, S. Guist, M. A. Kuhlmann-Jorgensen, L. Miele, A. Politis, M. Scardecchia, H. Kitano, P. R. Wurman, P. Stone, and M. Spranger, “Outplaying elite table tennis players with an autonomous robot,” _Nature_ , vol. 652, no. 8111, pp. 886–891, Apr 2026. [Online]. Available: https://doi.org/10.1038/s41586-026-10338-5 (Cited on page: 2). 

- [24] I. Leite, W. Ahlberg, A. Pereira, A. Sestini, L. Gisslén, and K. Tollmar, “A call for deeper collaboration between robotics and game development,” in _2025 IEEE Conference on Games (CoG)_ , 2025, pp. 1–8. (Cited on page: 2). 

- [25] D. J. Hancock, A. M. Rymal, and D. M. Ste-Marie, “A triadic comparison of the use of observational learning amongst team sport athletes, coaches, and officials,” _Psychology of Sport and Exercise_ , vol. 12, no. 3, pp. 236–241, 2011. [Online]. Available: https://doi.org/10.1016/j.psychsport.2010.11.002 (Cited on page: 2). 

- [26] H. Soza´nski, J. Sadowski, and J. Czerwi´nski, _Podstawy Teorii i Technologii Treningu Sportowego_ . Akademia Wychowania Fizycznego Józefa Piłsudskiego Filia w Białej Podlaskiej, 2015, vol. 2. (Cited on page: 2). 

- [27] R. McIlroy-Young, S. Sen, J. Kleinberg, and A. Anderson, “Aligning superhuman ai with human behavior: Chess as a model system,” in _Proceedings of the 26th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining_ , ser. KDD ’20. New York, NY, USA: Association for Computing Machinery, 2020, pp. 1677–1687. [Online]. Available: https://doi.org/10.1145/3394486.3403219 (Cited on page: 2). 

- [28] F. Gaessler and H. Piezunka, “Training with ai: Evidence from chess computers,” _Strategic Management Journal_ , vol. 44, no. 11, pp. 2724–2750, 2023. [Online]. Available: https://doi.org/10.1002/smj.3512 No citations. 

- [29] M. Bilali´c, M. Graf, and N. Vaci, “Computers and chess masters: The role of ai in transforming elite human performance,” _British Journal of Psychology_ , vol. 117, no. 2, pp. 585–609, 2026. [Online]. Available: https://doi.org/10.1111/bjop.12750 (Cited on page: 2). 

- [30] M. Sadler and N. Regan, _Game Changer: AlphaZero’s Groundbreaking Chess Strategies and the Promise of AI_ . Alkmaar, Netherlands: New In Chess, 2019. (Cited on page: 2). 

- [31] J. Kang, J. S. Yoon, and B. Lee, “How ai-based training affected the performance of professional go players,” in _Proceedings of the 2022 CHI Conference on Human Factors in Computing Systems_ , ser. CHI ’22. New York, NY, 

10 

Play Like Champions: Counterfactual Feedback Generation in Latent Space 

A PREPRINT 

USA: Association for Computing Machinery, 2022. [Online]. Available: https://doi.org/10.1145/3491102.3517540 (Cited on page: 2). 

- [32] M. Shin, J. Kim, and M. Kim, “Human learning from artificial intelligence: Evidence from human go players’ decisions after alphago,” in _CogSci 2021 - The 43rd Annual Meeting of the Cognitive Science Society_ , 07 2021. [Online]. Available: https://doi.org/10.5281/zenodo.5095146 (Cited on page: 2). 

- [33] O. Vinyals, I. Babuschkin, W. M. Czarnecki, M. Mathieu, A. Dudzik, J. Chung, D. H. Choi, R. Powell, T. Ewalds, P. Georgiev _et al._ , “Grandmaster level in StarCraft II using multi-agent reinforcement learning,” _Nature_ , vol. 575, no. 7782, pp. 350–354, 2019. (Cited on page: 2). 

- [34] M. Samvelyan, T. Rashid, C. S. de Witt, G. Farquhar, N. Nardelli, T. G. J. Rudner, C.-M. Hung, P. H. S. Torr, J. Foerster, and S. Whiteson, “The starcraft multi-agent challenge,” 2019. [Online]. Available: https://arxiv.org/abs/1902.04043 (Cited on page: 2). 

- [35] B. Ellis, J. Cook, S. Moalla, M. Samvelyan, M. Sun, A. Mahajan, J. N. Foerster, and S. Whiteson, “Smacv2: An improved benchmark for cooperative multi-agent reinforcement learning,” 2023. [Online]. Available: https://arxiv.org/abs/2212.07489 (Cited on page: 2). 

- [36] T. Avontuur, P. Spronck, and M. van Zaanen, “Player skill modeling in StarCraft II,” in _Proceedings of the AAAI Conference on Artificial Intelligence and Interactive Digital Entertainment_ , vol. 9, no. 1, 2013, pp. 2–8. (Cited on page: 2). 

- [37] S. Bowman, D. Lux, R. Vidal, and A. Drachen, “StarCraft winner prediction,” in _Proceedings of the 16th International Conference on the Foundations of Digital Games_ , 2021. (Cited on page: 2). 

- [38] D. P. Kingma and M. Welling, “Auto-encoding variational bayes,” 2022. [Online]. Available: https: //arxiv.org/abs/1312.6114 (Cited on page: 2). 

- [39] I. Higgins, L. Matthey, A. Pal, C. P. Burgess, X. Glorot, M. M. Botvinick, S. Mohamed, and A. Lerchner, “ _β_ -VAE: Learning basic visual concepts with a constrained variational framework,” in _Proceedings of the 5th International Conference on Learning Representations_ , Toulon, France, 2017. [Online]. Available: https://openreview.net/forum?id=Sy2fzU9gl (Cited on page: 2). 

- [40] Z. Ding, Y. Xu, W. Xu, G. Parmar, Y. Yang, M. Welling, and Z. Tu, “Guided variational autoencoder for disentanglement learning,” in _2020 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)_ , 2020, pp. 7917–7926. (Cited on pages: 2, 3, 3). 

- [41] M. L. Schrum, S. Srivatsa, D. E. Gopinath, G. Rosman, and T. L. Chen, “Disentangled skill representations for predictive human modeling,” in _ICLR 2026 Conference Withdrawn Submission_ , 2025, withdrawn from ICLR 2026. [Online]. Available: https://openreview.net/forum?id=rwvTTjcuHv (Cited on page: 2). 

- [42] E. Korkmaz, O. Anil Koyejo, and P. Smyth, “Optimal transport maps for distribution preserving operations on latent spaces of generative models,” in _ICLR Workshop on Deep Generative Models for Highly Structured Data_ , 2018. [Online]. Available: https://openreview.net/forum?id=BklCusRct7 (Cited on page: 2). 

- [43] Y. Song, A. Keller, N. Sebe, and M. Welling, “Latent traversals in generative models as potential flows,” in _Proceedings of the 40th International Conference on Machine Learning_ , ser. ICML’23. JMLR.org, 2023. (Cited on page: 3). 

- [44] E. Yeh, P. Sequeira, J. Hostetler, and M. Gervasio, “Outcome-guided counterfactuals from a jointly trained generative latent space,” in _Explainable Artificial Intelligence (xAI 2023)_ , ser. Communications in Computer and Information Science. Springer, 2023, pp. 449–469. [Online]. Available: https://arxiv.org/abs/2207.07710 (Cited on page: 3). 

- [45] R. Crupi, A. Castelnovo, D. Regoli, and B. S. M. Gonzalez, “Counterfactual explanations as interventions in latent space,” _Data Mining and Knowledge Discovery_ , vol. 38, pp. 2733–2769, 2022. (Cited on page: 3, 3). 

- [46] J. Bae, H. Nam, K. Ryu, J. Lee, J. Kim, H. Chun, J. Han, and J. Choi, “Data-driven driver training via counterfactual and language-based guidance in racing scenarios,” _IEEE Access_ , vol. 13, pp. 170 181–170 199, 2025. (Cited on page: 3). 

- [47] P. Pegios, A. Feragen, A. A. Hansen, and G. Arvanitidis, “Counterfactual explanations via Riemannian latent space traversal,” _arXiv preprint arXiv:2411.02259_ , 2024. [Online]. Available: https://arxiv.org/abs/2411.02259 (Cited on page: 3). 

- [48] D. P. Kingma and J. Ba, “Adam: A method for stochastic optimization,” 2017. [Online]. Available: https://arxiv.org/abs/1412.6980 (Cited on page: 3). 

- [49] I. Loshchilov and F. Hutter, “Decoupled weight decay regularization,” in _International Conference on Learning Representations_ , 2019. [Online]. Available: https://openreview.net/forum?id=Bkg6RiCqY7 (Cited on page: 3). 

11 

Play Like Champions: Counterfactual Feedback Generation in Latent Space 

A PREPRINT 

### **A StarCraft II Game Description** 

Before diving deeper it is important to state the rules governing StarCraft II competitive gameplay. The game contains three main “races” of choice for the players. Each race is differentiated by unit mechanics therefore forcing certain playstyles. In most cases the game is played in the format of player versus player (PvP), one versus one (1 vs 1). The ultimate goal for competitors is to destroy all of the opponents’ structures, or to force their counterpart to resign. In many cases tournaments have varying stages, such as the initial group stage, and a subsequent knockout bracket stage. Depending on the tournament format in most cases the group stages are played out as best of one (Bo1), best of two (Bo2), or best of three (Bo3) matches. Finally, the knockout bracket features Bo3, best of five (Bo5), and best of seven (Bo7) matches. 

### **B Model Details** 

**Training Objective:** The VAE is trained with the standard reconstruction and KL divergence objective. The reconstruction term is mean squared error between the original feature vector and the decoded feature vector. The KL term regularizes the posterior distribution toward a unit Gaussian prior. The VAE loss is shown in Equation 20 where _L_ MSE is the summed mean squared error between the input feature vector and its reconstruction, and _L_ KL regularizes the approximate posterior toward a unit Gaussian prior. To guide the latent space, we add a binary cross-entropy loss on the prediction produced from the first latent dimension. The main Guided VAE update is seen on Equation 21, where _λ_ cls controls the strength of supervision and encourages outcome-relevant information to be concentrated in the guided latent dimension. 

Aside from the typical structure of a Guided VAE model we clamp the log variance output of the encoder to the interval [ _−_ 20 _,_ 2] before the reparameterization step. This hard bound constrains the effective standard deviation to the range [ _≈_ 4 _._ 5 _×_ 10<sup>_−_5</sup> _, ≈_ 2 _._ 7], preventing two sources of numerical instability: a near-zero variance, which causes the KL divergence term in the evidence lower bound (ELBO) to diverge and produces exploding gradients; and an excessively large variance, which overwhelms the mean and injects too much noise into the decoder input, destabilizing reconstruction. These dimensions are used to predict the game outcome. The point of this is to force at least one direction of the latent space to be directly related to winning and losing. 

### **C Hardware** 

#### **C.1 Hardware and Computational Requirements** 

All experiments were conducted on a high-performance workstation using consumer-grade hardware. The specific configuration of the system components is detailed in Table 3. 

Table 3: Hardware specifications used for all experimental runs and hyperparameter sweeps. 

|**Component**|**Specification**|
|---|---|
|CPU|AMD Ryzen 9 9950X (16-Core, 32-Thread)|
|GPU|NVIDIA GeForce RTX 5090|
|Memory (RAM)|128 GB DDR5|

The model architectures and optimization strategies were designed for high efficiency. Consequently, the majority of individual experimental runs, including those within the Guided-VAE hyperparameter sweep and path generation evaluations, were completed in under 5 minutes. 

### **D Hyperparameter Search** 

#### **D.1 Guided-VAE Hyperparameter Search** 

#### **D.1.1 Search Space** 

The search space for the Guided-VAE is defined by a set of hierarchical constraints to ensure a valid bottleneck architecture. Let _W_ = _{w_ 0 _, w_ 1 _, . . . , wm}_ denote the set of available layer widths in ascending order. 

#### Architecture Constraints 

The encoder configuration is sampled via two primary parameters: the number of layers _n ∈{_ 2 _,_ 3 _,_ 4 _}_ and a categorical start width _wstart ∈W_ . To guarantee that the resulting hidden dimensions **H** _enc_ are strictly decreasing, we 

12 

Play Like Champions: Counterfactual Feedback Generation in Latent Space 

A PREPRINT 

calculate the actual starting index _i_ as: 

The sequence of hidden dimensions is then defined as: 

The latent dimensionality _nz_ is coupled to the final encoder width _hlast ∈_ **H** _enc_ through a fraction _fz ∈ {_ 0 _._ 25 _,_ 0 _._ 5 _,_ 1 _._ 0 _}_ , constrained by a minimum floor: 

Optimization Parameters The remaining parameters are sampled according to the following distributions: 

- **Learning Rates:** _ηvae, ηcls ∼_ LogUniform(10<sup>_−_5</sup> _,_ 10<sup>_−_3</sup> ) 

- **Weight Decays:** _λvae, λcls ∼_ LogUniform(10<sup>_−_6</sup> _,_ 10<sup>_−_3</sup> ) 

- **Classification Weight:** _α ∼_ LogUniform(1 _,_ 250) 

- **Supervised Dimensions:** _ns ∈{_ 1 _,_ 2 _,_ 4 _}_ 

#### **D.1.2 Hyperparameter Run Configuration** 

To find the best hyperparameters for our training, we ran the search using Ray (https://www.ray.io/) and Optuna (https://optuna.org/). Upon execution, we have decided on 150 total runs. The objective function, _OHP O_ , is defined as a weighted scalar sum of validation metrics logged during the training of the Guided VAE model. Formally, the minimization objective is expressed as: 

where _M_ denotes the set of validation metrics, _Li_ is the value of the _i_ -th metric, and _wi_ is the user-defined weight for that metric. In the configuration utilized for this sweep, the objective was set to equally weight the reconstruction and classification components: 

Given our configuration parameters _w_ vae = 0 _._ 5 and _w_ cls = 0 _._ 5, the final objective function simplifies to: 

#### **D.1.3 Guided VAE Final Hyperparameters** 

Table 4 contains the model we have selected for a best performing model. 

Table 4: Final hyperparameter values for the Guided-VAE model discovered via the Ray/Optuna optimization sweep. 

|**Category**|**Hyperparameter**|**Value**|
|---|---|---|
|**Architecture**|Input Dimension<br>Encoder Hidden Dimensions (**H**_enc_)<br>Latent Dimensionality (_nz_)<br>Supervised Dimensions (_ns_)|196<br>[32_,_16]<br>16<br>4|
|**Optimization**|VAE Learning Rate (_ηvae_)|1_._7725_×_10<sup>_−_4</sup><br>|
||VAE Weight Decay (_λvae_)|1_._3597_×_10<sup>_−_5</sup><br>|
||Classifier Learning Rate (_ηcls_)|4_._1398_×_10<sup>_−_4</sup>|
||Classifier Weight Decay (_λcls_)|4_._5500_×_10<sup>_−_6</sup>|
||Classification Weight (_α_)|1_._2824|

#### **D.2 Path Generation Strategies: Hyperparameter Search** 

#### **D.2.1 Search Space** 

The search space for the latent space traversal is structured hierarchically, where the subset of active hyperparameters is conditioned on the chosen strategy _S_ . 

13 

Play Like Champions: Counterfactual Feedback Generation in Latent Space 

A PREPRINT 

**Linear Strategy** The linear interpolation strategy relies on neighborhood density constraints: 

- **Nearest Neighbors (** _kneighbors_ **):** _knb ∼_ DiscreteUniform(3 _,_ 15) 

- **Opponent Constraints (** _kopponents_ **):** _kopp ∼_ DiscreteUniform(10 _,_ 200) 

**Gradient Ascent Strategy** This strategy utilizes a density-based optimization approach with fixed steps _T_ = 2000 and a convergence threshold _τ_ = 0 _._ 95: 

- **Learning Rate (** _η_ **):** _η ∼_ LogUniform(10<sup>_−_4</sup> _,_ 0 _._ 1) 

- **Momentum (** _µ_ **):** _µ ∼_ Uniform(0 _._ 0 _,_ 0 _._ 95) 

- **Density Weight (** _wρ_ **):** _wρ ∼_ Uniform(0 _._ 0 _,_ 1 _._ 0) 

- **KDE Bandwidth (** _h_ **):** _h ∼_ Uniform(0 _._ 1 _,_ 2 _._ 0) 

**Optimal Transport Strategy** The optimal transport strategy balances regularization and geometric constraints: 

- **Regularization (** _ϵ_ **):** _ϵ ∼_ LogUniform(0 _._ 01 _,_ 0 _._ 5) 

- **Step Size (** _γ_ **):** _γ ∼_ Uniform(0 _._ 05 _,_ 0 _._ 5) 

- **Opponent Constraints (** _kopponents_ **):** _kopp ∼_ DiscreteUniform(10 _,_ 200) 

**Neural Flow Strategy** The neural flow strategy utilizes a fixed guidance scale for its transformation: 

- **Guidance Scale (** _s_ **):** _s_ = 1 _._ 0 (fixed) 

#### **D.2.2 Hyperparameter Run Configuration** 

The optimization of hyperparameters for the latent space traversal strategies was performed using the Optuna framework. For each of the strategy we executed _N_ = 100 independent trials. In each trial, the performance was evaluated by generating _nsamples_ = 1000 latent paths. 

Unlike the model training phase, the objective for path charting is a maximization task. The objective function _J_ is defined as the mean performance of a specified evaluation metric _M_ : AUC across all generated samples: 

where _ϕ_ represents the set of strategy-specific hyperparameters sampled from the search space, and _S_ ( _ϕ_ ) denotes the distribution of paths generated under those parameters. 

#### **D.2.3 Path Generation Strategies: Final Hyperparameters** 

Table 5 contains the specific hyperparameters used for the final runs of our path generation strategies. 

Table 5: Hyperparameters used for the evaluated methods. Continuous values discovered via hyperparameter optimization are rounded to four decimal places. 

|**Method**|**Hyperparameter**|**Value**|
|---|---|---|
|**Neural Flow**|Guidance Scale|1_._0|
|**Gradient Ascent**|Steps<br>Learning Rate (lr)|2000<br>0_._0330|
||Momentum|0_._8815|
||Density Weight|0_._8444|
||KDE Bandwidth|0_._6516|
||Convergence Threshold|0_._95|
|**Linear Centroid**|_k_Neighbours<br>_k_Opponents|14<br>74|
|**Linear Nearest**|_k_Neighbours<br>_k_Opponents|10<br>11|
|**Optimal Transport**|Regularization (reg)<br>Step Size<br>_k_Opponents|0_._0887<br>0_._4999<br>64|

14 

Play Like Champions: Counterfactual Feedback Generation in Latent Space 

A PREPRINT 

Table 6: Cross-Dataset Comparison of Path-Charting Strategies with all of the computed metrics. 

|**Method**|**Metric**|**SC2EGSet**|**OOD Data**|**∆**Dataset|
|---|---|---|---|---|
|Linear (centroid)|Success rate|0.834|0.715|-0.118|
||Crossover_α_|0.659_±_0.202|0.704_±_0.236|+0.045|
||**∆**P(win)|0.813_±_0.320|0.681_±_0.399|-0.132|
||AUC|0.310_±_0.221|0.234_±_0.236|-0.076|
||Monotonicity|0.997_±_0.041|0.977_±_0.093|-0.020|
||Nearest-win dist.|0.06_±_0.04|0.05_±_0.03|-0.006|
||KDE density shift|1.51_±_1.11|1.74_±_1.48|+0.230|
||<br>Path KDE density|-3.12_±_0.74|-3.21_±_0.81|-0.096|
||Cycle error|0.218_±_0.096|0.239_±_0.096|+0.021|
||Max_∥_**z**_∥_|2.02_±_0.58|1.93_±_0.51|-0.092|
|Linear (k-NN)|Success rate|0.845|0.543|-0.303|
||Crossover_α_|0.688_±_0.190|0.700_±_0.250|+0.012|
||**∆**P(win)|0.824_±_0.310|0.510_±_0.443|-0.314|
||AUC|0.290_±_0.206|0.182_±_0.234|-0.108|
||Monotonicity|0.998_±_0.027|0.966_±_0.128|-0.032|
||Nearest-win dist.|0.05_±_0.05|0.06_±_0.04|+0.005|
||KDE density shift|1.43_±_1.06|1.59_±_1.40|+0.162|
||Path KDE density|-3.16_±_0.82|-3.35_±_0.94|-0.197|
||<br>Cycle error|0.206_±_0.087|0.235_±_0.095|+0.029|
||Max_∥_**z**_∥_|2.05_±_0.63|1.87_±_0.56|-0.180|
|Optimal Transport|Success rate|0.837|0.720|-0.117|
||Crossover_α_|0.120_±_0.065|0.140_±_0.084|+0.020|
||**∆**P(win)|0.819_±_0.315|0.682_±_0.397|-0.137|
||AUC|0.752_±_0.301|0.629_±_0.364|-0.123|
||Monotonicity|0.998_±_0.041|0.995_±_0.059|-0.003|
||Nearest-win dist.|0.06_±_0.04|<br>0.05_±_0.03|-0.005|
||KDE density shift|1.50_±_1.11|1.74_±_1.48|+0.239|
||Path KDE density|-2.80_±_0.50|-2.74_±_0.40|+0.060|
||<br>Cycle error|0.242_±_0.094|0.237_±_0.113|-0.005|
||Max_∥_**z**_∥_|2.03_±_0.58|1.93_±_0.51|-0.103|
|Neural Flow|Success rate|0.931|0.731|-0.200|
||Crossover_α_|0.524_±_0.230|0.494_±_0.279|-0.030|
||**∆**P(win)|0.915_±_0.241|0.701_±_0.427|-0.213|
||AUC|0.468_±_0.253|0.390_±_0.332|-0.078|
||Monotonicity|0.999_±_0.013|0.996_±_0.025|-0.002|
||Nearest-win dist.|0.18_±_0.16|0.20_±_0.19|+0.024|
||KDE density shift|0.52_±_1.78|0.79_±_1.49|+0.270|
||<br>Path KDE density|-3.43_±_1.11|-3.62_±_1.37|-0.192|
||Cycle error|0.294_±_0.143|0.311_±_0.151|+0.016|
||<br>Max_∥_**z**_∥_|2.54_±_0.81|2.26_±_0.61|-0.285|
|Gradient Ascent|Success rate|1.000|0.998|-0.002|
||Crossover_α_|0.486_±_0.367|0.513_±_0.337|+0.027|
||**∆**P(win)|0.986_±_0.076|0.969_±_0.139|-0.017|
||AUC|0.545_±_0.355|0.517_±_0.321|-0.029|
||Monotonicity|0727_±_0227|0749_±_0209|+0021|
||Nearest-win dist.|. .<br>0.15_±_0.12|. .<br>0.15_±_0.14|.<br>+0.005|
||KDE density shift|0.63_±_1.40|0.78_±_1.46|+0.152|
||<br>Path KDE density|-4.63_±_1.40|-4.20_±_1.25|+0.430|
||Cycle error|0.406_±_0.184|0.410_±_0.178|+0.004|
||Max_∥_**z**_∥_|3.95_±_1.74|3.91_±_1.56|-0.039|

15 

Play Like Champions: Counterfactual Feedback Generation in Latent Space 

A PREPRINT 

### **E Additional Results** 

#### **E.1 Model Interpretability** 

To verify that the Guided VAE’s outcome classifier grounds its predictions in strategically meaningful features, we analyze its decision process using SHapley Additive exPlanations (SHAP) as shown in Fig. 2 and Fig. 3. SHAP values provide a unified measure of feature importance by attributing the log-odds of the predicted outcome to the individual input features. The mean absolute SHAP values highlight the top global contributors to the win-probability prediction, confirming that the model relies on core economic and macroscopic indicators rather than spurious correlations. Furthermore, the SHAP beeswarm plot reveals the distribution of these impacts across the test. It visualizes both the magnitude and the direction of the feature effects, illustrating how higher or lower values of specific features correlate with the predicted likelihood of winning. This transparency is crucial, as it ensures that the counterfactual paths generated by traversing the latent space correspond to interpretable, domain-consistent shifts in player behavior. 

<!-- Start of picture text -->
P(win) SHAP   Top-8 Features (both players)<br>foodUsed<br>mineralsKilledArmy<br>vespeneKilledArmy<br>mineralsUsedCurrentArmy<br>mineralsUsedActiveForces Group / Player<br>early<br>mineralsKilledEconomy mid<br>late<br>final<br>mineralsUsedCurrentEconomy econDelta<br>meta<br>foodMade Player 0 (subject)<br>Player 1 (opponent)<br>0.00 0.01 0.02 0.03 0.04 0.05 0.06 0.07<br>Mean |SHAP value|<br><!-- End of picture text -->

Figure 2: Mean absolute SHAP values for the top-8 input features of the GuidedVAE win-probability classifier _P_ ( _win_ ). 

<!-- Start of picture text -->
SHAP vs. Feature Value     P(win)<br>final_foodUsed final_mineralsKilledArmy final_vespeneKilledArmy final_mineralsUsedCurrentArmy<br>0.40.3 0.50.4 0.6 0.2<br>0.20.1 0.30.2 0.4 0.1<br>0.0 0.1 0.2 0.0<br>0.1 0.10.0 0.0 0.1<br>0.2<br>0.3 0.2 0.2 0.2<br>0.3<br>2 1 0 1 2 1 0 1 2 3 4 5 6 7 1 0 1 2 3 4 5 6 7 2 1 0 1 2 3 4<br>Feature value Feature value Feature value Feature value<br>final_mineralsUsedActiveForces final_mineralsKilledEconomy final_mineralsUsedCurrentEconomy late_foodMade<br>0.3 0.2 0.15<br>0.2 0.30.2 0.1 0.10<br>0.1 0.05<br>0.1 0.0<br>0.0 0.00<br>0.0<br>0.1 0.1 0.1 0.05<br>0.2 0.2 0.2 0.10<br>1 0 1 2 3 4 1 0 1 2 3 4 5 6 7 2 1 0 1 2 3 4 2 1 0 1 2 3 4 5<br>Feature value Feature value Feature value Feature value<br>SHAP SHAP SHAP SHAP<br>SHAP SHAP SHAP SHAP<br><!-- End of picture text -->

Figure 3: SHAP dependence plots for the top-8 features by mean _|SHAP |_ for _P_ ( _win_ ). 

### **F Example Feedback Reports** 

Fig. 4 and Fig. 5 are examples of the output, informing the user about the counteractual latent space path, and which parameters they should focus on. 

16 

Play Like Champions: Counterfactual Feedback Generation in Latent Space 

A PREPRINT 

<!-- Start of picture text -->
Latent Space Counterfactual Improvement Path<br>Latent space (UMAP) + improvement path Win probability along path<br>10 Waypoints 1.0 Loss zone<br>Start (loss) Win zone<br>Target (win) Decision boundary<br>8<br>0.8<br>6<br>0.6<br>4<br>0.4<br>2<br>0.2<br>0<br>2 Blue = loss density  |  Red = win density 0.0<br>5.0 2.5 0.0 2.5 5.0 7.5 10.0 12.5 15.0 0.0 0.2 0.4 0.6 0.8 1.0<br>UMAP1 Path progress  (0=start, 1=end)<br>UMAP2 P(win)<br><!-- End of picture text -->

Figure 4: UMAP latent space projection with the counterfactual path shown. 

17 

Play Like Champions: 

Counterfactual Feedback Generation in Latent Space A PREPRINT 

## Three-Signal Feedback Report 

<!-- Start of picture text -->
Full path  (start -> end)<br>final_mineralsKilledArmy<br>final_mineralsUsedCurrentArmy<br>final_mineralsUsedActiveForces<br>final_vespeneKilledArmy<br>final_mineralsUsedCurrentEconomy<br>final_vespeneUsedCurrentArmy<br>final_vespeneUsedActiveForces<br>late_mineralsUsedCurrentEconomy<br>final_mineralsLostEconomy<br>final_mineralsUsedCurrentTechnology<br>2000 1000 0 1000 2000 3000 4000<br>Delta<br>Minimum viable  (waypoint 18/19  (P(win)=0.681))<br>final_mineralsKilledArmy<br>final_mineralsUsedCurrentArmy<br>final_mineralsUsedActiveForces<br>final_vespeneKilledArmy<br>final_mineralsUsedCurrentEconomy<br>final_vespeneUsedCurrentArmy<br>final_vespeneUsedActiveForces<br>late_mineralsUsedCurrentEconomy<br>final_mineralsLostEconomy<br>final_mineralsUsedCurrentTechnology<br>2000 1000 0 1000 2000 3000 4000<br>Delta<br>P(win)-gain weighted<br>final_mineralsKilledArmy<br>final_mineralsUsedActiveForces<br>final_mineralsUsedCurrentArmy<br>final_vespeneKilledArmy<br>final_mineralsUsedCurrentEconomy<br>final_vespeneUsedActiveForces<br>final_vespeneUsedCurrentArmy<br>final_mineralsUsedCurrentTechnology<br>final_mineralsLostEconomy<br>late_mineralsCurrent<br>100 50 0 50 100 150 200<br>18 Delta<br><!-- End of picture text -->

Figure 5: Feedback report with three distinct user interpretable signals. 

Play Like Champions: Counterfactual Feedback Generation in Latent Space 

A PREPRINT 

### **G Data and Code Repositories** 

Anonymized version of our code and the pre-processed tensor data, as well as the model checkpoint are available at: https://anonymous.4open.science/r/SC2_LatentTrainer-1E5B/. The original data repository is: https://huggingface.co/datasets/Kaszanas/SC2EGSet 

19
