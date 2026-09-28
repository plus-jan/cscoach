---
id: pandaskill
title: 'PandaSkill - Player Performance and Skill Rating in Esports: Application to
  League of Legends'
authors: Maxime De Bois, Flora Parmentier, Raphaël Puget, Matthew Tanti, Jordan Peltier
year: 2025
venue: arXiv preprint
url: https://arxiv.org/abs/2501.10049
arxiv_version: 2501.10049v2
license: arXiv default (code CC BY-SA 4.0) — check before redistributing
pdf_sha256: 3cab642732170ab7
converted: '2026-09-28'
converter: pymupdf4llm
---

# PandaSkill - Player Performance and Skill Rating in Esports: Application to League of Legends

> Auto-converted from PDF. Tables, equations and figure text may be garbled — check the original PDF before quoting numbers.

<!-- cscoach-notes:start -->
## cscoach notes (hand-written — preserved on re-conversion)

**Authors:** Maxime De Bois, Flora Parmentier, Raphaël Puget, Matthew Tanti, Jordan Peltier (PandaScore). arXiv 2501.10049v2.
Code/data: https://github.com/PandaScore/PandaSkill (CC BY-SA 4.0).

- **Relevance:** high for player-level ratings (M8) and for validation practice.
- **Verified claims:**
  - Data: 5 years pro LoL (2019-09-15 → 2024-09-15), 37,388 games, 4,927 players (Table II).
  - PScore: one XGBoost per role predicts win from the player's end-game stats → predicted probability →
    **percentile transform** (0–100) per role. **Monotone constraints on all features.**
  - Win model: accuracy 90.74%, **ECE 0.93%** (vs PlayeRank 1.28%, PI 2.28%); without monotone constraints
    91.79% but uninterpretable interactions.
  - Ratings: OpenSkill in **free-for-all** mode ranked by PScore (team outcome ignored) + **meta rating per
    region** for isolated pools. Forecasting via rolling 1-month windows; best inter-region ACC 70.07–70.23%.
  - Expert concordance: majority 80.63%, unanimity 88.98% (PScore + Meta FFA OpenSkill).
- **Corrections vs. synthesis:** consistent with the synthesis; note the performance model uses **end-game**
  stats (outcome-correlated) — fine for ratings, unusable as in-round features.
- **Use in project:**
  - M8: rate players by per-round/per-match value (WPA, xK-diff) ranked within the lobby, independent of the
    match result → "free-for-all" update; conservative display value μ − 3σ (or our credible intervals).
  - "Isolated rating pools" ≈ our tiers/platforms (MM vs FACEIT): contextual + meta rating is a candidate
    for cross-tier comparison (M8.1 ADR).
  - Confirms our choices: monotone GBDT (docs/specs/06_parameters.md, monotone constraints, A-27), ECE as a primary metric,
    percentile/role normalisation for cross-role fairness (CS roles: entry, AWP, support, lurker, IGL).
  - Role fairness check: Wasserstein distance between role rating distributions (PScore 0.09–0.44).
- **Caveats:** 5-fold CV not grouped by match/time for the PScore model; pro-only; LoL-specific features.
<!-- cscoach-notes:end -->

## Full text

JOURNAL OF L<sup>A</sup> TEX CLASS FILES, VOL. 14, NO. 8, AUGUST 2021 

1 

# PandaSkill - Player Performance and Skill Rating in Esports: Application to League of Legends 

Maxime De Bois , Flora Parmentier, Rapha¨el Puget, Matthew Tanti, and Jordan Peltier 

**_Abstract_ —To take the esports scene to the next level, we introduce PandaSkill, a framework for assessing player performance and skill rating. Traditional rating systems like Elo and TrueSkill often overlook individual contributions and face challenges in professional esports due to limited game data and fragmented competitive scenes. PandaSkill leverages machine learning to estimate in-game player performance from individual player statistics. Each in-game role is modeled independently, ensuring a fair comparison between them. Then, using these performance scores, PandaSkill updates the player skill ratings using the Bayesian framework OpenSkill in a free-for-all setting. In this setting, skill ratings are updated solely based on performance scores rather than game outcomes, hightlighting individual contributions. To address the challenge of isolated rating pools that hinder cross-regional comparisons, PandaSkill introduces a dual-rating system that combines players’ regional ratings with a meta-rating representing each region’s overall skill level. Applying PandaSkill to five years of professional League of Legends matches worldwide, we show that our method produces skill ratings that better predict game outcomes and align more closely with expert opinions compared to existing methods.** 

**_Index Terms_ —Esports, League of Legends, player performance, skill rating, TrueSkill, OpenSkill.** 

## I. INTRODUCTION 

**R** ATING and rankingpart of competitive sportsathletes[1],has[2].alwaysProvidingbeen simplean integraland quantifiable measures of player performance is beneficial for both professionals and fans. Such systems can be used by the industry for coaching and scouting future talents or to drive fan engagement by unveiling key game insights [3]. 

Recently, the increased availability of data has opened the way to more advanced, data-driven systems. Unlike traditional rating systems that rely on predefined formulas [4], datadriven approaches leverage large and fine-grained datasets with machine learning techniques to analyze player performance in a game [5]–[8]. These methods can model more complex aspects of the game, such as the role of a given player or their contribution to the outcome of the game [6]. 

A similar need for performance evaluation exists in esports, with titles such as League of Legends (LoL) or CounterStrike, which require precise metrics to assess player skill [9]. Such systems can benefit players through better matchmaking [10] and novel insights [11], [12], professional teams with quantified assessments of team performance [13], [14], and other actors in the ecosystem such as betting operators [15], [16]. 

All authors are from PandaScore. Email: maxime.debois@pandascore.co This work has been submitted to the IEEE for possible publication. Copyright may be transferred without notice, after which this version may no longer be accessible. 

As video games, esports titles often have easier access to very detailed data compared to traditional sports, which often rely on tracking devices [17] or human annotations [18]. In fact, publishers often provide means to access the data, such as demo files for Counter Strike or APIs for LoL and Dota 2 [9], [12], [15], [16], [19]. 

On the other hand, the game state is generally far more complex [9]. For example, in LoL, a player chooses between more than 150 characters (called _Champions_ ) to play in a game. Each Champion has its own style of play and contributes differently to the team’s victory. Players often play a specific role in a team, and even for a given role, it is common to see different playstyles develop [19]. Moreover, the game’s balance is updated frequently, often adding new game mechanics. Something that was effective in one version might not be in the next. 

Recent research has explored methods for evaluating player performance in games [11], [19]. Although analyzing a player’s past performances can provide a reasonable estimate of their general skill level, it fails to capture the complete picture. A player’s performance in a game is strongly influenced by the strength of their opponents. Facing weaker opponents may lead to exceptional performance, which might not accurately reflect their overall skill level. Algorithms such as Elo, TrueSkill, or OpenSkill [20]–[22] are usually used to estimate the skill of a player, based on the outcomes of past games and the strength of the opponents. However, these algorithms do not take into account the individual contribution of a player to the outcome of the game. Moreover, in esports, the lower number of games played per player, compared to non-professional gaming, slows down the calibration of these algorithms. Additionally, the scene is often fragmented, with some players rarely facing each other or even never at all. This raises the question of how to compare players from groups of players that have never played against each other. For instance, in LoL, apart from the two yearly international tournaments, players only face other players from the same region. This challenge, known as _isolated rating pools_ , where player skill ratings evolve independently within isolated regions, has been acknowledged in chess literature and remains an open problem [23]. 

To address these challenges, we propose _PandaSkill_ , a two-step framework to evaluate player performance and skill rating in esports. While the player performance represents the individual contribution of the player to the outcome of a given game, their skill rating represent how good they are in general compared to other players. We can summarize our contributions as follows: 

JOURNAL OF L<sup>A</sup> TEX CLASS FILES, VOL. 14, NO. 8, AUGUST 2021 

2 

- We propose an estimation of the player’s performance in a game by using machine learning models that predict the outcome of the game from the player’s statistics. By directly linking the performance score to the predicted probability, we make the methodology independent of the underlying model. Moreover, we ensure the fairness of the model by accounting for the different roles existing in the game. 

