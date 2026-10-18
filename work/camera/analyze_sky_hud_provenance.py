import json,sys
from pathlib import Path
pool=json.loads(Path(sys.argv[1]).read_text());checks=[];total=0;bad=0
for rec in pool['sky_region_records']:
 p=Path(rec['path']);final=p.read_bytes();before=p.with_suffix('.prehud.rgb').read_bytes();sky=p.with_suffix('.sky.rgb').read_bytes();mask=p.with_suffix('.hudmask').read_bytes();assert len(mask)==480 and set(mask)<=set((0,1));assert len(final)==len(before)==len(sky)==3240*16*3
 eligible=0;mismatch=0;sky_equal=0
 for y in range(16):
  sy=int((648+y+.5)//13.5)-48
  for x in range(3240):
   sx=int((x+.5)//13.5)
   if mask[sy*240+sx]:
    eligible+=1;i=(y*3240+x)*3;mismatch+=final[i:i+3]!=before[i:i+3];sky_equal+=before[i:i+3]==sky[i:i+3]
 total+=eligible;bad+=mismatch;checks.append(dict(identity=rec['values'][:3],eligible=eligible,mismatches=mismatch,preworld_color_agreement=sky_equal))
assert len(checks)==96 and total>0
out=dict(result='PASS_HUD_PRESERVED_BACKGROUND' if bad==0 else 'FAIL_HUD_PRESERVED_BACKGROUND',eligible_pixels=total,mismatches=bad,checks=checks,scope='Actual shader finalRGB equals preHUD RGB on conservative mask. Sky/preworld agreement is color equality only; world provenance and scanout remain unproven.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],total,bad)
assert bad==0
