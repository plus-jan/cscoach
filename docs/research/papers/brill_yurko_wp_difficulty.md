---
id: brill_yurko_wp_difficulty
title: 'Exploring the Difficulty of Estimating Win Probability: A Simulation Study'
authors: Ryan S. Brill, Ronald Yurko, Abraham J. Wyner
year: 2025
venue: Journal of Quantitative Analysis in Sports (arXiv v5, Aug 2025)
url: https://arxiv.org/abs/2406.16171
arxiv_version: 2406.16171v5
license: arXiv — not verified for redistribution
pdf_sha256: d184b3d7bc121dc0
converted: '2026-09-28'
converter: pymupdf4llm
---

# Exploring the Difficulty of Estimating Win Probability: A Simulation Study

> Auto-converted from PDF. Tables, equations and figure text may be garbled — check the original PDF before quoting numbers.

<!-- cscoach-notes:start -->
## cscoach notes (hand-written — preserved on re-conversion)

**Authors:** Brill (Penn), Yurko (CMU), Wyner (Wharton). arXiv v5 (21 Aug 2025); JQAS.

- **Relevance:** **very high** for uncertainty (A-24, A-10, MV.4) and for how far WP-based claims can be
  trusted (A-04, coaching CIs).
- **Verified claims (simulation "random walk football" with known true WP; XGBoost estimator):**
  - Holding the number of rows fixed, stronger within-game dependence (K plays sharing an outcome)
    increases bias and variance **linearly in K** (§2.4, Fig. 1).
  - **Keep all plays.** Using all plays per game beats sampling one play per game, even though they are
    correlated. Independent outcomes of the same size would be much better still (Fig. 2).
  - Bias is largest **early in the game** (Fig. 3).
  - **Effective sample size** (defined by matching RMSE with independent data, not Kish): 4,101 games →
    ESS 2,291 (56%). 2,050 games → 31%; 8,202 games → 84% (§2.5).
  - **Bootstrap CIs for WP(x) (refit per resample, B = 101, nominal 90%) under-cover** (Table 5):
    - standard bootstrap: 0.60;
    - **cluster bootstrap: 0.71**;
    - randomized cluster (resample games, then plays within them): 0.76.
  - **Fractional bootstrap:** resample only φ·G games. With the randomized cluster variant, **φ = 0.35
    reaches 0.90 coverage**, with a mean width of 6.3 percentage points (Table 6). Coverage is still ~85%
    near WP ≈ 0.3/0.7 (Fig. 5).
  - φ **cannot be tuned on real data**, because true WP is unobservable. The proposal: tune it on a
    realistic generative state-space simulator fitted to the real data (§2.7).
  - State-space models (a transition model + simulation) have higher ESS but more bias (§3).
- **Corrections vs. synthesis:** the synthesis cited "Brill and Yurko" plus "Andersen 2021" for ESS
  inflation. This is the real source. It measures ESS by estimator accuracy, not by an ICC design effect.
- **Use in project (important):**
  - Distinguish two kinds of uncertainty (docs/specs/04 §2/§7 updated):
    - **(a) test-metric CIs** (Brier, ECE, … on held-out matches, no refit): a match-level cluster
      bootstrap is appropriate;
    - **(b) model-uncertainty CIs** for WP(x), WPA and counterfactual ΔWP (refit per resample):
      standard/cluster bootstraps are **too narrow**. Use the fractional randomized cluster bootstrap
      with φ tuned in MV.4.
  - MV.4 must build a **CS round simulator fitted to CSDS** (a transition model over alive counts,
    economy, time and bomb) as the known-truth environment for tuning φ. Our synthetic generator
    (docs/specs/04 §7) is the starting point.
  - Snapshot policy: keep all snapshots (A-22). Expect the most WP bias early in rounds, so report
    metrics per round phase.
  - Coaching: given interval widths of several percentage points, small ΔWP counterfactuals will often
    not be significant. The "CI excludes 0" rule (docs/specs/05) will filter many items, as intended.
  - The Kish-based ESS remains a *descriptive* diagnostic. The accuracy-based ESS can be estimated in
    the MV.4 simulator.
- **Caveats:** a simplified sport. The authors expect real sports (larger state spaces) to be worse,
  not better.
<!-- cscoach-notes:end -->

## Full text

# Exploring the Difficulty of Estimating Win Probability: A Simulation Study 

Ryan S. Brill<sup>∗</sup> , Ronald Yurko<sup>†</sup> , and Abraham J. Wyner<sup>‡</sup> 

August 21, 2025 

##### **Abstract** 

Estimating win probability is one of the classic modeling tasks of sports analytics. Many widely used win probability estimators use machine learning to fit the relationship between a binary win/loss outcome variable and certain game-state variables. To illustrate just how difficult it is to accurately fit such a model from noisy and highly correlated observational data, in this paper we conduct a simulation study. We create a simplified random walk version of football in which true win probability at each game-state is known, and we see how well a model recovers it. We find that the dependence structure of observational play-by-play data substantially inflates the bias and variance of estimators and lowers the effective sample size. Further, to achieve approximately valid marginal coverage, win probability confidence intervals need to be substantially wide. Concisely, these are high variance estimators subject to substantial uncertainty. Our findings are not unique to the particular application of estimating win probability; they are broadly applicable across sports analytics, as myriad other sports datasets are clustered into groups of observations that share the same outcome. 

> ∗Graduate Group in Applied Mathematics and Computational Science, University of Pennsylvania. Correspondence to: ryguy123@sas.upenn.edu 

> †Dept. of Statistics and Data Science, Carnegie Mellon University 

