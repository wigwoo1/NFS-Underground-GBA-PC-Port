import sys,json,copy,struct
from pathlib import Path
import owned_scenery_thread_library_install_candidate,owned_visibility_thread_library_install_candidate,owned_viewport_bounds_fixed_types_install_candidate
import owned_endpoint_road_planner as planner
from owned_endpoint_road_fixed_types_candidate import endpoint_road_span_candidates
planner.endpoint_road_span_candidates=endpoint_road_span_candidates
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
from owned_endpoint_tail_reference_candidate import encode_samples,resolve_frame,TAG
from owned_segmented_borrowed_tail_encode_candidate import encode_samples as old_encode
from owned_shared_payload import write_payload,read_payload
from owned_source_process_sidecar_candidate import encode as encode_sidecar
from owned_endpoint_reference_process_service_candidate import ReferenceSamples
from owned_shared_blob import SharedBlobOwner
report=json.loads(Path(sys.argv[1]).read_text());folder=Path(report['live_preparation_profiles'][0]['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
ns={};exec(compile(source,'captured_setup','exec'),ns);ns['prepared'].close();ns['history'].close()
frames,scenes,rom,table=[ns[k] for k in ('frames','scenes','rom','table')];history=planner.EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);samples=PrecomputedSourceWorldSamples(prepared,(.1,.35,.9));owner=SharedBlobOwner(64*1024*1024)
try:
 original=old_encode(samples.samples,borrow_tails=True);reference=encode_samples(samples.samples,tuple(frames));assert reference['referenced_tail_bytes']>0
 identity=(scenes[0].graph.epoch,scenes[0].graph.refresh,scenes[1].graph.refresh)
 sidecar=encode_sidecar(samples,identity);reference['source_sidecar']=sidecar;original['source_sidecar']=sidecar
 a=write_payload(owner.memory,original,1,1);expected=read_payload(a,1,owner.memory)
 b=write_payload(owner.memory,reference,1,2);received=read_payload(b,1,owner.memory);checks=0
 for (alpha,value),(expected_alpha,expected_value) in zip(received['samples'],expected['samples']):
  assert alpha==expected_alpha and value[2:]==expected_value[2:]
  tail=received['tails'][value[1]]
  if isinstance(tail,tuple):frame=resolve_frame(value[0],tail,tuple(frames));assert frame.base in frames;assert bytes(frame)==expected_value[0]+expected['tails'][expected_value[1]]
  else:assert value[0]+tail==expected_value[0]+expected['tails'][expected_value[1]]
  checks+=1
 valid=ReferenceSamples(received,identity,tuple(frames));assert valid.endpoint_base_reuses==3;valid.close()
 bad_cases=[]
 for ref in [('bad',0,frames[0][:40],len(frames[0])-40), (TAG,True,frames[0][:40],1), (TAG,-1,frames[0][:40],1), (TAG,0,b'bad',1)]:
  bad=copy.deepcopy(received);bad['tails'][0]=ref;bad_cases.append(bad)
 bad=copy.deepcopy(received);t=list(bad['tails'][0]);t[3]+=1;bad['tails'][0]=tuple(t);bad_cases.append(bad)
 for index in (True,-1,999):
  bad=copy.deepcopy(received);alpha,value=bad['samples'][0];v=list(value);v[1]=index;bad['samples'][0]=(alpha,tuple(v));bad_cases.append(bad)
 bad=copy.deepcopy(received);bad['source_sidecar']['identity']=(identity[0]+1,*identity[1:]);bad_cases.append(bad)
 bad=copy.deepcopy(received);alpha,value=bad['samples'][0];v=list(value);v[0]=v[0][:-1];bad['samples'][0]=(alpha,tuple(v));bad_cases.append(bad)
 bad=copy.deepcopy(received);bad['samples'].append(bad['samples'][0]);bad_cases.append(bad)
 for bad in bad_cases:
  try:ReferenceSamples(bad,identity,tuple(frames))
  except ValueError:checks+=1
  else:raise AssertionError('Malformed integrated reference accepted')
 out=dict(result='PASS_INTEGRATED_REFERENCE_DECODER_GUARDS',checks=checks,valid_samples=3,rejected_cases=len(bad_cases),original_shared_bytes=a[3],reference_shared_bytes=b[3],referenced_tail_bytes=reference['referenced_tail_bytes'],scope='Actual captured3intermediate frame/array/detail/shared read parity and integrated reference/source-sidecar guard rejection; full live qualification separate.')
finally:samples.close();history.close();owner.close()
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
