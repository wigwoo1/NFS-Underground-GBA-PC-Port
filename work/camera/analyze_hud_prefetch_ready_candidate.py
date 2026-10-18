import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());api=r['bounded_diagnostic_stats']['whole_run_api_intervals'];ledger=api['long_intervals'];assert ledger['dropped']==0 and ledger['total']==api['over_33_333ms']==len(ledger['records'])
def analyze(rows):
 transfers=[x for x in rows if x is not None]
 for x in transfers:
  assert x['submitted_ns']<=x['started_ns']<=x['completed_ns']<=x['take_end_ns']
  assert x['take_begin_ns']<=x['take_end_ns']
  if x['ready_before_take']:assert x['completed_ns']<=x['take_begin_ns']
 return dict(transfers=len(transfers),ready_before_take=sum(x['ready_before_take'] for x in transfers),waited=sum(not x['ready_before_take'] for x in transfers),median_take_ms=statistics.median((x['take_end_ns']-x['take_begin_ns'])/1e6 for x in transfers) if transfers else None,median_create_ms=statistics.median((x['completed_ns']-x['started_ns'])/1e6 for x in transfers) if transfers else None)
retained=[(x.get('prepared') or {}).get('hud_transfer') for x in r['presentation_samples']]
long=[x.get('hud_transfer') for x in ledger['records']]
out=dict(result='HUD_PREFETCH_READINESS_ACCOUNTED',retained_last_window=analyze(retained),complete_long_intervals=analyze(long),long_interval_count=len(long),scope='Last retained120 presentation rows and complete bounded longinterval ledger separately; not whole-run transfer distribution. Actual Future readiness at take, ordered worker stamps, no causal performance/scanout claim.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