> ‡Dept. of Statistics and Data Science, The Wharton School, University of Pennsylvania 

1 

## **1 Introduction** 

Win probability (WP) as a function of game-state is a canonical value function in sports analytics (Baumer et al., 2023). In-game win probability is the crux of strategic decision making––make the decision that maximizes win probability––and is central to live betting on game outcomes. Fourth-down decision making in American football is a prime example: choose between a conversion attempt, field goal attempt, and punt according to win probability (Brill et al., 2025). 

Win probability is not a counting statistic or an observable quantity. Rather, it is defined by a model that is estimated from data. Estimating win probability is one of the classic modeling tasks of sports analytics. Win probability estimates arise broadly from one of three classes of models: simple mathematical models, probabilistic state-space models, and statistical models. Mathematical models are closed-form win probability functions with a simplified structure. State-space models simplify a game into a series of transitions between game-states, and transition probabilities are propagated into win probability by simulating games. Finally, statistical models are fit entirely from historical data––given the results of a set of observed plays, they fit the relationship between a binary win/loss outcome variable and certain game-state variables using regression or machine learning approaches. For a more thorough review of various ways of estimating win probability, see Section 2.3 and Baumer et al. (2023). 

Notably, statistical WP models are widely used today by analysts of American football (Lock and Nettleton, 2014; Baldwin, 2021). For instance, they form the foundation of open-source fourth-down recommendations (Brill et al., 2025). They are widely assumed to be reasonable and trustworthy because of the modeling flexibility of machine learning algorithms. Hence, in this paper we focus on statistical win probability estimators. The binary win/loss outcome variable, however, is noisy and features a strong dependence structure. In particular, each play in the same game shares the same draw of the win/loss outcome. Accordingly, Brill et al. (2025) found that these estimators are subject to substantial uncertainty and produce wide confidence intervals, even when fit from a large dataset featuring 229 _,_ 635 first-down plays across 4 _,_ 101 games and 16 years. We suspect statistical WP estimators have high variance, exacerbated by the dependence structure of observational 

2 

#### play-by-play data. 

To illustrate just how difficult it is to accurately fit a statistical win probability model from noisy and highly correlated observational data, in this paper we conduct a simulation study. We create a simplified random walk version of football in which true win probability at each game-state is known. Then, we see how well a statistical model recovers true win probability. We find that the dependence structure of observational play-by-play data inflates both the bias and variance of these estimators. We also calculate the effective sample size of the observational dataset. Due to the dependence structure, we have half as much data as we think. Specifically, a WP estimator fit from a correlated dataset with 4 _,_ 101 games has the same accuracy as one fit from a dataset of independent outcomes with half as many games. Finally, we explore the efficacy of bootstrapped confidence intervals in quantifying uncertainty in WP estimates. Naive bootstrapped confidence intervals do not achieve nominal marginal coverage. Tuning the bootstrap to produce approximately valid coverage, we find that to cover true win probability 90% of the time, confidence intervals need to be substantially wide (i.e., a mean width of 6 _._ 3% WP). Each of these findings emphasize the difficulty of estimating win probability using machine learning. 

Our study aligns thematically with existing research on the impact of clustered observations in sports analytics. Other researchers have found similar conclusions, though in the context of injury or biomechanics data rather than the context of estimating win probability: a strong dependence structure inflates the bias and variance of estimators. Hayen (2006) found that ignoring a clustered dependence structure can lead to “misleading conclusions” and confidence intervals that are too narrow; analyzing clustered data requires “an increased sample size when compared to those without clustering.” Cook (2010) similarly found that naive statistical techniques that do not account for such dependence structures are “inappropriate.” Chandran et al. (2019) studied the impact of clustering on drawing inferences from injury-surveillance data. They conducted a simulation study similar in spirit to ours, simulating injury datasets “using varying degrees of observation clustering,” comparing “inferences made using traditional techniques with those made after accounting for clustering.” Not accounting for the dependency structure resulted in “flawed inferences” and biased estimates, with the degree of bias increasing as the strength of the clustering 

3 

increased. Finally, Staynor et al. (2019) found that statistical analysis of clustered biomechanics data requires “statistically appropriate” models beyond naively applied regression models that result in “erroneous parameter estimates...which have the potential to mislead future research and real-world applications.” 

The remainder of this paper is organized as follows. In Section 2.1 we specify the rules of _random walk football_ . In Section 2.2 we discuss how we generate random walk football play-by-play datasets. In Section 2.3 we detail various ways of estimating win probability, including the statistical WP estimator that we consider throughout this paper. In Section 2.4 we compute the bias-variance decomposition of a win probability estimator fit from various versions of observational datasets. In Section 2.5 we use this bias-variance decomposition to compute the effective sample size of a dataset that mimics the historical dataset of real American football plays. In Section 2.6 we show that naive bootstrapped win probability confidence intervals do not achieve nominal coverage and are too narrow. In Section 2.7 we introduce the fractional bootstrap, which we tune to produce wider confidence intervals that achieve adequate coverage in our simulation setting. Finally, in Section 3 we conclude and discuss ideas for future work. 

## **2 The simulation study** 

### **2.1 Introducing random walk football** 

We begin by describing the rules of random walk football. Random walk football begins at midfield (yardline _L/_ 2, where _L_ is an even integer). Each play, the ball moves left or right by one yardline with equal probability. If the ball reaches the left end of the field (yardline 0), team one scores a touchdown, worth +1 point. If the ball reaches the right end of the field (yardline _L_ ), team two scores a touchdown, worth _−_ 1 point. The ball resets to midfield after each touchdown. After _T_ plays, the game ends. If the game is still tied after _T_ plays, a fair coin is flipped to determine the winner. 

