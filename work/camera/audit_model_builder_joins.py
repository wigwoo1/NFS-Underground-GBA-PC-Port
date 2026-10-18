"""Join original scenery matrix builds to later consumed poses by source/address/time."""
import json,struct,ctypes as C,collections
from pathlib import Path
from owned_model_builder_inputs import OwnedModelBuilders
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791279461173682600.json').read_text());p=Path(r['model_pose_trace']);builds=p.with_suffix('.builders.bin').read_bytes();poses=p.read_bytes();rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
@Read
def read(_,address,target,n):
 offset=address-0x08000000
 if not 0<=offset<=len(rom)-n:return 0
 C.memmove(target,rom[offset:offset+n],n);return 1
lib=C.CDLL('work/camera/visibility-probe-wide.dll');fn=lib.nf_object_projection_matrix;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p]
assert len(builds)%292==0 and len(poses)%292==0, 'Truncated pose trace'
bykey=collections.defaultdict(list);models=collections.Counter()
for at in range(0,len(builds),292):
 h=struct.unpack_from('<8I',builds,at);assert h[0]==0x31424d4e and h[5]==260 and h[6]==1, 'Invalid builder record';obj=builds[at+32:at+196];model=struct.unpack_from('<h',obj,54)[0];models[model]+=1
 if not 31<=model<=36:continue
 output=C.create_string_buffer(builds[at+244:at+292],48);assert fn(builds[at+196:at+244],obj,output,read,None)
 bykey[(h[3],h[4])].append((h[1],bytes(output),obj))
store=OwnedModelBuilders(builds)
checks=[]
for at in range(0,len(poses),292):
 h=struct.unpack_from('<8I',poses,at);assert h[0]==0x31504f4e and h[6]==260 and h[7]==1, 'Invalid consumed pose record';obj=poses[at+32:at+196];model=struct.unpack_from('<h',obj,54)[0]
 if not 31<=model<=36:continue
 try: builder=store.at(h[3],h[5],h[1])
 except ValueError: builder=None
 output=C.create_string_buffer(builder.initial_matrix,48) if builder else None
 if builder: assert fn(builder.camera,builder.source,output,read,None)
 checks.append(dict(refresh=h[1],model=model,object=h[3],matrix=h[5],builder_refresh=builder.refresh if builder else None,exact=bool(builder) and bytes(output)==poses[at+244:at+292]))

out=dict(builder_model_counts=dict(models),scenery_pose_count=len(checks),exact=sum(x['exact'] for x in checks),unjoined=sum(x['builder_refresh'] is None for x in checks),checks=checks);p.with_suffix('.builder-joins.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='checks'})

assert checks, 'No scenery poses checked'
assert out['unjoined']==0, 'Consumed scenery transform lacks owned builder inputs'
assert out['exact']==out['scenery_pose_count'], 'Reconstructed scenery transform differs from original consumed transform'
print('PASS: all scenery transforms match owned builder provenance')
