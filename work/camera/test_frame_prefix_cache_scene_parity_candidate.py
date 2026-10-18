import sys,json,hashlib,ctypes as C,time
from pathlib import Path
sys.argv=['test','work/camera/prototype-runs/owned-native-1791434872973979000.json']
setup=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0];exec(compile(setup,'saved-complete-scene','exec'))
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_frame_prefix_cache_candidate import install,stats
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
def capture(alpha):
 f,c,m,b,d=prepared.sample(alpha)
 return (bytes(f),None if c is None else bytes(c),None if m is None else bytes(m),bytes(b),d)
try:
 alphas=[x['alpha'] for x in expected];baseline={a:capture(a) for a in alphas}
 install();checks=[]
 for repeat in range(3):
  for alpha in alphas:
   actual=capture(alpha);assert actual==baseline[alpha],(repeat,alpha)
   checks.append(dict(repeat=repeat,alpha=alpha,frame_sha256=hashlib.sha256(actual[0]).hexdigest(),frame_bytes=len(actual[0])))
 assert stats['hits']>0 and stats['misses']>0
 cache=prepared.pair._immutable_prefix_cache;assert len(cache)<=8 and prepared.pair._immutable_prefix_bytes<=32*1024*1024
 out=dict(result='PASS_COMPLETE_SAVED_SCENE_PREFIX_CACHE_PARITY',checks=checks,cache_stats=stats,scope='Exact complete frame bytes, camera/model/bounds bytes and detail equality against original assembly for same saved source scene repeated phases. Bounded pair ownership; not live cadence, full-scene fidelity or60fps proof.')
 Path('work/camera/prototype-runs/frame-prefix-cache-scene-parity-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'],stats)
finally:prepared.close();history.close()
