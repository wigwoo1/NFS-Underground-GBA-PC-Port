"""Owned HUD API intervals within complete-scene rendering, not GPU timestamps."""
from pathlib import Path
import csv, json, statistics, sys

p=Path(__file__).resolve().parent
report=json.loads(Path(sys.argv[1] if len(sys.argv)>1 else p/'threaded-racing-motion-audit.json').read_text())
rows=list(csv.DictReader(Path(report['prefix']+'-components.csv').open()))
owned=[r for r in rows if r['kind'] in ('4','5','6')]
assert owned and all(int(r['hud_calls'])==1 for r in owned)
total=[(int(r['end_ns'])-int(r['begin_ns']))/1e6 for r in owned]
hud=[float(r['hud_wall_ms']) for r in owned]
prepare=[float(r['hud_prepare_ms']) for r in owned]
finish=[float(r['finish_wall_ms']) for r in owned]
# Ordered split submissions render both page bundles; stable/motion render one.
assert all(int(r['finish_calls'])==(2 if r['kind']=='4' else 1) for r in owned)
assert all(0<=h+f<=t+.01 for t,h,f in zip(total,hud,finish))
assert all(0<=b<=a+.01 for a,b in zip(total,hud))
assert all(0<=b<=a+.01 for a,b in zip(hud,prepare))
def summary(values):
    v=sorted(values)
    return dict(count=len(v),sum_ms=sum(v),median_ms=statistics.median(v),
                p95_ms=v[int((len(v)-1)*.95)],max_ms=max(v))
output=dict(result='OWNED_RENDER_COMPONENT_INTERVALS',prefix=report['prefix'],
            complete_render=summary(total),owned_hud=summary(hud),hud_candidates=summary(prepare),
            outside_hud=summary([a-b for a,b in zip(total,hud)]),
            hud_other_api_work=summary([a-b for a,b in zip(hud,prepare)]),
            finish_api=summary(finish),outside_hud_and_finish=summary([t-h-f for t,h,f in zip(total,hud,finish)]),
            async_finish=sorted(set(int(r['async_finish']) for r in owned)),
            scope='CPU wall intervals before repeat readbacks. Complete render includes ownership validation, world/model rendering, finish and HUD. Outside HUD includes all other work. HUD includes 4K background copy, candidates, texture upload and composition. GPU calls can block or defer execution; no GPU completion, scanout or 60fps proof. Previous stages CSV complete-scene entry called aggregate work scene and recorded zero HUD, so cannot localize HUD cost.')
Path(report['prefix']+'-owned-components.json').write_text(json.dumps(output,indent=2))
print(json.dumps(output,indent=2))
