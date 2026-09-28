import logging, structlog, pandas as pd, numpy as np, json, sys
from concurrent.futures import ProcessPoolExecutor
def seq(key):
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING))
    from pureskillgg_dsdk.ds_io import DsReaderFs, GameDsLoader
    re_=GameDsLoader(reader=DsReaderFs(root_path='/media/jan/merged/cs2coach', manifest_key=key)).get_channels([{"channel":"round_end","columns":["round","tick","win_reason_code"]}])['round_end']
    return key, tuple(zip(re_['round'], re_['tick'], re_['win_reason_code']))
if __name__=='__main__':
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING))
    from pureskillgg_dsdk.tome import TomeCuratorFs
    q=pd.read_parquet('/media/jan/merged/cs2coach/manifest/match_quality.parquet')
    h=TomeCuratorFs(ds_type="csds", tome_collection_root_path="/media/jan/merged/cs2coach/tomes", ds_collection_root_path="/", default_header_name="h").get_dataframe("header.2025-09-01,2026-09-28.full")
    q=q.merge(h[['match_id','key']],on='match_id')
    # A-36: groups with >=2 full-channel copies
    full=q[q.complete.fillna(False).astype(bool)]
    g=full.groupby('dedup_key').filter(lambda d: len(d)>=2)
    with ProcessPoolExecutor(12) as p: s=dict(p.map(seq, g.key, chunksize=8))
    g=g.assign(seq=g.key.map(s))
    same=g.groupby('dedup_key').seq.agg(lambda x: len(set(x))==1)
    out={'a36_groups_checked': int(len(same)), 'a36_groups_identical_round_end': int(same.sum())}
    # A-40: exclusion rate by platform and map among canonical 5v5 (match-level bootstrap)
    c=q[q.is_canonical & (q.format=='5v5')].copy(); c['excluded']=~c.clean
    rng=np.random.default_rng(20260928)
    def ci(x,B=2000):
        x=x.to_numpy().astype(float); b=[x[rng.integers(0,len(x),len(x))].mean() for _ in range(B)]
        return [round(x.mean(),4), round(float(np.quantile(b,.025)),4), round(float(np.quantile(b,.975)),4), int(len(x))]
    out['a40_overall']=ci(c.excluded)
    out['a40_by_platform']={k:ci(v.excluded) for k,v in c.groupby('platform')}
    top=c.map_name.value_counts().head(9).index
    out['a40_by_map']={k:ci(v.excluded) for k,v in c[c.map_name.isin(top)].groupby('map_name')}
    out['a40_by_reason']={k:int(c[k].fillna(False).astype(bool).sum()) for k in ['q_platform_unknown','q_player_count','q_incomplete','q_rounds_vs_score']}
    json.dump(out, open(sys.argv[1],'w'), indent=1); print(json.dumps(out, indent=1))
