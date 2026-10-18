import json,time,statistics,tracemalloc
from pathlib import Path
from owned_graph_packet import GraphPacket
from owned_graph_wall_sources import wall_sources
p=Path('work/camera');ns={};exec((p/'owned_graph_wall_sources.before-descriptor-skip.py').read_text(),ns);results=[]
for refresh in (8754,8758,8762,8765,8769,8772,8776):
 g=GraphPacket.decode((p/f'graph-packets/{refresh}.ngp').read_bytes());groups=[{d} for d in sorted({w.descriptor for w in wall_sources(g)})[:12]];samples={'baseline':[],'skip':[]};peaks={}
 for trial in range(20):
  for name,f in (('baseline',ns['wall_sources']),('skip',wall_sources)) if trial%2==0 else (('skip',wall_sources),('baseline',ns['wall_sources'])):
   cache=[g,None];begin=time.perf_counter_ns()
   for group in groups:f(g,descriptors=group,material_cache=cache)
   samples[name].append((time.perf_counter_ns()-begin)/1e6)
 for name,f in (('baseline',ns['wall_sources']),('skip',wall_sources)):
  cache=[g,None];tracemalloc.start()
  for group in groups:f(g,descriptors=group,material_cache=cache)
  peaks[name]=tracemalloc.get_traced_memory()[1];tracemalloc.stop()
 results.append(dict(refresh=refresh,groups=len(groups),median_ms={k:statistics.median(v) for k,v in samples.items()},peak_bytes=peaks,samples=samples))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wall-descriptor-skip-cost-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='MEASURED',results=results,scope='20 alternating paired trials per graph, 12 separately selected descriptor groups sharing one freshly decoded material cache per trial. Allocation measured separately. Not live cadence certification.'),indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
print(json.dumps([{k:v for k,v in x.items() if k!='samples'} for x in results]))
