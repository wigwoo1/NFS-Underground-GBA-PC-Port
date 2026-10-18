from pathlib import Path
import sys,copy,json
sys.path.insert(0,str(Path('work/camera').resolve()))
env={};exec(Path('work/camera/test_road_encode_flat_join_candidate.py').read_text(),env)
original=env['original'];candidate=env['candidate'];context,record,bounds=env['calls'][0];cases=[]
for label,field,value in [('missing','missing',True),('ring_size','vertices',b'x'),('face_size','face',b''),('material_size','material',b''),('animation_size','animation',b''),('offset_size','offsets',b''),('texture_size','texture',b'')]:
 bad=copy.copy(record);object.__setattr__(bad,field,value);cases.append((label,(context,bad,bounds)))
for label,clip in [('bounds_size',(0,1)),('bounds_nan',(float('nan'),1,0,1)),('bounds_reverse',(3,2,0,1)),('bounds_range',(0,240,0,159))]:cases.append((label,(context,record,clip)))
rows=[]
for label,args in cases:
 outcomes=[]
 for fn in (original,candidate):
  try:fn(*args)
  except Exception as error:outcomes.append((type(error).__name__,str(error)))
  else:raise AssertionError('invalid record accepted: '+label)
 assert outcomes[0]==outcomes[1];rows.append(dict(case=label,error=outcomes[0]))
out=dict(result='PASS_IDENTICAL_ROAD_ENCODER_REJECTIONS',cases=rows,scope='Preserves original rejection types/messages on 11 malformed source/bounds cases; component only.')
Path('outputs/nfsug-native-renderer/camera-research/road-flat-join-rejections-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
