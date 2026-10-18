from pathlib import Path
p=Path('work/camera/test_texture_provenance.py');s=p.read_text().replace('candidate_sources=[]','candidate_sources=[];candidate_palettes=[]\nd.nf_live_palette_draw.argtypes=sig+[C.c_void_p]')
s=s.replace('candidate_sources.append(dict(serial=h[4]', '''used=sorted(set(indices));palettes=[]
   for draw in range(256):
    key=(C.c_uint32*3)();colors=C.create_string_buffer(512)
    if not d.nf_live_palette_draw(epoch,h[4],h[5],h[6],draw,key,colors):break
    selected=b''.join(colors.raw[index*2:index*2+2] for index in used)
    palettes.append(dict(draw=draw,key=list(key),all_hash=hashlib.sha256(colors.raw).hexdigest(),used_hash=hashlib.sha256(selected).hexdigest()))
    if key[0]==2 and key[1]==139937176 or h[4]==140 and draw==0:
     (root/'camera'/f'candidate-palette-{h[4]}.bin').write_bytes(colors.raw)
   assert palettes
   candidate_palettes.append(dict(serial=h[4],used_indices=len(used),distinct_all=len(set(x['all_hash'] for x in palettes)),distinct_used=len(set(x['used_hash'] for x in palettes)),draws=palettes))
   candidate_sources.append(dict(serial=h[4]''')
s=s.replace('candidate_sources=candidate_sources,scope=', 'candidate_sources=candidate_sources,candidate_palettes=candidate_palettes,scope=');p.write_text(s)
