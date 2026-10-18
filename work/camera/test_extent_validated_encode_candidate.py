import owned_scenery_thread_library_install_candidate
import owned_endpoint_road_planner as road_planner
from owned_endpoint_road_fixed_types_candidate import endpoint_road_span_candidates
road_planner.endpoint_road_span_candidates=endpoint_road_span_candidates
import owned_viewport_bounds_fixed_types_install_candidate
import owned_visibility_thread_library_install_candidate
import owned_segmented_display_placement_install_candidate
import owned_hud_cache_lease_worker_install_candidate
import owned_renderer_dispatch_trace_install_candidate
import owned_present_stage_trace_install_candidate
import owned_renderer_fixed_types_install_candidate
import owned_hud_prefetch_d3d_profile_install_candidate
import owned_packet_profile_install_candidate
import owned_d3d_call_profile_install_candidate
import owned_ordered_render_tail_install_candidate
import owned_source_packet_phase_profile_install_candidate
import sys,json,ctypes as C,weakref
from pathlib import Path


import runpy,hashlib
import owned_wall_record_reuse_install_candidate
from owned_material_decode_process_service_candidate import ProcessPreparationService
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
from owned_prepared_world_segmented_candidate import PreparedWorldMotion

def fingerprint(owner,alpha):
 v=owner.sample(alpha);m=owner.source_masks[alpha]
 return (bytes(v[0]),*(None if x is None else bytes(x) for x in v[1:4]),v[4],bytes(m[0]),bytes(m[1]),m[2],m[3],owner.source_cameras)
if __name__=='__main__':
 report=json.loads(Path(sys.argv[1]).read_text());folder=Path(report['live_preparation_profiles'][0]['capture'])
 source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
 ns={};exec(compile(source,'captured_process_setup','exec'),ns);ns['prepared'].close();ns['history'].close()
 frames,scenes,rom,table=[ns[k] for k in ('frames','scenes','rom','table')]
 from owned_endpoint_road_planner import EndpointRoadPlanner
 history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
 alphas=(.1,.35,.9);direct=PrecomputedSourceWorldSamples(prepared,alphas);expected={a:fingerprint(direct,a) for a in alphas}


 from owned_extent_validated_sidecar_encode_candidate import original,encode
 import time,statistics,copy
 identity=(scenes[0].graph.epoch,scenes[0].graph.refresh,scenes[1].graph.refresh);times={};payloads={}
 for label,fn in [('original',original),('extent',encode)]:
  values=[]
  for i in range(100):
   start=time.perf_counter_ns();payload=fn(direct,identity);values.append(time.perf_counter_ns()-start)
  times[label]=statistics.median(values)/1e6;payloads[label]=payload
 assert payloads['original']==payloads['extent']
 from owned_source_process_sidecar_candidate import decode as old_decode
 from owned_source_extent_sidecar_candidate import decode as new_decode
 cases=[]
 for mode in ['identity','camera','mask','offset','diagnostic']:
  payload=copy.deepcopy(payloads['original'])
  if mode=='identity':payload['identity']=(0,1,2)
  elif mode=='camera':payload['cameras']=b''
  else:
   row=list(payload['masks'][0])
   if mode=='mask':row[2]=bytes([2])*len(row[2])
   elif mode=='offset':row[1]=b''
   else:row[4]['selected_faces']+=1
   payload['masks'][0]=tuple(row)
  errors=[]
  for fn in [old_decode,new_decode]:
   try:fn(payload,direct.samples,identity);raise AssertionError('Invalid payload accepted')
   except ValueError as e:errors.append(str(e))
  assert errors[0]==errors[1];cases.append(mode)
 import struct
 frame=bytes(direct.samples[alphas[0]][0]);frame_cases=[]
 for label,offset,value in [('magic',0,0),('epoch',24,0),('ticks',32,0),('source_magic',40,0),('source_kind',44,9),('source_blocks',52,11),('block_extent',56,0x100001)]:
  broken=bytearray(frame);struct.pack_into('<I',broken,offset,value);samples=dict(direct.samples);record=list(samples[alphas[0]]);record[0]=bytes(broken);samples[alphas[0]]=tuple(record)
  errors=[]
  for fn in [old_decode,new_decode]:
   try:fn(payloads['original'],samples,identity);raise AssertionError('Malformed frame accepted')
   except ValueError as e:errors.append(str(e))
  assert errors[0]==errors[1];frame_cases.append(label)
 direct.close();history.close()
 out=dict(result='PASS_EXTENT_VALIDATED_ENCODE_PARITY',samples=len(alphas),times_ms=times,rejected_cases=cases,frame_rejections=frame_cases,scope='Captured payload equality and five rejection cases; no native4K/live timing qualification.')
 Path('work/camera/prototype-runs/extent-validated-encode-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
