from pathlib import Path
import ctypes as C,json,struct,subprocess
from road_lattice_sampler import sample_contributors,compose_palette
p=Path('work/camera');table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());palettes=(p/'stable-road-display-palettes.bin').read_bytes();roads={r['command']:r for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']}
fixtures=[dict(command=c,ring=r['clipped_ring'],label='original') for c,r in roads.items()]
fixtures += [dict(command=f['command'],ring=f['rejected_ring'],label=str(i)) for i,f in enumerate(json.loads((p/'world-road-ledger-axis-motion-audit.json').read_text())['checks']) if not f['ledger_accepted']]
candidate=C.CDLL(str((p/'road-row-lattice-coverage.dll').resolve())).nf_road_row_lattice_coverage;candidate.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p]
runs=[]
for f in fixtures:
 cmd=f['command'];road=roads[cmd];ring=f['ring'];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));moments=(C.c_double*(38400*3))();assert candidate(data,len(ring),(C.c_uint16*4)(*road['bounds']),table,moments)
 covered=[i for i in range(38400) if moments[i*3+2]>0];destinations=sorted(set(covered[::max(1,len(covered)//32)]+[0,239,38399]+[i for i in covered if moments[i*3+2]<1][:16]));cases=[];mixed=0
 for d in destinations:
  contributors=sample_contributors(ring,road['bounds'],(p/f'road-{cmd}-index-texture.bin').read_bytes(),road['normalization'],table,d);mixed+=len({c['index'] for c in contributors})>1
  rgb=compose_palette(contributors,palettes[d//240*512:(d//240+1)*512]);r,g,b=map(round,rgb[:3]);cases.append([d]+[0]*7+[r|(g<<8)|(b<<16),round(rgb[3]*65536)])
 label=f'{cmd}-{f["label"]}';casefile=p/f'lattice-color-{label}-cases.bin';casefile.write_bytes(struct.pack('<I',len(cases))+b''.join(struct.pack('<10i',*c) for c in cases));ringfile=p/f'lattice-color-{label}-ring.bin';ringfile.write_bytes(struct.pack('<I',len(ring))+b''.join(struct.pack('<8d',r[0],r[1],r[3],r[4],r[5],0,0,0) for r in ring));out=p/f'lattice-color-{label}-output.bin'
 run=subprocess.run([str((p/'road-lattice-color-probe.exe').resolve()),str(p/'road_lattice_color.frag'),str(casefile),str(p/'road-correction-reciprocal.bin'),str(ringfile),str(p/f'road-{cmd}-index-texture.bin'),str(p/'stable-road-display-palettes.bin'),','.join(str(int(v)) for v in [road['bounds'][2],road['bounds'][3],*road['normalization']]),str(out)],capture_output=True,text=True,timeout=120)
 runs.append(dict(label=label,cases=len(cases),mixed=mixed,code=run.returncode,output=run.stdout,stderr=run.stderr));print(runs[-1],flush=True)
 if run.returncode:break
report=dict(result='PASS' if len(runs)==len(fixtures) and all(r['code']==0 for r in runs) else 'FAIL',runs=runs,scope='GPU source corner geometry/winner/continuous UV/index/palette blending against independent CPU sampler. Sparse diagnostic queries; horizontal world-motion discontinuities remain, no full-scene 4K or gameplay timing claim.')
(p/'road-lattice-color-gpu-tests.json').write_text(json.dumps(report,indent=2));assert report['result']=='PASS',report