- The skill ratings of the players are computed from all the past performance scores. We use the Bayesian framework OpenSkill in a novel free-for-all approach, where players are evaluated based on their performance relative to each other, independent of their teams. This way, the method focuses more on the players’ individual performances. 

- We highlight the challenge of isolated rating pools in esports, hurting cross-regional comparisons. To alleviate the issue, we propose that the player skill rating be a combination of their contextual rating (within their region) and a meta rating (representing the skill level of the region). Improving cross-regional comparisons, this dual-rating system enables a more accurate evaluation of players on a global scale. 

- We apply the framework to five years of professional League of Legends matches from all the regions in the world. Compared to other methods in the literature, we demonstrate that our approach produces ratings that better predict the outcome of a game and are more in concordance with human experts. 

- The source code and data associated with this paper can be found in the PandaSkill GitHub repository, alongside a web application to visualize the player performances and skill ratings. By making our tools publicly available, we hope to encourage further research and practical applications in esports. 

The remainder of the paper is structured as follows. In Section II, we review related work on player performance evaluation and rating systems in esports. We provide the reader with some background knowledge about League of Legends in Section III. Section IV details our proposed methodology. In Section V, we present the experimental setup, data used, and results of our experiments. Finally, we discuss the implications of our findings and potential directions for future research in Section VI. 

## II. RELATED WORK 

In this section, we review existing data-driven player performance and skill rating evaluation systems. We focus mostly on esports or video game applications. However, since the field is relatively new, when relevant, we also discuss work from traditional sports. 

## _A. Player Performance in a Game_ 

Evaluating player performance in esports involves a variety of methodologies, ranging from basic metrics to the use of machine learning models. 

The easiest way is to directly use one player statistic computed at the end of the game, such as the kill-death-assist 

ratio (KDA) in LoL [24], or kill-death ratio in Counter-Strike [25]. 

While easy to use, these metrics lack depth and do not tell the full story of what happened during the game. This led the community to craft more descriptive metrics, probably the most iconic of them in esports being the HLTV Rating for Counter-Strike [9], [15]. First introduced in 2010 and later improved with versions 2.0 and now 2.1, it combines player end-game statistics into a single value representing how much better the player performed in a given game compared to the average [25]. 

Likewise, Demediuk _et al._ proposed a framework to compute the current performance of a player during a game, which they called Performance Index (PI), for the esports game Dota 2 (which is similar to LoL) [19]. The PI is computed as the weighted sum of the percentiles of the player’s statistics. The weights are derived from random forest models trained to predict the game outcome from the player statistics. Multiple random forest models were trained, one per role and predefined playstyle archetype to account for the complexity of the game. 

A similar methodology has been followed in soccer with the PlayeRank framework [6]. They trained a single Support Vector Classifier (SVC) model to predict the game outcome from team statistics (e.g., number of passes). The performance of a player is then computed as the share of the team statistic that can be attributed to the player. They also explored a role-based version of their framework, where the weights are derived from players of similar roles. 

Alternatively, researchers have explored the creation of more descriptive metrics, albeit not necessarily fully representative of the player performance. For instance, for Counter-Strike, Xenopoulos _et al._ developed the Win Probability Added (WPA) framework to value players’ actions based on changes in their team’s chances of winning [15]. In LoL, Maymin proposed identifying _smart kills_ and _worthless deaths_ from the game events, as these are considered to have a strong impact on the outcome of the game [11]. 

## _B. Player Skill Rating_ 

The simplest way to rate the skill of players and rank them is to average player metrics representative of their past performance. For instance, PlayeRank used the exponentially weighted moving average (EWMA) technique over the performance scores of the player in past games, weighting recent performances higher [6]. On the other hand, Xenopoulos _et al._ used averages of their proposed WPA metric and HLTV Rating 2.0 over a rolling window of one month [15]. 

However, averaging on recent player’s performances does not take into account the strength of the opposing players in the calculation. Consequently, a high rating can be achieved by consistently competing against weaker opponents, resulting in an inflated ranking. In the context of chess, the Elo rating system has been widely adopted as a method to address this issue [20]. Elo adjusts a player’s rating based on both the outcome of the match and the relative strength of the opponent, ensuring that victories against stronger opponents yield a 

JOURNAL OF L<sup>A</sup> TEX CLASS FILES, VOL. 14, NO. 8, AUGUST 2021 

3 

greater rating increase, while wins against weaker opponents have a smaller impact. 

The Glicko and later the Glicko-2 rating systems improve upon Elo by introducing a measure of uncertainty into a player’s rating, making it one of the first Bayesian rating systems [26], [27]. The uncertainty represents the reliability of the rating. Each player starts with a high uncertainty value which slowly decreases game after game. Both Elo and Glicko ratings have been extensively used with applications in football [1], [2], in casual LoL matchmaking [9], and in professional Dota 2 teams rankings [16]. 

Nonetheless, both Elo and Glicko are designed for twoplayer games, which most esports titles are not. When applied to two-team games (which is very common), the individuality of the players is not considered. To address this problem in the context of casual matchmaking, Microsoft Research developed TrueSkill and TrueSkill2 to be used in first-person shooters (FPS) such as Halo or Gears of War [21], [28]. It differs from Elo and Glicko by updating the rating after each game instead of a given time period, and by working in multi-team/multiplayer contexts. One of the additions of TrueSkill2 is the use of additional metrics about the players, such as the number of kills scored or the tendency to quit the game. 

A key downside of TrueSkill, however, is that it remains a proprietary framework. To provide a free and open-source alternative, OpenSkill was developed [22]. Thanks to the use of Bayesian approximation, OpenSkill is also faster, which is convenient in video games when there are a lot of matches to compute [29]. 

Another alternative to TrueSkill has been proposed by Delalleau _et al._ to promote fun in casual matchmaking for the FPS Ghost Recon Online [10]. They used a neural network to predict both balance and player enjoyment from the players’ profiles (previous game statistics like number of kills or firing accuracy). Pradhan _et al._ explored a different approach, using a multi-criteria decision-making system to rank Dota 2 teams in a given season based on team metrics [16]. 

## _C. Position of Our Work_ 

In this paper, we propose a two-step end-to-end player skill rating evaluation. First, we compute the performance score of each player in a game from their end-game statistics. Then, we update the skill ratings of the players based on their respective performance in the game. This methodology is applied to five years of professional League of Legends. 

When calculating performance scores, our main goal is to base the evaluation on features that are most strongly tied to a team’s chances of winning. Existing methods approach this by combining end-game statistics in a linear way. In contrast, we tie the performance score directly to the predicted probability of winning, estimated by a machine learning model that predicts the outcome of the game from the player’s endgame statistics. This approach allows us to capture more complex relationships in the data, leading to a more accurate estimation of performance. 

As for the evaluation of the skill ratings, to the best of our knowledge, there exists no framework that simultaneously uses 

the player performance in-game whilst taking into account the strength of the players in the game. Moreover, all rating systems are prone to the isolated rating pools challenge, where skill ratings of players evolve independently due to a low number of games between certain players [23]. As we highlight the impact of this issue on League of Legends professional ratings, we address it by combining a player’s rating within their region with the rating of the region itself. 

III. BACKGROUND ON LEAGUE OF LEGENDS 

<!-- Start of picture text -->
Top<br>Jungler<br>Mid<br>Support<br>Bot<br>Nexus Tower Inhibitor<br>Baron Nashor Drake<br>Lanes & Roles<br><!-- End of picture text -->

Fig. 1: Annotated minimap of League of Legends. 

## _A. Game Layout_ 

League of Legends (LoL) is a competitive Multiplayer Online Battle Arena (MOBA) game. In LoL, two teams of five players each compete on a map called _Summoner’s Rift_ , with the goal of destroying the enemy _Nexus_ , located inside the enemy base and surrounded by _Towers_ and _Inhibitors_ . The two bases are connected by three paths, commonly called lanes: the top lane, the mid lane, and the bottom lane. Figure 1 shows the simplified LoL map. At regular time intervals, _Minions_ spawn in the two bases and push down the lanes, attacking nearby enemy buildings. To destroy the enemy base, the players assist the Minions in their efforts. Between the lanes is the jungle, where neutral monsters can be defeated. The strongest ones, such as the _Drake_ or the _Baron Nashor_ , provide powerful bonuses to the team that defeats them. 

