---
id: xenopoulos_optimal_economy
title: Optimal Team Economic Decisions in Counter-Strike
authors: Peter Xenopoulos, Bruno Coelho, Claudio Silva
year: 2021
venue: IJCAI 2021 AISA Workshop
url: https://arxiv.org/abs/2109.12990
arxiv_version: 2109.12990v1
license: arXiv — not verified for redistribution
pdf_sha256: d96af5f405750f10
converted: '2026-09-28'
converter: pymupdf4llm
---

# Optimal Team Economic Decisions in Counter-Strike

> Auto-converted from PDF. Tables, equations and figure text may be garbled — check the original PDF before quoting numbers.

<!-- cscoach-notes:start -->
## cscoach notes (hand-written — preserved on re-conversion)

**Authors:** Xenopoulos, Coelho, Silva (NYU). IJCAI 2021 AISA workshop. The source of **Optimal Spending
Error (OSE)**.

- **Relevance:** **high** for economy (M6.3, A-21, A-13).
- **Verified claims:**
  - A **game-level** (map) win-probability model at the **start of each round**. Its features: scores,
    score difference, each side's starting equipment value, money and **buy type**. The outcome has 3
    classes: CT win, T win, draw (§4). This differs from round-level WP.
  - Buy types are defined at the **team level** from start equipment and spend (Table 1). Examples:
    - Eco = equipment 0–3k and spend 0–2k (3% round win rate);
    - Half Buy = equipment 0–3k and spend 7.5–20k (34%);
    - "Hero" buys = equipment 3–20k with low spend;
    - Full Buy = equipment + spend > 20k (59%).
  - Data: 6,538 **online** pro matches (Apr 2020–Apr 2021; online only because LAN and online differ).
    **Temporal split:** train Apr–Sep 2020, validation Oct–Nov, test Dec 2020–Apr 2021.
  - Log-loss (Table 2): logistic (scores only) 0.793, XGBoost 0.739, NN 0.736 (weighted over maps).
    **A single model with the map one-hot encoded (0.730) beats per-map models.** On a held-out map, a
    model trained without map features does as well as map-specific models (§5.3).
  - Optimal buy = the buy type with the highest predicted game WP, obtained by swapping the buy-type
    feature. Teams "eco" more often than optimal; after losing the pistol round, the model says half-buy
    ~96–100% of the time (Tables 4–5).
  - **OSE** = mean squared difference between the predicted WP of the chosen buy and of the optimal buy.
    It correlates with the round win rate at r = −0.45 (top-50 teams, ≥ 300 rounds).
- **Corrections vs. our docs:** our spec used a *two-round* horizon for counterfactual buys; the source
  uses **game-level WP at round start**. The synthesis's OSE description is right in spirit. Its criticism
  about "hero buys" is not quite fair: the paper models hero buys explicitly as buy types.
