"""Audit retained scanline palettes against native indexed model material colors.

This is a color-state audit, not a screen polygon correspondence test. Texture
texels are counted irrespective of coverage; mismatch is not a pixel error count.
"""
import hashlib,json,struct
from collections import Counter
from pathlib import Path

p=Path(__file__).resolve().parent
prefix=p/'prototype-runs/threaded-prepared-2d9f8b417e1943be80cb86a65dc8f12d'
checks=[]
for frame in range(1,17):
    base=Path(str(prefix)+f'-dense-{frame:02}')
    hud=Path(str(base)+'-owned-hud.bin').read_bytes()
    packet=Path(str(base)+'-native-scene.bin').read_bytes()
    assert len(hud)==160*34944
    palettes=[hud[y*34944+32896:y*34944+32896+512] for y in range(160)]
    headers=[struct.unpack_from('<2I',hud,y*34944) for y in range(160)]
    assert all(row==y for y,(_,row) in enumerate(headers))
    assert len({refresh for refresh,_ in headers})==1
    sections={tag:packet[off:off+size] for tag,off,size in
              (struct.unpack_from('<3I',packet,32+j*12) for j in range(5))}
    models=sections[1]
    assert models[:4] in (b'NML1',b'NFM2')
    count=struct.unpack_from('<I',models,4)[0] if models[:4]==b'NML1' else 1
    model_checks=[]
    for j in range(count):
        off,size=struct.unpack_from('<2I',models,8+j*8) if models[:4]==b'NML1' else (0,len(models))
        m=models[off:off+size]
        magic,vertices,faces,corners,width,height=struct.unpack_from('<6I',m)
        assert magic==0x324d464e
        tex=160+vertices*24+faces+corners*18
        pixels=width*height
        rgba=m[tex:tex+pixels*4]
        trailer=tex+pixels*4
        assert m[trailer:trailer+4]==b'NZI1'
        assert struct.unpack_from('<3I',m,trailer+4)==(width,height,0)
        indices=m[trailer+16:trailer+16+pixels]
        assert len(indices)==pixels and len(rgba)==pixels*4
        texels=Counter((index,rgba[k*4:k*4+3]) for k,index in enumerate(indices) if index)
        per_row=[]
        bank_results={}
        mismatched_indices=set()
        for y in range(24,144):
            if palettes[y] in bank_results:
                per_row.append(bank_results[palettes[y]])
                continue
            bank=struct.unpack('<256H',palettes[y])
            mismatch=0
            for (index,baked),frequency in texels.items():
                color=bank[index]
                rgb=bytes(((color>>(c*5))&31)*255//31 for c in range(3))
                if baked!=rgb:
                    mismatch+=frequency
                    mismatched_indices.add(index)
            per_row.append(mismatch)
            bank_results[palettes[y]]=mismatch
        model_checks.append(dict(model=j,nonzero_texels=sum(bool(i) for i in indices),
                                 mismatching_texels_min=min(per_row),mismatching_texels_max=max(per_row),
                                 rows_with_mismatch=sum(bool(n) for n in per_row),mismatched_indices=sorted(mismatched_indices),
                                 focus_colors={i:dict(baked_rgb=sorted({tuple(rgb) for index,rgb in texels if index==i}),
                                     display_bgr555=sorted({struct.unpack_from('<H',palettes[y],i*2)[0] for y in range(24,144)})) for i in (192,223)}))
    spans=[]
    for y,bank in enumerate(palettes):
        digest=hashlib.sha256(bank).hexdigest()
        if spans and spans[-1]['sha256']==digest: spans[-1]['end_row_exclusive']=y+1
        else: spans.append(dict(begin_row=y,end_row_exclusive=y+1,sha256=digest))
    checks.append(dict(frame=frame,refresh=headers[0][0],hud_sha256=hashlib.sha256(hud).hexdigest(),
                       packet_sha256=hashlib.sha256(packet).hexdigest(),palette_spans=spans,models=model_checks))
report=dict(result='AUDITED',frames=checks,
            scope='Owned BG palette bytes and indexed model texture RGB; all nonzero texels compared at each world scanline 24..143. No coverage, original output index, lighting, GPU fidelity or 60fps proof. No live behavior changed.')
out=p/'owned-display-palette-audit.json'
out.write_text(json.dumps(report,indent=2))
print(json.dumps(dict(result=report['result'],frames=len(checks),palette_span_counts=[len(c['palette_spans']) for c in checks],models=[c['models'] for c in checks],report=str(out))))
