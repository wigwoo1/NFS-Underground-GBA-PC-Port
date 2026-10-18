from pathlib import Path
from dataclasses import replace
import struct,json,collections
from owned_scene_bundle import SceneBundle,chunks
from owned_object_filter import select_owned
p=Path('work/camera');raw=(p/'owned-object-chains.bin').read_bytes();offset=0;expected={}
while offset<len(raw):
 h=struct.unpack_from('<8I',raw,offset);expected[len(expected)]=[struct.unpack_from('<I',raw,offset+304+i*168)[0] for i in range(h[5])];offset+=304+h[6]
scenes=lists=supplements=rejected=associations=empty=0
for file in (p/'scene-bundles').glob('*.nsb'):
 bundle=SceneBundle.decode(file.read_bytes());callbacks=collections.defaultdict(dict)
 for h,raw in chunks(bundle.associations,'associations'):
  associations+=1;empty+=h[4]==65535
 for h,raw in chunks(bundle.callbacks,'callbacks'):
  if h[2]==0x03002090:callbacks[h[7]][struct.unpack_from('<H',raw,32)[0]]=raw[32:196]
 for h,raw in chunks(bundle.objects,'objects'):
  objects={struct.unpack_from('<I',raw,80+i*168)[0]:raw[84+i*168:248+i*168] for i in range(h[5])}
  assert select_owned(h[3],objects,raw[32:80],callbacks[h[4]])==expected[h[4]];lists+=1
 supplements+=len(list(chunks(bundle.supplements,'supplements')));scenes+=1
 for invalid in (file.read_bytes()[:-1],replace(bundle,textures=b'').encode(),replace(bundle,associations=b'').encode(),replace(bundle,graph_objects=b'').encode()):
  try:SceneBundle.decode(invalid)
  except ValueError:rejected+=1
  else:raise AssertionError('Incomplete scene accepted')
assert (scenes,lists,supplements,rejected,associations,empty)==(7,17,9,28,40,23)
r=dict(result='PASS_BUNDLED_SOURCE_OBJECT_SELECTION',scenes=scenes,region_associations=associations,empty_associations=empty,original_lists_exact=lists,supplemental_regions=supplements,invalid_bundles_rejected=rejected,scope='Camera-aligned transport component; ordinary model assets, callback-complete invisible objects/model assets and live integration pending.')
(p/'owned-scene-bundle-tests.json').write_text(json.dumps(r,indent=2));print(r)
