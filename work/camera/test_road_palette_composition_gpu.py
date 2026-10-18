from pathlib import Path
import ctypes as C,json,struct,subprocess
from road_lattice_sampler import sample_contributors,compose_palette
p=Path('work/camera');table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());roads={r['command']:r for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};checks=[];palettes=(p/'stable-road-display-palettes.bin').read_bytes();color_checks=0
cases=[];maximum_weight_error=0.
def add_case(contributors,destination):
 global maximum_weight_error
 assert len(contributors)<=4
 addresses=[];weights=[];totals=[0,0,0]
 for c in contributors:
  address=(destination//240)*256+c['index'];weight=round(c['weight']*65536);maximum_weight_error=max(maximum_weight_error,abs(weight/65536-c['weight']));word=struct.unpack_from('<H',palettes,address*2)[0];addresses.append(address);weights.append(weight)
  for channel in range(3):
   component=(word>>(channel*5))&31;totals[channel]+=weight*((component<<3)|(component>>2))
 alpha=sum(weights);rgb=[round(v/65536) for v in totals];packed=rgb[0]|rgb[1]<<8|rgb[2]<<16
 cases.append(addresses+[0]*(4-len(addresses))+weights+[0]*(4-len(weights))+[packed,alpha])
for row in range(160):
 for index in range(256):add_case([dict(index=index,weight=1.)],row*240)
add_case([],0)

for cmd,road in roads.items():
 payload=(p/f'stable-road-{cmd}-all-original-samples.bin').read_bytes();immutable={struct.unpack_from('<IB',payload,i)[0]:struct.unpack_from('<IB',payload,i)[1] for i in range(0,len(payload),5)};destinations=sorted(immutable)[::max(1,len(immutable)//32)]
 for destination in destinations:
  result=sample_contributors(road['clipped_ring'],road['bounds'],(p/f'road-{cmd}-index-texture.bin').read_bytes(),road['normalization'],table,destination);add_case(result,destination);assert len(result)==1 and result[0]['weight']==1 and result[0]['index']==immutable[destination],(cmd,destination,result)
  color=compose_palette(result,palettes[(destination//240)*512:(destination//240+1)*512]);assert color[3]==1;word=struct.unpack_from('<H',palettes,(destination//240)*512+immutable[destination]*2)[0];assert color[:3]==tuple(((((word>>(k*5))&31)<<3)|(((word>>(k*5))&31)>>2)) for k in range(3));color_checks+=1
 checks.append(dict(command=cmd,original_index_queries=len(destinations)))
for fixture in json.loads((p/'world-road-ledger-axis-motion-audit.json').read_text())['checks']:
 if fixture['ledger_accepted']:continue
 ring=fixture['rejected_ring'];road=roads[fixture['command']];candidate=C.CDLL(str((p/'road-row-lattice-coverage.dll').resolve())).nf_road_row_lattice_coverage;candidate.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));moments=(C.c_double*(38400*3))();assert candidate(data,len(ring),(C.c_uint16*4)(*road['bounds']),table,moments);covered=[i for i in range(38400) if moments[i*3+2]>0];mixed=0;queries=0
 for destination in covered[::max(1,len(covered)//32)]:
  result=sample_contributors(ring,road['bounds'],(p/f"road-{fixture['command']}-index-texture.bin").read_bytes(),road['normalization'],table,destination);add_case(result,destination);assert abs(sum(r['weight'] for r in result)-moments[destination*3+2])<1e-10;assert all(0<=r['index']<=255 for r in result);color=compose_palette(result,palettes[(destination//240)*512:(destination//240+1)*512]);assert abs(color[3]-moments[destination*3+2])<1e-10;assert all(0<=v<=255 for v in color[:3]);color_checks+=1;queries+=1;mixed+=len({r['index'] for r in result})>1
 checks.append(dict(command=fixture['command'],axis=fixture['world_axis'],translation=fixture['world_translation'],queries=queries,mixed_index_destinations=mixed))
words=struct.unpack('<40960H',palettes);palettefile=p/'road-display-palettes-u32.bin';palettefile.write_bytes(struct.pack('<40960I',*words));runs=[]
for batch,start in enumerate(range(0,len(cases),14000)):
 chunk=cases[start:start+14000];path=p/f'road-palette-composition-cases-{batch}.bin';path.write_bytes(struct.pack('<I',len(chunk))+b''.join(struct.pack('<10i',*case) for case in chunk));run=subprocess.run([str((p/'road-palette-composition-probe.exe').resolve()),str(p/'road_palette_composition.frag'),str(path),str(palettefile)],capture_output=True,text=True,timeout=120);assert run.returncode==0,(run.returncode,run.stdout,run.stderr);runs.append(dict(cases=len(chunk),output=run.stdout))
report=dict(result='PASS',gpu_cases=len(cases),exhaustive_retained_palette_entries=40960,actual_geometry_sampled_contributor_cases=len(cases)-40961,maximum_supplied_weight_quantization_error=maximum_weight_error,runs=runs,scope='Actual GPU per-contributor palette-address lookup, original bit-replicated RGB and premultiplied color sum against independent integer arithmetic. CPU supplies sampled indices and fixed16 weights; not GPU geometry/UV, fullnative4K, motion or gameplay timing proof.')
(p/'road-palette-composition-gpu-tests.json').write_text(json.dumps(report,indent=2));print(report)
