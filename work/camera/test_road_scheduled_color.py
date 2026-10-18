from pathlib import Path
import ctypes as C,json,struct,subprocess,math
p=Path('work/camera');dll=C.CDLL(str((p/'road-span-padding-segmented.dll').resolve()));span=dll.nf_road_span_transition_at;padfn=dll.nf_road_span_padding_segmented;span.argtypes=padfn.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];uv=C.CDLL(str((p/'road-pair-uv-continuous.dll').resolve())).nf_road_pair_uv_continuous;uv.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_double,C.c_void_p,C.c_void_p];query=C.CDLL(str((p/'road-source-query-coverage.dll').resolve())).nf_road_source_query_coverage;query.argtypes=[C.c_void_p,C.c_double,C.c_double,C.c_void_p];pairfn=C.CDLL(str((p/'road-pair-query-continuous.dll').resolve())).nf_road_pair_query_continuous;pairfn.argtypes=[C.c_double,C.c_double,C.c_void_p];ledger=C.CDLL(str((p/'road-write-ledger.dll').resolve())).nf_road_write_ledger;ledger.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[]
palettes=(p/'stable-road-display-palettes.bin').read_bytes()
def color(index,row,coverage):
 word=struct.unpack_from('<H',palettes,row*512+index*2)[0];values=[(word>>(k*5))&31 for k in range(3)];return tuple(round(((v<<3)|(v>>2))*coverage) for v in values)+(round(coverage*65536),)

for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 cmd=road['command'];ring=road['clipped_ring'];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));bounds=(C.c_uint16*4)(*road['bounds']);writes=(C.c_int16*(38400*2))();assert ledger(data,len(ring),bounds,table,writes);payload=(p/f'road-{cmd}-index-texture.bin').read_bytes();w,h=struct.unpack_from('<2I',payload);plane=payload[8:];nu,nv=road['normalization'];original=(p/f'stable-road-{cmd}-all-original-samples.bin').read_bytes();immutable={struct.unpack_from('<IB',original,i)[0]:struct.unpack_from('<IB',original,i)[1] for i in range(0,len(original),5)}
 for offset in [0,.25]:
  shader=p/f'road-{cmd}-scheduled-color-{offset}.frag';shader.write_text((p/f'road-{cmd}-scheduled-color.frag').read_text().replace('QUERY_OFFSET',str(offset)));output=p/f'road-{cmd}-scheduled-color-{offset}-output.bin';run=subprocess.run([str((p/'road-scheduled-color-probe.exe').resolve()),str(shader),str(p/f'road-{cmd}-index-cases-0.bin'),str(p/'road-correction-reciprocal.bin'),str(p/f'road-{cmd}-span-gpu-ring.bin'),str(p/f'road-{cmd}-index-texture.bin'),str(output),str(p/'road_source_span_cache_double.frag'),str(p/f'road-{cmd}-double-coverage-cache.frag'),str(p/'stable-road-display-palettes.bin')],capture_output=True,text=True,timeout=180);assert run.returncode==0,(run.returncode,run.stdout,run.stderr);actual=list(struct.iter_unpack('<4i',output.read_bytes()));assert len(actual)==38400;unresolved=0;covered=0
  for i,value in enumerate(actual):
   row,x=divmod(i,240);source=(C.c_double*3)();want=(-77,)*4
   if query(writes,x+offset,row+offset,source):
    edges=(C.c_double*8)();pad=(C.c_double*2)();coordinate=C.c_double()
    if span(data,len(ring),source[0],table,edges) and padfn(data,len(ring),source[0],table,pad) and pairfn(pad[1],source[1]-pad[0],C.byref(coordinate)):
     sample=(C.c_double*2)();assert uv((C.c_double*3)(*edges[1:4]),(C.c_double*3)(*edges[5:8]),pad[1],coordinate.value,table,sample);tx=2*math.floor(sample[0]/(65536*nu)*(w/2))+(math.floor(source[1]-pad[0])&1);ty=math.floor(sample[1]/(65536*nv)*h);want=color(plane[(ty%h)*w+tx%w],row,source[2]);covered+=1
    else:unresolved+=1
   assert value==want,(cmd,offset,i,value,want)
   if offset==0:assert value==(color(immutable[i],row,1) if i in immutable else (-77,)*4),(cmd,i,value)
  checks.append(dict(command=cmd,offset=offset,exact_queries=38400,covered=covered,unresolved_source_queries=unresolved))
report=dict(result='PASS',checks=checks,scope='Actual GPU geometry writewinner->weighted sourcequery->segmentedpadding->pairUV->original index->proven scanlinepalette->premultiplied RGB, integer originalindex/palette oracle exact andquarterphase CPU candidate parity. Any unresolved positivecoverage queries block finaladoption; not4K/fullscene/live motion.');(p/'road-scheduled-color-tests.json').write_text(json.dumps(report,indent=2));print(report)