Formally, the outcome of the _t_<sup>_th_</sup> play of the _g_<sup>_th_</sup> game is 

4 

The game starts at midfield, _Xg_ 0 = _L/_ 2, and the game begins tied, _Sg_ 0 = 0. The field position at the start of play _t_ is 

and the score differential at the start of play _t_ is 

The binary win/loss response column is 

The true win probability 

of random walk football is computed explicitly using dynamic programming, 

5 

and 

### **2.2 Random walk football play-by-play data** 

A simulated observational dataset of random walk football plays consists of _G_ games, each with _T_ plays per game. Such a dataset has the form 

For each play of game _g_ , we record the timestep _t_ , the field position _Xgt_ , the score differential _Sgt_ , and a binary variable _ygt_ indicating whether the team with possession wins the game. The dependence structure of random walk football (and real football) play-by-play data manifests in the outcome vector _{ygt}_ : plays from the same game share the same draw of the winner of the game. Formally, _ygt ≡ yg,T_ +1 as in Equation (4). Importantly, we also know the underlying true win probability WP _gt_ at each play, which we use to evaluate win probability estimates. 

Throughout this study, we let _T_ = 56, the average number of first-down plays per game in the dataset of American football plays from Brill et al. (2025). We use _L_ = 4 yardlines so that the average number of plays between each score is similar to the average number of first-down plays in a game of American football. 

We want to assess the impact of the dependence structure of the response variable of observational football data on the accuracy of a statistical win probability estimator. To do so, we compare the accuracy of a WP estimator fit from datasets of varying degrees of dependence. We introduce a parameter _K_ that controls the degree of dependence of the win/loss outcome variable in a generated dataset: we keep a random subsample of _K_ plays per generated game. _K_ = 1––keep just 1 randomly sampled play in each of the _G_ simulated games––reflects independence across all plays in the filtered dataset because each game is generated independently. When _K_ = 1, the outcome variable _ygt_ reflects an independent draw of the win/loss outcome of the game since each play is filtered from a 

6 

separate game. _K_ = _T_ ––keep all _T_ plays in each of the _G_ simulated games––reflects full dependence within each game and is equivalent to the original dataset. When _K_ = _T_ , the outcome variable _ygt_ for each play _t_ in game _g_ reflects the same draw of the win/loss outcome of the game. Integer values of _K_ between 1 and _T_ reflect intermediate degrees of dependence because just 1 _< K < T_ plays per game share the same draw of the response variable. For concreteness, we visualize example datasets for _K_ = 1, _K_ = 3, and _K_ = _T_ in Table 4. 

<!-- Start of picture text -->
x t s y<br>x t s y x 2 5 t 0 s y 1  2321 1234 0000 1111 <br>1331 2243521 0513 1111 }}}} fromfromfromfrom gamegamegamegame 1234 13221 1637172254 -1-4130 00110  fromfrom gamegame 12 21... 5556... . . . 22... 11...  game 1<br>22... 215... -77... 01... }} fromfrom gamegame ζζ ·· T T − 1 1... 3... . . . 0... 1...  2121 1234 0000 0000 <br>Table 1: Visualizing a  K = 1 13 1941 01 11  from game ζ · T/ 3 3... 55... -5... 0...  game ζ<br>2 56 -5 0 <br><!-- End of picture text -->

Table 1: Visualizing a _K_ = 1 dataset. 

Table 2: Visualizing a _K_ = 3 dataset. 

Table 3: Visualizing a _K_ = _T_ = 56 dataset. 

Table 4: Visualizing example generated datasets with varying degrees of dependence _K_ . Each dataset has the same nominal sample size, _ζ · T_ plays (rows). The variables are: field position _x_ , time _t_ , score differential _s_ , binary win/loss _y_ . In the _K_ = 1 dataset (a), all plays are independent because they are generated from separate independent games. In the _K_ = 3 dataset (b), groups of 3 plays are generated from the same game. Each group of 3 plays shares the same draw of the response _y_ and plays from different games are independent. The _K_ = _T_ dataset (c) includes all _T_ plays from each generated game. Within each game, all plays share the same draw of the response _y_ , and plays from different games are independent. 

Generating a dataset with _G_ games and _T_ = 56 plays per game, keeping just _K_ randomly sampled plays per game, has a nominal sample size (number of rows) of _G · K_ plays. We want to compare the performance of a win probability estimator fit from datasets of varying degrees of dependence _K_ that have the same nominal sample size. To do so, given _K_ , we generate _G_ = round( _ζ · T/K_ ) games and keep _K_ plays per game. This yields a dataset consisting of (approximately) _ζ · T_ plays, which is independent of _K_ . As _T_ = 56 throughout this paper, _ζ_ parameterizes the sample size. 

7 

### **2.3 Ways to estimate win probability** 

From a dataset of football plays, we want to estimate win probability. Win probability is not a counting statistic or an observable quantity. Rather, it is defined by a model that is estimated from data. Estimating win probability is one of the classic modeling tasks of sports analytics. Win probability estimates arise broadly from one of three classes of models: simple mathematical models, probabilistic state-space models, and statistical models. We give an overview of these classes below. For a more thorough review we refer to the reader to Baumer et al. (2023). 

