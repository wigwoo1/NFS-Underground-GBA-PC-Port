"""Measure spatial quantization of the existing sky-pan shader, not scanout."""
import json, math
from pathlib import Path
source=Path("work/camera/owned_d3d_sky_pan_candidate.c").read_text()
assert "floor(source.x+phase)>floor(source.x)" in source
# 3240 output pixel centers map to 240 source columns at scale 13.5.
def mask(phase):
 return bytes(math.floor((x+.5)*2/27+phase)>math.floor((x+.5)*2/27) for x in range(3240))
rows=[mask(i/240) for i in range(240)]
holds=sum(a==b for a,b in zip(rows,rows[1:]))
out=dict(result="CONFIRMED_SHADER_SPATIAL_QUANTIZATION",samples=240,
 distinct_masks=len(set(rows)),adjacent_pixel_mask_holds=holds,
 source_pixels_per_output_pixel=2/27,
 scope="Analytical evaluation of existing shader at output pixel centers. Does not prove active DLL selection, live sky colors, source camera correctness, or visible scanout cadence.")
assert holds>0 and len(set(rows))>1
Path("outputs/nfsug-native-renderer/camera-research/sky-pan-quantization-20261009.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
