"""Correlate missing display slots with producer tick and extraction intervals."""
from pathlib import Path
import csv,json,sys,statistics
p=Path(sys.argv[1]);read=lambda k:list(csv.DictReader(Path(str(p)+'-'+k+'.csv').open()))
w=[r for r in read('worker') if int(r['committed'])==1 and int(r['result'])==0];ticks=read('input');producer=read('producer')
assert len(w)>1 and ticks
attempt_path=Path(str(p)+"-attempts.csv")
attempts=read("attempts") if attempt_path.exists() else None
if attempts is not None:
 assert len(producer)==sum(int(r["outcome"])!=0 for r in attempts)
 assert sum(int(r["pushed"]) for r in producer)==sum(int(r["outcome"])==2 for r in attempts)
 assert all(int(r["outcome"]) in (0,1,2) for r in attempts)
captures=attempts if attempts is not None else producer
capture_end="end_ns" if attempts is not None else "push_end_ns"
clip=lambda rows,start,end,lo,hi:sum(max(0,min(hi,int(r[end]))-max(lo,int(r[start]))) for r in rows)/1e6
intervals=sorted([(int(r['start_ns']),int(r['end_ns'])) for r in ticks]+[(int(r['begin_ns']),int(r[capture_end])) for r in captures])
assert all(b>=a for a,b in intervals)
assert all(a[1]<=b[0] for a,b in zip(intervals,intervals[1:])), 'Producer tick/capture intervals overlap; cannot add their wall coverage'
rate=16777216/(280896*60)
def slot(r):
 v=(float(r['target'])-int(r['source_base'])+8)/rate;assert abs(v-round(v))<1e-7;return round(v)
gaps=[]
for a,b in zip(w,w[1:]):
 missing=slot(b)-slot(a)-1;assert missing>=0
 if not missing:continue
 lo,hi=int(a['commit_begin_ns']),int(b['commit_begin_ns']);assert hi>lo
 overlapping=[r for r in ticks if int(r['start_ns'])<hi and int(r['end_ns'])>lo]
 debt=[max(0,(int(r['end_ns'])-int(a['clock_origin']))*16777216//(1000000000*280896)-(int(r['after'])-int(a['source_base']))) for r in overlapping]
 gaps.append(dict(begin_ns=lo,end_ns=hi,missing_slots=missing,gap_ms=(hi-lo)/1e6,original_tick_ms=clip(ticks,'start_ns','end_ns',lo,hi),capture_extract_ms=clip(producer,'begin_ns','extract_end_ns',lo,hi),capture_total_ms=clip(captures,'begin_ns',capture_end,lo,hi),unavailable_capture_ms=clip([r for r in attempts if int(r['outcome'])==0],'begin_ns','end_ns',lo,hi) if attempts is not None else None,successful_pushes=sum(lo<=int(r['push_end_ns'])<hi and int(r['pushed'])==1 for r in producer),overlapping_updates=len(overlapping),max_original_backlog=max(debt,default=0)))
assert gaps
cpu_path=Path(str(p)+'-producer-cpu.csv')
if cpu_path.exists():
 cpu_rows=list(csv.DictReader(cpu_path.open()))
 for gap in gaps:
  lo,hi=gap['begin_ns'],gap['end_ns']
  for kind in ('original_tick','submission'):
   overlapping=[r for r in cpu_rows if r['kind']==kind and int(r['begin_ns'])<hi and int(r['end_ns'])>lo]
   assert all(int(r['valid'])==1 and int(r['cpu_end_ns'])>=int(r['cpu_begin_ns']) for r in overlapping)
   gap[kind+'_full_overlapping_cpu_ms']=sum(int(r['cpu_end_ns'])-int(r['cpu_begin_ns']) for r in overlapping)/1e6
   gap[kind+'_full_overlapping_wall_ms']=sum(int(r['end_ns'])-int(r['begin_ns']) for r in overlapping)/1e6
out=dict(result='PRESENTATION_PRODUCER_GAP_CORRELATION',prefix=str(p),commits=len(w),complete_attempt_coverage=attempts is not None,attempts=len(captures),missing_slots=sum(r['missing_slots'] for r in gaps),gap_count=len(gaps),gap_tick_ms=sum(r['original_tick_ms'] for r in gaps),gap_capture_ms=sum(r['capture_total_ms'] for r in gaps),gap_ms=sum(r['gap_ms'] for r in gaps),producer_covered_fraction=sum(r['original_tick_ms']+r['capture_total_ms'] for r in gaps)/sum(r['gap_ms'] for r in gaps),longest_gaps=sorted(gaps,key=lambda r:r['gap_ms'],reverse=True)[:10],scope='Clipped producer tick and capture wall intervals; all attempts included only when complete_attempt_coverage is true. Extraction phase still successful owners only. Correlation, not CPU/GPU causality or scanout proof.')
Path(str(p)+'-gap-correlation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

