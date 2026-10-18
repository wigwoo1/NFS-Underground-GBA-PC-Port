"""Correlate the longest commit gap with original updates and producer activity."""
from pathlib import Path
import csv,json
p=Path(__file__).resolve().parent
r=json.loads((p/'threaded-racing-motion-audit.json').read_text());prefix=r['prefix']
def rows(kind):return list(csv.DictReader(Path(prefix+'-'+kind+'.csv').open()))
w=[x for x in rows('worker') if int(x['committed'])==1]
a,b=max(zip(w,w[1:]),key=lambda pair:int(pair[1]['commit_begin_ns'])-int(pair[0]['commit_begin_ns']))
lo,hi=int(a['commit_begin_ns']),int(b['commit_begin_ns'])
ticks=[x for x in rows('input') if lo<=int(x['start_ns'])<hi]
producer=[x for x in rows('producer') if lo<=int(x['begin_ns'])<hi]
busy=sum(max(0,min(hi,int(x['end_ns']))-max(lo,int(x['start_ns']))) for x in rows('input'))
origin=int(a['clock_origin']);base=int(a['source_base'])
backlogs=[max(0,((int(x['end_ns'])-origin)*16777216//(1000000000*280896))-(int(x['after'])-base)) for x in ticks]
out=dict(max_original_update_backlog=max(backlogs,default=0),ticks_ending_behind=sum(x>0 for x in backlogs),result='LONGEST_GAP_CORRELATION',prefix=prefix,gap_ms=(hi-lo)/1e6,targets=[float(a['target']),float(b['target'])],original_updates_in_gap=len(ticks),original_update_indices=[int(ticks[0]['index']),int(ticks[-1]['index'])] if ticks else [],original_tick_wall_ms=busy/1e6,producer_attempts_in_gap=len(producer),successful_pushes_in_gap=sum(int(x['pushed'])==1 for x in producer),scope='Correlation only; skipped display plans are not individually logged. No causal CPU/scheduler proof.')
(p/'presentation-starvation-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

