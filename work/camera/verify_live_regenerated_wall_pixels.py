"""Exact4K pixels for captured paired live regenerated-wall scenes."""
from pathlib import Path
import ctypes as C,json,hashlib,sys,statistics
report_path=Path(sys.argv[1]);report=json.loads(report_path.read_text());pairs=report['wall_diagnostic_frames'];assert pairs
p=Path('work/camera');d=C.CDLL(str((p/'owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3);checks=[]
def render(path):
 raw=Path(path).read_bytes();assert d.nf_owned_gpu_draw(raw,len(raw))==0;assert d.nf_owned_gpu_read(rgb,len(rgb))==0;return rgb.raw
try:
 for pair in pairs:
  expected=render(pair['original']);actual=render(pair['regenerated']);assert actual==expected,(pair['refresh'],sum(a!=b for a,b in zip(actual,expected)))
  checks.append(dict(refresh=pair['refresh'],pixels_exact=3840*2160,rgb_sha256=hashlib.sha256(actual).hexdigest()))
finally:assert d.nf_owned_gpu_close()
cost=[x['reconstruction_ns']/1e6 for x in report['regenerated_wall_validation']]
r=dict(result='PASS_LIVE_REGENERATED_WALL_4K_PIXELS',checks=checks,reconstruction_ms=dict(median=statistics.median(cost),maximum=max(cost)),scope='Exact live captured scene pixel parity; no full-scene60fps or real-time throughput proof. Diagnostic writes affect host performance; remaining scene records and cross-kind order retained.')
report_path.with_suffix('.wall-pixels.json').write_text(json.dumps(r,indent=2));print(r)