Stern (1994), for example, uses a simple mathematical model to estimate win probability in basketball. Supposing possession-level score differential outcomes are independent and approximately Gaussian, he models the score differential process by a Brownian motion with drift _µ_ points advantage for the home team and variance _σ_<sup>2</sup> . He uses probit regression to estimate _p_ ( _l, t_ ), the probability the home team wins if they are leading by _l_ points after _t_ seconds of game time, _p_ ( _l, t_ ) = Φ�( _l_ + (1 _− t_ ) _µ_ ) _/_ ~~�~~ (1 _− t_ ) _σ_<sup>2�</sup> . The benefit of such mathematical models is their simplicity: they have closed-form solutions. The drawback is they rely on unreasonable assumptions (e.g., normality), which fail in particular towards the end of a game and work for a limited set of game-state variables (e.g., just score differential and time). 

State-space models simplify a game into a series of transitions between game-states. Transition probabilities are estimated from play-level data and are then propagated into win probability by simulating games. Win probability in baseball is commonly estimated using state-space models going back to Lindsey (1961). These models work well in baseball because the game consists of discrete events (i.e., the game is divided into 9 innings, each of which feature a sequence of individual pitcher-batter matchups) and there are just a few important game-state variables (e.g., base-state, outs, runs, and inning). When implemented correctly, state-space models are sensible ways to estimate WP. However, they are difficult in practice, as they require: a careful encoding of the convoluted rules of a sport into a set of states and the actions between those states, careful estimation of transition probabilities, and enough computing power to run enough simulated games to achieve desired granularity. Each of these can be nontrivial depending on the complexity 

8 

of the sport. 

Finally, statistical models are fit entirely from historical data. Given the results of a set of observed plays, statistical models fit the relationship between a binary win/loss outcome variable and certain game-state variables using regression or machine learning approaches. Notably, these models are widely used today by analysts of American football (Lock and Nettleton, 2014; Baldwin, 2021). They form the foundation of open-source fourth-down recommendations (Brill et al., 2025). These models are popular due to the accessibility of rich publicly available data (e.g., play-by-play data from nflFastR Carl and Baldwin (2022)) and off-the-shelf machine learning tools (e.g., XGBoost Chen and Guestrin (2016)). They are widely assumed to be reasonable and trustworthy because of the modeling flexibility of machine learning algorithms. For these reasons, in this paper we focus on statistical win probability estimators. The binary win/loss outcome variable, however, is noisy and features a strong dependence structure–each play in the same game shares the same draw of the win/loss outcome. Accordingly, Brill et al. (2025) found that these estimators are subject to substantial uncertainty and produce wide confidence intervals, even when fit from a large dataset featuring 229 _,_ 635 first-down plays across 4 _,_ 101 games and 16 years. We suspect statistical WP estimators have high variance, exacerbated by the dependence structure of observational play-by-play data. 

Continuing the tradition of Baldwin (2021), throughout this paper we estimate win probability using XGBoost. The covariates are **x** = ( _t, x, s_ ), where _t_ denotes time, _x_ denotes field position, and _s_ denotes score differential. The outcome variable is binary win/loss _y_ . We use half of the games from the training set as a validation set to tune XGBoost models. 

### **2.4 Bias-variance decomposition** 

In this section, we analyze the bias-variance decomposition of an XGBoost win probability estimator. We compare a WP estimator fit from datasets having the same nominal sample size _ζ ·T_ but generated with varying degrees of dependence _K_ . Given a combination of data generating parameters, we generate _M_ = 100 training datasets. We fit a win probability estimator from each dataset, _{_ WP<sup>�</sup> ( _m_ ) _}Mm_ =1<sup>.We also generate</sup><sup>_M_= 100 out-of-sample testing</sup> datasets _{_ Dtest<sup>(</sup><sup>_m_)</sup><sup>_}M_</sup> _m_ =1<sup>using(</sup><sup>_G_=10</sup><sup>_,_000</sup><sup>_, T_=56</sup><sup>_, K_=1).Then,wecalculatethesquared</sup> 

9 

bias of the _m_<sup>_th_</sup> estimator by 

and the variance by 

The root mean squared error is RMSE _m_ = ~~�~~ bias<sup>2</sup> _m_<sup>+ var</sup><sup>_m_.Wethencalculatetheaverage</sup> squared bias, variance, and RMSE across the _M_ simulations and their standard errors. 

First, let _ζ_ = 4 _,_ 101 to mimic the dataset of real American football plays. We compare the accuracy of a WP estimator fit from a ( _G_ = round( _ζ · T/K_ ) _, T_ = 56 _, K_ ) dataset as the degree of dependence _K_ varies. The sample size in each of these datasets is (approximately) the same, _G · K_ = _ζ · T_ . We visualize this bias-variance decomposition as _K_ varies in Figure 1. As the strength _K_ of the correlation increases, accuracy decreases linearly. Fixing the number of observations in the dataset but increasing the degree of dependence across outcomes reduces model accuracy. Intuitively, this makes sense because the degree of dependence _K_ is inversely proportional to the amount of available independent data––there are (approximately) _ζ · T/K_ independent draws of the response variable. Less independent data produces less accurate estimators. 

Next, as a function of sample size _ζ · T_ (with _T_ = 56), we compare the accuracy of a WP estimator fit from three types of datasets. First, we consider a ( _G_ = _ζ, K_ = _T_ ) dataset, which keeps each generated play per game. This dataset mimics the historical dataset of real American football plays. Then, we consider a ( _G_ = _ζ, K_ = 1) dataset, which keeps just one randomly sampled play per game. This dataset consists entirely of independent outcomes, and can be formed wholly from a ( _G_ = _ζ, K_ = _T_ ) dataset, but its sample size is much smaller ( _ζ_ rather than _ζ · T_ ). Finally, we consider a ( _G_ = _ζ · T, K_ = 1) dataset, which has the same sample size (number of rows) _ζ · T_ as the first dataset, but consists entirely of independent outcomes. 

