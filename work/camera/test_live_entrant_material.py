"""Observe actual rejected entrant material invariance without changing policy."""
import ctypes as C,json,runpy
from pathlib import Path
p=Path(__file__).resolve().parent
crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p,C.c_char_p]
assert crt._putenv_s(b'NF_TEST_ENTRANT_MATERIAL_AUDIT',b'1')==0
context=runpy.run_path(str(p/'test_draw_camera_pair.py'))
d=context['d'];out=(C.c_uint32*8)()
d.nf_live_entrant_material_audit.argtypes=[C.c_void_p]
d.nf_live_entrant_material_audit(out)
assert out[0]>0 and out[0]==out[1]+out[3] and out[3]==0 and out[2]>0,list(out)
assert out[4]==out[0] and out[5]==0 and out[6]>0 and out[7]>0,list(out)
report=dict(result='PASS',comparisons=out[0],geometry_uv_alpha_lighting_invariant=out[1],expanded_rgba_differences=out[2],failures=out[3],indexed_materials_verified=out[4],indexed_failures=out[5],nontransparent_index_color_checks=out[6],owned_index_bytes=out[7],scope='Actual entering commands extracted from owned sampled root reader under differing older-pass palettes; geometry/UV/alpha/lighting headers unchanged. All owned source/shade index planes reproduce nontransparent RGB in both palette expansions. Existing palette rejection remains; complete consumer ownership and GPU index/UV correspondence still required.')
(p/'live-entrant-material-tests.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
