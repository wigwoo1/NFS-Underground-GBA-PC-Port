from pathlib import Path
import ctypes as C,json,struct,subprocess,math
p=Path('work/camera');fn=C.CDLL(str((p/'road-span-transition-at.dll').resolve())).nf_road_span_transition_at;fn.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[];padding=C.CDLL(str((p/'road-span-padding-segmented.dll').resolve())).nf_road_span_padding_segmented;padding.argtypes=fn.argtypes;query=C.CDLL(str((p/'road-pair-query-continuous.dll').resolve())).nf_road_pair_query_continuous;query.argtypes=[C.c_double,C.c_double,C.c_void_p];uv=C.CDLL(str((p/'road-pair-uv-continuous.dll').resolve())).nf_road_pair_uv_continuous;uv.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_double,C.c_void_p,C.c_void_p]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 cmd=road['command'];ring=[[v+(.25 if k in [0,1,3,4,5] else 0) for k,v in enumerate(r)] for r in road['clipped_ring']];rf=p/f'road-{cmd}-fractional-cache-ring.bin';rf.write_bytes(struct.pack('<I',len(ring))+b''.join(struct.pack('<8d',r[0],r[1],r[3],r[4],r[5],0,0,0) for r in ring));data=(C.c_double*(len(ring)*6))(*(v for row in ring for v in row));output=p/f'road-{cmd}-native-index-cache-output.bin'
 run=subprocess.run([str((p/'road-source-native-index-cache-probe.exe').resolve()),str(p/f'road-{cmd}-native-index-cache.frag'),str(p/f'road-{cmd}-span-gpu-cases.bin'),str(p/'road-correction-reciprocal.bin'),str(rf),str(p/f'road-{cmd}-index-texture.bin'),str(output)],capture_output=True,text=True,timeout=60)
 assert run.returncode==0,(run.returncode,run.stdout,run.stderr)
 actual=list(struct.iter_unpack('<14d',output.read_bytes()));assert len(actual)==2160
 for row in range(2160):
  out=(C.c_double*8)();ok=fn(data,len(ring),(row+.5)/13.5,table,out)
  for side in range(2):
   expected=tuple(out[side*4+k] for k in range(4)) if ok else (-77,)*4
   assert all(abs(a-b)<1e-8 for a,b in zip(actual[row][side*4:side*4+4],expected)),(cmd,row,side,actual[row][side*4:side*4+4],expected)
 for row in range(2160):
  out=(C.c_double*2)(-77,-77);padding(data,len(ring),(row+.5)/13.5,table,out);assert all(abs(a-b)<1e-8 for a,b in zip(actual[row][8:10],out)),(cmd,row,actual[row][8:10],list(out))
 for row in range(2160):
  edges=(C.c_double*8)();out=(C.c_double*2)(-77,-77);pad=(C.c_double*2)()
  if fn(data,len(ring),(row+.5)/13.5,table,edges) and padding(data,len(ring),(row+.5)/13.5,table,pad):
   coordinate=C.c_double();assert query(pad[1],2*pad[1]*((row%32)+.5)/32,C.byref(coordinate));assert uv((C.c_double*3)(*edges[1:4]),(C.c_double*3)(*edges[5:8]),pad[1],coordinate.value,table,out)
  assert all(abs(a-b)<1e-6 for a,b in zip(actual[row][10:12],out)),(cmd,row,actual[row][10:12],list(out))
 payload=(p/f'road-{cmd}-index-texture.bin').read_bytes();w,h=struct.unpack_from('<2I',payload);plane=payload[8:];nu,nv=road['normalization']
 for row in range(2160):
  samples=actual[row];want=(-77,-77)
  reference_edges=(C.c_double*8)();reference_pad=(C.c_double*2)()
  reference_valid=fn(data,len(ring),(row+.5)/13.5,table,reference_edges) and padding(data,len(ring),(row+.5)/13.5,table,reference_pad)
  if reference_valid:
   # Use independent C UV result for index/address oracle.
   edges=(C.c_double*8)();pad=(C.c_double*2)();sample=(C.c_double*2)();coordinate=C.c_double();assert fn(data,len(ring),(row+.5)/13.5,table,edges) and padding(data,len(ring),(row+.5)/13.5,table,pad)
   relative=2*pad[1]*((row%32)+.5)/32;assert query(pad[1],relative,C.byref(coordinate));assert uv((C.c_double*3)(*edges[1:4]),(C.c_double*3)(*edges[5:8]),pad[1],coordinate.value,table,sample)
   tx=2*math.floor(sample[0]/(65536*nu)*(w/2))+(math.floor(relative)&1);ty=math.floor(sample[1]/(65536*nv)*h);want=(plane[(ty%h)*w+tx%w],1)
  assert tuple(samples[12:14])==want,(cmd,row,samples[12:14],want)
 checks.append(dict(command=cmd,rows=2160,endpoints=4320,output=run.stdout))
report=dict(result='PASS',checks=checks,scope='GPU row prepass readback versus C corrected span: native4K viewport pixelcenter rows, packed full-double X/UVQ with fractional source geometry and attributes. Diagnostic only; two-pass renderer and timing remain pending.');(p/'road-source-native-index-cache-tests.json').write_text(json.dumps(report,indent=2));print(report)
