import sys,json,time,threading
from pathlib import Path
from owned_road_record_diagnostic import decode
from owned_road_history_diagnostic import restore,snapshot
from owned_sample_signature import signature
report=json.loads(Path(sys.argv[1]).read_text());meta=report['live_preparation_profiles'][0];folder=Path(meta['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
exec(compile(source,'captured_scene_setup','exec'));prepared.close();history.close()
h=json.loads((folder/'road-history.json').read_text());roads=decode(json.loads((folder/'older-roads.json').read_text()));expected=json.loads((folder/'prepared-signatures.json').read_text())

import ctypes as C,hashlib
from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
from owned_source_draw_context_candidate import OwnedSourceDraw
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset
history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=None;cached=None
from owned_native_source_world_upload_session_candidate import NativeSourceSession
session=None;results=[]
try:
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected),trace=True)
 boundaries=[]
 for scene in scenes:
  record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
  origin=record['asset_origin'];offset=record['source']-0x08000000
  boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
 origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
 from owned_native_source_process_preparation_candidate import encode_samples,ProcessSamples
 from test_scene_process_transport import digest
 import pickle
 encoded=encode_samples(cached.samples)
 encoded['source_cameras']=cached.source_cameras
 encoded['source_masks']={a:(bytes(v[0]),bytes(v[1]),v[2],v[3]) for a,v in cached.source_masks.items()}
 malformed=[]
 def rejects(label,mutate):
  candidate=pickle.loads(pickle.dumps(encoded));mutate(candidate)
  try:unexpected=ProcessSamples(candidate)
  except ValueError:malformed.append(label)
  else:unexpected.close();raise AssertionError('Accepted malformed '+label)
 alpha=next(iter(encoded['source_masks']))
 def mask_change(e,index,value):
  row=list(e['source_masks'][alpha]);row[index]=value;e['source_masks'][alpha]=tuple(row)
 rejects('camera_count',lambda e:e.update(source_cameras=e['source_cameras'][:3]))
 rejects('nonfinite_camera',lambda e:e.update(source_cameras=((float('nan'),)+e['source_cameras'][0][1:],)+e['source_cameras'][1:]))
 rejects('missing_mask_identity',lambda e:e['source_masks'].pop(alpha))
 rejects('oversized_offsets',lambda e:mask_change(e,0,bytes(146*4)))
 rejects('misaligned_offsets',lambda e:mask_change(e,0,b'x'))
 rejects('wrong_mask_length',lambda e:mask_change(e,1,b''))
 rejects('oversized_face_count',lambda e:mask_change(e,2,32769))
 rejects('invalid_mask_bit',lambda e:mask_change(e,1,b'\x02'+e['source_masks'][alpha][1][1:]))
 rejects('nonzero_first_offset',lambda e:mask_change(e,0,b'\x01\x00\x00\x00'+e['source_masks'][alpha][0][4:]))
 owned=ProcessSamples(pickle.loads(pickle.dumps(encoded)));checks=[]
 try:
  assert owned.source_cameras==cached.source_cameras
  for a in cached.samples:
   assert digest(owned.sample(a))==digest(cached.sample(a))
   original=cached.source_masks[a];copy=owned.source_masks[a]
   assert bytes(copy[0])==bytes(original[0]) and bytes(copy[1])==bytes(original[1]) and copy[2:]==original[2:]
   checks.append(dict(alpha=a,digest=digest(owned.sample(a)),offset_bytes=len(bytes(copy[0])),mask_bytes=len(bytes(copy[1]))))
 finally:owned.close()
 assert not owned.samples and not owned.source_masks
finally:
 if cached is not None:cached.close()
 if prepared is not None:prepared.close()
 history.close()
result=dict(result='PASS_SOURCE_PROCESS_SERIALIZATION_PARITY',checks=checks,malformed_rejections=malformed,scope='Five captured source samples including camera tuples, frame/geometry/details and masks survive actualpickletransport and parent reconstruction exactly; child history computation and live cadence separatelyverified.')
Path('work/camera/prototype-runs/native-source-process-transport-parity.json').write_text(json.dumps(result,indent=2));print(result['result'])
