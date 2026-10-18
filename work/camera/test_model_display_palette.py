from pathlib import Path
import ctypes as C,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()))
fn=d.nf_model_display_palette;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_uint,C.c_void_p]
a=bytearray(512);b=bytearray(512);struct.pack_into('<H',a,0,123);struct.pack_into('<H',b,0,456)
struct.pack_into('<H',a,14,31);struct.pack_into('<H',b,14,31);b[40:42]=b'XY'
out=C.create_string_buffer(b'X'*512,512)
assert fn(bytes([0,7,7,0]),4,bytes(a+b),2,out) and out.raw==bytes(a)
b[14:16]=b'ZZ';C.memset(out,0xa5,512)
assert not fn(bytes([0,7]),2,bytes(a+b),2,out) and out.raw==bytes([0xa5])*512
assert not fn(bytes([0,7]),2,bytes(a+b),0,out) and out.raw==bytes([0xa5])*512
report=dict(result='PASS',display_zero_and_unused_color_differences_allowed=True,used_nonzero_disagreement_atomic_reject=True,missing_bank_atomic_reject=True,scope='Opaque-model nonzero palette consensus only; requires NZI1 plus exact display-row zero composition, not valid for legacy RGBA-only models.')
(p/'model-display-palette-tests.json').write_text(json.dumps(report,indent=2));print(report)