In Figure 2 we visualize the bias-variance decomposition of a win probability estimator 

10 

Figure 1: Squared bias (left), variance (middle), and RMSE of a win probability estimator fit from a ( _G_ = round( _ζ · T/K_ ) _, T_ = 56 _, K_ ) dataset as a function of _K_ , where _ζ_ = 4 _,_ 101. The dots denote the average values across _M_ = 100 simulations and the bars denote plus/minus twice the standard errors. The gray line is the regression line. 

fit from these three types of datasets as a function of _ζ_ . The _x_ -axis is log4( _ζ_ ) because 4<sup>6</sup> = 4 _,_ 096 _≈_ 4 _,_ 101 is the sample size of the historical dataset of American football plays. We see that it is much better to use all plays per game rather than one independent play per game. Despite the strong dependence structure, keeping all the plays elucidates information about the structure of the covariate space. We also see that it would be much better if the plays had independent outcomes. This suggests that the dependence structure reduces the effective sample size of the dataset. We explore the extent of this reduction in the next section. 

Interestingly, as shown in Figure 3, we see that the bias is much worse at the beginning of the game. Game-states with larger score differentials in the early game occur less frequently than other game-states. Also, intuitively it is easier to tie later game-states to the ultimate win/loss outcome, which is determined at the end of the game. 

11 

<!-- Start of picture text -->
(a)<br>(b)<br><!-- End of picture text -->

Figure 2: Squared bias (left), variance (middle), and RMSE (right) of a win probability estimator fit from three datasets as a function of _ζ_ . The ( _G_ = _ζ, K_ = _T_ ) dataset (blue) involves keeping each generated play per game, which mimics the historical dataset of real American football plays. The ( _G_ = _ζ, K_ = 1) dataset (red) is formed by keeping just 1 play per game. The ( _G_ = _ζ · T, K_ = 1) dataset (orange) has the same sample size (number of rows) _ζ · T_ as the first dataset but consists entirely of independent outcomes. 

### **2.5 Effective sample size** 

As discussed in the previous section, we can calculate the accuracy of a win probability estimator fit from a ( _G_ = _ζ, T_ = 56 _, K_ ) dataset, denoted RMSE( _ζ, K_ ). The sample size (number of rows) of such a dataset with _ζ_ = 4 _,_ 101 and _K_ = _T_ , which mimics the historical dataset of American football plays, is _ζ · T_ . We saw that the dependence structure of this dataset reduces the accuracy of our estimator, but we would like to understand the extent of this reduction. In particular, we are interested in the _effective sample size_ (ESS) of that dataset. The ESS is the sample size _ζ_<sup>_′_</sup> _·T_ of a ( _G_ = _ζ_<sup>_′_</sup> _·T, T_ = 56 _, K_ = 1) dataset consisting of independent outcomes, which produces an estimator having the same accuracy as one fit from the original dataset. For brevity, we refer to the sample size as _ζ_ and the effective sample size as _ζ_<sup>_′_</sup> , dropping the _T_ since we use _T_ = 56 throughout this study. 

To estimate this effective sample size, we begin by fitting the _K_ = 1 and _K_ = _T_ 

12 

Figure 3: Bias ( _y_ -axis) versus time _n_ ( _x_ -axis) and score differential _s_ (color) at midfield (field position _x_ = 2) of win probability estimated from a ( _G_ = 4 _,_ 101 _, T_ = 56 _, K_ = _T_ ) dataset. The lines denote the average values across _M_ = 100 simulations and the shaded regions denote plus-minus twice the standard errors. 

accuracy curves _ζ �→_ RMSE( _ζ, K_ ) from Figure 2b. For each curve, we fit a biexponential model using nonlinear least squares. Then, as a function of _ζ_ , the ESS is the value _ζ_<sup>_′_</sup> satisfying RMSE( _ζ_<sup>_′_</sup> _, K_ = 1) = RMSE( _ζ, K_ = _T_ ). In Figure 4 we visualize the ESS _ζ_<sup>_′_</sup> as a function of _ζ_ . The ESS of a ( _ζ_ = 4 _,_ 101 _, K_ = _T_ ) dataset is _ζ_<sup>_′_</sup> = 2 _,_ 291, or 56% of the nominal sample size. This result is striking: we estimate that the historical dataset of American football plays (where _ζ_ = 4 _,_ 101) consists of about half as much data as suggested by the number of plays. In other words, we are effectively fitting win probability models from 8 years, not 16 years, worth of independent win/loss outcomes. Real American football is exponentially more complex than random walk football. Its game-state space is much larger, so we expect the ESS to be even smaller in real life. 

If we halved the size of our _K_ = _T_ dataset, fitting a win probability model from _ζ_ = 2 _,_ 050 games (8 seasons), we estimate the effective sample size is _ζ_<sup>_′_</sup> = 645, or just 31% of the nominal sample size. This mimics fitting a win probability model from just recent data. If we doubled the size of our _K_ = _T_ dataset, fitting a win probability model from _ζ_ = 8 _,_ 202 games (32 seasons), we estimate the effective sample size is _ζ_<sup>_′_</sup> = 6 _,_ 911, or 84% of the nominal sample size. 

13 

Figure 4: The effective sample size _ζ_<sup>_′_</sup> of a ( _G_ = _ζ, T_ = 56 _, K_ = _T_ ) dataset as a function of _ζ_ . The red dot denotes _ζ_ = 4 _,_ 101, the number of games in the historical dataset of real American football plays. 

### **2.6 Coverage of bootstrapped confidence intervals** 