## _B. Players_ 

Each player embodies a character called a _Champion_ . All Champions have a distinct set of abilities, strengths, and weaknesses. In a game, a player is also assigned a role. There are five different roles, one for each player: _Top_ , _Jungler_ , _Mid_ , _Bottom_ , and _Support_ . The roles represent both the area of the 

JOURNAL OF L<sup>A</sup> TEX CLASS FILES, VOL. 14, NO. 8, AUGUST 2021 

4 

map the player is supposed to play in during the early stages of the game (see Figure 1) and the job of the player within the team. Here is a basic general understanding of the roles: 

- **Top** : plays in the top lane; strong and independent; often provides tankiness and map control to the team. 

- **Jungle** : plays between the lanes; moves around the map to apply pressure on the different lanes and help securing objectives. 

- **Mid** : plays in the mid lane; has the most agency out of the laners in the early to mid game due to their central position in the map; often provides burst damage to the team. 

- **Bot** : plays with the Support player in the early game in the bottom lane; provides sustained damage to the team; scales well into the late game by obtaining more gold. 

- **Support** : plays with the Bot player in the early game in the bottom lane; does not need a lot of gold to perform; helps the team by providing visionand utility (e.g., healing, buffs, control). 

## _C. General Game Strategy_ 

A typical game of League of Legends lasts between 20 and 50 minutes. During this time, each player tries to become stronger by leveling up and buying powerful items with the gold obtained by killing Minions, neutral monsters, enemy Champions or buildings. Securing important neutral objectives, such as Drakes or the Rift Herald, also provides valuable advantages. When they are strong enough, they can attempt to break into the enemy base by sieging and fighting the enemy team together. 

## _D. The Esports Ecosystem_ 

The highest competition tier of League of Legends is managed by the game publisher Riot Games. The world is divided into geographic regions, each having its own league and tournament format. Twice a year, on the occasions of the Mid-Season Invitational (MSI) and the Worlds, the best teams from each region compete against each other. For years, the international scene has been dominated by Korea and China, followed by Europe and North America. As the esports scene matures, other regions (e.g., Asia-Pacific) are starting to emerge as serious contenders. 

## IV. PANDASKILL 

PandaSkill computes the players’ skill ratings in two steps. First, after each game, it computes the performance of the players in the game. Then, it uses the player performances to update the players’ skill ratings. Table I shows a practical example of the framework applied to a game. 

## _A. Measuring the Performance Score of Players in a Game_ 

Measuring a player’s performance in a game is challenging due to the absence of a known ground truth. Similarly to the PlayeRank and PI frameworks, we use the outcome of the game as a proxy for the player’s performance [6], [19]. The idea is that if a player played well during a game, 

their performance should be reflected both in their end-game statistics and in the outcome of the game. 

More specifically, we propose the following methodology to calculate the Performance Score (PScore) of a player in a game: 

- 1) For each role, we train a machine learning model that predicts the probability of a player winning the game based on their end-game statistics (e.g., number of kills). 

- 2) The predicted probabilities are then transformed into percentiles. This transformation is learned for each model on the training data. 

- Compared to PI and PlayeRank, our approach has the 

- following advantages: 

- Both PI and PlayeRank calculate the performance of the players by doing a linear combination of their endgame statistics, with weights that are derived from a model trained to predict the game outcome. By linking the performance scores directly to the model’s predicted probabilities, we account for the model’s non-linearity, enabling a more complex calculation of the player’s performance score. 

- We ensure a fair cross-role comparison as all the scores are normalized on the same scale (from 0 to 100) by the percentile transformation, independent of the underlying model. This makes it possible to compare players with different roles, which is not the case for PlayeRank. 

- Our approach is model-agnostic as long as the model can output probabilities. Both PI and PlayeRank work with specific models from which feature importance can be easily computed (i.e., random forest for PI and linear SVC for PlayeRank). 

Three qualities should be considered in order to choose which machine learning algorithm to use to compute the performance scores: 

- **Strong predicting capability** : A model without a good predicting capability will fail at capturing the nuances of the games. 

- **Calibrated probabilities** : The model should produce probabilities that closely reflect reality; it is particularly important as performance scores are directly derived from the probabilities. 

- **Interpretability** : It should be possible to explain how the performance scores are determined to ensure the system is transparent and trustworthy. 

In this paper, we used XGBoost models as they satisfy these qualities well. 

## _B. Estimating the Skill Rating of the Players_ 

_1) OpenSkill:_ We base the evaluation of the skill rating of the players on the OpenSkill framework [22]. It has the advantage of being both open and working in multi-team or multi-player settings, which is not the case for Elo, Glicko, or TrueSkill [20], [21], [26]. 

OpenSkill models the player’s skill rating as a Gaussian distribution with the average skill of the player _µ_ and an estimation of its uncertainty _σ_ . Specifically, we represent the skill _Si_ of player _i_ as: 

5 

JOURNAL OF L<sup>A</sup> TEX CLASS FILES, VOL. 14, NO. 8, AUGUST 2021 

|**Player**|**Team**|**Role**|**PScore**|**Skill Rating**|
|---|---|---|---|---|
|Viper|HLE|Bot|82.52|92.68 (+0.50)|
|Faker|T1|Mid|81.02|84.43 (+0.45)|
|Gumayusi|T1|Bot|74.20|88.93 (+0.29)|
|Peanut|HLE|Jungle|69.88|91.84 (+0.20)|
|Zeka|HLE|Mid|59.09|89.61 (+0.17)|
|Keria|T1|Support|58.76|90.26 (+0.05)|
|Delight|HLE|Support|52.95|90.84 (-0.11)|
|Oner|T1|Jungle|43.11|89.15 (-0.20)|
|Doran|HLE|Top|31.97|86.10 (-0.30)|
|Zeus|T1|Top|28.29|86.73 (-0.81)|

(a) Player performances (PScore) and updated skill ratings 

<!-- Start of picture text -->
f(x) = 4.432<br>7 = Kill-life-assist ratio +3.21<br>486.47 = Gold per minute +0.75<br>0.12 = Objective contest loserate 0.56<br>4 = Largest multi kill +0.52<br>1234.05 = Damage taken total kills ratio +0.43<br>0 = Worthless death ratio +0.37<br>485.07 = Experience per minute +0.16<br>0.12 = Objective contest winrate +0.07<br>0.43 = Free kill ratio +0.06<br>6 other features 0.01<br>0 2 4<br>E[f(X)] = 0.56<br>SHAP Values<br><!-- End of picture text -->

(b) Explanation of Faker’s PScore with SHAP values 

TABLE I: Analysis of PandaSkill applied to game 2 of LCK Summer 2024 lower-bracket final, opposing Hanwha Life Esports (HLE) to T1 (victory of T1). The table highlights player skill ratings updated based on individual performance (PScore) rather than team outcomes. 

The ratings of all players are initialized to the default values of _µi_ = 25 and _σi_ = 25 _/_ 3, as it is generally done in Bayesian rating systems [21], [22]. After a game, both _µi_ and _σi_ are updated based on the outcome of the player’s team. The updates are derived from Bayesian inference, adjusting the player’s skill distribution to reflect the new information provided by the game outcome. Formally, the update mechanism can be described by the following equation: 

where: 

- ( **_µ_**<sup>_t_</sup> , **_σ_**<sup>_t_</sup> ) represent the ratings of all the players in the game before the game at time step _t_ ; 

- ( **_µ_**<sup>_t_+1</sup> , **_σ_**<sup>_t_+1</sup> ) denote their ratings after the game at time step _t_ + 1; 

- Ω is the Bayesian update made by the OpenSkill framework. 

Since probabilistic estimates of skill ratings are often impractical to use directly (e.g., for creating rankings), they can be transformed into single-value estimates by taking the lower bound _θi_ = _µi −_ 3 _· σi_ . This provides a conservative estimate of the player’s skill rating, ensuring a 99.7% likelihood that the player’s true rating is higher. 

