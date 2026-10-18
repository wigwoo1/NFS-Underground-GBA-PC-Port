from pathlib import Path
import ctypes as C,json,struct
from road_lattice_sampler import sample_contributors,compose_palette
p=Path('work/camera');table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());roads={r['command']:r for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};checks=[];palettes=(p/'stable-road-display-palettes.bin').read_bytes();color_checks=0
for cmd,road in roads.items():
 payload=(p/f'stable-road-{cmd}-all-original-samples.bin').read_bytes();immutable={struct.unpack_from('<IB',payload,i)[0]:struct.unpack_from('<IB',payload,i)[1] for i in range(0,len(payload),5)};destinations=sorted(immutable)[::max(1,len(immutable)//32)]
 for destination in destinations:
  result=sample_contributors(road['clipped_ring'],road['bounds'],(p/f'road-{cmd}-index-texture.bin').read_bytes(),road['normalization'],table,destination);assert len(result)==1 and result[0]['weight']==1 and result[0]['index']==immutable[destination],(cmd,destination,result)
  color=compose_palette(result,palettes[(destination//240)*512:(destination//240+1)*512]);assert color[3]==1;word=struct.unpack_from('<H',palettes,(destination//240)*512+immutable[destination]*2)[0];assert color[:3]==tuple(((((word>>(k*5))&31)<<3)|(((word>>(k*5))&31)>>2)) for k in range(3));color_checks+=1
 checks.append(dict(command=cmd,original_index_queries=len(destinations)))
for fixture in json.loads((p/'world-road-ledger-axis-motion-audit.json').read_text())['checks']:
 if fixture['ledger_accepted']:continue
 ring=fixture['rejected_ring'];road=roads[fixture['command']];candidate=C.CDLL(str((p/'road-row-lattice-coverage.dll').resolve())).nf_road_row_lattice_coverage;candidate.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));moments=(C.c_double*(38400*3))();assert candidate(data,len(ring),(C.c_uint16*4)(*road['bounds']),table,moments);covered=[i for i in range(38400) if moments[i*3+2]>0];mixed=0;queries=0
 for destination in covered[::max(1,len(covered)//32)]:
  result=sample_contributors(ring,road['bounds'],(p/f"road-{fixture['command']}-index-texture.bin").read_bytes(),road['normalization'],table,destination);assert abs(sum(r['weight'] for r in result)-moments[destination*3+2])<1e-10;assert all(0<=r['index']<=255 for r in result);color=compose_palette(result,palettes[(destination//240)*512:(destination//240+1)*512]);assert abs(color[3]-moments[destination*3+2])<1e-10;assert all(0<=v<=255 for v in color[:3]);color_checks+=1;queries+=1;mixed+=len({r['index'] for r in result})>1
 checks.append(dict(command=fixture['command'],axis=fixture['world_axis'],translation=fixture['world_translation'],queries=queries,mixed_index_destinations=mixed))
report=dict(result='PASS',palette_color_queries=color_checks,checks=checks,scope='CPU per-contributor corner geometry/winner/continuousUV/original paired texture lane sampling. Original immutable index spot checks; fractional mixtures retain separate indices/weights. Per-destination scanline palette lookup and premultiplied RGB/coverage composition connected to proven retained display8780 banks. Temporal horizontal repair, full-screen color fidelity and GPU/live integration remain unproven.');(p/'road-lattice-palette-composition-tests.json').write_text(json.dumps(report,indent=2));print(report)
