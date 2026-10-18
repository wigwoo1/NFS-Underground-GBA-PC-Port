import csv,struct,json
from pathlib import Path
p=Path(__file__).resolve().parent/'prototype-runs';done=max(p.glob('*-bitmap-blits.csv.glyphs-done.csv'),key=lambda p:p.stat().st_mtime);entries=list(csv.DictReader(done.open()));base=done.with_name(done.name.removesuffix('.glyphs-done.csv'));raw=Path(str(base)+'.glyphs.bin').read_bytes();actual=list(csv.DictReader(base.open()));offset=0;writes=[];calls=0
while offset<len(raw):
 h=struct.unpack_from('<16I',raw,offset);offset+=64;frame,pc,descriptor,glyph,dest,stride,pal,w,height,dw,flags,transparent,source,size,lr,target=h;asset=raw[offset:offset+size];offset+=size;e=entries[calls];assert int(e['index'])==calls and int(e['begin'])==frame and int(e['destination'],16)==dest;begin,end=int(e['begin']),int(e['end']);assert begin<=end<=begin+1;calls+=1
 if flags&1:
  for y in range(height):
   for x in range(dw):
    i=y*w+x
    if asset[i]!=transparent:writes.append((begin,end,dest+y*stride+x,source+i,asset[i],pal))
assert len(writes)==len(actual)
for a,b in zip(writes,actual):
 assert a[0]<=int(b['refresh'])<=a[1]
 assert a[2:]==(int(b['pixel_address'],16),int(b['source'],16),int(b['source_index']),int(b['palette_offset']))
r={'result':'PASS','completed_calls':calls,'original_writes_within_actual_call_interval':len(actual),'cross_refresh_calls':sum(e['begin']!=e['end'] for e in entries),'scope':'actual glyph return completion interval and asset/write order; per-scanline partial visibility not yet verified'};done.with_suffix('.verification.json').write_text(json.dumps(r,indent=2));print(r)
