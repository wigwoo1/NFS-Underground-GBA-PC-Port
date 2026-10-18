"""Diagnostic full-scene supplemental insertion with explicit retained order anchor."""
import struct,ctypes as C
from owned_motion_pairs import records
from owned_complete_supplemental_gpu import sampled_gpu_records

def encode(row):return struct.pack('<4I',0x3147534e,row['kind'],row['context'],12)+b''.join(struct.pack('<I',len(b))+bytes(b) for b in row['blocks'])

def assemble(pair,alpha,rom):
 base,camera,old_models=pair.portal.motion.sample(alpha);rows=records(base)['records'];endpoint=1 if alpha==1 else 0
 keys={w.vertices for w in pair.assets[endpoint]}
 supplemental=[i for i,r in enumerate(rows) if r['kind']==2 and bytes(r['blocks'][0]) in keys]
 models=[i for i,r in enumerate(rows) if r['kind']==3]
 if len(models)!=1 or models[0]!=len(rows)-1:raise ValueError('Unverified ordinary object placement')
 anchor=models[0]
 if supplemental and supplemental!=list(range(min(supplemental),anchor)):raise ValueError('Supplemental records do not precede retained model anchor')
 if any(r['kind'] not in (1,2) for r in rows[:anchor]):raise ValueError('Unverified surface/object interleave')
 selected=sampled_gpu_records(pair,alpha,rom);output=[];bounds=[];indices=[]
 for i,row in enumerate(rows[:anchor]):
  if i in supplemental:continue
  output.append(encode(row));bounds.extend(struct.unpack('<4H',row['blocks'][5]) if row['kind']==2 else (0,0,0,0));indices.append(i)
 for item in selected:
  output.append(item['record']);bounds.extend(item['bounds']);indices.append(None)
 output.append(encode(rows[anchor]));bounds.extend((0,0,0,0));indices.append(anchor)
 h=list(struct.unpack_from('<6I2Q',base));tail=base[40+h[2]:];geometry=b''.join(output);h[2]=len(geometry);frame=struct.pack('<6I2Q',*h)+geometry+tail
 models_out=None
 if old_models is not None:
  models_out=(C.c_double*(12*len(output)))()
  for destination,source in enumerate(indices):
   if source is not None:
    for k in range(12):models_out[destination*12+k]=old_models[source*12+k]
 return frame,camera,models_out,(C.c_double*len(bounds))(*bounds),dict(supplemental_records=len(selected),removed_endpoint_records=len(supplemental),retained_world_records=anchor-len(supplemental),retained_model_records=1,order_scope='Original endpoint surface/model anchor retained; independent cross-kind ordering pending')