- **Use in project:**
  - Economy counterfactuals should be scored with a **game-level WP model** (score state + economy),
    with the two-round simulation as the fallback (docs/specs/03#economy updated).
  - Buy classes: evaluate team-level definitions (team equipment + spend) next to per-player classes
    (A-21, MV.6).
  - Pooling with a conditioning feature beat separate per-group models → analogous evidence for pooling
    tiers with `tier` as a feature (A-01, ADR-0002).
  - OSE per player/team per match is a candidate economy metric (M6.3). It must pass the within-match
    reliability gates.
  - **Causal caveat:** "optimal buy" comes from changing one feature while holding the others fixed.
    Buy type is confounded with team strength and money, which is exactly A-04 (MV.10).
- **Caveats:** CS:GO MR15 economy rules (CS2 differs; A-13); pro only; no calibration or CIs reported.
<!-- cscoach-notes:end -->

## Full text

# **Optimal Team Economic Decisions in Counter-Strike** 

## **Peter Xenopoulos**<sup>1</sup> , **Bruno Coelho**<sup>1</sup> , **Claudio Silva**<sup>1</sup> 

1New York University 

_{_ xenopoulos, bruno.coelho, csilva _}_ @nyu.edu 

## **Abstract** 

The outputs of win probability models are often used to evaluate player actions. However, in some sports, such as the popular esport Counter-Strike, there exist important team-level decisions. For example, at the beginning of each round in a CounterStrike game, teams decide how much of their ingame dollars to spend on equipment. Because the dollars are a scarce resource, different strategies have emerged concerning how teams should spend in particular situations. To assess team purchasing decisions in-game, we introduce a game-level win probability model to predict a team’s chance of winning a game at the beginning of a given round. We consider features such as team scores, equipment, money, and spending decisions. Using our win probability model, we investigate optimal team spending decisions for important game scenarios. We identify a pattern of sub-optimal decision-making for CSGO teams. Finally, we introduce a metric, _Optimal Spending Error_ (OSE), to rank teams by how closely their spending decisions follow our predicted optimal spending decisions. 

## **1 Introduction** 

While traditional sports, such as basketball or soccer, have embraced data to analyze and value players, esports, also known as professional video gaming, still lags behind. Expanded data acquisition methods, such as player-worn sensors or cameras that track player movement, typically have driven analytical efforts in a sport. However, esports is unique in that many player actions and trajectories are recorded by a game server. In many esports, like Counter-Strike: Global Offensive (CSGO), a popular round-based first person shooter (FPS), game server logs are written to a _demofile_ . Because CSGO demofiles are easier to obtain and parse than demofiles from other esports, CSGO represents a promising direction for esports analytics, particularly in player and team valuation. 

Accepted to IJCAI 2021 AISA Workshop 

A common approach to valuing players is through the use of win probability models. As players perform actions in a CSGO round, they change their team’s probability of winning that round. We can value players through the cumulative value of their actions [Xenopoulos _et al._ , 2020]. While evaluating players in CSGO is important for teams, fans and leagues alike, there exist many team-level actions that are important to value. For example, at the beginning of each CSGO round, two teams asymmetrically determine how much of their in-game money to spend on in-game equipment. Given the current game situation, such as the scores between the teams, as well as each team’s current equipment value and money, a team will decide how much of their money to spend. 

Teams consider several different spending strategies depending on the game scenario. For example, some teams may elect to “save” for a round, meaning they limit how much ingame money they spend. On the other hand, some teams may “half buy”, meaning they spend some of their money, but still retain some dollars for future rounds. The relative outcomes of the different strategies on win probability are unknown, since there are many factors to consider, such as team scores, equipment values and team money. Furthermore, current win probability models are tailored towards round-level win probability, whereas teams are making decisions with game-level win probability in mind. 

In this paper, we introduce a game-level win probability model using features such as team scores, team equipment values and total team money. We consider various models, such as tree-based models and neural networks, and compare their performance to a logistic regression baseline. Then, we use these win probability models to assess the optimal spending decisions for various CSGO scenarios. We identify important game situations where the CSGO community is making sub-optimal decisions. Additionally, we introduce _Optimal Spending Error (OSE)_ , a metric to measure how much a team’s spending decisions deviate from optimal ones. 

We structure the paper as follows. In section 2, we cover literature on win probability and valuation frameworks for esports. Then, in section 3, we describe CSGO as game, as well as how CSGO data is collected. Section 4 describes our data and win probability problem formulation, along with the performance of our candidate models. Next, in section 5, we discover the optimal spending decisions in various CSGO scenarios, as well as introduce our OSE metric. Finally, we dis- 

cuss limitations, future work and conclude the paper in section 6. 

## **2 Related Work** 

Predicting the chance that a team will win a game is an important task in sports analytics. The models used to predict who will win a game are typically called _win probability_ models, and often use the current state of a game as input. From these win probability models, we can assess the value of player actions and decisions. For example, Yurko et al. value American football players by how their actions change their respective team’s chance of winning the game [Yurko _et al._ , 2019]. Likewise, Decroos et al. value soccer players by observing how their actions chance their team’s chance of scoring [Decroos _et al._ , 2019]. Valuing actions and decisions through changes in a team’s chance of winning and scoring is common among contemporary sports, such as in ice hockey [Luo _et al._ , 2020; Liu and Schulte, 2018], basketball [Sicilia _et al._ , 2019; Cervone _et al._ , 2014], or soccer [Fern´andez _et al._ , 2019]. 

With new data acquisition pipelines, esports has also started to develop a win probability estimation and player valuation literature. Yang et al. built a model to predict the winning team in Defense of the Ancients 2 (DOTA2), a popular massively online battle arena (MOBA) esport video game [Yang _et al._ , 2017]. They consider a combination of of pre-match features, as well as real-time features, as input to a logistic regression model. Semenov et al. use pre-match hero draft information to predict winners in DOTA2 [Semenov _et al._ , 2016]. Hodge et al. parse DOTA2 game replays, not only those from professional matches, but those of very high ranked public players, to predict outcomes in DOTA2 [Hodge _et al._ , 2017]. Later, they also create a live win prediction model for DOTA2 using an ensemble of various machine learning techniques, such as logistic regression, random forests and gradient boosted trees [Hodge _et al._ , 2019]. Recently, Kim et al. propose a confidence calibration method for predicting winners in League of Legends, a similar style game to DOTA2 [Kim _et al._ , 2020]. Yang et al. introduce an interpretable model architecture to analyze win predictions in Honor of Kings, another popular MOBA game [Yang _et al._ , 2020]. Wang et al. provide a framework to jointly model win probability and player performance in Fever Basketball, a popular sports game [Wang _et al._ , 2020]. 

While MOBA games have attracted increasing interest for win prediction and player valuation, first-person shooters (FPS), such as Counter-Strike, have received less attention. Makarov et al. predict round winners in CSGO in post-plant scenarios using decision trees and logistic regression [Makarov _et al._ , 2017]. Bednarek et al. values players by clustering death locations, however, they do not create a win prediction model [Bedn´arek _et al._ , 2017b]. Recently, Xenopoulos et al. introduce a player valuation framework that uses changes in a team’s win probability to value players [Xenopoulos _et al._ , 2020]. They model a team’s chance of winning a CSGO round using XGBoost with input features such as a team’s remaining players and total equipment. Prior CSGO work has focused on round-level win probability 

Figure 1: Teams earn $3,250 per player for winning a round, or $3,500 if they successfully detonate the bomb. When a team loses a round, they gain a variable amount of money (“loss bonus”) that depends on how many rounds they have lost since they last won a round. After each win, the loss bonus resets. Because the money from losing can be small, teams often find themselves in situations where they must determine how much money to invest to maximize their chance of winning the game. 

and player-level analysis. Our work differs in that we predict game-level win probability, and we analyze team decisions and actions, rather than those from players. 

## **3 Counter-Strike** 

### **3.1 Game Rules** 

Counter-Strike: Global Offensive (CSGO) is the latest rendition in the popular Counter-Strike series of video games. In a professional CSGO match, two teams first meet to decide what _maps_ , or virtual worlds, they plan on playing. Usually, games are structured as a best-of-three, and the two teams go through a picking and banning process to choose maps they want to play. There are seven maps used in professional play, and the pool of seven maps changes occasionally. Teams win a map when they win 16 rounds, unless the score is 15 for each team; then, an overtime process takes place. 

When teams begin to play a map, they are first assigned to either the Terrorists (T) or the Counter-Terrorists (CT). They then play for 15 rounds as their assigned side, and the two teams switch sides after 15 rounds. Each round lasts slightly under two minutes. Teams can achieve a variety of round win conditions based on their current side. The T side can win a round by eliminating all CT players, or by planting a bomb and having it defuse at one of two designated bomb sites. At the beginning of each round, a random T player starts with the bomb. When the bomb is planted, a timer for 35 seconds starts counting down. The CT side can win a round by eliminating all T players, defusing a planted bomb, or allowing the round time to run out, without reaching any of the aforementioned win conditions. 

Players begin a round with 100 health points (HP) and are eliminated when their HP reaches zero. Players lose HP when they are damaged by gunfire or grenades from other players. At the beginning of each round, players can use money earned from previous rounds to buy guns, armor, grenades and other equipment. Players earn money by eliminating other players and through completing objectives. If a team wins a round, each member gains $3,250 in-game money. However, if a team loses, their monetary gain is based on how many previous rounds they have lost since their last win. For example, if a team lost the previous round, but won two rounds ago, they only earn $1,400. We show an example of the variable 

|**Buy Type**|**Equipment**|**Spend**|**Win %**|
|---|---|---|---|
|Eco|0 – 3k|0 – 2k|3%|
|Low Buy|0 – 3k|2k – 7.5k|27%|
|Half Buy|0 – 3k|7.5k – 20k|34%|
|Hero Low Buy|3k – 20k|0 – 7.5k|25%|
|Hero Half Buy|3k – 20k|7.5k – 17k|48%|
|Full Buy|Equip. +Sp|end_>_20k+|59%|

Table 1: Teams use different buying strategies depending on their current money, and which strategy they think will improve their chance of winning the game. We also report the average round win rates for each buy type. 

“loss bonus” in Figure 1. Since the loss bonus can be minimal, teams often use strategies, known as _buy types_ , to guide their in-game economic decisions. Some buy types include deciding not to buy any equipment in a round (referred to as an “eco”), or buying cheap guns (“low buy” or “half buy”) in an effort to save money while maximizing their chance of winning the game. If a player saves equipment from a previous round, but the team elects to either eco or half buy, they these are referred to as “hero” buys. Finally, if a team’s starting equipment value, plus their round monetary spend, is $20,000 or greater, the team’s buy is referred to as a full buy. We define the main buy types in Table 1. 

### **3.2 Data Acquisition** 

CSGO games take place on a game server, to which the clients (players) connect. Each client persists a local game state, containing information such as where other players are standing, team scores and so on. When a client performs some input that changes the game, that input is sent to the game server which then reconciles the global game state across all connected clients. As the game server updates the global game state, and sends it to each client, the game server also writes the change to a _demofile_ [Bedn´arek _et al._ , 2017a]. Demofiles are limited to a single map, so for a best-of-three game, at minimum, two demofiles are generated. One can parse a demofile into a JSON format using a demo parser [Xenopoulos _et al._ , 2020]. 

## **4 Modeling Win Probability** 

In previous win probability works, the objective is typically a regression problem starting with a game state _Gr,t_ , which encapsulates the game information, such as player locations, equipment values and so on, in round _r_ at time _t_ [Xenopoulos _et al._ , 2020]. Using this aforementioned game state, the goal is to estimate _P_ ( _Yr_ = 1 _|Gr,t_ ), where _Yr_ is 1 if the CT side wins round _r_ and 0 otherwise. We vary from this formulation by instead considering _Rg,i_ , which is the game information at the start of round _i_ for game _g_ . We can represent _Rg,i_ as a vector including each side’s current score, the difference in score, each side’s starting equipment value and money, and the buy decisions for both sides in round _i_ . Using _Rg,i_ , we want to estimate _P_ ( _Yg|Rg,i_ ), where _Yg_ represents the game outcome decision for game _g_ . _Yg_ can represent three unique values: (1) the game is won by the current CT side, (2) the current T side, or (3) the game ends in a draw. 

Figure 2: CT win probability by score on the map _Inferno_ from our baseline logistic regression model that uses team scores. Winning the first two rounds can increase a team’s chance of winning the game by roughly 15%. 

Past win probability works have considered a variety of models. For example, logistic regression and gradient boosted trees are often used to model win probability, particularly because they provide good performance and allow for easy interpretability measures [Makarov _et al._ , 2017; Decroos _et al._ , 2019; Yang _et al._ , 2017; Semenov _et al._ , 2016]. At the same time, neural network approaches are relatively untested for win probability prediction, particularly in esports. Therefore, we consider three modeling techniques: (1) logistic regression, (2) XGBoost, and (3) neural networks [Chen and Guestrin, 2016]. Logistic regression serves as our baseline model, and we show the predicted game win probabilities given different score combinations on the _Inferno_ map in Figure 2. We use the default parameters for logistic regression and fine tune the parameters of the other model as described in Section 4.2. We train a separate model for each of the seven competitive maps in CSGO, as well as a model where we one-hot encode the map as a feature, denoted “ _OHE Map_ ”. We evaluate each model by using log-loss, defined as 

where _K_ is the number of labels, _N_ is the number of observations. Each model’s log-loss on the test set is shown in Table 2. While more complex models, like XGBoost and neural networks, clearly outperform our logistic regression baseline, the performance differences between XGBoost and our neural network are minimal. We found a small performance benefit to using one-hot encoding for the map feature. 

|**Map**|**Rounds**|**Logistic**<br>**Regression**|**XGBoost**|**Neural**<br>**Network**|
|---|---|---|---|---|
|dust2|8144|0.820|**0.766**|0.767|
|inferno|10508|0.769|**0.708**|0.709|
|mirage|7712|0.876|**0.827**|0.830|
|nuke|8266|0.773|**0.716**|**0.716**|
|overpass|6230|0.717|0.673|**0.660**|
|train|7565|0.824|0.767|**0.766**|
|vertigo|6080|0.768|0.710|**0.707**|
|_Weighted_|_Average_|_0.793_|_0.739_|_0.736_|
|_OHE_|_Map_|-|**_0.730_**|_0.732_|

Table 2: Log-loss results by map for each of our candidate models. The logistic regression baseline uses only team scores. The tuned XGBoost model and the tuned neural network have similar results, with the neural network having a slightly smaller weighted average loss. Using map as a feature, instead of a separate model for each map, performs slightly better. 

|**Model**|**Hyperparameter**|**Lower**|**Upper**|**Step**|
|---|---|---|---|---|
||Learning rate|0.05|0.31|0.05|
|XGBoost|Max depth|3|10|1|
||Min. child weight|1|8|1|
||Colsample|0.3|0.8|0.1|
||Dense 1|16|128|16|
|NN|Dense 2|16|128|16|
||Dropout|0.1|0.6|0.1|
||Learning rate|10<sup>_−_3</sup>|10<sup>_−_5</sup>|0.1*|

Table 3: Range of values and step sizes considered for each hyperparameter. For the learning rate of the neural network, we instead use a exponential step increment and multiply each value by 0.1. 

explored for each hyperparameter. We use the same range for both tuning a model per map and for the OHE Map models. 

## **5 Discussion** 

### **4.1 Data** 

We use 6,538 demofiles from matches between April 1st, 2020 to April 20th, 2021. We use this time period as all matches were played online, however, for matches before April 2020, it was common for matches to be played on local area networks, where players were in the same room to lower game server ping. Liu et al. find that lower latencies can drastically affect player performance [Liu _et al._ , 2021]. Therefore, matches held in LAN tournaments versus those held online may not be directly comparable. We acquired our demofiles from the popular CSGO fan site, HLTV.org. For training, we use matches from April 1st, 2020 to the end of September 2020 (3,308 demofiles), for validation, we use matches from October and November 2020 (1,108 demofiles), and finally, for testing, we use matches from December 1st, 2020 to April 20th, 2021 (2,122 demofiles). 

### **4.2 Hyperparameter Tuning** 

For XGBoost, we use the Hyperopt [Bergstra _et al._ , 2013] optimization library with default parameters to fine-tune the learning rate, maximum tree depth, minimum child weight and the subsample ratio of columns for each level. We use the validation set indicated in Section 4.1. On the final model we use early stopping on the validation loss with a patience of 10 iterations to also tune the number of boosting rounds. 

For the neural network, we create a two-layer fullyconnected network, where each layer has a ReLU activation function and dropout applied [Srivastava _et al._ , 2014]. We base our two-layer design choice on the work of Yurko et al. , where they considered a two layer fully-connected network to predict an American football ball carrier’s end position as one of their candidate models [Yurko _et al._ , 2020]. We fine-tune the amount of hidden units in each layer, the dropout probability and the learning rate using random search and use early stopping with a patience of 10 epochs on the final model. Our output layer contains three units, one for a CT win, T win and draw, the three possible game outcomes, to which we apply a softmax activation function. In Table 3 we specify the range 

### **5.1 Investigating Common Buy Strategies** 

One benefit of our approach is that we can estimate the game win probability for a variety of possible buy types. We would expect that different buys should naturally change a team’s probability of winning a game. We show the effects of different buys on predicted team win probability in Figure 3. In doing so, we can determine the optimal buy type for a side in a given round by observing which buy type maximizes a team’s game win probability. We present a confusion matrix in Table 4 which shows the optimal buy types, along with the actual performed buy types for each side. While some buy types are overwhelmingly taken when optimal, such as the Full Buy, others, like an Eco buy, are performed more often than is predicted optimal. For example, out of the nearly 2,000 rounds where CT side performed an Eco buy, the predicted optimal buy was either a Low or Half buy, in over 90% of rounds, leading to an average lost win probability of about 3%. 

The first few rounds of any CSGO game are crucial for both sides. As we see from Figure 2, by winning the first two rounds, the CT side achieves a 68% game win rate on the _Inferno_ map. Such a high game win rate for winning the first two rounds is standard across all maps. The side which loses the first round must then decide what their buy type will be for the second round. Almost always, the possible buys will be an eco, low buy or half buy. The rational behind half buying is that the team which won the first round will still not have the best equipment available, thus by half buying, they will have a better chance of winning the second round and forcing their opponents to have a low loss bonus. However, if a team chooses to eco, they may save more money to spend in the third or fourth rounds. In Table 5, we show the buy rates by side for second rounds where a team lost the first round. It is clear that in general, opting to half buy in the second round is a popular strategy, but in almost 40% of rounds, the T side will either eco or low buy. At the same time, our model overwhelmingly predicts that a team should half buy in the second if they lose the first. 

||||||**ACTUAL**<br>|||
|---|---|---|---|---|---|---|---|
|**O**|**CT**|_Eco_|_Low Buy_|_Half Buy_|_Hero Low Buy_|_Hero Half Buy_|_Full Buy_|
|**P**|_Eco_|47|136|141|0|0|756|
|**T**|_Low Buy_|258|270|1218|0|0|2880|
|**I**|_Half Buy_|1675|2126|3557|0|0|2173|
|**M**|_Hero Low Buy_|0|0|0|680|86|1081|
|**A**|_Hero Half Buy_|0|0|0|1926|568|4453|
|**L**|_Full Buy_|3|86|114|31|29|25967|
||||||**ACTUAL**<br>|||
|**O**|**T**|_Eco_|_Low Buy_|_Half Buy_|_Hero Low Buy_|_Hero Half Buy_|_Full Buy_|
|**P**|_Eco_|20|23|26|0|0|1|
|**T**|_Low Buy_|174|706|1647|0|0|1378|
|**I**|_Half Buy_|1582|2283|4726|0|0|157|
|**M**|_Hero Low Buy_|0|0|0|159|247|1794|
|**A**|_Hero Half Buy_|0|0|0|241|196|4225|
|**L**|_Full Buy_|0|63|623|30|13|29946|

Table 4: Confusion matrices of predicted optimal side buy types and actual side buy types for our test set. We see that in many instances, the predicted optimal buy type differs from the actual buy type, particularly for eco and low buy situations. 

Figure 3: The estimated win probability for each side in the first half of a game on the _Inferno_ map. We show two alternate buys, one where buying _less_ (Eco instead of Half Buy) would have decreased the T’s chance of winning, and one where buying _more_ (Hero Half Buy instead of Hero Low Buy) would have decreased the T’s chance of winning. 

|||**Eco**|**Low**<br>**Buy**|**Half**<br>**Buy**|
|---|---|---|---|---|
|Al|T|27%|10%|63%|
|ctua|CT|6%|3%|91%|
||T|0%|0%|100%|
|Optimal|CT|4%|0%|96%|

Table 5: Actual and optimal buy type rates, by side, for second rounds where the team lost the first (pistol) round. Our model predicts that half buy is the most optimal buy type in most situations, increasing 

### **5.2 Assessing Team Economic Decisions** 

Aside from observing community-wide team buy tendencies, we can also rank teams by how well their buys correlate with the optimal ones determined from our model. To that effect, we introduce _Optimal Spending Error_ , defined as 

which is the mean-squared error between the predicted win probability, and the optimal buy win probability, for team _T_ across all rounds which team _T_ plays, denoted _RT_ . Thus, teams with low OSEs are making economic decisions in line with what our model predicts as optimal. We calculate OSE for all teams in our test set, and report the results for teams ranked in the top 50 in Table 6. We see that in general teams with a top HLTV ranks have low OSEs, although the relationship is not completely captured by HLTV ranks, since teams experience different tiers of competition not delineated in the data. For example, a top 50 team is not often playing against a team ranked below the top 50. Therefore, we consider the relationship between a team’s round win rate and their OSE. We would expect that teams which attain low OSEs, and therefore make optimal buy decisions, would also have high round win rates. We confirm this relationship between team OSE and round win rates in Figure 4. We find a slight ( _r_ = _−_ 0 _._ 45) relationship between team OSE and round win rate, indicating that teams with higher OSEs have lower round win rates. 

### **5.3 Accounting for New Maps** 

One interesting consideration is understanding how our models behave when a new map is added to the Active Duty Group, which is the list of active competitive maps. To study the generalization abilities of our models, we train a neural network with no map features on six out of the seven available maps, and then evaluate the test loss on the held out map, imitating a scenario where a brand new map is introduced. 

|||_Top 5_<br>||||_B_<br>|_ottom 5_<br>|||
|---|---|---|---|---|---|---|---|---|---|
|**Team**|**Average**<br>**OSE**|**CT**<br>**OSE**|**T**<br>**OSE**|**HLTV**<br>**Rank**|**Team**|**Average**<br>**OSE**|**CT**<br>**OSE**|**T**<br>**OSE**|**HLTV**<br>**Rank**|
|FPX|0.00024|0.00043|0.00005|16|ENCE|0.00352|0.00501|0.00178|26|
|Gambit|0.00133|0.00090|0.00114|1|HAVU|0.00309|0.00348|0.00271|14|
|SKADE|0.00141|0.00114|0.00165|23|Liquid|0.00306|0.00312|0.00300|8|
|Dignitas|0.00160|0.00143|0.00176|25|Copenhagen<br>Flames|0.00265|0.00387|0.00155|33|
|NIP|0.00176|0.00122|0.00230|13|Anonymo|0.00247|0.00264|0.00229|47|

Table 6: Top and Bottom 5 teams by OSE. Only teams in the Top 50 HLTV.org rankings on April 26th, 2021, and have played at least 300 rounds in our test set, are included. 

Figure 4: Teams with a high Optimal Spending Error (OSE), which translates into more sub-optimal team economic decision making, typically have lower round win rates ( _r_ = _−_ 0 _._ 45). 

We maintain the neural network architecture described in section 4.2 and use 96 and 32 neurons for the first and second layer respective, 0.1 dropout probability and a learning rate of 10<sup>_−_4</sup> with no hyperparameter tuning. We then fine tune our model with a lower learning rate of 10<sup>_−_5</sup> on the new map and observe the new test loss. Table 7 shows the loss for each map, where we also repeat the neural network results from Table 2 for easier comparison. We observe that both the initial models and the fine tuned models perform better or equal to our previous neural network trained on a specific map only, showing that for our problem the amount of data available for the model is more helpful than explicitly capturing effects of a specific map. This agrees with our previous results in Table 2 where the OHE model had a lower average loss than the individual per map models across both neural networks and XGBoost. Thus, for future additions to the map pool, we can consider a model which uses no map information to achieve a rough win probability estimate. 

## **6 Conclusion** 

This work introduces a game-level win probability model for CSGO. We consider features at the start of each round, such as the map, team scores, equipment, money, and buy types. We consider a variety of modeling design choices, from model architecture to how to encode map information. 

|**Held out map**|**Previous**<br>**best NN**|**Initial model**|**Fine Tuned**|
|---|---|---|---|
|dust2|0.767|**0.759**|0.761|
|inferno|0.709|0.715|**0.705**|
|mirage|0.830|**0.821**|0.822|
|nuke|**0.716**|0.718|**0.716**|
|overpass|0.660|**0.646**|**0.646**|
|train|0.766|0.768|**0.759**|
|vertigo|0.707|0.697|**0.695**|

Table 7: Log-loss results by map for our previous hyperparameter tuned models, a initial model which was trained with data from all other maps and one that was fine tuned on the held out map. The maps trained on more data, either before or after fine-tuning perform better in 6 out of 7 cases indicating there is little advantage to training a model on a specific map only. 

We then investigate team buying decisions across the professional CSGO community. We find that teams are much more conservative with respect to round buying decisions than our model predicts is optimal. Particularly in second rounds, where a team lost the first round of the game, many teams are making sub-optimal buy decisions on the T side, with respect to our model. We also introduce _Optimal Spending Error_ (OSE), a metric to assess a team’s economic decision making. We find that OSE is correlated with other team success measures, such as round win rate. Finally, we conduct a test to assess how our model performs for “unplayed” maps, or maps that are not part of the active map pool. We find that our models can easily generalize to win probability prediction on new maps. 

We see many avenues of future work. One of the limitations of our work is that our data is limited to organized semi-professional and professional games. Because these games often have teams with dedicated, oftentimes very similar, strategies for particular scenarios, in some cases there may not be much variation buy types. Consider the example in Table 5. While there is variation in T buys for second rounds, the CT round buys have a high imbalance. One way to alleviate this issue is to also consider data from amateur, unorganized matches, which typically display more variation in buys. As buy decisions also exist in other FPS esports, such as Valorant, future work will be directed towards extending our framework to other games. 

## **References** 

- [Bedn´arek _et al._ , 2017a] David Bedn´arek, Martin Krulis, Jakub Yaghob, and Filip Zavoral. Data preprocessing of esport game records - counter-strike: Global offensive. In _Proceedings of the 6th International Conference on Data Science, Technology and Applications, DATA 2017, Madrid, Spain, July 24-26, 2017_ , pages 269–276. SciTePress, 2017. 

- [Bedn´arek _et al._ , 2017b] David Bedn´arek, Martin Krulis, Jakub Yaghob, and Filip Zavoral. Player performance evaluation in team-based first-person shooter esport. In _Data Management Technologies and Applications - 6th International Conference, DATA 2017, Madrid, Spain, July 24-26, 2017, Revised Selected Papers_ , volume 814 of _Communications in Computer and Information Science_ , pages 154–175. Springer, 2017. 

- [Bergstra _et al._ , 2013] James Bergstra, Daniel L K Yamins, and David Daniel Cox. Making a science of model search: Hyperparameter optimization in hundreds of dimensions for vision architectures. In _Proceedings of the 30th International Conference on International Conference on Machine Learning - Volume 28_ , ICML’13, page I–115–I–123. JMLR.org, 2013. 

- [Cervone _et al._ , 2014] Dan Cervone, Alexander D’Amour, Luke Bornn, and Kirk Goldsberry. Pointwise: Predicting points and valuing decisions in real time with nba optical tracking data. In _Proceedings of the 8th MIT Sloan Sports Analytics Conference, Boston, MA, USA_ , volume 28, page 3, 2014. 

- [Chen and Guestrin, 2016] Tianqi Chen and Carlos Guestrin. Xgboost: A scalable tree boosting system. In Balaji Krishnapuram, Mohak Shah, Alexander J. Smola, Charu C. Aggarwal, Dou Shen, and Rajeev Rastogi, editors, _Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, San Francisco, CA, USA, August 13-17, 2016_ , pages 785–794. ACM, 2016. 

- [Decroos _et al._ , 2019] Tom Decroos, Lotte Bransen, Jan Van Haaren, and Jesse Davis. Actions speak louder than goals: Valuing player actions in soccer. In _Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining, KDD 2019, Anchorage, AK, USA, August 4-8, 2019_ , pages 1851–1861. ACM, 2019. 

- [Fern´andez _et al._ , 2019] Javier Fern´andez, Luke Bornn, and Dan Cervone. Decomposing the immeasurable sport: A deep learning expected possession value framework for soccer. In _13th MIT Sloan Sports Analytics Conference_ , 2019. 

- [Hodge _et al._ , 2017] Victoria J. Hodge, Sam Devlin, Nick Sephton, Florian Block, Anders Drachen, and Peter I. Cowling. Win prediction in esports: Mixed-rank match prediction in multi-player online battle arena games. _CoRR_ , abs/1711.06498, 2017. 

- [Hodge _et al._ , 2019] Victoria Hodge, Sam Devlin, Nick Sephton, Florian Block, Peter Cowling, and Anders 

Drachen. Win prediction in multi-player esports: Live professional match prediction. _IEEE Transactions on Games_ , 2019. 

- [Kim _et al._ , 2020] Dong-Hee Kim, Changwoo Lee, and KiSeok Chung. A confidence-calibrated MOBA game winner predictor. In _IEEE Conference on Games, CoG 2020, Osaka, Japan, August 24-27, 2020_ , pages 622–625. IEEE, 2020. 

- [Liu and Schulte, 2018] Guiliang Liu and Oliver Schulte. Deep reinforcement learning in ice hockey for contextaware player evaluation. In _Proceedings of the 27th International Joint Conference on Artificial Intelligence_ , pages 3442–3448, 2018. 

- [Liu _et al._ , 2021] Shengmei Liu, A Kuwahara, J Scovell, J Sherman, and M Claypool. Lower is better? the effects of local latencies on competitive first-person shooter game players. _Proceedings of ACM CHI. Yokohama, Japan_ , 2021. 

- [Luo _et al._ , 2020] Yudong Luo, Oliver Schulte, and Pascal Poupart. Inverse reinforcement learning for team sports: Valuing actions and players. In _Proceedings of the TwentyNinth International Joint Conference on Artificial Intelligence, IJCAI 2020_ , pages 3356–3363. ijcai.org, 2020. 

- [Makarov _et al._ , 2017] Ilya Makarov, Dmitry Savostyanov, Boris Litvyakov, and Dmitry I. Ignatov. Predicting winning team and probabilistic ratings in ”dota 2” and ”counter-strike: Global offensive” video games. In _Analysis of Images, Social Networks and Texts - 6th International Conference, AIST 2017, Moscow, Russia, July 2729, 2017, Revised Selected Papers_ , volume 10716 of _Lecture Notes in Computer Science_ , pages 183–196. Springer, 2017. 

- [Semenov _et al._ , 2016] Aleksandr M. Semenov, Peter Romov, Sergey Korolev, Daniil Yashkov, and Kirill Neklyudov. Performance of machine learning algorithms in predicting game outcome from drafts in dota 2. In _Analysis of Images, Social Networks and Texts - 5th International Conference, AIST 2016, Yekaterinburg, Russia, April 7-9, 2016, Revised Selected Papers_ , volume 661 of _Communications in Computer and Information Science_ , pages 26– 37, 2016. 

- [Sicilia _et al._ , 2019] Anthony Sicilia, Konstantinos Pelechrinis, and Kirk Goldsberry. Deephoops: Evaluating microactions in basketball using deep feature representations of spatio-temporal data. In _Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining, KDD 2019, Anchorage, AK, USA, August 4-8, 2019_ , pages 2096–2104. ACM, 2019. 

- [Srivastava _et al._ , 2014] Nitish Srivastava, Geoffrey E. Hinton, Alex Krizhevsky, Ilya Sutskever, and Ruslan Salakhutdinov. Dropout: a simple way to prevent neural networks from overfitting. _J. Mach. Learn. Res._ , 15(1):1929–1958, 2014. 

- [Wang _et al._ , 2020] Kai Wang, Hao Li, Linxia Gong, Jianrong Tao, Runze Wu, Changjie Fan, Liang Chen, and Peng Cui. Match tracing: A unified framework for real-time 

win prediction and quantifiable performance evaluation. In _CIKM ’20: The 29th ACM International Conference on Information and Knowledge Management, Virtual Event, Ireland, October 19-23, 2020_ , pages 2781–2788. ACM, 2020. 

- [Xenopoulos _et al._ , 2020] Peter Xenopoulos, Harish Doraiswamy, and Cl´audio T. Silva. Valuing player actions in counter-strike: Global offensive. In _IEEE International Conference on Big Data, Big Data 2020, Atlanta, GA, USA, December 10-13, 2020_ , pages 1283–1292. IEEE, 2020. 

- [Yang _et al._ , 2017] Yifan Yang, Tian Qin, and Yu-Heng Lei. Real-time esports match result prediction. _CoRR_ , abs/1701.03162, 2017. 

- [Yang _et al._ , 2020] Zelong Yang, Zhu Feng Pan, Yan Wang, Deng Cai, Shuming Shi, Shao-Lun Huang, and Xiaojiang Liu. Interpretable real-time win prediction for honor of kings, a popular mobile MOBA esport. _CoRR_ , abs/2008.06313, 2020. 

- [Yurko _et al._ , 2019] Ronald Yurko, Samuel Ventura, and Maksim Horowitz. nflwar: A reproducible method for offensive player evaluation in football. _Journal of Quantitative Analysis in Sports_ , 15(3):163–183, 2019. 

- [Yurko _et al._ , 2020] Ronald Yurko, Francesca Matano, Lee F Richardson, Nicholas Granered, Taylor Pospisil, Konstantinos Pelechrinis, and Samuel L Ventura. Going deep: models for continuous-time within-play valuation of game outcomes in american football with tracking data. _Journal of Quantitative Analysis in Sports_ , 1(ahead-of-print), 2020.
