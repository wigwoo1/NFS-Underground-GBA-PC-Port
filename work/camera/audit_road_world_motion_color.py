from pathlib import Path
import ctypes as C,json,struct,subprocess
from road_lattice_sampler import sample_contributors,compose_palette
p=Path('work/camera');table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());palettes=(p/'stable-road-display-palettes.bin').read_bytes();roads={r['command']:r for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};checks=[]
failures=[f for f in json.loads((p/'world-row-lattice-adaptive-motion.json').read_text())['checks'] if f['source_rings']]
for number,f in enumerate(failures):
 cmd=f['command'];road=roads[cmd];d=f['pixel'];row,x=divmod(d,240);destinations=[y*240+xx for y in range(max(0,row-2),min(160,row+3)) for xx in range(max(0,x-3),min(240,x+4))];states=[];runs=[]
 for side,ring in enumerate(f['source_rings']):
  samples=[];cases=[]
  for destination in destinations:
   contributors=sample_contributors(ring,road['bounds'],(p/f'road-{cmd}-index-texture.bin').read_bytes(),road['normalization'],table,destination);color=compose_palette(contributors,palettes[destination//240*512:(destination//240+1)*512]);r,g,b=map(round,color[:3]);cases.append([destination]+[0]*7+[r|(g<<8)|(b<<16),round(color[3]*65536)]);samples.append(dict(destination=destination,contributors=contributors,color=color))
  states.append(samples);label=f'{number}-{side}';casefile=p/f'motion-color-{label}-cases.bin';casefile.write_bytes(struct.pack('<I',len(cases))+b''.join(struct.pack('<10i',*c) for c in cases));ringfile=p/f'motion-color-{label}-ring.bin';ringfile.write_bytes(struct.pack('<I',len(ring))+b''.join(struct.pack('<8d',r[0],r[1],r[3],r[4],r[5],0,0,0) for r in ring));out=p/f'motion-color-{label}-output.bin'
  run=subprocess.run([str((p/'road-lattice-color-probe.exe').resolve()),str(p/'road_lattice_color.frag'),str(casefile),str(p/'road-correction-reciprocal.bin'),str(ringfile),str(p/f'road-{cmd}-index-texture.bin'),str(p/'stable-road-display-palettes.bin'),','.join(str(int(v)) for v in [road['bounds'][2],road['bounds'][3],*road['normalization']]),str(out)],capture_output=True,text=True,timeout=120);assert run.returncode==0,(number,side,run.stdout,run.stderr);runs.append(dict(cases=len(cases),output=run.stdout))
 changes=[]
 for a,b in zip(*states):
  alpha_gap=abs(a['color'][3]-b['color'][3]);rgb_gap=max(abs(u-v) for u,v in zip(a['color'][:3],b['color'][:3]));signature=lambda s:[(c['mask'],c['source_row'],c['source_x'],c['index']) for c in s['contributors']]
  if alpha_gap>.001 or rgb_gap>.01:changes.append(dict(destination=a['destination'],alpha_gap=alpha_gap,rgb_gap=rgb_gap,winner_or_index_changed=signature(a)!=signature(b),before=a,after=b))
 assert changes,'Expected proven coverage failure missing from color audit'
 check=dict(command=cmd,axis=f['axis'],world_bracket=f['bracket'],world_bracket_width=f['bracket_width'],original_failing_pixel=d,gpu_runs=runs,changed_pixels=changes);checks.append(check);print(dict(command=cmd,axis=f['axis'],changed=len(changes),max_alpha_gap=max(c['alpha_gap'] for c in changes),max_rgb_gap=max(c['rgb_gap'] for c in changes)),flush=True)
report=dict(result='GPU_PARITY_PASS_MOTION_REJECTED',checks=checks,scope='Actual before/after world-derived source rings at seven previously localized tiny motion brackets; local35pixel neighborhoods, GPU color parity independently checked. Coverage/color jumps persist despite per-corner texture blending. Not a temporal policy fix or fullscene proof.')
(p/'road-world-motion-color-audit.json').write_text(json.dumps(report,indent=2));print(report['result'])