_2) Free-For-All (FFA):_ Natively, OpenSkill does not use the performance of the players to adjust the rating updates (which is also the case for Elo, Glicko, or TrueSkill). To incorporate the evaluation of the performance of the players in the game into the rating updates, we suggest framing the ratings updates as a free-for-all (FFA) game. In this setting, all players compete against each other. After a game, they are ranked based on their individual PScore and their skill ratings are updated based on this ranking. The update mechanism can then be written as follows: 

where: 

- **PScore** represents the performance scores of the players in the game; 

- ΩFFA is the Bayesian update made by the OpenSkill framework in the free-for-all setting. 

Using the FFA setting has several consequences: 

- The outcome of the game doesn’t directly impact the update of the skill ratings. This means that a player can see their rating improve due to a good performance, even if they lost. 

- Rating updates depend on the relative performance the player has achieved compared to the other players in the game. To increase their rating, the player needs to perform better than the other players (regardless of their team). 

_3) Contextual and Meta Ratings:_ A significant challenge in global player ranking systems is the potential for ratings of players from different contexts (e.g., different regions or competition tiers) to evolve independently, creating isolated rating pools where direct comparisons become difficult. This is particularly problematic for some esports titles (e.g., League of Legends), where inter-regional play may be infrequent, limited to specific international tournaments. 

To address this issue, we propose to model the skill rating of a player as the combination of two distinct ratings: a _contextual rating_ and a _meta rating_ . The contextual rating represents the player’s skill within their context (e.g., region), while the meta rating represents the skill level of the context itself. This means that all players from the same context share the same meta rating. 

We define the overall skill rating of a player as the sum of their contextual ( _µ_<sup>ctx</sup> _i_<sup>_, σ_</sup> _i_<sup>ctx)andmeta(</sup><sup>_µ_meta</sup> _i , σi_<sup>meta</sup> ) ratings to 

6 

JOURNAL OF L<sup>A</sup> TEX CLASS FILES, VOL. 14, NO. 8, AUGUST 2021 

capture both the skill of the player’s within their context, and the context of the player: 

After a game, using the OpenSkill framework, only one of the two ratings is updated depending on the context of the opponents in the match. If both teams share the same context, then the contextual rating of each player is updated. On the other hand, if the teams have different contexts (e.g., they are coming from different regions), we update the ratings of the teams’ contexts. The following details how the updates are made in both cases: 

- **Updating contextual ratings** : If all opponents are from the same context, we update only the contextual ratings. Because all the players in the game share the same meta rating, we do not need to use the meta ratings to update the contextual ones. As a consequence, updating the contextual ratings can be seen as standard rating update as described earlier. Formally, we can write: 

- **Updating meta ratings** : If the opponents are from different contexts, we update only the meta ratings. Contrary to the contextual rating updates, here we use the contextual ratings as offsets to the meta ratings to take into consideration the individual strength of the players in the game. The offsetting technique has been used in TrueSkill2 as an efficient way to balance the skill ratings of players playing as a squad and solo players [28]. The meta ratings update can be written as follows: 

where **_θ_**<sup>ctx</sup><sup>_,t_</sup> are the players lower-bound contextual ratings in the game. 

However, there are two issues with Equation 7. First, all the resulting _µ_<sup>meta</sup> _i_<sup>_,t_+1</sup> are shifted by _θi_<sup>ctx</sup><sup>_,t_</sup> . We need to reverse the offset to preserve the original scale of _µ_<sup>meta</sup> _i_<sup>_,t_</sup> . Moreover, **_µ_**<sup>meta</sup><sup>_,t_+1</sup> contains multiple different meta rating updates for players sharing the same context. These variations arise from the variability in the players’ contextual ratings and their individual performances in the game. In order to have the same updated meta rating for players that share the same context, we need to derive a single updated meta rating for each context in the game. We chose to average the updates for the same context as it ensures that the meta rating reflects the collective contributions and performances of all players associated with the context. The post-processing of the updates can be written as follows: 

where _j_ represents a player in the game, and _n_ is the number of players in the game. 

Note that, in both Equations 6 and 7, while we used the FFA OpenSkill setting, we can also use the standard OpenSkill, which bases the updates on the game outcome, if we prefer. 

Now that we know how to update the contextual and meta ratings, we need to handle the following edge case. When a player’s context changes (e.g., the player goes to another team in another region), their contextual rating might not be representative to the player’s skill level in this new context. When that happens, we suggest resetting _σi_<sup>ctx</sup> to its default value of 25 _/_ 3 to represent increased uncertainty in the contextual rating of the player in this new context. 

## _C. Ranking & Player Comparison_ 

PandaSkill can be used to rank and compare players. In particular, the probability of player _i_ being better than player _j_ can be estimated using the cumulative distribution function (CDF) Φ: 

To rank all the players, instead of using the player comparison probability estimation, which would be too computationally heavy, we can use the lower bound _θi_ = _µi −_ 3 _· σi_ as a single-value estimate. While this approach is computationally efficient and easy to interpret, it may result in lower _θi_ values for players with fewer games (e.g., new professional players or substitutes) due to higher uncertainty ( _σi_ ). However, this ensures that the rankings reflect not only performance but also the confidence in the player’s skill rating. 

## V. EXPERIMENTS 

In this section, we describe the experiments we conducted applying PandaSkill to the esports title League of Legends. The general goal is to assess the fairness and relevance of the PScores and skill ratings, both across roles and regions. Because, there is no known ground truth for neither of them, we must rely on proxy metrics and experiments. 

## _A. Data_ 

_1) Raw Data:_ We used publicly available data from professional League of Legends games obtained through the Leaguepedia API [30]. The dataset comprises games from all the professional regions worldwide, spanning five years from 2019-09-15 to 2024-09-15. The end date coincides with the end of the last major regional tournaments before the start of Worlds 2024. Table II provides a detailed view of the 

JOURNAL OF L<sup>A</sup> TEX CLASS FILES, VOL. 14, NO. 8, AUGUST 2021 

7 

TABLE III: Description of player statistics used as input features to the performance score models. 

|**Feature**|**Description**|
|---|---|
|**Kill-life-assist ratio (KLA)**|Ratio of enemy player kills compared to deaths. Computed as (_kills_+_assists_)_/_(_deaths_+ 1).|
|**Gold per minute**|Rate at which the player obtained gold in the game.|
|**Experience per minute**|Rate at which the player gained experience in the game.|
|**Creep score per minute**|Rate at which the player slays Minions or neutral monsters, procuring gold.|
|**Wards placed per minute**|Rate at which the player placed wards to provide vision for the team.|
|**Damage dealt total kills ratio**|Amount of damage dealt to players, normalized by the total number of kills in the game.|
|**Damage dealt per gold total kills ratio**|Player damage dealing efficiency, computed as _Damage dealt total kills ratio_ further normalized by gold obtained.|
|**Damage taken total kills ratio**|Amount of damage taken from players, normalized by the total number of kills in the game.|
|**Damage taken per gold total kills ratio**|Player damage tanking efficiency, computed as _Damage taken total kills ratio_ further normalized by gold obtained.|
|**Largest multi kill**|Maximum number of player kills in a short time window.|
|**Largest killing spree total kills ratio**|Maximum number of successive player kills without dying, normalized by the total number of kills in the game.|
|**Worthless death ratio**|Ratio of player deaths that did not benefit the team in any way.|
|**Free kill ratio**|Ratio of player kills that resulted in a worthless death for the enemy.|
|**Objective contest winrate**|Share of neutral objectives contested and won by the player.|
|**Objective contest loserate**|Share of neutral objectives contested but lost by the player.|

composition of this dataset. We note the large discrepancy between the number of games in inter-region tournaments (Worlds and MSI) compared to regional ones. 

TABLE II: Description of the dataset for major competitions. 