We have seen that machine learning win probability estimators fit from noisy and highly correlated observational data have high variance. Due to the dependence structure of historical football data, the effective sample size is much smaller than the nominal sample size. Therefore, we want to quantify uncertainty in win probability point estimates. The point estimates alone may not be trustworthy. The bootstrap is a natural choice to capture such uncertainty since it is non-parametric and does not make strong assumptions. Hence, in this section we explore the efficacy of bootstrapped win probability confidence intervals. 

We begin with the standard (i.i.d.) bootstrap, which assumes each row (play) of the dataset is independently drawn. In the standard bootstrap, each of _B_ bootstrapped datasets are formed by re-sampling _G · T_ plays uniformly with replacement (recall _G_ is the number of games, _T_ is the number of plays per game, and _G · T_ is the total number of plays in a random walk football observational dataset). The assumptions of the standard bootstrap do not apply to observational play-by-play data due to its dependence structure. Hence, we also try the cluster bootstrap, in which each of _B_ bootstrapped datasets are formed by re-sampling _G_ games uniformly with replacement, keeping each observed play 

14 

within each re-sampled game. Finally, in the randomized cluster bootstrap, each of _B_ bootstrapped datasets are formed by re-sampling _G_ games uniformly with replacement, and within each game re-sampling _T_ plays uniformly with replacement. 

Each type of bootstrap produces _B_ bootstrapped datasets _{_ Dtrain<sup>(</sup><sup>_b_)</sup><sup>_}_</sup> _b_<sup>_B_</sup> =1<sup>from the training</sup> dataset Dtrain. We then fit a win probability model to each bootstrapped dataset using XGBoost, _{_ WP<sup>�</sup> _b}_<sup>_B_</sup> _b_ =1<sup>.Fromthese,weforma90%confidenceintervalforWP(</sup><sup>**x**)atgame-</sup> state **x** by the 5<sup>_th_</sup> and 95<sup>_th_</sup> quantiles of _{_ WP<sup>�</sup> _b_ ( **x** ) _}_<sup>_B_</sup> _b_ =1<sup>.Letting</sup><sup>_B_=101inthissection,</sup> we form a 90% confidence interval by [WP<sup>�</sup> (6)( **x** ) _,_ WP<sup>�</sup> (96)( **x** )]. To avoid substantially low coverage near the extremes (WP( **x** ) _≈_ 0 or WP( **x** ) _≈_ 1), we widen our confidence intervals when WP<sup>�</sup> ( **x** ) _<_ 0 _._ 025 to have a lower bound of 0 and when WP<sup>�</sup> ( **x** ) _>_ 0 _._ 975 to have an upper bound of 1. We evaluate the efficacy of these intervals by their coverage and width. For each type of bootstrap (standard bootstrap, cluster bootstrap, and randomized cluster bootstrap) and each simulation _m ∈{_ 1 _, ..., M_ = 100 _}_ , we compute the pointwise marginal coverage of bootstrapped confidence intervals, 

This is the proportion of plays in _m_<sup>_th_</sup> held-out dataset whose true win probability lies inside the confidence interval. We also compute the mean width, 

For each play in the _m_<sup>_th_</sup> held-out dataset, we calculate the width of the confidence interval, and then take the average across all the plays. We report the average and the standard error of these values _{_ coverage _m}_<sup>_M_</sup> _m_ =1<sup>and</sup><sup>_{_width</sup><sup>_m}M_</sup> _m_ =1<sup>in Table 5.To mimic the historical</sup> dataset of American football plays, each simulated dataset here consists of _G_ = 4 _,_ 101 games, _T_ = 56 plays per game, and _K_ = _T_ plays per game that share the same outcome. 

Even in our simplified setting of random walk football, each of these bootstrapped win probability confidence intervals are undercovered. Intuitively, naive bootstraps produce 

15 

|90% CI method|coverage|width|
|---|---|---|
|standard bootstrap|0_._60_±_0_._01|0_._027_±_0_._0005|
|cluster bootstrap|0_._71_±_0_._01|0_._036_±_0_._0004|
|randomized cluster bootstrap|0_._76_±_0_._01|0_._042_±_0_._0003|

Table 5: Pointwise marginal coverage and mean width of nominally 90% confidence intervals formed from each type of bootstrap with _B_ = 101 bootstrapped re-samples. We report these values averaged over the _M_ = 100 simulations plus/minus twice their standard errors. Each simulation uses _G_ = 4 _,_ 101, _T_ = 56, and _K_ = _T_ . 

intervals that are too narrow because they involve resampling from observed data––which entails re-using observations without generating new ones––thus exploring a strictly smaller subspace of the ( **x** _, y_ ) space than the true sampling distribution. In other words, the bootstrapped resampling distribution is a rough approximation of the true sampling distribution. The naive standard bootstrap in particular achieves dismally low marginal coverage. Even the randomized cluster bootstrap that accounts for the dependence structure does not achieve high enough coverage. We suspect this coverage issue would be even worse for real American football, which is exponentially more complex than random walk football. 

### **2.7 The fractional bootstrap** 

Naive bootstrapped confidence intervals are not wide enough. A natural question arises: how wide do confidence intervals need to be so that nominally 90% intervals actually achieve 90% marginal coverage? Hence, in this section we explore alternative forms of the bootstrap to increase coverage. 

