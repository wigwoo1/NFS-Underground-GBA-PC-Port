"""Measure logged swap-call timing and missing presentation slots, not scanout."""
from pathlib import Path
import csv,json,statistics
p=Path(__file__).resolve().parent
report=json.loads((p/'threaded-racing-motion-audit.json').read_text())
rows=list(csv.DictReader(Path(report['prefix']+'-worker.csv').open()))
commits=[r for r in rows if int(r['committed'])==1 and int(r['result'])==0]
assert len(commits)>1
rate=16777216/(280896*60)
slots=[round((float(r['target'])-int(r['source_base'])+8)/rate) for r in commits]
assert all(b>a for a,b in zip(slots,slots[1:])), 'Nonmonotonic presentation slots'
def summary(values):
 values=sorted(values)
 return dict(count=len(values),median_ms=statistics.median(values),p95_ms=values[int((len(values)-1)*.95)],max_ms=max(values))
gaps=[(int(b['commit_begin_ns'])-int(a['commit_begin_ns']))/1e6 for a,b in zip(commits,commits[1:])]
late=[max(0,int(r['commit_begin_ns'])-int(r['deadline_ns']))/1e6 for r in commits]
draw=[(int(r['draw_end_ns'])-int(r['start_ns']))/1e6 for r in commits]
missing=sum(b-a-1 for a,b in zip(slots,slots[1:]))
output=dict(result='PRESENTATION_GAPS_OBSERVED' if missing or max(gaps)>25 else 'LOGGED_PACING_ONLY',prefix=report['prefix'],readback_requested=report['complete_readback_requested'],committed_frames=len(commits),first_slot=slots[0],last_slot=slots[-1],missing_interior_slots=missing,slot_coverage=len(slots)/(slots[-1]-slots[0]+1),commit_intervals=summary(gaps),late_commit_begin=summary(late),worker_draw_duration=summary(draw),intervals_over_25ms=sum(g>25 for g in gaps),scope='Logged commit calls; readback_requested records whether image export was enabled. No physical scanout, fullscene fidelity or smooth60fps proof.')
(p/'presentation-pacing-audit.json').write_text(json.dumps(output,indent=2))
print(json.dumps(output,indent=2))

