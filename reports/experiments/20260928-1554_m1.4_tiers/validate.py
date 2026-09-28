"""M1.4 checks on the seeded sample (F-01, F-03): coverage, tier missingness (A-12), exclusion by tier (A-40).
Match-level bootstrap, seed 20260928."""
import json, sys
import numpy as np, pandas as pd
rng = np.random.default_rng(20260928)
def ci(x, B=2000):
    x = np.asarray(x, float); b = [x[rng.integers(0, len(x), len(x))].mean() for _ in range(B)]
    return [round(float(x.mean()), 4), round(float(np.quantile(b, .025)), 4), round(float(np.quantile(b, .975)), 4), int(len(x))]
t = pd.read_parquet('/media/jan/merged/cs2coach/manifest/match_tiers.parquet')
q = pd.read_parquet('/media/jan/merged/cs2coach/manifest/match_quality.parquet')[['match_id', 'final_state', 'q_abandonment']]
f = t[(t['format'] == '5v5') & t['in_seeded_sample'].fillna(False).astype(bool)].merge(q, on='match_id')
f['missing'] = f['tier'].isna()
out = {
    'scope': 'canonical 5v5, seeded sample',
    'n': int(len(f)),
    'coverage_by_platform': {k: g['tier'].fillna('null').value_counts().to_dict() for k, g in f.groupby('platform')},
    'tier_share_of_labelled_by_source': {k: g['tier'].value_counts(normalize=True).round(3).to_dict() for k, g in f[f['tier'].notna()].groupby('tier_source')},
    'a12_missing_by_source': {k: ci(g['missing']) for k, g in f.groupby('tier_source')},
    'a12_missing_by_channel_set': {k: ci(g['missing']) for k, g in f.groupby('channel_set')},
    'a12_missing_by_map': {k: ci(g['missing']) for k, g in f[f['map_name'].isin(f['map_name'].value_counts().head(7).index)].groupby('map_name')},
    'a12_spread_ge2_share_of_labelled': ci(f.loc[f['tier'].notna(), 'tier_spread'] >= 2),
    'a12_spread_ge2_by_source': {k: ci(g['tier_spread'] >= 2) for k, g in f[f['tier'].notna()].groupby('tier_source')},
    'a40_excluded_by_tier': {k: ci(~g['clean'].astype(bool)) for k, g in f.assign(tier=f['tier'].fillna('null')).groupby('tier')},
    'a40_incomplete_by_tier': {k: ci(g['final_state'] == 'incomplete') for k, g in f.assign(tier=f['tier'].fillna('null')).groupby('tier')},
}
json.dump(out, open(sys.argv[1], 'w'), indent=1); print(json.dumps(out, indent=1))
