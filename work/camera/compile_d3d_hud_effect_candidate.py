import ctypes as C,json,hashlib
from pathlib import Path
p=Path('work/camera');src=(p/'owned_d3d_hud_effect_candidate.hlsl').read_bytes();d=C.WinDLL('d3dcompiler_47.dll');P=C.c_void_p
fn=d.D3DCompile;fn.argtypes=[P,C.c_size_t,C.c_char_p,P,P,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(P),C.POINTER(P)];fn.restype=C.c_long
blob=P();err=P();h=fn(src,len(src),b'owned_d3d_hud_effect_candidate.hlsl',None,None,b'pixel',b'ps_4_0',1,0,C.byref(blob),C.byref(err))
def method(b,i,typ,*args):
 table=C.cast(b,C.POINTER(C.POINTER(P))).contents
 return C.WINFUNCTYPE(typ,P,*args)(table[i])
def contents(b):return C.string_at(method(b,3,P)(b),method(b,4,C.c_size_t)(b))
message=contents(err).decode(errors='replace') if err else ''
if err:method(err,2,C.c_ulong)(err)
assert h>=0,(h,message)
code=contents(blob);method(blob,2,C.c_ulong)(blob);(p/'owned-d3d-hud-effect-candidate.cso').write_bytes(code)
r=dict(result='PASS_HUD_HLSL_COMPILE',source_sha256=hashlib.sha256(src).hexdigest(),bytecode_sha256=hashlib.sha256(code).hexdigest(),bytecode_bytes=len(code),compiler_messages=message,scope='Shader compilation only; texture binding, GPU output parity, full-scene replay and live motion not yet verified.')
(p/'prototype-runs/d3d-hud-shader-compile.json').write_text(json.dumps(r,indent=2));print(r)
