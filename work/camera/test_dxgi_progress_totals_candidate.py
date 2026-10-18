import json
from pathlib import Path
from owned_dxgi_progress_totals_candidate import DisplayProgressTotals
x=DisplayProgressTotals()
def stats(p,r):return [0,0,p+3,p,r,r,r*166667,0,10000000]
x.observe((1,1),stats(10,100));x.observe((1,1),stats(10,100));x.observe((1,1),stats(11,102));assert x.repeated==1 and x.advances==1 and x.multi_refresh_single_image==1
x.observe((1,2),stats(12,110));assert x.discontinuities==1 and x.refreshes==2
x.observe((1,2),[2289696779,0,13,0,0,0,0,0,10000000]);assert x.unavailable==1 and x.previous is None
x.observe((1,2),stats(14,113));assert x.advances==1
Path('work/camera/prototype-runs/dxgi-progress-guards-20261008.json').write_text(json.dumps(dict(result='PASS',stats=x.stats(),scope='Synthetic repeat/generation/disjoint handling.'),indent=2));print('PASS DXGI repeat/discontinuity guards')
