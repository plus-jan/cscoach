# Forschungssynthese (Original, Deutsch)

> Quelle: vom Projektinhaber bereitgestellte Literatursynthese. Behalten als Referenz.
> Zahlen und Quellen sind **nicht verifiziert** — siehe `sources.yaml` und Task M0.2.
> Englische, umsetzungsorientierte Ableitungen stehen in `docs/specs/`.
>
> **Bekannte Fehler (geprüft gegen Volltexte, siehe `papers/*.md` → cscoach notes):**
> - Same-Player Verification (v2): Hauptergebnis AUC **0,926** (Amateure, 3.570 Demos) bzw. **0,956** (Profis); v1 meldete 0,931 (0,955 = ein einzelner Split). Korrelation mit Rang wird **nicht** untersucht; Datensatz ist **nicht** öffentlich.
> - Contextual xT: 19,2 % gilt nur für Ballübergänge; für die Torwahrscheinlichkeit (xT-Wert) nur ~0,4 % Verbesserung, ohne Konfidenzintervalle.
> - MLMove: <0,5 ms ist amortisiert (7–8 ms pro Anfrage); CS:GO-Profidaten auf de_dust2. X-Ego: nur de_mirage, Videodaten, Split nach Runden.
> - TAR²: „Shapley-Werte“ werden per Attention approximiert; Gutschriften sind nicht-negativ.
> - VALORANT: 21.229 (nicht 29.506) Runden genutzt; Evaluation nur auf 100 Runden, nur Accuracy.
> - CHAMP: Vorhersage **vor** dem Match (Matchmaking), nicht Echtzeit-WP; "Kill-Crushing" ist ein MOBA-Matchmaking-Maß, keine CS-Rang-Erkenntnis.
> - Coaching-Studie heißt *Understanding Game Coaching on Gig Platforms*; "Kaltstart" bezieht sich auf Kundengewinnung der Coaches.
> - Datenpolitik geändert: einzige Datenquelle ist das PureSkill.gg-CSDS-Korpus (ADR-0003); Demo-Parsing (demoparser2), X-Ego-, ESTA- und externe NavMesh-Daten werden nicht verwendet. Spieler sind im Korpus nicht über Matches hinweg verknüpfbar (ADR-0005).
> - "Andersen 2021" nicht auffindbar → ersetzt durch Brill, Yurko & Wyner (`brill_yurko_wp_difficulty`).

Die Entwicklung eines datengesteuerten Coachingsystems für Amateur- und Semi-Profi-Spieler in Counter-Strike 2 (CS2) erfordert eine präzise Orchestrierung von maschinellen Lernmodellen, strenger statistischer Validierung und der Verarbeitung von Telemetriedaten. Der Rahmen – Runden-Siegwahrscheinlichkeiten (Win Probability), Attribution von Erwartungswerten (Expected Value), Evaluierung von Duellen (Expected Kills) und wirtschaftliche Kontextualisierung – schließt die Lücke zwischen traditioneller Sportanalytik (z. B. _Expected Threat_ im Fußball) und den hochfrequenten, komplexen räumlichen Umgebungen taktischer Shooter.

## 1. Quellenmatrix

