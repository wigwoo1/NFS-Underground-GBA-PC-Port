from pathlib import Path
import ctypes as C,json,struct,subprocess
from road_lattice_sampler import sample_contributors,sample_contributor_buffer,compose_palette
p=Path('work/camera');table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());palettes=(p/'stable-road-display-palettes.bin').read_bytes();roads={r['command']:r for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};fixtures=[]
for cmd in (3,4):
 fixtures.append(next(f for f in json.loads((p/'world-road-ledger-axis-motion-audit.json').read_text())['checks'] if f['command']==cmd and not f['ledger_accepted']))
runs=[];spotchecks=0
for fixture in fixtures:
 cmd=fixture['command'];road=roads[cmd];ring=fixture['rejected_ring'];texture=(p/f'road-{cmd}-index-texture.bin').read_bytes();buffer=sample_contributor_buffer(ring,road['bounds'],texture,road['normalization'],table)
 for d in range(0,38400,97):
  assert buffer[d]==sample_contributors(ring,road['bounds'],texture,road['normalization'],table,d),(cmd,d);spotchecks+=1
 cases=[];mixed=sum(len({c['index'] for c in v})>1 for v in buffer);partial=sum(0<sum(c['weight'] for c in v)<1 for v in buffer)
 for d,contributors in enumerate(buffer):
  color=compose_palette(contributors,palettes[d//240*512:(d//240+1)*512]);r,g,b=map(round,color[:3]);cases.append([d]+[0]*7+[r|(g<<8)|(b<<16),round(color[3]*65536)])
 ringfile=p/f'lattice-full-{cmd}-ring.bin';ringfile.write_bytes(struct.pack('<I',len(ring))+b''.join(struct.pack('<8d',r[0],r[1],r[3],r[4],r[5],0,0,0) for r in ring))
 for batch,start in enumerate(range(0,len(cases),14000)):
  chunk=cases[start:start+14000];casefile=p/f'lattice-full-{cmd}-{batch}-cases.bin';casefile.write_bytes(struct.pack('<I',len(chunk))+b''.join(struct.pack('<10i',*c) for c in chunk));out=p/f'lattice-full-{cmd}-{batch}-output.bin'
  run=subprocess.run([str((p/'road-lattice-color-probe.exe').resolve()),str(p/'road_lattice_color.frag'),str(casefile),str(p/'road-correction-reciprocal.bin'),str(ringfile),str(p/f'road-{cmd}-index-texture.bin'),str(p/'stable-road-display-palettes.bin'),','.join(str(int(v)) for v in [road['bounds'][2],road['bounds'][3],*road['normalization']]),str(out)],capture_output=True,text=True,timeout=180)
  runs.append(dict(command=cmd,batch=batch,cases=len(chunk),mixed_buffer_destinations=mixed,partial_buffer_destinations=partial,code=run.returncode,output=run.stdout,stderr=run.stderr));print(runs[-1],flush=True)
  if run.returncode:break
 if runs[-1]['code']:break
report=dict(result='PASS' if len(runs)==6 and all(r['code']==0 for r in runs) else 'FAIL',oracle_spotchecks=spotchecks,runs=runs,scope='Two complete fractional source-viewport road buffers. Cached CPU oracle reuses corner ledger/row/pair evaluations; spot checked against query-local independent API. GPU computes geometry/winners/UV/index/color. Not continuous horizontal motion, native4K fullscene or gameplay timing proof.')
(p/'road-lattice-full-color-gpu-tests.json').write_text(json.dumps(report,indent=2));assert report['result']=='PASS',report
