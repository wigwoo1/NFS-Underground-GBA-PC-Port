from pathlib import Path
import ctypes as C,json,struct,subprocess,math,os
offset=float(os.environ.get('NF_ROAD_PHASE','.25'));assert math.isfinite(offset) and -1<=offset<=1
p=Path('work/camera');span=C.CDLL(str((p/'road-span-transition-at.dll').resolve())).nf_road_span_transition_at;span.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];uv=C.CDLL(str((p/'road-pair-uv-continuous.dll').resolve())).nf_road_pair_uv_continuous;uv.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_double,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 cmd=road['command'];ring=[[v+(offset if k in [0,1,3,4,5] else 0) for k,v in enumerate(r)] for r in road['clipped_ring']];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));expected=[(-77,-77)]*38400;payload=(p/f'road-{cmd}-index-texture.bin').read_bytes();w,h=struct.unpack_from('<2I',payload);plane=payload[8:];nu,nv=road['normalization'];scan=int(max(0,min(r[1] for r in ring)));doubled=False;covered=0
 while scan<=road['bounds'][3]:
  edges=(C.c_double*8)()
  if span(data,len(ring),scan,table,edges):
   a=list(edges[:4]);b=list(edges[4:]);doubled=doubled or a[3]>49152;start=math.floor(a[0]/2)*2;width=math.floor((b[0]-a[0])/2)+2
   for pair in range(width):
    sample=(C.c_double*2)();assert uv((C.c_double*3)(*a[1:]),(C.c_double*3)(*b[1:]),width,pair,table,sample)
    tx=2*math.floor(sample[0]/(65536*nu)*(w/2));ty=math.floor(sample[1]/(65536*nv)*h)
    for duplicate in range(2 if doubled else 1):
     for lane in range(2):
      dest=(scan+duplicate)*240+start+pair*2+lane
      if 0<=dest<38400:expected[dest]=(plane[(ty%h)*w+(tx+lane)%w],1)
  scan+=2 if doubled else 1
 rf=p/f'road-{cmd}-fractional-cache-ring.bin';rf.write_bytes(struct.pack('<I',len(ring))+b''.join(struct.pack('<8d',r[0],r[1],r[3],r[4],r[5],0,0,0) for r in ring));output=p/f'road-{cmd}-fractional-pipeline-output.bin';run=subprocess.run([str((p/'road-source-fractional-pipeline-probe.exe').resolve()),str(p/f'road-{cmd}-fractional-pipeline.frag'),str(p/f'road-{cmd}-index-cases-0.bin'),str(p/'road-correction-reciprocal.bin'),str(rf),str(p/f'road-{cmd}-index-texture.bin'),str(output),str(p/'road_source_span_cache_double.frag'),str(p/f'road-{cmd}-double-coverage-cache.frag')],capture_output=True,text=True,timeout=120);assert run.returncode==0,(run.returncode,run.stdout,run.stderr);actual=list(struct.iter_unpack('<2i',output.read_bytes()));assert len(actual)==38400
 for i,(a,b) in enumerate(zip(actual,expected)):assert a==b,(cmd,i,a,b)
 checks.append(dict(command=cmd,exact_destinations=38400,covered=sum(v[1]==1 for v in expected)))
report=dict(result='PASS',phase=offset,checks=checks,scope='Fractional sourceX/Y/Q/U/V quarter offsets through packed GPU spans, integer coverage scheduling and continuous UV sampling vs CPU source-write oracle. Not fractional viewport/fullscene motion.');(p/'road-source-fractional-pipeline-tests.json').write_text(json.dumps(report,indent=2));print(report)
