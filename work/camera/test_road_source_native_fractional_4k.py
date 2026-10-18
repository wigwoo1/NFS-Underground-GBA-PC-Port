from pathlib import Path
import ctypes as C,json,math,random,struct,subprocess,re
p=Path('work/camera');dll=C.CDLL(str((p/'road-span-padding-segmented.dll').resolve()));span=dll.nf_road_span_transition_at;padfn=dll.nf_road_span_padding_segmented;span.argtypes=padfn.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];query=C.CDLL(str((p/'road-pair-query-continuous.dll').resolve())).nf_road_pair_query_continuous;query.argtypes=[C.c_double,C.c_double,C.c_void_p];uv=C.CDLL(str((p/'road-pair-uv-continuous.dll').resolve())).nf_road_pair_uv_continuous;uv.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_double,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());rng=random.Random(20201005);checks=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 cmd=road['command'];ring=[[v+(.25 if k in [0,1,3,4,5] else 0) for k,v in enumerate(r)] for r in road['clipped_ring']];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));rf=p/f'road-{cmd}-fractional-cache-ring.bin';rf.write_bytes(struct.pack('<I',len(ring))+b''.join(struct.pack('<8d',r[0],r[1],r[3],r[4],r[5],0,0,0) for r in ring));output=p/f'road-{cmd}-native-fractional-4k-output.bin';run=subprocess.run([str((p/'road-source-native-fractional-4k-probe.exe').resolve()),str(p/f'road-{cmd}-native-fractional-4k.frag'),str(p/f'road-{cmd}-index-cases-0.bin'),str(p/'road-correction-reciprocal.bin'),str(rf),str(p/f'road-{cmd}-index-texture.bin'),str(output),str(p/'road_source_span_padding_cache.frag')],capture_output=True,text=True,timeout=180);assert run.returncode==0,(cmd,run.returncode,run.stdout,run.stderr);pixels=output.read_bytes();assert len(pixels)==3840*2160*8;payload=(p/f'road-{cmd}-index-texture.bin').read_bytes();w,h=struct.unpack_from('<2I',payload);plane=payload[8:];nu,nv=road['normalization'];samples=[(rng.randrange(3840),rng.randrange(2160)) for _ in range(2000)]
 for row in range(2160):
  pad=(C.c_double*2)()
  if padfn(data,len(ring),(row+.5)/13.5,table,pad):
   for fraction in [.02,.25,.5,.75,.98]:samples.append((int(300+(pad[0]+2*pad[1]*fraction)*13.5),2159-row))
 covered=0
 for x,y in samples:
  if not 0<=x<3840:continue
  want=(-77,-77);scan=(2159-y+.5)/13.5;edges=(C.c_double*8)();pad=(C.c_double*2)()
  if 300<=x<3540 and span(data,len(ring),scan,table,edges) and padfn(data,len(ring),scan,table,pad):
   relative=(x+.5-300)/13.5-pad[0];coordinate=C.c_double()
   if query(pad[1],relative,C.byref(coordinate)):
    value=(C.c_double*2)();assert uv((C.c_double*3)(*edges[1:4]),(C.c_double*3)(*edges[5:8]),pad[1],coordinate.value,table,value);tx=2*math.floor(value[0]/(65536*nu)*(w/2))+(math.floor(relative)&1);ty=math.floor(value[1]/(65536*nv)*h);want=(plane[(ty%h)*w+tx%w],1);covered+=1
  actual=struct.unpack_from('<2i',pixels,(y*3840+x)*8);assert actual==want,(cmd,x,y,actual,want)
 checks.append(dict(command=cmd,queries=len(samples),covered_queries=covered,draw_finish_ms=[float(v) for v in re.findall(r'draw_finish_ms=([0-9.]+)',run.stdout)]))
report=dict(result='PASS',checks=checks,scope='Experimental two-pass native fractional 4K road index raster vs CPU candidate coverage/UV/lane policy. No doubledrow/spill endpoint visibility parity or fullscene/live motion/timing proof.');(p/'road-source-native-fractional-4k-tests.json').write_text(json.dumps(report,indent=2));print(report)