The traditional method of tuning non-parametric bootstrapped confidence intervals is to calibrate the bootstrapped quantiles (DiCiccio and Efron, 1996). For instance, instead of using the _α/_ 2<sup>_th_</sup> and (1 _− α/_ 2)<sup>_th_</sup> quantiles of _{_ WP<sup>�</sup> _b_ ( **x** ) _}_<sup>_B_</sup> _b_ =1<sup>toforma1</sup><sup>_−α_confidence</sup> interval, use the _β/_ 2<sup>_th_</sup> and (1 _−β/_ 2)<sup>_th_</sup> quantiles for some _β < α_ . In order for this traditional calibration method to work, _B_ would have to be much larger than 101, likely an order of magnitude larger (e.g., _B_ = 1001). We, however, prefer to use lower values of _B_ (e.g., closer to 101) for several reasons. It is much better to keep _B_ small for applications that require evaluating bootstrapped predictions in real time. For example, a bootstrapped fourth-down decision recommendation from Brill et al. (2025) takes about 15 seconds when 

16 

_B_ = 101 and about 2 _._ 5 minutes when _B_ = 1001. The former can be run before a fourthdown play begins and the latter takes far too long. Additionally, storing 1001 machine learning models is much more expensive than storing 101 of them. For these reasons, in this study we stray away from the traditional bootstrap calibration method. 

Instead, we introduce an alternative method to calibrate bootstrapped confidence intervals, the _fractional bootstrap_ . It has the same time and storage complexity as traditional bootstrap methods. Specifically, we introduce a parameter _ϕ ∈_ (0 _,_ 1] denoting the fraction of data to be re-sampled in generating a bootstrapped dataset. By re-sampling less data than in the original dataset, we widen bootstrapped confidence intervals and increase coverage. In the fractional standard bootstrap, we re-sample _T ·G·ϕ_ plays (rows) uniformly with replacement. In the fractional cluster bootstrap, we re-sample _G · ϕ_ games uniformly with replacement, keeping each observed play within each re-sampled game. Finally, in the fractional randomized cluster bootstrap, we re-sample _G · ϕ_ games uniformly with replacement, and within each game re-sample _T_ plays uniformly with replacement. 

In Table 6 we report the results of applying the randomized cluster bootstrap to our simulation study for various values of _ϕ_ . To mimic the historical dataset of American football plays, each simulated dataset consists of _G_ = 4 _,_ 101 games, _T_ = 56 plays per game, and _K_ = _T_ plays per game that share the same outcome. As expected, lowering _ϕ_ widens the confidence intervals and increases marginal coverage. In order to achieve 90% marginal coverage, _ϕ_ needs to be as small as 0 _._ 35. Those intervals have a mean width of 6 _._ 3%. This result is striking: in our simplified setting of random walk football, win probability confidence intervals need to be extremely wide to achieve approximately valid coverage. This exemplifies the difficulty of accurately estimating win probability by fitting a machine learning model from noisy and highly correlated football game outcomes. These estimators are subject to large uncertainty. 

Marginal coverage is a sufficient condition for confidence intervals to be “good,” but it is not a necessary requirement for decision making. Even with 90% marginal coverage, it could be that CI( **x** ) always covers WP( **x** ) for 90% of game-states **x** and never covers for the other 10%. It may be disastrous to make decisions at the game-states for which intervals never cover. To check that these intervals achieve reasonable coverage across the space 

17 

|_ϕ_|coverage|width|
|---|---|---|
|1|0_._76_±_0_._01|0_._042_±_0_._0003|
|0_._75|0_._80_±_0_._01|0_._047_±_0_._0003|
|0_._5|0_._85_±_0_._01|0_._055_±_0_._0004|
|0_._35|0_._90_±_0_._01|0_._063_±_0_._0004|

Table 6: Pointwise marginal coverage and mean width of nominally 90% confidence intervals formed from the _ϕ_ -fractional randomized cluster bootstrap with _B_ = 101 bootstrapped re-samples for various values of _ϕ_ . We report these values averaged over the _M_ = 100 simulations plus/minus twice their standard errors. Each simulation uses _T_ = 56, _K_ = 56, and _G_ = 4 _,_ 101. 

of game-states, we bin game-states **x** by their true win probability WP( **x** ) and consider coverage in each bin. In Figure 5 we visualize coverage and its standard error across such bins. For bins near the middle (WP _≈_ 0 _._ 5) or the extremes (WP _≈_ 0 and WP _≈_ 1), coverage is high enough. For other bins (WP _≈_ 0 _._ 3 and WP _≈_ 0 _._ 7), the intervals remain undercovered, albeit slightly (coverage hovers around 85%). The game is still competitive in those regions and strategic decisions matter. In future work, we recommend exploring more refined confidence intervals that achieve higher conditional coverage. 

Figure 5: Coverage of 90% bootstrapped confidence intervals, via the fractional randomized cluster bootstrap for _ϕ_ = 0 _._ 35, across the space of game-states **x** binned by WP( **x** ). 

In practice, it is impossible to tune the bootstrap at all, using either the traditional 

18 

method from DiCiccio and Efron (1996) or the fractional bootstrap. This is because we need to know true win probability in order to tune the _β_ or _ϕ_ values in these alternative bootstraps to achieve adequate coverage. While we know true win probability in our simulation setting, it is an unobservable quantity in real life. Coverage is not calculable for real data because the win/loss outcome is either 0 or 1 and win probability estimates lie in (0 _,_ 1). 

This severe limitation of the tuned bootstrap, nonetheless, does not render its development in this paper worthless––it helped us further illustrate that win probability estimates are subject to substantial uncertainty. Furthermore, though imperfect and difficult, we propose a way to tune the bootstrap with real data as follows. Succinctly, we suggest tuning the fractional bootstrap using a hyper-realistic generative win probability model. To do so, first, given the real historical play-by-play dataset, fit as realistic and granular a probabilistic state-space win probability model as possible. As discussed in Section 2.3, this entails fitting a play-level transition probability model, which is then propagated into win probability by simulating games. Then, generate _M_ synthetic play-by-play datasets from the simulator, apply the _ϕ_ -fractional randomized cluster bootstrap for various values of _ϕ_ to each of them, and select the value of _ϕ_ that achieves desired marginal coverage. 

