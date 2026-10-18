import owned_segmented_display_placement_install_candidate
import owned_renderer_dispatch_trace_install_candidate
import owned_present_stage_trace_install_candidate
import owned_source_draw_type_reuse_install_candidate
import sys,json,ctypes as C,weakref
from pathlib import Path
sys.argv=['test','work/camera/prototype-runs/owned-native-1791434872973979000.json']
setup=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0];exec(compile(setup,'captured_setup','exec'))
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_source_segmented_draw_candidate import OwnedSourceDraw
from owned_native_source_segmented_release_worker_candidate import NativeSourceWorker
from owned_native_source_segmented_session_candidate import NativeFrameIdentityError
reference=json.loads(Path('work/camera/prototype-runs/source-segmented-parity-20261008.json').read_text())['samples']
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected))
boundaries=[]
for scene in scenes:
 record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity);origin=record['asset_origin'];offset=record['source']-0x08000000
 boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376]);worker=NativeSourceWorker();results=[]
namespace={};exec(compile(Path('work/camera/owned_source_segmented_draw_candidate.py').read_text(),'original_draw_source','exec'),namespace);OriginalDraw=namespace['OwnedSourceDraw']


import gc,sys
from collections import Counter
from collections.abc import Mapping

def inventory(root):
 stack=[root];seen=set();types=Counter();tracked=Counter();sizes=Counter()
 while stack:
  value=stack.pop();identity=id(value)
  if identity in seen:continue
  seen.add(identity)
  if len(seen)>500000:raise RuntimeError('Inventory bound exceeded')
  name=type(value).__module__+'.'+type(value).__name__;types[name]+=1;sizes[name]+=sys.getsizeof(value)
  if gc.is_tracked(value):tracked[name]+=1
  if isinstance(value,Mapping):stack.extend(value.values())
  elif isinstance(value,(tuple,list,set,frozenset)):stack.extend(value)
  elif type(value).__module__.startswith(('owned_','live_')) and hasattr(value,'__dict__'):stack.append(vars(value))
 return dict(unique_objects=len(seen),tracked_objects=sum(tracked.values()),tracked_types=tracked.most_common(15),shallow_bytes_by_type=sizes.most_common(10),scope='Owned object dictionaries and containers, shared identities deduplicated per root. External library/type/function/module internals excluded; shallow sizes not total process memory.')
try:
 out={name:inventory(value) for name,value in dict(precomputed=cached,prepared=prepared,scene_snapshots=scenes,road_history=history,road_endpoints=roads).items()}
 objects=gc.get_objects();counts=Counter(type(x).__module__+'.'+type(x).__name__ for x in objects);out['process_tracked_inventory']=dict(total=len(objects),types=counts.most_common(25),scope='Captured fixture/harness process with imports and initialized worker, not live gameplay; no root ownership or GC-cost causal claim.');del objects
 Path('work/camera/prototype-runs/captured-retention-inventory-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
finally:worker.close();cached.close();history.close()
