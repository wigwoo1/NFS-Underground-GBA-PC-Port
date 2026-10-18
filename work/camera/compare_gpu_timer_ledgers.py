import csv,json
from pathlib import Path
p=Path('work/camera');a=p/'prototype-runs/racing-motion-audit-585020b371e94817a7405da6c1de93a4';b=p/'prototype-runs/racing-motion-audit-04324915e7eb4c498cd26479a69b2726'
read=lambda x,s:list(csv.DictReader(Path(str(x)+s).open()))
ai,bi=read(a,'-input.csv'),read(b,'-input.csv');assert len(ai)==len(bi)==756
for x,y in zip(ai,bi):assert all(x[k]==y[k] for k in ('index','keys','before','after'))
r=dict(result='SYNC_ASYNC_ORIGINAL_LEDGER_EXACT',updates=756,sync_prefix=str(a),async_prefix=str(b),scope='Same original input/update ledger; independent live runs, scheduling uncontrolled, no causal speedup proof.')
(p/'gpu-sync-async-ledger.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