As stressed in Section 2.3, fitting a hyper-realistic football simulator is a delicate and extremely difficult task. This is because it requires a careful encoding of the convoluted rules of football into a set of states and the actions between those states and careful estimation of transition probabilities. Those we know who have created such simulators––including professional sports bettors, football analysts, and hedge fund analysts––do not make them publicly available because they are proprietary and because they use them to make money on the betting markets. One contact said it took him eight months to construct such a simulator. 

## **3 Discussion** 

Statistical win probability estimators are widely used across sports analytics. For instance, they form the foundation of open source fourth-down recommendations. Here, we use a simulation study to show just how difficult it is to accurately estimate win probability using 

19 

a statistical model. Observational play-by-play data has a strong dependence structure that inflates the bias and variance of these estimators. Further, to achieve approximately valid marginal coverage, win probability confidence intervals need to be substantially wide. Concisely, these are high variance estimators subject to substantial uncertainty. 

In future work, we suggest exploring probabilistic state-space models to estimate win probability (for real sports like American football). Those models simplify the game of football into a series of transitions between game-states. Transition probabilities are estimated from play-level data and win probability is calculated by simulating games. The effective sample size (ESS) is the number of plays because transition probabilities are fit from independent play-level observations. Though state-space models have lower variance (via a higher ESS) than statistical models, they have higher bias, as they make stronger simplifying assumptions. 

We also look forward to further research on the impact of a strong dependency structure in other sports applications. The structure of play-by-play win probability data, in which groups of observations share the same outcome, is not unique. It is prevalent across myriad sports datasets. It appears in any dataset in which the outcome variable is the final result of some unit of time (e.g., a game or play) and the observations consist of units (e.g., frames or plays) leading to that end result. For instance, expected points models are fit from play-by-play data for which large clusters of plays share the same next score outcome (Yurko et al., 2019). This structure also appears in models fit from tracking data that map actions during each frame of a play to the ultimate outcome of a play. For instance, Yurko et al. (2020) use tracking data to model the expected yards gained for a ball-carrier during the course of a play. Each row (frame) within the same play shares the same outcome (yards gained on that play). 

20 

## **References** 

- Baldwin, B. (2021). NFL win probability from scratch using xgboost in R. `https://www.opensourcefootball.com/posts/ 2021-04-13-creating-a-model-from-scratch-using-xgboost-in-r/` . 

- Baumer, B. S., Matthews, G. J., and Nguyen, Q. (2023). Big ideas in sports analytics and statistical tools for their investigation. _Wiley Interdisciplinary Reviews: Computational Statistics_ , 15(6):e1612. 

- Brill, R. S., Yurko, R., and Wyner, A. J. (2025). Analytics, have some humility: A statistical view of fourth-down decision making. _The American Statistician_ , 79(3):393–409. 

- Carl, S. and Baldwin, B. (2022). _nflfastR: Functions to Efficiently Access NFL Play by Play Data_ . `https://www.nflfastr.com/` . 

- Chandran, A., Brown, D., Nedimyer, A., and Kerr, Z. (2019). Statistical methods for handling observation clustering in sports injury surveillance. _Journal of Athletic Training_ , 54. 

- Chen, T. and Guestrin, C. (2016). XGBoost: A scalable tree boosting system. In _Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining_ , KDD ’16, pages 785–794, New York, NY, USA. ACM. 

- Cook, I. (2010). Analysing recurrent events in exercise science and sports medicine. _South African Journal of Sports Medicine_ , 22:44–45. 

- DiCiccio, T. J. and Efron, B. (1996). Bootstrap confidence intervals. _Statistical Science_ , 11(3):189–212. 

- Hayen, A. (2006). Clustered data in sports research. _Journal of Science and Medicine in Sport_ , 9(1):165–168. 

- Lindsey, G. R. (1961). The progress of the score during a baseball game. _Journal of the American Statistical Association_ , 56(295):703–728. 

21 

- Lock, D. and Nettleton, D. (2014). Using random forests to estimate win probability before each play of an nfl game. _Journal of Quantitative Analysis in Sports_ , 10. 

- Staynor, J. M., Byrne, S. D., Alderson, J. A., and Donnelly, C. J. (2019). The applied impact of ‘na¨ıve’ statistical modelling of clustered observations of motion data in injury biomechanics research. _Journal of Science and Medicine in Sport_ , 22(4):420–424. 

- Stern, H. S. (1994). A brownian motion model for the progress of sports scores. _Journal of the American Statistical Association_ , 89(427):1128–1134. 

- Yurko, R., Matano, F., Richardson, L. F., Granered, N., Pospisil, T., Pelechrinis, K., and Ventura, S. L. (2020). Going deep: models for continuous-time within-play valuation of game outcomes in american football with tracking data. _Journal of Quantitative Analysis in Sports_ , 16(2):163–182. 

- Yurko, R., Ventura, S., and Horowitz, M. (2019). nflwar: a reproducible method for offensive player evaluation in football. _Journal of Quantitative Analysis in Sports_ , 15(3):163– 183. 

### **SUPPLEMENTARY MATERIAL** 

## **A Our code** 

The code for this study is publicly available on GitHub at `https://github.com/snoopryan123/ fourth_down` in the folder `1` ~~`s`~~ `imulation/sim` ~~`v`~~ `3` . 

22