|**Competition**|**Region**|**Editions**|**Games**|**Players**|
|---|---|---|---|---|
|**Worlds**|Global|5|592|353|
|**MSI**|Global|4|312|166|
|**LCK**|Korea|10|2,438|198|
|**LPL**|China|12|3,643|283|
|**LEC**|Europe|15|1,315|149|
|**LCS**|North America|13|1,371|182|
|**PCS**|Asia-Pacific|10|1,295|235|
|**VCS**|Vietnam|12|1,489|158|
|**CBLOL**|Brazil|10|1,153|196|
|**LLA**|Latin America<br>..|12<br>.|890|175|
|**Total**||**392**|**37,388**|**4,927**|

For each game, we have the raw end-game statistics of the players (e.g., amount of gold, number of kills), events (e.g., player killing another player), game-related data (e.g., duration), and metadata (e.g., competition the game was in). Each player in a game has been assigned a region based on their participation in the latest highest-tier regional tournaments. 

_2) Feature Extraction:_ From the raw data, we extracted features that both reflect metrics widely used by players and facilitate modeling. Table III describes all the features we used. 

Most of the data points are normalized using reference values specific to each game. The two most common normalizations are the game-length normalization and total-kills normalization. Game-length normalization accounts for different game durations (e.g., having 10 kills in 15 minutes is not the same as in 50 minutes). Total-kills normalization accounts for different pacing in the game, as some games can have much more fighting than others. 

Particular attention has been given to using features or data points that are strongly linked solely to the player’s performance. Because of that, we have excluded all teamrelated statistics (e.g, total number of kills by the team), and decided against using team-normalization techniques (e.g., share of number of kills within the team). 

Some features described in Table III deserve more attention: 

- **Kill-life-assist ratio (KLA)** : This formula has been preferred over the more traditional Kill-death-assist ratio (KDA) for numerical stability. Indeed, both formulas _KDA_ = ( _kills_ + _assists_ ) _/deaths_ or _KDA_ = ( _kills_ + _assists_ ) _/max_ ( _deaths,_ 1) are either instable when _deaths_ = 0 or cannot differentiate between 0 and 1 death. 

- **Worthless death ratio and Free kill ratio** : A player’s death is considered worthless if, within a 1-minute window, the player has not been involved in an enemy kill or their team has not secured an objective (e.g., a Drake or a Tower). The latter describes situations where the player’s death gave the opportunity to their team to accomplish something else important on the map. Note that, while it shares the same core idea as the worthless death described by Maymin [11], we preferred a less complex implementation as it is not the focus of the paper. 

- **Objective contest winrate and loserate** : These features are computed based on neutral monster kill events. An event is considered contested if players from both teams are present among the killer or assists of the event, with the contest win assigned to the team of the killer. The rates are calculated by normalizing the number of contest wins and losses by the total number of contestable objectives in the game. It is important to note that, due to the lack of event location data in the dataset, fights occurring near a neutral objective are not categorized as contests for that objective unless explicitly registered as part of the neutral monster kill event. 

## _B. Computing and Evaluating the Players’ Game Performance_ 

First, we consider the computation of the player’s performance scores. 

_1) Implementation Details:_ As discussed in Section IV-A, we implemented our proposed approach using multiple XGBoost models, one per role. Specifically, they were trained with 2,000 boosted rounds and a learning rate of 0.01. 

To improve the interpretability of the model, we enforce monotonicity constraints for all the features. These constraints 

JOURNAL OF L<sup>A</sup> TEX CLASS FILES, VOL. 14, NO. 8, AUGUST 2021 

8 

force each feature to impact the output probability in only one direction. For instance, an increase in the KLA should only increase the win probability, not decrease it. This prevents the model from finding hidden patterns in the combination of features that could lead to unexpected uses of certain features. In practice, of all the features we used, only the Worthless death ratio and Objective contest loserate are forced to decrease the output probability with higher values. 

A 5-fold cross-validation was used to compute the performance of the players and evaluate the models. Before being input to the models, all the features were standardized to zero mean and unit variance. 

_2) Experimental Results:_ Evaluating the performance scores is difficult because of the lack of known ground truth. In these experiments, three aspects of the models are looked at: their predictive capability, the calibration of the predicted probabilities, and the interpretability of the outputs. 

First, regarding the predictive capability, our XGBoost models achieve an average accuracy of 90.74% (Standard Deviation, SD = 0.60), comparable to role-based SVC models (91.00% accuracy, SD = 0.46) from the PlayeRank framework [6], and Random Forest models (91.30% accuracy, SD = 0.58) from the PI framework [19]. These high accuracy values are expected, as we are predicting game outcomes based on end-game statistics, which contain extensive information about in-game events. The slightly lower accuracy of our models can be attributed to the enforcement of monotonicity constraints. Without these constraints, our models achieve a higher accuracy of 91.79% (SD = 0.56). However, this improved performance comes at the cost of using unintended feature interactions, which undermine the explainability of the performance scores (e.g., a higher creep score per minute paradoxically decreasing the predicted winning probability). 

<!-- Start of picture text -->
1.0<br>Top<br>Jungle<br>Mid<br>Bot 20000<br>0.8 Support<br>Perfect calibration<br>15000<br>0.6<br>0.4 10000<br>0.2 5000<br>0.0 0<br>0.0 0.2 0.4 0.6 0.8 1.0<br>Mean Predicted Probability<br>Count<br>Fraction of Positives<br><!-- End of picture text -->

Fig. 2: Calibration plots with histograms of predicted probabilities for each role. 

As mentioned in section IV-A, the good calibration of the model is very important, as the player performance is directly related to the trustworthiness of the probabilities. We used the Expected Calibration Errror (ECE) to measure quality of 

the estimated probabilities [31]. With a mean ECE ( of 0.93% (SD = 0.03), the model is fairly well calibrated. In comparison, the PlayeRank approach has an average ECE of 1.28% (SD = 0.13) and the PI approach an average ECE of 2.28% (SD = 0.09). Figure 2 displays the calibration plots of our models for the different roles, alongside the histogram of the probability values. The U-shape of the probability distribution, combined with its variability across different roles, shows the need for the percentile transformation in the calculation of PScore to achieve uniformly distributed game performances across all roles. 

Finally, we examine the importance of the different features used to compute the performance scores. To quantify each feature’s contribution to the predictions, we use SHAP (SHapley Additive exPlanations) values [32]. SHAP is a model-agnostic explainability method that measures the average change in a model’s predictions when a given feature is included or excluded. SHAP values can explain individual predictions, as shown in Table I, or represent general behavior through their distribution over games and roles, as illustrated in Figure 3. The KLA emerges as the most important feature across all roles. Other significant features include the Free kill ratio, Experience per minute, Gold per minute, Worthless death ratio, and Objective contest loserate. This highlights not only the importance of well-known metrics like Gold per minute but also the relevance of new features we introduced, such as the Free kill ratio. Besides, Figure 3 shows the impact of the monotonicity constraints that have been enforced in the XGBoost models, as all the features are pushing the winning probabilities in the expected directions. 

To conclude, our approach implemented with XGBoost has a good predictive capability while being calibrated and maintaining a good interpretability. The next sets of experiments will further validate the approach by showing the usefulness of the PScore values in the creation of accurate skill ratings. 

## _C. Computing and Evaluating the Player Skill Ratings_ 

_1) Experimental Models:_ In this section, we are interested in how well our OpenSkill-based framework estimates the player’s skill ratings. To measure the impact of the different modules we proposed, we consider the following model variations: 

- **OpenSkill** : The skill rating updates only depend on the team outcome of the game and not the player’s in-game performance. 

- **FFA** **<u>OpenSkill</u>** : The skill rating updates use the FFA setting described in Section IV-B2. 

- **Meta** **<u>OpenSkill</u>** : The skill rating is defined as the combination of both contextual and meta ratings as described in Section IV-B3. 

- **Meta** **<u>FFA OpenSkill</u>** : The skill rating is both defined as the combination of both contextual and meta rating, and use the FFA setting in the update. 

- **Meta** **<u>FFA TrueSkill</u>** : Similar to the Meta FFA <u>OpenSkill</u> variation, but with TrueSkill instead of OpenSkill. We specifically used the non official implementation of Lee, as the official one is not available [22], [33]. 

JOURNAL OF L<sup>A</sup> TEX CLASS FILES, VOL. 14, NO. 8, AUGUST 2021 

9 

