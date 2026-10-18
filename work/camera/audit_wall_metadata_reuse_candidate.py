from pathlib import Path
import sys,json,types,time
sys.path.insert(0,str(Path('work/camera').resolve()))
env={};exec(Path('work/camera/test_progressive_source_samples_candidate.py').read_text(),env)
import owned_sampled_graph_wall_visibility as module
fn=module.wall_metadata;original=types.FunctionType(fn.__code__,fn.__globals__,fn.__name__,fn.__defaults__,fn.__closure__)
rows=[]
def traced(portal,graph):
 hit=any(owner is graph for owner,_ in getattr(portal,'_wall_metadata_cache',()))
 kind='older' if graph is portal.older else 'newer' if graph is portal.newer else 'other'
 begin=time.perf_counter_ns();result=_metadata_original(portal,graph);end=time.perf_counter_ns()
 _metadata_rows.append(dict(hit=hit,kind=kind,elapsed_ms=(end-begin)/1e6,cache_size=len(portal._wall_metadata_cache)))
 return result
fn.__globals__.update(_metadata_original=original,_metadata_rows=rows);fn.__code__=traced.__code__
try:
 history,prepared=env['prepare']();packets=[]
 try:samples=env['ProgressiveSourceWorldSamples'](prepared,env['alphas'],on_sample=packets.append);samples.close();assert [env['fingerprint'](p) for p in packets]==env['expected']
 finally:history.close()
finally:fn.__code__=original.__code__
out=dict(result='PASS_EXACT_WALL_METADATA_REUSE_AUDIT',calls=len(rows),misses=sum(not x['hit'] for x in rows),rows=rows,scope='One saved complete six-sample fixture; identity cache hits/misses, exact outputs; no live performance claim.')
Path('outputs/nfsug-native-renderer/camera-research/wall-metadata-reuse-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
