import runpy,json
from pathlib import Path
baseline=runpy.run_path('work/camera/owned_source_native_depth_rectangle_candidate.py.before-buffer-types')['SourceFaceDeterminants']
source=Path('work/camera/test_precomputed_source_eight_samples.py').read_text();ns={};exec(source[:source.index(' import gc')]+'\nfinally: pass\n',ns)
ns['cached'].close();ns['history'].close();checks=0
for classifier in ns['classifiers'].values():
 old=baseline.__new__(baseline);old.__dict__.update(classifier.__dict__)
 for alpha in (0,.1,.5,.9,1):
  m=tuple((1-alpha)*a+alpha*b for a,b in zip(*classifier.matrices))
  assert old.projected(m,classifier.scales[0],classifier.centers[0])==classifier.projected(m,classifier.scales[0],classifier.centers[0])
  assert old.decisions(m,alpha)==classifier.decisions(m,alpha);checks+=1
 a=classifier._projection_buffer_type();b=classifier._projection_buffer_type()
 if len(a):a[0]=123;assert b[0]==0
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/depth-buffer-types-audit-20261007')
(cp/'parity.json').write_text(json.dumps(dict(result='PASS',classifiers=len(ns['classifiers']),projection_and_face_checks=checks,private_buffers=True,scope='Actual captured source classifiers at five fractions after source owner close, baseline projection and face decisions; component only'),indent=2))
for name in ('test_depth_buffer_types_parity.py','owned_source_native_depth_rectangle_candidate.py','owned_source_native_depth_rectangle_candidate.py.before-buffer-types'):(cp/name).write_bytes(Path('work/camera',name).read_bytes())
print('PASS',checks,'source projection/face decision comparisons and private buffers')