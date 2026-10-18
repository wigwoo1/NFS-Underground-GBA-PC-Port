"""Opt-in immutable child scene capture before planner advancement."""
import json,struct,time,hashlib
from pathlib import Path
completed=False
def capture(older,newer,alphas,history,roads):
 global completed
 import os
 target=int(os.environ.get('NFSUG_CHILD_SCENE_CAPTURE_REFRESH','0'))
 if completed or target<=0 or older[1].graph.refresh<target:return None
 folder=Path('work/camera/prototype-runs')/('child-scene-'+str(time.time_ns()));folder.mkdir()
 for label,(frame,owned) in zip(('older','newer'),(older,newer)):
  (folder/(label+'.frame.bin')).write_bytes(frame)
  (folder/(label+'.graph.bin')).write_bytes(owned.graph.graph.encode())
  for section in ('objects','callbacks','associations'):(folder/(label+'.'+section+'.bin')).write_bytes(getattr(owned.graph,section))
  if owned.builders is not None:(folder/(label+'.builders.bin')).write_bytes(owned.builders.payload)
  if owned.sources is not None:(folder/(label+'.current-sources.bin')).write_bytes(owned.sources.payload)
  supplements=owned.supplements
  packet=struct.pack('<6IQ',0x3143534e,1,supplements.refresh,supplements.source_refresh,len(supplements.geometry),len(supplements.textures),supplements.epoch)+supplements.geometry+supplements.textures
  (folder/(label+'.supplements.bin')).write_bytes(packet)
 import json
 (folder/'capture.json').write_text(json.dumps(dict(older=older[1].identity,newer=newer[1].identity,alphas=alphas,scope='Immutable child inputs; planner history saved separately; no prepared signatures'),indent=2))
 from owned_road_history_diagnostic import snapshot
 from owned_road_record_diagnostic import encode,decode
 encoded=encode(roads)
 if decode(json.loads(json.dumps(encoded)))!=roads:raise ValueError('Captured road roundtrip mismatch')
 (folder/'road-history.json').write_text(json.dumps(dict(epoch=history.epoch,refresh=history.refresh,scratch=snapshot(history.scratch)),indent=2))
 (folder/'older-roads.json').write_text(json.dumps(encoded))
 files={f.name:dict(bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in folder.iterdir()}
 (folder/'manifest.json').write_text(json.dumps(dict(result='CAPTURED',target=target,older=older[1].identity,newer=newer[1].identity,files=files,scope='Immutable actual child endpoints and pre-advance planner history; capture overhead excludes performance claims'),indent=2))
 completed=True
 print('CHILD_SCENE_CAPTURE',str(folder),flush=True)
 return str(folder)