<!-- Start of picture text -->
Top Jungle Mid Bot Support<br>Kill-life-assist ratio<br>Free kill ratio High<br>Experience per minute<br>Gold per minute<br>Worthless death ratio<br>Objective contest loserate<br>Wards placed per minute<br>Damage taken per gold total kills ratio<br>Objective contest winrate<br>Damage taken total kills ratio<br>Largest multi kill<br>Largest killing spree total kills ratio<br>Damage dealt per gold total kills ratio<br>Creep score per minute<br>Damage dealt total kills ratio Low<br>5 0 5 5 0 5 5 0 5 5 0 5 5 0 5<br>SHAP Value<br>Feature Value<br><!-- End of picture text -->

Fig. 3: Relative importance of features for each role-based XGBoost model using SHAP values. The features are ordered in descending order based on their average importance across roles. 

In addition, as it is used in the PlayeRank framework [6], we compare these rating models to EWMA, which we implemented with a smoothing factor of 0.05 to put more emphasis on the player’s performance history. 

We apply these rating models to the PScore, PlayeRank, and PI performance models. 

_2) Pre-match Game Outcome Forecasting Experiment:_ First, we evaluate the models by their ability to forecast the outcome of the game from the players’ skill ratings before the game. The intuition is that more accurate skill ratings should be better predictors of the outcome of the game. 

To account for the gradual changes in the rating distribution and potential meta shifts in the video game, we used a rolling window of one month. We trained a logistic regression model on one year of data and tested it on the subsequent month. Then, we shifted our window by one month and repeated the training-testing evaluation. 

Table IV shows the performance of the models in terms of accuracy and ECE. Results are detailed for both intra-region and inter-region matches. We can observe the following: 

- All the OpenSkill (or TrueSkill) variations have a higher accuracy than their EWMA counterparts. This shows the benefits of having Bayesian ratings with updates depending on the skill ratings of the opponents. 

- All the models implementing the Meta OpenSkill variation see a large increase in accuracy in inter-region matches, without sacrificing much in intra-region accuracy. Inter-region accuracy becomes higher than intraregion accuracy, which makes sense given how spread apart the skill of different regions can be (and thus easier to predict), as shown by Figure 4. 

- The FFA OpenSkill variation observes a small decrease in accuracy compared to the non-FFA OpenSkill model. This is not surprising, as for this experiment, only a good 

overall team rating is needed. 

- The improvements of the proposed rating model transfer well to other game performance models, as shown by the PI + Meta FFA <u>OpenSkill</u> and PlayeRank + Meta FFA <u>OpenSkill</u> model combinations. 

- Compared to OpenSkill, TrueSkill obtains comparable accuracy, but significantly worse calibration. 

<!-- Start of picture text -->
120<br>100<br>80<br>60<br>40<br>20<br>0<br>20<br>Korea China Europe North Asia Vietnam Brazil Latin Other<br>America Pacific America<br>Region<br>Player Skill Rating<br><!-- End of picture text -->

Fig. 4: Distribution of players’ skill ratings per region using the Meta <u>FFA OpenSkill</u> rating model with PScore. 

_3) Skill Ratings Distribution per Role:_ One important aspect of PandaSkill, from the evaluation of players’ in-game performance to the computation of their skill ratings, is that all roles are treated identically. To measure this fairness of treatment, we use the Wasserstein distance between the rating distributions of two roles, averaged over every pair of 

JOURNAL OF L<sup>A</sup> TEX CLASS FILES, VOL. 14, NO. 8, AUGUST 2021 

10 

TABLE IV: Accuracy and ECE of a logistic regression model forecasting the game outcome from the players’ skill ratings. Results are described for all the games, or for intra-region or inter-region games only. 

|**Model**|**Acc**|**uracy (%**|**)** _↑_|**E**|**CE (%)**|_↓_|
|---|---|---|---|---|---|---|
||All|Intra|Inter|All|Intra|Inter|
|**PScore + EWMA**|63.06|63.33|52.34|1.43|1.57|5.51|
|**PScore + OpenSkill**|**65.56**|**65.51**|67.39|1.53|1.39|7.59|
|**PScore + Meta**<br>**OpenSkill**|65.12|65.01|69.23|0.89|0.88|5.51|
|**PScore + FFA**<br>**OpenSkill**|64.79|64.86|61.71|**0.77**|**0.79**|4.02|
|**PScore + Meta**<br>**FFA**<br>**OpenSkill**|64.98|64.86|70.07|1.01|0.97|**3.27**|
|**PScore + Meta**<br>**FFA**<br>**TrueSkill**|65.15|65.05|68.90|2.85|2.85|4.85|
|**PI + EWMA**|63.53|63.75|54.68|1.88|1.99|4.61|
|**PI + Meta**<br>**FFA**<br>**OpenSkill**|65.05|64.92|**70.23**|1.00|1.05|4.15|
|**PlayeRank + EWMA**|62.25|62.80|51.67|2.03|2.22|6.16|
|**PlayeRank + Meta**<br>**FFA**<br>**OpenSkill**|64.94|64.84|69.23|1.01|0.97|5.40|

roles. The Wasserstein distance measures the minimal ’effort’ required to transform one probability distribution into another, effectively quantifying differences between distributions [34]. Results, grouped by performance score model, are as follows: 

- **PlayeRank** : Performs poorly, with the best one averaging a Wasserstein distance of 2.44 (SD = 1.32). 

- **PI** : Shows good performance, with distances ranging from 0.35 (SD = 0.12) to 0.66 (SD = 0.21). 

- **PScore** : Achieves the best performance, with distances between 0.09 (SD = 0.01) and 0.44 (SD = 0.13). 

First, both PScore-based and PI-based models significantly outperform PlayeRank-based approaches. This can be attributed to the use of percentile transformations. While PI applies this transformation to the input features, PandaSkill applies it to the output performance scores. In both cases, roles are treated more fairly as the scale of either the model inputs or outputs becomes independent of the role. However, from the lower average distance of PScore, we can conclude that doing the percentile transformation at the end, as in PandaSkill, is more effective. 

To analyze the results, we investigated two different types of concordance between the model and the experts: 

- **Majority concordance** : The fraction of pairs for which a given model agrees with the majority of the experts. 

- **Unanimity concordance** : The fraction of pairs for which a given model agrees with all the experts. 

In cases where no majority could be achieved among the experts (e.g., when the number of experts was even, and exactly half of them preferred one player), we chose to drop those comparisons (represented by the _No majority_ column in Table VI). 

TABLE VI: Description of player comparison surveys with number of experts, number of unique players, ratio of unanimous answers, ratio of no majority answers. 

|**Region**|**Experts**|**Players**|**Unanimity**|**No majority**|
|---|---|---|---|---|
|Global|5|477|0.51|-|
|Korea|4|54|0.70|0.06|
|China|3|96|0.59|-|
|Europe|4|52|0.62|0.17|
|North America|3|40|0.59|-|
|**Total**|5|629|0.60|0.05|

## _D. Evaluating the Player Ranking_ 

Table V shows the top 50 players from all the regions. We can see it is dominated by Korea and China, which aligns with most of the inter-region results from the past few years (e.g., MSI or Worlds). Only one Western team, G2 Esports, made it into the top 50 ranking. 

To perform a quantitative evaluation of the rankings and the underlying skill ratings, as done in the evaluation of PlayeRank [6], we conducted an evaluation by human experts. 

_1) Experimental Setting:_ We created several surveys, each containing 300 randomly selected pairs of players, and asked experts to choose the better player from each pair. Five surveys were created: four focused on the major regions (Korea, China, Europe, and North America), and one global survey with players from all regions. The experts, recruited from PandaScore’s odds traders, were selected based on their expertise in the different LoL regions. Since not all traders were equally familiar with every region, the regional surveys were only completed by those with sufficient knowledge. Table VI details the composition of these surveys. 

_2) Results:_ The PScore + Meta FFA <u>OpenSkill</u> model achieves the second- highest majority concordance (average of 80.63%, SD = 6.52), just behind PI + Meta FFA <u>OpenSkill,</u> which has 80.70% (SD = 5.41). However, it achieves the highest average unanimity concordance with an average of 88.98 % (SD = 5.99). 

