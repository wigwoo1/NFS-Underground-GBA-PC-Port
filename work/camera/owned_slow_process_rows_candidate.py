"""Bounded serialized slow preparation evidence; no retained source objects."""
from owned_serialized_recent_rows_candidate import RecentRows
import json
from owned_compact_stage_storage_candidate import pack,unpack
class ProcessRows(RecentRows):
 def __init__(self,*args,slow_threshold_ns=80000000,slow_capacity=512,**kwargs):
  assert type(slow_threshold_ns) is int and slow_threshold_ns>0
  assert type(slow_capacity) is int and 1<=slow_capacity<=4096
  self.slow_threshold_ns=slow_threshold_ns;self.slow_capacity=slow_capacity
  super().__init__(*args,**kwargs);self.slow=[];self.slow_total=0;self.slow_dropped=0
 def append(self,row):
  if row['ipc_and_prepare_ns']>self.slow_threshold_ns:
   child=row['child_stages'];end=row['parent_completed_ns']
   selected=dict(older=row['older'],newer=row['newer'],begin_ns=end-row['ipc_and_prepare_ns'],end_ns=end,parent_received_ns=row['parent_received_ns'],ipc_and_prepare_ns=row['ipc_and_prepare_ns'],child_prepare_ns=row['child_prepare_ns'],parent_output_decode_ns=row['parent_output_decode_ns'],shared_read=row['shared_read'],child_boundaries=child['child_boundaries'],child_gc_rows=child['child_gc_rows'],child_gc_dropped=child['child_gc_dropped'],child_send_ns=child['send_ns'],child_precompute_ns=child['precompute_ns'],child_construct_ns=child['construct_advance_ns'])
   selected['shared_write']=dict(child.get('shared_write') or {})
   if child.get('process_context') is not None:selected['process_context']={k:(dict(v) if isinstance(v,dict) else v) for k,v in child['process_context'].items()}
   if 'child_thread_cpu_ns' in child:selected['child_thread_cpu_ns']=child['child_thread_cpu_ns']
   encoding=child.get('encode_samples',[])
   selected['encode_sample_encoding']='alpha_start_end_cycles_framebytes_tailindex_v1'
   selected['encode_sample_count']=len(encoding)
   selected['encode_samples']=[[x['alpha'],x['started_ns'],x['completed_ns'],x['thread_cycles'],x['frame_bytes'],x['tail_index']] for x in encoding[:8]]
   selected['encode_samples_truncated']=len(encoding)>8
   selected['encoding_cleanup']=dict(child.get('encoding_cleanup') or {})
   selected['source_sidecar_trace']=dict(child.get('source_sidecar_trace') or {})
   selected['construct_stages']=[{k:x[k] for k in ('name','started_ns','completed_ns','wall_ns','thread_cycles','thread_cpu_ns') if k in x} for x in child.get('construct_stages',[])[:32]]
   for retained,original in zip(selected['construct_stages'],child.get('construct_stages',[])[:32]):
    phases=original.get('asset_stages',[])
    if phases:
     retained['asset_stage_encoding']='name_start_wall_cycles_v1'
     retained['asset_stage_count']=len(phases)
     retained['asset_stages']=[[p['name'],p['started_ns'],p['wall_ns'],p['thread_cycles']] for p in phases[:5]]
     retained['asset_stages_truncated']=len(phases)>5
   selected['sample_stages']=[dict(alpha=x['alpha'],started_ns=x['started_ns'],completed_ns=x['completed_ns'],wall_ns=x['wall_ns'],thread_cycles=x['thread_cycles'],**({'thread_cpu_ns':x['thread_cpu_ns']} if 'thread_cpu_ns' in x else {}),stages=[{k:y[k] for k in ('name','started_ns','completed_ns','wall_ns','thread_cycles','thread_cpu_ns') if k in y} for y in x.get('source_sample_stages',[])[:16]]) for x in child.get('sample_timings',[])[:8]]
   all_samples=child.get('sample_timings',[])[:8]
   anchor_index=max(range(len(all_samples)),key=lambda i:all_samples[i]['wall_ns']) if all_samples else None
   selected['anchor_detail_sample_index']=anchor_index
   for sample_index,(retained,sample) in enumerate(zip(selected['sample_stages'],all_samples)):
    for target,original in zip(retained['stages'],sample.get('source_sample_stages',[])[:16]):
     anchors=original.get('anchor_stages',[]) if sample_index==anchor_index else []
     if not anchors:continue
     target['anchor_stage_encoding']='name_start_wall_cycles_v1'
     target['anchor_stage_count']=len(anchors)
     target['anchor_stages']=[[a['name'],a['started_ns'],a['wall_ns'],a['thread_cycles']] for a in anchors[:4]]
     target['anchor_stages_truncated']=len(anchors)>4
     metadata=[m for a in anchors for m in a.get('metadata_stages',[])]
     target['metadata_stage_count']=len(metadata)
     target['metadata_stages']=[[m['name'],m['started_ns'],m['wall_ns'],m['thread_cycles']] for m in metadata[:8]]
     target['metadata_stages_truncated']=len(metadata)>8
    assembly=sample.get('assembly_stages',[])
    top=sorted(enumerate(assembly),key=lambda item:item[1]['wall_ns'],reverse=True)[:3]
    retained['assembly_stage_count']=len(assembly)
    retained['slowest_assembly_stages']=[dict(stage_index=i,**{k:stage[k] for k in ('name','started_ns','completed_ns','wall_ns','thread_cycles','thread_cpu_ns') if k in stage}) for i,stage in top]
    for detail,(index,original) in zip(retained['slowest_assembly_stages'],top):
     visibility=original.get('visibility_stages',[])
     detail['visibility_stage_count']=len(visibility)
     detail['visibility_stages']=[[phase['name'],phase['count'],phase['started_ns'],phase['wall_ns'],phase['thread_cycles']] for phase in visibility[:5]]
     detail['visibility_stage_encoding']='name_count_start_wall_cycles_v1'
     detail['visibility_stages_truncated']=len(visibility)>5
   selected['stage_records_truncated']=len(child.get('construct_stages',[]))>32 or len(child.get('sample_timings',[]))>8 or any(len(x.get('source_sample_stages',[]))>16 for x in child.get('sample_timings',[]))
   encoded=json.dumps(pack(selected),separators=(',',':'),allow_nan=False);self.slow_total+=1
   if len(encoded.encode())>16384 or len(self.slow)>=self.slow_capacity:self.slow_dropped+=1
   else:self.slow.append(encoded)
  super().append(row)
 def stats(self):
  result=super().stats();result['slow_process_intervals']=dict(threshold_ns=self.slow_threshold_ns,total=self.slow_total,dropped=self.slow_dropped,capacity=self.slow_capacity,records=[unpack(json.loads(x)) for x in self.slow],scope=f'Requests above{self.slow_threshold_ns/1e6:g}ms; parent end-minus-total begin is approximate, child absolute boundaries authoritative; GC clock values comparable on same host. Not exclusive stage attribution.')
  return result
