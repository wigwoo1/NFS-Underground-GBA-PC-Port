"""Exact return intervals correlated to independently retained parent GC ledger."""
import json,sys,copy
from pathlib import Path
def analyze(raw,tail):
 assert raw['gc_trace_dropped']==0 and raw['gc_collection_samples']
 events=raw['gc_collection_samples'];seen=set()
 for e in events:
  key=(e['thread_id'],e['start_ns'],e['end_ns']);assert key not in seen;seen.add(key);assert e['start_ns']<=e['end_ns'] and e['thread_cpu_ns']>=0
 rows=[]
 for r in tail['rows']:
  x=r['return_execution'];v=x['native'];a=v[0];b=x['python_return_ns'];assert x['identity']==r['identity'] and a<=b
  if b-a<=10_000_000:continue
  overlap=[dict(generation=e['generation'],thread=e['thread_id'],gc_ms=(e['end_ns']-e['start_ns'])/1e6,gc_cpu_ms=e['thread_cpu_ns']/1e6,overlap_ms=(min(b,e['end_ns'])-max(a,e['start_ns']))/1e6,collected=e['collected']) for e in events if max(a,e['start_ns'])<min(b,e['end_ns'])]
  rows.append(dict(identity=r['identity'],return_ms=(b-a)/1e6,renderer_cpu_ms=(x['python_cpu_100ns']-v[2])/10000,renderer_cycles=x['python_cycles']-v[1],parent_gc_overlaps=overlap))
 return dict(result='PASS_RETURN_PARENT_GC_INTERVAL_CORRELATION',events=len(events),long_returns=len(rows),rows=rows,scope='Exact native/Python return intervals and zero-drop completed parent GC events. Overlap supports contention hypothesis, not exclusive causal proof; empty overlap does not exclude other GIL or OS scheduling work.')
if __name__=='__main__':
 raw=json.loads(Path(sys.argv[1]).read_text());tail=json.loads(Path(sys.argv[2]).read_text());out=analyze(raw,tail)
 bad=copy.deepcopy(raw);bad['gc_collection_samples'][0]['end_ns']=bad['gc_collection_samples'][0]['start_ns']-1
 try:analyze(bad,tail)
 except AssertionError:out['reverse_gc_negative_control']='PASS'
 else:raise AssertionError('Reversed GC accepted')
 Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(out)