Figure 5 details the results per model and per region: 

- EWMA is outperformed by the Meta <u>FFA</u> OpenSkill rating model for almost all underlying performance models and regions. 

- Using the FFA OpenSkill setting shows a significant improvement in the concordance with the experts, demonstrating the usefulness of incorporating the player’s ingame performance in the updates of their skill ratings. 

- Using the dual-rating system with a contextual rating and a meta rating, alongside the FFA setting, significantly increases the concordance for the Global survey. This highlights the issue of isolated rating pools coming from the low number of inter-region games. PandaSkill provides a working solution to this issue. 

JOURNAL OF L<sup>A</sup> TEX CLASS FILES, VOL. 14, NO. 8, AUGUST 2021 

11 

|**Rank**|**Player**|**Team**|**Region**|**Role**|**Rating**|**Rank**|**Player**|**Team**|**Region**|**Role**|**Rating**|
|---|---|---|---|---|---|---|---|---|---|---|---|
|1|Chovy|Gen.G|Korea|Mid|102.81|26|Missing|JD Gaming<br>|China|Support|84.24|
|2<br>|Peyz<br>|Gen.G<br>|Korea<br>|Bot<br>|101.31<br>|27|XUN|BLG<sup>2</sup>|China|Jungle|83.89|
|3<br>|Canyon<br>|Gen.G<br>|Korea<br>|Jungle<br>|97.96<br>|28|Faker|T1|Korea|Mid|83.49|
|4<br>|Kiin<br>|Gen.G<br>|Korea|Top|96.10<br>|29|Creme|Top Esports|China|Mid|82.61|
|5|Viper|HLE<sup>1</sup><br>|Korea|Bot|94.37|30|Hans sama|G2 Esports|Europe|Bot|82.36|
|6|Delight|HLE<sup>1</sup><br>|Korea|Support|91.93|31|JackeyLove|Top Esports|China|Bot|82.32|
|7<br>|Peanut<br>|HLE<sup>1</sup><br>|Korea<br>|Jungle<br>|91.92<br>|32|Bdd|KT Rolster|Korea|Mid|81.84|
|8<br>|Lehends<br>|Gen.G<br>|Korea<br>|Support<br>|91.92<br>|33|ShowMaker|Dplus KIA|Korea|Mid|81.80|
|9<br>|Zeka<br>|HLE<sup>1</sup><br><sup>2</sup>|Korea<br>|Mid<br>|91.31<br>|34|Flandre|JD Gaming|China|Top|80.36|
|10<br>|ON<br>|BLG<br>|China<br>|Support<br>|89.85<br>|35|Yagao|JD Gaming|China|Mid|80.18|
|11<br>|Aiming<br>|Dplus KIA<br>|Korea<br>|Bot<br>|89.73<br>|36|BrokenBlade|G2 Esports|Europe|Top|79.11|
|12<br>|Oner<br>|T1<br>|Korea<br>|Jungle<br>|89.08<br>|37|Hang|LNG Esports|China|Support|78.94|
|13<br>|Elk<br>|BLG<sup>2</sup><br>|China<br>|Bot<br>|89.06<br>|38|Scout|LNG Esports|China|Mid|78.94|
|14<br>|knight<br>|BLG<sup>2</sup><br>|China<br>|Mid<br>|88.64<br>|39|Pyosik|KT Rolster|Korea|Jungle|78.86|
|15<br>|Keria<br>|T1<br>|Korea<br>|Support<br>|88.11<br>|40|GALA|LNG Esports|China|Bot|78.74|
|16<br>|Gumayusi<br>|T1|Korea<br>|Bot<br>|87.93<br>|41|Caps|G2 Esports|Europe|Mid|78.20|
|17|Tian|Top Esports|China|Jungle|87.90|42|BeryL|KT Rolster|Korea|Support|78.13|
|18|Lucid|Dplus KIA<br>|Korea|Jungle|86.56|43|Deft|KT Rolster|Korea|Bot|77.74|
|19|Doran|HLE<sup>1</sup><br>|Korea|Top|86.23|44|Kellin|Dplus KIA|Korea|Support|77.61|
|20|Bin|BLG<sup>2</sup>|China|Top|86.18|45|Tarzan|Weibo Gaming|China|Jungle|76.91|
|21|Meiko|Top Esports|China|Support|86.12|46|Zika|LNG Esports|China|Top|76.83|
|22|369|Top Esports|China|Top|86.08|47|Yike|G2 Esports|Europe|Jungle|76.73|
|23|Kanavi|JD Gaming|China|Jungle|86.02|48|Light|Weibo Gaming|China|Bot|76.71|
|24|Zeus|T1|Korea|Top|85.73|49|Mikyx|G2 Esports|Europe|Support|76.13|
|25|Ruler|JD Gaming|China|Bot|85.26|50|Weiwei|LNG Esports|China|Jungle|75.94|

> 1 Hanwha Life Esports. 

> 2 Bilibili Gaming. 

TABLE V: Ranking for the first 50 players using the lower bound of their skill rating. 

<!-- Start of picture text -->
100 Majority Concordance<br>Region<br>90 Global Korea China Europe North America<br>80<br>70<br>60<br>50<br>100 Unanimity Concordance<br>90<br>80<br>70<br>60<br>50<br>PScore + PScore + PScore + PScore + PScore + PScore + PlayeRank+ PlayeRank + PI + PI +<br>EWMA OpenSkill Meta_OpenSkill FFA_OpenSkill Meta_FFA_OpenSkill Meta_FFA_TrueSkill EWMA Meta_FFA_OpenSkill EWMA Meta_FFA_OpenSkill<br>Model<br>Concordance (%)<br><!-- End of picture text -->

Fig. 5: Majority and unanimity concordance between models and experts per region. 

- TrueSkill is comparable to OpenSkill, being only notably worse for the Global survey. This indicates that the dualrating system we propose works better with the OpenSkill framework. 

- PI-based player performance ultimately offers very similar skill ratings compared to PScore. This shows that PScore is a valid alternative to PI, with the advantage of being model-agnostic by design. 

- Even when improved by the Meta FFA <u>OpenSkill rating</u> model, PlayeRank still fails to offer convincing skill ratings compared to other approaches. This underscores the need for a good underlying player performance model. 

- Surprisingly, the concordance between experts and the models is very high for the Korea region. This can be explained by the wider range of skill ratings that is within the region compared to the others, as shown by Figure 4. 

_E. Example of the Framework Applied onto a Game_ 

To demonstrate PandaSkill’s practical usage, we propose to look at how it behaves in a given game. We chose game 2 of the match between Hanwha Life Esports (HLE) and T1 in the lower-bracket final of the LCK Summer 2024. It was a highstake game, between two of the strongest teams in the world (see Table V). The game was very close and ended with the victory for T1. 

As shown in Table I, despite losing the game, the skill ratings of multiple players from HLE (Viper, Peanut, and Zeka) increased after the game. This was due to the strong performances of these players compared to most of T1’s players. Conversely, the skill ratings of some T1 players decreased (Oner, Zeus). 

Faker was the Most Valuable Player (MVP) of his team, having the highest PScore, with a difference of 21.93 com- 

JOURNAL OF L<sup>A</sup> TEX CLASS FILES, VOL. 14, NO. 8, AUGUST 2021 

12 

pared to Zeka, the player in the same role for HLE (Mid). Looking at the feature contributions to Faker’s performance, around half of his PScore can be attributed to his exceptional KLA (7.0). Other outstanding features are his Gold per minute, Largest multi kill, and Damage taken total kills ratio. 

## VI. CONCLUSION 

In this paper, we presented PandaSkill, a framework to compute the performance of players in a game (PScore) and their skill ratings. Compared to other approaches in the literature, PandaSkill is unique in that it fairly compares players from different roles, is model-agnostic, and addresses the isolated rating pools issue common in esports. We applied PandaSkill to five years of professional League of Legends, demonstrating its usefulness. 

