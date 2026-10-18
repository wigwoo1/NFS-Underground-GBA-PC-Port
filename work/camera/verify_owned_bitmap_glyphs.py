from pathlib import Path
import struct,csv,json
p=Path(__file__).resolve().parent/'prototype-runs';base=max(p.glob('*-bitmap-blits.csv.glyphs.bin'),key=lambda x:x.stat().st_mtime);raw=base.read_bytes();offset=0;predicted=[];calls=0
while offset<len(raw):
 h=struct.unpack_from('<16I',raw,offset);offset+=64;frame,pc,descriptor,glyph,dest,stride,pal,width,height,draw,flags,transparent,source,size,lr,target=h;asset=raw[offset:offset+size];offset+=size;assert len(asset)==size==width*height;calls+=1
 if flags&1:
  for y in range(height):
   for x in range(draw):
    index=asset[y*width+x]
    if index!=transparent:predicted.append((frame,dest+y*stride+x,source+y*width+x,index,pal))
actual=[]
for r in csv.DictReader(base.with_name(base.name.removesuffix('.glyphs.bin')).open()):actual.append((int(r['refresh']),int(r['pixel_address'],16),int(r['source'],16),int(r['source_index']),int(r['palette_offset'])))
report={'result':'PASS' if predicted==actual else 'FAIL','owned_glyph_calls':calls,'predicted_writes':len(predicted),'original_writes':len(actual),'exact_ordered_writes':predicted==actual,'scope':'owned descriptor/asset reconstruction vs actual transparent glyph original write journal'}
if predicted!=actual:
 report['first_mismatch']=next(({'ordinal':i,'predicted':a,'actual':b} for i,(a,b) in enumerate(zip(predicted,actual)) if a!=b),None)
report['exact_ordered_asset_destination_palette']=len(predicted)==len(actual) and all(a[1:]==b[1:] for a,b in zip(predicted,actual))
report['write_refresh_offsets']=sorted({b[0]-a[0] for a,b in zip(predicted,actual)})
report['result']='PASS_GEOMETRY' if report['exact_ordered_asset_destination_palette'] else 'FAIL'
print(report);base.with_suffix('.verification.json').write_text(json.dumps(report,indent=2));assert report['exact_ordered_asset_destination_palette']