| Gruppe | Titel | Autoren | Jahr | Venue | Spiel | Daten | Methode | Kernbefund | Fragen | Code | Peer-rev. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | Same-Player Verification for Account Consistency in CS2 | Anonym | 2026 | arXiv 2608.24893 | CS2 | 1.330 Demos, 13.300 Beob. (Tier C bis Diamond) | LightGBM, XGBoost, Transformer-Embeddings | ROC AUC 0,955 | A, C | Nein | Nein |
| B | Round Outcome Prediction in VALORANT Using Tactical Features from Video Analysis | Hayakawa et al. | 2025 | IEEE CoG (arXiv 2510.17199) | VALORANT | 1.376 Videos, 29.506 Runden (Pro) | TimeSformer auf Minimap | 80,55 % ab Rundenmitte vs. 72,28 % | B, G | Nein | Ja |
| B | CHAMP: Cross-domain Hybrid Architecture for Matchmaking | Wang et al. | 2026 | arXiv 2609.04870 | LoL | Multimodale MOBA-Daten | Hybride Domänen-Features, DAKE-Encoder | "Kill-Crushing"-Rate −20,73 % in niedrigen Tiers | B, C | Nein | Nein |
| C | The Gig Economy of Esports Coaching | Anonym | 2026 | arXiv 2609.12695 | Diverse | Qualitative Interviews | Situierte Interpretationsanalyse | Wert durch kontextuelle Interpretation | C, I | Nein | Nein |
| D | PandaSkill | De Bois et al. | 2025 | arXiv 2501.10049 | LoL | 5 Jahre Profi-Matches | ML → Perzentile, OpenSkill | Rollen-Einfluss vom Team-Sieg entkoppelt | D | Ja | Nein |
| D | Contextual Expected Threat (xT) using Spatial Event Data | Everett et al. | 2022 | StatsBomb | Fußball | StatsBomb 360 | CNN über Raster | −19,2 % Log-Loss | D, G | Nein | Ja |
| D | TAR2: Joint Temporal and Agent Credit Assignment | Anonym | 2025 | arXiv 2502.04864 | Multi-Agent | Sparse Reward | Duale Transformer, Shapley | Verzögerte Belohnung verteilt | D | Nein | Nein |
| E | xK analysis / Deep Dive into Budapest Major | bradac3k | 2024 (sic) | Reddit | CS2 | BLAST Bounty, Budapest Major 2025 | ML, 20+ Variablen | AK-47 +6,67 xK/Spiel; MP9 −1,87 | E | Nein | Nein |
| F | HLTV Rating 3.0 CS2 Update Analysis | SkinClub | 2025 | Artikel | CS2 | MM + Pro | "Round Swing", Eco-Anpassung | Entry im 5v5 ≈ +20 %; 1v2 Clutch bis 50 % | D, F | Nein | Nein |
| G | Learning to Move Like Professional Counter-Strike Players | Durst et al. | 2024 | ACM SIGGRAPH (arXiv 2408.13934) | CS:GO | 123 h Pro | Transformer Behavioral Cloning | <0,5 ms/Schritt; 16–59 % höherer TrueSkill | G, I | Ja | Ja |
| G | X-Ego | Anonym | 2025 | arXiv 2510.19150 | CS2 | 124 h, 45 Pro-Spiele (Mirage) | Cross-egozentrisches kontrastives Lernen | Zustand-Aktions-Trajektorien | G, J | Ja | Nein |
| H | Meta-Analytics | Franks et al. | 2016 | JQAS | NBA/NHL/Fußball | Event-Daten | Stabilität, Diskriminierung, Unabhängigkeit | r = 0,70 (Offensivzone ↔ Punkte) | H | Nein | Ja |
| I | Play Like Champions: Counterfactual Feedback Generation in Latent Space | Anonym | 2026 | arXiv 2607.00190 | StarCraft II | 23.476 Replays | VAE, Optimal Transport, Flow Matching | Algorithmischer Recourse | I | Nein | Nein |
| J | PureSkill.gg Competitive CS2 Gameplay Data Set | PureSkill | 2023 | AWS/Kaggle | CS2 | ~1.300 Spiele (Amateur) | Telemetrie | Skill-gelabelte Runden | J | Ja | Nein |
| J | Demoparser2 | LaihoE | 2023 | GitHub | CS2 | alle .dem | Rust + Python/Node Bindings | 4,6 GB in 6,14 s (12 Kerne) | J | Ja | Nein |

## 2. Synthese der Forschungsfragen

### A. Siegwahrscheinlichkeit in Counter-Strike
**Beantwortet:** In-Game-WP aus Telemetrie ist fortgeschritten. Klassisch: logistische Regression auf Überlebende und HP. Modern: XGBoost/LightGBM und MLPs, aktualisiert pro Tick/Event.
**Teilweise:** Räumliche Topologie (GNNs an Choke Points) ist rechenintensiv; aufgenommene Waffen (z. B. AWP im 1v2) sind in flachen Vektoren schwer darstellbar.
**Lücke:** Neukalibrierung auf Amateur-/Semi-Pro-Niveau. Profimodelle überschätzen z. B. 5v4-Vorteile in niedrigen Rängen (schlechte Positionierung, fehlende Trades). **Separate, tier-kalibrierte Baselines sind Pflicht**, sonst ist WPA-Feedback ungültig.

### B. Siegwahrscheinlichkeit in anderen Shootern / E-Sports
**Beantwortet:** VALORANT-TimeSformer auf Minimap + taktischen Events: 80,55 % ab Rundenmitte. CHAMP (LoL) nutzt modusübergreifende Sequenzen gegen Cold-Start.
**Teilweise:** MOBA-Ökonomie (kontinuierlich) schwer übertragbar auf rundenbasierte CS-Ökonomie mit Resets/Verlustbonus; VALORANT-Fähigkeiten deterministischer als CS2-Smokes.
**Lücke:** Domänenübergreifendes Transfer-Learning. CHAMP als Blaupause: MM-Daten nutzen, um Cold-Start bei FACEIT zu vermeiden.

### C. Unterschiede zwischen Skill-Tiers
**Beantwortet:** Tiers trennbar über mikro-mechanische Fingerabdrücke (Fadenkreuzkontrolle, Schussrhythmus, Bewegung-Stopp-Schuss); AUC 0,955 für Spielerverifikation; korreliert mit Rang.
**Teilweise:** Spieler suchen Coaches wegen "situierter Interpretation", nicht Dashboards. Hohe "Kill-Crushing"-Rate in niedrigen Rängen.
**Lücke:** Quantifizierung des "Chaos-Faktors". Feature Importance verschiebt sich: niedrige Ränge → Counter-Strafing hat überproportionale Vorhersagekraft; hohe Ränge → Verlust eines Utility-Trägers.

