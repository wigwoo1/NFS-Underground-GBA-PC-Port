from pathlib import Path
import ctypes as C,json,struct
p=Path('work/camera');events=json.loads((p/'stable-original-road-source.json').read_text())['roads'];Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t);f=C.CDLL(str((p/'road-camera-metadata.dll').resolve())).nf_road_camera_metadata_owned;f.argtypes=[C.c_void_p,Read,C.c_void_p,C.c_void_p];checks=[]
for event in events:
 state=bytes.fromhex(event['blocks']['1']['hex']);matrix=bytes.fromhex(event['blocks']['2']['hex']);address=event['blocks']['2']['address'];assert struct.unpack_from('<I',state,84)[0]==address
 calls=[]
 @Read
 def read(user,a,out,size):
  calls.append((a,size))
  if a!=address or size!=48:return 0
  C.memmove(out,matrix,48);return 1
 out=C.create_string_buffer(bytes([0x7b])*56,56);assert f(state,read,None,out);assert out.raw==struct.pack('<2I',1,address)+matrix;assert calls==[(address,48)]
 # Callback storage is changed after publication; copied metadata must survive.
 saved=out.raw;matrix=bytes(48);assert out.raw==saved
 @Read
 def fail(user,a,target,size):C.memset(target,0,size);return 0
 out=C.create_string_buffer(bytes([0x7b])*56,56);assert not f(state,fail,None,out);assert out.raw==bytes([0x7b])*56
 bad=bytearray(state);struct.pack_into('<I',bad,84,0xfffffffc);calls.clear();assert not f(bytes(bad),read,None,out);assert not calls and out.raw==bytes([0x7b])*56
 checks.append(dict(source=event['source'],matrix_address=address,exact_owned_bytes=56,atomic_reader_and_address_rejections=2))
report=dict(result='PASS',checks=checks,scope='Standalone producer helper consuming original state and owned-reader callback; no packet schema/live integration yet.')
(p/'road-camera-metadata-tests.json').write_text(json.dumps(report,indent=2));print(report)
