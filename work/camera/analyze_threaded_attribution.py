"""Join producer gaps/late renders to recorded original tick deadlines."""
import csv,hashlib,json,math,sys
from pathlib import Path
manifest=Path(sys.argv[1]);m=json.loads(manifest.read_text(encoding='utf-8-sig'));prefix=m['prefix'];assert not m.get('window_lifecycle')
def rows(suffix):return list(csv.DictReader(Path(prefix+suffix).open()))
workers=[r for r in rows('-worker.csv') if int(r['committed'])];producers=[r for r in rows('-producer.csv') if int(r['pushed'])];inputs=rows('-input.csv');origin=int(workers[0]['clock_origin']);base=int(workers[0]['source_base']);assert all(int(r['clock_origin'])==origin and int(r['source_base'])==base for r in workers)
ticks=[]
for r in inputs:
 index=int(r['index']);
 if index<40:continue
 due=origin+((index-39)*280896*1000000000+16777216-1)//16777216
 ticks.append(dict(index=index,before=int(r['before']),after=int(r['after']),start=int(r['start_ns']),end=int(r['end_ns']),due=due,start_delay_ms=(int(r['start_ns'])-due)/1e6,execution_ms=(int(r['end_ns'])-int(r['start_ns']))/1e6))
assert all(t['after']-t['before']==1 for t in ticks)
def window(lo,hi):
 selected=[t for t in ticks if t['start']<hi and t['end']>lo]
 return dict(original_ticks=[dict(index=t['index'],before=t['before'],after=t['after'],start_delay_ms=t['start_delay_ms'],execution_ms=t['execution_ms']) for t in selected],tick_overlap_ms=sum(max(0,min(t['end'],hi)-max(t['start'],lo)) for t in selected)/1e6)
gaps=[]
for a,b in zip(producers,producers[1:]):
 def slot(r):return round((float(r['target'])-base+8)*280896*60/16777216)
 previous,current=slot(a),slot(b)
 if current==previous+1:continue
 assert current>previous+1;lo=int(a['begin_ns']);hi=int(b['begin_ns']);spans=[r for r in producers if int(r['begin_ns'])<hi and int(r['push_end_ns'])>lo];extraction=sum(max(0,min(int(r['extract_end_ns']),hi)-max(int(r['begin_ns']),lo)) for r in spans)/1e6;copy=sum(max(0,min(int(r['copy_end_ns']),hi)-max(int(r['extract_end_ns']),lo)) for r in spans)/1e6;tick=window(lo,hi)
 gaps.append(dict(previous_slot=previous,current_slot=current,missing=current-previous-1,from_target=float(a['target']),to_target=float(b['target']),producer_begin_gap_ms=(hi-lo)/1e6,extraction_overlap_ms=extraction,copy_overlap_ms=copy,unattributed_wall_ms=(hi-lo)/1e6-extraction-copy-tick['tick_overlap_ms'],**tick))
late=[];lookup={(r['epoch'],r['target']):r for r in producers}
for w in workers:
 if int(w['draw_end_ns'])<=int(w['deadline_ns']):continue
 r=lookup[w['epoch'],w['target']];lo=int(r['begin_ns'])-40000000;hi=int(r['push_end_ns']);late.append(dict(target=float(w['target']),ready_margin_ms=(int(w['deadline_ns'])-hi)/1e6,render_ms=(int(w['draw_end_ns'])-int(w['start_ns']))/1e6,**window(lo,hi)))
out=Path(prefix+'-timing-attribution.json');out.write_text(json.dumps(dict(result='JOINED',manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),ledger_sha256={suffix:hashlib.sha256(Path(prefix+suffix).read_bytes()).hexdigest() for suffix in ['-input.csv','-producer.csv','-worker.csv']},gaps=gaps,late_frames=late,maximum_tick_start_delay_ms=max(t['start_delay_ms'] for t in ticks),scope='CPU wall-clock interval attribution using original tick due times and actual execution intervals. Unattributed time includes waits, logging, dispatch, copies outside recorded span and OS scheduling; cannot label it CPU idle or infer OS causality. No game logic rate changes or scanout proof.'),indent=2));print(json.dumps(dict(report=str(out),gaps=gaps,late_count=len(late))))