### D. Bewertung von Aktionen / Credit Assignment
**Beantwortet:** xT (Fußball) → "Round Swing" (HLTV 3.0): Entry-Kill im 5v5 ≈ +20 %, isolierter Kill im 1v5 < 0,1 %. PandaSkill: Perzentil-Transformation, rollenbasiert, vom Teamsieg entkoppelt.
**Teilweise:** MARL-Credit (TAR2, Shapley) komplex; nicht-tödliche, verzögerte Beiträge in HLTV 3.0 vereinfacht.
**Lücke:** "Spatial Credit" – passiver Raumgewinn (Winkel halten, Rotationen verhindern). DxT (off-ball) auf CS2 übertragen; Beitrag via WP-Delta + Shapley isolieren.

### E. Duell-Modellierung (xK)
**Beantwortet:** xK mit 20+ Pre-Shot-Variablen (Waffen-Matchup, Flick-Winkel, Geschwindigkeit, Distanz). Trennt Entscheidungsqualität von Ausführung.
**Teilweise:** Reaktionszeit/Crosshair-Placement extrahierbar; Latenz/Peeker's Advantage in Demos geglättet.
**Lücke:** Notwendigkeit des Duells. **xK × WPA kreuzen**: Duell mit xK 0,20 in Post-Plant-Situation mit 95 % WP bei Überleben ist schlecht – egal ob gewonnen.

### F. Wirtschaft
**Beantwortet:** HLTV 3.0 passt Kill-Wert an Waffendifferenz an (Eco-Farming ≈ wertlos; SMG vs. Full-Buy belohnt).
**Teilweise:** "Optimal Spending Error" (OSE) ignoriert Hero-Buys.
**Lücke:** Team-Synchronisation der Ökonomie messen; kontrafaktische Empfehlung: "Runde 7 $2.000 gekauft während Team sparte; bei Save hätte Runde 8 WP 48 % statt 22 %."

### G. Räumliche Analysen
**Beantwortet:** X-Ego-CS (egozentrisch + globale Koordinaten), MLMove (NavMesh, Behavioral Cloning, <0,5 ms/Schritt), Spatial xT (−19,2 % Log-Loss).
**Teilweise:** Utility wird meist post-hoc bewertet; Smokes verändern aber die Topologie.
**Lücke:** NavMesh + Spatial xT fusionieren: Kürzeste Wege vor/nach Utility → Sekunden Verzögerung → WPA für den Werfer.

### H. Statistische Validität
**Beantwortet:** Franks et al.: Stabilität, Diskriminierung, Unabhängigkeit.
**Teilweise:** Kalibrierung bei geclusterten Ergebnissen (Brill & Yurko): Zustände einer Runde teilen ein Ergebnis → Konfidenzintervalle zu eng. ESS via Intracluster-Korrelation reduzieren.
**Lücke:** Stabilität von WPA/xK für Amateure überwachen; hierarchische Bayes-Glättung, ESS-angepasste Reliability Curves – sonst hyperreaktives Feedback aus Rauschen.

### I. Coaching und Skill-Entwicklung
**Beantwortet:** Werkzeuge liefern Wahrheit, Vermittlung braucht situierte Interpretation. Kontrafaktische Szenarien im latenten Raum (SC2; KL-Divergenz, EMD) → minimaler Veränderungsaufwand.
**Teilweise:** WP-Verlaufsdiagramme sind deskriptiv, nicht präskriptiv.
**Lücke:** WPA/xK-Defizite in **algorithmischen Recourse** übersetzen ("Smoke 8 s länger halten → +14 % WP"); Validierung per RCT.

### J. Datensätze und Werkzeuge
**Beantwortet:** demoparser2 (Rust) → Tick-Daten als DataFrames; 4,6 GB in 6,14 s.
**Teilweise:** PureSkill.gg mit Rang-Labels.
**Lücke:** Kohärente Pipeline: `.dem` → demoparser2 → NavMesh-Kontrolle → xK → WPA-Zeitreihe → Dashboard nach Match-Ende.

## 3. Top-10 Pflichtlektüre
1. HLTV Rating 3.0 (Round Swing, Eco-Anpassung)
2. Contextual xT (Everett et al., 2022)
3. demoparser2
4. Meta-Analytics (Franks et al., 2016)
5. Play Like Champions (2026)
6. xK Budapest Major (bradac3k)
7. Dynamic Expected Threat (Hassani et al., 2025)
8. Same-Player Verification CS2 (2026)
9. Effective Sample Size in clustered outcomes (Andersen, 2021)
10. PandaSkill (De Bois et al., 2025)

## 4. Datensätze mit Skill-Labels
- **PureSkill.gg CS2** – >1.300 Amateur/MM-Spiele (Zielgruppe).
- **X-Ego-CS** – 124 h, 45 Profispiele, Mirage; Trajektorien.
- **Perfect World Arena Consistency Dataset** – 1.330 Demos, 12 Amateur-Tiers (C bis Diamond S).

## Fazit
Paradigmenwechsel von deskriptiver zu prädiktiver und kontrafaktischer Modellierung: WPA-Framework mit NavMesh-Topologie, Granateneffekten, wirtschaftlich justiertem xK; rigorose Kalibrierung mit ESS-Korrektur für Clustering; kontrafaktisches, umsetzbares Feedback.
