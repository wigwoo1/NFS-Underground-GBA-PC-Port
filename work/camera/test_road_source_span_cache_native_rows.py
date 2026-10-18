from pathlib import Path
import ctypes as C,json,struct,subprocess
p=Path('work/camera');fn=C.CDLL(str((p/'road-span-transition-at.dll').resolve())).nf_road_span_transition_at;fn.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 cmd=road['command'];ring=[[v+(.25 if k in [0,1,3,4,5] else 0) for k,v in enumerate(r)] for r in road['clipped_ring']];rf=p/f'road-{cmd}-fractional-cache-ring.bin';rf.write_bytes(struct.pack('<I',len(ring))+b''.join(struct.pack('<8d',r[0],r[1],r[3],r[4],r[5],0,0,0) for r in ring));data=(C.c_double*(len(ring)*6))(*(v for row in ring for v in row));output=p/f'road-{cmd}-span-cache-native-rows-output.bin'
 run=subprocess.run([str((p/'road-source-span-cache-native-rows-probe.exe').resolve()),str(p/'road_source_span_cache_native_rows.frag'),str(p/f'road-{cmd}-span-gpu-cases.bin'),str(p/'road-correction-reciprocal.bin'),str(rf),str(p/f'road-{cmd}-index-texture.bin'),str(output)],capture_output=True,text=True,timeout=60)
 assert run.returncode==0,(run.returncode,run.stdout,run.stderr)
 actual=list(struct.iter_unpack('<4d',output.read_bytes()));assert len(actual)==4320
 for row in range(2160):
  out=(C.c_double*8)();ok=fn(data,len(ring),(row+.5)/13.5,table,out)
  for side in range(2):
   expected=tuple(out[side*4+k] for k in range(4)) if ok else (-77,)*4
   assert all(abs(a-b)<1e-8 for a,b in zip(actual[row*2+side],expected)),(cmd,row,side,actual[row*2+side],expected)
 checks.append(dict(command=cmd,rows=2160,endpoints=4320,output=run.stdout))
report=dict(result='PASS',checks=checks,scope='GPU row prepass readback versus C corrected span: native4K viewport pixelcenter rows, packed full-double X/UVQ with fractional source geometry and attributes. Diagnostic only; two-pass renderer and timing remain pending.');(p/'road-source-span-cache-native-rows-tests.json').write_text(json.dumps(report,indent=2));print(report)
