"""Whole child preparation CPU/elapsed correlation; scheduling cause remains unknown."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());requests=r['world_preparation_stage_samples'];events=[];seen=set();stages=[];cycle_owners={};cycle_enabled=[]
for request in requests:
 c=request['terminal'][5];assert c['cpu_trace'] is True
 cycle_enabled.append(c.get('cycle_trace',False))
 if c.get('cycle_trace'):
  owner=(c['pid'],c['cycle_thread']);assert all(isinstance(v,int) and v>0 for v in owner)
  assert c['pid'] not in cycle_owners or cycle_owners[c['pid']]==c['cycle_thread'];cycle_owners[c['pid']]=c['cycle_thread']
 g=c['child_gc_trace'];assert g['dropped']==0
 for e in g['rows']:
  key=(e['thread'],e['generation'],e['start_ns'],e['end_ns']);assert key not in seen;seen.add(key);events.append(e)
 def add(name,a,b,cpu):
  assert a is not None and b is not None and cpu is not None and b>=a and cpu>=0
  wall=b-a
  stages.append({'older':request['older'],'newer':request['newer'],'generation':request['generation'] if 'generation' in request else None,'stage':name,'begin_ns':a,'end_ns':b,'wall_ms':wall/1e6,'cpu_ms':cpu/1e6,'elapsed_minus_cpu_ms':(wall-cpu)/1e6})
 if c['constructed_ns'] is not None:
  add('world_construct',c['initialized_ns'],c['constructed_ns'],c['constructed_cpu_ns']-c['initialized_cpu_ns'])
  if c.get('cycle_trace'):
   cycles=c['world_construct_thread_cycles'];assert isinstance(cycles,int) and cycles>=0;stages[-1]['thread_cycles']=cycles
 for sample in c['sample_transfer_rows']:
  if c.get('cycle_trace'):assert isinstance(sample['prepare_thread_cycles'],int) and sample['prepare_thread_cycles']>=0
  if sample['index']==0:
   add('source_setup_first_sample',sample['ready_ns']-sample['prepare_since_ack_ns'],sample['ready_ns'],sample['prepare_cpu_ns'])
   if c.get('cycle_trace'):stages[-1]['thread_cycles']=sample['prepare_thread_cycles']
for stage in stages:
 a,b=stage['begin_ns'],stage['end_ns'];stage['gc_overlaps']=[{'generation':e['generation'],'duration_ms':(e['end_ns']-e['start_ns'])/1e6,'overlap_ms':(min(b,e['end_ns'])-max(a,e['start_ns']))/1e6} for e in events if max(a,e['start_ns'])<min(b,e['end_ns'])]
assert stages
cpu_ns=[round(stage['cpu_ms']*1e6) for stage in stages];quantum=15625000
coarse=all(value%quantum==0 for value in cpu_ns)
quantization={'all_cpu_deltas_multiple_of_15_625_ms':coarse,'zero_cpu_stages':sum(value==0 for value in cpu_ns),'cpu_exceeds_elapsed_stages':sum(stage['cpu_ms']>stage['wall_ms'] for stage in stages),'interpretation':'Observed coarse CPU counters prevent reliable individual-stage elapsed-minus-CPU attribution. Thread-cycle evidence required.' if coarse else 'No fixed15.625ms quantum established; timer/scheduling limitations still apply.'}
out={'result':'MEASURED_COMPLETE_CHILD_CPU_ELAPSED_CORRELATION','thread_cycle_trace_all_requests':all(cycle_enabled),'cycle_worker_threads':cycle_owners,'cpu_counter_quantization':quantization,'requests':len(requests),'stages':len(stages),'unique_gc_events':len(events),'largest_wall_stages':sorted(stages,key=lambda s:s['wall_ms'],reverse=True),'largest_elapsed_minus_cpu_stages':sorted(stages,key=lambda s:s['elapsed_minus_cpu_ms'],reverse=True),'scope':'All retained request world construction and first sample intervals with enabled child CPU counters and unique no-drop GC events. Elapsed-minus-CPU includes scheduling, waits, timer quantization and instrumentation; not exclusive cause, not optimization benefit or visible60 proof.'}
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],len(requests),'requests',len(stages),'stages');print(json.dumps(out['largest_wall_stages'][:4],indent=2))
