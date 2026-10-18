import sys,json,time
from pathlib import Path
source=Path('work/camera/profile_captured_preparation_warm.py').read_text().split('import statistics')[0]
exec(compile(source,'captured-setup','exec'))
import owned_sampled_graph_gpu as graph_gpu
import owned_wall_visibility_candidate as visibility
if len(sys.argv)>2 and sys.argv[2]=='warm':visibility.helper();visibility.table(table)
import owned_sampled_graph_wall_visibility as edge_module
original_edge=edge_module.sampled_edge;edge_inputs=[]
def edge(*args,**kwargs):
 edge_inputs.append((args[2],args[3],args[4]));return original_edge(*args,**kwargs)
edge_module.sampled_edge=edge
original_meta=graph_gpu.wall_metadata;original_batch=visibility.batch;counts=[];batches=[];current=0

def metadata(*args):
 global current
 current+=1;return original_meta(*args)
def batch(calls):
 start=time.perf_counter_ns();out=original_batch(calls);batches.append(dict(candidates=len(calls),wall_ns=time.perf_counter_ns()-start));return out
graph_gpu.wall_metadata=metadata;visibility.batch=batch
history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=None
try:
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);samples=[]
 for x in expected:
  current=0;edge_inputs.clear();samples.append(prepared.sample(x['alpha']));counts.append(current);assert current==1
  assert edge_inputs and isinstance(edge_inputs[0][2],tuple)
  assert all(all(a is b for a,b in zip(v,edge_inputs[0])) for v in edge_inputs)
 actual=json.loads(json.dumps([dict(alpha=x['alpha'],signature=signature(sample)) for x,sample in zip(expected,samples)]));assert actual==expected
finally:
 edge_module.sampled_edge=original_edge;graph_gpu.wall_metadata=original_meta;visibility.batch=original_batch
 if prepared is not None:prepared.close()
 history.close()
out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wall-camera-input-identity-20261006');out.mkdir(exist_ok=True)
(out/('warm-tests.json' if len(sys.argv)>2 else 'tests.json')).write_text(json.dumps(dict(result='PASS',capture=str(folder),lookups=counts,batches=batches,scope='Captured complete signatures and graph encoder lookup count; native wall batch wrapper timing includes pack/call/unpack and host scheduling; no fullscene60fps proof'),indent=2));print('PASS one graph encoder metadata lookup each sample',counts,'batch costs',[(x['candidates'],x['wall_ns']/1e6) for x in batches])
