from pathlib import Path
import sys,cProfile,pstats,json
sys.path.insert(0,str(Path('work/camera').resolve()))
import owned_wall_record_reuse_install_candidate
import owned_rom_slice_reuse_install_candidate
import owned_record_miss_container_reuse_install_candidate
import owned_road_planner_library_install_candidate
import owned_road_material_decode_install_candidate
import owned_preparation_fixed_types_install_candidate
import owned_road_record_worker_install_candidate
import owned_endpoint_road_planner as planner
from owned_endpoint_road_fixed_types_candidate import endpoint_road_span_candidates
planner.endpoint_road_span_candidates=endpoint_road_span_candidates
import owned_source_presentation_batch_candidate as batch
from owned_source_depth_transition_candidate import SourceFaceDeterminants
batch.SourceFaceDeterminants=SourceFaceDeterminants
env={};exec(Path('work/camera/test_progressive_source_samples_candidate.py').read_text(),env)
data=env['env'];history=env['EndpointRoadPlanner'](data['rom'],data['table']);roads,_=history.plan(data['scenes'][0].graph)
profiles={};construction=cProfile.Profile();construction.enable()
prepared=env['PreparedWorldMotion'](*data['frames'],*data['scenes'],history,roads,data['rom'])
construction.disable();profiles['construction']=construction
first=cProfile.Profile();packets=[]
def ready(packet):
 if not packets:first.disable()
 packets.append(packet)
try:
 first.enable();samples=env['ProgressiveSourceWorldSamples'](prepared,env['alphas'],on_sample=ready);first.disable();samples.close()
 assert [env['fingerprint'](p) for p in packets]==env['expected'];profiles['first_ready']=first
finally:history.close()
rows={}
for phase,prof in profiles.items():
 stats=pstats.Stats(prof);output=[]
 for (file,line,name),(cc,nc,tt,ct,callers) in stats.stats.items():
  if tt>=.00002:output.append(dict(file=file,line=line,name=name,calls=nc,self_ms=tt*1000,cumulative_ms=ct*1000,callers=[dict(file=k[0],line=k[1],name=k[2],metrics=list(v) if isinstance(v,tuple) else v) for k,v in callers.items()]))
 rows[phase]=sorted(output,key=lambda x:x['self_ms'],reverse=True)
out=dict(result='PASS_EXACT_CURRENT_HELPER_FIRST_READY_PROFILE',rows=rows,scope='One saved fixture; cProfile perturbs timing, self time helps target functions; component exact six-sample fingerprint, no live cadence proof.')
Path('outputs/nfsug-native-renderer/camera-research/current-helper-first-ready-profile-20261009.json').write_text(json.dumps(out,indent=2))
for phase,items in rows.items():print(phase,[(x['name'],round(x['self_ms'],3),x['calls']) for x in items[:12]])