We have open-sourced PandaSkill so that it can be reused by the community, driving future research. Here are some directions we think could be worth studying. Because our approach is model-agnostic, more complex models such as neural networks could be envisaged [10]. The input features to the model are as important, if not more so, than the model itself. The usefulness of more complex features linked to the impact of player actions could be worth exploring [11], [15]. Last but not least, applying PandaSkill to other esports titles such as Counter-Strike or Dota 2 should yield interesting results. While similar to League of Legends in essence, both games have specific aspects that would need to be addressed. For instance, the conception of roles is quite different, potentially being more fluid and less defined than in LoL [9], [19]. Moreover, the competitive scenes are fragmented differently. Instead of being fragmented by region, they are fragmented by tiers of competition. 

## REFERENCES 

- [1] L. M. Hvattum, “A comprehensive review of plus-minus ratings for evaluating individual players in team sports,” _International Journal of Computer Science in Sport_ , vol. 18, no. 1, pp. 1–23, 2019. 

- [2] J. Lasek, Z. Szl´avik, and S. Bhulai, “The predictive power of ranking systems in association football,” _International Journal of Applied Pattern Recognition_ , vol. 1, no. 1, pp. 27–46, 2013. 

- [3] L. Bornn, D. Cervone, and J. Fernandez, “Soccer analytics: Unravelling the complexity of “the beautiful game”,” _Significance_ , vol. 15, no. 3, pp. 26–29, 2018. 

- [4] J. Thorn, P. Palmer, and D. Reuther, _The hidden game of baseball: A revolutionary approach to baseball and its statistics_ . University of Chicago Press, 2015. 

- [5] J. Brooks, M. Kerr, and J. Guttag, “Developing a data-driven player ranking in soccer using predictive model weights,” in _Proceedings of the 22nd ACM SIGKDD international conference on knowledge discovery and data mining_ , 2016, pp. 49–55. 

- [6] L. Pappalardo, P. Cintia, P. Ferragina, E. Massucco, D. Pedreschi, and F. Giannotti, “Playerank: data-driven performance evaluation and player ranking in soccer via a machine learning approach,” _ACM Transactions on Intelligent Systems and Technology (TIST)_ , vol. 10, no. 5, pp. 1–27, 2019. 

- [7] R. Rein and D. Memmert, “Big data and tactical analysis in elite soccer: future challenges and opportunities for sports science,” _SpringerPlus_ , vol. 5, pp. 1–13, 2016. 

- [8] T. Decroos, L. Bransen, J. Van Haaren, and J. Davis, “Actions speak louder than goals: Valuing player actions in soccer,” in _Proceedings of the 25th ACM SIGKDD international conference on knowledge discovery & data mining_ , 2019, pp. 1851–1861. 

   - [10] O. Delalleau, E. Contal, E. Thibodeau-Laufer, R. C. Ferrari, Y. Bengio, and F. Zhang, “Beyond skill rating: Advanced matchmaking in ghost recon online,” _IEEE Transactions on Computational Intelligence and AI in Games_ , vol. 4, no. 3, pp. 167–177, 2012. 

   - [11] P. Z. Maymin, “Smart kills and worthless deaths: esports analytics for league of legends,” _Journal of Quantitative Analysis in Sports_ , vol. 17, no. 1, pp. 11–27, 2021. 

   - [12] E. Kleinman and M. S. El-Nasr, “Using data to” git gud”: a push for a player-centric approach to the use of data in esports,” in _EHPHCI: Esports and High-Performance HCI Workshop, 2021 CHI Conference on Human Factors in Computing Systems. OSF Preprints_ , 2021. 

   - [13] B. Sabtan, S. Cao, and N. Paul, “Current practice and challenges in coaching esports players: An interview study with league of legends professional team coaches,” _Entertainment Computing_ , vol. 42, p. 100481, 2022. 

   - [14] B. T. Sharpe, N. Besombes, M. R. Welsh, and P. D. Birch, “Indexing esport performance,” _Journal of Electronic Gaming and Esports_ , vol. 1, no. 1, 2022. 

   - [15] P. Xenopoulos, H. Doraiswamy, and C. Silva, “Valuing player actions in counter-strike: Global offensive,” in _2020 IEEE international conference on big data (big data)_ . IEEE, 2020, pp. 1283–1292. 

   - [16] S. Pradhan and Y. Abdourazakou, ““power ranking” professional circuit esports teams using multi-criteria decision-making (mcdm),” _Journal of Sports Analytics_ , vol. 6, no. 1, pp. 61–73, 2020. 

   - [17] J. Gudmundsson and M. Horton, “Spatio-temporal analysis of team sports,” _ACM Computing Surveys (CSUR)_ , vol. 50, no. 2, pp. 1–34, 2017. 

   - [18] L. Pappalardo, P. Cintia, A. Rossi, E. Massucco, P. Ferragina, D. Pedreschi, and F. Giannotti, “A public data set of spatio-temporal match events in soccer competitions,” _Scientific data_ , vol. 6, no. 1, p. 236, 2019. 

   - [19] S. Demediuk, A. Kokkinakis, M. S. Patra, J. Robertson, B. Kirman, A. Coates, A. Chitayat, J. Hook, I. Nolle, O. Olarewaju _et al._ , “Performance index: A new way to compare players,” in _2021 MIT Sloan Sports Analytics Conference. IEEE_ , 2021. 

   - [20] A. E. Elo, _The Rating of Chessplayers, Past and Present_ . New York: Arco Pub., 1978. [Online]. Available: http://www.amazon.com/ Rating-Chess-Players-Past-Present/dp/0668047216 

   - [21] R. Herbrich, T. Minka, and T. Graepel, “Trueskill™: a bayesian skill rating system,” _Advances in neural information processing systems_ , vol. 19, 2006. 

   - [22] V. Joshy, “Openskill: A faster asymmetric multi-team, multiplayer rating system,” _Journal of Open Source Software_ , vol. 9, no. 93, p. 5901, 2024. [Online]. Available: https://doi.org/10.21105/joss.05901 

   - [23] M. E. Glickman and A. C. Jones, “Rating the chess rating system,” _CHANCE-BERLIN THEN NEW YORK-_ , vol. 12, pp. 21–28, 1999. 

   - [24] A. Sapienza, Y. Zeng, A. Bessi, K. Lerman, and E. Ferrara, “Individual performance in team-based online games,” _Royal Society open science_ , vol. 5, no. 6, p. 180329, 2018. 

   - [25] Introducing rating 2.1. https://www.hltv.org/news/40051/introducingrating-21. Accessed: 2024-10-23. 

   - [26] M. E. Glickman, “The glicko system,” _Boston University_ , vol. 16, no. 8, p. 9, 1995. 

   - [27] ——, “Example of the glicko-2 system,” _Boston University_ , vol. 28, 2012. 

   - [28] T. Minka, R. Cleven, and Y. Zaykov, “Trueskill 2: An improved bayesian skill rating system,” _Technical Report_ , 2018. 

   - [29] R. C. Weng and C.-J. Lin, “A bayesian approximation method for online ranking.” _Journal of Machine Learning Research_ , vol. 12, no. 1, 2011. 

   - [30] Fandom, “Leaguepedia api documentation,” 2024, accessed: 2024-09-15. [Online]. Available: https://lol.fandom.com/wiki/Help:Leaguepedia <u>API</u> 

   - [31] T. Silva Filho, H. Song, M. Perello-Nieto, R. Santos-Rodriguez, M. Kull, and P. Flach, “Classifier calibration: a survey on how to assess and improve predicted class probabilities,” _Machine Learning_ , vol. 112, no. 9, pp. 3211–3260, 2023. 

   - [32] S. Lundberg, “A unified approach to interpreting model predictions,” _arXiv preprint arXiv:1705.07874_ , 2017. 

   - [33] H. Lee, “An implementation of the trueskill rating system for python,” https://github.com/sublee/trueskill, 2018, gitHub repository. [Online]. Available: https://github.com/sublee/trueskill 

   - [34] V. M. Panaretos and Y. Zemel, “Statistical aspects of wasserstein distances,” _Annual review of statistics and its application_ , vol. 6, no. 1, pp. 405–431, 2019. 

- [9] P. Varga, T. M. Scholz, and E. T. Tan, “Esports player analytics,” _Routledge Handbook of Esports_ , 2024.
